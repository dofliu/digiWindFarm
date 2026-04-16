# digiWindFarm Daily Report

> 最後更新：2026-04-16（第三次）

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/gifted-noether-X6J7D`）：
- [fe856bb] feat: add tower shadow effect with 3P torque/thrust/load modulation (#69)

過去 24 小時 main 分支合併：
- [e35b21a] Merge pull request #68（峰值因子/峭度異常警報）
- [f54dbf8] Merge pull request #66（齒輪嚙合邊帶分析模型）
- [0e0e409] Merge pull request #65（BPFO/BPFI 軸承缺陷頻率模型）
- [fbcd68a] Merge pull request #64（塔架 SDOF 動態響應）
- [029b929] Merge pull request #63（Cp 氣動模型 + docstrings）

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 新建 | #69 | 塔架陰影效應 — 3P 功率/扭矩/載荷調變 | TODO/physics_model_status 有待辦但無對應 issue，已建立並實作 |
| 進展 | #69 | 塔架陰影效應 | 已實作：轉子方位角追蹤 + 高斯型塔架陰影 3P 調變，已推送 |
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
| #69 | 塔架陰影效應 — 3P 功率/扭矩/載荷調變 | enhancement, physics, auto-detected | 2026-04-16 | 新建並已實作，待合併 |
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
| `server/` | 2026-04-16 | 0 | 無測試套件 | 無變更 |
| `server/routers/` | 2026-04-16 | 0 | 無測試套件 | 無變更 |
| `simulator/` | 2026-04-16 | 0 | 無測試套件 | 無變更 |
| `simulator/physics/` | 2026-04-16 | 0 | 無測試套件 | 新增塔架陰影效應 (#69) |
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
- SCADA 標籤：90 個（無變更）

## 今日新增功能

### 塔架陰影效應（#69）
- **物理原理**：上風式三葉片風機的葉片通過塔架前方時，受勢流效應影響，局部風速降低。三支葉片依序通過塔架，產生每轉三次（3P）的確定性功率/扭矩/推力振盪。
- **實作方式**：
  1. `turbine_physics.py`：新增轉子方位角（`_rotor_azimuth`）追蹤，每個時間步進更新
  2. 高斯型塔架陰影模型：`deficit = A × exp(-0.5 × ((θ-π)/σ)²)`，σ = 0.15 rad
  3. 三支葉片的陰影效應疊加，產生 3P 調變因子
  4. 調變因子同時作用於氣動扭矩、推力和功率
  5. 每台風機有獨立的陰影振幅（±3% 個體差異），典型值 A ≈ 12%/blade
  6. `fatigue_model.py`：接收轉子方位角，對葉片揮舞彎矩加入 3P 塔架陰影調變
- **驗證結果**：
  - 功率信號：3P 振盪約 0.6% CV（經變流器平滑後的預期值）
  - 葉片揮舞彎矩：3P 振盪約 2.7% CV（直接反映塔架陰影載荷）
  - 效應自然傳播至傳動鏈扭振、振動、疲勞計算
- **影響範圍**：
  - 功率曲線更接近真實 SCADA 資料
  - 葉片疲勞 DEL 增加（3P 循環載荷是壽命計算的重要因素）
  - 塔架前後彎矩出現 3P 成分（透過推力調變）

## 建議行動

1. **合併塔架陰影效應**：已推送至 `claude/gifted-noether-X6J7D`，可建立 PR 合併
2. **實作 #67 保護繼電器協調**：LVRT/OVRT 電壓-時間保護曲線與保護動作序列，提升電氣模型真實度
3. **完成 #58 頻帶警報閾值曲線**：各頻帶加入基於工況的動態警報閾值曲線
4. **建立測試套件**（#52）：核心物理模型和 API endpoint 仍無自動化測試
5. **升級有漏洞的套件**（#48）：優先處理 `cryptography`（7 個 CVE）
6. **考慮新增風切效應**：目前葉片揮舞載荷包含簡化風切，但缺少完整的葉片位置相關風速分布
