#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
專門診斷 AddItems 卡住問題
逐步拆解 AddItems 操作，找出確切的卡點
"""

import sys
import time
import threading
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root / "openopc2-0.1.18"))

import pythoncom
import win32com.client

OPC_SERVER = "BACHMANN.OPCEnterpriseServer.2"
OPC_CLASS = "Graybox.OPC.DAWrapper"
OPC_HOST = "localhost"
TEST_TAG = "Z72.H01.WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedNacAvg10m"

def test_with_timeout(func, timeout=5, description="操作", needs_com=False):
    """執行函數並設定逾時"""
    result = [None]
    error = [None]

    def wrapper():
        try:
            # 如果需要 COM，在執行緒內初始化
            if needs_com:
                pythoncom.CoInitialize()
            result[0] = func()
            if needs_com:
                pythoncom.CoUninitialize()
        except Exception as e:
            error[0] = e
            if needs_com:
                try:
                    pythoncom.CoUninitialize()
                except:
                    pass

    thread = threading.Thread(target=wrapper, daemon=True)
    print(f"  → 開始 {description}...", flush=True)
    thread.start()

    for i in range(timeout):
        if not thread.is_alive():
            break
        if i > 0 and i % 2 == 0:
            print(f"    等待中... {i}s", flush=True)
        time.sleep(1)

    if thread.is_alive():
        print(f"  ✗ {description} 逾時（超過 {timeout} 秒）")
        return None, True

    if error[0]:
        print(f"  ✗ {description} 失敗: {error[0]}")
        return None, False

    print(f"  ✓ {description} 成功")
    return result[0], False

print("\n" + "="*80)
print("診斷 AddItems 卡住問題")
print("="*80)

opc = None
group = None
items = None

try:
    # 步驟 1: COM 初始化（在主執行緒）
    print("\n[步驟 1] COM 初始化（主執行緒）")
    try:
        pythoncom.CoInitialize()
        print("  ✓ COM 初始化成功")
    except Exception as e:
        print(f"  ✗ COM 初始化失敗: {e}")
        sys.exit(1)

    # 步驟 2: 建立客戶端（不使用逾時，因為 COM 已初始化）
    print("\n[步驟 2] 建立 OPC 客戶端")
    try:
        print("  → 開始 Dispatch...", flush=True)
        opc = win32com.client.Dispatch(OPC_CLASS)
        print("  ✓ Dispatch 成功")
    except Exception as e:
        print(f"  ✗ Dispatch 失敗: {e}")
        print("\n可能原因：")
        print("  1. OPC_CLASS 設定錯誤")
        print("  2. gbda_aut.dll 未正確註冊")
        print("  3. DCOM Launch Permissions 不足")
        sys.exit(1)

    # 步驟 3: 連接（使用逾時監控）
    print("\n[步驟 3] 連接到 OPC 伺服器")
    print("  → 開始 Connect...", flush=True)

    connect_done = [False]
    connect_error = [None]

    def connect_thread():
        try:
            opc.Connect(OPC_SERVER, OPC_HOST)
            connect_done[0] = True
        except Exception as e:
            connect_error[0] = e

    thread = threading.Thread(target=connect_thread, daemon=True)
    thread.start()

    for i in range(10):
        if connect_done[0] or connect_error[0]:
            break
        if i > 0 and i % 2 == 0:
            print(f"    等待中... {i}s", flush=True)
        time.sleep(1)

    if connect_error[0]:
        print(f"  ✗ Connect 失敗: {connect_error[0]}")
        sys.exit(1)
    elif not connect_done[0]:
        print("  ✗ Connect 逾時（超過 10 秒）")
        sys.exit(1)

    print("  ✓ Connect 成功")
    print(f"    ServerName: {opc.ServerName}")

    # 步驟 4: 建立群組
    print("\n[步驟 4] 建立 OPC 群組")
    try:
        print("  → 開始 Add Group...", flush=True)
        groups = opc.OPCGroups
        group = groups.Add("DiagGroup")
        print("  ✓ Add Group 成功")
        print(f"    GroupName: {group.Name}")
    except Exception as e:
        print(f"  ✗ Add Group 失敗: {e}")
        sys.exit(1)

    # 取得 OPCItems 介面
    print("\n[步驟 4.5] 取得 OPCItems 介面")
    try:
        print("  → 開始 Get OPCItems...", flush=True)
        items = group.OPCItems
        print("  ✓ Get OPCItems 成功")
    except Exception as e:
        print(f"  ✗ Get OPCItems 失敗: {e}")
        sys.exit(1)

    # 步驟 5a: Validate（驗證標籤）- 使用逾時監控
    print("\n[步驟 5a] 驗證標籤（Validate）")
    print(f"    標籤: {TEST_TAG}")
    print("  → 開始 Validate...", flush=True)

    validate_result = [None]
    validate_error = [None]

    def validate_thread():
        try:
            validate_result[0] = items.Validate(1, [0, TEST_TAG])
        except Exception as e:
            validate_error[0] = e

    thread = threading.Thread(target=validate_thread, daemon=True)
    thread.start()

    for i in range(10):
        if validate_result[0] is not None or validate_error[0]:
            break
        if i > 0 and i % 2 == 0:
            print(f"    等待中... {i}s", flush=True)
        time.sleep(1)

    if validate_error[0]:
        print(f"  ✗ Validate 失敗: {validate_error[0]}")
        sys.exit(1)
    elif validate_result[0] is None:
        print("\n✗✗✗✗✗ 找到問題了！Validate 逾時 ✗✗✗✗✗")
        print("\n問題定位：items.Validate() 呼叫被阻塞")
        print("\n這表示 DCOM 權限在『項目驗證』層級就有問題")
        print("\n重點檢查：")
        print("  1. dcomcnfg → Graybox.OPC.DAWrapper → Security")
        print("  2. Access Permissions → 確保有 Local Access")
        print("  3. Identity → 建議改為 'The interactive user'")
        sys.exit(1)

    errors = validate_result[0]
    if errors[0] != 0:
        error_msg = opc.GetErrorString(errors[0])
        print(f"  ✗ 標籤驗證失敗: {error_msg}")
        print("\n這表示標籤不存在或無效，請檢查標籤名稱")
        sys.exit(1)

    print("  ✓ Validate 成功")
    print("    標籤驗證通過")

    # 步驟 5b: AddItems（加入項目）- 這是關鍵！
    print("\n[步驟 5b] 加入項目（AddItems）")
    print("    這是您卡住的地方！")
    print("  → 開始 AddItems...", flush=True)

    additems_result = [None]
    additems_error = [None]

    def additems_thread():
        try:
            additems_result[0] = items.AddItems(1, [0, TEST_TAG], [0, 1])
        except Exception as e:
            additems_error[0] = e

    thread = threading.Thread(target=additems_thread, daemon=True)
    thread.start()

    for i in range(15):
        if additems_result[0] is not None or additems_error[0]:
            break
        if i > 0 and i % 2 == 0:
            print(f"    等待中... {i}s", flush=True)
        time.sleep(1)

    if additems_error[0]:
        print(f"  ✗ AddItems 失敗: {additems_error[0]}")
        sys.exit(1)
    elif additems_result[0] is None:
        print("\n✗✗✗✗✗ 確認問題！AddItems 逾時 ✗✗✗✗✗")
        print("\n問題定位：items.AddItems() 呼叫被阻塞")
        print("\n這是一個 DCOM Access Permissions 問題")
        print("\n解決方案：")
        print("\n1. 開啟 dcomcnfg")
        print("2. 展開 Component Services → Computers → My Computer → DCOM Config")
        print("3. 找到 'Graybox.OPC.DAWrapper'")
        print("4. 右鍵 → Properties → Security 標籤")
        print("\n5. 【重點】Access Permissions:")
        print("   - 選擇 'Customize'")
        print("   - 點擊 'Edit'")
        print("   - 點擊 'Add' 加入您的使用者（或 Everyone）")
        print("   - 勾選 'Local Access' 和 'Remote Access'")
        print("   - 點擊 'OK' 儲存")
        print("\n6. 【同時檢查】Launch and Activation Permissions:")
        print("   - 也要確保有 Local Launch 和 Local Activation")
        print("\n7. 【建議】Identity 標籤:")
        print("   - 選擇 'The interactive user'")
        print("\n8. 套用所有變更並重新執行此腳本")
        print("\n如果還是不行，試試看以系統管理員身分執行 Python")
        sys.exit(1)

    server_handles, add_errors = additems_result[0]
    if add_errors[0] != 0:
        error_msg = opc.GetErrorString(add_errors[0])
        print(f"  ✗ AddItems 回傳錯誤: {error_msg}")
        sys.exit(1)

    print("  ✓ AddItems 成功！")
    print(f"    ServerHandle: {server_handles[0]}")

    # 步驟 6: SyncRead（如果能到這裡）
    print("\n[步驟 6] 同步讀取（SyncRead）")
    print("    如果能到這一步，表示 AddItems 問題已解決")
    print("  → 開始 SyncRead...", flush=True)

    syncread_result = [None]
    syncread_error = [None]

    def syncread_thread():
        try:
            syncread_result[0] = group.SyncRead(2, 1, [0, server_handles[0]])
        except Exception as e:
            syncread_error[0] = e

    thread = threading.Thread(target=syncread_thread, daemon=True)
    thread.start()

    for i in range(10):
        if syncread_result[0] is not None or syncread_error[0]:
            break
        if i > 0 and i % 2 == 0:
            print(f"    等待中... {i}s", flush=True)
        time.sleep(1)

    if syncread_error[0]:
        print(f"  ✗ SyncRead 失敗: {syncread_error[0]}")
        sys.exit(1)
    elif syncread_result[0] is None:
        print("  ✗ SyncRead 逾時（超過 10 秒）")
        print("\nAddItems 成功但 SyncRead 失敗，這是另一個問題")
        sys.exit(1)

    values, read_errors, qualities, timestamps = syncread_result[0]
    print("  ✓ SyncRead 成功！")

    print(f"\n✓✓✓ 完全成功！✓✓✓")
    print(f"\n讀取結果：")
    print(f"  標籤: {TEST_TAG}")
    print(f"  值: {values[0]}")
    print(f"  品質: {qualities[0]}")
    print(f"  時間: {timestamps[0]}")

except KeyboardInterrupt:
    print("\n\n[!] 使用者中斷")
    print("\n在哪個步驟被中斷，那個步驟就是問題所在")
except Exception as e:
    print(f"\n✗ 未預期的錯誤: {e}")
    import traceback
    traceback.print_exc()
finally:
    print("\n[清理]")
    try:
        if group and opc:
            opc.OPCGroups.Remove(group.Name)
        if opc:
            opc.Disconnect()
        pythoncom.CoUninitialize()
    except:
        pass

print("\n" + "="*80)
print("診斷結束")
print("="*80 + "\n")
