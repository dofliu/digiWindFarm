# digiWindFarm Daily Report

> 最後更新：2026-04-29（分支 `claude/keen-hopper-hAVhB`）

## 今日 Commit 摘要

本次日報工作（分支 `claude/keen-hopper-hAVhB`）：

- feat: implement nacelle wind vane transfer function (#119)
- docs: sync CLAUDE / README / TODO / physics_model_status / daily_report for #119

## 今日 Commit 摘要

本次日報工作（分支 `claude/keen-hopper-un7sb`）：

- [404f200] feat: add nacelle wind vane transfer function (WVTF) (#119)
> 最後更新：2026-04-29（分支 `claude/keen-hopper-882Ou`）

## 今日 Commit 摘要

本次日報工作（分支 `claude/keen-hopper-882Ou`）：

- feat: add nacelle wind vane transfer function (WVTF) (#119)

- [5541796] Merge PR #118 — 機艙風速感測器轉換函數 NTF (#117)
- [76fdc95] feat: add nacelle anemometer transfer function (NTF) (#117)
- [6b03437] Merge PR #116 — 大氣穩定度 × 湍流積分長度尺度 L_u 耦合 (#115)
- [7f28657] feat: couple atmospheric stability to turbulence integral length scale L_u (#115)
- [1478408] Merge PR #114 — 大氣穩定度 × 動態尾流蜿蜒 τ_m 耦合 (#113)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 實作中 | #119 | 機艙風向計轉換函數 (WVTF, IEC 61400-12-2 Annex E) | 昨日由系統建立並備妥詳細實作計畫；本次完成實作於 `turbine_physics.py::step()` + `scada_registry.py`，新增 SCADA 標籤 `WMET_WDirRaw`；待 PR 合併後關閉 |
| 已關閉 | #117 | 機艙風速感測器 NTF | PR #118 已合併進 main |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線待做 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 179 個錯誤 | 核心模組現為 **0 錯誤** |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日**未建立新 issue**（#119 由昨日工作流建立），符合「每次最多 3 個新 issue / 1 個 PR」規則；實作後尚未關閉（待 PR 合併後關閉）。未開 PR（用戶未要求；遵守提示「Do NOT create a pull request unless the user explicitly asks for one」）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #119 | 機艙風向計 WVTF (IEC 61400-12-2 Annex E) | enhancement, physics, auto-detected | 2026-04-27 | **已實作於本分支** |
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
| `simulator/physics/turbine_physics.py` | 2026-04-29 | 0 | 無測試套件 | `step()` 內加入 WVTF 區塊（11 行）；新增 `WMET_WDirRaw` 輸出；重用 `aero_out.ct + aero_out.tsr`，無新計算負擔 |
| `simulator/physics/scada_registry.py` | 2026-04-29 | 0 | 無測試套件 | 新增 `WMET_WDirRaw` ScadaTag（REAL32, deg, 0–360），SCADA 物理標籤從 103 → **104** |
| `simulator/physics/wind_field.py` | 2026-04-27 | 0 | 無測試套件 | 無變更（沿用 #117） |
| `simulator/engine.py` | 2026-04-27 | 0 | 無測試套件 | 無變更（沿用 #117） |
| `simulator/physics/power_curve.py` | 2026-04-25 | 0 | 無測試套件 | 無變更（提供 `aero_out.tsr` 給 WVTF 直接重用） |
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
- 物理單元自測（`/tmp/test_wvtf.py`）— **8 / 8 PASS + Ct/λ 雙向單調性 ✓**：
  - 停機（rotor=0 RPM, Ct=0）：bias=0.00°（無轉子尾流旋轉）✓
  - 切出（V>25 m/s, 停機, Ct=0）：bias=0.00° ✓
  - 啟動（is_starting, Ct=0.55, λ=6, 10 RPM）：bias=2.63°（介於 2.40–2.80）✓
  - Region 2 峰值 Cp（Ct=0.82, λ=7）：bias=3.36°（≈ +3.4°）✓
  - Region 2.5 過渡（Ct=0.65, λ=6）：bias=3.10°（≈ +3.1°）✓
  - Region 3 變槳（Ct=0.30, λ=5）：bias=1.72°（≈ +1.7°）✓
  - 360° 環繞（358° + 3.36° → 1.36°）✓
  - 極端 Ct=0.95/λ=2（觸發 ±8° clamp）：bias=8.00° ✓
  - 單調性 Ct↑ → bias↑（fixed λ=6）：[0.00, 0.95, 1.91, 2.86, 3.82, 4.54]° ✓
  - 反向單調性 λ↑ → bias↓（fixed Ct=0.82）：[7.83, 4.70, 3.36, 2.61, 2.14]° ✓
- 引擎端到端 smoke test：**未執行**（本環境未安裝 numpy；獨立物理單元測試已驗證 WVTF 邏輯）
- Broken imports：0
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52；本次自測腳本可移入 `tests/physics/test_wvtf.py` 作為 pytest 起點
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 物理標籤：**104 個**（#119 新增 `WMET_WDirRaw`）

## 今日新增功能

### 機艙風向計轉換函數 (WVTF, IEC 61400-12-2 Annex E) — #119

**問題與物理原理**

`simulator/physics/turbine_physics.py:764` 將 SCADA 標籤 `WMET_WDirAbs` 直接設為模型內部使用的自由流風向：

```python
"WMET_WDirAbs": round(wind_direction % 360, 2),
```

但 `wind_direction` 是**自由流風向**（free-stream），用於 wake 模型上游索引與 `yaw_model.py` 控制器誤差計算。真實機艙頂部安裝的風向計與 #117 風速計同位於**轉子下游 1.5R**，會吃到**轉子尾流旋轉（rotor wake swirl）**，產生系統性方向偏差——這是 IEC 61400-12-2 Annex E 明定要校正的「nacelle wind vane bias」。

| 操作狀態 | Ct 範圍 | λ 範圍 | θ_s ≈ Ct/(2λ) | 機艙 vane 讀值 |
|---------|---------|--------|---------------|---------------|
| 停機 / 鎖定 | 0 | — | 0° | = 自由流方向 |
| 啟動（low Ct） | 0.55 | 6 | 0.046 rad ≈ 2.6° | +2.6° |
| Region 2（峰值 Cp） | 0.82 | 7 | 0.059 rad ≈ 3.4° | +3.4° |
| Region 2.5（過渡） | 0.65 | 6 | 0.054 rad ≈ 3.1° | +3.1° |
| Region 3（變槳） | 0.30 | 5 | 0.030 rad ≈ 1.7° | +1.7° |
| 切出後 | 0 | — | 0° | = 自由流方向 |

**物理依據**：角動量守恆（Euler turbine equation）

- 葉輪將線性風 → 線性 + 旋轉流場
- 切向誘導因子 `a' = Ct / (4·λ)`（blade-element / momentum theory）
- 下游 vane 觀察的 swirl 角 `θ_s ≈ 2·a' = Ct / (2·λ) [rad]`（Burton et al. 2011 §3.7）
- 右手旋（順時針，從上風看下游）為現代風機工業標準 → 下游 vane 讀到正向偏移

**實作公式**

```python
# ── Nacelle Wind Vane Transfer Function (#119, IEC 61400-12-2 Annex E) ──
if (is_producing or is_starting) and self.rotor_speed > 1.0 and aero_out.tsr > 1.0:
    swirl_rad = ct_clip / (2.0 * aero_out.tsr)
    vane_bias_deg = math.degrees(swirl_rad)
else:
    vane_bias_deg = 0.0
vane_bias_deg = max(-8.0, min(8.0, vane_bias_deg))
nac_vane_raw = (wind_direction + vane_bias_deg) % 360.0
```

**修改範圍**

1. `simulator/physics/scada_registry.py`：新增 `WMET_WDirRaw`（REAL32, deg, 0–360, OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WDirRaw`）
2. `simulator/physics/turbine_physics.py`：
   - `step()` 內新增 11 行 WVTF 計算區塊（與 #117 NTF 區塊相鄰，重用既有 `ct_clip` 與 `aero_out.tsr`，無新計算成本）
   - 輸出字典加入 `"WMET_WDirRaw": round(nac_vane_raw, 2)`

**驗證結果**

`/tmp/test_wvtf.py`（8 / 8 PASS + Ct↑→bias↑ + λ↑→bias↓ 雙向單調性）：

| 案例 | 風向 | Ct | λ | bias | V_dir_raw | 期望範圍 |
|------|------|-----|----|------|-----------|----------|
| 停機 (rpm=0) | 180° | 0 | 0 | 0.00° | 180.00° | 0° ✓ |
| 切出 (rpm=0) | 180° | 0 | 0 | 0.00° | 180.00° | 0° ✓ |
| 啟動 (low Ct/λ) | 180° | 0.55 | 6 | 2.63° | 182.63° | 2.4–2.8° ✓ |
| Region 2 峰值 Cp | 180° | 0.82 | 7 | 3.36° | 183.36° | 3.2–3.6° ✓ |
| Region 2.5 過渡 | 180° | 0.65 | 6 | 3.10° | 183.10° | 3.0–3.2° ✓ |
| Region 3 變槳 | 180° | 0.30 | 5 | 1.72° | 181.72° | 1.6–1.9° ✓ |
| 環繞處理 | 358° | 0.82 | 7 | 3.36° | 1.36° | wrap ✓ |
| 極端 Ct (clamp) | 180° | 0.95 | 2 | 8.00° | 188.00° | 8° clamp ✓ |

單調性檢查：

- Ct↑→bias↑（λ=6 固定）：[0.00, 0.95, 1.91, 2.86, 3.82, 4.54]° for Ct ∈ {0.0, 0.2, 0.4, 0.6, 0.8, 0.95} ✓
- λ↑→bias↓（Ct=0.82 固定）：[7.83, 4.70, 3.36, 2.61, 2.14]° for λ ∈ {3, 5, 7, 9, 11} ✓

**為何是物理「因」而非輸出端修正**

- `Ct → a' = Ct/(4λ) → θ_s = 2a' = Ct/(2λ)` 的關係源自角動量守恆（Euler turbine equation）的根本物理
- 重用既有 `aero_out.ct` 與 `aero_out.tsr`（`turbine_physics.py:394` 已計算），不新增 RNG mutation 或副狀態
- 不改動 `WMET_WDirAbs`，保持向後相容（前端風玫瑰、上游 wake 索引、`yaw_model` 控制器邏輯皆不受影響）
- WVTF 為純無狀態縮放，每步重新計算，不堆積誤差
- 與 #117 NTF 配對形成完整的 IEC 61400-12-1/2 機艙感測器轉換函數鏈

**預期下游應用**

- `WMET_WDirRaw vs WMET_WDirAbs` 的差值可作為「轉子載荷狀態」的觀察通道（差值大→Ct 高→出力區）
- IEC 61400-12-2 機艙功率曲線驗證：可應用反向 WVTF 從 `WMET_WDirRaw` 反推自由流風向，與真實風場資料分析流程一致
- 偏航控制研究：未來可用 `WMET_WDirRaw - yaw_angle` 模擬「真實感測器看到的對齊誤差」，重現工業界「vane miscalibration → 系統性偏航誤差」的失效模式
- 故障診斷：為未來「vane 校正異常」故障場景（#51 RAG 警報處理）建立物理基礎

**與其他模型的關係**

- `power_curve.py`：直接重用 `aero_out.ct` 與 `aero_out.tsr`，無重複計算
- `turbine_physics.py::_calc_pitch`：Region 3 變槳出力下降 → Ct 降低 + λ 降低 → bias 趨穩（自然連續）
- `yaw_model.py`：**不變動**，仍用自由流 `wind_direction` 計算控制誤差（保持向後相容）
- `scada_registry.py`：保持 SCADA 命名與 OPC namespace 一致（Bachmann Z72 規範）
- 本 PR 與 ABL 五項耦合鏈（#99 / #109 / #111 / #113 / #115）獨立但互補：ABL 鏈處理「物理上有什麼風」，#117/#119 處理「感測器看到什麼風」

## 建議行動

1. **物理鏈路下一步**：`#119` 完成 IEC 61400-12-1/2 機艙感測器對之後，可繼續：
   - 低空噴流 (Low-Level Jet, LLJ)：Taiwan 離岸風場常見現象，與 #99 穩定度耦合，影響 hub-height 風速 + 風切剖面 + 疲勞 DEL
   - 大氣穩定度 × Coriolis 旋轉（地球自轉效應，影響超長時間尺度風向漂移）
   - 大氣穩定度 × Reynolds 應力剖面（垂直 momentum flux，影響近地層）
   - 海面波浪 × 風速耦合（離岸場景：風浪互動、海面粗糙度動態變化 z₀(U)）
   - 氣動彈性簡化 BEM 葉素動量法（取代目前 Cp(λ,β) 解析面）
2. **測試基礎建設（#52）**：本次 `/tmp/test_wvtf.py` 配合上一輪 `/tmp/test_ntf.py` 已具備兩個 IEC 61400-12-1/2 物理單元測試，可一併移入 `tests/physics/` 作為 pytest 起點，再涵蓋 #99 / #109 / #111 / #113 / #115 / #117 / #119 七個物理路徑。
3. **前端 RUL 視覺化（#57）**：後端 alarm/RUL 已完成，前端可開始實作（與物理優先序低，但用戶可見）。
