# DCOM 權限檢查指南 - Bachmann OPC Server

## 問題診斷

您遇到的問題是程式進入 `da_client.py` 的 `read()` 方法後沒有回應，這通常是由於：

1. **DCOM 權限設定不正確** - COM 呼叫被阻擋或逾時
2. **SyncRead 呼叫卡住** - 伺服器無法回應或權限不足
3. **pythoncom 執行緒問題** - COM 執行緒模型配置不當

## DCOM 權限設定檢查步驟

### 1. 開啟 Component Services (dcomcnfg)

1. 按 `Win + R`，輸入 `dcomcnfg`，按 Enter
2. 展開 **Component Services** → **Computers** → **My Computer**

### 2. 檢查全域 DCOM 設定

1. 右鍵點擊 **My Computer**，選擇 **Properties**
2. 進入 **Default Properties** 標籤
   - 確認 **Enable Distributed COM on this computer** 已勾選
   - **Default Authentication Level**: 設為 **Connect** 或更高
   - **Default Impersonation Level**: 設為 **Identify** 或更高

3. 進入 **COM Security** 標籤

   **Access Permissions（存取權限）：**
   - 點擊 **Edit Default**
   - 確保您的使用者帳號或 **Everyone** 群組有：
     - ✅ Local Access
     - ✅ Remote Access

   **Launch and Activation Permissions（啟動與啟用權限）：**
   - 點擊 **Edit Default**
   - 確保您的使用者帳號或 **Everyone** 群組有：
     - ✅ Local Launch
     - ✅ Remote Launch
     - ✅ Local Activation
     - ✅ Remote Activation

### 3. 檢查 OPC Server 特定設定

1. 在 **Component Services** → **Computers** → **My Computer** → **DCOM Config** 中
2. 尋找以下項目：
   - `Graybox.OPC.DAWrapper`
   - `BACHMANN.OPCEnterpriseServer.2`
   - `OPC` 開頭的相關項目

3. 右鍵點擊，選擇 **Properties**

#### General 標籤
- **Authentication Level**: 設為 **Default** 或 **Connect**

#### Location 標籤
- 確認 **Run application on this computer** 已勾選

#### Security 標籤
確保以下三個項目都設定正確：

**Launch and Activation Permissions:**
- 選擇 **Customize**
- 點擊 **Edit**
- 加入您的使用者帳號，給予：
  - ✅ Local Launch
  - ✅ Remote Launch
  - ✅ Local Activation
  - ✅ Remote Activation

**Access Permissions:**
- 選擇 **Customize**
- 點擊 **Edit**
- 加入您的使用者帳號，給予：
  - ✅ Local Access
  - ✅ Remote Access

**Configuration Permissions:**
- 選擇 **Customize**
- 點擊 **Edit**
- 加入您的使用者帳號，給予：
  - ✅ Full Control
  - ✅ Read

#### Identity 標籤
- 選擇 **The interactive user** 或 **This user**（填入您的帳號）

### 4. 防火牆設定

1. 開啟 **Windows Defender 防火牆**
2. 點擊 **允許應用程式或功能通過 Windows Defender 防火牆**
3. 確保以下項目已勾選（如果存在）：
   - OPC 相關服務
   - Python (python.exe)
   - 您的 OPC Server 程式

### 5. 檢查服務狀態

1. 按 `Win + R`，輸入 `services.msc`
2. 尋找 OPC 相關服務（例如：Bachmann OPC Server）
3. 確認：
   - 服務狀態為 **執行中**
   - 啟動類型為 **自動** 或 **手動**
   - 登入身分設定正確

## 程式碼層級的改進

我已經創建了改進版的程式 `opc_data_reader_fixed.py`，包含以下改進：

### 1. 新增的功能

- **分批讀取**：使用 `--read-batch-size` 參數控制每次讀取的標籤數量
- **逾時控制**：使用執行緒實現更可靠的逾時機制
- **非同步模式**：使用 `--use-async` 參數嘗試非同步讀取
- **詳細錯誤追蹤**：印出完整的 traceback 協助診斷
- **逐一讀取降級**：當批次讀取失敗時，自動改用逐一讀取

### 2. 使用方式

```bash
# 基本診斷模式（推薦先執行）
python opc_data_reader_fixed.py --diag-only

# 使用較小的批次大小（更穩定）
python opc_data_reader_fixed.py --read-batch-size 3

# 啟用非同步模式
python opc_data_reader_fixed.py --use-async

# 啟用除錯模式
python opc_data_reader_fixed.py --debug-opc

# 組合使用
python opc_data_reader_fixed.py --read-batch-size 3 --use-async --debug-opc
```

## 常見問題排除

### 問題 1：程式卡在 SyncRead
**症狀**：進入 `da_client.py` 後無回應

**解決方案**：
1. 檢查上述所有 DCOM 權限設定
2. 使用改進版程式的 `--use-async` 參數
3. 減少 `--read-batch-size` 到 1-3
4. 確認 OPC Server 服務正在運行

### 問題 2：Access Denied 錯誤
**症狀**：出現 "Access is denied" 錯誤

**解決方案**：
1. 以**系統管理員身分**執行 Python
2. 檢查 DCOM Security 設定中的所有權限
3. 將使用者加入 **Distributed COM Users** 群組
4. 重新啟動電腦

### 問題 3：COM 初始化失敗
**症狀**：pythoncom.CoInitialize() 失敗

**解決方案**：
1. 確認使用 32-bit Python
2. 重新註冊 DLL：
   ```cmd
   regsvr32 "路徑\gbda_aut.dll"
   ```
3. 重建 COM cache：
   ```python
   import win32com.client
   win32com.client.gencache.Rebuild(verbose=1)
   ```

## 進階診斷指令

### 查看 DCOM 設定
```cmd
# 匯出 DCOM 權限設定
reg export "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Ole" dcom_settings.reg

# 查看 OPC Server 註冊資訊
reg query "HKEY_CLASSES_ROOT\CLSID" /s /f "Bachmann"
```

### Python 環境檢查
```python
# 檢查 Python 位元版本
import platform
print(platform.architecture())  # 應該是 ('32bit', ...)

# 檢查 win32com 版本
import win32com
print(win32com.__file__)

# 測試 COM 初始化
import pythoncom
pythoncom.CoInitialize()
print("COM initialized successfully")
pythoncom.CoUninitialize()
```

## 建議的測試順序

1. **執行基本診斷**
   ```bash
   python opc_data_reader_fixed.py --diag-only
   ```

2. **如果步驟 1 失敗**，檢查並修正 DCOM 權限

3. **如果步驟 3 成功**，使用小批次測試
   ```bash
   python opc_data_reader_fixed.py --read-batch-size 1 --debug-opc
   ```

4. **如果仍然卡住**，嘗試非同步模式
   ```bash
   python opc_data_reader_fixed.py --read-batch-size 1 --use-async --debug-opc
   ```

5. **成功後逐步增加批次大小**
   ```bash
   python opc_data_reader_fixed.py --read-batch-size 5
   ```

## 聯絡資訊

如果以上步驟都無法解決問題，建議：

1. 檢查 OPC Server 的官方文件
2. 使用 OPC Server 廠商提供的測試工具（例如：Matrikon OPC Explorer）
3. 查看 Windows 事件檢視器中的錯誤記錄
4. 聯絡 Bachmann 技術支援

## 參考資料

- [Microsoft DCOM 文件](https://docs.microsoft.com/en-us/windows/win32/com/dcom)
- [OPC Foundation 技術支援](https://opcfoundation.org/)
- [OpenOPC2 GitHub](https://github.com/reluxa/openopc2)
