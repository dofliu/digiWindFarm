# digiWindFarm Daily Report

> 最後更新：2026-04-13（第二次更新）

## 昨日 Commit 摘要

過去 24 小時 main 分支合併：
- [8bd89f3] Merge pull request #47 from dofliu/claude/cool-newton-9NAoS
- [ab4d114] Merge pull request #46 from dofliu/claude/jolly-feynman-l88Tt
- [e21c365] docs: update physics_model_status.md to reflect current state
- [edc69b9] docs: add daily report for 2026-04-13
- [3c070dc] chore: auto-fix 53 ruff lint errors, update README API list and CLAUDE.md gaps

本次日報工作提交（分支 `claude/tender-ramanujan-sgTfg`）：
- 修復核心模組 15 個 lint 錯誤（server/ + simulator/ 全部通過）
- 關閉 3 個已完成 issue（#41、#42、#43）
- 新建 1 個安全漏洞 issue（#48）
- 更新日報、專案文件

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 關閉 | #41 | 疲勞/載荷模型 — DEL、Miner 累積損傷 | PR #46 已合併至 main，程式碼已驗證 |
| 關閉 | #42 | Docker Compose 部署 + .env 整理 | PR #46 已合併至 main，程式碼已驗證 |
| 關閉 | #43 | README.md API endpoint 列表不完整 | commit 3c070dc 已修復，53 路由全部同步 |
| 新建 | #48 | pip-audit 偵測到 17 個安全漏洞（5 套件） | cryptography、pip、pyjwt、setuptools、wheel |
| 保持 | #44 | Ruff lint 179 個錯誤 | 核心模組已全部修復（0 錯誤），剩餘 109 個在 opc_bachmann/ 和原型檔 |
| 保持 | #45 | 108 個公開函數缺少 docstring | 掃描結果 109 個，分布同上次 |
| 保持 | #26 | 部署強化 — 認證、權限、Docker、HTTPS | Docker Compose 已完成（#42 關閉），JWT/RBAC/HTTPS 待做 |
| 保持 | #24 | 歷史資料儲存 — 保留策略、儲存架構 | 保留策略已實作，SQLite vs 時序 DB 待決策 |

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #48 | pip-audit 偵測到 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 新建：cryptography 41→46 跨度大 |
| #45 | 108 個公開函數缺少 docstring | documentation, auto-detected | 2026-04-13 | 持續追蹤 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組已清零，剩餘皆為舊原型/第三方 |
| #26 | 部署強化 — 認證、權限、Docker、HTTPS | enhancement, deployment | 2026-04-05 | Docker 已完成，JWT/RBAC/HTTPS 待做 |
| #24 | 歷史資料儲存 — 保留策略、儲存架構 | enhancement, platform | 2026-04-05 | 保留策略已做，架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-13 | 0 | 無測試套件 | API route handlers，lint 全部通過 |
| `server/routers/` | 2026-04-13 | 0 | 無測試套件 | 8 個 router 模組 |
| `simulator/` | 2026-04-13 | 0 | 無測試套件 | 引擎、grid_model、modbus_server |
| `simulator/physics/` | 2026-04-13 | 0 | 無測試套件 | 14 個物理模型檔案，lint 全部通過 |
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

- Lint 錯誤：109（核心模組 server/ + simulator/ 已全部修復為 0，剩餘皆在 opc_bachmann/ 和根目錄原型檔案）
- 無 docstring 的公開函數：109
- Broken imports：0（核心模組）；5（根目錄早期原型，dash/plotly/pandas/openopc2 — 已知非核心）
- 測試套件：未建立（無 pytest）
- 安全漏洞：17 個（5 個套件），詳見 #48
  - cryptography 41.0.7 → 需升級至 ≥46.0.6（7 個 CVE）
  - pyjwt 2.7.0 → 需升級至 ≥2.12.0（1 個 CVE）
  - setuptools 68.1.2 → 需升級至 ≥78.1.1（3 個 CVE）
  - pip 24.0 → 需升級至 ≥26.0（4 個 CVE）
  - wheel 0.42.0 → 需升級至 ≥0.46.2（2 個 CVE）

## 建議行動

1. **升級有漏洞的套件**（#48）：優先處理 `cryptography`（7 個 CVE）和 `pyjwt`（影響未來 JWT 實作），注意大版本升級的兼容性
2. **建立測試套件**：核心物理模型（`simulator/physics/`）和 API endpoint 仍無自動化測試，建議優先建立
3. **清理早期原型檔案**：根目錄的 `dashboard.py`、`scada_system.py`、`turbine_model.py`、`main_architecture.py` 等有 109 個 lint 錯誤中的大部分，建議移至 `legacy/` 或移除
4. **更新 #44 進度**：核心模組 lint 已全部修復，可考慮將 issue 重新定義為「清理根目錄原型 lint」或關閉
5. **推進 #26 部署強化**：Docker Compose 已完成並關閉 #42，下一步是 JWT 認證和基本 RBAC
