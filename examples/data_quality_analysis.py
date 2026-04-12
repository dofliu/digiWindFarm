"""
SCADA 資料品質分析腳本

產生 48 小時模擬資料（含多種風況和故障），然後進行全面性分析：
1. 功率曲線 shape（power vs wind scatter）
2. 溫度響應時間常數
3. 振動頻譜在不同工況的分布
4. 載荷與風速/功率的相關性
5. 故障前後信號變化幅度
6. tag 間的物理相關性
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from simulator.engine import WindFarmSimulator
from simulator.physics.fault_engine import TEST_PLANS

# ═══════════════════════════════════════════════════════════
# Phase 1: 產生模擬資料
# ═══════════════════════════════════════════════════════════
def generate_data(duration_hours=2.0, time_step=1.0, turbine_count=5):
    """產生含多種工況的模擬資料"""
    print(f"[Phase 1] 產生 {duration_hours}h 模擬資料 ({turbine_count} 台風機, dt={time_step}s)...")

    sim = WindFarmSimulator(turbine_count=turbine_count)
    sim.start()
    import time; time.sleep(1)

    plan = TEST_PLANS["basic_validation"]
    fault_steps = sorted(plan["steps"], key=lambda s: s.offset_seconds)
    fault_idx = 0

    all_rows = []
    total_steps = int(duration_hours * 3600 / time_step)
    report_interval = max(1, total_steps // 20)

    sim_time = datetime.now()

    for step_i in range(total_steps):
        sim_time += timedelta(seconds=time_step)
        sim_seconds = step_i * time_step

        # 注入故障（按計劃）
        while fault_idx < len(fault_steps) and fault_steps[fault_idx].offset_seconds <= sim_seconds:
            fs = fault_steps[fault_idx]
            if fs.turbine_id in [f"WT{str(i+1).zfill(3)}" for i in range(turbine_count)]:
                sim.fault_engine.inject(
                    scenario_id=fs.scenario_id,
                    turbine_id=fs.turbine_id,
                    severity_rate=fs.severity_rate,
                    initial_severity=fs.initial_severity,
                )
                print(f"  [t={sim_seconds/3600:.1f}h] Injected {fs.scenario_id} on {fs.turbine_id}")
            fault_idx += 1

        # 切換風況
        if step_i == int(total_steps * 0.25):
            sim.wind_model.set_override(wind_speed=15.0, wind_direction=270.0)
            print(f"  [t={sim_seconds/3600:.1f}h] Wind → strong (15 m/s)")
        elif step_i == int(total_steps * 0.50):
            sim.wind_model.set_override(wind_speed=4.0, wind_direction=180.0)
            print(f"  [t={sim_seconds/3600:.1f}h] Wind → weak (4 m/s)")
        elif step_i == int(total_steps * 0.75):
            sim.wind_model.clear_override()
            print(f"  [t={sim_seconds/3600:.1f}h] Wind → auto mode")

        # 模擬一步
        readings = sim._run_one_step(sim_time, time_step)

        for r in readings:
            row = {
                "timestamp": sim_time.isoformat(),
                "sim_seconds": sim_seconds,
                "turbine_id": r["turbine_id"],
            }
            scada = r.get("scada", {})
            row.update(scada)

            # 故障狀態
            tid = r["turbine_id"]
            active = [f.__dict__ for f in sim.fault_engine.active_faults if f.turbine_id == tid]
            row["has_fault"] = len(active) > 0
            row["fault_severity"] = max((f["severity"] for f in active), default=0.0)
            row["fault_id"] = active[0]["scenario_id"] if active else ""

            all_rows.append(row)

        if step_i % report_interval == 0:
            pct = step_i / total_steps * 100
            print(f"  Progress: {pct:.0f}% ({step_i}/{total_steps})")

    sim.stop()
    df = pd.DataFrame(all_rows)
    print(f"  完成：{len(df)} 筆資料, {df['turbine_id'].nunique()} 台風機")
    return df


# ═══════════════════════════════════════════════════════════
# Phase 2: 資料品質分析
# ═══════════════════════════════════════════════════════════
def analyze_data(df: pd.DataFrame):
    """全面性資料品質分析"""
    report = []
    report.append("=" * 70)
    report.append("SCADA 資料品質分析報告")
    report.append(f"Data: {len(df)} rows, {df['turbine_id'].nunique()} turbines")
    report.append(f"Time span: {df['sim_seconds'].max()/3600:.1f} hours")
    report.append("=" * 70)

    # ── 1. 功率曲線分析 ──────────────────────────────────
    report.append("\n## 1. 功率曲線 (Power vs Wind)")
    producing = df[df["WTUR_TurSt"] == 6.0].copy()
    if len(producing) > 0:
        ws = producing["WMET_WSpeedNac"]
        pwr = producing["WTUR_TotPwrAt"]

        # 分風速區間統計
        bins = [(3, 5), (5, 7), (7, 9), (9, 11), (11, 13), (13, 15), (15, 20), (20, 25)]
        report.append(f"  {'Wind (m/s)':<15} {'Mean kW':<12} {'Std kW':<12} {'Count':<8} {'CV%':<8}")
        report.append("  " + "-" * 55)

        issues_pc = []
        for lo, hi in bins:
            mask = (ws >= lo) & (ws < hi)
            subset = pwr[mask]
            if len(subset) > 5:
                mean_p = subset.mean()
                std_p = subset.std()
                cv = std_p / mean_p * 100 if mean_p > 0 else 0
                report.append(f"  {lo}-{hi:<12} {mean_p:<12.1f} {std_p:<12.1f} {len(subset):<8} {cv:<8.1f}")

                # 功率曲線問題檢測
                if cv < 1.0 and mean_p > 100:
                    issues_pc.append(f"  ⚠ Wind {lo}-{hi}: CV={cv:.1f}% 太低，信號可能過於平滑")
                if hi <= 13 and mean_p <= 0:
                    issues_pc.append(f"  ⚠ Wind {lo}-{hi}: Mean power=0, cut-in 設定可能有問題")

        # 檢查 Region 2/3 轉折
        region2 = producing[(ws >= 5) & (ws < 11)]
        region3 = producing[(ws >= 13) & (ws < 20)]
        if len(region2) > 10 and len(region3) > 10:
            r2_slope = np.polyfit(region2["WMET_WSpeedNac"], region2["WTUR_TotPwrAt"], 1)[0]
            r3_slope = np.polyfit(region3["WMET_WSpeedNac"], region3["WTUR_TotPwrAt"], 1)[0]
            report.append(f"\n  Region 2 slope: {r2_slope:.1f} kW/(m/s)")
            report.append(f"  Region 3 slope: {r3_slope:.1f} kW/(m/s)")
            if r3_slope > r2_slope * 0.3:
                issues_pc.append(f"  ⚠ Region 3 slope ({r3_slope:.1f}) 偏高，額定功率限制可能不足")
            if r2_slope < 20:
                issues_pc.append(f"  ⚠ Region 2 slope ({r2_slope:.1f}) 偏低，功率對風速敏感度不足")

        if not issues_pc:
            report.append("  ✓ 功率曲線 shape 合理")
        else:
            report.extend(issues_pc)

    # ── 2. 溫度響應分析 ──────────────────────────────────
    report.append("\n## 2. 溫度響應")
    temp_tags = ["WGEN_GnStaTmp1", "WGEN_GnBrgTmp1", "WNAC_NacTmp", "WCNV_CnvCabinTmp"]
    for tag in temp_tags:
        if tag in df.columns:
            vals = df[tag].dropna()
            report.append(f"  {tag:<25} range={vals.min():.1f}~{vals.max():.1f}°C  mean={vals.mean():.1f}  std={vals.std():.1f}")

    # 檢查溫度-功率相關性
    if "WGEN_GnStaTmp1" in df.columns and "WTUR_TotPwrAt" in df.columns:
        corr_tp = producing[["WGEN_GnStaTmp1", "WTUR_TotPwrAt"]].corr().iloc[0, 1]
        report.append(f"\n  Stator temp ~ Power correlation: {corr_tp:.3f}")
        if corr_tp < 0.3:
            report.append("  ⚠ 定子溫度與功率相關性偏低 (<0.3)，溫度模型可能過於獨立")
        elif corr_tp > 0.95:
            report.append("  ⚠ 相關性過高 (>0.95)，溫度可能直接跟隨功率，缺乏熱慣性")
        else:
            report.append("  ✓ 溫度-功率相關性合理（有熱慣性效應）")

    # 溫度變化率（檢查熱慣性）
    for tid in df["turbine_id"].unique()[:1]:
        sub = df[df["turbine_id"] == tid].sort_values("sim_seconds")
        if "WGEN_GnStaTmp1" in sub.columns and len(sub) > 10:
            dT = sub["WGEN_GnStaTmp1"].diff().abs()
            max_dT = dT.max()
            mean_dT = dT.mean()
            report.append(f"\n  {tid} Stator temp change rate: max={max_dT:.3f}°C/step  mean={mean_dT:.4f}°C/step")
            if max_dT > 2.0:
                report.append(f"  ⚠ 溫度跳變過大 ({max_dT:.2f}°C/step)，缺乏足夠的熱慣性平滑")
            else:
                report.append("  ✓ 溫度變化平滑，熱慣性模型正常")

    # ── 3. 振動頻譜分析 ──────────────────────────────────
    report.append("\n## 3. 振動頻譜")
    vib_bands = ["WVIB_Band1pX", "WVIB_Band3pX", "WVIB_BandGearX", "WVIB_BandHfX", "WVIB_BandBbX"]
    for tag in vib_bands:
        if tag in producing.columns:
            vals = producing[tag].dropna()
            report.append(f"  {tag:<20} range={vals.min():.4f}~{vals.max():.4f}  mean={vals.mean():.4f}  std={vals.std():.4f}")

    # 振動-轉速相關性
    if "WVIB_Band1pX" in producing.columns:
        corr_vr = producing[["WVIB_Band1pX", "WROT_RotSpd"]].corr().iloc[0, 1]
        report.append(f"\n  1P band ~ RPM correlation: {corr_vr:.3f}")
        if corr_vr < 0.5:
            report.append("  ⚠ 1P 頻帶與轉速相關性偏低，振動模型可能不夠物理驅動")
        else:
            report.append("  ✓ 1P 頻帶隨轉速變化，物理合理")

    # 停機時振動應趨近 0
    stopped = df[df["WTUR_TurSt"] != 6.0]
    if len(stopped) > 0 and "WVIB_Band1pX" in stopped.columns:
        vib_stopped = stopped["WVIB_Band1pX"].mean()
        report.append(f"  Stopped-state 1P mean: {vib_stopped:.5f} mm/s")
        if vib_stopped > 0.1:
            report.append("  ⚠ 停機時振動偏高，應趨近環境噪聲水平")
        else:
            report.append("  ✓ 停機時振動很低，合理")

    # ── 4. 載荷分析 ──────────────────────────────────────
    report.append("\n## 4. 載荷 (Fatigue / DEL)")
    load_tags = ["WFAT_TwrBsMy", "WFAT_TwrBsMx", "WFAT_BldRtMy", "WFAT_BldRtMx"]
    for tag in load_tags:
        if tag in producing.columns:
            vals = producing[tag].dropna()
            report.append(f"  {tag:<20} range={vals.min():.1f}~{vals.max():.1f}  mean={vals.mean():.1f}  std={vals.std():.1f}")

    # 載荷-推力（風速^2）相關性
    if "WFAT_TwrBsMy" in producing.columns:
        producing_copy = producing.copy()
        producing_copy["wind_sq"] = producing_copy["WMET_WSpeedNac"] ** 2
        corr_lw = producing_copy[["WFAT_TwrBsMy", "wind_sq"]].corr().iloc[0, 1]
        report.append(f"\n  Tower My ~ Wind^2 correlation: {corr_lw:.3f}")
        if corr_lw < 0.6:
            report.append("  ⚠ 塔基彎矩與風速平方相關性偏低，推力→載荷模型可能不夠")
        else:
            report.append("  ✓ 塔基彎矩與風速平方高度相關（推力驅動），物理合理")

    # 載荷-功率相關性
    if "WFAT_TwrBsMy" in producing.columns:
        corr_lp = producing[["WFAT_TwrBsMy", "WTUR_TotPwrAt"]].corr().iloc[0, 1]
        report.append(f"  Tower My ~ Power correlation: {corr_lp:.3f}")

    # 停機載荷
    if len(stopped) > 0 and "WFAT_TwrBsMy" in stopped.columns:
        load_stopped = stopped["WFAT_TwrBsMy"].mean()
        report.append(f"  Stopped-state Tower My mean: {load_stopped:.1f} kNm")
        if load_stopped > 500:
            report.append("  ⚠ 停機時塔基載荷偏高 (>500 kNm)，應僅含重力項")
        else:
            report.append("  ✓ 停機載荷合理（重力+微風）")

    # ── 5. 故障效應分析 ──────────────────────────────────
    report.append("\n## 5. 故障前後信號變化")
    fault_df = df[df["has_fault"] == True]
    normal_df = producing[producing["has_fault"] == False]

    if len(fault_df) > 0 and len(normal_df) > 0:
        fault_ids = fault_df["fault_id"].unique()
        for fid in fault_ids:
            if fid == "":
                continue
            f_sub = fault_df[fault_df["fault_id"] == fid]
            tid = f_sub["turbine_id"].iloc[0]
            n_sub = normal_df[normal_df["turbine_id"] == tid]

            if len(n_sub) < 5 or len(f_sub) < 5:
                continue

            report.append(f"\n  [{fid}] on {tid} ({len(f_sub)} fault samples)")

            # 比較 key tags
            check_tags = ["WTUR_TotPwrAt", "WGEN_GnStaTmp1", "WVIB_BandHfX",
                          "WVIB_Band1pX", "WFAT_TwrBsMy", "WFAT_BldRtMy"]
            for tag in check_tags:
                if tag in n_sub.columns and tag in f_sub.columns:
                    n_mean = n_sub[tag].mean()
                    f_mean = f_sub[tag].mean()
                    if n_mean > 0:
                        pct_change = (f_mean - n_mean) / n_mean * 100
                    else:
                        pct_change = 0
                    marker = "▲" if pct_change > 5 else "▼" if pct_change < -5 else "~"
                    report.append(f"    {tag:<22} normal={n_mean:>10.2f}  fault={f_mean:>10.2f}  change={pct_change:>+7.1f}% {marker}")
    else:
        report.append("  （本次模擬無故障資料或正常資料不足）")

    # ── 6. Tag 間物理相關性矩陣 ─────────────────────────
    report.append("\n## 6. Tag 間物理相關性")
    corr_tags = [
        "WMET_WSpeedNac", "WTUR_TotPwrAt", "WROT_RotSpd", "WGEN_GnStaTmp1",
        "WNAC_VibMsNacXDir", "WVIB_Band1pX", "WVIB_BandHfX",
        "WFAT_TwrBsMy", "WFAT_BldRtMy",
    ]
    avail = [t for t in corr_tags if t in producing.columns]
    if len(avail) >= 4:
        corr_matrix = producing[avail].corr()

        # 應該高度相關的組合
        expected_high = [
            ("WMET_WSpeedNac", "WTUR_TotPwrAt", "風速 ↔ 功率"),
            ("WMET_WSpeedNac", "WROT_RotSpd", "風速 ↔ 轉速"),
            ("WTUR_TotPwrAt", "WROT_RotSpd", "功率 ↔ 轉速"),
            ("WVIB_Band1pX", "WROT_RotSpd", "1P振動 ↔ 轉速"),
            ("WFAT_TwrBsMy", "WMET_WSpeedNac", "塔基載荷 ↔ 風速"),
        ]
        report.append("\n  應高度相關的 tag 組合：")
        for t1, t2, desc in expected_high:
            if t1 in corr_matrix.columns and t2 in corr_matrix.columns:
                r = corr_matrix.loc[t1, t2]
                status = "✓" if abs(r) > 0.6 else "⚠ 偏低"
                report.append(f"    {desc:<25} r={r:>+.3f}  {status}")

        # 不應該高度相關的組合
        expected_low = [
            ("WVIB_BandHfX", "WMET_WSpeedNac", "HF振動 ↔ 風速（除非故障）"),
        ]
        report.append("\n  不應高度相關的 tag 組合：")
        for t1, t2, desc in expected_low:
            if t1 in corr_matrix.columns and t2 in corr_matrix.columns:
                r = corr_matrix.loc[t1, t2]
                status = "✓ 合理" if abs(r) < 0.8 else "⚠ 可能有問題"
                report.append(f"    {desc:<35} r={r:>+.3f}  {status}")

    # ── 7. 個體差異分析 ──────────────────────────────────
    report.append("\n## 7. 風機個體差異")
    if "WTUR_TotPwrAt" in producing.columns:
        per_turb = producing.groupby("turbine_id")["WTUR_TotPwrAt"].mean()
        report.append(f"  各風機平均功率: min={per_turb.min():.1f}  max={per_turb.max():.1f}  std={per_turb.std():.1f} kW")
        spread = (per_turb.max() - per_turb.min()) / per_turb.mean() * 100
        report.append(f"  Spread: {spread:.1f}%")
        if spread < 1.0:
            report.append("  ⚠ 風機間差異太小 (<1%)，individuality model 可能不足")
        elif spread > 30:
            report.append("  ⚠ 風機間差異太大 (>30%)，可能有異常值")
        else:
            report.append("  ✓ 風機間存在合理差異")

    # ── 8. 數值品質檢查 ──────────────────────────────────
    report.append("\n## 8. 數值品質")
    nan_counts = df.isnull().sum()
    nan_cols = nan_counts[nan_counts > 0]
    if len(nan_cols) > 0:
        report.append(f"  ⚠ 有 {len(nan_cols)} 個欄位含 NaN 值:")
        for col, cnt in nan_cols.items():
            report.append(f"    {col}: {cnt} NaN ({cnt/len(df)*100:.1f}%)")
    else:
        report.append("  ✓ 無 NaN 值")

    # 檢查值域異常
    range_checks = [
        ("WTUR_TotPwrAt", -100, 5500),
        ("WROT_RotSpd", -1, 30),
        ("WGEN_GnStaTmp1", -10, 200),
        ("WFAT_TwrBsMy", -100, 20000),
        ("WVIB_Band1pX", -0.01, 20),
    ]
    for tag, lo, hi in range_checks:
        if tag in df.columns:
            out_of_range = df[(df[tag] < lo) | (df[tag] > hi)]
            if len(out_of_range) > 0:
                report.append(f"  ⚠ {tag}: {len(out_of_range)} 筆超出合理範圍 [{lo}, {hi}]")
            else:
                report.append(f"  ✓ {tag}: 全部在合理範圍內")

    # ═══════════════════════════════════════════════════════════
    # 彙整問題與建議
    # ═══════════════════════════════════════════════════════════
    report.append("\n" + "=" * 70)
    report.append("問題彙整與優先順序")
    report.append("=" * 70)

    issues = [line for line in report if "⚠" in line]
    goods = [line for line in report if "✓" in line]

    report.append(f"\n通過項目：{len(goods)} 項")
    report.append(f"待改善項目：{len(issues)} 項")
    if issues:
        report.append("\n待改善列表：")
        for i, issue in enumerate(issues, 1):
            report.append(f"  {i}. {issue.strip()}")

    return "\n".join(report)


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    # 產生 2 小時資料（dt=1s, 5 台風機）→ 約 36000 筆
    df = generate_data(duration_hours=2.0, time_step=1.0, turbine_count=5)

    # 儲存原始資料
    csv_path = os.path.join(os.path.dirname(__file__), "simulated_scada_2h.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"\n[Phase 1] 已儲存至 {csv_path}")

    # 分析
    print("\n[Phase 2] 分析中...\n")
    report = analyze_data(df)
    print(report)

    # 儲存報告
    report_path = os.path.join(os.path.dirname(__file__), "data_quality_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[Phase 2] 報告已儲存至 {report_path}")
