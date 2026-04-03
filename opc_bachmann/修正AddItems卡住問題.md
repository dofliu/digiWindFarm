# 修正 AddItems 卡住問題 - 詳細步驟

## 問題確認

您的程式卡在 **`items.AddItems()`** 呼叫，而不是 `SyncRead`。這是一個非常具體的 DCOM Access Permissions 問題。

## 根本原因

`AddItems` 操作需要：
1. **Launch Permissions**（啟動權限）- 已經有了（因為您能連接和瀏覽）
2. **Access Permissions**（存取權限）- **這個有問題！**

當您呼叫 `AddItems` 時，OPC Server 需要在 COM 物件上建立新的項目介面，這需要 **Access Permissions**。

## 🔧 立即修正步驟

### 方法 1：設定 Graybox.OPC.DAWrapper 的 Access Permissions

1. **開啟 Component Services**
   - 按 `Win + R`
   - 輸入 `dcomcnfg`
   - 按 Enter

2. **找到 Graybox.OPC.DAWrapper**
   - 展開：Component Services → Computers → My Computer → DCOM Config
   - 往下滾動找到 **Graybox.OPC.DAWrapper**
   - 如果找不到，試試搜尋 "Graybox" 或 "OPC"

3. **設定 Access Permissions**
   - 右鍵點擊 **Graybox.OPC.DAWrapper**
   - 選擇 **Properties**
   - 切換到 **Security** 標籤

4. **Access Permissions（關鍵步驟）**
   ```
   在 Security 標籤中找到 "Access Permissions"

   ○ Use Default          ← 不要選這個
   ● Customize            ← 選這個

   [Edit...] 按鈕          ← 點這個
   ```

5. **編輯 Access Permissions**
   - 點擊 **[Add...]** 按鈕
   - 輸入：`Everyone` 或您的使用者名稱
   - 點擊 **[Check Names]** 驗證
   - 點擊 **[OK]**

6. **設定權限**
   - 在清單中選擇剛加入的使用者
   - 勾選以下權限：
     ```
     ☑ Local Access      ← 必須勾選
     ☑ Remote Access     ← 也勾選（雖然是 localhost）
     ```
   - 點擊 **[OK]**

7. **同時檢查 Launch and Activation Permissions**
   - 在同一個 Security 標籤
   - 找到 "Launch and Activation Permissions"
   - 也選擇 **Customize** 並 **Edit**
   - 確保有：
     ```
     ☑ Local Launch
     ☑ Remote Launch
     ☑ Local Activation
     ☑ Remote Activation
     ```

8. **設定 Identity（重要）**
   - 切換到 **Identity** 標籤
   - 選擇：
     ```
     ● The interactive user    ← 建議選這個

     或

     ● This user:              ← 填入您的帳號
       User: 您的使用者名稱
       Password: 您的密碼
     ```

9. **套用變更**
   - 點擊所有對話框的 **[OK]** 按鈕
   - 關閉 Component Services

### 方法 2：以系統管理員身分執行（快速測試）

如果您不想改 DCOM 設定，可以先試試：

1. 找到您的 Python 執行檔（例如：`python.exe`）
2. 右鍵 → **以系統管理員身分執行**
3. 在管理員權限的終端機中執行：
   ```bash
   python diagnose_additems.py
   ```

### 方法 3：檢查全域 DCOM 設定

有時候問題在全域設定：

1. 在 `dcomcnfg` 中
2. 右鍵點擊 **My Computer**
3. 選擇 **Properties**
4. 切換到 **COM Security** 標籤

5. **Access Permissions**
   - 點擊 **Edit Default...**
   - 確保 **Everyone** 或您的使用者有：
     - ☑ Local Access
     - ☑ Remote Access

6. **Launch and Activation Permissions**
   - 點擊 **Edit Default...**
   - 確保有：
     - ☑ Local Launch
     - ☑ Local Activation

## 🧪 測試步驟

完成設定後：

1. **重新啟動 OPC Server 服務**（如果有的話）
   ```cmd
   services.msc
   ```
   找到 Bachmann 相關服務，重新啟動

2. **執行診斷腳本**
   ```bash
   python diagnose_additems.py
   ```

   這個腳本會：
   - 逐步測試每個操作
   - 精確告訴您卡在 Validate 還是 AddItems
   - 每個步驟都有 5-15 秒逾時

3. **查看結果**
   - 如果通過步驟 5a (Validate) 但卡在 5b (AddItems)
     → 確認是 Access Permissions 問題

   - 如果已經通過步驟 5b
     → 問題已解決！

## 🔍 進階診斷

### 檢查當前權限設定

在 PowerShell（系統管理員）中執行：

```powershell
# 檢查 DCOM 設定
Get-CimInstance -ClassName Win32_DCOMApplicationSetting |
  Where-Object {$_.Caption -like "*Graybox*" -or $_.Caption -like "*OPC*"} |
  Select-Object Caption, AppID

# 查看您的使用者群組
whoami /groups
```

### 查看事件記錄

1. 開啟 **Event Viewer** (eventvwr.msc)
2. 展開：Windows Logs → System
3. 篩選：來源 = DistributedCOM
4. 查看是否有相關錯誤訊息

常見錯誤：
- **錯誤 10016**：應用程式特定權限設定未授予...
- **錯誤 10010**：伺服器 {GUID} 沒有在要求的逾時...

## 📋 完整檢查清單

確認以下所有項目都已設定：

**Graybox.OPC.DAWrapper 設定：**
- [ ] Security → Launch and Activation Permissions = Customize
  - [ ] 您的使用者有 Local Launch
  - [ ] 您的使用者有 Local Activation
- [ ] Security → Access Permissions = Customize ← **最重要**
  - [ ] 您的使用者有 Local Access
  - [ ] 您的使用者有 Remote Access
- [ ] Security → Configuration Permissions = Customize
  - [ ] 您的使用者有 Full Control
- [ ] Identity = "The interactive user"

**全域設定（My Computer）：**
- [ ] COM Security → Access Permissions (Default)
  - [ ] Everyone 或您的使用者有 Local Access
- [ ] COM Security → Launch Permissions (Default)
  - [ ] Everyone 或您的使用者有 Local Launch
  - [ ] Everyone 或您的使用者有 Local Activation

**防火牆：**
- [ ] Windows Defender 防火牆允許 Python
- [ ] Windows Defender 防火牆允許 OPC Server

**其他：**
- [ ] 以系統管理員身分執行 Python（測試用）
- [ ] OPC Server 服務正在運行
- [ ] 使用 32-bit Python

## 🎯 快速參考：最小權限設定

如果您只想設定最少的權限來讓它運作：

**只設定 Graybox.OPC.DAWrapper：**

1. Launch and Activation Permissions → Customize → Edit
   - 加入您的使用者
   - 勾選：Local Launch + Local Activation

2. Access Permissions → Customize → Edit ← **關鍵**
   - 加入您的使用者
   - 勾選：Local Access

3. Identity
   - 選擇：The interactive user

## ⚠️ 常見陷阱

1. **忘記點 Apply/OK**
   - 每個對話框都要點 OK
   - 最後要套用變更

2. **選錯物件**
   - 確認是 "Graybox.OPC.DAWrapper"
   - 不是 "Graybox.OPC.DAWrapper.1"
   - 如果有多個，都設定一遍

3. **使用者名稱錯誤**
   - 確認是正確的網域\使用者名稱
   - 或直接使用 "Everyone"（測試用）

4. **沒有重新啟動服務**
   - 改完設定要重啟 OPC Server 服務
   - 或重新啟動電腦

## 📞 如果還是不行

請執行以下命令並回報結果：

```bash
# 1. 執行診斷腳本
python diagnose_additems.py

# 2. 查看在哪個步驟卡住
# 步驟 5a 卡住 → Validate 問題
# 步驟 5b 卡住 → AddItems 問題（Access Permissions）

# 3. 截圖 dcomcnfg 設定
# Graybox.OPC.DAWrapper → Properties → Security 標籤
```

## 🎉 成功指標

當診斷腳本顯示：

```
[步驟 5b] 加入項目（AddItems）
  → 開始 AddItems...
  ✓ AddItems 成功

[步驟 6] 同步讀取（SyncRead）
  → 開始 SyncRead...
  ✓ SyncRead 成功

✓✓✓ 完全成功！✓✓✓
```

恭喜！您的 DCOM 權限設定正確了！
