# digiWindFarm Daily Report

> 最後更新：2026-04-28（分支 `claude/keen-hopper-un7sb`）

## 今日 Commit 摘要

本次日報工作（分支 `claude/keen-hopper-un7sb`）：

- [404f200] feat: add nacelle wind vane transfer function (WVTF) (#119)

近 48 小時主幹 `main` 合併摘要：

- [5541796] Merge PR #118 — 機艙風速感測器轉換函數 NTF (#117)
- [76fdc95] feat: add nacelle anemometer transfer function (NTF) (#117)
- [6b03437] Merge PR #116 — 大氣穩定度 × 湍流積分長度尺度 L_u 耦合 (#115)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 實作 | #119 | 機艙風向計轉換函數 (WVTF, IEC 61400-12-2 Annex E) | 昨日已建立；本次完成實作於 `turbine_physics.py::step()` + `scada_registry.py`，新增 SCADA 標籤 `WMET_WDirRaw`。**待 PR 合併後關閉** |
| 保持 | #117 | 機艙風速感測器 NTF | 已合併（PR #118） |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線待做 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 115 個錯誤 | 核心模組現為 **0 錯誤** |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日**未建立**新 issue（直接實作既有 #119），符合「每次最多 3 個新 issue / 1 個 PR」規則；實作後尚未關閉（待 PR 合併後關閉）。未開 PR（用戶未要求；遵守提示「Do NOT create a pull request unless the user explicitly asks for one」）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #119 | 機艙風向計 WVTF (IEC 61400-12-2 Annex E) | enhancement, physics, auto-detected | 2026-04-27 | **本日已實作於本分支** |
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | 電壓-時間曲線 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 前端 RUL 待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #44 | Ruff lint 115 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組 0 錯誤 |
| #26 | 部署強化 | enhancement, platform, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `simulator/physics/turbine_physics.py` | 2026-04-28 | 0 | 無測試套件 | `step()` 內加入 WVTF 區塊（8 行）；新增 `WMET_WDirRaw` 輸出 |
| `simulator/physics/scada_registry.py` | 2026-04-28 | 0 | 無測試套件 | 新增 `WMET_WDirRaw` ScadaTag（REAL32, deg, 0–360），SCADA 物理標籤從 103 → **104** |
| `simulator/physics/wind_field.py` | 2026-04-26 | 0 | 無測試套件 | 無變更 |
| `simulator/engine.py` | 2026-04-26 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/power_curve.py` | 2026-04-25 | 0 | 無測試套件 | 無變更（提供 `aero_out.ct` 與 `aero_out.tsr` 給 WVTF 直接重用） |
| `simulator/physics/fatigue_model.py` | 2026-04-22 | 0 | 無測試套件 | 無變更 |
| `wind_model.py`（根目錄） | 2026-04-24 | 0 | 無測試套件 | 無變更 |
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |

## API Endpoints

共 60 個 HTTP 路由 + 1 WebSocket。本日無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（10 個路由）仍未完整同步至 README 的 Core APIs 章節（追蹤項，不阻塞物理模型優先工作）。

## 程式碼品質

- Lint 錯誤：核心模組 `server/` + `simulator/` + `wind_model.py` = **0**
- `ruff check simulator/ server/ wind_model.py` — `All checks passed!`
- `python -m py_compile simulator/physics/turbine_physics.py simulator/physics/scada_registry.py` — 通過
- 物理單元自測（`/tmp/test_wvtf.py`）— **11 / 11 PASS + Ct/λ 雙向單調性 ✓**：
  - 停機（rotor=0 RPM, Ct=0）：bias = 0.000° ✓
  - 啟動（is_starting, Ct=0.55, λ=6）：bias = +2.626° ✓（介於 +2.50..+2.70°）
  - Region 2 峰值 Cp（Ct=0.82, λ=7）：bias = +3.356° ✓（介於 +3.30..+3.50°）
  - Region 2.5 過渡（Ct=0.65, λ=6）：bias = +3.104° ✓
  - Region 3 變槳（Ct=0.30, λ=5）：bias = +1.719° ✓
  - 切出風速以上（V=27, 停機）：bias = 0.000° ✓
  - 極端 Ct=0.95 / λ=4：bias = +6.804° ✓（在 ±8° clamp 內）
  - 極低 TSR=0.5（clamp guard）：bias = 0.000° ✓
  - 360° 環繞處理：358° + 3.36° → 1.36° ✓
  - 單調性 Ct↑ → bias↑：[0.819, 1.637, 2.456, 3.274, 3.888]° ✓
  - 單調性 λ↑ → bias↓：[7.83, 4.70, 3.36, 2.61, 2.14]° ✓
- 引擎端到端 smoke test：**未執行**（本環境未安裝 numpy；獨立物理單元測試已驗證 WVTF 邏輯）
- Broken imports：0
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52；本次自測腳本可移入 `tests/physics/test_wvtf.py` 作為 pytest 起點（同 #117 NTF）
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 物理標籤：**104 個**（#119 新增 `WMET_WDirRaw`）

## 今日新增功能

### 機艙風向計轉換函數 (WVTF, IEC 61400-12-2 Annex E) — #119

**問題與物理原理**

`simulator/physics/turbine_physics.py:764` 將 SCADA 標籤 `WMET_WDirAbs` 直接設為自由流風向：

```python
"WMET_WDirAbs": round(wind_direction % 360, 2),
```

但 `wind_direction` 是模型內部的**自由流方向**（free-stream），用於上游尾流索引 (`wind_field.py`) 與偏航控制器 (`yaw_model.py`) 的對齊基準。真實機艙頂部安裝的風向計位於**轉子下游 ~1.5R**，吃到旋轉葉輪在尾流中注入的**切向旋轉 (rotor wake swirl)**，因此讀值與自由流方向有系統性偏差。這是 IEC 61400-12-2 Annex E 明定要校正的 nacelle wind vane bias，與 #117 NTF 為同一條 IEC 61400-12-1/2 機艙感測器物理鏈。

**物理依據**：角動量守恆 (Euler turbine equation)
- 葉片元素 + 動量理論：`a' = Ct / (4·λ)` （切向誘導因子）
- 下游 vane 觀測到的 swirl angle：`θ_s ≈ 2·a' = Ct / (2·λ)` rad（Burton et al. 2011 Wind Energy Handbook §3.7）
- 右手旋轉子（順時針，從上風看向下游，現代風機與 Z72 標準）→ 正向偏移

**實作公式**

```python
# ── Nacelle Wind Vane Transfer Function (#119, IEC 61400-12-2 Annex E) ──
if (is_producing or is_starting) and self.rotor_speed > 1.0 and aero_out.tsr > 1.0:
    vane_bias_deg = math.degrees(ct_clip / (2.0 * aero_out.tsr))
else:
    vane_bias_deg = 0.0
vane_bias_deg = max(-8.0, min(8.0, vane_bias_deg))
nac_vane_raw = (wind_direction + vane_bias_deg) % 360.0
```

**修改範圍**

1. `simulator/physics/scada_registry.py`：新增 `WMET_WDirRaw`（REAL32, deg, 0–360, OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WDirRaw`）
2. `simulator/physics/turbine_physics.py`：
   - `step()` 內新增 8 行 WVTF 計算區塊（重用 `ct_clip` 與 `aero_out.tsr`，無新計算成本）
   - 輸出字典加入 `"WMET_WDirRaw": round(nac_vane_raw, 2)`

**驗證結果**

`/tmp/test_wvtf.py`：

| 案例 | V_∞ 風向 | Ct | λ | bias | V_raw 風向 | 期望範圍 |
|------|---------|-----|----|------|-----------|----------|
| 停機 (rotor=0) | 90° | 0.00 | — | +0.00° | 90.00° | 0° ✓ |
| 啟動 (low Ct) | 90° | 0.55 | 6 | +2.63° | 92.63° | +2.50..+2.70° ✓ |
| Region 2 峰值 Cp | 90° | 0.82 | 7 | +3.36° | 93.36° | +3.30..+3.50° ✓ |
| Region 2.5 過渡 | 90° | 0.65 | 6 | +3.10° | 93.10° | +3.00..+3.20° ✓ |
| Region 3 變槳 | 90° | 0.30 | 5 | +1.72° | 91.72° | +1.65..+1.85° ✓ |
| 切出後 | 90° | 0.00 | — | +0.00° | 90.00° | 0° ✓ |
| 極端 Ct (clamp) | 90° | 0.95 | 4 | +6.80° | 96.80° | +6.70..+6.90° ✓ |
| 極低 TSR | 90° | 0.85 | 0.5 | +0.00° | 90.00° | 0° (clamp guard) ✓ |
| 360° 環繞 | 358° | 0.82 | 7 | +3.36° | 1.36° | wrap-around ✓ |

單調性測試：
- Ct↑ → bias↑（λ=7 固定）：[0.82, 1.64, 2.46, 3.27, 3.89]° ✓
- λ↑ → bias↓（Ct=0.82 固定）：[7.83, 4.70, 3.36, 2.61, 2.14]° ✓

**為何是物理「因」而非輸出端修正**

- `Ct, λ → a' → θ_s` 的關係源自 Euler turbine equation 與 BEM 理論的根本物理
- 重用既有 `aero_out.ct` 與 `aero_out.tsr`（`turbine_physics.py:394` 已計算），不新增 RNG mutation 或副狀態
- 不改動 `WMET_WDirAbs`，保持向後相容（`wind_field.py` 上游尾流索引、`yaw_model.py` 控制誤差、前端風玫瑰、既有 `data_quality_analysis.py` 皆不受影響）
- WVTF 為純無狀態縮放，每步重新計算，不堆積誤差
- 與 #117 NTF 形成完整的 IEC 61400-12-1/2 機艙感測器轉換函數鏈（兩者皆重用 `aero_out.ct`）

**預期下游應用**

- `WMET_WDirRaw − WMET_WDirAbs` 的時序差可作為「轉子載荷狀態」的另一個觀察通道（Region 2 偏差最大、Region 3 偏差小）
- 配合 `WYAW_YwVn1AlgnAvg5s` 「真實對齊誤差」與 `WMET_WDirRaw - yaw_angle` （vane 觀察的 misalignment），可重現工業界「vane miscalibration → 系統性偏航誤差」的失效模式
- 為未來「vane 校正異常」故障場景（#51 RAG 警報處理）建立物理基礎
- IEC 61400-12-2 機艙風向計研究：可應用反向 WVTF 從 `WMET_WDirRaw` 反推自由流方向，與真實風場 nacelle vane 校正流程一致

**與其他模型的關係**

- `power_curve.py`：直接重用 `aero_out.ct` 與 `aero_out.tsr`，無重複計算
- `turbine_physics.py::_calc_pitch`：Region 3 變槳出力下降 → Ct 降低 → bias 下降（自然連續）
- `yaw_model.py`：**不變動**，仍用自由流 `wind_direction` 計算控制誤差（保持向後相容）
- `wind_field.py`：**不變動**，上游尾流索引仍用自由流方向
- `scada_registry.py`：保持 SCADA 命名與 OPC namespace 一致（Bachmann Z72 規範）
- 與 #117 NTF 配對形成完整 IEC 61400-12-1/2 機艙感測器物理鏈（雙感測器同步暴露 raw 讀值）

## 建議行動

1. **物理鏈路下一步**：`#119` 完成 IEC 61400-12-1/2 雙感測器轉換函數鏈後，可繼續往「次發物理鏈」探索：
   - **低空噴流 (Low-Level Jet)**：Taiwan 離岸風場常見現象，與 #99 大氣穩定度耦合，影響夜間風切剖面與發電量
   - **大氣穩定度 × Reynolds 應力剖面**：垂直 momentum flux 補完 ABL 鏈
   - **Coriolis 旋轉效應**：地球自轉影響超長時間尺度（與 #115 L_u 在不同時間尺度互補）
   - **波浪載荷耦合 (offshore-specific)**：浪向與風向不同步時的塔基 6-DOF 載荷，與 #62 塔架動態響應銜接
   - **血洞效應 (rotor-tower interaction)**：與 #69 tower shadow 相連的塔架擺動 → 葉片靠近時的氣動衝擊
2. **測試基礎建設（#52）**：本次 `/tmp/test_wvtf.py` 已可作為 `tests/physics/test_wvtf.py` 的 pytest 起點，搭配 #117 NTF 自測完成後可一併涵蓋 #99 / #109 / #111 / #113 / #115 / #117 / #119 七個物理路徑。
3. **前端 RUL 視覺化（#57）**：後端 alarm/RUL 已完成，前端可開始實作（與物理優先序低，但用戶可見）。
