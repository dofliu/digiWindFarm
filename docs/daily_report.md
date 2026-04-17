# digiWindFarm Daily Report

> 最後更新：2026-04-17（第三次）

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/gifted-noether-mgdYZ`）：
- [1f3d747] feat: add coolant level tracking with leak detection and pump cavitation (#75)

過去 24 小時合併至 main：
- [4931b08] Merge pull request #78（葉片質量不平衡模型 — 文件更新）
- [887b38b] Merge pull request #74（風切剖面模型 — 文件更新）
- [4982827] Merge pull request #70（塔架陰影效應 — 3P 功率/扭矩/載荷調變）

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 實作完成 | #75 | 冷卻液液位與洩漏偵測模型 | 液位追蹤 + 泵浦空蝕 + 故障耦合，待合併 |
| 新建 | #79 | 風向隨高度偏轉模型（Wind Veer） | physics_model_status.md 缺口 |
| 保持 | #76 | 齒輪齒面接觸模型 | 時變嚙合剛度 + 齒面磨耗 |
| 保持 | #72 | 葉片質量不平衡模型 | 已合併至 main |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電氣模型尚未加入保護曲線比對邏輯 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線待做 |
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
| #79 | 風向隨高度偏轉模型 | enhancement, physics, auto-detected | 2026-04-17 | 新建 |
| #76 | 齒輪齒面接觸模型 | enhancement, physics, auto-detected | 2026-04-17 | 齒面力學 |
| #75 | 冷卻液液位與洩漏偵測模型 | enhancement, physics, auto-detected | 2026-04-17 | 已實作，待合併 |
| #72 | 葉片質量不平衡模型 | enhancement, physics, auto-detected | 2026-04-17 | 已合併 |
| #71 | 風切剖面模型 | enhancement, physics, auto-detected | 2026-04-17 | 已合併 |
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | LVRT/OVRT 保護曲線 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 後端完成，前端待做 |
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
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `server/routers/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/` | 2026-04-17 | 0 | 無測試套件 | 新增冷卻液液位 (#75) |
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
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：96 個（+2 新增 WCOL_CoolantLvl, WCOL_CoolantAlm）

## 今日新增功能

### 冷卻液液位與洩漏偵測模型（#75）
- **物理原理**：水冷迴路的 O-ring 隨運轉時數劣化，導致冷卻液緩慢洩漏。液位下降時泵浦吸入空氣，產生空蝕效應（cavitation），流量和壓力不穩定，冷卻效能非線性下降。
- **實作方式**：
  1. `cooling_model.py`：WaterCoolingLoop 新增 `_coolant_level_pct`（0-100%）和 `_leak_rate_lph`（公升/小時）狀態變數
  2. 泵浦空蝕模型：液位 < 70% 時流量按 `(level - 10) / 60` 比例衰減
  3. 三級警報：0=正常(≥70%), 1=低液位(<70%), 2=極低(<50%), 3=危急(<30%)
  4. `turbine_physics.py`：`converter_cooling_fault` 故障耦合洩漏率（0.8 L/h × severity）
  5. `scada_registry.py`：新增 `WCOL_CoolantLvl`（%）和 `WCOL_CoolantAlm`（警報等級）
  6. 維護 API：`refill_coolant()` 補充、`set_coolant_leak()` 設定洩漏率
- **物理效果**：
  - 洩漏液位緩慢下降 → 泵浦空蝕 → 流量不穩 → 冷卻效能非線性下降 → 溫度上升
  - 漸進式故障指標，適合預測性維護分析訓練資料
  - converter_cooling_fault 故障注入後，液位逐步下降提供可觀測的前兆訊號

## 建議行動

1. **合併冷卻液液位模型**：已推送至 `claude/gifted-noether-mgdYZ`，可建立 PR 合併
2. **實作 #79 風向隨高度偏轉（Wind Veer）**：補充風場模型，影響葉片攻角和載荷不對稱
3. **實作 #76 齒輪齒面接觸模型**：時變嚙合剛度 + 齒面磨耗進程
4. **實作 #67 保護繼電器協調**：LVRT/OVRT 電壓-時間保護曲線
5. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試
6. **升級有漏洞的套件**（#48）：優先處理 `cryptography`（7 個 CVE）
