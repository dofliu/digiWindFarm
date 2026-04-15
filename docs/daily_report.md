# digiWindFarm Daily Report

> 最後更新：2026-04-15（第三次更新）

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/happy-goodall-sfnpJ`）：
- [8261c0a] feat: use Cp aerodynamic model in Region 3 for realistic power variation (#61)
- [9822b64] docs: add docstrings to main() and time_scale setter (#45)

過去 24 小時 main 分支合併：
- [076073e] Merge pull request #60 from dofliu/claude/awesome-albattani-IzD2C
- [096f924] Merge pull request #59 from dofliu/claude/awesome-albattani-o49ay
- [d2a5c1f] Merge pull request #56 from dofliu/claude/determined-goldberg-f1OFZ
- [7220898] Merge pull request #55 from dofliu/claude/gracious-mccarthy-j7IiT
- [e658f75] Merge pull request #54 from dofliu/claude/gracious-mccarthy-MNcvo

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 新建 | #61 | Region 3 功率變異過低 — 槳距控制器響應延遲與風擾動耦合 | 已提交修復：Cp 模型取代查詢表，目標 CV 3-5% |
| 新建 | #62 | 塔架前後動態響應 — 自然頻率振盪模擬 | 待實作，追蹤 TODO.md 中的物理改進項目 |
| 進展 | #45 | 108 個公開函數缺少 docstring | 累計修復 102 個（今日 2 個），剩餘 6 個（根目錄原型+內部輔助函數） |
| 進展 | #61 | Region 3 功率變異修復 | 提交 power_curve.py + turbine_physics.py 修改 |
| 保持 | #62 | 塔架前後動態響應 | 待實作 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 待實作 |
| 保持 | #57 | 疲勞警報閾值與剩餘使用壽命（RUL）估算 | 後端完成，剩前端視覺化 |
| 保持 | #52 | 缺少自動化測試套件 — 核心模組無 pytest 覆蓋 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制來產生結果 | 用戶功能需求，待規劃 |
| 保持 | #50 | 提供可讓外部擷取資料的 API 功能 | 用戶功能需求，待規劃 |
| 保持 | #48 | pip-audit 偵測到 17 個安全漏洞（5 套件） | 漏洞數量不變，尚未升級 |
| 保持 | #44 | Ruff lint 179 個錯誤 | 核心模組維持 0 錯誤 |
| 保持 | #26 | 部署強化 — 認證、權限、Docker、HTTPS | Docker Compose 已完成 |
| 保持 | #24 | 歷史資料儲存 — 保留策略、儲存架構 | 架構決策待定 |

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #62 | 塔架前後動態響應 — 自然��率振盪模擬 | auto-detected, enhancement, physics | 2026-04-15 | 新建，待實作 |
| #61 | Region 3 功率變異過低 | auto-detected, enhancement, physics | 2026-04-15 | 已提交修復 |
| #58 | 頻��振動警報閾值與邊帶分析 | auto-detected, enhancement, physics | 2026-04-15 | 待實作 |
| #57 | 疲���警報閾值與 RUL 估算 | auto-detected, enhancement, physics | 2026-04-15 | 後端完成，前端待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #45 | 108 個公開函數缺少 docstring | documentation, auto-detected | 2026-04-13 | 已修 102 個，剩 6 個 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組已清零 |
| #26 | 部署強化 | enhancement, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-15 | 0 | 無測試套件 | 疲勞警報事件偵測邏輯已完��� |
| `server/routers/` | 2026-04-15 | 0 | 無測試���件 | 8 個 router 全部有 docstring |
| `simulator/` | 2026-04-15 | 0 | 無測試套件 | engine time_scale setter 已補 docstring |
| `simulator/physics/` | 2026-04-15 | 0 | 無測試套件 | Region 3 Cp 模型改進完成 |
| `frontend/` | 2026-04-15 | 0 | 無測��套件 | RUL 視覺化待實作 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案（dashboard.py 等） |

## API Endpoints

| Method | Path | 狀態 | 文件同步 |
|--------|------|------|----------|
| GET | /api/health | 正常 | ��� |
| GET | /api/turbines | 正常 | ✅ |
| GET | /api/turbines/{id} | 正常 | ✅ |
| GET | /api/turbines/{id}/history | 正常 | ✅ |
| GET | /api/turbines/{id}/trend | 正常 | ✅ |
| GET | /api/turbines/farm-status | 正常 | ✅ |
| GET | /api/turbines/farm-trend | 正常 | ✅ |
| GET | /api/config | 正常 | ✅ |
| POST | /api/config/datasource | 正常 | ✅ |
| POST | /api/config/simulation | 正常 | ✅ |
| GET | /api/config/wind | 正常 | �� |
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

- Lint 錯誤：~109（核心模組 server/ + simulator/ 維持 0 錯誤，剩餘皆在 opc_bachmann/ 和根目錄原型檔案）
- 無 docstring 的公開函數：6 個（上次 8 個，今日修復 2 個，累計修復 102/108 個）
  - 根目錄原型：dashboard.py `update_charts()`、wind_model.py `get_status()`/`get_wind_direction()`/`get_ambient_temp()`
  - 內部輔助：storage.py `to_float()` ×2（巢狀函數，非模組級公開）
- Broken imports：0（核心模組；環境缺 numpy/fastapi 等非程式碼問題）
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），與上次相同，詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：75 個

## 今日新增功能

### Region 3 功率變異改進（#61）
- **根本原因**：Region 3 功率輸出直接使用查詢表（恆定額定功率），完全繞過 Cp(λ,β) 氣動力模型，導致槳距控制器延遲對功率零影響
- **修復方式**：
  1. `power_curve.py`：Region 3 改用 Cp 氣動力模型計算功率，槳距控制器延遲和死區自然產生功率變異
  2. 允許 4% 額定功率過衝（真實風機在槳距追上前的暫態行為）
  3. `turbine_physics.py`：Region 3 功率斜坡時間常數從 4s 降至 2s，讓槳距延遲引起的變異通過
- **預期效果**：Region 3 功率 CV 從 0.8-0.9% ���升至 3-5%
- **驗證方式**：使用 `examples/data_quality_analysis.py` 執行 2 小時模擬分析

### Docstring 補充（#45）
- 新增 2 個 docstring：`run.py:main()`、`simulator/engine.py:time_scale` setter
- 累計修復 102/108 個，剩餘 6 個為根目錄原型和巢狀輔助函數

## 建議行動

1. **驗證 #61 修復效果**：啟動模擬，使用 `data_quality_analysis.py` 確認 Region 3 功率 CV 達到 3-5%
2. **實作 #62 塔架動態響應**：加入單自由度振動模型，模擬塔架自然頻率振盪
3. **實作 #58 頻譜警報**：各頻帶警報閾值定義、峰值因子/峭度超標警報、邊帶分析
4. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試
5. **升級有漏洞的套件**���#48）：優先處理 `cryptography`（7 個 CVE）
6. **完善 #57 前端視覺化**：前端新增 RUL 顯示和疲勞警報等級視覺化
