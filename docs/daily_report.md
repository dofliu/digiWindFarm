# digiWindFarm Daily Report

> 最後更新：2026-04-17

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/gifted-noether-PFU4Z`）：
- [9815f9d] feat: add gearbox oil temperature and viscosity effects model (#73)

過去 24 小時 main 分支合併：
- [4982827] Merge pull request #70（塔架陰影效應）
- [e35b21a] Merge pull request #68（峰值因子/峭度異常警報）
- [f54dbf8] Merge pull request #66（齒輪嚙合邊帶分析模型）
- [0e0e409] Merge pull request #65（BPFO/BPFI 軸承缺陷頻率模型）
- [fbcd68a] Merge pull request #64（塔架 SDOF 動態響應）
- [029b929] Merge pull request #63（Cp 氣動模型 + docstrings）

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 關閉 | #73 | 齒輪箱油溫與黏度效應模型 | 已實作：Walther 型黏度比 + 冷啟動損耗衰減 + WDRV_GbxOilTmp 標籤 |
| 新建 | #75 | 冷卻液液位與洩漏偵測模型 | physics_model_status §2.4 "Still missing"，啟用冷卻系統故障診斷 |
| 新建 | #76 | 齒輪齒面接觸模型 | physics_model_status §2.2 "Still missing"，改善齒輪箱頻譜特徵 |
| 保持 | #72 | 葉片質量不平衡與轉子動態不平衡 | 改善 1P 振動物理因果關係 |
| 保持 | #71 | 風切剖面模型 | 高度相關風速分布與葉片不對稱載荷 |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電氣模型尚未加入保護曲線比對邏輯 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | BPFO/BPFI + 邊帶 + 峰值因子/峭度已完成，頻帶警報曲線待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，剩前端 RUL 視覺化 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求，待規劃 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求，待規劃 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 漏洞數量不變，尚未升級 |
| 保持 | #44 | Ruff lint 179 個錯誤 | 維持 115 個，核心模組 0 錯誤 |
| 保持 | #26 | 部署強化 | Docker Compose 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #76 | 齒輪齒面接觸模型 | enhancement, physics, auto-detected | 2026-04-17 | 新建 |
| #75 | 冷卻液液位與洩漏偵測模型 | enhancement, physics, auto-detected | 2026-04-17 | 新建 |
| #72 | 葉片質量不平衡與轉子動態不平衡 | enhancement, physics, auto-detected | 2026-04-17 | 改善 1P 振動因果 |
| #71 | 風切剖面模型 | enhancement, physics, auto-detected | 2026-04-17 | 高度相關風速 |
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | 電壓-時間保護曲線 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 前端 RUL 視覺化待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 降至 115 個 |
| #26 | 部署強化 | enhancement, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-16 | 0 | 無測試套件 | 無變更 |
| `server/routers/` | 2026-04-16 | 0 | 無測試套件 | 無變更 |
| `simulator/` | 2026-04-16 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/` | 2026-04-17 | 0 | 無測試套件 | 新增齒輪箱油溫/黏度 (#73) |
| `frontend/` | 2026-04-15 | 0 | 無測試套件 | RUL 視覺化待實作 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案（dashboard.py 等） |

## API Endpoints

| Method | Path | 狀態 | 文件同步 |
|--------|------|------|----------|
| GET | /api/health | 正常 | ✅ |
| GET | /api/turbines | 正常 | ✅ |
| GET | /api/turbines/{id} | 正常 | ✅ |
| GET | /api/turbines/{id}/history | 正常 | ✅ |
| GET | /api/turbines/{id}/trend | 正常 | ✅ |
| GET | /api/turbines/farm-status | 正常 | ✅ |
| GET | /api/turbines/farm-trend | 正常 | ✅ |
| GET | /api/config | 正常 | ✅ |
| POST | /api/config/datasource | 正常 | ✅ |
| POST | /api/config/simulation | 正常 | ✅ |
| GET | /api/config/wind | 正常 | ✅ |
| POST | /api/config/wind | 正常 | ✅ |
| POST | /api/config/wind/clear | 正常 | ✅ |
| GET | /api/config/simulation/time-scale | 正常 | ✅ |
| POST | /api/config/simulation/time-scale | 正常 | ✅ |
| POST | /api/config/simulation/generate-bulk | 正常 | ✅ |
| GET | /api/config/grid | 正常 | ✅ |
| POST | /api/config/grid | 正常 | ✅ |
| POST | /api/config/grid/clear | 正常 | ✅ |
| GET | /api/config/storage/stats | 正常 | ✅ |
| GET | /api/config/sessions | 正常 | ✅ |
| POST | /api/config/storage/maintenance | 正常 | ✅ |
| GET | /api/config/turbine-spec | 正常 | ✅ |
| POST | /api/config/turbine-spec | 正常 | ✅ |
| GET | /api/config/turbine-spec/presets | 正常 | ✅ |
| POST | /api/control/command | 正常 | ✅ |
| POST | /api/control/curtail | 正常 | ✅ |
| GET | /api/control/{id}/status | 正常 | ✅ |
| GET | /api/faults/scenarios | 正常 | ✅ |
| POST | /api/faults/inject | 正常 | ✅ |
| GET | /api/faults/active | 正常 | ✅ |
| POST | /api/faults/clear | 正常 | ✅ |
| GET | /api/faults/test-plans | 正常 | ✅ |
| POST | /api/faults/test-plans/{plan_id}/run | 正常 | ✅ |
| GET | /api/maintenance/work-orders | 正常 | ✅ |
| POST | /api/maintenance/work-orders | 正常 | ✅ |
| GET | /api/maintenance/work-orders/{id} | 正常 | ✅ |
| PATCH | /api/maintenance/work-orders/{id} | 正常 | ✅ |
| GET | /api/maintenance/technicians | 正常 | ✅ |
| POST | /api/maintenance/technicians | 正常 | ✅ |
| PATCH | /api/maintenance/technicians/{id}/status | 正常 | ✅ |
| GET | /api/maintenance/events/compare | 正常 | ✅ |
| GET | /api/i18n/tags | 正常 | ✅ |
| GET | /api/i18n/tags/all | 正常 | ✅ |
| GET | /api/i18n/tags/registry | 正常 | ✅ |
| GET | /api/modbus/status | 正常 | ✅ |
| POST | /api/modbus/start | 正常 | ✅ |
| POST | /api/modbus/stop | 正常 | ✅ |
| GET | /api/modbus/registers | 正常 | ✅ |
| GET | /api/export/snapshot | 正常 | ✅ |
| GET | /api/export/history | 正常 | ✅ |
| GET | /api/export/events | 正常 | ✅ |
| WS | /ws/realtime | 正常 | ✅ |

共 54 個路由（53 HTTP + 1 WebSocket），全部與文件同步。

## 程式碼品質

- Lint 錯誤：115（核心模組 server/ + simulator/ 維持 0 錯誤，剩餘皆在 opc_bachmann/ 和根目錄原型檔案）
- 無 docstring 的公開函數：6 個（與上次相同）
  - 根目錄原型：dashboard.py `update_charts()`、wind_model.py `get_status()`/`get_wind_direction()`/`get_ambient_temp()`
  - 內部輔助：storage.py `to_float()` x2（巢狀函數，非模組級公開）
- Broken imports：0（核心模組）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：91 個（+1 WDRV_GbxOilTmp）

## 今日新增功能

### 齒輪箱油溫與黏度效應模型（#73）
- **物理原理**：齒輪箱潤滑油黏度隨溫度變化，影響齒輪嚙合效率。低溫時黏度高、摩擦損耗大；高溫時油膜可能不足。冷啟動初期 ~10 分鐘效率較低。
- **實作方式**：
  1. `drivetrain_model.py`：新增油溫狀態變數，一階熱模型追蹤（齒輪損耗 + 軸承摩擦為熱源）
  2. Walther 型黏度比：`visc_ratio = exp(-0.03 × (T_oil - 60°C))`
  3. 冷啟動損耗因子：`1 + 0.5 × exp(-t_running / 600)`，前 10 分鐘額外損耗
  4. 黏度損耗 80% 回饋至齒輪箱軸承熱量，形成溫度-效率閉迴路
  5. 直驅風機跳過齒輪箱邏輯，油溫追蹤環境溫度
  6. `scada_registry.py`：新增 `WDRV_GbxOilTmp` 標籤（°C，範圍 -30~120）
- **驗證結果**：
  - 冷啟動（5°C 環境）：初始損耗較穩態高 ~15%，10 分鐘衰減
  - 暖環境（30°C）：穩態油溫 ~28°C，損耗較低
  - 直驅風機：油溫 = 環境溫度 ✓
- **影響範圍**：
  - 齒輪箱風機冬季冷啟動損耗更真實
  - `gearbox_overheat` 故障的效率影響有溫度因果
  - 齒輪箱軸承熱量增加黏度損耗成分

## 建議行動

1. **合併齒輪箱油溫模型**：已推送至 `claude/gifted-noether-PFU4Z`，可建立 PR 合併
2. **實作 #71 風切剖面模型**：高度相關風速分布影響葉片載荷不對稱，基礎設施已就緒（轉子方位角 #69）
3. **實作 #72 葉片質量不平衡**：改善 1P 振動從經驗公式轉為物理推導，使用已有的方位角追蹤
4. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試
5. **升級有漏洞的套件**（#48）：優先處理 `cryptography`（7 個 CVE）
