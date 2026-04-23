# digiWindFarm Daily Report

> 最後更新：2026-04-23

## 今日 Commit 摘要

本次日報工作提交（分支 `claude/keen-hopper-uUP72`）：

- feat: add wake-added turbulence intensity (Crespo-Hernández) (#103)

近 24 小時主幹 `main` 合併摘要：

- [f1e085e] Merge PR #102 — 空氣密度耦合文件同步
- [f01b9a5] docs: update project docs and daily report for air density coupling (#101)
- [3565467] feat: couple air density to ambient temperature and humidity (#101)
- [5ab4f32] Merge PR #100 — 大氣穩定度 α/TI 文件同步
- [cdaa177] feat: atmospheric stability couples diurnal cycle to shear α and TI (#99)

## Issue 狀態

| 動作 | Issue # | 標題 | 說明 |
|------|---------|------|------|
| 實作 | #103 | 尾流誘發紊流增強 Crespo-Hernández | 新增 `WMET_WakeTi`，7 項自測全過；SCADA 101 個 |
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

本日建立 0 個 issue（#103 已由專案維護者於今日凌晨建立，本次直接實作）、關閉 0 個。符合「每次最多 3 個新 issue」規則。

## Open Issues 總覽

| # | 標題 | Labels | 建立日期 | 備註 |
|---|------|--------|----------|------|
| #103 | 尾流誘發紊流增強 Crespo-Hernández | enhancement, physics, auto-detected | 2026-04-23 | 已實作 |
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
| `simulator/` | 2026-04-23 | 0 | 無測試套件 | `engine.py` 每步取得並傳遞 `wake_added_ti` |
| `simulator/physics/` | 2026-04-23 | 0 | 無測試套件 | `wind_field` 新增 Crespo-Hernández 尾流 TI；`turbine_physics` 新增 `wake_added_ti` kwarg 與 `WMET_WakeTi` 輸出；`scada_registry` 新增 `WMET_WakeTi` |
| `wind_model.py`（根目錄） | 2026-04-22 | 0 | 無測試套件 | 無變更 |
| `frontend/` | 2026-04-17 | 0 | 無測試套件 | 無變更 |
| 根目錄原型 | 2026-04-12 | 0 | — | 早期原型檔案 |

## API Endpoints

共 62 個路由（61 HTTP + 1 WebSocket）。本日無新增路由。詳見 README.md「Core APIs」章節。

待同步：`/api/farms`（10 個路由）仍未完整同步至 README 的 Core APIs 章節。

## 程式碼品質

- Lint 錯誤：115（核心模組 `server/` + `simulator/` 維持 0 錯誤）
- `ruff check simulator/ server/ wind_model.py` — All checks passed ✓
- `python -m py_compile simulator/engine.py simulator/physics/wind_field.py simulator/physics/turbine_physics.py simulator/physics/scada_registry.py` — 4 個修改檔案全部通過
- Broken imports：0（核心模組全部通過）
- 語法錯誤：0
- 測試套件：未建立（無 pytest）— 追蹤 issue #52
- 安全漏洞：17 個（5 個套件），詳見 #48
- TODO/FIXME/HACK：0 個（核心模組）
- SCADA 標籤：**101 個**（+1：`WMET_WakeTi`）

## 今日新增功能

### 尾流誘發紊流增強 — Crespo-Hernández (#103)

**問題與物理原理**

`simulator/physics/wind_field.py` 目前已有完整的尾流**速度赤字**模型：Bastankhah-Porté-Agel 高斯尾流（#93）+ 動態尾流擺動（#95）+ 偏航尾流偏轉（#97）。然而**尾流對紊流強度 TI 的增強**這項物理事實一直未被建模：

- 上游風機的葉尖渦流 + 剪切層 → 下游 TI 顯著上升
- IEC 61400-1 Annex E：5D–10D 範圍附加 TI 可達 +5–10%
- 影響：下游風機功率時變性、控制器負載、疲勞 DEL

原本 `WMET_LocalTi` 僅反映局部亂流氣袋（#91），不含尾流誘發部分。下游風機在尾流中應有更高的有效 TI，但 AR(1) 亂流產生器只看到原始環境 TI，無法感受下游 σ_v 的真實上升。

**公式與實作**

Crespo-Hernández (1996) 經驗公式：

```
TI_w(x, r=0) = 0.73 · a^0.8325 · TI_∞^0.0325 · (x/D)^(-0.32)
其中 a = 0.5·(1 − √(1 − Ct))              軸向誘導因子
```

- 有效範圍 5 ≤ x/D ≤ 15；近場（x/D<5）保守以 x/D=5 作上限
- 徑向衰減**共用** Bastankhah σ（避免新增自由參數）：`TI_w(x,r) = TI_w(x,0) · exp(−0.5·r²/σ²)`
- 多源疊加採 Frandsen 平方和（IEC 61400-1 Annex E）：`TI_eff² = TI_amb² + Σ TI_w²`

**與現有模型的耦合**

1. `_update_wake_factors` 內同一對 `(j, i)` 迴圈，共用已計算的 `x_down`、`r_lat`、`σ`、`radial` — 無額外迴圈開銷
2. `PerTurbineWind.step()` 將每台下游風機的 `wake_added_ti` 與 `pocket_mult` **平方和相加**，轉為 AR(1) 產生器的有效 TI 倍率：

   ```
   mult_combined = √(pocket_mult² + (wake_added_ti / TI_amb)²)
   ti_local = turbulence_intensity · 0.4 · mult_combined
   ```

   這使得 `_turb_gens[i]` 真的看到下游提升後的 σ_v，自然體現在 `get_local_wind()` 回傳的風速波動上

3. `simulator/engine.py`：新增 `wake_added_ti = self._per_turbine_wind.get_wake_added_ti(idx)` 傳入 `turbine.step`
4. `simulator/physics/turbine_physics.py`：`step()` 新增 `wake_added_ti: float = 0.0` kwarg，`self._wake_added_ti = clamp([0, 0.50])`，輸出 `"WMET_WakeTi": round(self._wake_added_ti * 100.0, 2)`（單位 %）
5. `simulator/physics/scada_registry.py`：新增 `WMET_WakeTi`（REAL32, %, 0–50）→ **SCADA 總數 100→101**

**物理效應（自測驗證 — 3 台 E-W 線列，500 m 間距，D=70.65 m）**

| 測試情境 | 預期 | 實測 | 結果 |
|----------|------|------|------|
| T0 自由流 | ≈ 0 | 0.00% | ✓ |
| T1（~7D 下游）10 m/s, TI=0.08 | 12% 左右（解析 12.16%） | 12.00% | ✓ |
| T2（~14D 下游，疊加 T0+T1） | ≈ √(12² + 9.74²) = 15.46% | 15.41% | ✓ |
| 側向風（270° 垂直線列） | 全為 0 | 0.00% | ✓ |
| 18 m/s Region 3（Ct ≈ 0.31） | 顯著下降 | T1=4.54% | ✓ |
| AR(1) 產生器實際感受 | T1 std > T0 std | 1.36 倍（+36%） | ✓ |
| Frandsen 疊加一致性 | T2 ≈ √(T0→T2² + T1→T2²) | 15.41% ≈ 15.46% | ✓ |

**為何這是物理「因」而非輸出偏移**

- 使用 IEC 61400-1 Annex E 所引用的經驗公式（Crespo-Hernández 1996）
- 透過既有 `_turb_gens[i].step(...)` 路徑傳遞，AR(1) 擾動自動反映上升後的 σ_v
- 葉片載荷 / 疲勞 DEL（#41 #57）會因下游 σ_v 上升而自然加重，無須任何輸出層修正
- 全場共用同一 Ct、同一 σ、同一 ε/D，迴圈與 Bastankhah 赤字疊合，無重複成本
- 四個尾流機制（速度赤字 #93 + 擺動 #95 + 偏航偏轉 #97 + 附加紊流 #103）完整涵蓋主流尾流物理

**與其他模型的耦合**

- **#91（局部紊流氣袋）**：兩者在 AR(1) 倍率層平方和相加；`WMET_LocalTi` 維持純氣袋指標，`WMET_WakeTi` 為新增的尾流指標
- **#93 / #95 / #97**：共用迴圈與幾何量（x_down, r_lat, σ, radial），零額外成本
- **#99（大氣穩定度）**：環境 TI_amb 受穩定度調變後，`ch_amp = 0.73·a^0.8325·TI_amb^0.0325` 自動響應（雖 0.0325 指數很低，影響溫和）
- **#57（疲勞 DEL / RUL）**：下游塔基 FA 與葉片 flapwise DEL 會因真實 σ_v 上升而加重，未來可校準加重比例

## 建議行動

1. **長時段資料品質驗證**：以 `examples/data_quality_analysis.py` 跑 **7 天自動模式**（time_scale=144），觀察：
   - `WMET_WakeTi` 在不同風向下的空間分佈（相同下游位置但風向改變時應看到角色互換）
   - 下游風機的 `WLOD_*` 疲勞累積速率是否相對上游加快 5–15%
   - `WMET_LocalTi` 與 `WMET_WakeTi` 的相關性（應為弱相關，各自獨立來源）
2. **疲勞 DEL 校準**：以 Lillgrund / Horns Rev 的實測 DEL 增幅（典型下游 +10–20%）校準 `ch_amp` 係數
3. **前端視覺化**：Dashboard 可加上「有效 TI 熱圖」疊加速度赤字，使尾流結構更易理解
4. **實作 #58 頻譜警報曲線**：前端顯示各頻帶警報閾值
5. **實作 #57 前端 RUL 視覺化**：後端已就緒
6. **建立 pytest 測試套件（#52）**：`wake_added_ti` 的解析驗證（7D → 12%、14D 疊加 → 15.5%）與 Frandsen 平方和為理想首批單元測試
7. **未來擴充**：
   - 大氣壓 P 的日週期/天氣鋒面依賴（目前固定 P=101325 Pa；實測可偏 ±2%）
   - Curled-wake 扭斜流入修正（與偏航偏轉合併實作，可另案追蹤）
   - 近場 x/D<5 的更精確修正（Türk & Emeis 2010 提出的 near-wake decay 模型）
8. **同步 `/api/farms` 10 個路由至 README.md**：仍未完成
