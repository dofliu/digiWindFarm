"""
疲勞與載荷模型 — 塔架/葉片載荷計算與 DEL 損傷指標

計算：
  - 塔基前後/左右彎矩 (Tower base fore-aft / side-to-side moment)
  - 葉根揮舞/擺振彎矩 (Blade root flapwise / edgewise moment)
  - 簡化 DEL (Damage Equivalent Load) — peak-valley range counting + Wöhler curve
  - 累積損傷比 (Miner's rule cumulative damage fraction)

載荷來源：
  - 氣動推力 (thrust) → 塔基前後彎矩主成分
  - 氣動扭矩 (aero torque) → 葉根擺振主成分
  - 重力 1P 循環 → 葉根擺振週期性成分
  - 風擾動 → 塔基隨機載荷
  - 故障耦合 → 結冰/旋角不平衡/偏航偏差加劇特定載荷
"""

import math
import numpy as np
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class FatigueOutput:
    """疲勞模型單步輸出"""
    twr_bs_my: float = 0.0   # kNm — 塔基前後彎矩
    twr_bs_mx: float = 0.0   # kNm — 塔基左右彎矩
    bld_rt_my: float = 0.0   # kNm — 葉根揮舞彎矩
    bld_rt_mx: float = 0.0   # kNm — 葉根擺振彎矩
    del_twr: float = 0.0     # 0-100 — 塔架 DEL 指標
    del_bld: float = 0.0     # 0-100 — 葉片 DEL 指標
    dmg_accum: float = 0.0   # 0-1 — 累積損傷比 (Miner's rule)


class FatigueModel:
    """塔架/葉片載荷與疲勞損傷模型

    基於物理因果：推力→塔基彎矩、扭矩→葉根彎矩、重力→1P循環。
    DEL 使用簡化的 peak-valley range counting 搭配 Wöhler 曲線。
    """

    # Wöhler 指數：鋼材 m=4, 複合材料 m=10
    _M_TOWER = 4
    _M_BLADE = 10

    # 設計基準 DEL (kNm)，用於正規化至 0-100
    _DESIGN_DEL_TWR = 800.0
    _DESIGN_DEL_BLD = 400.0

    # 設計壽命（秒）— 20 年
    _DESIGN_LIFE_S = 20 * 365.25 * 24 * 3600

    # DEL 更新頻率（每 N 步更新一次，減少計算量）
    _DEL_UPDATE_INTERVAL = 60

    def __init__(
        self,
        seed: int = 0,
        hub_height: float = 64.0,
        rotor_diameter: float = 70.65,
        rated_power_kw: float = 2000.0,
    ):
        self._rng = np.random.RandomState(seed)
        self._hub_height = hub_height
        self._blade_length = rotor_diameter / 2.0
        self._rated_power_kw = rated_power_kw

        # 轉子重量估算（Z72 約 50 kN）
        self._rotor_weight_kn = 45.0 + self._rng.uniform(-5.0, 8.0)

        # Per-turbine 永久差異：材料疲勞特性
        self._material_fatigue_scale = 1.0 + self._rng.uniform(-0.15, 0.15)
        self._tower_damping_scale = 1.0 + self._rng.uniform(-0.10, 0.10)
        self._blade_stiffness_scale = 1.0 + self._rng.uniform(-0.12, 0.12)

        # 1P 相位追蹤（模擬葉片重力循環）
        self._rotor_phase = self._rng.uniform(0, 2 * math.pi)

        # Ring buffers — 儲存彎矩歷史供 DEL 計算
        self._twr_my_buf: deque = deque(maxlen=120)
        self._bld_my_buf: deque = deque(maxlen=120)

        # 狀態
        self._prev = FatigueOutput()
        self._dmg_accum = 0.0
        self._del_counter = 0
        self._cached_del_twr = 0.0
        self._cached_del_bld = 0.0
        # Warm-up：啟動暫態期間不計算 DEL（避免 0→rated 的巨大範圍）
        self._warmup_steps = 0
        self._WARMUP_THRESHOLD = 180  # 前 3 分鐘不計算 DEL

    def step(
        self,
        thrust_kn: float,
        aero_torque_knm: float,
        aero_load_factor: float,
        rotor_speed_rpm: float,
        wind_speed: float,
        pitch_angle: float,
        power_kw: float,
        dt: float,
        active_faults: Optional[List[Dict]] = None,
    ) -> FatigueOutput:
        """計算單步載荷與疲勞指標

        所有載荷源自物理因果而非直接偏移輸出標籤。
        """
        out = FatigueOutput()

        # 更新轉子相位（1P 重力循環）
        if rotor_speed_rpm > 0.5:
            rot_freq = rotor_speed_rpm / 60.0
            self._rotor_phase += 2 * math.pi * rot_freq * dt
            self._rotor_phase %= 2 * math.pi

        pitch_rad = math.radians(max(0.0, min(90.0, pitch_angle)))

        # ── 塔基前後彎矩 (Tower base fore-aft) ──
        # 主成分：推力 × 輪轂高度
        twr_my_thrust = thrust_kn * self._hub_height
        # 風擾動造成的隨機載荷
        twr_my_turb = wind_speed * abs(self._rng.normal(0, 0.02)) * self._hub_height
        # 轉子重量偏心
        twr_my_grav = self._rotor_weight_kn * 1.2
        out.twr_bs_my = (twr_my_thrust + twr_my_turb + twr_my_grav) * self._tower_damping_scale

        # ── 塔基左右彎矩 (Tower base side-to-side) ──
        # 扭矩反作用力 + 1P 不平衡效應
        twr_mx_torque = aero_torque_knm * 0.15
        twr_mx_1p = thrust_kn * 0.05 * math.sin(self._rotor_phase)
        twr_mx_noise = abs(self._rng.normal(0, 0.01)) * self._hub_height * wind_speed * 0.3
        out.twr_bs_mx = abs(twr_mx_torque + twr_mx_1p + twr_mx_noise) * self._tower_damping_scale

        # ── 葉根揮舞彎矩 (Blade root flapwise) ──
        # 推力分配至三片葉片，受旋角影響
        cos_pitch = math.cos(pitch_rad)
        bld_my_thrust = (thrust_kn / 3.0) * self._blade_length * cos_pitch
        # 風剪應力貢獻
        bld_my_shear = wind_speed * 0.08 * self._blade_length * 0.3
        bld_my_noise = abs(self._rng.normal(0, 0.008)) * self._blade_length * wind_speed
        out.bld_rt_my = (bld_my_thrust + bld_my_shear + bld_my_noise) * self._blade_stiffness_scale

        # ── 葉根擺振彎矩 (Blade root edgewise) ──
        # 扭矩分配 + 重力 1P 循環（物理關鍵特徵）
        bld_mx_torque = aero_torque_knm / 3.0
        # 重力在擺振方向的 1P 循環：mg × r × sin(θ)
        bld_mx_grav = (self._rotor_weight_kn / 3.0) * self._blade_length * 0.3 * math.sin(self._rotor_phase)
        bld_mx_noise = abs(self._rng.normal(0, 0.005)) * self._blade_length
        out.bld_rt_mx = abs(bld_mx_torque + bld_mx_grav + bld_mx_noise) * self._blade_stiffness_scale

        # ── 故障耦合 ──
        if active_faults:
            self._apply_fault_effects(out, active_faults, rotor_speed_rpm, wind_speed)

        # ── Low-pass smoothing（避免瞬間跳變）──
        alpha = min(1.0, dt / 3.0)
        out.twr_bs_my = self._smooth(self._prev.twr_bs_my, out.twr_bs_my, alpha)
        out.twr_bs_mx = self._smooth(self._prev.twr_bs_mx, out.twr_bs_mx, alpha)
        out.bld_rt_my = self._smooth(self._prev.bld_rt_my, out.bld_rt_my, alpha)
        out.bld_rt_mx = self._smooth(self._prev.bld_rt_mx, out.bld_rt_mx, alpha)

        # 確保非負
        out.twr_bs_my = max(0.0, out.twr_bs_my)
        out.twr_bs_mx = max(0.0, out.twr_bs_mx)
        out.bld_rt_my = max(0.0, out.bld_rt_my)
        out.bld_rt_mx = max(0.0, out.bld_rt_mx)

        # ── 更新 ring buffer ──
        self._twr_my_buf.append(out.twr_bs_my)
        self._bld_my_buf.append(out.bld_rt_my)

        # ── DEL 計算（每 N 步更新，減少運算量）──
        # Warm-up 期間不計算，避免啟動暫態（0→rated）的巨大範圍汙染 DEL
        self._warmup_steps += 1
        self._del_counter += 1
        if (self._warmup_steps > self._WARMUP_THRESHOLD
                and self._del_counter >= self._DEL_UPDATE_INTERVAL
                and len(self._twr_my_buf) >= 10):
            self._del_counter = 0
            self._cached_del_twr = self._compute_del(
                list(self._twr_my_buf), self._M_TOWER, self._DESIGN_DEL_TWR
            )
            self._cached_del_bld = self._compute_del(
                list(self._bld_my_buf), self._M_BLADE, self._DESIGN_DEL_BLD
            )

        out.del_twr = self._cached_del_twr
        out.del_bld = self._cached_del_bld

        # ── Miner's rule 累積損傷 ──
        if rotor_speed_rpm > 0.5 and out.twr_bs_my > 0:
            # 簡化：使用當前載荷水準估算每秒損傷增量
            load_ratio_twr = out.twr_bs_my / (self._DESIGN_DEL_TWR * 15.0)
            load_ratio_bld = out.bld_rt_my / (self._DESIGN_DEL_BLD * 15.0)
            dmg_rate = (
                (load_ratio_twr ** self._M_TOWER + load_ratio_bld ** self._M_BLADE)
                * self._material_fatigue_scale
            )
            self._dmg_accum += dmg_rate * dt / self._DESIGN_LIFE_S
            self._dmg_accum = min(1.0, self._dmg_accum)

        out.dmg_accum = self._dmg_accum

        self._prev = out
        return out

    def _apply_fault_effects(
        self, out: FatigueOutput,
        faults: List[Dict],
        rotor_speed_rpm: float,
        wind_speed: float,
    ):
        """故障耦合：透過物理因果加劇載荷"""
        speed_ratio = min(1.0, rotor_speed_rpm / 22.0)

        for fault in faults:
            sev = float(fault.get("severity", 0.0))
            sid = fault.get("scenario_id", "")

            if sid == "blade_icing":
                # 結冰造成質量不平衡 → 葉根彎矩大幅增加
                out.bld_rt_my *= 1.0 + 0.70 * sev
                out.bld_rt_mx *= 1.0 + 0.50 * sev
                # 不對稱推力 → 塔基也受影響
                out.twr_bs_my *= 1.0 + 0.20 * sev

            elif sid in ("pitch_imbalance", "pitch_motor_fault"):
                # 旋角不平衡 → 1P 擺振彎矩加劇
                out.bld_rt_mx *= 1.0 + 0.50 * sev * speed_ratio
                out.bld_rt_my *= 1.0 + 0.20 * sev * speed_ratio

            elif sid in ("yaw_misalignment", "yaw_sensor_drift"):
                # 偏航偏差 → 不對稱風載 → 塔基左右彎矩加劇
                out.twr_bs_mx *= 1.0 + 0.40 * sev
                out.twr_bs_my *= 1.0 + 0.10 * sev

            elif sid == "bearing_wear":
                # 軸承磨損 → 摩擦增加 → 疲勞加速（但載荷變化較小）
                out.twr_bs_my *= 1.0 + 0.05 * sev
                out.bld_rt_mx *= 1.0 + 0.08 * sev

            elif sid == "gearbox_overheat":
                # 齒輪箱問題 → 扭轉振盪 → 擺振彎矩增加
                out.bld_rt_mx *= 1.0 + 0.15 * sev

    def _compute_del(self, buf: List[float], m: int, design_del: float) -> float:
        """簡化 DEL：peak-valley range counting + Wöhler 正規化

        從歷史 buffer 提取峰谷對，計算等效載荷範圍。
        """
        if len(buf) < 4:
            return 0.0

        # 提取峰谷點
        peaks_valleys = self._extract_peaks_valleys(buf)
        if len(peaks_valleys) < 3:
            return 0.0

        # 計算相鄰峰谷差的載荷範圍
        ranges = []
        for i in range(1, len(peaks_valleys)):
            r = abs(peaks_valleys[i] - peaks_valleys[i - 1])
            if r > 0.1:  # 過濾極小波動
                ranges.append(r)

        if not ranges:
            return 0.0

        # DEL = (Σ range^m / N)^(1/m)
        n = len(ranges)
        sum_rm = sum(r ** m for r in ranges)
        del_val = (sum_rm / n) ** (1.0 / m)

        # 正規化至 0-100
        normalized = min(100.0, (del_val / design_del) * 100.0)
        return round(normalized, 1)

    @staticmethod
    def _extract_peaks_valleys(buf: List[float]) -> List[float]:
        """從時間序列提取局部峰值和谷值"""
        if len(buf) < 3:
            return list(buf)

        result = [buf[0]]
        for i in range(1, len(buf) - 1):
            prev_val, curr, next_val = buf[i - 1], buf[i], buf[i + 1]
            # 局部極大或極小
            if (curr >= prev_val and curr >= next_val) or (curr <= prev_val and curr <= next_val):
                result.append(curr)
        result.append(buf[-1])
        return result

    @staticmethod
    def _smooth(prev: float, target: float, alpha: float) -> float:
        return prev + (target - prev) * alpha
