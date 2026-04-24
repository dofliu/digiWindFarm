# digiWindFarm Daily Report

> 最後更新：2026-04-24

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-mZpPO`）：

- feat: couple ambient pressure dynamically to synoptic weather state (#106)

近 48 小時主幹 `main` 合併摘要：

- [6728bae] Merge PR #105 — 尾流誘發紊流增強文件同步
- [d4bb997] docs: update project docs and daily report for wake-added TI (#103)
- [590c2d7] feat: add wake-added turbulence intensity (Crespo-Hernández) (#103)
- [f1e085e] Merge PR #102 — 空氣密度耦合文件同步
- [f01b9a5] docs: update project docs and daily report for air density coupling (#101)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立+實作 | #106 | 大氣壓 P(t) 動態耦合 | 新 `WMET_AmbPressure`（hPa），7 項自測全過；SCADA 102 個 |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線待做 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 115 個錯誤 | 核心模組 0 錯誤 |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日建立 1 個 issue（#106，源於昨日建議行動 7a）、關閉 0 個。符合「每次最多 3 個新 issue」規則。
本日建立 1 個 issue（#103）、關閉 1 個（#101）、開 1 個 PR（#104），符合「每次最多 3 個新 issue / 1 個 PR」規則。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #106 | 大氣壓 P(t) 動態耦合 | enhancement, physics, auto-detected | 2026-04-24 | 已實作 |
| #67 | 完整保護繼電器協調 LVRT/OVRT | enhancement, physics, auto-detected | 2026-04-16 | 電壓-時間曲線 |
| #58 | 頻譜振動警報閾值與邊帶分析 | enhancement, physics, auto-detected | 2026-04-15 | 頻帶警報曲線待做 |
| #57 | 疲勞警報閾值與 RUL 估算 | enhancement, physics, auto-detected | 2026-04-15 | 前端 RUL 待做 |
| #52 | 缺少自動化測試套件 | auto-detected, code-quality | 2026-04-14 | 無進展 |
| #51 | 警報處理透過 RAG 機制 | — | 2026-04-14 | 用戶功能需求 |
| #50 | 外部擷取資料 API | — | 2026-04-14 | 用戶功能需求 |
| #48 | pip-audit 17 個安全漏洞 | security, auto-detected | 2026-04-13 | 未升級 |
| #44 | Ruff lint 115 個錯誤 | code-quality, auto-detected | 2026-04-13 | 核心模組 0 錯誤 |
| #26 | 部署強化 | enhancement, platform, deployment | 2026-04-05 | Docker 已完成 |
| #24 | 歷史資料儲存架構 | enhancement, platform | 2026-04-05 | 架構決策待定 |

## 模組狀態

| 模組 | 最後修改 | TODO 數 | 測試 | 備註 |
|------|----------|---------|------|------|
| `server/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| `simulator/` | 2026-04-24 | 0 | 無測試套件 | `engine.py` 每步取得 `ambient_pressure` 並傳遞 |
| `simulator/physics/` | 2026-04-24 | 0 | 無測試套件 | `turbine_physics` 新增 `ambient_pressure_pa` kwarg 與 `WMET_AmbPressure` 輸出；`scada_registry` 新增 `WMET_AmbPressure` |
| `wind_model.py`（根目錄） | 2026-04-24 | 0 | 無測試套件 | 新增 `get_ambient_pressure(ts)`；`get_air_density` 接受 `pressure_pa` kwarg |
| `simulator/` | 2026-04-23 | 0 | 無測試套件 | `engine.py` 將 `wake_added_ti` 傳入 `turbine.step` |
| `simulator/physics/` | 2026-04-23 | 0 | 無測試套件 | `wind_field` 計算 wake-added TI；`turbine_physics` 接收並寫入 `WMET_WakeTi`；`scada_registry` 新增 1 個標籤 |
| `wind_model.py`（根目錄） | 2026-04-22 | 0 | 無測試套件 | 無變更（沿用 #101 air density） |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案 |

## API Endpoints

共 63 個路由（62 HTTP + 1 WebSocket）。本日無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（10 個路由）仍未完整同步至 README 的 Core APIs 章節。

## 程式碼品質

- Lint 錯誤：115（核心模組 `server/` + `simulator/` 維持 0 錯誤）
- `ruff check simulator/ server/ wind_model.py` — All checks passed ✓
- `python -m py_compile simulator/engine.py simulator/physics/turbine_physics.py simulator/physics/scada_registry.py wind_model.py` — 4 個修改檔案全部通過
- `python -m py_compile simulator/engine.py simulator/physics/turbine_physics.py simulator/physics/scada_registry.py simulator/physics/wind_field.py wind_model.py` — 5 個檔案全部通過
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：**102 個**（+1：`WMET_AmbPressure`）

## 今日新增功能

### 大氣壓 P(t) 動態耦合 — #106

**問題與物理原理**

#101 已把空氣密度 ρ 接上環境溫度 T 與濕度 RH，但 `wind_model.py::get_air_density` 內**大氣壓仍硬編碼為 101325 Pa**（海平面 ISA 標準）。實際風場中 P 會因天氣鋒面持續變動：

| 情境 | 典型 P | ΔP | Δρ（同 T, RH） |
|------|-------|-----|----------------|
| 穩定高壓 | 1028 hPa | +15 hPa | +1.5% |
| 平均 | 1013 hPa | 0 | 基準 |
| 活躍低壓/鋒面 | 998 hPa | −15 hPa | −1.5% |
| 颱風 | 950 hPa | −63 hPa | −6.3% |

`_weather._pressure_state` 已在 `WeatherSystem` 內自然演化（OU 隨機遊走 + 鋒面事件），但從未轉換為實際 Pa 並餵回 ρ。這使 `WMET_AirDensity` 僅反映 T/RH 變動，少了鋒面驅動的一階時間變異。

**公式與實作**

```
P(t) = 101325 + pressure_state · 1500 Pa        clamp [90000, 105000]
```

- 係數 1500 Pa ≈ 15 hPa 對應中緯度鋒面典型振幅
- `pressure_state` 為既有 [−1, +1] 連續分數，τ ≈ 2 h，鋒面週期 2–7 天
- 手動 override 強制 P = 101325 Pa（ISA 基準，保持 demo 穩定）
`simulator/physics/wind_field.py::PerTurbineWind._update_wake_factors` 在 #93/#95/#97 已實作 Bastankhah 速度赤字 + Larsen DWM 擺動 + Bastankhah 偏航偏轉。但**尾流的紊流增強**（即下游風機因上游尾流剪切層而 TI 上升）尚未模擬：

- 下游 1–10 D：實測 TI 可較自由流上升 20%–80%
- 影響下游風機**疲勞 DEL**、功率變動、控制器負載
- 對叢聚式 / 多排風場影響顯著
- IEC 61400-1 Annex E 已將此列為強制建模項目

**公式**

Crespo & Hernández (1996)：

```
TI_added(x, r=0) = 0.73 · a^0.8325 · TI_amb^0.0325 · (x/D)^(-0.32)
a = 0.5 · (1 − √(1 − Ct))     （軸向誘導因子）
```

多重尾流疊加（IEC 61400-1 Annex E sum-of-squares）：

```
TI_w² = Σ_i TI_w,i²
TI_eff² = (TI_amb · pocket_mult)² + TI_w²
```

1. `wind_model.py::WindEnvironmentModel`
   - 新增 `get_ambient_pressure(timestamp) -> float`
   - `get_air_density` 新增 `pressure_pa: Optional[float]` kwarg；未傳時自動呼叫 `get_ambient_pressure`
2. `simulator/engine.py::_run_one_step`
   - 每步計算 `ambient_pressure` 一次，連同 T、RH 一起傳入 `get_air_density`
   - 同值透過 `ambient_pressure_pa` kwarg 傳給每台 `turbine.step`（物理事實：全場共享同一氣團）
3. `simulator/physics/turbine_physics.py`
   - `step()` 新增 `ambient_pressure_pa: float = 101325.0` kwarg
   - 輸出 `WMET_AmbPressure = round(ambient_pressure_pa / 100, 1)`（單位 hPa）
4. `simulator/physics/scada_registry.py`
   - 新增 `WMET_AmbPressure`（REAL32, hPa, 900–1050）→ **SCADA 總數 101 → 102**

**物理效應（自測驗證）**

| 測試情境 | 預期 | 實測 | 結果 |
|----------|------|------|------|
| T1 reference state=0 | P=1013.25 hPa, ρ=1.2250 | P=1013.25, ρ=1.2250 | ✓ |
| T2 state=+1（高壓） | P=1028.25 hPa, ρ +1.5% | P=1028.25, ρ=1.2431 (+1.48%) | ✓ |
| T3 state=−1（低壓） | P=998.25 hPa, ρ −1.5% | P=998.25, ρ=1.2068 (−1.49%) | ✓ |
| T4 Δρ at T=15°C/RH=50% | ~3% | 3.01% | ✓ |
| T5 override 鎖定 | P=101325 Pa | P=101325.0 Pa | ✓ |
| T6 6 h 自然演化 | 合理擺動（幾 hPa） | 1012.9–1020.5 hPa（7.6 hPa） | ✓ |
| T7 24 h 自然擺動 | 平均近 1013，範圍 ±15 | 1012–1023，均值 1018 | ✓ |

引擎 end-to-end 驗證：手動設 `pressure_state=0.5` 5 步後，`WMET_AmbPressure` = 1020.7 hPa、`WMET_AirDensity` = 1.21；切換至 `pressure_state=-0.8`，P 轉為 1001.2 hPa、ρ 降至 1.14。經含感測器雜訊 + 漂移後數值仍一致。

**為何這是物理「因」而非輸出偏移**

- 理想氣體定律是 ρ 的第一性來源；P 改變必然線性影響 ρ
- `_pressure_state` 已自然存在於 `WeatherSystem` 並有 OU + 鋒面時間尺度
- 全鏈路只替換一個常數（`get_air_density` 中的 `p_atm`）
- 下游耦合（power P ∝ ρ·V³、thrust F ∝ ρ·V²、塔基 FA 疲勞 DEL）自動沿既有路徑反映
- 14 台風機共用同一 P（真實氣象事實），但仍各自帶感測器漂移、地形偏差
**實作方式**

1. `simulator/physics/wind_field.py`：
   - 新增 `_wake_added_ti` 陣列；`_update_wake_factors` 在既有 source-target 雙迴圈中**同時累計**速度赤字與附加 TI（共用 σ、x_down、r_lat、meander、yaw deflection），無重複計算
   - 新增 `get_wake_added_ti(turbine_index)` getter
   - `step()` 將「pocket TI 倍率」與「wake-added TI」以平方相加再餵入 AR(1) 紊流產生器：`eff_mult = √(pocket_mult² + (wake_ti / TI_amb)²)`

2. `simulator/physics/turbine_physics.py`：
   - `step()` 新增 `wake_added_ti: float = 0.0` kwarg，clamp 至 [0, 0.40]
   - `__init__` / `reset()` 初始化 `self._wake_added_ti = 0.0`
   - 輸出 SCADA `"WMET_WakeTi"`（百分比格式）

3. `simulator/engine.py`：
   - 取得 `wake_added_ti = self._per_turbine_wind.get_wake_added_ti(idx)`
   - 傳入 `turbine.step(..., wake_added_ti=wake_added_ti, ...)`

4. `simulator/physics/scada_registry.py`：
   - 新增 `ScadaTag("WMET_WakeTi", ..., "REAL32", "%", ..., 0, 40)`
   - **SCADA 總數從 100 增為 101**

**物理效應（自測 7 項驗證）**

| 測試 | 預期 | 實測 | 結果 |
|------|------|------|------|
| 單機獨立（無上游） | 0% | 0.00% | ✓ |
| 5D 下游 (V=8 m/s, TI=10%) | 5–18% | 13.98% | ✓ |
| 12D 遠場下游 | < 5D 值 | 10.19% | ✓ |
| 風向 270° → 90° 對稱反轉 | 上下游互換 | 互換成功 | ✓ |
| 4 機一列疊加 | 遞增 | T1=12.95%, T2=16.92%, T3=19.43% | ✓ |
| Ct 敏感度（V=8 vs V=18） | Region2 > Region3 | 13.98% > 4.96% | ✓ |
| AR(1) 整合（下游/上游 σ 比） | > 1.0 | 2.12 | ✓ |

**為何這是物理「因」而非輸出偏移**

- 直接套用 Crespo-Hernández 經驗公式（IEC 61400-1 Annex E 引用）
- 透過既有 `_turb_gens[i].step(..., ti_local, ...)` 路徑傳遞，下游風機 wind_speed σ 自然上升
- 葉片載荷 / 疲勞 DEL（#41 #57）會因下游 σ_v 上升而自然加重，**不需修改疲勞輸出**
- 與 #93 共用迴圈與幾何，無重複計算
- pocket TI（#91）為**空間獨立來源**，與 wake TI 物理上相互獨立 → 平方相加合理

**完整尾流模型現況**

| 機制 | Issue | 方法 |
|------|-------|------|
| 速度赤字 ΔU/U | #93 | Bastankhah-Porté-Agel Gaussian |
| 中心線擺動 σ_θ | #95 | Larsen-DWM AR(1) |
| 偏航偏轉 δ_y | #97 | Bastankhah 2016 θ_c |
| **附加紊流 TI_w** | **#103** | **Crespo-Hernández** |

- **#101（ρ(T, RH)）**：本 issue 把理想氣體三變數鏈的第三項 P 也接上，ρ = f(T, RH, P) 完整閉合
- **#99（大氣穩定度）**：同源使用 `_pressure_state`（低壓系統 → 雲層 → |s| 壓低），兩者協同但不重複
- **#89（濕度散熱）**：本更動不影響 nacelle/cabinet 散熱層（該層用 RH + ΔT_dew）
- **#57（疲勞 DEL / RUL）**：±1.5% ρ 擺動 → 推力 F 同步擺動 → 塔基 FA DEL 會有額外低頻調變

## 建議行動

1. **長時段資料品質驗證**：`examples/data_quality_analysis.py` 跑 **7 天自動模式**（time_scale=144），觀察：
   - `WMET_AmbPressure` 出現鋒面通過事件（連續 12–24 h 下降 10 hPa 以上）
   - `WMET_AirDensity` 與 `WMET_AmbPressure` 在鋒面時段強相關（r > 0.6）
   - 鋒面時段 `WTUR_TotPwrAt` 是否呈現 1–2% 系統性下修（常規氣壓係數應）
2. **前端視覺化**：Dashboard 可加「氣壓趨勢」卡片，與溫濕度並列，凸顯鋒面事件
3. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值
4. **實作 #57 前端 RUL 視覺化**：後端已就緒
5. **建立 pytest 測試套件（#52）**：`get_ambient_pressure` 與 `get_air_density` 的三變數單元測試是理想首批
6. **未來擴充**：
   - 半日大氣潮 S2（熱帶 ±1.5 hPa、中緯度 ±0.3 hPa），若 #106 後觀測到日週期過於平靜再加
   - 颱風 / 極端低壓事件（pressure_state 需擴展 clamp）→ 可作單獨事件注入 API
   - 海拔修正（目前假設海平面；若部署於山地風場需加 Hypsometric 公式）
   - 壓力引起的水平梯度力對風向偏移（目前 `weather_shift` 已用 `_pressure_state`，互不重複）
7. **同步 `/api/farms` 10 個路由至 README.md**：仍未完成

## 通知

已透過 email 發送日報至 moredof@gmail.com（請依專案實際 email 通知管道配置執行）。
四者形成「動量赤字 + 紊流增強 + 空間動態」的完整尾流物理模型。

## 建議行動

1. **長時段資料品質驗證**：以 `examples/data_quality_analysis.py` 跑 **24 小時自動模式**，觀察：
   - `WMET_WakeTi` 隨風向變化（不同風向下游機輪換）
   - 多排風場（row 2、3）的 TI 累積 vs row 1
   - 下游風機的 fatigue DEL 是否同步上升 5–15%
2. **前端視覺化**：Dashboard 可在 weather widget 加上 wake-added TI 與環境 TI 的疊加比較
3. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值
4. **實作 #57 前端 RUL 視覺化**：後端已就緒
5. **建立 pytest 測試套件（#52）**：wake-added TI、ρ(T, RH)、α(s) 都是理想首批單元測試
6. **未來擴充**：
   - **curled-wake 模型**：偏航 wake 的 counter-rotating vortex pair 細節（Bastankhah 線性式已涵蓋主項）
   - **wake recovery 紊流**：尾流末端 TI 恢復至自由流的時間常數
   - **大氣壓 P 的日週期 / 鋒面依賴**（目前固定 P=101325 Pa；實測可偏 ±2%，與 #101 air density 串聯）
   - **大氣穩定度對尾流長度的影響**：穩定大氣下尾流持續更遠（與 #99 串聯）
7. **同步 `/api/farms` 10 個路由至 README.md**：仍未完成
