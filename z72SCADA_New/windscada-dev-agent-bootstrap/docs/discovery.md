# Discovery（需求萃取）
## 背景與目標
建立一個可擴充的風場監控後端樣板，演示代理人導向開發流程。

## 問答逐字稿（摘要）
- 目標受眾：實驗室/課程/PoC
- MVP 功能：health、logs；後續擴充到 OPC UA、警報彙整、RAG
- 技術棧：FastAPI、pytest、（後續）Postgres
- 非功能性：可測試、可觀測、可擴充

## MVP 定義（MoSCoW）
- Must: /health, /logs、新增文件與 CI
- Should: ADR、樣板腳本
- Could: Docker 化
- Won’t (初期): 雲端部署

## 成功量尺
- 單元測試通過率 100%（MVP 範圍）
- CI 穩定通過
