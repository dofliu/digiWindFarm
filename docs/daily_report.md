# digiWindFarm Daily Report

> 最後更新：2026-05-02（分支 `claude/keen-hopper-GbY6P`）

## 今日 Commit 摘要

本次日報工作（分支 `claude/keen-hopper-GbY6P`）：

- feat(turbine_physics): add cup-anemometer overspeeding bias (#127, IEC 61400-12-1 Annex H)
  - `simulator/physics/turbine_physics.py::step()` 在 #117/#125 NTF 區塊後新增 overspeeding 區塊
  - 公式：`bias = 1 + 1.5·TI_local²`，`TI_local = sqrt((effective_ti · _local_ti_multiplier)² + _wake_added_ti²)`
  - 物理依據：杯式風速計對陣風加速比下沉減速更快（D ∝ V² 不對稱拖曳力矩，Kristensen 1998 / Pedersen 2006）
  - clamp 上限 +10%；停機 / rotor_speed ≤ 1 RPM 時 bias = 1.0（杯子不轉）
  - 重用既有 `effective_ti`（`engine.py:112`）+ `_local_ti_multiplier` (#91) + `_wake_added_ti` (#103)，**首度將三條 TI 路徑串接到感測器讀值**
- feat(engine): pass `effective_ti` to `model.step(...)` as new kwarg（1 行）
- docs: sync CLAUDE.md / TODO.md / README.md / docs/physics_model_status.md / docs/daily_report.md for #127

最近主線（main → 本分支）合併紀錄：

- [070de49] Merge PR #126 — 上一輪 Glauert 修正分支同步
- [b97e98f] feat: add Glauert yaw skewed-flow correction on NTF + WVTF (#125)
- [62115d9] Merge PR #124 — WVTF 收尾分支
- [c6df8b0] feat: add nacelle wind vane transfer function (WVTF, IEC 61400-12-2 Annex E) (#119)
- [76fdc95] feat: add nacelle anemometer transfer function (NTF, IEC 61400-12-1 Annex D) (#117)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 實作完成 | #127 | 機艙杯式風速計 overspeeding 統計偏置（IEC 61400-12-1 Annex H 延伸 #117/#125） | 本次完成實作於 `turbine_physics.py::step()`；`bias = 1 + 1.5·TI_local²` 套用於 #117/#125 NTF 區塊之後；無新 SCADA 標籤；19/19 self-test PASS；待 PR 合併後關閉 |
| 已關閉 | #125 | 機艙風感測器 Glauert γ 修正 | PR #126 已合併進 main |
| 已關閉 | #119 | 機艙風向計 WVTF | PR #124 已合併進 main |
| 已關閉 | #117 | 機艙風速計 NTF | PR #118 已合併進 main |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線待做 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest，本次新增 `/tmp/test_overspeeding.py` 可作為 #127 物理鏈共用 pytest 起點 |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 179 個錯誤 | 核心模組仍為 **0 錯誤** |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日**未建立新 issue**（#127 由前一日工作流建立並備齊實作計畫；本次直接實作），符合「每次最多 3 個新 issue / 1 個 PR」規則；實作後尚未關閉（待 PR 合併後關閉）。未開 PR（用戶未要求；遵守提示「Do NOT create a pull request unless the user explicitly asks for one」）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #127 | 機艙杯式風速計 overspeeding 統計偏置 | enhancement, physics, auto-detected | 2026-05-02 | **已實作於本分支** |
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | 電壓-時間曲線 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 前端 RUL 待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組 0 錯誤 |
| #26 | 部署強化 | enhancement, platform, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `simulator/physics/turbine_physics.py` | 2026-05-02 | 0 | 無 pytest，但有 `/tmp/test_overspeeding.py` (19/19) | 簽章新增 `effective_ti=0.10` kwarg；NTF 之後加入 9 行 overspeeding bias 區塊；無新 SCADA 標籤 |
| `simulator/engine.py` | 2026-05-02 | 0 | 無 pytest | `model.step(...)` 呼叫加入 `effective_ti=effective_ti` kwarg（1 行）|
| `simulator/physics/scada_registry.py` | 2026-05-01 | 0 | 無 pytest | 無變更（本日未改 SCADA 註冊表，仍 104 標籤）|
| `simulator/physics/wind_field.py` | 2026-04-27 | 0 | 無 pytest | 無變更 |
| `simulator/physics/power_curve.py` | 2026-04-25 | 0 | 無 pytest | 無變更（提供 `aero_out.ct/tsr` 給 NTF/WVTF 重用）|
| `simulator/physics/yaw_model.py` | 2026-04-17 | 0 | 無 pytest | 無變更（`yaw_out["yaw_error"]` 已先被 `step()` 計算好）|
| `simulator/physics/fatigue_model.py` | 2026-04-22 | 0 | 無 pytest | 無變更 |
| `wind_model.py`（根目錄） | 2026-04-24 | 0 | 無 pytest | 無變更 |
| `server/` | 2026-04-17 | 0 | 無 pytest | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無 pytest | 無變更 |

## API Endpoints

共 63 個 HTTP 路由 + WebSocket。本日無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（10 個路由）仍未完整同步至 README 的 Core APIs 章節（追蹤項，不阻塞物理模型優先工作）。

## 程式碼品質

- Lint 錯誤：核心模組 `server/` + `simulator/` + `wind_model.py` = **0**
- `ruff check simulator/ server/ wind_model.py` — `All checks passed!`
- `python -m py_compile simulator/physics/turbine_physics.py simulator/engine.py` — 通過
- 物理單元自測（`/tmp/test_overspeeding.py`）— **19 / 19 PASS**：
  - TI=0.00 → 1.000（#117 NTF baseline 完整保留）
  - TI=0.06（離岸 / 穩定夜間）→ +0.5%（幾乎不可見）
  - TI=0.10（中性、IEC 參考）→ +1.5%（校驗實務需扣除）
  - TI=0.15（陸上 / 對流午後）→ +3.4%（IEC Annex H 典型量級）
  - TI=0.20（高湍流 / 強陣風）→ +6.0%
  - TI=0.25 → +9.4%
  - TI=0.30 → clamped at +10%
  - TI=0.50 → clamped at +10%
  - rotor_speed=0 / 0.5 → bias = 1.0（杯子不轉）
  - rotor_speed=1.5 → bias 套用
  - producing=False → bias = 1.0
  - pocket multiplier 1.5×TI=0.10 → +3.4%（與直接 TI=0.15 結果一致）
  - pocket multiplier 0.5×TI=0.10 → +0.4%（低 TI 案例）
  - quadrature combine TI=0.10 + wake=0.05 → +1.88%
  - quadrature combine TI=0.10 + wake=0.10 → +3.0%
  - 複合案例 eff=0.10/mult=1.3/wake=0.07 → +3.27%
  - 單調性 TI↑ → bias↑（TI ∈ {0.05, 0.10, 0.15, 0.20, 0.25}）通過
  - 邊界 [1.0, 1.10] 通過

## 本次新增的物理機制（#127 詳解）

### 問題與物理原理

`#117`（NTF, IEC 61400-12-1 Annex D）+ `#119`（WVTF, Annex E）+ `#125`（Glauert γ 修正）已建立機艙風速計與風向計**在均值與偏航條件下**的轉換函數鏈，但兩者皆以**理想線性響應**為前提實作：

```python
# 修正前
nac_anem_raw = effective_wind_speed * ntf_factor   # 沒有考慮統計偏置
```

實際上 IEC 61400-12-1 Annex H 明確記錄的**另一項系統性誤差**為——

**杯式風速計 overspeeding bias**：
- 杯子受拖曳力 D ∝ V²（非線性），對陣風加速比對風速下沉減速更快（asymmetric drag torque）
- 長期均值讀值系統性偏高 `ΔV/V ≈ k_overspeed · TI²`
- `k_overspeed ≈ 1.0–2.0` 典型加熱杯式（Risø Class 1）；超音波 sonic 為 0
- 此偏置與 NTF 的誘導折扣**反方向**，但兩者**獨立疊加**

### 物理依據

**Kristensen 1998（Risø-R-1024 / J. Atmos. Oceanic Technol. 15, 5–17）**：

從風速 `V(t) = ⟨V⟩ + v(t)`、`σ_v² = TI² · ⟨V⟩²`，在杯子的二次轉動方程式上對渦流脈動取平均，得到：

```
⟨V_cup⟩ = ⟨V⟩ · (1 + k · TI²)
```

其中 `k` 由杯子幾何（cup factor、distance constant、moment of inertia）決定，IEC 61400-12-1 Annex H 提供標準校驗程序，典型 k=1.0–2.5。本實作取 k=1.5 為加熱 Risø Class 1 默認（>70% 商用）。

**TI_local 三條來源 quadrature combine**：

```
TI_pocket   = effective_ti · _local_ti_multiplier  # #99 ABL × #91 pocket
TI_local    = sqrt(TI_pocket² + _wake_added_ti²)   # 加上 #103 wake-added TI
overspeed_bias = 1 + 1.5 · TI_local²
```

quadrature 組合是正確的，因為 pocket TI（大氣翻轉）與 wake-added TI（轉子尾流）為**獨立隨機來源**，能量為平方和（與 Frandsen 多源 TI 模型一致）。

| TI | bias 值 | 物理意義 |
|----|--------|----------|
| 0.06（離岸 / 穩定夜間）| +0.5% | 微小，幾乎不可見 |
| 0.10（中性 IEC 參考）| +1.5% | 校驗實務需扣除 |
| 0.15（陸上 / 對流午後）| +3.4% | IEC Annex H 典型量級 |
| 0.20（高湍流 / 強陣風）| +6.0% | 顯著 |
| 0.27 起 → clamp | +10% | 物理上限（杯子拖曳力矩飽和）|

### 實作公式

```python
# ── Cup-Anemometer Overspeeding Bias (#127, IEC 61400-12-1 Annex H) ──
if (is_producing or is_starting) and self.rotor_speed > 1.0:
    ti_pocket = max(0.0, float(effective_ti)) * self._local_ti_multiplier
    ti_local_total = math.sqrt(ti_pocket * ti_pocket + self._wake_added_ti * self._wake_added_ti)
    overspeed_bias = 1.0 + 1.5 * ti_local_total * ti_local_total
    overspeed_bias = min(overspeed_bias, 1.10)
else:
    overspeed_bias = 1.0
nac_anem_raw *= overspeed_bias
```

### 修改範圍

1. `simulator/physics/turbine_physics.py::step()`：
   - 簽章新增 kwarg `effective_ti: float = 0.10`（保持向後相容預設值）
   - NTF 區塊（line 738）後插入 9 行 overspeeding bias 區塊
2. `simulator/engine.py`：`model.step(...)` 呼叫加入 `effective_ti=effective_ti` 參數（1 行）
3. **無 SCADA 標籤總數變化**：仍為 **104**（透過既有 `WMET_WSpeedRaw / WMET_WSpeedNac × WMET_LocalTi × WMET_WakeTi` 觀察）

### 驗證結果（`/tmp/test_overspeeding.py`，19/19 PASS）

| 案例 | TI / 條件 | bias | 期望範圍 |
|------|-----------|------|----------|
| TI=0.00 | 0 | 1.000 | =1.0 ✓ |
| TI=0.06 | offshore / 穩定夜間 | 1.0054 | +0.5% ✓ |
| TI=0.10 | neutral, IEC 參考 | 1.015 | +1.5% ✓ |
| TI=0.15 | onshore / 對流午後 | 1.0338 | +3.4% ✓ |
| TI=0.20 | 高湍流 | 1.060 | +6.0% ✓ |
| TI=0.25 | 極端 | 1.0938 | +9.4% ✓ |
| TI=0.30 | clamp | 1.10 | clamp ✓ |
| TI=0.50 | clamp | 1.10 | clamp ✓ |
| rotor_speed=0 | TI=0.20 | 1.0 | 杯子不轉 ✓ |
| rotor_speed=0.5 | TI=0.20 | 1.0 | 杯子不轉 ✓ |
| rotor_speed=1.5 | TI=0.20 | 1.060 | 套用 ✓ |
| producing=False | TI=0.20 | 1.0 | 不在運轉 ✓ |
| pocket mult 1.5 × TI=0.10 | local TI=0.15 | 1.0338 | +3.4% ✓ |
| pocket mult 0.5 × TI=0.10 | local TI=0.05 | 1.00375 | +0.4% ✓ |
| TI=0.10 + wake=0.05 | quadrature | 1.0188 | +1.88% ✓ |
| TI=0.10 + wake=0.10 | quadrature | 1.030 | +3.0% ✓ |
| 複合 eff=0.10/mult=1.3/wake=0.07 | 全來源 | 1.0327 | +3.27% ✓ |
| 單調性 TI↑ → bias↑ | TI ∈ {0.05..0.25} | 通過 | ✓ |
| 邊界 [1.0, 1.10] | 全範圍 | 通過 | ✓ |

### 為何是物理「因」而非輸出端修正

- `k · TI²` 由動量方程加上 cup torque 不對稱阻力（Kristensen 1998 推導），**非經驗修正**
- 重用 `effective_ti × _local_ti_multiplier`（已在 `step()` 狀態）+ `_wake_added_ti`（已在 `step()` 狀態），無新狀態、無新 RNG mutation
- 不改 `WMET_WSpeedNac`（自由流），保持向後相容
- TI=0 → bias=1 → **完全保留 #117 baseline 行為**
- 純無狀態縮放，不堆積誤差
- 停機 / rotor_speed ≤ 1 RPM 時 bias=1.0 物理正確（杯子不轉，無 overspeeding）

### 與其他模型的耦合

- `power_curve.py`：完全不變（`aero_out.ct/tsr` 仍維持自由流計算）
- `yaw_model.py`：完全不變
- `wind_field.py`：上游 wake 索引仍用 `WMET_WDirAbs`（自由流），不受 overspeeding 影響
- `fault_engine.py`：`yaw_misalignment` 透過 #125 已耦合到 NTF；overspeeding 在此基礎上再多套用一層 TI² 偏置；未來 `anemometer_drift` 故障可疊加在此 bias 之後
- **首度將三條 TI 路徑（#99 ABL + #91 pocket + #103 wake-added）coupled back 到感測器讀值** — 過去這三條路徑只影響 AR(1) 風場與結構載荷，不影響感測器
- 完成 **IEC 61400-12-1 Annex D（NTF 均值, #117） + Glauert γ 修正（#125） + Annex H（cup 統計偏置, #127）** 的閉合鏈

### 預期下游應用

- **真實風場校驗流程接軌**：IEC 61400-12-1 ed.2 Annex H 規定的「nacelle anemometer overspeeding correction」需要把 TI² 偏置從讀值扣除；本次實作後可直接逆推出 `V_∞`，與真實風場分析腳本邏輯一致
- **TI-coupled 故障場景前置**：未來可實作 `anemometer_drift` 故障模擬感測器漂移；現在的 NTF + Glauert + overspeeding 三層物理基線已完備，故障注入只需單純疊加常數偏移
- **#51 RAG 警報處理**：`(WMET_WSpeedRaw / WMET_WSpeedNac)` ÷ `(NTF_baseline)` 偏差比值可作為 RAG 警報分析的輸入特徵；TI 高的場景應當看到比值上升 3–6%，TI 低時應當貼近 NTF baseline

## 建議行動

1. **物理鏈路下一步**：`#127` 完成 IEC 61400-12-1 Annex D + γ + H 鏈閉合之後，可繼續：
   - 機艙風向計 vane 的 distance constant / 角度 lag（IEC 61400-12-2 Annex F：類似 cup overspeeding 但對方向訊號）
   - 低空噴流（Low-Level Jet, LLJ）：Taiwan 離岸風場常見現象，與 #99 穩定度耦合
   - 大氣穩定度 × Coriolis 旋轉（地球自轉效應，影響超長時間尺度風向漂移）
   - 海面波浪 × 風速耦合（離岸場景：風浪互動、海面粗糙度動態變化 z₀(U)）
   - 氣動彈性簡化 BEM 葉素動量法（取代目前 Cp(λ,β) 解析面）
2. **測試基礎建設（#52）**：本次 `/tmp/test_overspeeding.py` 配合 `/tmp/test_glauert_yaw.py`（#125）、`/tmp/test_ntf.py`（#117）、`/tmp/test_wvtf.py`（#119）已具備四個 IEC 61400-12-1/2 物理單元測試；建議一併移入 `tests/physics/` 作為 pytest 起點，再涵蓋 #99 / #109 / #111 / #113 / #115 / #117 / #119 / #125 / #127 九個物理路徑。
3. **前端 RUL 視覺化（#57）**：後端 alarm/RUL 已完成，前端可開始實作（與物理優先序低，但用戶可見）。
