# digiWindFarm Daily Report

> 最後更新：2026-04-17

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/gifted-noether-T5rZz`）：
- [1266ec3] feat: add wind veer model with Ekman spiral blade direction offset (#79)

過去 24 小時主要合併/提交：
- [2b52e7d] Merge PR #85 — 建立風場對話框簡化
- [cf57db8] Merge PR #84 — 建立風場彈窗佈局重寫
- [9027346] Merge PR #83 — 建立風場彈窗溢出修復
- [ee73469] Merge PR #82 — 新增建立風場對話框
- [cb61c01] Merge PR #81 — 多風場管理功能（獨立 DB）
- [612058f] Merge PR #77 — 齒輪箱油溫模型合併
- [36b4fe1] Merge PR #80 — 文件更新
- [1f3d747] feat: 冷卻液液位追蹤與洩漏偵測 (#75)
- [4931b08] Merge PR #78 — 文件更新
- [a7f000b] feat: 葉片質量不平衡離心力耦合 (#72)
- [9815f9d] feat: 齒輪箱油溫與黏度效應 (#73)
- [dbb6e16] feat: 風切剖面模型 (#71)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 關閉 | #79 | 風向隨高度偏轉模型（Wind Veer） | 已實作：Ekman 螺旋 + 葉片側向力耦合 |
| 關閉 | #75 | 冷卻液液位與洩漏偵測模型 | 已實作：液位追蹤 + 泵浦空蝕 + 故障耦合 |
| 關閉 | #72 | 葉片質量不平衡與轉子動態不平衡 | 已實作：離心力 ω² 耦合 + 1P 振動 |
| 關閉 | #71 | 風切剖面模型 | 已實作：power-law V(h) + 方位角葉片載荷 |
| 新建 | #86 | 進階尾流模型（Bastankhah-Porté-Agel） | physics_model_status §2.6 "Still missing" |
| 保持 | #76 | 齒輪齒面接觸模型 | 嚙合剛度與載荷分布 |
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

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #86 | 進階尾流模型（Bastankhah-Porté-Agel） | enhancement, physics, auto-detected | 2026-04-17 | 新建 |
| #76 | 齒輪齒面接觸模型 | enhancement, physics, auto-detected | 2026-04-17 | 嚙合剛度 |
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
| `server/` | 2026-04-17 | 0 | 無測試套件 | 新增 farm_registry.py、routers/farms.py |
| `server/routers/` | 2026-04-17 | 0 | 無測試套件 | 新增 farms.py |
| `simulator/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/` | 2026-04-17 | 0 | 無測試套件 | wind veer (#79) |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | FarmSelector 元件新增 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案 |

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
| GET | /api/farms | 正常 | ❌ 新增，未同步至 README |
| POST | /api/farms | 正常 | ❌ 新增，未同步至 README |
| GET | /api/farms/{id} | 正常 | ❌ 新增，未同步至 README |
| POST | /api/farms/{id}/activate | 正常 | ❌ 新增，未同步至 README |

共 58 個路由（57 HTTP + 1 WebSocket），54 個與文件同步，4 個新增路由待同步。

## 程式碼品質

- Lint 錯誤：115（核心模組 server/ + simulator/ 維持 0 錯誤，剩餘皆在 opc_bachmann/ 和根目錄原型檔案）
- 無 docstring 的公開函數：14 個（+8 從新增的 farm_registry.py 和 data_broker.py）
  - 根目錄原型：dashboard.py `update_charts()`、wind_model.py 3 個
  - server/storage.py：`to_float()` x2（巢狀函數）
  - server/farm_registry.py：`to_dict()`, `from_row()`, `get_farm()`, `list_farms()`, `get_active_farm_id()`, `set_active_farm()`, `get_farm_dir()` — 新增模組
  - server/data_broker.py：`active_farm_id()` — 新增屬性
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：91 個（無變更）

## 今日新增功能

### 風向隨高度偏轉模型（#79）
- **物理原理**：受科氏力和地表摩擦影響，風向隨高度偏轉（Ekman 螺旋效應）。離岸典型偏轉率 0.05–0.15 °/m。
- **實作方式**：
  1. `wind_field.py`：新增 `blade_veer_offset_deg()` 靜態方法
  2. `turbine_physics.py`：新增 `wind_veer_rate` 個體差異參數（0.07–0.13 °/m），計算等效偏航誤差導致的功率損失
  3. `fatigue_model.py`：新增 veer 對塔架側向彎矩的淨側向力，以及葉片揮舞彎矩的側向力分量
  4. `docs/physics_model_status.md`：更新 §2.6 和 §5
- **物理效應**：
  - 葉片尖端偏轉差異：±R × veer_rate（R=35m, veer=0.1°/m → ±3.5°）
  - 塔架側向彎矩增加（veer 產生的淨側向推力）
  - 葉片揮舞 1P 不對稱增大（側向力隨方位角變化）
  - 功率因等效偏航誤差略微降低（cos² 效應）
- **影響範圍**：
  - 疲勞 DEL 增加（特別是塔架側向和葉片揮舞）
  - 與風切剖面（#71）效應疊加，使 1P 載荷更真實
  - 離岸風場模擬更貼近實際環境條件

## 建議行動

1. **同步 README.md API 列表**：新增的 farms API（4 個路由）尚未列於 README
2. **補充 farm_registry.py docstrings**：新增模組有 7 個公開函數缺少 docstring
3. **實作 #86 進階尾流模型**：Bastankhah-Porté-Agel 高斯尾流，改善風場級功率預估
4. **實作 #76 齒輪齒面接觸模型**：為 GMF 振動提供物理因果關係
5. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試
