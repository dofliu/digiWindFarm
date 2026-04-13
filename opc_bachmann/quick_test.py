#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速測試腳本 - 用於診斷 OPC 讀取問題
"""

import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root / "openopc2-0.1.18"))

import pythoncom
import win32com.client

OPC_SERVER = "BACHMANN.OPCEnterpriseServer.2"
OPC_CLASS = "Graybox.OPC.DAWrapper"
OPC_HOST = "localhost"
TEST_TAG = "Z72.H01.WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedNacAvg10m"

print("\n" + "="*80)
print("OPC 讀取問題快速診斷")
print("="*80)

# 測試 1: COM 初始化
print("\n[測試 1] COM 初始化...")
try:
    pythoncom.CoInitialize()
    print("✓ COM 初始化成功")
except Exception as e:
    print(f"✗ COM 初始化失敗: {e}")
    sys.exit(1)

# 測試 2: 建立 OPC 客戶端
print("\n[測試 2] 建立 OPC 客戶端...")
try:
    opc = win32com.client.Dispatch(OPC_CLASS)
    print(f"✓ OPC 客戶端建立成功（類別: {OPC_CLASS}）")
except Exception as e:
    print(f"✗ OPC 客戶端建立失敗: {e}")
    sys.exit(1)

# 測試 3: 連接到伺服器
print("\n[測試 3] 連接到伺服器...")
try:
    opc.Connect(OPC_SERVER, OPC_HOST)
    print("✓ 連接成功")
    print(f"  ServerName: {opc.ServerName}")
    print(f"  ServerState: {opc.ServerState}")
except Exception as e:
    print(f"✗ 連接失敗: {e}")
    sys.exit(1)

# 測試 4: 建立群組
print("\n[測試 4] 建立 OPC 群組...")
try:
    groups = opc.OPCGroups
    group = groups.Add("QuickTestGroup")
    print(f"✓ 群組建立成功: {group.Name}")
except Exception as e:
    print(f"✗ 群組建立失敗: {e}")
    sys.exit(1)

# 測試 5: 加入項目
print("\n[測試 5] 加入測試標籤...")
print(f"  標籤: {TEST_TAG}")
try:
    items = group.OPCItems

    # 驗證標籤
    errors = items.Validate(1, [0, TEST_TAG])
    if errors[0] != 0:
        error_msg = opc.GetErrorString(errors[0])
        print(f"✗ 標籤驗證失敗: {error_msg}")
        sys.exit(1)
    print("  ✓ 標籤驗證通過")

    # 加入標籤
    server_handles, add_errors = items.AddItems(1, [0, TEST_TAG], [0, 1])
    if add_errors[0] != 0:
        error_msg = opc.GetErrorString(add_errors[0])
        print(f"✗ 標籤加入失敗: {error_msg}")
        sys.exit(1)
    print(f"  ✓ 標籤加入成功（ServerHandle: {server_handles[0]}）")

except Exception as e:
    print(f"✗ 項目操作失敗: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 測試 6: 關鍵測試 - SyncRead
print("\n[測試 6] 執行 SyncRead...")
print("  這是最關鍵的測試！")
print("  如果這裡卡住超過 5 秒，請按 Ctrl+C 中斷")
print("  然後檢查 DCOM 權限設定\n")

try:
    print("  → 準備讀取...")
    print("  → 呼叫 SyncRead...")

    import threading
    result = [None]
    error = [None]

    def read_thread():
        try:
            print("    [執行緒] 開始 SyncRead...")
            start = time.time()
            values, read_errors, qualities, timestamps = group.SyncRead(
                2,  # OPC_DS_DEVICE
                1,
                [0, server_handles[0]]
            )
            elapsed = time.time() - start
            result[0] = (values, read_errors, qualities, timestamps, elapsed)
            print(f"    [執行緒] SyncRead 完成（耗時 {elapsed:.2f}s）")
        except Exception as e:
            error[0] = e
            print(f"    [執行緒] SyncRead 失敗: {e}")

    thread = threading.Thread(target=read_thread, daemon=True)
    thread.start()

    # 等待最多 10 秒
    for i in range(10):
        if not thread.is_alive():
            break
        print(f"  等待中... {i+1}s")
        time.sleep(1)

    if thread.is_alive():
        print("\n✗✗✗ SyncRead 逾時（超過 10 秒）✗✗✗")
        print("\n問題確認：SyncRead 呼叫被阻塞")
        print("\n最可能的原因是 DCOM 權限設定問題！")
        print("\n請按照以下步驟檢查：")
        print("  1. 執行 dcomcnfg")
        print("  2. 找到 Graybox.OPC.DAWrapper")
        print("  3. 檢查 Security 標籤中的三個權限：")
        print("     - Launch and Activation Permissions")
        print("     - Access Permissions")
        print("     - Configuration Permissions")
        print("  4. 確保您的使用者有完整權限")
        print("\n詳細步驟請參考 DCOM權限檢查指南.md")
        sys.exit(1)

    if error[0]:
        print(f"\n✗ SyncRead 失敗: {error[0]}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    if result[0]:
        values, read_errors, qualities, timestamps, elapsed = result[0]
        print("\n✓✓✓ SyncRead 成功！✓✓✓")
        print(f"\n耗時: {elapsed:.2f} 秒")

        # 顯示結果
        value = values[0]
        quality = qualities[0]
        timestamp = timestamps[0]
        read_error = read_errors[0]

        quality_status = (quality >> 6) & 3
        quality_text = ["Bad", "Uncertain", "Unknown", "Good"][quality_status]

        print("\n讀取結果：")
        print(f"  標籤: {TEST_TAG}")
        print(f"  值: {value}")
        print(f"  品質: {quality_text}")
        print(f"  時間: {timestamp}")
        print(f"  錯誤碼: {read_error}")

        if read_error == 0 and quality_text == "Good":
            print("\n✓✓✓ 完美！OPC 讀取完全正常 ✓✓✓")
            print("\n這表示您的 DCOM 權限設定是正確的。")
            print("原始程式的問題可能在於 openopc2 的實作細節。")
            print("\n建議使用 opc_direct_read_test.py 來讀取資料。")
        else:
            print("\n⚠ 讀取成功但資料品質有問題")
            print("這可能表示標籤存在但目前沒有有效資料。")

except KeyboardInterrupt:
    print("\n\n[!] 使用者中斷測試")
    print("\n如果是在 SyncRead 階段中斷，這確認了 DCOM 權限問題。")
except Exception as e:
    print(f"\n✗ 測試失敗: {e}")
    import traceback
    traceback.print_exc()
finally:
    # 清理
    print("\n[清理資源]")
    try:
        opc.OPCGroups.Remove(group.Name)
        opc.Disconnect()
        pythoncom.CoUninitialize()
        print("✓ 清理完成")
    except:
        pass

print("\n" + "="*80)
print("測試完成")
print("="*80 + "\n")
