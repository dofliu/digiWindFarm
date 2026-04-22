# digiWindFarm Daily Report

> 最後更新：2026-04-22

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-V6hEC`）：

- feat: couple air density to ambient temperature and humidity (#101)

近 24 小時主幹 `main` 合併摘要：

- [5ab4f32] Merge PR #100 — 大氣穩定度 α/TI 文件同步
- [b275bdb] docs: update project docs and daily report for atmospheric stability (#99)
- [cdaa177] feat: atmospheric stability couples diurnal cycle to shear α and TI (#99)
- [d5b9adb] Merge PR #98 — 偏航引發尾流偏轉文件同步
- [f96ec88] docs: update project docs and daily report for yaw-induced wake deflection (#97)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 關閉 | #97 | 偏航引發尾流偏轉 | 已於 PR #98 合併 main，補上完成註解並 close |
| 建立 | #101 | 空氣密度 ρ(T, RH) 動態耦合 | 今日建立並實作 |
| 實作 | #101 | 空氣密度耦合 | 新增 `WMET_AirDensity`，4 項自測全過 |
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

本日建立 1 個 issue（#101）、關閉 1 個（#97），符合「每次最多 3 個新 issue」規則。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #101 | 空氣密度 ρ(T, RH) 動態耦合 | enhancement, physics, auto-detected | 2026-04-22 | 已實作 |
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
| `simulator/` | 2026-04-22 | 0 | 無測試套件 | `engine.py` 每步計算 `air_density` 並傳遞 |
| `simulator/physics/` | 2026-04-22 | 0 | 無測試套件 | `turbine_physics` 接收 `air_density` kwarg 並更新 `PowerCurveModel.air_density`；`scada_registry` 新增 `WMET_AirDensity` |
| `wind_model.py`（根目錄） | 2026-04-22 | 0 | 無測試套件 | 新增 `get_air_density(ts, temp?, rh?)` |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案 |

## API Endpoints

共 62 個路由（61 HTTP + 1 WebSocket）。本日無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（10 個路由）仍未完整同步至 README 的 Core APIs 章節。

## 程式碼品質

- Lint 錯誤：115（核心模組 `server/` + `simulator/` 維持 0 錯誤）
- `ruff check simulator/ server/ wind_model.py` — All checks passed ✓
- `python -m py_compile simulator/engine.py simulator/physics/turbine_physics.py simulator/physics/scada_registry.py wind_model.py` — 4 個修改檔案全部通過
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：**100 個**（+1：`WMET_AirDensity`）

## 今日新增功能

### 空氣密度 ρ(T, RH) 動態耦合（#101）

**問題與物理原理**

`simulator/physics/power_curve.py` 與 `turbine_physics.py` 長期以 `air_density = 1.225 kg/m³` 常數計算氣動功率與推力：

- `P_aero = Cp × 0.5 × ρ × A × V³` — P 對 ρ 線性
- `F_thrust = 0.5 × ρ × A × Ct × V²` — F 對 ρ 線性

但實際大氣中 ρ 會依**溫度**與**濕度**顯著變動：

| 典型條件 | ρ (kg/m³) | 相對 1.225 | 物理意義 |
|----------|-----------|------------|----------|
| 標準 ISA（15 °C, 0% RH） | 1.2250 | ±0.0% | 基準 |
| 熱帶雨季（32 °C, 95% RH） | 1.1372 | −7.2% | 高溫 + 水氣稀釋 |
| 沙漠白天（40 °C, 40% RH） | 1.1147 | −9.0% | 高溫主導 |
| 溫帶夜間（0 °C, 50% RH） | 1.2908 | +5.4% | 冷空氣緻密 |
| 寒冷冬夜（−10 °C, 50% RH） | 1.3406 | +9.4% | 空氣最緻密 |
| 極冷乾燥（−20 °C, 30% RH） | 1.3500 | +10.2% | clamp 上限 |

兩極差異達 15%，代表**冷冬空氣可比熱夏空氣多產生約 10–12% 的功率**，這是真實風場不可忽略的季節/日週期特徵，先前完全未被模擬。

**公式**

理想氣體定律 + Buck/Magnus 飽和蒸氣修正：

```
ρ_dry    = P / (R_d × T_K)                      R_d = 287.058 J/(kg·K)
e_s(T_C) = 611.2 · exp(17.67 · T_C / (T_C + 243.5))    # 飽和蒸氣壓 (Pa)
e        = (RH/100) × e_s                        # 實際蒸氣壓
ρ_moist  = ρ_dry × (1 − 0.378 · e / P)           # 水蒸氣較輕，總體密度下降
```

海平面 `P = 101325 Pa`，結果 clamp 至 [0.95, 1.35]。

**實作方式**

1. `wind_model.py::WindEnvironmentModel`：
   - `get_air_density(timestamp, ambient_temp=None, humidity=None) -> float`
   - `ambient_temp` / `humidity` 可選 — 若 engine 已計算好就直接傳入，避免再度呼叫 `_weather._pressure_state` 等並污染 RNG（同 #99 設計）

2. `simulator/engine.py`：每步共用一組 `ambient_temp`、`ambient_humidity`，新增

   ```python
   air_density = self.wind_model.get_air_density(
       sim_time, ambient_temp=ambient_temp, humidity=ambient_humidity
   )
   ```

   傳入每台 `turbine.step(..., air_density=air_density)`。**全場共享同一 ρ**（物理事實：同一氣團）。

3. `simulator/physics/turbine_physics.py`：
   - `step()` 新增 `air_density: float = 1.225` kwarg
   - `self._air_density = clamp(...)`；**最關鍵：`self.power_curve.air_density = self._air_density`**，使下一次 `get_power_cp` 內部即使用最新的 ρ
   - 新增 SCADA 輸出 `"WMET_AirDensity"`（`round(ρ, 4)`）
   - `__init__` 與 `reset()` 初始化 `self._air_density = self.spec.air_density`

4. `simulator/physics/scada_registry.py`：
   - 新增 `ScadaTag("WMET_AirDensity", ..., "REAL32", "kg/m3", ..., 0.95, 1.35)`
   - **SCADA 總數從 99 增為 100**

**物理效應（自測驗證）**

| 測試 | 預期 | 實測 | 結果 |
|------|------|------|------|
| 15 °C / 0% RH（ISA） | 1.225 ± 0.005 | 1.2250 | ✓ |
| 25 °C / 65% RH（日常） | 約 1.17 | 1.1748 | ✓ |
| 0 °C / 50% RH | ≈ 1.29 | 1.2908 | ✓ |
| −10 °C / 50% RH | ≈ 1.34 | 1.3406 | ✓ |
| −20 °C / 30% RH | ≥ 1.35（hit clamp） | 1.3500 | ✓ |
| 32 °C / 95% RH（熱帶） | 約 1.14 | 1.1372 | ✓ |
| 40 °C / 40% RH（沙漠） | 約 1.11 | 1.1147 | ✓ |
| 冷/熱功率比（0°C 50% vs 30°C 80%） | 1.10–1.12 | 1.123 | ✓ |

**為何這是物理「因」而非輸出偏移**

- 直接源於氣體狀態方程與水蒸氣的摩爾質量差（M_v=18 vs M_a=29），為物理定律
- ρ 變化經由 `PowerCurveModel` 內**原本就存在**的 `air_density` 代入點傳遞；P、F、Ct 推力估算、疲勞 DEL 全路徑自動耦合，**無需**直接修改功率輸出 tag
- 全場共享同一 ρ 反映「同一氣團」的物理事實；per-turbine 差異則留給 `wind_sensor_scale` 等既有個體路徑
- 手動 override ambient_temp 會產生穩定的中性濕度，ρ 仍會依當時溫度自然計算，不需額外分支邏輯

**與其他模型的耦合**

- **#89（環境濕度）**：濕度路徑共用；本 issue 走**進氣密度**，#89 走**散熱效率**，兩者互為補充而非重複
- **#99（大氣穩定度）**：夜間穩定度高 → 溫度低 → ρ 升高 → 功率升高；日間對流 → 溫度高 → ρ 降低。日週期協同加強
- **#71 / #72（風切、葉片不平衡）**：塔基推力 F 亦 ∝ ρ，塔基疲勞 DEL 會在季節/日週期上同步振動
- **#93 / #95 / #97（尾流）**：尾流 Ct 係經驗公式未依 ρ 縮放，未來若要做「尾流推力與風場動能耗散」一致性校驗，ρ 會是必要輸入

## 建議行動

1. **長時段資料品質驗證**：以 `examples/data_quality_analysis.py` 跑 **7 天自動模式**（time_scale=144），觀察：
   - `WMET_AirDensity` 日週期（清晨高、午後低）
   - 冷暖季基準差異（ρ 在冬夏月之間應有 ~5% 差距）
   - 相同風速時段的平均功率是否呈現 ρ-相關變動
2. **前端視覺化**：Dashboard 可於 weather widget 加上即時 ρ 與相對 1.225 的差異百分比（冷空氣 +5% 的提示能直觀表達物理因）
3. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值
4. **實作 #57 前端 RUL 視覺化**：後端已就緒
5. **建立 pytest 測試套件（#52）**：ρ(T, RH)、α(s)、TI_mult(s)、override 中性化為理想首批單元測試
6. **未來擴充**：
   - 大氣壓 P 的日週期/天氣鋒面依賴（目前固定 P=101325 Pa；實測可偏 ±2%）
   - 高海拔風場的海拔修正（離岸通常 ~0 m，陸上山坡風場可偏 5–10%）
   - 冷空氣對葉片結冰閾值的聯合觸發（`blade_icing` 故障可視 ρ 與 T 同時判斷）
7. **同步 `/api/farms` 10 個路由至 README.md**：仍未完成
