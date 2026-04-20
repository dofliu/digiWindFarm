# digiWindFarm Daily Report

> 最後更新：2026-04-20

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-pDlDb`）：
- feat: upgrade wake model to Bastankhah-Porté-Agel Gaussian (#93)

近 24 小時合併/提交摘要：
- [45c2f20] Merge PR #92 — 局部亂流袋（#91）
- [fab8bf9] feat: add localized turbulence pockets with Gaussian spatial TI boost (#91)
- [b788861] Merge PR #90 — 環境濕度影響空氣冷卻（#89）
- [a102cfc] feat: add ambient humidity air-cooling model with dew-point penalty (#89)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立 | #93 | 尾流模型升級：Bastankhah-Porté-Agel 高斯尾流 | Jensen top-hat 模型過度簡化；本日建立並實作 |
| 關閉 | #93 | 尾流模型升級 | 已實作 Bastankhah-Porté-Agel + Ct 耦合 + TI 依賴膨脹 + SoS 疊加 + `WMET_WakeDef` 標籤 |
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

本日建立並關閉 1 個 issue（#93），符合「每次最多 3 個新 issue」規則。

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
| `simulator/` | 2026-04-20 | 0 | 無測試套件 | `engine.py` 傳入 `wake_deficit` |
| `simulator/physics/` | 2026-04-20 | 0 | 無測試套件 | `wind_field.py` 升級為 Bastankhah 高斯尾流；`turbine_physics`、`scada_registry` 新增 `WMET_WakeDef` |
| `wind_model.py`（根目錄） | 2026-04-19 | 0 | 無測試套件 | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案 |

## API Endpoints

共 58 個路由（57 HTTP + 1 WebSocket）。無新增路由，狀態與昨日相同。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（4 個路由）仍未同步至 README 的 Core APIs 章節。

## 程式碼品質

- Lint 錯誤：115（核心模組 `server/` + `simulator/` 維持 0 錯誤，剩餘皆在 `opc_bachmann/` 和根目錄原型檔案）
- `ruff check simulator/ server/ wind_model.py` — All checks passed ✓
- `python -m py_compile simulator/physics/{wind_field,turbine_physics,scada_registry}.py simulator/engine.py` — 4 個修改檔案全部通過
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：**95 個**（+1：`WMET_WakeDef`）

## 今日新增功能

### Bastankhah-Porté-Agel 高斯尾流模型（#93）

**物理原理**

- 舊模型為簡化的 Jensen/Park top-hat：`deficit = 0.08 × alignment × (200/dist)^0.5`，硬性 clip 至 0.85
  - 問題 1：尾流赤字與推力係數 Ct 無耦合，僅為經驗常數
  - 問題 2：side-to-side 無 Gaussian 衰減，只是 cos(θ) > 0.3 的圓錐檢查
  - 問題 3：下游距離以經驗根號衰減，非物理的線性膨脹
  - 問題 4：多尾流用乘法疊加，不是標準 sum-of-squares
- 新模型為 Bastankhah-Porté-Agel 2014 高斯尾流（風能界最通用的解析尾流模型之一）：
  - 近尾流偏移：ε/D = 0.25 × √((1 + √(1 − Ct)) / (2√(1 − Ct)))
  - 線性膨脹：σ(x)/D = k* × (x/D) + ε/D
  - 最大赤字（中心軸）：C(x) = 1 − √(1 − Ct / (8·(σ/D)²))
  - 徑向 Gaussian：ΔU(x,r)/U∞ = C(x) × exp(−0.5·(r/σ)²)
- 尾流膨脹率（Niayifar & Porté-Agel 2016）：k* ≈ 0.38·TI + 0.004
  - TI=0.06（離岸低亂流）→ k* ≈ 0.027（尾流恢復慢，深尾流持續遠）
  - TI=0.20（高亂流）→ k* ≈ 0.080（尾流快速恢復）
- 多尾流疊加改為 sum-of-squares：ΔU_total/U = √(Σ (ΔU_i/U)²)

**實作方式**

1. `simulator/physics/wind_field.py`：
   - `PerTurbineWind.__init__` 新增 `rotor_diameter: float = 70.65` 參數與 `self._wake_deficits` 狀態陣列
   - `_update_wake_factors(wind_direction, mean_wind, turbulence_intensity)` 重寫為 Bastankhah-Porté-Agel 公式
   - Ct 啟發式：V<3 m/s 為 0；Region 2 (3 ≤ V < 11) 為 0.82 − 0.015·|V−8|；Region 3 為 0.82·(V_rated/V)²（限制 0.05-0.90）
   - k* = max(0.02, 0.38·TI + 0.004)
   - 下游距離 x_down ≤ 0.5·D 視為不受尾流影響（含側向與上游）
   - 當判別式 1 − Ct/(8·(σ/D)²) ≤ 0（極近尾流）時 cap 在 C_max = 0.70
   - 最終 `self._wake_factors = 1.0 − np.clip(total_deficit, 0, 0.70)`
   - 新增公開方法 `get_wake_deficit(turbine_index)`
2. `simulator/engine.py`：每步取得 `get_wake_deficit(idx)` 並傳入 `turbine.step`
3. `simulator/physics/turbine_physics.py`：
   - `step()` 新增 `wake_deficit: float = 0.0` kwarg
   - `reset()` 與 `__init__` 新增 `_wake_deficit = 0.0`
   - 輸出 `WMET_WakeDef`（%，wake velocity deficit）
4. `simulator/physics/scada_registry.py`：新增 `WMET_WakeDef`（REAL32, %, 0–70）

**物理效應（自測驗證）**

| 條件 | 預期 | 實測 |
|------|------|------|
| 3 台一列、500 m 間距、風速 10 m/s 270°、TI=0.08 | 上游 0%，下游深尾流 15–20% | T0=0% / T1=17.3% / T2=19.1% ✓ |
| 風向 0°（側向吹、無尾流重疊） | 所有 0% | 全部 0.0% ✓ |
| 16 m/s（Region 3，Ct≈0.39） | 赤字下降 | T1=12.4% / T2=13.8% ✓ |
| TI=0.20（高亂流，k*≈0.080） | 尾流快速恢復 | T1=6.6% / T2=7.0% ✓ |
| 2 m/s（cut-in 以下，Ct=0） | 全部 0% | 全部 0.0% ✓ |

**影響範圍**

- `WMET_WakeDef` 可於歷史圖表觀察風向改變時的尾流關係切換（風向旋轉 → 尾流方向跟著旋轉 → 不同機組進入/離開尾流）
- 尾流赤字上限從舊模型的 15%（clip 0.85）提升至 70%，更真實反映深尾流
- 高 TI 時尾流快速恢復 → 符合大氣穩定度對尾流長度的影響（離岸低穩定度 vs 日間對流）
- Region 3 尾流赤字下降 → 符合變槳後 Ct 下降的物理
- 為未來前端尾流視覺化、Lillgrund / Horns Rev 風場基準驗證鋪前置介面

## 建議行動

1. **整合測試 #93**：建議在 `examples/data_quality_analysis.py` 追加「風向旋轉前後下游風機功率變化」以驗證尾流方向耦合。
2. **前端視覺化 #93**：Dashboard 可新增尾流熱圖（以風場佈局 + `WMET_WakeDef` 顏色編碼呈現），對操作員直觀展示尾流效應。
3. **Lillgrund / Horns Rev 基準驗證**：以業界公開基準資料（8D 間距 LES）比對模型輸出，校準 k* 與 Ct 啟發式。
4. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值。
5. **實作 #57 前端 RUL 視覺化**：後端已就緒，前端 Load/Fatigue 分頁補 RUL 顯示。
6. **同步 `/api/farms` 4 個路由至 README.md**：仍未完成。
7. **建立測試套件（#52）**：Bastankhah 尾流模型的數值預期（Ct→ε/D、k*→σ(x)/D、C_max 判別式）非常適合做為物理模型 pytest 第一批案例。
