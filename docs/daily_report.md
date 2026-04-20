# digiWindFarm Daily Report

> 最後更新：2026-04-20

## 昨日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-sQJ2G`）：
- feat: add localized turbulence pockets (Gaussian spatial TI boost) — 對應 #91

過去 24 小時主要合併/提交：
- [b788861] Merge PR #90 — 環境濕度影響空氣冷卻（#89）
- [a102cfc] feat: add ambient humidity air-cooling model with dew-point penalty (#89)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 建立 | #91 | 局部亂流袋（localized turbulence pockets） | TODO/physics_model_status 列為 Still missing 但無對應 issue；本日建立並同步實作 |
| 關閉 | #91 | 局部亂流袋 | 已實作：Gaussian spatial pocket、stochastic spawn、per-turbine TI multiplier、`WMET_LocalTi` 標籤 |
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

本日建立並關閉 1 個 issue（#91），符合「每次最多 3 個新 issue」規則。

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
| `simulator/` | 2026-04-20 | 0 | 無測試套件 | `engine.py` 傳入 `local_ti_multiplier` |
| `simulator/physics/` | 2026-04-20 | 0 | 無測試套件 | `wind_field` 新增亂流袋；`turbine_physics`、`scada_registry` 接線 |
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
- SCADA 標籤：**94 個**（+1：`WMET_LocalTi`）

## 今日新增功能

### 局部亂流袋（localized turbulence pockets, #91）

**物理原理**

- 離岸風場邊界層中，除了全場尺度的亂流統計外，還會出現尺度較小（100–500 m）、持續時間較短（30–180 s）的局部 coherent 亂流結構
- 主因：對流邊界層的熱通量不均勻、上游尾流破裂（wake breakdown）、海面應力局部變化
- 袋**不改變平均風速**，而是**放大 TI（亂流強度）**，造成袋內 1–3 台相鄰風機的風速標準差、功率 CV、振動 broadband 短暫升高

**實作方式**

1. `simulator/physics/wind_field.py`：
   - 新增 `TurbulencePocket` dataclass（中心座標、Gaussian 半徑 σ、TI 倍率、rise/hold/fall 壽命）
   - `PerTurbineWind` 新增 `_pockets: List[TurbulencePocket]`、`_pocket_sim_time`、`_current_ti_multipliers`
   - `_update_turbulence_pockets()`：stochastic spawn（機率 `dt × (0.0006 + 0.0004 × max(0, farm_wind − 6))`，約每 10–15 min 1 顆於 10 m/s），袋心位置隨機錨定任一風機附近 ±250 m，半徑 180–380 m，TI 倍率 1.4–2.0×
   - 空間權重：`w_i = exp(-dist²/(2σ²))`（Gaussian）
   - 時間包絡：cosine rise → flat hold → cosine fall
   - 每台風機 `TI_eff_i = TI_base × (1 + Σ(boost_k × w_i,k × env_k(t)))`
   - 餵給原有 `TurbulenceGenerator.step`，放大 AR(1) 白噪音的 σ
2. `simulator/engine.py`：每步取得 `get_local_ti_multiplier(idx)` 並傳入 `turbine.step`
3. `simulator/physics/turbine_physics.py`：`step()` 新增 `local_ti_multiplier` kwarg，輸出 `WMET_LocalTi`（%，相對基準 TI 的倍率 × 100）
4. `simulator/physics/scada_registry.py`：新增 `WMET_LocalTi`（REAL32, %, 80–300）

**物理效應（自測驗證）**

| 條件 | 預期 WMET_LocalTi | 實測 |
|------|-------------------|------|
| 無袋（基準） | 100% | 100.0 ✓ |
| 袋心 1.8×，袋半徑 250 m，距袋心 0 m | ~180% | 180.0 ✓ |
| 袋心 1.8×，袋半徑 250 m，距袋心 500 m | ~110% | 110.8 ✓（高斯衰減） |
| 袋心 1.8×，袋半徑 250 m，距袋心 1500 m | ~100% | 100.0 ✓（袋外） |
| 鄰近兩台在同一袋內（相距 430 m） | 同步升高 | 兩台同時 118% ✓ |

**影響範圍**

- `WMET_LocalTi` 可於歷史圖表觀察局部亂流事件（典型持續 30–180 s）
- 袋作用時段：振動 broadband/HF 頻帶短期升 20–30%，DEL 小幅升高（因亂流驅動的 σ 放大 → 塔基與葉根彎矩 variance 增加）
- 相鄰風機之 `WMET_LocalTi` 具空間相關性，可作為故障診斷輔助訊號（排除單機故障誤報）
- 平均風速（`WMET_WdSpd`）不變，僅風速標準差與振動變化，與真實邊界層現象一致
- 為未來尾流破裂、對流邊界層模型鋪前置介面

## 建議行動

1. **整合測試 #91**：建議在 `examples/data_quality_analysis.py` 追加「局部亂流期間 vs 平穩期間」的振動/DEL 比對（可人工注入袋驗證）。
2. **前端視覺化 #91**：Dashboard 可加上 `WMET_LocalTi` 迷你圖，輔助辨識目前有無袋影響。
3. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值（目前已有 ISO 10816 分區但未以曲線形式顯示）。
4. **實作 #57 前端 RUL 視覺化**：後端已就緒，前端 Load/Fatigue 分頁補 RUL 顯示。
5. **同步 `/api/farms` 4 個路由至 README.md**：仍未完成。
6. **建立測試套件（#52）**：袋空間權重、時間包絡、生成機率計算均具數值預期，適合做為物理模型 pytest 第一批案例。
