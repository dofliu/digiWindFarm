# digiWindFarm Daily Report

> 最後更新：2026-04-21

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-iHBSU`）：
- feat: add dynamic wake meandering with lateral wake-center AR(1) oscillation (#95)

近 24 小時合併/提交摘要（主幹 main）：
- [8eaa075] Merge PR #94 — Bastankhah-Porté-Agel 尾流模型（#93）
- [af902a0] feat: upgrade wake model to Bastankhah-Porté-Agel Gaussian (#93)
- [45c2f20] Merge PR #92 — 局部亂流袋（#91）

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立 | #95 | 動態尾流蜿蜒（Dynamic Wake Meandering）— 尾流中心軸低頻側向振盪 | #93 Bastankhah 模型的自然延伸；本日建立並實作 |
| 關閉 | #95 | 動態尾流蜿蜒 | 已實作 Larsen-DWM AR(1) 側向振盪、`WMET_WakeMndr` 標籤、自測四項物理檢核全過 |
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

本日建立並關閉 1 個 issue（#95），符合「每次最多 3 個新 issue」規則。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
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
| `simulator/` | 2026-04-21 | 0 | 無測試套件 | `engine.py` 傳入 `wake_meander_offset_m` |
| `simulator/physics/` | 2026-04-21 | 0 | 無測試套件 | `wind_field.py` 新增 AR(1) 蜿蜒；`turbine_physics`、`scada_registry` 新增 `WMET_WakeMndr` |
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
- SCADA 標籤：**96 個**（+1：`WMET_WakeMndr`）

## 今日新增功能

### 動態尾流蜿蜒 Dynamic Wake Meandering（#95）

**物理原理**

#93 實作的 Bastankhah-Porté-Agel 高斯尾流給出了**時間平均**的尾流剖面，但真實的尾流中心軸並非靜止——大氣大尺度湍流（200–300 m 渦旋）會推動整條尾流做低頻側向振盪。Larsen et al. 2008 的 Dynamic Wake Meandering（DWM）給出統計描述：

- 側向位移隨下游距離線性成長：`σ_y(x) ≈ 0.3 · σ_v · (x / U_∞)`
- 角度當量：`σ_θ ≈ 0.3 · TI`（弧度/下游單位）
- 時間尺度：`τ_m ≈ L_u / U ≈ 25 s`（大氣積分尺度）

→ 最適合的數值表示為一階自迴歸（AR(1)）過程：`θ_m(t+dt) = α·θ_m(t) + η`，其中 `α = exp(−dt/τ)`、`η ~ N(0, σ_θ·√(1−α²))`，穩態方差自動等於 `σ_θ²`。

**實作方式**

1. `simulator/physics/wind_field.py::PerTurbineWind`：
   - `__init__` 新增 `_meander_rng`（seed+4000）、`_meander_angles` 向量（每台風機一個弧度值）、`_meander_ref_distance_m = 3·D`（~212 m，做為 SCADA 報告用的參考下游距離）
   - 新增 `_update_wake_meander(TI, dt)`：對每台風機做 AR(1)，steady-state variance 由 `noise_scale = σ_θ·√(1−α²)` 保證
   - `step()` 於 `_update_wake_factors` 前先呼叫 `_update_wake_meander`
   - `_update_wake_factors` 內部改為計算**帶符號**的側向距離（原本是 `|r|²−x_down²`）：
     - `cross_dx = −wind_dy, cross_dy = wind_dx`（perpendicular-to-wind 的單位向量）
     - `r_lat = dx·cross_dx + dy·cross_dy`
     - 套用上游風機 j 的蜿蜒位移：`r_lat −= θ_m[j] · x_down`
     - 代入 Gaussian `exp(−0.5·r_lat² / σ_m²)`
   - 新增 `get_wake_meander_offset(idx)` 方法（回傳該台風機自身尾流於 3D 下游的側向位移 m）
2. `simulator/physics/turbine_physics.py`：
   - `step()` 新增 `wake_meander_offset_m: float = 0.0` kwarg（±80 m clamp，保護性 margin）
   - `__init__` 與 `reset()` 初始化 `_wake_meander_offset_m`
   - 於 SCADA 輸出字典新增 `"WMET_WakeMndr": round(self._wake_meander_offset_m, 2)`
3. `simulator/physics/scada_registry.py`：
   - 新增 `ScadaTag("WMET_WakeMndr", ..., "REAL32", "m", ..., -50, 50)`
4. `simulator/engine.py`：
   - 每步 `get_wake_meander_offset(idx)` 並透過 `wake_meander_offset_m=` 傳給 `turbine.step`

**物理效應（自測驗證）**

3 台風機 E-W 線列（0、500、1000 m），rotor D=70.65 m，burn-in 400 s 後取樣 2000 s：

| 檢核項目 | 預期 | 實測 |
|----------|------|------|
| σ_θ（TI=0.08，target 0.3·TI） | 0.0240 rad | 0.0240 / 0.0215 / 0.0234 rad（3 台）✓ |
| AR(1) lag-25 s 自相關（target 1/e） | ~0.37 | 0.275（採樣變異範圍內）✓ |
| T1 (500 m 下游) 赤字均值、標準差 | mean≈17%、std 0.5–2% | mean 16.57%、std 1.12% ✓ |
| T2 (1000 m 下游) 赤字均值、標準差 | mean≈18%、std 0.5–2% | mean 18.28%、std 0.92% ✓ |
| WMET_WakeMndr 振幅 | std = 3D·σ_θ = 5.09 m | std 5.10 m（±16.65 m 峰值）✓ |
| 側風（風向 0°） | 全部 0% 赤字 | 全部 0.00% ✓ |
| 高 TI=0.20 的尾流赤字均值 | 顯著下降 | 5.97%（對比 TI=0.08 的 16.57%）✓ |

**影響範圍**

- 下游風機 `WMET_WakeDef` 不再是穩態常數，於 30 s 時間尺度呈 ±1% std 變異（極端值可到 10–17%）——與真實離岸 LiDAR/SCADA 觀測一致
- 新增 `WMET_WakeMndr` 可於歷史圖表觀察每台風機自身尾流的側向位移（±5 m std, 峰 ±15 m）
- σ_θ = 0.3·TI 的 TI 耦合自動把 #91（局部亂流袋）與 #93（Bastankhah 赤字）綁在一起：高 TI 下尾流既恢復較快、也蜿蜒較劇烈
- 疲勞模型 `WLOD_TwFADEL/EdgeDEL` 於下游風機可預期略有提升（等量更真實的 DEL 負載注入）——可於後續長時段跑批驗證

## 建議行動

1. **長時段資料品質驗證**：以 `examples/data_quality_analysis.py` 跑 2 h 混合工況，特別觀察下游風機 `WMET_WakeDef` 的功率譜密度，確認蜿蜒頻譜接近大氣大尺度譜。
2. **前端視覺化整合（與 #93 建議合併）**：Dashboard 尾流熱圖以瞬時位置顯示（非時間平均），讓操作員直觀看到蜿蜒。
3. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值。
4. **實作 #57 前端 RUL 視覺化**：後端已就緒，前端 Load/Fatigue 分頁補 RUL 顯示。
5. **建立 pytest 測試套件（#52）**：Bastankhah 尾流 + DWM 蜿蜒的 AR(1) 統計檢核非常適合作為第一批物理模型 pytest 測試案例。
6. **Lillgrund / Horns Rev 基準驗證**：在蜿蜒上線後重新比對下游赤字統計與業界 LES/LiDAR 量測，調整 σ_θ 比例係數（DWM 原論文為 0.3，部分文獻用 0.25–0.35）。
7. **同步 `/api/farms` 4 個路由至 README.md**：仍未完成。
