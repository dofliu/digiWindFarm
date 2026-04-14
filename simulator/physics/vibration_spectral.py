"""
Vibration frequency-band model with fault-specific signatures.

Extends the existing VibrationModel with spectral band outputs that
are useful for condition monitoring and diagnostics.

Frequency bands:
  - band_1p:   1× rotational frequency (rotor imbalance)
  - band_3p:   3× blade-pass frequency (tower shadow, blade issues)
  - band_gear: gear mesh frequency band (gearbox condition)
  - band_hf:   high-frequency band (bearing defects, electrical)
  - band_bb:   broadband / overall (structural, aerodynamic)

Fault signatures:
  - bearing_wear:           elevated band_hf, modulated at shaft speed
  - pitch_imbalance:        elevated band_1p, asymmetric X/Y
  - gearbox_overheat:       elevated band_gear, temperature-correlated
  - blade_icing:            elevated band_1p + band_3p, asymmetric
  - generator_overspeed:    elevated band_hf, speed-correlated
  - yaw_misalignment:       elevated band_3p, direction-dependent
  - stator_winding_degradation: elevated band_hf (electrical noise)
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List


@dataclass
class AlarmThresholds:
    """振動頻帶警報門檻輸出 — ISO 10816 啟發"""
    alarm_1p: int = 0        # 0=normal, 1=warning, 2=alarm
    alarm_3p: int = 0
    alarm_gear: int = 0
    alarm_hf: int = 0
    alarm_bb: int = 0
    alarm_overall: int = 0   # max(all bands)
    thresh_1p_warn: float = 0.0   # mm/s — 當前 1P 警告門檻（供顯示參考）
    thresh_1p_alrm: float = 0.0   # mm/s — 當前 1P 警報門檻


@dataclass
class VibrationBands:
    """Output of spectral vibration analysis."""
    band_1p_x: float = 0.0   # mm/s RMS at 1P frequency, X direction
    band_1p_y: float = 0.0
    band_3p_x: float = 0.0   # mm/s RMS at 3P frequency
    band_3p_y: float = 0.0
    band_gear_x: float = 0.0  # mm/s RMS at gear mesh frequency
    band_gear_y: float = 0.0
    band_hf_x: float = 0.0   # mm/s RMS high-frequency (>100Hz equivalent)
    band_hf_y: float = 0.0
    band_bb_x: float = 0.0   # mm/s RMS broadband
    band_bb_y: float = 0.0
    crest_factor: float = 0.0 # peak / RMS ratio (bearing defect indicator)
    kurtosis: float = 3.0     # signal kurtosis (3.0 = Gaussian normal)

    def to_dict(self) -> Dict[str, float]:
        return {
            "vib_band_1p_x": round(self.band_1p_x, 4),
            "vib_band_1p_y": round(self.band_1p_y, 4),
            "vib_band_3p_x": round(self.band_3p_x, 4),
            "vib_band_3p_y": round(self.band_3p_y, 4),
            "vib_band_gear_x": round(self.band_gear_x, 4),
            "vib_band_gear_y": round(self.band_gear_y, 4),
            "vib_band_hf_x": round(self.band_hf_x, 4),
            "vib_band_hf_y": round(self.band_hf_y, 4),
            "vib_band_bb_x": round(self.band_bb_x, 4),
            "vib_band_bb_y": round(self.band_bb_y, 4),
            "vib_crest_factor": round(self.crest_factor, 3),
            "vib_kurtosis": round(self.kurtosis, 3),
        }


class SpectralVibrationModel:
    """Frequency-band vibration model with fault-specific signatures.

    This model decomposes the overall vibration into physically
    meaningful frequency bands, each of which responds differently
    to operating conditions and fault types.
    """

    def __init__(self, seed: int = 0, gear_ratio: float = 1.0, gear_teeth: int = 97):
        self._rng = np.random.RandomState(seed)
        self._gear_ratio = gear_ratio
        self._gear_teeth = gear_teeth  # teeth on ring gear (for mesh frequency)
        self._is_geared = gear_ratio > 1.0

        # Per-turbine permanent characteristics
        self._imbalance_1p = 1.0 + self._rng.uniform(-0.25, 0.30)
        self._blade_3p = 1.0 + self._rng.uniform(-0.15, 0.20)
        self._gear_mesh_amp = (1.0 + self._rng.uniform(-0.20, 0.25)) if self._is_geared else 0.0
        self._hf_floor = 0.02 + self._rng.uniform(0, 0.015)
        self._bb_floor = 0.04 + self._rng.uniform(0, 0.02)

        # Smoothing state for each band
        self._prev = VibrationBands()
        self._peak_buffer: List[float] = []

        # ── 警報門檻系統（ISO 10816 啟發）──
        # 各頻帶基礎門檻（rated 工況下，mm/s RMS）
        self._base_thresholds = {
            "1p":   {"warn": 0.80, "alarm": 1.50},
            "3p":   {"warn": 0.60, "alarm": 1.20},
            "gear": {"warn": 0.50, "alarm": 1.00},
            "hf":   {"warn": 0.30, "alarm": 0.60},
            "bb":   {"warn": 0.50, "alarm": 1.00},
        }
        # Per-turbine 門檻差異
        self._thresh_variation = {
            band: 1.0 + self._rng.uniform(-0.10, 0.12)
            for band in self._base_thresholds
        }
        # 警報狀態追蹤
        self._alarm_levels = {band: 0 for band in self._base_thresholds}
        self._alarm_timers = {band: 0.0 for band in self._base_thresholds}
        # 遲滯比例：須降至門檻的 85% 才解除
        self._HYST_RATIO = 0.85
        # 最短保持時間（秒）— 避免快速切換
        self._HYST_MIN_HOLD_S = 5.0

    def step(
        self,
        rotor_speed_rpm: float,
        wind_speed: float,
        power_kw: float,
        rated_power_kw: float,
        turbulence: float,
        dt: float,
        active_faults: Optional[List[Dict]] = None,
    ) -> VibrationBands:
        """Compute spectral vibration bands for current conditions.

        Args:
            rotor_speed_rpm: Current rotor speed
            wind_speed: m/s
            power_kw: Current power output
            rated_power_kw: Rated power for normalization
            turbulence: Wind turbulence intensity
            dt: Timestep
            active_faults: List of active fault dicts with scenario_id and severity

        Returns:
            VibrationBands with per-band amplitudes
        """
        bands = VibrationBands()

        if rotor_speed_rpm < 0.5:
            # Standstill: ambient noise only
            bands.band_bb_x = self._bb_floor * 0.3 + abs(self._rng.normal(0, 0.005))
            bands.band_bb_y = self._bb_floor * 0.2 + abs(self._rng.normal(0, 0.004))
            bands.band_hf_x = self._hf_floor * 0.2 + abs(self._rng.normal(0, 0.003))
            bands.band_hf_y = self._hf_floor * 0.15 + abs(self._rng.normal(0, 0.002))
            bands.crest_factor = 3.0 + self._rng.normal(0, 0.2)
            bands.kurtosis = 3.0 + self._rng.normal(0, 0.1)
            self._prev = bands
            return bands

        speed_ratio = min(1.0, rotor_speed_rpm / 22.0)
        power_ratio = min(1.0, power_kw / max(rated_power_kw, 1.0))
        load_factor = max(power_ratio, speed_ratio)

        # ── 1P band (rotor imbalance) ──
        base_1p = self._imbalance_1p * speed_ratio * 0.35
        bands.band_1p_x = base_1p * 0.85 + abs(self._rng.normal(0, 0.015))
        bands.band_1p_y = base_1p * 1.10 + abs(self._rng.normal(0, 0.018))

        # ── 3P band (blade pass / tower shadow) ──
        base_3p = self._blade_3p * speed_ratio * 0.22
        aero_3p = wind_speed * turbulence * 0.008
        bands.band_3p_x = base_3p * 1.15 + aero_3p + abs(self._rng.normal(0, 0.012))
        bands.band_3p_y = base_3p * 0.75 + aero_3p * 0.6 + abs(self._rng.normal(0, 0.010))

        # ── Gear mesh band ──
        if self._is_geared:
            # Gear mesh frequency = rotor_speed * teeth / 60
            base_gear = self._gear_mesh_amp * speed_ratio * 0.18
            load_gear = power_ratio * 0.08  # load-dependent gear vibration
            bands.band_gear_x = base_gear + load_gear + abs(self._rng.normal(0, 0.010))
            bands.band_gear_y = (base_gear + load_gear) * 0.7 + abs(self._rng.normal(0, 0.008))

        # ── High-frequency band (bearings, electrical) ──
        base_hf = self._hf_floor + speed_ratio * 0.06 + power_ratio * 0.04
        bands.band_hf_x = base_hf + abs(self._rng.normal(0, 0.008))
        bands.band_hf_y = base_hf * 0.85 + abs(self._rng.normal(0, 0.006))

        # ── Broadband ──
        base_bb = self._bb_floor + wind_speed * turbulence * 0.02 + load_factor * 0.08
        bands.band_bb_x = base_bb + abs(self._rng.normal(0, 0.012))
        bands.band_bb_y = base_bb * 0.80 + abs(self._rng.normal(0, 0.010))

        # ── Crest factor and kurtosis (baseline) ──
        bands.crest_factor = 3.0 + speed_ratio * 0.3 + self._rng.normal(0, 0.15)
        bands.kurtosis = 3.0 + speed_ratio * 0.2 + self._rng.normal(0, 0.10)

        # ── Fault-specific signatures ──
        if active_faults:
            self._apply_fault_signatures(bands, active_faults, speed_ratio, power_ratio, load_factor)

        # Low-pass smooth all bands
        alpha = min(1.0, dt / 2.5)
        bands.band_1p_x = self._smooth(self._prev.band_1p_x, bands.band_1p_x, alpha)
        bands.band_1p_y = self._smooth(self._prev.band_1p_y, bands.band_1p_y, alpha)
        bands.band_3p_x = self._smooth(self._prev.band_3p_x, bands.band_3p_x, alpha)
        bands.band_3p_y = self._smooth(self._prev.band_3p_y, bands.band_3p_y, alpha)
        bands.band_gear_x = self._smooth(self._prev.band_gear_x, bands.band_gear_x, alpha)
        bands.band_gear_y = self._smooth(self._prev.band_gear_y, bands.band_gear_y, alpha)
        bands.band_hf_x = self._smooth(self._prev.band_hf_x, bands.band_hf_x, alpha)
        bands.band_hf_y = self._smooth(self._prev.band_hf_y, bands.band_hf_y, alpha)
        bands.band_bb_x = self._smooth(self._prev.band_bb_x, bands.band_bb_x, alpha)
        bands.band_bb_y = self._smooth(self._prev.band_bb_y, bands.band_bb_y, alpha)
        bands.crest_factor = self._smooth(self._prev.crest_factor, bands.crest_factor, alpha)
        bands.kurtosis = self._smooth(self._prev.kurtosis, bands.kurtosis, alpha)

        # Ensure non-negative
        for attr in ['band_1p_x', 'band_1p_y', 'band_3p_x', 'band_3p_y',
                      'band_gear_x', 'band_gear_y', 'band_hf_x', 'band_hf_y',
                      'band_bb_x', 'band_bb_y']:
            setattr(bands, attr, max(0.0, getattr(bands, attr)))

        self._prev = bands
        return bands

    def compute_alarms(
        self,
        bands: VibrationBands,
        rotor_speed_rpm: float,
        power_kw: float,
        rated_power_kw: float,
        dt: float,
    ) -> AlarmThresholds:
        """計算各頻帶警報等級

        門檻隨轉速調整（低轉速時門檻降低），
        帶遲滯邏輯避免警報快速切換。
        """
        # 轉速因子：低速時降低門檻（靜止時約 40%）
        speed_factor = 0.4 + 0.6 * min(1.0, rotor_speed_rpm / 22.0)

        # 各頻帶量測值取 X/Y 的最大值
        measured = {
            "1p":   max(bands.band_1p_x, bands.band_1p_y),
            "3p":   max(bands.band_3p_x, bands.band_3p_y),
            "gear": max(bands.band_gear_x, bands.band_gear_y),
            "hf":   max(bands.band_hf_x, bands.band_hf_y),
            "bb":   max(bands.band_bb_x, bands.band_bb_y),
        }

        result_levels = {}
        for band_name in self._base_thresholds:
            base = self._base_thresholds[band_name]
            var = self._thresh_variation[band_name]

            warn_thresh = base["warn"] * speed_factor * var
            alarm_thresh = base["alarm"] * speed_factor * var
            val = measured[band_name]

            current = self._alarm_levels[band_name]
            self._alarm_timers[band_name] += dt

            # 最短保持時間內不切換
            if self._alarm_timers[band_name] < self._HYST_MIN_HOLD_S:
                result_levels[band_name] = current
                continue

            new_level = current
            if current == 0:
                if val > alarm_thresh:
                    new_level = 2
                elif val > warn_thresh:
                    new_level = 1
            elif current == 1:
                if val > alarm_thresh:
                    new_level = 2
                elif val < warn_thresh * self._HYST_RATIO:
                    new_level = 0
            elif current == 2:
                if val < warn_thresh * self._HYST_RATIO:
                    new_level = 0
                elif val < alarm_thresh * self._HYST_RATIO:
                    new_level = 1

            if new_level != current:
                self._alarm_timers[band_name] = 0.0
            self._alarm_levels[band_name] = new_level
            result_levels[band_name] = new_level

        # 1P 門檻參考值（供前端顯示）
        var_1p = self._thresh_variation["1p"]
        thresh_1p_warn = self._base_thresholds["1p"]["warn"] * speed_factor * var_1p
        thresh_1p_alrm = self._base_thresholds["1p"]["alarm"] * speed_factor * var_1p

        return AlarmThresholds(
            alarm_1p=result_levels["1p"],
            alarm_3p=result_levels["3p"],
            alarm_gear=result_levels["gear"],
            alarm_hf=result_levels["hf"],
            alarm_bb=result_levels["bb"],
            alarm_overall=max(result_levels.values()),
            thresh_1p_warn=round(thresh_1p_warn, 4),
            thresh_1p_alrm=round(thresh_1p_alrm, 4),
        )

    def _apply_fault_signatures(
        self, bands: VibrationBands,
        faults: List[Dict],
        speed_ratio: float, power_ratio: float, load_factor: float,
    ):
        """Inject fault-specific vibration signatures into frequency bands."""
        for fault in faults:
            sev = float(fault.get("severity", 0.0))
            sid = fault.get("scenario_id", "")

            if sid == "bearing_wear":
                # Bearing defects: elevated HF with impact-like crest factor
                # BPFO/BPFI harmonics appear in HF band
                speed_coupling = 0.3 + 0.7 * speed_ratio
                bands.band_hf_x += 0.45 * sev * speed_coupling
                bands.band_hf_y += 0.35 * sev * speed_coupling
                # Bearing defects cause impulsive signals → high crest factor and kurtosis
                bands.crest_factor += 2.5 * sev * speed_coupling
                bands.kurtosis += 4.0 * sev * speed_coupling
                # Some 1P modulation from uneven bearing clearance
                bands.band_1p_x += 0.08 * sev * speed_coupling
                bands.band_1p_y += 0.10 * sev * speed_coupling

            elif sid in ("pitch_imbalance", "pitch_motor_fault"):
                # Pitch imbalance: strong 1P (mass/aero imbalance)
                bands.band_1p_x += 0.60 * sev * speed_ratio
                bands.band_1p_y += 0.85 * sev * speed_ratio  # Y dominant (side-to-side)
                # Some 3P modulation
                bands.band_3p_x += 0.15 * sev * speed_ratio
                bands.band_3p_y += 0.10 * sev * speed_ratio

            elif sid == "gearbox_overheat":
                # Gearbox issues: elevated gear mesh band
                bands.band_gear_x += 0.50 * sev * load_factor
                bands.band_gear_y += 0.40 * sev * load_factor
                # Gear damage creates sidebands → higher broadband
                bands.band_bb_x += 0.12 * sev * load_factor
                bands.band_bb_y += 0.10 * sev * load_factor
                bands.kurtosis += 1.5 * sev * load_factor

            elif sid == "blade_icing":
                # Ice: mass imbalance → strong 1P, aerodynamic → 3P
                bands.band_1p_x += 0.70 * sev * speed_ratio
                bands.band_1p_y += 1.10 * sev * speed_ratio  # asymmetric
                bands.band_3p_x += 0.40 * sev * speed_ratio
                bands.band_3p_y += 0.55 * sev * speed_ratio

            elif sid == "generator_overspeed":
                # Overspeed: elevated HF from electrical and mechanical stress
                bands.band_hf_x += 0.55 * sev * (0.5 + 0.5 * speed_ratio)
                bands.band_hf_y += 0.45 * sev * (0.5 + 0.5 * speed_ratio)
                bands.band_1p_x += 0.20 * sev * speed_ratio
                bands.band_1p_y += 0.25 * sev * speed_ratio

            elif sid in ("yaw_misalignment", "yaw_sensor_drift"):
                # Yaw misalignment: uneven blade loading → 3P dominant
                bands.band_3p_x += 0.50 * sev * speed_ratio
                bands.band_3p_y += 0.30 * sev * speed_ratio
                bands.band_bb_x += 0.15 * sev * load_factor

            elif sid == "stator_winding_degradation":
                # Electrical fault: HF electrical noise
                bands.band_hf_x += 0.30 * sev * power_ratio
                bands.band_hf_y += 0.25 * sev * power_ratio
                # Winding asymmetry can create 2× line frequency components
                bands.band_bb_x += 0.10 * sev * power_ratio

            elif sid in ("converter_cooling_fault", "grid_voltage_sag"):
                # Converter stress: mild HF increase
                bands.band_hf_x += 0.15 * sev * power_ratio
                bands.band_hf_y += 0.12 * sev * power_ratio

            elif sid == "nacelle_cooling_failure":
                # Thermal expansion → bearing clearance changes → HF modulation
                bands.band_hf_x += 0.12 * sev * load_factor
                bands.band_hf_y += 0.10 * sev * load_factor
                bands.band_bb_x += 0.08 * sev

            elif sid == "hydraulic_leak":
                # Yaw brake pressure loss → yaw oscillation → broadband
                bands.band_bb_x += 0.20 * sev * load_factor
                bands.band_bb_y += 0.25 * sev * load_factor

    @staticmethod
    def _smooth(prev: float, target: float, alpha: float) -> float:
        return prev + (target - prev) * alpha
