# digiWindFarm Daily Report

> 最後更新：2026-04-15（第二次更新）

## 昨日 Commit 摘要

過去 24 小時 main 分支合併：
- [096f924] Merge pull request #59 from dofliu/claude/awesome-albattani-o49ay
- [15b5e9c] docs: update project docs and daily report for 2026-04-15
- [d2a5c1f] Merge pull request #56 from dofliu/claude/determined-goldberg-f1OFZ
- [7220898] Merge pull request #55 from dofliu/claude/gracious-mccarthy-j7IiT
- [e658f75] Merge pull request #54 from dofliu/claude/gracious-mccarthy-MNcvo
- [beeeee5] Merge pull request #53 from dofliu/claude/tender-ramanujan-XzZMe

本次日報工作提交（分支 `claude/awesome-albattani-IzD2C`）：
- [86e1707] feat: add fatigue alarm event integration — auto-generate history events on threshold crossing (#57)
- [06860a1] docs: add 23 docstrings to public functions across server and simulator (#45)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 進展 | #57 | 疲勞警報閾值與剩餘使用壽命（RUL）估算 | 新增疲勞警報事件整合：閾值跨越時自動產生歷史事件 |
| 進展 | #45 | 108 個公開函數缺少 docstring | 累計修復 99 個（今日 23 個），剩餘約 9 個 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 待實作 |
| 保持 | #52 | 缺少自動化測試套件 — 核心模組無 pytest 覆蓋 | 仍無 pytest，需優先處理 |
| 保持 | #51 | 警報處理透過 RAG 機制來產生結果 | 用戶功能需求，待規劃 |
| 保持 | #50 | 提供可讓外部擷取資料的 API 功能 | 用戶功能需求，待規劃 |
| 保持 | #48 | pip-audit 偵測到 17 個安全漏洞（5 套件） | 漏洞數量不變，尚未升級 |
| 保持 | #44 | Ruff lint 179 個錯誤 | 核心模組維持 0 錯誤，剩餘 109 個在 opc_bachmann/ 和根目錄原型 |
| 保持 | #26 | 部署強化 — 認證、權限、Docker、HTTPS | Docker Compose 已完成，JWT/RBAC/HTTPS 待做 |
| 保持 | #24 | 歷史資料儲存 — 保留策略、儲存架構 | 保留策略已做，架構決策待定 |

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #58 | 頻譜振動警報閾值與邊帶分析 | auto-detected, enhancement, physics | 2026-04-15 | 待實作 |
| #57 | 疲勞警報閾值與剩餘使用壽命（RUL）估算 | auto-detected, enhancement, physics | 2026-04-15 | 警報閾值+RUL+事件整合已完成，剩前端視覺化 |
| #52 | 缺少自動化測試套件 — 核心模組無 pytest 覆蓋 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制來產生結果 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 提供可讓外部擷取資料的 API 功能 | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 偵測到 17 個安全漏洞 | security, auto-detected | 2026-04-13 | cryptography 41→46 跨度大 |
| #45 | 108 個公開函數缺少 docstring | documentation, auto-detected | 2026-04-13 | 已修 99 個，剩約 9 個 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組已清零 |
| #26 | 部署強化 — 認證、權限、Docker、HTTPS | enhancement, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存 — 保留策略、儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-15 | 0 | 無測試套件 | 新增疲勞警報事件偵測邏輯 |
| `server/routers/` | 2026-04-15 | 0 | 無測試套件 | 8 個 router 模組全部有 docstring |
| `simulator/` | 2026-04-15 | 0 | 無測試套件 | engine 和 modbus_server property 已補 docstring |
| `simulator/physics/` | 2026-04-15 | 0 | 無測試套件 | 14 個物理模型，疲勞事件整合完成 |
| `frontend/` | 2026-04-12 | 0 | 無測試套件 | React 前端，RUL 視覺化待實作 |
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

## 程式碼品質

- Lint 錯誤：109（核心模組 server/ + simulator/ 維持 0 錯誤，剩餘皆在 opc_bachmann/ 和根目錄原型檔案）
- 無 docstring 的公開函數：約 9 個（上次 32，今日修復 23 個，累計修復 99 個）
- Broken imports：0（核心模組結構正確）；環境缺少依賴套件（numpy/fastapi）非程式碼問題；根目錄早期原型有 5 個已知缺失（dash/plotly/pandas/openopc2）
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），與上次相同，詳見 #48
  - cryptography 41.0.7 → 需升級至 ≥46.0.6（7 個 CVE）
  - pyjwt 2.7.0 → 需升級至 ≥2.12.0（1 個 CVE）
  - setuptools 68.1.2 → 需升級至 ≥78.1.1（3 個 CVE）
  - pip 24.0 → 需升級至 ≥26.0（4 個 CVE）
  - wheel 0.42.0 → 需升級至 ≥0.46.2（2 個 CVE）
- TODO/FIXME/HACK：0 個（核心模組；opc_bachmann/ 中有 4 個，屬第三方套件）
- SCADA 標籤：75 個（含 3 個疲勞警報/RUL 標籤）

## 今日新增功能

### 疲勞警報事件整合（#57）
- **自動事件產生**：當疲勞警報等級變化（塔架或葉片）時，自動產生歷史事件記錄
- **事件內容**：包含元件名稱、從/到等級、等級名稱（正常/注意/警告/危險/停機）、RUL 估算
- **事件類型**：`fatigue`，來源 `simulator`，可透過歷史事件 API 查詢
- **追蹤機制**：使用 `_last_fatigue_alarm` 字典追蹤每部風機的上次警報等級，避免重複事件

### Docstring 補充（#45）
- 新增 23 個 docstring，覆蓋：
  - `server/app.py`：lifespan、health、websocket_realtime
  - 6 個 router 的 `get_broker()` 函數
  - `server/opc_adapter.py`：on_data、start、stop
  - `server/data_broker.py`：turbine_ids property
  - `simulator/engine.py`：is_running、turbine_ids properties
  - `simulator/modbus_server.py`：get_status、is_running
  - `simulator/physics/`：fault_engine、power_curve、thermal_model、vibration_spectral、wind_field、yaw_model

## 建議行動

1. **完善 #57 前端視覺化**：前端新增 RUL 顯示和疲勞警報等級視覺化（後端事件整合已完成）
2. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試
3. **實作 #58 頻譜警報**：各頻帶警報閾值定義、峰值因子/峭度超標警報
4. **升級有漏洞的套件**（#48）：優先處理 `cryptography`（7 個 CVE）
5. **完成 docstring**（#45）：剩餘約 9 個，主要是 storage.py 內部函數和 engine.py time_scale setter
6. **處理用戶功能需求**（#50、#51）：外部 API 文件和 RAG 警報處理
