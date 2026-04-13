# digiWindFarm Daily Report

> 最後更新：2026-04-13

## 昨日 Commit 摘要

過去 24 小時無新 commit（main 分支）。

本次日報工作提交：
- [3c070dc] chore: auto-fix 53 ruff lint errors, update README API list and CLAUDE.md gaps

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 新建 | #43 | README.md API endpoint 列表不完整 | 自動偵測：實際 ~50 路由，文件僅列 ~30 |
| 新建 | #44 | Ruff lint 179 個錯誤 | 自動偵測：53 個已修復，剩餘 123 個 |
| 新建 | #45 | 108 個公開函數缺少 docstring | 自動偵測：核心模組 docstring 覆蓋率不足 |
| 保持 | #42 | Docker Compose 部署 + .env 整理 | 程式碼在 `claude/jolly-feynman-l88Tt`，未合併至 main |
| 保持 | #41 | 疲勞/載荷模型 | 程式碼在 `claude/jolly-feynman-l88Tt`，未合併至 main |
| 保持 | #26 | 部署強化 — 認證、權限、Docker、HTTPS | 持續進行中 |
| 保持 | #24 | 歷史資料儲存 — 保留策略、查詢篩選 | 持續進行中 |

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #45 | 108 個公開函數缺少 docstring | documentation, auto-detected | 2026-04-13 | 新建 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 53 個已修復 |
| #43 | README.md API endpoint 列表不完整 | documentation, auto-detected | 2026-04-13 | 已在本次修復 |
| #42 | Docker Compose 部署 + .env 整理 | enhancement, deployment | 2026-04-12 | 待合併 PR |
| #41 | 疲勞/載荷模型 — DEL、Miner 累積損傷 | enhancement, physics | 2026-04-12 | 待合併 PR |
| #26 | 部署強化 — 認證、權限、Docker、HTTPS | enhancement, platform, deployment | 2026-04-05 | 長期追蹤 |
| #24 | 歷史資料儲存 — 保留策略、儲存架構 | enhancement, platform | 2026-04-05 | 長期追蹤 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-13 | 0 | 無測試套件 | API route handlers |
| `simulator/` | 2026-04-13 | 0 | 無測試套件 | 引擎與物理模擬 |
| `simulator/physics/` | 2026-04-13 | 0 | 無測試套件 | 核心物理模型 |
| `frontend/` | 2026-04-12 | 0 | 無測試套件 | React 前端 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案（dashboard.py 等） |

## API Endpoints

| Method | Path | 狀態 | 文件同步 |
|--------|------|------|----------|
| GET | /api/health | 正常 | ✅ (已更新) |
| GET | /api/turbines | 正常 | ✅ |
| GET | /api/turbines/{id} | 正常 | ✅ |
| GET | /api/turbines/{id}/history | 正常 | ✅ |
| GET | /api/turbines/{id}/trend | 正常 | ✅ |
| GET | /api/turbines/farm-status | 正常 | ✅ |
| GET | /api/turbines/farm-trend | 正常 | ✅ (已更新) |
| GET | /api/config | 正常 | ✅ |
| POST | /api/config/datasource | 正常 | ✅ (已更新) |
| POST | /api/config/simulation | 正常 | ✅ (已更新) |
| GET | /api/config/wind | 正常 | ✅ (已更新) |
| POST | /api/config/wind | 正常 | ✅ |
| POST | /api/config/wind/clear | 正常 | ✅ |
| GET | /api/config/simulation/time-scale | 正常 | ✅ (已更新) |
| POST | /api/config/simulation/time-scale | 正常 | ✅ (已更新) |
| POST | /api/config/simulation/generate-bulk | 正常 | ✅ (已更新) |
| GET | /api/config/grid | 正常 | ✅ |
| POST | /api/config/grid | 正常 | ✅ |
| POST | /api/config/grid/clear | 正常 | ✅ |
| GET | /api/config/storage/stats | 正常 | ✅ (已更新) |
| GET | /api/config/sessions | 正常 | ✅ (已更新) |
| POST | /api/config/storage/maintenance | 正常 | ✅ (已更新) |
| GET | /api/config/turbine-spec | 正常 | ✅ |
| POST | /api/config/turbine-spec | 正常 | ✅ |
| GET | /api/config/turbine-spec/presets | 正常 | ✅ (已更新) |
| POST | /api/control/command | 正常 | ✅ |
| POST | /api/control/curtail | 正常 | ✅ |
| GET | /api/control/{id}/status | 正常 | ✅ |
| GET | /api/faults/scenarios | 正常 | ✅ |
| POST | /api/faults/inject | 正常 | ✅ |
| GET | /api/faults/active | 正常 | ✅ |
| POST | /api/faults/clear | 正常 | ✅ |
| GET | /api/faults/test-plans | 正常 | ✅ (已更新) |
| POST | /api/faults/test-plans/{plan_id}/run | 正常 | ✅ (已更新) |
| GET | /api/maintenance/work-orders | 正常 | ✅ |
| POST | /api/maintenance/work-orders | 正常 | ✅ |
| GET | /api/maintenance/work-orders/{id} | 正常 | ✅ (已更新) |
| PATCH | /api/maintenance/work-orders/{id} | 正常 | ✅ |
| GET | /api/maintenance/technicians | 正常 | ✅ |
| POST | /api/maintenance/technicians | 正常 | ✅ |
| PATCH | /api/maintenance/technicians/{id}/status | 正常 | ✅ |
| GET | /api/maintenance/events/compare | 正常 | ✅ |
| GET | /api/i18n/tags | 正常 | ✅ (已更新) |
| GET | /api/i18n/tags/all | 正常 | ✅ (已更新) |
| GET | /api/i18n/tags/registry | 正常 | ✅ (已更新) |
| GET | /api/modbus/status | 正常 | ✅ (已更新) |
| POST | /api/modbus/start | 正常 | ✅ (已更新) |
| POST | /api/modbus/stop | 正常 | ✅ (已更新) |
| GET | /api/modbus/registers | 正常 | ✅ (已更新) |
| GET | /api/export/snapshot | 正常 | ✅ |
| GET | /api/export/history | 正常 | ✅ |
| GET | /api/export/events | 正常 | ✅ |
| WS | /ws/realtime | 正常 | ✅ |

## 程式碼品質

- Lint 錯誤：123（修復前 179，自動修復 53 個 F401 未使用 import）
- 無 docstring 的公開函數：108
- Broken imports：5（`dashboard.py` 缺 dash/plotly/pandas、`scada_system.py` 缺 pandas、`server/opc_adapter.py` 缺 openopc2 — 均為早期原型或選用模組）
- 測試套件：未建立（無 pytest）
- 安全漏洞：pip-audit 未安裝，無法掃描

## 建議行動

1. **合併待處理 PR**：Issues #41（疲勞模型）和 #42（Docker Compose）描述已完成但程式碼在 `claude/jolly-feynman-l88Tt` 分支未合併，建議檢視並合併
2. **建立測試套件**：目前完全沒有自動化測試，建議優先為核心物理模型（`simulator/physics/`）和 API endpoint 建立基本測試
3. **清理早期原型檔案**：根目錄的 `dashboard.py`、`scada_system.py`、`turbine_model.py`、`wind_model.py` 等為早期原型且有 broken import，建議移至 `legacy/` 目錄或移除
4. **安裝 pip-audit**：加入 `pip-audit` 到開發依賴以定期掃描安全漏洞
5. **處理剩餘 123 個 lint 錯誤**：主要為未使用變數（F841）等，需手動審查
