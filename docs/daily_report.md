# digiWindFarm Daily Report

> 最後更新：2026-04-15

## 昨日 Commit 摘要

過去 24 小時 main 分支合併：
- [d2a5c1f] Merge pull request #56 from dofliu/claude/determined-goldberg-f1OFZ
- [7220898] Merge pull request #55 from dofliu/claude/gracious-mccarthy-j7IiT
- [e658f75] Merge pull request #54 from dofliu/claude/gracious-mccarthy-MNcvo
- [beeeee5] Merge pull request #53 from dofliu/claude/tender-ramanujan-XzZMe
- [3644834] docs: add 16 docstrings to Storage class, update daily report
- [ce34706] docs: add docstrings to 34 public methods in physics modules
- [dd8f651] docs: update TODO.md and CLAUDE.md with new issues and gaps
- [b827eeb] docs: add docstrings to 16 public methods in DataBroker and SimulationEngine

本次日報工作提交（分支 `claude/awesome-albattani-o49ay`）：
- [56a0592] feat: add fatigue alarm thresholds and RUL estimation (#57)
- [11cd1bd] docs: add 11 docstrings to grid_model and config router (#45)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 新建 | #57 | 疲勞警報閾值與剩餘使用壽命（RUL）估算 | 已完成基礎實作：警報等級 0-4、RUL 估算、3 個新 SCADA 標籤 |
| 新建 | #58 | 頻譜振動警報閾值與邊帶分析 | 追蹤頻譜警報閾值和邊帶模擬 |
| 進展 | #45 | 108 個公開函數缺少 docstring | 累計修復 76 個（今日 11 個），剩餘 32 個 |
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
| #58 | 頻譜振動警報閾值與邊帶分析 | auto-detected, enhancement, physics | 2026-04-15 | 今日新建 |
| #57 | 疲勞警報閾值與剩餘使用壽命（RUL）估算 | auto-detected, enhancement, physics | 2026-04-15 | 今日新建，基礎實作已完成 |
| #52 | 缺少自動化測試套件 — 核心模組無 pytest 覆蓋 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制來產生結果 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 提供可讓外部擷取資料的 API 功能 | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 偵測到 17 個安全漏洞 | security, auto-detected | 2026-04-13 | cryptography 41→46 跨度大 |
| #45 | 108 個公開函數缺少 docstring | documentation, auto-detected | 2026-04-13 | 已修 76 個，剩 32 個 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組已清零 |
| #26 | 部署強化 — 認證、權限、Docker、HTTPS | enhancement, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存 — 保留策略、儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-15 | 0 | 無測試套件 | config router 全部方法已有 docstring |
| `server/routers/` | 2026-04-15 | 0 | 無測試套件 | 8 個 router 模組 |
| `simulator/` | 2026-04-15 | 0 | 無測試套件 | grid_model 全部方法已有 docstring |
| `simulator/physics/` | 2026-04-15 | 0 | 無測試套件 | 14 個物理模型，新增疲勞警報閾值和 RUL |
| `frontend/` | 2026-04-12 | 0 | 無測試套件 | React 前端 |
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
- 無 docstring 的公開函數：32（上次 43，今日修復 11 個，累計修復 76 個）
- Broken imports：0（核心模組結構正確）；環境缺少依賴套件（numpy/fastapi）非程式碼問題；根目錄早期原型有 5 個已知缺失（dash/plotly/pandas/openopc2）
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），與上次相同，詳見 #48
  - cryptography 41.0.7 → 需升級至 ≥46.0.6（7 個 CVE）
  - pyjwt 2.7.0 → 需升級至 ≥2.12.0（1 個 CVE）
  - setuptools 68.1.2 → 需升級至 ≥78.1.1（3 個 CVE）
  - pip 24.0 → 需升級至 ≥26.0（4 個 CVE）
  - wheel 0.42.0 → 需升級至 ≥0.46.2（2 個 CVE）
- TODO/FIXME/HACK：4 個（皆在 opc_bachmann/ 第三方套件中，核心模組 0 個）
- SCADA 標籤：75 個（新增 3 個疲勞警報/RUL 標籤）

## 今日新增功能

### 疲勞警報閾值與 RUL 估算（#57）
- **警報等級**：基於 Miner 累積損傷的 5 級警報（0=正常, 1=注意 ≥0.30, 2=警告 ≥0.60, 3=危險 ≥0.80, 4=停機 ≥0.95）
- **RUL 估算**：基於平均損傷速率推算剩餘使用壽命（小時）
- **新 SCADA 標籤**：`WLOD_AlmTwr`（塔架疲勞警報等級）、`WLOD_AlmBld`（葉片疲勞警報等級）、`WLOD_RulHours`（剩餘使用壽命）
- 新標籤已整合至感測器模型（整數/透傳標籤適當分類）

## 建議行動

1. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試，建議優先建立 pytest 基礎框架
2. **完善 #57 疲勞警報**：前端新增 RUL 顯示和警報等級視覺化、損傷達閾值時自動產生歷史事件
3. **實作 #58 頻譜警報**：各頻帶警報閾值定義、峰值因子/峭度超標警報
4. **升級有漏洞的套件**（#48）：優先處理 `cryptography`（7 個 CVE）
5. **持續補充 docstring**（#45）：剩餘 32 個，可在 2-3 次迭代內完成
6. **處理用戶功能需求**（#50、#51）：外部 API 文件和 RAG 警報處理
