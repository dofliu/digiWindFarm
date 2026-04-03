#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPC 直接讀取測試程式 - 繞過 openopc2 的 read/iread 方法
直接使用底層 COM 介面進行讀取
"""

import sys
import time
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root / "openopc2-0.1.18"))

import pythoncom
import win32com.client

# OPC 伺服器設定
OPC_SERVER = "BACHMANN.OPCEnterpriseServer.2"
OPC_CLASS = "Graybox.OPC.DAWrapper"
OPC_HOST = "localhost"

# 測試標籤
TEST_TAGS = [
    "Z72.H01.WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedNacAvg10m",
    "Z72.H01.WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedNac",
    "Z72.H01.WTUR.Z72PLC__UI_Loc_WTUR_State_TurSt",
]


def print_step(msg):
    print(f"\n{'='*80}")
    print(f"  {msg}")
    print(f"{'='*80}")


def direct_read_test():
    """
    使用底層 COM 介面直接讀取 OPC 標籤
    """
    print_step("開始 OPC 直接讀取測試")

    opc_client = None
    opc_group = None

    try:
        # 步驟 1: 初始化 COM
        print("\n[1] 初始化 COM...")
        pythoncom.CoInitialize()
        print("    ✓ COM 初始化成功")

        # 步驟 2: 建立 OPC 客戶端
        print("\n[2] 建立 OPC 客戶端...")
        print(f"    使用 COM 類別: {OPC_CLASS}")
        opc_client = win32com.client.Dispatch(OPC_CLASS)
        print("    ✓ OPC 客戶端建立成功")

        # 步驟 3: 連接到 OPC 伺服器
        print("\n[3] 連接到 OPC 伺服器...")
        print(f"    伺服器: {OPC_SERVER}")
        print(f"    主機: {OPC_HOST}")
        opc_client.Connect(OPC_SERVER, OPC_HOST)
        print("    ✓ 連接成功")

        # 顯示伺服器資訊
        print("\n[伺服器資訊]")
        print(f"    ServerName: {opc_client.ServerName}")
        print(f"    ServerState: {opc_client.ServerState}")
        print(f"    Version: {opc_client.MajorVersion}.{opc_client.MinorVersion}")

        # 步驟 4: 建立 OPC 群組
        print("\n[4] 建立 OPC 群組...")
        opc_groups = opc_client.OPCGroups
        opc_groups.DefaultGroupIsActive = True
        opc_groups.DefaultGroupUpdateRate = 1000
        opc_group = opc_groups.Add("TestGroup")
        print(f"    ✓ 群組建立成功: {opc_group.Name}")
        print(f"    群組 UpdateRate: {opc_group.UpdateRate} ms")
        print(f"    群組 IsActive: {opc_group.IsActive}")

        # 步驟 5: 加入 OPC 項目（標籤）
        print("\n[5] 加入 OPC 項目...")
        opc_items = opc_group.OPCItems

        # 準備標籤列表（需要在索引 0 放入計數）
        tag_count = len(TEST_TAGS)
        tags_with_index = [0] + TEST_TAGS  # [0, tag1, tag2, tag3]
        client_handles = [0] + list(range(1, tag_count + 1))  # [0, 1, 2, 3]

        print(f"    準備加入 {tag_count} 個標籤...")
        for i, tag in enumerate(TEST_TAGS, 1):
            print(f"      {i}. {tag}")

        # 驗證標籤
        print("\n    驗證標籤...")
        errors = opc_items.Validate(tag_count, tags_with_index)

        valid_tags = []
        valid_handles = []
        for i in range(tag_count):
            if errors[i] == 0:
                print(f"      ✓ {TEST_TAGS[i]} - 有效")
                valid_tags.append(TEST_TAGS[i])
                valid_handles.append(client_handles[i+1])
            else:
                error_msg = opc_client.GetErrorString(errors[i])
                print(f"      ✗ {TEST_TAGS[i]} - 無效: {error_msg}")

        if not valid_tags:
            print("\n[✗] 沒有有效的標籤，無法繼續測試")
            return

        # 加入有效的標籤
        print(f"\n    加入 {len(valid_tags)} 個有效標籤...")
        valid_tags_with_index = [0] + valid_tags
        valid_handles_with_index = [0] + valid_handles

        server_handles, add_errors = opc_items.AddItems(
            len(valid_tags),
            valid_tags_with_index,
            valid_handles_with_index
        )

        final_tags = []
        final_server_handles = []
        for i in range(len(valid_tags)):
            if add_errors[i] == 0:
                print(f"      ✓ {valid_tags[i]} - 已加入（ServerHandle: {server_handles[i]}）")
                final_tags.append(valid_tags[i])
                final_server_handles.append(server_handles[i])
            else:
                error_msg = opc_client.GetErrorString(add_errors[i])
                print(f"      ✗ {valid_tags[i]} - 加入失敗: {error_msg}")

        if not final_tags:
            print("\n[✗] 沒有成功加入的標籤，無法繼續測試")
            return

        # 步驟 6: 同步讀取
        print("\n[6] 執行同步讀取 (SyncRead)...")
        print("    這是最容易卡住的步驟！")
        print("    準備讀取...")

        handles_with_index = [0] + final_server_handles
        data_source = 2  # 2 = OPC_DS_DEVICE (從設備讀取)

        print(f"    呼叫 SyncRead(DataSource={data_source}, Count={len(final_tags)})...")
        print("    如果這裡卡住，問題就是 DCOM 權限或伺服器回應！")

        # 這裡是關鍵：SyncRead 可能會卡住
        start_time = time.time()
        values, read_errors, qualities, timestamps = opc_group.SyncRead(
            data_source,
            len(final_tags),
            handles_with_index
        )
        elapsed = time.time() - start_time

        print(f"    ✓ SyncRead 完成！耗時 {elapsed:.2f} 秒")

        # 步驟 7: 顯示結果
        print("\n[7] 讀取結果:")
        print("-" * 80)

        for i, tag in enumerate(final_tags):
            value = values[i]
            quality = qualities[i]
            timestamp = timestamps[i]
            error = read_errors[i]

            # 品質位元解碼
            quality_status = (quality >> 6) & 3
            quality_text = ["Bad", "Uncertain", "Unknown", "Good"][quality_status]

            error_msg = ""
            if error != 0:
                error_msg = f" (錯誤: {opc_client.GetErrorString(error)})"

            print(f"  標籤: {tag}")
            print(f"    值: {value}")
            print(f"    品質: {quality_text} ({quality})")
            print(f"    時間: {timestamp}")
            print(f"    錯誤碼: {error}{error_msg}")
            print()

        print("-" * 80)
        print("\n✓ 測試成功完成！")

    except Exception as e:
        print(f"\n[✗] 發生錯誤: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # 清理
        print("\n[清理]")
        try:
            if opc_group:
                print("    移除 OPC 群組...")
                opc_client.OPCGroups.Remove(opc_group.Name)
                print("    ✓ 群組已移除")
        except:
            pass

        try:
            if opc_client:
                print("    斷開連接...")
                opc_client.Disconnect()
                print("    ✓ 已斷開連接")
        except:
            pass

        try:
            print("    解除 COM 初始化...")
            pythoncom.CoUninitialize()
            print("    ✓ COM 已清理")
        except:
            pass


def timeout_read_test(timeout_seconds=15):
    """
    使用執行緒實現逾時的讀取測試
    """
    import threading

    print_step(f"開始帶逾時的 OPC 讀取測試（逾時: {timeout_seconds} 秒）")

    result_container = {"success": False, "error": None}

    def read_task():
        try:
            direct_read_test()
            result_container["success"] = True
        except Exception as e:
            result_container["error"] = e

    print(f"\n啟動讀取執行緒...")
    thread = threading.Thread(target=read_task, daemon=True)
    thread.start()

    print(f"等待結果（最多 {timeout_seconds} 秒）...")
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        print(f"\n[✗] 讀取逾時！執行緒在 {timeout_seconds} 秒內沒有完成")
        print("\n這表示程式確實卡在 SyncRead 呼叫中。")
        print("\n可能的原因：")
        print("  1. DCOM 權限設定不正確（最可能）")
        print("  2. OPC 伺服器沒有正確回應")
        print("  3. 防火牆阻擋了通訊")
        print("  4. 標籤不存在或無法讀取")
        print("\n建議檢查 DCOM權限檢查指南.md 中的所有設定！")
        return False
    elif result_container["success"]:
        print("\n✓ 讀取成功完成！")
        return True
    else:
        print(f"\n[✗] 讀取失敗: {result_container['error']}")
        return False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OPC 直接讀取測試程式")
    parser.add_argument(
        "--timeout",
        type=int,
        default=15,
        help="讀取逾時秒數（預設: 15）"
    )
    parser.add_argument(
        "--no-timeout",
        action="store_true",
        help="不使用逾時機制（可能會永久卡住）"
    )

    args = parser.parse_args()

    if args.no_timeout:
        print("\n警告：未啟用逾時機制，程式可能會永久卡住！")
        print("按 Ctrl+C 可以中斷程式\n")
        time.sleep(2)
        direct_read_test()
    else:
        timeout_read_test(args.timeout)
