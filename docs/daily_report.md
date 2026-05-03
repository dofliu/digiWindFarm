# digiWindFarm Daily Report

> 最後更新：2026-04-30（分支 `claude/keen-hopper-ij4mw`）

## 今日 Commit 摘要

本次日報工作（分支 `claude/keen-hopper-ij4mw`）：

- feat: yaw-skew Glauert correction for NTF + WVTF (#125)
- fix: remove duplicate `WMET_WDirRaw` registration left by #119 merge
- docs: sync CLAUDE / README / TODO / physics_model_status / daily_report for #125

近 14 日已合併進 main 的代表性 commit：

| Hash | 訊息 |
|------|------|
| `c6df8b0` | feat: add nacelle wind vane transfer function (WVTF, IEC 61400-12-2 Annex E) (#119) |
| `76fdc95` | feat: add nacelle anemometer transfer function (NTF) (#117) |
| `7f28657` | feat: couple atmospheric stability to turbulence integral length scale L_u (#115) |
| `e47bd1d` | feat: couple atmospheric stability to wake meander timescale τ_m (#113) |
| `5e9c2b2` | feat: couple atmospheric stability to wind veer (Ekman) (#111) |
| `8223232` | feat: couple atmospheric stability to Bastankhah wake expansion k* (#109) |
| `4b78380` | feat: couple ambient pressure to synoptic weather state (#106) |
| `590c2d7` | feat: add wake-added turbulence intensity (Crespo-Hernández) (#103) |

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立 | #125 | 機艙風感測器在偏航誤差下的 Glauert 偏航斜流修正（NTF + WVTF 延伸 #117 / #119） | 本次新建並完成實作於 `turbine_physics.py::step()`（NTF + WVTF 區塊各 2 行）；同時修掉 #119 合併殘留的 `WMET_WDirRaw` 重複鍵；待 PR 合併後關閉 |
| 已合併 | #119 | 機艙風向計轉換函數 WVTF | PR #120 / #122 / #124 已合併進 main |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線待做 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做（BPFO/BPFI、邊帶、峰值因子/峭度警報已完成） |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest，本次新增 `/tmp/test_glauert_yaw.py` 可作為 #117/#119/#125 物理鏈共用 pytest 起點 |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 179 個錯誤 | 核心模組仍為 **0 錯誤** |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日**新建 1 個 issue（#125）**，符合「每次最多 3 個新 issue / 1 個 PR」規則；實作隨 issue 同步完成，未開 PR（用戶未要求；遵守「Do NOT create a pull request unless the user explicitly asks for one」）。所有變更已提交 push 至 `claude/keen-hopper-ij4mw`。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #125 | 機艙風感測器偏航斜流修正 (NTF + WVTF) | enhancement, physics, auto-detected | 2026-04-30 | **已實作於本分支** |
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
| `simulator/physics/turbine_physics.py` | 2026-04-30 | 0 | 無測試套件 | NTF 區塊新增 Glauert `a·cos²(γ)`；WVTF 區塊新增 `θ_s·cos(γ)`；皆重用 `yaw_out["yaw_error"]`，零額外計算成本；同步移除重複的 `WMET_WDirRaw` 字典鍵 |
| `simulator/physics/scada_registry.py` | 2026-04-30 | 0 | 無測試套件 | 移除 `_TAGS` 中重複的 `WMET_WDirRaw` 註冊（保留與 `WMET_WSpeedRaw` 並列、含 IEC 61400-12-2 Annex E 描述的版本）；110 個 registry 條目（104 個 physics tag）未變動 |
| `simulator/physics/wind_field.py` | 2026-04-27 | 0 | 無測試套件 | 無變更 |
| `simulator/engine.py` | 2026-04-27 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/power_curve.py` | 2026-04-25 | 0 | 無測試套件 | 無變更（提供 `aero_out.ct` / `aero_out.tsr`） |
| `simulator/physics/yaw_model.py` | 2026-04-22 | 0 | 無測試套件 | 無變更（提供 `yaw_out["yaw_error"]`） |
| `simulator/physics/fatigue_model.py` | 2026-04-22 | 0 | 無測試套件 | 無變更 |
| `wind_model.py`（根目錄） | 2026-04-24 | 0 | 無測試套件 | 無變更 |
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |

## API Endpoints

共 60 個 HTTP 路由 + 1 WebSocket。本日無新增路由。詳見 `README.md` 「Core APIs」章節。

## 程式碼品質

- Lint 錯誤：核心模組 `server/` + `simulator/` + `wind_model.py` = **0**（修復前為 1 × F601）
- `ruff check simulator/ server/ wind_model.py` — `All checks passed!`
- `python -m py_compile simulator/physics/turbine_physics.py simulator/physics/scada_registry.py` — 通過
- 修復前 `ruff` 偵測到的 `F601 Dictionary key literal "WMET_WDirRaw" repeated`（#119 合併殘留），本次一併清除
- SCADA registry 完整性檢查：110 個條目、110 個唯一 ID、`WMET_WDirRaw` 與 `WMET_WSpeedRaw` 各保留一筆 — 通過
- 物理單元自測（`/tmp/test_yaw_skew_ntf_wvtf.py`）— **14 / 14 PASS**：
  - NTF γ=0° baseline → 0.842（與 #117 完全一致）
  - NTF γ=15° → 0.852（縮減量 ×0.933 = cos²(15°)）
  - NTF γ=30° → 0.881（縮減量 ×0.75）
  - NTF γ=45° → 0.921（縮減量 ×0.5，半折）
  - 停機轉子 NTF=1.04（不受 γ 影響）
  - WVTF γ=0° baseline → +3.36°（與 #119 完全一致）
  - WVTF γ=15° → +3.24°（縮減 ×0.966）
  - WVTF γ=30° → +2.91°（縮減 ×0.866）
  - NTF γ symmetry：f(−15°)=f(+15°)（cos² 偶函數）
  - NTF γ clamp ±45°：f(60°)=f(45°)
  - Region 3 / γ=15°：絕對縮減量小於 Region 2（Ct 較小）
  - NTF 單調性：γ↑ → 修正量↓（0.842 → 0.846 → 0.860 → 0.881 → 0.907）
  - WVTF 單調性：γ↑ → bias↓（3.36 → 3.30 → 3.15 → 2.91 → 2.57°）

## 物理改善亮點（#125）

**問題**：#117 NTF 和 #119 WVTF 都假設偏航誤差 γ=0，但實際運轉中：
- 偏航控制 dead-band（±5°）下平時就有 ±5° 誤差
- `yaw_misalignment` 故障可拉到 15–25°
- 強陣風 / 風向急轉時瞬時 γ 可達 15°

**解法**：套用 Glauert 結合動量理論 / Coleman 斜尾流修正
- NTF：`V_raw = V_∞·(1 − 0.55·a·cos²(γ))`
- WVTF：`θ_s_eff = (Ct/(2·λ))·cos(γ)`
- γ 截斷在 ±45°（cos 法則在小到中偏航範圍內準確）
- 重用 `yaw_out["yaw_error"]`（已包含故障注入與感測器偏置）
- 零額外計算、零新 RNG、零新狀態變數、零新 SCADA 標籤

**影響**：
- `yaw_misalignment` 故障場景下，`WMET_WSpeedRaw` 會逐漸接近自由流 `WMET_WSpeedNac`（轉子「擋住」的越少）
- `WMET_WDirRaw - WMET_WDirAbs`（旋轉偏差）會隨 γ 增加而縮小
- 完成 IEC 61400-12-1/2 機艙感測器轉換函數鏈在偏航條件下的閉合
- 為 #51（RAG 警報分析）的「風向計校準漂移 → 偏航失準 → 功率損失」故障場景建立物理基線

**參考文獻**：
- IEC 61400-12-1 ed.2 Annex D（NTF）
- IEC 61400-12-2 ed.1 Annex E（WVTF）
- Glauert (1935) "Airplane Propellers" in *Aerodynamic Theory* (Durand) §VII
- Burton, Sharpe, Jenkins, Bossanyi (2011) *Wind Energy Handbook* 2nd ed. §3.7, §3.10
- Castillo-Negro et al. (2008) — Coleman skewed wake correction

## 建議行動

1. **frontend RUL 視覺化（#57）**：後端的 4 級警報（notice/warning/danger/shutdown）與 RUL 估算已完成，前端 Load/Fatigue 分頁需新增 RUL 與警報等級顯示。優先度：中。
2. **頻譜警報曲線（#58）**：BPFO/BPFI、邊帶、峰值因子/峭度警報均完成，剩下頻帶相依的動態警報曲線（前端顯示用）。優先度：中。
3. **自動化測試套件（#52）**：物理模型已累積 26 個物理改善（#61 → #125），但全無 pytest 覆蓋。建議先建 `tests/test_physics/` 為 NTF / WVTF / Bastankhah / 大氣穩定度等核心邏輯加 unit test。優先度：高（規模成長後回歸風險高）。
4. **依賴安全升級（#48）**：cryptography / pyjwt / setuptools 等 17 個 CVE 仍未升級。優先度：低（lab-internal）但建議在實驗前處理。
5. **物理模型下一步**：可考慮的方向（按物理影響大小排序）
   - 葉片振動模態 SDOF（first edgewise / first flapwise）— 補完 BEM/aeroelastic 缺口
   - 發電機銅損溫度耦合（R(T) = R₀·(1 + α·ΔT)，α≈0.00393 for Cu）— 與已建立的 `gen_winding_temp` 直接耦合
   - 變槳油壓低溫黏度模型 — 補完冷啟動行為，與 `gearbox_overheat` / 故障場景銜接
