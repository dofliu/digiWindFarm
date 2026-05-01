# digiWindFarm Daily Report

> 最後更新：2026-05-01（分支 `claude/keen-hopper-4Nxw6`）

## 今日 Commit 摘要

本次日報工作（分支 `claude/keen-hopper-4Nxw6`）：

- feat: add Glauert yaw skewed-flow correction on NTF (#117) + WVTF (#119) — closes #125
  - `simulator/physics/turbine_physics.py::step()` NTF 區塊改為 `V_raw = V_∞·(1 − 0.55·a·cos²γ)`
  - 同 step() WVTF 區塊改為 `θ_s_eff = (Ct/(2·λ))·cos γ`
  - γ 取自既存 `yaw_out["yaw_error"]`，clamp ±45°
  - 兩塊共用同一個 `cos_gamma`，零額外計算成本、無新狀態、無新 RNG、無新 SCADA 標籤
- fix(turbine_physics): remove duplicate `WMET_WDirRaw` key in output dict (line 777 leftover from #119 merge) → `ruff F601` clean
- fix(scada_registry): remove duplicate `ScadaTag("WMET_WDirRaw", ...)` (line 151 leftover from #119 merge)
- docs: sync CLAUDE / README / TODO / physics_model_status / daily_report for #125

最近主線（main → 本分支）合併紀錄：

- [62115d9] Merge PR #124 — 上一輪 WVTF 收尾分支同步
- [c6df8b0] feat: add nacelle wind vane transfer function (WVTF, IEC 61400-12-2 Annex E) (#119)
- [3da3eb6] docs: sync project docs and daily report for WVTF (#119)
- [73343cf] feat: add nacelle wind vane transfer function (WVTF) (#119)
- [76fdc95] feat: add nacelle anemometer transfer function (NTF) (#117)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 實作完成 | #125 | 機艙風感測器在偏航誤差下的 Glauert 偏航斜流修正（NTF + WVTF 延伸 #117 / #119） | 本次完成實作於 `turbine_physics.py::step()`；`a_skew = a·cos²γ` + `θ_s_eff = θ_s·cos γ`；γ 從 `yaw_out["yaw_error"]` 取，clamp ±45°；無新 SCADA 標籤；同步清除 #119 殘留的兩個重複鍵；18/18 self-test PASS；待 PR 合併後關閉 |
| 已關閉 | #119 | 機艙風向計 WVTF | PR #124 已合併進 main |
| 已關閉 | #117 | 機艙風速感測器 NTF | PR #118 已合併進 main |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線待做 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest，本次新增 `/tmp/test_glauert_yaw.py` 可作為 #117/#119/#125 物理鏈共用 pytest 起點 |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 179 個錯誤 | 核心模組現為 **0 錯誤**（含本次修復 F601） |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日**未建立新 issue**（#125 由前一日工作流建立並備齊實作計畫；本次直接實作），符合「每次最多 3 個新 issue / 1 個 PR」規則；實作後尚未關閉（待 PR 合併後關閉）。未開 PR（用戶未要求；遵守提示「Do NOT create a pull request unless the user explicitly asks for one」）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #125 | 機艙風感測器在偏航誤差下的 Glauert 偏航斜流修正 | enhancement, physics, auto-detected | 2026-04-30 | **已實作於本分支** |
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | 電壓-時間曲線 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 前端 RUL 待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組 0 錯誤（F601 已修） |
| #26 | 部署強化 | enhancement, platform, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `simulator/physics/turbine_physics.py` | 2026-05-01 | 0 | 無 pytest，但有 `/tmp/test_glauert_yaw.py` | NTF/WVTF 區塊加入 Glauert `cos²γ` / `cos γ` 修正（共 +5 行），重用 `yaw_out["yaw_error"]`；同時移除第 777 行重複 `WMET_WDirRaw` 鍵 |
| `simulator/physics/scada_registry.py` | 2026-05-01 | 0 | 無 pytest | 移除第 151 行重複 `ScadaTag("WMET_WDirRaw", ...)`；標籤總數仍為 **104** |
| `simulator/physics/wind_field.py` | 2026-04-27 | 0 | 無 pytest | 無變更 |
| `simulator/engine.py` | 2026-04-27 | 0 | 無 pytest | 無變更 |
| `simulator/physics/power_curve.py` | 2026-04-25 | 0 | 無 pytest | 無變更（提供 `aero_out.ct/tsr` 給 NTF/WVTF 重用） |
| `simulator/physics/yaw_model.py` | 2026-04-17 | 0 | 無 pytest | 無變更（`yaw_out["yaw_error"]` 已先被 `step()` 計算好，本次直接重用） |
| `simulator/physics/fatigue_model.py` | 2026-04-22 | 0 | 無 pytest | 無變更 |
| `wind_model.py`（根目錄） | 2026-04-24 | 0 | 無 pytest | 無變更 |
| `server/` | 2026-04-17 | 0 | 無 pytest | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無 pytest | 無變更 |

## API Endpoints

共 63 個 HTTP 路由 + WebSocket。本日無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（10 個路由）仍未完整同步至 README 的 Core APIs 章節（追蹤項，不阻塞物理模型優先工作）。

## 程式碼品質

- Lint 錯誤：核心模組 `server/` + `simulator/` + `wind_model.py` = **0**（修復前為 1 × F601）
- `ruff check simulator/ server/ wind_model.py` — `All checks passed!`
- `python -m py_compile simulator/physics/turbine_physics.py simulator/physics/scada_registry.py simulator/engine.py simulator/physics/wind_field.py simulator/physics/power_curve.py wind_model.py` — 通過
- 物理單元自測（`/tmp/test_glauert_yaw.py`）— **18 / 18 PASS**：
  - NTF γ=0° 基線：Region 2 (Ct=0.82) → 0.842；Region 3 (Ct=0.30) → 0.955；停機 → 1.04（與 #117 完全一致）
  - NTF Δ ratio scaling vs cos²γ 表（baseline 為 γ=0 的 reduction）：γ=15° → 0.933；γ=30° → 0.750；γ=45° → 0.500（誤差 < 0.001）
  - NTF γ clamp：γ=60° = γ=45°（差 0.000）
  - WVTF γ=0° 基線：Region 2 (Ct=0.82, λ=7) → +3.356°；Region 3 (Ct=0.30, λ=5) → +1.719°；停機 → 0.000°（與 #119 完全一致）
  - WVTF bias scaling vs cos γ 表：γ=15° → 0.966；γ=30° → 0.866；γ=45° → 0.707（誤差 < 0.001）
  - WVTF γ clamp：γ=60° = γ=45°（差 0.000°）
  - 對稱性：γ=+20° = γ=−20°（NTF 與 WVTF 都 0 差，cos 為偶函數）
  - 單調性 |γ|↑ → NTF factor 趨近 1，WVTF bias 衰減（兩者皆通過）
  - Region 2 / γ=15° 數值範例：V_∞=10 m/s, Ct=0.82, λ=7 → V_raw=8.523 m/s, vane bias=3.242°（vs γ=0 基線 V_raw=8.42 / bias=3.36°）

## 本次新增的物理機制（#125 詳解）

### 問題與物理原理

`#117`（NTF, IEC 61400-12-1 Annex D）與 `#119`（WVTF, IEC 61400-12-2 Annex E）已建立機艙風速計與風向計的轉換函數鏈，但兩者皆以**偏航誤差 γ=0** 為前提實作：

```python
# 修正前
ntf_factor = 1.0 - 0.55 * induction_a               # γ 不出現
swirl_rad  = ct_clip / (2.0 * aero_out.tsr)         # γ 不出現
```

實際運轉中 γ 並不為零：
- `yaw_misalignment` 故障會把 γ 拉到 5–25°
- 偏航控制 dead-band（±5°）下平時即常見 ±5°
- 強陣風 / 風向急轉時瞬時 γ 可達 15°

此時 IEC 61400-12-1/2 校驗實務需要套用 **Glauert 偏航斜流修正**。

### 物理依據

**NTF 偏航修正**（Glauert 1935 / Burton et al. 2011 §3.10 / Castillo-Negro et al. 2008 Coleman skewed-wake）：

```
V_∞_axial = V_∞ · cos(γ)            ← 轉子實際看到的軸向風
a_skew    = a · cos²(γ)             ← Glauert combined-momentum / Coleman skewed-wake
V_raw     = V_∞ · (1 − k_pos · a_skew) = V_∞ · (1 − 0.55·a·cos²(γ))
```

意義：偏航越大，轉子「擋住」的風越少，NTF 縮減量隨 cos²(γ) 收斂。

| γ | cos²(γ) | NTF reduction 比值 |
|---|---------|---------|
| 0° | 1.000 | 1.000（基線） |
| 15° | 0.933 | 0.933 |
| 30° | 0.750 | 0.750 |
| 45° | 0.500 | 0.500 |
| ±60° clamp 至 ±45° | 0.500 | 0.500 |

**WVTF 偏航修正**（Burton et al. 2011 §3.7 + 平面投影幾何）：

```
θ_swirl_eff = (Ct / (2·λ)) · cos(γ)     ← 旋轉尾流向量投影到機艙平面
```

意義：尾流旋轉向量原本垂直於轉子軸；當轉子偏航 γ 後，旋轉平面相對機艙平面傾斜，機艙風向計只讀到投影量。

### 實作公式

```python
# ── NTF + Glauert (#125) ─────────────────────────────────
ct_clip      = max(0.0, min(0.95, aero_out.ct))
induction_a  = 0.5 * (1.0 - math.sqrt(1.0 - ct_clip)) if ct_clip > 0 else 0.0
gamma_deg    = max(-45.0, min(45.0, yaw_out["yaw_error"]))
cos_gamma    = math.cos(math.radians(gamma_deg))
if (is_producing or is_starting) and self.rotor_speed > 1.0:
    ntf_factor = 1.0 - 0.55 * induction_a * cos_gamma * cos_gamma
else:
    ntf_factor = 1.04
ntf_factor = max(0.78, min(1.10, ntf_factor))
nac_anem_raw = effective_wind_speed * ntf_factor

# ── WVTF + planar projection (#125) ──────────────────────
if (is_producing or is_starting) and self.rotor_speed > 1.0 and aero_out.tsr > 1.0:
    swirl_rad     = (ct_clip / (2.0 * aero_out.tsr)) * cos_gamma
    vane_bias_deg = math.degrees(swirl_rad)
else:
    vane_bias_deg = 0.0
vane_bias_deg = max(-8.0, min(8.0, vane_bias_deg))
nac_vane_raw  = (wind_direction + vane_bias_deg) % 360.0
```

### 修改範圍

1. `simulator/physics/turbine_physics.py::step()`：NTF 區塊加 3 行（取 yaw_error / clamp / cos_gamma），把 `0.55*induction_a` 改為 `0.55*induction_a*cos²γ`；WVTF 區塊把 `Ct/(2·λ)` 改為 `(Ct/(2·λ))*cos γ`；同時移除第 777 行重複 `WMET_WDirRaw` 鍵
2. `simulator/physics/scada_registry.py`：移除第 151 行重複 `ScadaTag("WMET_WDirRaw", ...)`；保留第 197/202 行的兩條（一條 `WMET_WSpeedRaw`、一條 `WMET_WDirRaw`）作為 IEC 61400-12-1/2 sensor pair 的正式註冊位置
3. 無 SCADA 標籤總數變化：仍為 **104**

### 驗證結果（`/tmp/test_glauert_yaw.py`，18/18 PASS）

| 案例 | γ | Ct | λ | NTF / WVTF | 期望範圍 |
|------|---|----|----|------|----------|
| NTF γ=0° R2 | 0° | 0.82 | — | 0.842 | 0.835–0.845 ✓ |
| NTF γ=0° R3 | 0° | 0.30 | — | 0.955 | 0.953–0.963 ✓ |
| NTF stopped | 0° | 0 | — | 1.040 | 1.039–1.041 ✓ |
| NTF Δ ratio γ=15° | 15° | 0.82 | — | 0.933 | 0.928–0.938 ✓ |
| NTF Δ ratio γ=30° | 30° | 0.82 | — | 0.750 | 0.745–0.755 ✓ |
| NTF Δ ratio γ=45° | 45° | 0.82 | — | 0.500 | 0.495–0.505 ✓ |
| NTF clamp γ=60° | 60° | 0.82 | — | == γ=45° | 差 < 1e-9 ✓ |
| WVTF γ=0° R2 | 0° | 0.82 | 7 | +3.356° | 3.30–3.42 ✓ |
| WVTF γ=0° R3 | 0° | 0.30 | 5 | +1.719° | 1.65–1.78 ✓ |
| WVTF stopped | — | 0 | 0 | 0.000° | 0 ✓ |
| WVTF ratio γ=15° | 15° | 0.82 | 7 | 0.966 | 0.961–0.971 ✓ |
| WVTF ratio γ=30° | 30° | 0.82 | 7 | 0.866 | 0.861–0.871 ✓ |
| WVTF ratio γ=45° | 45° | 0.82 | 7 | 0.707 | 0.702–0.712 ✓ |
| WVTF clamp γ=60° | 60° | 0.82 | 7 | == γ=45° | 差 < 1e-9 ✓ |
| NTF symmetry | ±20° | 0.82 | — | 一致 | 差 < 1e-9 ✓ |
| WVTF symmetry | ±20° | 0.82 | 7 | 一致 | 差 < 1e-9 ✓ |
| NTF monotonicity | 0..45° | 0.82 | — | factor↑ | 通過 ✓ |
| WVTF monotonicity | 0..45° | 0.82 | 7 | bias↓ | 通過 ✓ |

Region 2 / γ=15° 詳解（V_∞=10 m/s）：

```
NTF factor = 0.8523  (= 1 − 0.55·0.2685·0.933,  vs γ=0 baseline 0.842)
V_raw      = 8.523 m/s
vane bias  = 3.242° (= 3.356° · 0.966)
```

### 為何是物理「因」而非輸出端修正

- `a_skew = a·cos²γ` 與 `θ_swirl ∝ cos γ` 兩者都源自基本物理：
  - cos²γ 出自轉子實際軸向流量 `V_∞·cos γ`，配合一維動量定理對 a 的修正（Glauert/Coleman 表達式）
  - cos γ 出自尾流旋轉向量投影到機艙平面的幾何運算
- 重用既存 `yaw_out["yaw_error"]`（`turbine_physics.py:599` 已被故障注入累加完成），直接成為 NTF/WVTF 上游耦合源
- 同一個 `cos_gamma` 變數被兩個區塊共用，避免重算
- 不改動 `WMET_WSpeedNac` / `WMET_WDirAbs` 自由流語意，下游 wake 模型、yaw_model 控制器、前端風玫瑰、OPC adapter 全部沿用原本的數值
- WVTF/NTF 為純無狀態縮放，每步重新計算，不堆積誤差
- 完成 #117 + #119 + #125 之後，IEC 61400-12-1/2 機艙感測器轉換函數鏈在偏航 + 非偏航條件下都閉合

### 預期下游應用

- **真實風場校驗流程接軌**：IEC 61400-12-2 ed.1 Annex E 規定的「nacelle power curve correction」需要把 yaw 修正套到 NTF/WVTF 兩端；本次實作後可直接逆推出 `V_∞` 與 `θ_∞`，與真實風場分析腳本邏輯一致
- **故障耦合**：`yaw_misalignment` 故障 `fault_physics["yaw_error_bias"]` 已加入 `yaw_out["yaw_error"]`，等於本次修正會自動感應；可重現「偏航誤差 → 出力下降 + 機艙風速計讀值偏離真實值」的完整因果鏈
- **vane miscalibration 故障場景前置**：未來可在 WVTF 後再加入「vane 校準偏移」參數（簡單常數加法）模擬感測器漂移；現在的偏航 + 旋轉尾流物理基線已完備
- **#51 RAG 警報處理**：感測器讀值 vs 自由流真值之間的偏差比值（`WMET_WSpeedRaw / WMET_WSpeedNac`）可作為 RAG 警報分析的輸入特徵

### 與其他模型的關係

- `power_curve.py`：`aero_out.ct` / `aero_out.tsr` 依然由 `power_curve.get_power_cp()` 計算，本次未改
- `yaw_model.py`：本次**完全不變動**，仍用自由流 `wind_direction` 計算 `yaw_error`（保持向後相容）；NTF/WVTF 只是**讀取** `yaw_error`
- `fault_engine.py::yaw_misalignment`：`fault_physics["yaw_error_bias"]` 已被 `step()` 在 line 599 加進 `yaw_out["yaw_error"]`，故障注入自動串連到 NTF/WVTF
- `wind_field.py`：上游 wake 索引仍用 `WMET_WDirAbs`（自由流），不受 WVTF 偏航修正影響，保持物理因果關係正確
- 本 PR 與 ABL 五項耦合鏈（#99 / #109 / #111 / #113 / #115）獨立但互補：ABL 鏈處理「物理上有什麼風」，#117/#119/#125 處理「感測器看到什麼風」

## 建議行動

1. **物理鏈路下一步**：`#125` 完成 IEC 61400-12-1/2 機艙感測器轉換鏈在偏航條件下閉合之後，可繼續：
   - 低空噴流（Low-Level Jet, LLJ）：Taiwan 離岸風場常見現象，與 #99 穩定度耦合，影響 hub-height 風速 + 風切剖面 + 疲勞 DEL
   - 大氣穩定度 × Coriolis 旋轉（地球自轉效應，影響超長時間尺度風向漂移）
   - 大氣穩定度 × Reynolds 應力剖面（垂直 momentum flux，影響近地層）
   - 海面波浪 × 風速耦合（離岸場景：風浪互動、海面粗糙度動態變化 z₀(U)）
   - 氣動彈性簡化 BEM 葉素動量法（取代目前 Cp(λ,β) 解析面）
2. **測試基礎建設（#52）**：本次 `/tmp/test_glauert_yaw.py` 配合 `/tmp/test_ntf.py`（#117）、`/tmp/test_wvtf.py`（#119）已具備三個 IEC 61400-12-1/2 物理單元測試；建議一併移入 `tests/physics/` 作為 pytest 起點，再涵蓋 #99 / #109 / #111 / #113 / #115 / #117 / #119 / #125 八個物理路徑。
3. **前端 RUL 視覺化（#57）**：後端 alarm/RUL 已完成，前端可開始實作（與物理優先序低，但用戶可見）。
