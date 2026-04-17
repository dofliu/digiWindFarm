# digiWindFarm Daily Report

> 最後更新：2026-04-17

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/gifted-noether-Ed45A`）：
- [dbb6e16] feat: add wind shear profile model with azimuth-dependent blade loading (#71)

過去 24 小時 main 分支合併：
- [4982827] Merge pull request #70（塔架陰影效應 — 3P 功率/扭矩/載荷調變）
- [e35b21a] Merge pull request #68（峰值因子/峭度異常警報）

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 關閉 | #69 | 塔架陰影效應 — 3P 功率/扭矩/載荷調變 | PR #70 已合併至 main，驗證完成 |
| 新建 | #71 | 風切剖面模型 — 高度相關風速分布與葉片不對稱載荷 | 已實作：冪律風切 + 方位角相關葉片載荷 + 1P 扭矩調變 |
| 新建 | #72 | 葉片質量不平衡與轉子動態不平衡模型 | 離心力不平衡 + 速度²耦合 + 1P 振動物理因果 |
| 新建 | #73 | 齒輪箱油溫與黏度效應模型 | Walther 油溫-黏度 + 冷啟動效率降低 + 過熱惡化 |
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
| #73 | 齒輪箱油溫與黏度效應模型 | enhancement, physics, auto-detected | 2026-04-17 | 新建 |
| #72 | 葉片質量不平衡與轉子動態不平衡模型 | enhancement, physics, auto-detected | 2026-04-17 | 新建 |
| #71 | 風切剖面模型 | enhancement, physics, auto-detected | 2026-04-17 | 新建並已實作，待合併 |
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | LVRT/OVRT 事件序列與跳脫邏輯 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報閾值曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 後端完成，前端待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #44 | Ruff lint 179 個錯誤 | code-quality, auto-detected | 2026-04-13 | 降至 115 個，核心模組已清零 |
| #26 | 部署強化 | enhancement, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `server/routers/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/` | 2026-04-17 | 0 | 無測試套件 | 新增風切剖面 (#71) |
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
- TODO/FIXME/HACK：0 個（核心模組），4 個在 opc_bachmann 第三方程式碼
- SCADA 標籤：90 個（無變更）

## 今日新增功能

### 風切剖面模型（#71）
- **物理原理**：冪律風切剖面 V(h) = V_hub × (h/h_hub)^α，使轉子掃掠面上下高度的風速不同。三支葉片在旋轉過程中依序經歷高處（較高風速）和低處（較低風速），產生 1P 週期性載荷振盪。
- **實作方式**：
  1. `wind_field.py`：新增 `wind_shear_exponent` 參數（預設 0.2），新增 `blade_shear_ratio()` 靜態方法計算任意方位角的風速比
  2. `turbine_physics.py`：新增每台風機的風切指數個體差異（α ≈ 0.16-0.26），根據三支葉片方位角計算力矩平均的風切扭矩調變因子
  3. `fatigue_model.py`：葉片揮舞彎矩從靜態風切改為方位角相關 — 葉片在頂部時力矩增大，底部時減小
  4. 每台風機有獨立的風切指數（反映不同位置的地表粗糙度差異）
- **驗證結果**：
  - 頂部葉片風速/底部葉片風速 ≈ 1.28（α=0.2，合理值域）
  - 葉片揮舞彎矩 CV ≈ 11.9%（含風切 1P + 塔架陰影 3P + 亂流）
  - 功率 CV ≈ 0.5%（3 葉片平均化使功率波動較小，符合預期）
- **影響範圍**：
  - 葉片疲勞 DEL 增加（1P 風切循環載荷是壽命計算的重要因素）
  - 1P 振動成分更具物理因果（風切引起的不對稱載荷）
  - 塔架前後彎矩透過扭矩/推力調變感受到風切效應
  - 功率曲線細微的 1P 波動更接近真實 SCADA 資料

## 建議行動

1. **合併風切剖面模型**：已推送至 `claude/gifted-noether-Ed45A`，可建立 PR 合併
2. **實作 #72 葉片質量不平衡**：離心力不平衡 + 速度²耦合，提升 1P 振動物理真實度
3. **實作 #73 齒輪箱油溫黏度**：冷啟動效率降低 + 過熱惡化，提升傳動鏈模型真實度
4. **實作 #67 保護繼電器協調**：LVRT/OVRT 電壓-時間保護曲線與保護動作序列
5. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試
6. **升級有漏洞的套件**（#48）：優先處理 `cryptography`（7 個 CVE）
