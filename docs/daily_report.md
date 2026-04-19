# digiWindFarm Daily Report

> 最後更新：2026-04-19

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-ZWcLi`）：
- feat: add ambient humidity air-cooling model (moist-air density + dew-point condensation) — 對應 #89

過去 24 小時主要合併/提交：
- [6c79117] Merge PR #88 — 齒輪齒面接觸（#76，接觸比嚙合剛度漣波 + 齒面磨耗指數）
- [0971e0a] feat: add gear tooth contact model with mesh stiffness ripple and wear index (#76)
- [811f689] Merge PR #87 — 風向隨高度偏轉（#79，Ekman 螺旋）
- [bf933de] docs: update daily report and project docs for 2026-04-17 fourth run
- [1266ec3] feat: add wind veer model with Ekman spiral blade direction offset (#79)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 關閉 | #89 | 環境濕度影響空氣冷卻效率 | 已實作：`get_ambient_humidity` 季節/晝夜曲線、密度因子、露點冷凝懲罰、`WMET_HumOutside` 標籤 |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 115 個錯誤 | 核心模組 0 錯誤 |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日未建立新 issue（本日實作並關閉 #89，其他 open issues 已涵蓋待辦項目，符合「每次最多 3 個新 issue」規則）。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | 電壓-時間曲線 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 前端 RUL 待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #44 | Ruff lint 115 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組 0 錯誤 |
| #26 | 部署強化 | enhancement, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/` | 2026-04-19 | 0 | 無測試套件 | `engine.py` 增加 humidity 傳入 |
| `simulator/physics/` | 2026-04-19 | 0 | 無測試套件 | `cooling_model`、`turbine_physics`、`scada_registry` 新增濕度耦合（#89） |
| `wind_model.py`（根目錄） | 2026-04-19 | 0 | 無測試套件 | 新增 `get_ambient_humidity` |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案 |

## API Endpoints

共 58 個路由（57 HTTP + 1 WebSocket）。無新增路由，狀態與昨日相同。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（4 個路由）仍未同步至 README 的 Core APIs 章節。

## 程式碼品質

- Lint 錯誤：115（核心模組 `server/` + `simulator/` 維持 0 錯誤，剩餘皆在 `opc_bachmann/` 和根目錄原型檔案）
- `ruff check simulator/ server/ wind_model.py` — All checks passed ✓
- `python -m py_compile wind_model.py simulator/engine.py simulator/physics/{cooling_model,turbine_physics,scada_registry}.py` — 5 個修改檔案全部通過
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：**93 個**（+1：`WMET_HumOutside`）

## 今日新增功能

### 環境濕度對空氣冷卻效率之影響（#89）

**物理原理**

1. **濕空氣密度衰減**：水蒸氣分子量（18）低於乾空氣（29），高濕度降低空氣密度 → 風扇質量流量與對流散熱係數下降。
2. **露點鄰近（condensation risk）**：若機櫃/鰭片表面溫度接近露點，水氣會在散熱鰭片上冷凝，造成：
   - 冷凝熱佔據部分散熱能力
   - 積水阻礙對流
   - 長期會引發電氣腐蝕

**實作方式**

1. `wind_model.py`：新增 `get_ambient_humidity(timestamp)`
   - 季節基線 68–85%（東亞/離岸風場雨季偏高）
   - 晝夜週期（凌晨 05:00 附近最高、15:00 附近最低，振幅 ≈±8%）
   - 低壓鋒面加成 +10%（weather system pressure_state 耦合）
   - 手動 override 模式固定 65% ± 1%（避免示範期間意外抖動）
2. `simulator/engine.py`：每步呼叫 `wind_model.get_ambient_humidity` 並傳入 `turbine.step`
3. `simulator/physics/turbine_physics.py`：
   - `step()` 新增 `ambient_humidity_pct=65.0` kwarg
   - 傳入 `CoolingSystem.step`
   - 輸出 `WMET_HumOutside` SCADA 標籤
4. `simulator/physics/cooling_model.py`：
   - `CoolingSystem.step` 新增 `ambient_humidity_pct` 參數
   - 密度因子：`density = max(0.965, 1 − 0.0007 × max(0, RH − 50))`
   - 露點：`T_d ≈ T − (100 − RH)/5`（Magnus 近似）
   - 冷凝因子：`cond = max(0.94, 1 − max(0, 5 − (T − T_d)) × 0.01)`
   - `humidity_factor = density × cond`，套用至 `nacelle_fan_eff`、`cabinet_fan_eff`（水冷迴路不受影響，水的質量流量由泵決定）
   - 新增 `last_humidity_factor`、`last_ambient_humidity` property 供 SCADA/診斷使用
   - `get_status()` 擴充 `ambient_humidity_pct` 與 `humidity_factor`
5. `simulator/physics/scada_registry.py`：新增 `WMET_HumOutside`（REAL32, %, 0–100, 室外相對濕度）

**物理效應（自測驗證，對照 issue 規格表）**

| 條件 | humidity_factor | 冷卻減損 |
|------|-----------------|----------|
| 25 °C, 20% RH（乾冷） | 1.0000 | 0.00% |
| 25 °C, 70% RH | 0.9860 | 1.40% |
| 25 °C, 90% RH | 0.9428 | 5.72% |
| 25 °C, 100% RH | 0.9167 | 8.33%（下限） |
| 32 °C, 95% RH（熱帶雨季） | 0.9298 | 7.02% |
| 5 °C, 98% RH（寒冬高濕） | 0.9219 | 7.81%（接近冷凝下限） |

**影響範圍**

- `WMET_HumOutside` trend 可於歷史圖表觀察（季節/晝夜/鋒面模式）
- 高濕度時段 `WNAC_NacTmp`、`WNAC_NacCabTmp` 會較乾燥季節略高約 1–3 °C（雨季 ≈5–8% 空冷下降 → 穩態溫升約 1–2 °C，加上露點冷凝貢獻）
- 水冷（水泵、水冷排、IGCT 水迴路）不受影響 — 這與真實風場熱管理一致
- 為未來 radiator fin model、腐蝕偵測、冷凝警報提供前置 humidity 資料路徑
- 後續 #58 頻譜警報曲線可將高濕季節與軸承水氣侵入做關聯分析

## 建議行動

1. **整合測試 #89**：建議在 `examples/data_quality_analysis.py` 追加高/低濕度對比模擬（例：1 月乾燥 vs 6 月雨季），驗證雨季 `WNAC_NacTmp` 確實略高。
2. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值（目前已有 ISO 10816 分區但未以曲線形式顯示）。
3. **實作 #57 前端 RUL 視覺化**：後端已就緒，前端 Load/Fatigue 分頁補 RUL 顯示。
4. **同步 `/api/farms` 4 個路由至 README.md**：昨日建議仍未完成。
5. **建立測試套件（#52）**：本日新增的 density/condensation 計算具明確數值預期，適合做為物理模型 pytest 的第一個案例。
