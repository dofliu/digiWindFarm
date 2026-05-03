# digiWindFarm Daily Report

> 最後更新：2026-05-01（分支 `claude/keen-hopper-dAj1l`）

## 今日 Commit 摘要

本次日報工作（分支 `claude/keen-hopper-dAj1l`）：

- [c5f4347] feat: Glauert yaw-skew correction on NTF + WVTF (#125)
  - 將 Glauert (1935) / Coleman 偏航斜流修正套用至 #117 NTF 與 #119 WVTF
  - 軸向誘導 `a_skew = a · cos²(γ)`、旋轉尾流投影 `θ_swirl_eff = (Ct/(2λ)) · cos(γ)`
  - γ clamp 至 ±45°，單一共用 cos(γ) 因子（零額外計算成本）
  - 同步清除 #119 合併殘留的 `WMET_WDirRaw` 重複 key（F601）

歷史延續（前 48 小時）：

- [62115d9] Merge PR #124 — 機艙風向計 WVTF (#119)
- [c6df8b0] feat: add nacelle wind vane transfer function (WVTF, IEC 61400-12-2 Annex E)
- [3da3eb6] docs: sync project docs and daily report for WVTF (#119)
- [73343cf] feat: add nacelle wind vane transfer function (WVTF) (#119)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 實作完成 | #125 | NTF/WVTF 在偏航誤差下的 Glauert 偏航斜流修正 | 已於 `turbine_physics.py::step()` 內加入共用 `cos(γ)` 因子，套用至 NTF + WVTF；同步清除 #119 殘留的 `WMET_WDirRaw` 重複 key；9/9 物理自測 PASS；待 PR 合併後關閉 |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線待做 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做（BPFO/BPFI、邊帶、峰值因子/峭度警報已完成） |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest，本次新增 `/tmp/test_overspeeding.py` 可作為 #127 物理鏈共用 pytest 起點 |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 179 個錯誤 | 核心模組仍為 **0 錯誤** |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日**未建立新 issue**（#125 由前一輪日報工作流建立），符合「每次最多 3 個新 issue / 1 個 PR」規則。本次工作主要驅動方向為**處理已建立的 #125 並清除其指出的 lint 缺陷**，未新增 PR（用戶未要求）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #125 | NTF/WVTF Glauert 偏航斜流修正 | enhancement, physics, auto-detected | 2026-04-30 | **已實作於本分支**，待 PR 合併 |
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
| `simulator/physics/turbine_physics.py` | 2026-05-01 | 0 | 無測試套件 | `step()` 內 #117/#119 區塊前新增 5 行共用 Glauert cos(γ) 計算；NTF 公式加入 `cos²(γ)`、WVTF 公式加入 `cos(γ)`；移除輸出 dict 內重複的 `WMET_WDirRaw` |
| `simulator/physics/scada_registry.py` | 2026-05-01 | 0 | 無測試套件 | 移除重複的 `WMET_WDirRaw` ScadaTag 定義（保留行 151 的原始定義） |
| `simulator/physics/wind_field.py` | 2026-04-27 | 0 | 無測試套件 | 無變更 |
| `simulator/engine.py` | 2026-04-27 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/power_curve.py` | 2026-04-25 | 0 | 無測試套件 | 無變更（提供 `aero_out.tsr` / `aero_out.ct` 供 #125 共用） |
| `simulator/physics/yaw_model.py` | 2026-04-17 | 0 | 無測試套件 | 無變更（提供 `yaw_out["yaw_error"]` 供 #125 讀取） |
| `simulator/physics/fatigue_model.py` | 2026-04-22 | 0 | 無測試套件 | 無變更 |
| `wind_model.py`（根目錄） | 2026-04-24 | 0 | 無測試套件 | 無變更 |
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |

## API Endpoints

共 60 個 HTTP 路由 + 1 WebSocket。本日無新增路由。詳見 `README.md` 「Core APIs」章節。

## 程式碼品質

- Lint 錯誤：核心模組 `server/` + `simulator/` + `wind_model.py` = **0**
- `ruff check simulator/ server/ wind_model.py` — `All checks passed!`（修正前有 1 個 F601 重複 key 錯誤，本次連同 #125 實作一起清除）
- `python -m py_compile simulator/physics/turbine_physics.py simulator/physics/scada_registry.py` — 通過
- 物理單元自測（`/tmp/test_glauert_yaw_skew.py`）— **9 / 9 PASS**：
  - 基準（γ=0°, Region 2, Ct=0.82, λ=7）：NTF=0.8417, bias=3.36°（完整重現 #117/#119）✓
  - γ=15°（cos²=0.933, cos=0.966）：NTF=0.8523, bias=3.24°（誘導減量縮 6.7%、bias 縮 3.4%）✓
  - γ=30°（cos²=0.75, cos=0.866）：NTF=0.8813, bias=2.91° ✓
  - γ=45°（cos²=0.5, cos=0.707）：NTF=0.9208, bias=2.37° ✓
  - γ=60° clamp 至 ±45°：NTF 與 γ=45° 完全相同 ✓
  - 對稱性 γ=±15°：NTF 與 bias 量值一致（cos² 與 cos 對 ± 對稱）✓
  - Region 3 γ=0° vs γ=15°：NTF 0.9551→0.9581（向 1.0 收斂），bias 1.72°→1.66° ✓
  - 停機（rpm=0）γ=30°：NTF=1.04（鈍體加速）, bias=0°（無偏航效應）✓
  - 單調性：NTF(γ) 隨 |γ|↑ 單調趨近 1.0（[0.8417, 0.8429, ..., 0.9208]）✓
- 引擎端到端 smoke test：**未執行**（本環境未安裝 numpy；獨立物理單元測試已驗證 #125 邏輯）
- Broken imports：0
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52；本次自測腳本可移入 `tests/physics/test_glauert_yaw.py` 作為 pytest 起點
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 物理標籤：**104 個**（#125 不新增標籤）

## 今日新增功能

### NTF + WVTF 在偏航誤差下的 Glauert 偏航斜流修正 — #125

**問題與物理原理**

`#117`（NTF, IEC 61400-12-1 Annex D）與 `#119`（WVTF, IEC 61400-12-2 Annex E）已建立機艙風速計與風向計的轉換函數鏈，但兩者皆以**偏航誤差 γ=0**為前提實作。實際運轉中：

- `yaw_misalignment` 故障會把 γ 拉到 5–25°
- 偏航控制 dead-band（±5°）下，平時也常見 ±5°
- 強陣風 / 風向急轉時瞬時 γ 可達 15°

此時 IEC 61400-12-1/2 校驗實務需要套用 **Glauert 偏航斜流修正**（Glauert 1935 / Coleman skewed-wake）：

| 操作狀態 | γ | cos²(γ) | NTF 縮減量比例 | NTF 因子 | bias 比例 | bias |
|---------|---|---------|--------------|---------|----------|------|
| Region 2 (Ct=0.82, λ=7) | 0° | 1.000 | 100% | 0.842 | 100% | 3.36° |
| Region 2 | ±5° | 0.992 | 99.2% | 0.843 | 99.6% | 3.34° |
| Region 2 | ±15° | 0.933 | 93.3% | 0.852 | 96.6% | 3.24° |
| Region 2 | ±25° | 0.821 | 82.1% | 0.870 | 90.6% | 3.04° |
| Region 2 | ±30° | 0.750 | 75.0% | 0.881 | 86.6% | 2.91° |
| Region 2 | ±45° | 0.500 | 50.0% | 0.921 | 70.7% | 2.37° |

**物理依據**：

1. **NTF 偏航修正**（Glauert 1935 / Burton et al. 2011 §3.10 / Castillo-Negro et al. 2008 Coleman skewed-wake）：

   ```
   a_skew = a · cos²(γ)              ← Glauert combined-momentum 修正
   V_raw  = V_∞ · (1 − k_pos · a_skew) = V_∞ · (1 − 0.55·a·cos²(γ))
   ```

   意義：偏航越大，轉子「擋住」的風越少，NTF 縮減量隨 cos²(γ) 收斂。

2. **WVTF 偏航修正**（Burton 2011 §3.7 + 平面投影幾何）：

   ```
   θ_swirl_eff = (Ct / (2·λ)) · cos(γ)    ← 旋轉尾流向量投影到機艙平面
   ```

   意義：旋轉向量原本垂直於轉子軸，當轉子偏航 γ 後，旋轉平面相對機艙平面傾斜，風向計只讀到投影量。

**實作公式**

```python
# ── Glauert yaw-skew factor (#125) shared by NTF + WVTF ──
yaw_err_deg = max(-45.0, min(45.0, yaw_out["yaw_error"]))
cos_gamma   = math.cos(math.radians(yaw_err_deg))
cos2_gamma  = cos_gamma * cos_gamma

# NTF (#117) — 軸向誘導折減
ntf_factor = 1.0 - 0.55 * induction_a * cos2_gamma   # γ=0° 時退化為 #117 baseline

# WVTF (#119) — 尾流旋轉投影
swirl_rad = (ct_clip / (2.0 * aero_out.tsr)) * cos_gamma   # γ=0° 時退化為 #119 baseline
```

**修改範圍**

1. `simulator/physics/turbine_physics.py`：
   - `step()` 內於 #117/#119 區塊前新增 5 行共用 `cos(γ)` 計算（讀 `yaw_out["yaw_error"]`，clamp ±45°）
   - NTF 公式：`1 - 0.55 * a * cos²(γ)`
   - WVTF 公式：`(Ct/(2λ)) * cos(γ)`
   - 移除輸出 dict 內重複的 `WMET_WDirRaw`（F601 lint 修復，#119 殘留）
2. `simulator/physics/scada_registry.py`：
   - 移除重複的 `WMET_WDirRaw` ScadaTag 定義（保留行 151 原始定義，刪除行 202 重複）
3. SCADA 標籤總數**保持 104 個**

**驗證結果**

`/tmp/test_glauert_yaw_skew.py`（9 / 9 PASS）：

| 案例 | γ | NTF | bias | 驗證 |
|------|---|-----|------|------|
| Region 2 baseline | 0° | 0.8417 | 3.36° | 完整重現 #117/#119 ✓ |
| Region 2 偏航小 | 15° | 0.8523 | 3.24° | NTF↑、bias↓ ✓ |
| Region 2 偏航中 | 30° | 0.8813 | 2.91° | cos²=0.75 對應 ✓ |
| Region 2 偏航大 | 45° | 0.9208 | 2.37° | cos²=0.5 對應 ✓ |
| 過界 clamp | 60°→45° | 0.9208 | 2.37° | 與 45° 完全相同 ✓ |
| 對稱性 | ±15° | 0.8523 | ±3.24° | cos / cos² 都偶函數 ✓ |
| Region 3 γ=15° | — | 0.9581 | 1.66° | 比 γ=0° 更接近 1.0 ✓ |
| 停機 γ=30° | — | 1.0400 | 0.00° | 偏航無效 ✓ |
| 單調性 | 0..45° | ↗ | — | NTF 單調趨近 1.0 ✓ |

**為何是物理「因」而非輸出端修正**

- Glauert (1935) 的 `a_skew = a·cos²(γ)` 來自動量定理在偏航條件下的封閉解
- 平面投影 `θ_swirl_eff = θ_swirl·cos(γ)` 來自旋轉向量在傾斜平面上的幾何投影
- 重用既有 `aero_out.ct` / `aero_out.tsr` / `yaw_out["yaw_error"]`，無新計算成本、無新 RNG mutation
- 不改動 `WMET_WSpeedNac` 或 `WMET_WDirAbs`，保持向後相容（前端風玫瑰、上游 wake 索引、`yaw_model` 控制器邏輯皆不受影響）
- γ=0° 時公式自動退化為 #117/#119 baseline，無破壞性變更

**為何 cos(γ) 一次計算就好**

- NTF 與 WVTF 區塊相鄰（`turbine_physics.py:719–755`）
- 兩個區塊都需要從 `yaw_out["yaw_error"]` 取 γ
- 兩者都在同一個 `step()` 內計算
- → 共用一個 `cos_gamma`/`cos2_gamma` 變數，零額外計算成本

**與其他模型的關係**

- `power_curve.py`：提供 `aero_out.ct` / `aero_out.tsr` 給 NTF/WVTF/Glauert 共用，無重複計算
- `yaw_model.py`：**不變動**，仍用自由流 `wind_direction` 計算控制誤差（Glauert 修正僅作用於 SCADA 感測器讀值）
- `fault_engine.py`：`yaw_misalignment` 故障在 γ=15–25° 區間時，#125 修正使 `WMET_WSpeedRaw` 偏離 `WMET_WSpeedNac` 的程度減小（與真實儀器物理一致）
- 與 ABL 五項耦合鏈（#99 / #109 / #111 / #113 / #115）：ABL 鏈處理「物理上有什麼風」，#117 / #119 / #125 處理「感測器看到什麼風 + 在不同操作條件下感測器如何看」

**預期下游應用**

- `WMET_WSpeedRaw / WMET_WSpeedNac` 與 `WYAW_YwVn1AlgnAvg5s` 的相關性可作為「偏航品質」的觀察通道
- IEC 61400-12-2 機艙功率曲線驗證在 ±5° dead-band 下更逼真
- 故障診斷：未來「vane 校正異常 → 系統性偏航誤差 → 功率損失」故障場景（#51 RAG 警報處理）建立完整物理基線
- 教學示範：學生可從 SCADA 資料反推「轉子確實處於偏航」的隱性訊號

## 建議行動

1. **物理鏈路下一步**：`#125` 完成 IEC 61400-12-1/2 機艙感測器在偏航條件下的閉合，可繼續：
   - 低空噴流 (Low-Level Jet, LLJ)：Taiwan 離岸風場常見現象，與 #99 穩定度耦合，影響 hub-height 風速 + 風切剖面 + 疲勞 DEL
   - 大氣穩定度 × Coriolis 旋轉（地球自轉效應，影響超長時間尺度風向漂移）
   - 大氣穩定度 × Reynolds 應力剖面（垂直 momentum flux，影響近地層）
   - 海面波浪 × 風速耦合（離岸場景：風浪互動、海面粗糙度動態變化 z₀(U)）
   - 氣動彈性簡化 BEM 葉素動量法（取代目前 Cp(λ,β) 解析面）
   - 風速計 1P/3P 高頻擾動（葉片通過機艙頂部的機械擾動）— 補完 #117 的時間域訊號真實性
2. **測試基礎建設（#52）**：本次 `/tmp/test_glauert_yaw_skew.py` 配合上一輪的 `/tmp/test_ntf.py` / `/tmp/test_wvtf.py` 已具備三個 IEC 61400-12-1/2 物理單元測試，可一併移入 `tests/physics/` 作為 pytest 起點，再涵蓋 #99 / #109 / #111 / #113 / #115 / #117 / #119 / #125 共八個物理路徑。
3. **前端 RUL 視覺化（#57）**：後端 alarm/RUL 已完成，前端可開始實作（與物理優先序低，但用戶可見）。
