# digiWindFarm Physics Changelog

> 此檔自動歸檔自 `docs/physics_model_status.md` Section 2.6（風場事件真實性）。
> 每個 PR 一節，依 PR 編號倒序排列。本檔僅累加，既有條目不再修改。
> 新增物理機制時：在此加一節 `## PR-NNN — 標題`，然後在 `physics_model_status.md` 留 1 行短摘要 + 連結。

---

<a id="pr-127"></a>
## PR-127 — Cup-anemometer overspeeding bias

Cup-anemometer overspeeding bias (#127, IEC 61400-12-1 ed.2 §6.3.4 + Annex H / Kristensen 1998 Risø-R-1024 *J. Atmos. Oceanic Technol.* 15, 5–17 / Pedersen et al. 2006 Risø-R-1473 / Westermann 1996 *Wind Engineering* 20): real cup-type anemometers respond faster to gusts than to lulls because the drag torque is asymmetric in `V` (D ∝ V², so a +ΔV gust contributes more torque than a −ΔV lull subtracts). Over averaging windows of 1 s and longer, the mean reading is biased high by `Δ⟨V⟩/⟨V⟩ ≈ k_overspeed · TI²` (Kristensen 1998 closed form; Pedersen 2006 measured k=1.0–2.5 on commercial Risø Class 1 cups). k=1.5 is taken as the heated Risø Class 1 default in this simulator (industry typical >70%); sonic anemometers have k≈0 and therefore zero overspeeding. The bias is applied multiplicatively after the #117/#125 NTF block — `nac_anem_raw *= 1 + 1.5·TI_local²` — where the local TI is the quadrature combine of the per-turbine atmospheric TI (`effective_ti × _local_ti_multiplier`, integrating #99 ABL TI multiplier and #91 pocket multiplier) and the wake-added TI (`_wake_added_ti` from #103 Crespo-Hernández): `TI_local = sqrt((effective_ti·local_mult)² + wake_added_ti²)`. Quadrature is the correct combination because pocket TI and wake-added TI are independent stochastic sources (different physical mechanisms — atmospheric overturning vs rotor wake). Clamp ≤+10% reflects the physical upper bound (cup torque saturates and the bias formula breaks down beyond TI≈0.27). Operating-state branching: `(is_producing or is_starting) and rotor_speed > 1 RPM` applies the bias; stopped/parked rotor has no overspeeding because the cup is not turning (a real cup at rest with airflow simply tilts on its hub bearing without registering). Self-test (19/19 PASS): TI=0.00 → 1.000 (#117 baseline preserved exactly); TI=0.06 (offshore / stable nocturnal) → +0.5% (barely visible in trend charts); TI=0.10 (neutral, IEC reference) → +1.5% (calibration practice subtracts this); TI=0.15 (onshore / convective afternoon) → +3.4% (IEC Annex H typical scale); TI=0.20 (high-TI / strong gusts) → +6.0% (significant); TI=0.25 → +9.4%; TI=0.30 → clamped at +10%; pocket multiplier 1.5×TI=0.10 → +3.4% (matches direct TI=0.15, confirms the multiplier path); pocket multiplier 0.5×TI=0.10 → +0.4% (confirms low-TI case); composite eff=0.10/mult=1.3/wake=0.07 → +3.27% (quadrature combine); monotonicity TI↑ → bias↑ verified across {0.05, 0.10, 0.15, 0.20, 0.25}; bounds [1.00, 1.10] verified across all cases; rotor_speed=0 → bias=1.0 verified (cup not turning); rotor_speed=0.5 → bias=1.0 verified; rotor_speed=1.5 → bias applies. Implementation reuses the existing `effective_ti` from `engine.py:112` (passed through as a new keyword argument to `model.step(...)`) and the per-turbine `_local_ti_multiplier` / `_wake_added_ti` already in `step()` state from #91 / #103, so there is zero extra cost, no new state, no new RNG mutation, and no new SCADA tag. This is the **first time three TI paths (#99 ABL, #91 pocket, #103 wake-added)** couple back into the as-measured sensor reading — previously they only affected the AR(1) wind field and structural loads. Closes the IEC 61400-12-1 mean (Annex D, #117) + Glauert yaw correction (#125) + statistical bias (Annex H, #127) chain for cup-style nacelle anemometers; in field data both the NTF and the overspeeding bias must be inverted to recover the free-stream wind for power-curve analysis. Observable via `WMET_WSpeedRaw / WMET_WSpeedNac × WMET_LocalTi × WMET_WakeTi` correlation: at high TI the ratio should rise above the NTF baseline by 3–6%, at low TI it should sit on the NTF baseline. 104 SCADA tags total (unchanged): no new tag (the bias is folded into the existing `WMET_WSpeedRaw`).

---

<a id="pr-119"></a>
## PR-119 — Nacelle wind vane transfer function

Nacelle wind vane transfer function (#119, IEC 61400-12-2 ed.1 §6.4 + Annex E / Burton, Sharpe, Jenkins, Bossanyi 2011 *Wind Energy Handbook* 2nd ed. §3.7 / Pedersen et al. 2008 Risø-R-1602 / Kragh & Hansen 2014 *J. Sol. Energy Eng.* 136): the SCADA tag `WMET_WDirAbs` previously aliased the free-stream wind direction `wind_direction`. A real wind vane (cup or ultrasonic) mounted on top of the nacelle sits ~1.5R behind the hub, in the rotor's swirl zone, and reads a systematic angular bias because the rotor converts linear inflow into linear+rotational outflow (angular momentum conservation, Euler turbine equation). Burton et al. §3.7 derives the swirl angle from blade-element-momentum theory: tangential induction `a' = Ct / (4·λ)` produces a downstream swirl angle `θ_s ≈ 2·a' = Ct / (2·λ)` rad. The sign follows the rotor sense; modern utility-scale turbines are right-handed (clockwise from the upwind side, e.g. Vestas V236, GE Haliade-X, Siemens Gamesa SG 14-222 DD), giving a positive vane bias downstream of the hub. Operating-state branching: stopped/parked (`is_producing == False and is_starting == False`) or `rotor_speed ≤ 1 RPM` or `tsr ≤ 1` → 0° (no rotor torque, no swirl); producing/starting with `rotor_speed > 1 RPM` and `tsr > 1` → `vane_bias_deg = degrees(Ct / (2·λ))`. Final clamp to `±8°` mirrors the largest realistic field observations even at extreme Ct/λ. Self-test (8/8 + double monotonicity, against a fixed (Ct, λ, rotor_state) sweep): Region 2 (Ct=0.82, λ=7) → +3.36°; Region 2.5 (Ct=0.65, λ=6) → +3.10°; Region 3 (Ct=0.30, λ=5) → +1.72°; starting (Ct=0.55, λ=6) → +2.63°; stopped/cut-out → 0.00°; extreme Ct=0.95/λ=4 → +6.80° (within ±8° clamp); 360°-wrap (358° + 3.36° → 1.36°) ✓. Monotonicity Ct↑ → bias↑ (Ct=0,0.3,0.5,0.7,0.82,0.9 at λ=7 → 0.00, 1.23, 2.05, 2.87, 3.36, 3.68°) and λ↑ → bias↓ (λ=3,5,6,7,8,10 at Ct=0.82 → 7.83, 4.70, 3.92, 3.36, 2.94, 2.35°) verified. Implementation reuses both `aero_out.ct` and `aero_out.tsr` already computed by `power_curve.get_power_cp(...)` for the #117 NTF block, so zero extra cost, no new RNG mutation, no new state. Backwards compatibility: the existing `WMET_WDirAbs` is intentionally left as the free-stream wind direction so that `wind_field.py` upstream-turbine indexing (which uses absolute direction to find which turbines are upstream of which), `yaw_model.py` controller error calculation, `farm_layout.py` direction-aware wake routing, frontend wind rose, and any downstream analysis that relies on absolute geographic direction all keep working without change. The new `WMET_WDirRaw` (REAL32, deg, 0–360, OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WDirRaw`) carries the as-measured vane reading so downstream consumers can opt in to the more realistic signal — for instance, IEC 61400-12-2 nacelle-power-performance verification can apply the inverse WVTF to recover free-stream direction, exactly as is done in field measurements; future fault scenarios can simulate "vane miscalibration → systematic yaw misalignment → power loss" by injecting a constant offset on top of WVTF, mirroring a well-known industry failure mode. Pairs with #117 NTF as the second half of the IEC 61400-12-1/2 nacelle-sensor transfer-function chain — `WMET_WSpeedRaw` for the anemometer (axial induction reduces apparent speed), `WMET_WDirRaw` for the vane (rotor swirl shifts apparent direction). 104 SCADA tags total (was 103): +1 raw nacelle wind vane tag (`WMET_WDirRaw`).

---

<a id="pr-117"></a>
## PR-117 — Nacelle anemometer transfer function

Nacelle anemometer transfer function (#117, IEC 61400-12-1 ed.2 Annex D / IEC 61400-12-2 / Smaïli & Masson 2004 / Antoniou & Pedersen 1997): the SCADA tag `WMET_WSpeedNac` previously aliased the free-stream wind `effective_wind_speed`, which is what the model uses internally for `Cp(λ,β)` and `Ct(λ,β)`. A real cup/sonic anemometer mounted on top of the nacelle sits ~1.5R behind the hub, in the rotor's induction zone, so it reads systematically below free-stream. The NTF derives the as-measured reading from momentum theory `a = 0.5·(1 − √(1 − Ct))` and a position weight `k_pos = 0.55`: `V_raw = V_∞ · (1 − 0.55·a)`. Operating-state branching: producing or starting with `rotor_speed > 1 RPM` applies the induction reduction; otherwise (rotor stopped/parked, no induction) the bluff-body speed-up at the nacelle top dominates → `V_raw = 1.04·V_∞`. Final clamp to `[0.78, 1.10]` keeps the factor inside physically observed bounds. Self-test (7/7 + monotonicity check on a fixed `aero_out.ct` sweep): Region 2 (Ct=0.82) → 0.84·V_∞; Region 2.5 (Ct=0.65) → 0.89·V_∞; Region 3 (Ct=0.30) → 0.96·V_∞; stopped/cut-out → 1.04·V_∞; clamp triggers at Ct=0.95 → 0.79·V_∞. Implementation reuses `aero_out.ct` already computed by `power_curve.get_power_cp(...)` so there is zero extra cost and no new RNG mutation. Backwards compatibility: the existing `WMET_WSpeedNac` is intentionally left as the free-stream wind so that `examples/data_quality_analysis.py` (which uses it as the X-axis of the power curve), `server/routers/turbines.py`, `server/opc_adapter.py`, the frontend trend chart panel, and the `data_quality_report.txt` 18/21 pass-rate are all unchanged. The new `WMET_WSpeedRaw` (REAL32, m/s, 0–40, OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedRaw`) carries the as-measured reading so downstream consumers can opt in to the more realistic signal — for instance, IEC 61400-12-2 power performance verification scripts can apply the inverse NTF to recover the free-stream wind, exactly as is done in field measurements. 103 SCADA tags total (was 102): +1 raw nacelle anemometer tag (`WMET_WSpeedRaw`).

---

<a id="pr-115"></a>
## PR-115 — Atmospheric-stability × turbulence integral length scale L_u coupling

Atmospheric-stability × turbulence integral length scale L_u coupling (#115, connects #99 × Kaimal AR(1) hub-height wind, parallel to #113, Counihan 1975 *Atmos. Environ.* 9, 871–905 / Kaimal & Finnigan 1994 *Atmospheric Boundary Layer Flows* §1.6 / §3 / Peña & Hahmann 2012 *Wind Energy* 15, 717–731 / IEC 61400-1 ed.4 Annex C): `TurbulenceGenerator.step(...)` (the AR(1) wind-speed generator that drives both the farm base wind and every per-turbine spatial-decorrelation channel) now applies `L_u_eff = 340 · clamp(1 − 0.6·s, 0.4, 2.0)` m on top of the IEC 61400-1 hub-height neutral baseline. Because `τ = L_u / V`, the AR(1) coefficient `α = exp(−dt/τ)` becomes stability-dependent without touching the noise-scaling factor `σ·√(1−α²)`. Mapping at V=10 m/s: s=−1 (stable, suppressed vertical mixing, elongated streamwise eddies) → L_u=544 m, τ≈54 s; s=0 (neutral) → 340 m, 34 s; s=+1 (convective, vigorous overturning, broken-up eddies) → 136 m, 14 s. Validation on a 4000 s sequence at TI=0.10 (warm-up 200 s discarded): lag-30 s observed autocorrelation 0.574 / 0.401 / 0.097 vs analytical exp(−30/τ) = 0.576 / 0.414 / 0.110 — within 1.4 % / 3.1 % / 1.3 % of closed form; steady-state σ_v measured at 0.99 / 0.98 / 0.99 m/s vs expected TI·V = 1.00 m/s — amplitude path is preserved (TI multiplier under #99 still owns it). Backwards compatibility verified: omitting the new `stability` kwarg reproduces the prior behaviour bit-for-bit (diff = 0). The same s ∈ [−1, +1] is forwarded from `engine._run_one_step` to both the farm-wide `_turbulence_gen.step(..., stability=atm_stability)` and from `PerTurbineWind.step(..., atm_stability=...)` to every `_turb_gens[i].step(..., stability=atm_stability)`, so the whole farm shares one ABL timescale (consistent with the physical fact that L_u is set by the boundary layer, not by individual rotors). No new SCADA tag — observable via `WMET_AtmStab × WROT_RotSpd` low-frequency autocorrelation; expected lag-30 s autocorr ≥ 0.4 on stable nights vs ≤ 0.15 in convective afternoons. The persistent low-frequency wind on stable nights should also lift low-frequency content of `WLOD_TwrFaMom` and smooth `WYAW_YwVn1AlgnAvg5s` variability, completing the five-link ABL chain (#99 amplitude → #109 wake k* → #111 veer → #113 wake τ_m → #115 wind τ).

---

<a id="pr-113"></a>
## PR-113 — Atmospheric-stability × wake-meander τ_m coupling

Atmospheric-stability × wake-meander τ_m coupling (#113, connects #99 × #95, Counihan 1975 *Atmos. Environ.* 9, 871–905 / Larsen et al. 2008 *Wind Energy* 11, 289–301 / Peña & Hahmann 2012 *Wind Energy* 15, 717–731 / IEC 61400-1 ed.4 Annex C): the DWM AR(1) atmospheric integral timescale (#95 baseline `τ_m = 25 s`) is now stability-dependent. `_update_wake_meander(turbulence_intensity, dt, stability)` computes `τ_m_eff = 25 · clamp(1 − 0.6·s, 0.4, 2.0)` s using the existing #99 score `s ∈ [−1, +1]`. Mapping: s=−1 (stable, suppressed vertical mixing, larger streamwise integral length scale L_u) → τ_m=40 s (slow meander); s=0 (neutral) → 25 s baseline; s=+1 (convective, vigorous overturning) → τ_m=10 s (fast turnover). σ_θ amplitude path is unchanged (still `0.3·TI`) — the amplitude response to stability is already owned by #99's TI multiplier (0.5–1.6×), so this PR adds the orthogonal timescale path only. Self-test on a 4000 s AR(1) sequence at TI=0.10 (1 turbine, σ_θ ≈ 0.030 rad theoretical): lag-25 s autocorrelation 0.452 (stable) / 0.283 (neutral) / 0.010 (convective), matching the analytical `exp(−25/τ)` of 0.535 / 0.368 / 0.082; zero-crossing rate of `WMET_WakeMndr` 0.082 / 0.098 / 0.140 — slower waveform under stable ABL, faster turnover under convection. Implementation is a 6-line change inside `_update_wake_meander` plus passing `stability=atm_stability` from `PerTurbineWind.step(...)` (the kwarg was already plumbed through for #109). No new SCADA tag — directly observable via `WMET_WakeMndr × WMET_AtmStab` autocorrelation; the persistent meander on stable nights also feeds back into downstream blade DEL through the existing wake-meander → Bastankhah deficit path so `WLOD_BldFlapMom` low-frequency content should mirror the lag-25 s rise.

---

<a id="pr-111"></a>
## PR-111 — Atmospheric-stability × wind-veer coupling

Atmospheric-stability × wind-veer coupling (#111, connects #99 × #79, Holton *Atmospheric Dynamics* §5.3 / Stull *Boundary Layer Met* §8.5 / van der Laan et al. 2017 *Wind Energy* 20, 1191–1208): the per-turbine `wind_veer_rate` (#79 baseline 0.10 ± 0.03 °/m) is now multiplied by `factor = clamp(1 − 1.0·s, 0.3, 2.5)` driven by the existing #99 stability score `s ∈ [−1, +1]`. Stable ABL (s<0, nocturnal) preserves the Ekman spiral → strong veer; convective ABL (s>0, afternoon mixing) mixes the directional gradient out → weak veer. Mapping: s=−1 → veer ≈ 0.20 °/m; s=0 → 0.10 °/m (neutral baseline); s=+1 → 0.03 °/m (clamped). Self-test (12 m/s steady, 200 s warm-up): tower side-side moment 255.9 kNm at s=−1 vs 137.2 kNm at s=+1 (+37 % / −26 % vs 186.2 kNm neutral); aero power loss differs by ~13 kW between extremes. Per-turbine `wind_veer_rate` is retained as site/manufacturing variance on top of the atmospheric trend. The effective `veer_rate` is computed once per step in `turbine_physics.step()` (block #79 aero power-loss) and the same value is passed to `fatigue_model.step(wind_veer_rate=...)` so structural loads and aero power stay numerically consistent. No new SCADA tag — observable via `WMET_AtmStab × WLOD_TwrSsMom` correlation; expected r < −0.4 at producing turbines during diurnal cycling.

---

<a id="pr-109"></a>
## PR-109 — Atmospheric-stability × wake-expansion coupling

Atmospheric-stability × wake-expansion coupling (#109, connects #99 × #93, Abkar & Porté-Agel 2015 / Peña et al. 2016): the Bastankhah wake expansion rate `k* = 0.38·TI + 0.004` is now modulated by the existing #99 stability score `s ∈ [−1, +1]`: `k*_eff = k*_neutral · clamp(1 + 0.30·s, 0.55, 1.45)`, clamped to `[0.015, 0.08]`. Stable ABL (s<0, nocturnal / low wind / clear sky) suppresses vertical mixing → smaller k* → wake persists farther. Convective ABL (s>0, afternoon surface heating) enhances mixing → larger k* → wake recovers faster. Self-test on a 3-turbine row at 6 D spacing, V=10 m/s, TI=8 %: stable s=−1 → wake deficit +33.8 %; convective s=+1 → deficit −22.0 %. No new SCADA tag is introduced — the effect is directly observable via correlation between existing `WMET_WakeDef` (per-turbine deficit) and `WMET_AtmStab` (farm-level s). `simulator/engine.py::_run_one_step` passes `atm_stability` into `PerTurbineWind.step(..., atm_stability=...)` which forwards to `_update_wake_factors(..., stability=...)`.

---

<a id="pr-108"></a>
## PR-108 — Bug fix: duplicate `get_wake_added_ti` removed

#108: removed duplicate `PerTurbineWind.get_wake_added_ti` definition in `wind_field.py` (F811 lint error introduced by PR merge conflict of #103 and #106; both bodies were identical so the fix is purely cleanup — no behavior change).

---

<a id="pr-106"></a>
## PR-106 — Dynamic atmospheric pressure coupling

Dynamic atmospheric pressure coupling (#106, extends #101): the existing synoptic weather state `_pressure_state ∈ [−1, +1]` (OU random walk, τ≈2 h, frontal cycle 2–7 days) is mapped to real pressure via `P(t) = 101325 + s·1500 Pa`, bounded to [90000, 105000] Pa. Mid-latitude amplitude ±15 hPa matches temperate-zone frontal statistics (1 σ ≈ 8 hPa, 2 σ ≈ 15 hPa). `WindEnvironmentModel.get_air_density(ts, ..., pressure_pa=...)` now accepts the per-step P so ρ responds to synoptic swings on top of T/RH. With identical T=15 °C / RH=50%, high-P (+15 hPa) vs low-P (−15 hPa) gives ρ=1.2392 vs 1.2030 (Δρ = 3.01%). `WindFarmSimulator._run_one_step` computes P once and hands it to both `get_air_density` and every `turbine.step(..., ambient_pressure_pa=...)` so the whole farm shares the same airmass P. Manual overrides lock P at ISA reference (101325 Pa) to keep demos predictable. New SCADA tag `WMET_AmbPressure` (hPa, 900–1050).

---

<a id="pr-103"></a>
## PR-103 — Wake-added turbulence intensity

Wake-added turbulence intensity (#103, Crespo-Hernández 1996 / IEC 61400-1 Annex E):
  per source-target pair, `TI_added(x, r) = 0.73·a^0.8325·TI_amb^0.0325·(x/D)^-0.32 · gauss(r)` where `a = 0.5·(1−√(1−Ct))` is the axial induction factor. Multi-source contributions combine as sum-of-squares; the result is then quadratically combined with the localized-pocket TI multiplier (#91) — `TI_eff² = (TI_amb·pocket_mult)² + TI_w²` — and fed back into the per-turbine AR(1) wind generator so downstream wind_speed σ rises naturally (downstream/upstream σ ratio measured at 2.12× in self-test). Reuses the Bastankhah Gaussian envelope (#93) and the meander/yaw deflection geometry (#95/#97), so no new pair-distance loop. Self-test: isolated → 0%, 5D downstream → ~14%, 12D → ~10%, multi-row sum-of-squares accumulating, Region 2 (Ct≈0.82) > Region 3 (Ct≈0.31). New SCADA tag `WMET_WakeTi` (REAL32, %, 0–40).

---

<a id="pr-101"></a>
## PR-101 — Air density coupling

Air density coupling (#101): moist-air ρ from ideal gas law + Buck/Magnus vapor correction,
  `ρ = P/(R_d·T_K) · (1 − 0.378·e/P)`, P=101325 Pa, R_d=287.058. `WindEnvironmentModel.get_air_density(ts, temp?, rh?)` shares the temp/humidity already computed for stability, so no extra RNG mutation per step. Engine passes ρ to every turbine (same airmass), and `turbine_physics.step()` writes it into `PowerCurveModel.air_density` each tick so aero power `P = Cp·0.5·ρ·A·V³` and thrust `F = 0.5·ρ·A·Ct·V²` both respond automatically. Verified: 15 °C / 0% RH → 1.2250 (ISA), −10 °C / 50% RH → 1.3406 (+9.4%), 32 °C / 95% RH → 1.1372 (−7.2%), cold/hot power ratio 1.123. Clamp [0.95, 1.35]. New SCADA tag `WMET_AirDensity`.

---

<a id="pr-99"></a>
## PR-99 — Atmospheric stability / diurnal shear-TI coupling

Atmospheric stability / diurnal shear-TI coupling (#99, Monin-Obukhov simplified): continuous stability score s ∈ [−1, +1] composed from solar(t) · wind_damping(V) · cloud_damping(pressure). Drives:
  - wind shear exponent α = clamp(0.14 − 0.10·s, 0.04, 0.30) — nighttime 0.18–0.22, convective afternoon 0.08–0.11
  - turbulence multiplier TI_mult = clamp(1.0 + 0.5·s, 0.5, 1.6) — applied to base TI in both the global and per-turbine turbulence generators
  - Strong-wind regime (V > 15 m/s) damps |s| toward 0 (mechanical mixing)
  - Low-pressure / frontal weather damps |s| toward 0 (cloud cover)
  - Manual wind overrides force neutral s = 0
  - per-turbine permanent α offset (±0.04–0.06) renamed to `wind_shear_exp_offset` and stacks on farm-level α
  - New SCADA tags: `WMET_ShearAlpha` (α), `WMET_AtmStab` (s)

---

<a id="pr-97"></a>
## PR-97 — Yaw-induced wake deflection / wake steering

Yaw-induced wake deflection / wake steering (#97, Bastankhah & Porté-Agel 2016): for each source turbine j with yaw misalignment γ_j (=yaw_error, clamped ±45°), the initial skew angle is θ_c = 0.3·γ·(1−√(1−Ct·cos γ))/cos γ. Near-wake lateral deflection δ_y(x) = tan(θ_c)·x_down is added per-source to the signed cross-stream distance (alongside DWM meander). Engine captures per-turbine `WYAW_YwVn1AlgnAvg5s` each step and feeds it back to `PerTurbineWind.set_yaw_misalignments()` before the next wake update, so the `yaw_misalignment` fault and transient yaw lag both drive end-to-end wake steering. At γ=15°/Ct=0.82 the wake centerline deflects ~9.4 m @ 3D (exact closed-form match), ~22 m @ 500 m downstream. New SCADA tag `WMET_WakeDefl` (m, ±50).

---

<a id="pr-95"></a>
## PR-95 — Dynamic wake meandering

Dynamic wake meandering (#95, Larsen DWM 2008): each turbine's wake centerline oscillates laterally as an AR(1) process with σ_θ ≈ 0.3·TI (radians) and τ ≈ 25 s (atmospheric integral timescale). The meander offset θ_m[source]·x_down is applied to the signed cross-stream distance inside the Bastankhah Gaussian deficit term, so downstream turbines now see time-varying deficit (±1% std at TI=0.08, 500 m spacing). New SCADA tag `WMET_WakeMndr` (wake lateral offset at 3D reference, m, ±50).

---

<a id="pr-93"></a>
## PR-93 — Bastankhah-Porté-Agel Gaussian wake model

Bastankhah-Porté-Agel Gaussian wake model (#93): replaces the simplified Jensen top-hat. Implements ε/D near-wake offset, linear wake expansion σ(x)/D = k*·(x/D)+ε/D with TI-dependent k* (Niayifar & Porté-Agel 2016 k*≈0.38·TI+0.004), Ct-coupled max deficit C(x)=1−√(1−Ct/(8·(σ/D)²)), Gaussian radial profile, and sum-of-squares multi-wake superposition. Ct heuristically follows operating point (~0.82 in Region 2, drops with V² above rated). New SCADA tag `WMET_WakeDef` (wake velocity deficit %).

---

<a id="pr-91"></a>
## PR-91 — localized turbulence pockets

localized turbulence pockets (#91): Gaussian spatial pockets (R=180–380 m), stochastic spawn (~1 per 10–15 min at 10 m/s), TI multiplier 1.4–2.0× at pocket center with Gaussian falloff, rise/hold/fall envelope; applies per-turbine TI boost to `TurbulenceGenerator`; new SCADA tag `WMET_LocalTi` (local TI multiplier %)

---

<a id="pr-79"></a>
## PR-79 — wind veer

wind veer (directional shear with height): linear Ekman spiral model, per-turbine veer rate (0.07–0.13 °/m), azimuth-dependent blade direction offset, lateral force coupling to tower SS and blade flapwise moments (see #79). The per-turbine `wind_veer_rate` is now the *baseline* component; the actual rate fed to the aero / fatigue paths is dynamically modulated by atmospheric stability (#111).

---

<a id="pr-71"></a>
## PR-71 — wind shear profile

wind shear profile: power-law vertical wind profile with configurable exponent (default α=0.2, per-turbine variation ±0.04-0.06), azimuth-dependent blade loading in fatigue model (see #71)

---

