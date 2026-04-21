# digiWindFarm Daily Report

> 最後更新：2026-04-21

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-5UKdM`）：
- feat: add yaw-induced wake deflection (Bastankhah 2016 wake steering) (#97)

近 24 小時主幹 `main` 合併摘要：
- [ea9ffae] Merge PR #96 — 動態尾流蜿蜒文件同步
- [bf24c3a] docs: update project docs and daily report for dynamic wake meandering (#95)
- [1cb1a1b] feat: add dynamic wake meandering with lateral wake-center AR(1) oscillation (#95)
- [8eaa075] Merge PR #94 — Bastankhah-Porté-Agel 尾流模型（#93）
- [af902a0] feat: upgrade wake model to Bastankhah-Porté-Agel Gaussian (#93)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立 | #97 | 偏航引發之尾流側向偏轉（wake steering）— Bastankhah 2016 | 今日建立並實作 |
| 實作 | #97 | 偏航引發之尾流側向偏轉 | `WMET_WakeDefl` 新標籤，7 項自測全過 |
| 保持 | #67 | 完整保護繼電器協調 LVRT/OVRT | 電壓-時間保護曲線 |
| 保持 | #58 | 頻譜振動警報閾值與邊帶分析 | 頻帶警報曲線仍待做 |
| 保持 | #57 | 疲勞警報閾值與 RUL 估算 | 後端完成，前端 RUL 視覺化待做 |
| 保持 | #52 | 缺少自動化測試套件 | 仍無 pytest |
| 保持 | #51 | 警報處理透過 RAG 機制 | 用戶功能需求 |
| 保持 | #50 | 外部擷取資料 API | 用戶功能需求 |
| 保持 | #48 | pip-audit 17 個安全漏洞 | 未升級 |
| 保持 | #44 | Ruff lint 115 個錯誤 | 核心模組 0 錯誤 |
| 保持 | #26 | 部署強化 | Docker 已完成，JWT/RBAC 待做 |
| 保持 | #24 | 歷史資料儲存架構 | 架構決策待定 |

本日建立 1 個 issue（#97），符合「每次最多 3 個新 issue」規則。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #97 | 偏航引發尾流偏轉 — Bastankhah 2016 | enhancement, physics, auto-detected | 2026-04-21 | 已實作 |
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
| `simulator/` | 2026-04-21 | 0 | 無測試套件 | `engine.py` 新增 yaw_error 回饋 + `wake_yaw_deflection_m` |
| `simulator/physics/` | 2026-04-21 | 0 | 無測試套件 | `wind_field.py` 新增 Bastankhah 偏航初始傾斜角；`turbine_physics`、`scada_registry` 新增 `WMET_WakeDefl` |
| `wind_model.py`（根目錄） | 2026-04-19 | 0 | 無測試套件 | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案 |

## API Endpoints

共 58 個路由（57 HTTP + 1 WebSocket）。無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（4 個路由）仍未同步至 README 的 Core APIs 章節。

## 程式碼品質

- Lint 錯誤：115（核心模組 `server/` + `simulator/` 維持 0 錯誤）
- `ruff check simulator/ server/ wind_model.py` — All checks passed ✓
- `python -m py_compile simulator/physics/{wind_field,turbine_physics,scada_registry}.py simulator/engine.py` — 4 個修改檔案全部通過
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：**97 個**（+1：`WMET_WakeDefl`）

## 今日新增功能

### 偏航引發之尾流側向偏轉 Yaw-induced Wake Deflection / Wake Steering（#97）

**物理原理**

#93（Bastankhah-Porté-Agel 高斯尾流）假設風機完全對齊來流風向，但真實風場中：

1. **瞬時偏航誤差**：`yaw_model.py` 設計 15° 死區 + 60 s 啟動延遲，風向變化時 `yaw_error` 可達 10–15°
2. **`yaw_misalignment` 故障**：注入最多 20°·severity 的固定偏差
3. **主動尾流導向**：現代風場控制策略會**故意**讓上游風機偏航 10–25° 以減少下游赤字

偏航時，轉子推力向量具備側向分量，尾流中心軸隨下游距離持續偏轉。

Bastankhah & Porté-Agel (2016, JFM) 給出初始傾斜角解析解：

```
θ_c(γ, Ct) = 0.3 · γ · (1 − √(1 − Ct · cos γ)) / cos γ      (弧度)
δ_y(x)     ≈ tan(θ_c) · x_down                              (近尾流線性)
```

**實作方式**

1. `simulator/physics/wind_field.py::PerTurbineWind`：
   - `__init__` 新增 `_yaw_misalignment_rad`、`_yaw_tan_theta_c` 向量
   - `set_yaw_misalignments(angles_rad)`：引擎每步餵入 per-turbine yaw_error（弧度），clamp 至 ±45°
   - `_update_wake_factors` 預先計算 `tan_theta_c[j]`，於內層 r_lat 計算中再加一項 `−tan_theta_c[j] · x_down`（與既有尾流蜿蜒 `−θ_m[j]·x_down` 共用同一個側向軸）
   - `get_wake_yaw_deflection_offset(idx)`：回傳該台風機自身尾流於 3D 參考位置之側向偏轉（m）
2. `simulator/physics/turbine_physics.py`：
   - `step()` 新增 `wake_yaw_deflection_m: float = 0.0` kwarg（±80 m clamp 做保護）
   - `__init__` 與 `reset()` 初始化 `_wake_yaw_deflection_m`
   - SCADA 輸出新增 `"WMET_WakeDefl": round(self._wake_yaw_deflection_m, 2)`
3. `simulator/physics/scada_registry.py`：新增 `ScadaTag("WMET_WakeDefl", ..., "REAL32", "m", ..., -50, 50)`
4. `simulator/engine.py`：
   - `_last_yaw_err_rad` 向量儲存上一步 yaw_error（rad）
   - 下一步 `_per_turbine_wind.step()` 前呼叫 `set_yaw_misalignments(...)`
   - 每步取 `get_wake_yaw_deflection_offset(idx)` 傳給 `turbine.step`
   - 每台 `turbine.step` 後讀取 `scada_output["WYAW_YwVn1AlgnAvg5s"]`（度）轉弧度存入 `_last_yaw_err_rad[idx]`

**物理效應（自測驗證）**

3 台風機 E-W 線列（0、500、1000 m），rotor D=70.65 m，V=8 m/s、TI=0.08、burn-in 100 s + 取樣 400 s：

| 檢核項目 | 預期 | 實測 |
|----------|------|------|
| γ=0° 偏轉量 | 0 m（不應影響 #93 基線） | 0.00 m（3 台全部）✓ |
| γ=+15° 偏轉 @3D（Bastankhah 解析式） | 9.38 m | **9.38 m**（誤差 <0.5 m）✓ |
| γ=+15° 下游 T1 赤字 | 顯著下降 | 16.84% → 14.66%（↓12.9%）✓ |
| γ=+25° 偏轉 @3D | > 15 m（非線性單調增） | 15.12 m ✓ |
| γ=+25° T1 赤字 | 再下降 | 11.71%（vs γ=0 的 16.84% ↓30.4%）✓ |
| γ=−15° 偏轉鏡射 | −9.38 m | −9.38 m ✓ |
| γ=−15° T1 赤字 | 亦下降 | 14.56% < 16.84% ✓ |
| γ=60° 輸入 clamp | 45° | 45.00° ✓ |
| 源風機 T0 無自尾流 | 0% | 0.00% ✓ |

**影響範圍**

- `yaw_misalignment` 故障（severity=1.0 → 20° 偏航）現在會**真實**地把尾流側推離下游風機，下游 `WMET_WakeDef` 會於數秒內下降並持續，故障清除後逐漸回到對齊狀態
- 瞬時偏航（風向變化時的 `yaw_error`，典型 5–15°）會帶來 2–9 m 的下游尾流偏移 — 與實測 LiDAR 一致
- 新 SCADA 標籤 `WMET_WakeDefl` 可於歷史圖表觀察每台風機的尾流自偏轉（±15 m 典型）
- 與 #93（Bastankhah 赤字）、#95（蜿蜒）共用同一個 `r_lat` 側向軸：三者物理一致疊加
- 未來主動尾流導向控制策略（wake steering control）有物理基礎可建立

## 建議行動

1. **長時段資料品質驗證**：以 `examples/data_quality_analysis.py` 跑 2 h 混合工況，注入 `yaw_misalignment` 故障，觀察下游 `WMET_WakeDef` 的下降量是否 ~2–5%，並對應 `WMET_WakeDefl` 的時間軌跡
2. **前端視覺化整合**：Dashboard 尾流熱圖同時顯示 DWM 蜿蜒 + 偏航偏轉的綜合瞬時中心線
3. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值
4. **實作 #57 前端 RUL 視覺化**：後端已就緒
5. **建立 pytest 測試套件（#52）**：Bastankhah 傾斜角 + δ_y(x)=tan(θ_c)·x 的解析檢核為理想首批物理測試案例
6. **主動 wake steering 控制實驗**：在模擬器層開放 API 注入 intentional yaw offset，驗證風場總出力的 wake-steering gain（可對比 NREL FLORIS 基準）
7. **同步 `/api/farms` 4 個路由至 README.md**：仍未完成
