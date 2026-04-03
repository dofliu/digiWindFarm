# WindSCADA Dev Agent
## 目標
以代理人驅動的開發流程，建立可擴充的風場監控與知識輔助後端服務（示範版）。

## 範圍（MVP）
- 健康檢查 API `/health`
- 簡易開發紀錄 API `/logs`（in-memory/檔案追加）
- 文件與任務循環、CI/測試

## 架構總覽
- 後端：FastAPI + Uvicorn
- 測試：pytest
- 文件：`docs/`（discovery/inception/ADR）
- 自動化：GitHub Actions CI

## 編碼規範與工具
- Python 3.10+，black/ruff（可後續加入）

## 測試策略
- 單元測試涵蓋健康檢查與紀錄寫入

## 發布策略
- dev：手動
- ci：lint/test 全通過才允許合併

## 變更紀錄（由代理人維護）
- 2025-11-02 16:46: 初始化專案骨架（#T001）
