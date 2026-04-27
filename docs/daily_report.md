# digiWindFarm Daily Report

> 最後更新：2026-04-27（分支 `claude/keen-hopper-7ZEZ8`）

## 今日 Commit 摘要

本次日報工作（分支 `claude/keen-hopper-7ZEZ8`）：

- feat: implement nacelle anemometer transfer function (#117)
- docs: sync CLAUDE / README / TODO / physics_model_status / daily_report for #117

近 48 小時主幹 `main` 合併摘要：

- [6b03437] Merge PR #116 — 大氣穩定度 × 湍流積分長度尺度 L_u 耦合 (#115)
- [7f28657] feat: couple atmospheric stability to turbulence integral length scale L_u (#115)
- [1478408] Merge PR #114 — 大氣穩定度 × 動態尾流蜿蜒 τ_m 耦合 (#113)
- [e47bd1d] feat: couple atmospheric stability to wake meander timescale τ_m (#113)
- [7dc8c1b] Merge PR #112 — 大氣穩定度 × 風切偏向耦合 (#111)
- [5e9c2b2] feat: couple atmospheric stability to wind veer (Ekman) (#111)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立+實作 | #117 | 機艙風速感測器轉換函數 (NTF, IEC 61400-12-1 Annex D) | 今日 04:30 由本任務建立；本次完成實作於 `turbine_physics.py::step()` + `scada_registry.py`，新增 SCADA 標籤 `WMET_WSpeedRaw` |
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

本日**建立 1 個** issue（#117，IEC 61400-12-1 Annex D NTF），符合「每次最多 3 個新 issue / 1 個 PR」規則；實作後尚未關閉（待 PR 合併後關閉）。未開 PR（用戶未要求；遵守提示「Do NOT create a pull request unless the user explicitly asks for one」）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #117 | 機艙風速感測器 NTF (IEC 61400-12-1 Annex D) | enhancement, physics, auto-detected | 2026-04-27 | **已實作於本分支** |
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
| `simulator/physics/turbine_physics.py` | 2026-04-27 | 0 | 無測試套件 | `step()` 內加入 NTF 區塊（11 行）；新增 `WMET_WSpeedRaw` 輸出 |
| `simulator/physics/scada_registry.py` | 2026-04-27 | 0 | 無測試套件 | 新增 `WMET_WSpeedRaw` ScadaTag（REAL32, m/s, 0–40），SCADA 物理標籤從 102 → **103** |
| `simulator/physics/wind_field.py` | 2026-04-26 | 0 | 無測試套件 | 無變更（沿用 #115） |
| `simulator/engine.py` | 2026-04-26 | 0 | 無測試套件 | 無變更（沿用 #115） |
| `simulator/physics/power_curve.py` | 2026-04-25 | 0 | 無測試套件 | 無變更（提供 `aero_out.ct` 給 NTF 直接重用） |
| `simulator/physics/fatigue_model.py` | 2026-04-22 | 0 | 無測試套件 | 無變更 |
| `wind_model.py`（根目錄） | 2026-04-24 | 0 | 無測試套件 | 無變更 |
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |

## API Endpoints

共 61 個 HTTP 路由 + 1 WebSocket。本日無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（10 個路由）仍未完整同步至 README 的 Core APIs 章節（追蹤項，不阻塞物理模型優先工作）。

## 程式碼品質

- Lint 錯誤：核心模組 `server/` + `simulator/` + `wind_model.py` = **0**
- `ruff check simulator/ server/ wind_model.py` — `All checks passed!`
- `python -m py_compile simulator/physics/turbine_physics.py simulator/physics/scada_registry.py` — 通過
- 物理單元自測（`/tmp/test_ntf.py`）— **7 / 7 PASS + 單調性 ✓**：
  - 停機（rotor=0 RPM, Ct=0）：NTF=1.040（鈍體 +4%）✓
  - 啟動（is_starting, Ct=0.55, 10 RPM）：NTF=0.909（介於 0.90–0.92）✓
  - Region 2 峰值 Cp（Ct=0.82）：NTF=0.842（≈ 0.84·V_∞）✓
  - Region 2.5 過渡（Ct=0.65）：NTF=0.888（≈ 0.89·V_∞）✓
  - Region 3 變槳（Ct=0.30）：NTF=0.955（≈ 0.96·V_∞）✓
  - 切出風速以上（V=27, 停機）：NTF=1.040 ✓
  - 極端 Ct=0.95（觸發 clamp 0.78）：NTF=0.786 ✓
  - 單調性 Ct↑ → NTF↓ ✓
- 引擎端到端 smoke test：**未執行**（本環境未安裝 numpy；獨立物理單元測試已驗證 NTF 邏輯）
- Broken imports：0
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52；本次自測腳本可移入 `tests/physics/test_ntf.py` 作為 pytest 起點
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 物理標籤：**103 個**（#117 新增 `WMET_WSpeedRaw`）

## 今日新增功能

### 機艙風速感測器轉換函數 (NTF, IEC 61400-12-1 Annex D) — #117

**問題與物理原理**

`simulator/physics/turbine_physics.py:748` 將 SCADA 標籤 `WMET_WSpeedNac` 直接設為模型內部使用的 `effective_wind_speed`：

```python
"WMET_WSpeedNac": round(effective_wind_speed, 2),
```

但 `effective_wind_speed` 是**自由流風速**（free-stream），用於 `Cp(λ,β)` / `Ct(λ,β)` 等氣動計算。真實機艙頂部安裝的杯式或超音波風速計位於**轉子下游 1–3 m**，量測值會系統性低於自由流風速：

| 操作狀態 | Ct 範圍 | 誘導因子 a | NTF 比例 |
|---------|---------|-----------|---------|
| 停機 / 鎖定 | 0 | 0 | 1.02–1.08（鈍體加速） |
| Region 2（峰值 Cp） | 0.78–0.85 | 0.27–0.32 | 0.83–0.87 |
| Region 2.5（過渡） | 0.55–0.75 | 0.16–0.25 | 0.87–0.92 |
| Region 3（變槳） | 0.20–0.40 | 0.06–0.11 | 0.94–0.98 |

**物理依據**：1-D 動量理論
- 軸向誘導因子 `a = 0.5·(1 − √(1 − Ct))`
- 機艙位置權重 `k_pos ≈ 0.55`（風速計在轉子下游約 1.5R）
- NTF 因子 `1 − k_pos·a`

**實作公式**

```python
ct_clip = max(0.0, min(0.95, aero_out.ct))
induction_a = 0.5 * (1.0 - math.sqrt(1.0 - ct_clip)) if ct_clip > 0 else 0.0
if (is_producing or is_starting) and self.rotor_speed > 1.0:
    ntf_factor = 1.0 - 0.55 * induction_a
else:
    ntf_factor = 1.04   # bluff-body speed-up at nacelle top
ntf_factor = max(0.78, min(1.10, ntf_factor))
nac_anem_raw = effective_wind_speed * ntf_factor
```

**修改範圍**

1. `simulator/physics/scada_registry.py`：新增 `WMET_WSpeedRaw`（REAL32, m/s, 0–40, OPC suffix `WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedRaw`）
2. `simulator/physics/turbine_physics.py`：
   - `step()` 內新增 11 行 NTF 計算區塊（重用 `aero_out.ct`，無新計算成本）
   - 輸出字典加入 `"WMET_WSpeedRaw": round(nac_anem_raw, 2)`

**驗證結果**

`/tmp/test_ntf.py`：

| 案例 | V_∞ | Ct | NTF | V_raw | 期望範圍 |
|------|-----|-----|-----|-------|----------|
| 停機 (rotor=0) | 8.0 | 0 | 1.040 | 8.32 | 1.04 ✓ |
| 啟動 (low Ct) | 6.0 | 0.55 | 0.909 | 5.46 | 0.90–0.92 ✓ |
| Region 2 峰值 Cp | 8.0 | 0.82 | 0.842 | 6.73 | 0.84–0.86 ✓ |
| Region 2.5 過渡 | 10.5 | 0.65 | 0.888 | 9.32 | 0.87–0.89 ✓ |
| Region 3 變槳 | 16.0 | 0.30 | 0.955 | 15.28 | 0.94–0.96 ✓ |
| 切出後 | 27.0 | 0 | 1.040 | 28.08 | 1.04 ✓ |
| 極端 Ct (clamp) | 7.0 | 0.95 | 0.786 | 5.51 | 0.78–0.81 ✓ |

單調性 Ct↑ → NTF↓：[1.000, 0.986, 0.955, 0.919, 0.876, 0.832] ✓

**為何是物理「因」而非輸出端修正**

- `Ct → a → V_raw` 的關係源自 1-D 動量理論（Betz）的根本物理
- 重用既有 `aero_out.ct`（`turbine_physics.py:394` 已計算），不新增 RNG mutation 或副狀態
- 不改動 `WMET_WSpeedNac`，保持向後相容（`examples/data_quality_analysis.py`、`server/routers/turbines.py`、`server/opc_adapter.py`、前端趨勢圖、`data_quality_report.txt` 18/21 通過率皆不受影響）
- NTF 為純無狀態縮放，每步重新計算，不堆積誤差

**預期下游應用**

- 散點圖 `WMET_WSpeedRaw vs WTUR_TotPwrAt` 會呈現「向左偏移的功率曲線」——這正是業界以機艙風速計做功率曲線時的真實樣貌
- IEC 61400-12-2 機艙功率曲線驗證：可應用反向 NTF 從 `WMET_WSpeedRaw` 反推自由流風速，與真實風場資料分析流程一致
- 偏航控制研究：未來可用 `WMET_WSpeedRaw` 模擬感測器訊號的尾流偏差
- 故障診斷：`WMET_WSpeedRaw / WMET_WSpeedNac` 比值偏離預期 NTF 曲線可作為「風速計讀值異常」或「Ct 估算異常」的指標

**與其他模型的關係**

- `power_curve.py`：直接重用 `aero_out.ct`，無重複計算
- `turbine_physics.py::_calc_pitch`：Region 3 變槳出力下降 → Ct 降低 → NTF 趨近 1（自然連續）
- `scada_registry.py`：保持 SCADA 命名與 OPC namespace 一致（Bachmann Z72 規範）
- 本 PR 與 ABL 五項耦合鏈（#99 / #109 / #111 / #113 / #115）獨立但互補：ABL 鏈處理「物理上有什麼風」，NTF 處理「感測器看到什麼風」

## 建議行動

1. **物理鏈路下一步**：`#117` 完成「自由流 vs 感測器讀值」差異後，可繼續往「次發物理鏈」探索：
   - 風速計訊號的方向偏差（鼓風機尾流 → 風向計讀值偏移）— 同源於 IEC 61400-12-2
   - 大氣穩定度 × Coriolis 旋轉（地球自轉效應，影響超長時間尺度）
   - 大氣穩定度 × Reynolds 應力剖面（垂直 momentum flux）
   - 低空噴流 (Low-Level Jet)：Taiwan 離岸風場常見現象，與 #99 穩定度耦合
2. **測試基礎建設（#52）**：本次 `/tmp/test_ntf.py` 已可作為 `tests/physics/test_ntf.py` 的 pytest 起點，完成後可一併涵蓋 #99 / #109 / #111 / #113 / #115 / #117 六個物理路徑。
3. **前端 RUL 視覺化（#57）**：後端 alarm/RUL 已完成，前端可開始實作（與物理優先序低，但用戶可見）。
