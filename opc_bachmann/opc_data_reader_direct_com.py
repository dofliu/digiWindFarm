#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPC 資料持續擷取程式 - 直接使用 COM 介面
完全繞過 openopc2 的 read() 和 iread() 方法，直接使用底層 COM API
"""

import time
import re
import sys
from pathlib import Path
from datetime import datetime, timedelta

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root / "openopc2-0.1.18"))

import pythoncom
import win32com.client
import pytz

# ==================== 配置部分 ====================
OPC_SERVER = "BACHMANN.OPCEnterpriseServer.2"
OPC_HOST = "localhost"
OPC_CLASS = "Graybox.OPC.DAWrapper"

# 資料擷取範圍
START = 1
END = 1

# 擷取間隔（秒）
SLEEP_TIME = 17

# OPC Tag 基礎配置
BASE_TAGS = [
    "Z72.H{}.WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedNacAvg10m",
    "Z72.H{}.WMET.Z72PLC__UI_Loc_WMET_Analogue_WSpeedNac",
    "Z72.H{}.Z72PLC__ActiveAlarm[0]",
    "Z72.H{}.Z72PLC__ActiveAlarm[1]",
    "Z72.H{}.Z72PLC__ActiveAlarm[2]",
    "Z72.H{}.Z72PLC__ActiveAlarm[3]",
    "Z72.H{}.Z72PLC__ActiveAlarm[4]",
    "Z72.H{}.Z72PLC__ActiveAlarm[5]",
    "Z72.H{}.Z72PLC__ActiveAlarm[6]",
    "Z72.H{}.Z72PLC__ActiveAlarm[7]",
    "Z72.H{}.Z72PLC__ActiveAlarm[8]",
    "Z72.H{}.Z72PLC__ActiveAlarm[9]",
    "Z72.H{}.Z72PLC__ActiveTrip1[0]",
    "Z72.H{}.Z72PLC__ActiveTrip1[1]",
    "Z72.H{}.Z72PLC__ActiveTrip1[2]",
    "Z72.H{}.Z72PLC__ActiveTrip1[3]",
    "Z72.H{}.Z72PLC__ActiveTrip1[4]",
    "Z72.H{}.Z72PLC__ActiveTrip1[5]",
    "Z72.H{}.Z72PLC__ActiveTrip1[6]",
    "Z72.H{}.Z72PLC__ActiveTrip1[7]",
    "Z72.H{}.Z72PLC__ActiveTrip1[8]",
    "Z72.H{}.Z72PLC__ActiveTrip1[9]",
    "Z72.H{}.Z72PLC__ActiveTrip2[0]",
    "Z72.H{}.Z72PLC__ActiveTrip2[1]",
    "Z72.H{}.Z72PLC__ActiveTrip2[2]",
    "Z72.H{}.Z72PLC__ActiveTrip2[3]",
    "Z72.H{}.Z72PLC__ActiveTrip2[4]",
    "Z72.H{}.Z72PLC__ActiveTrip2[5]",
    "Z72.H{}.Z72PLC__ActiveTrip2[6]",
    "Z72.H{}.Z72PLC__ActiveTrip2[7]",
    "Z72.H{}.Z72PLC__ActiveTrip2[8]",
    "Z72.H{}.Z72PLC__ActiveTrip2[9]",
    "Z72.H{}.WTUR.Z72PLC__UI_Loc_WTUR_State_TurSt"
]

# OPC Data Source 常數
OPC_DS_CACHE = 1
OPC_DS_DEVICE = 2

def add_eight_hours(original_time):
    """將時間增加 8 小時（UTC+8）"""
    return original_time + timedelta(hours=8)


def get_adjusted_time(tag_time):
    """調整時間戳記，將時間轉換為 UTC+8"""
    try:
        if isinstance(tag_time, str):
            tag_time = datetime.strptime(tag_time, '%Y-%m-%d %H:%M:%S.%f%z')
        adjusted_time = add_eight_hours(tag_time)
        return adjusted_time.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_quality_string(quality_bits):
    """轉換 OPC 品質位元為字串"""
    quality = (quality_bits >> 6) & 3
    quality_map = {0: "Bad", 1: "Uncertain", 2: "Unknown", 3: "Good"}
    return quality_map.get(quality, "Unknown")


class DirectOpcClient:
    """直接使用 COM 介面的 OPC 客戶端（繞過 openopc2 的 read/iread）"""

    def __init__(self):
        self.opc_client = None
        self.opc_group = None
        self.connected = False
        self.items_added = False
        self.server_handles = []
        self.tag_list = []

    def initialize(self):
        """初始化 COM 和 OPC 客戶端"""
        print("="*80)
        print("初始化 OPC 客戶端（直接 COM 模式）")
        print("="*80)

        try:
            print("\n[1] 初始化 COM...")
            pythoncom.CoInitialize()
            print("    ✓ COM 初始化成功")

            print("\n[2] 建立 OPC 客戶端...")
            self.opc_client = win32com.client.Dispatch(OPC_CLASS)
            print(f"    ✓ 客戶端建立成功（{OPC_CLASS}）")

            print("\n[3] 連接到 OPC 伺服器...")
            self.opc_client.Connect(OPC_SERVER, OPC_HOST)
            self.connected = True
            print(f"    ✓ 連接成功")
            print(f"    ServerName: {self.opc_client.ServerName}")
            print(f"    ServerState: {self.opc_client.ServerState}")

            print("\n[4] 建立 OPC 群組...")
            opc_groups = self.opc_client.OPCGroups
            opc_groups.DefaultGroupIsActive = True
            opc_groups.DefaultGroupUpdateRate = 1000
            self.opc_group = opc_groups.Add("DataReadGroup")
            print(f"    ✓ 群組建立成功: {self.opc_group.Name}")

            return True

        except Exception as e:
            print(f"    ✗ 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def add_tags(self, tags):
        """加入 OPC 標籤到群組（逐一加入避免卡住）"""
        print("\n[5] 加入 OPC 標籤...")
        print(f"    準備加入 {len(tags)} 個標籤")
        print("    使用逐一加入模式（避免批次 AddItems 卡住）")

        try:
            opc_items = self.opc_group.OPCItems

            final_tags = []
            final_server_handles = []
            failed_count = 0

            # 逐一加入每個標籤
            for i, tag in enumerate(tags, 1):
                try:
                    # 每次只加入一個標籤
                    server_handles, add_errors = opc_items.AddItems(
                        1,  # 只加入 1 個
                        [0, tag],  # [0, 單一標籤]
                        [0, i]  # [0, client_handle]
                    )

                    if add_errors[0] == 0:
                        final_tags.append(tag)
                        final_server_handles.append(server_handles[0])
                        # 每 5 個標籤顯示一次進度
                        if i % 5 == 0:
                            print(f"    ✓ 已加入 {i}/{len(tags)} 個標籤")
                    else:
                        failed_count += 1
                        error_msg = self.opc_client.GetErrorString(add_errors[0])
                        print(f"    ✗ [{i}/{len(tags)}] {tag}: {error_msg}")

                except Exception as e:
                    failed_count += 1
                    print(f"    ✗ [{i}/{len(tags)}] {tag}: 加入時發生錯誤 - {e}")

            if not final_tags:
                print("    ✗ 沒有成功加入的標籤")
                return False

            self.tag_list = final_tags
            self.server_handles = final_server_handles
            self.items_added = True

            print(f"\n    ✓ 成功加入 {len(final_tags)} 個標籤")
            if failed_count > 0:
                print(f"    ⚠ {failed_count} 個標籤加入失敗")

            return True

        except Exception as e:
            print(f"    ✗ 加入標籤過程失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def read_values(self):
        """讀取所有標籤的值"""
        if not self.items_added:
            print("✗ 尚未加入標籤，無法讀取")
            return None

        try:
            # 準備 ServerHandle 列表（索引 0 要放計數）
            handles_with_index = [0] + self.server_handles

            # 執行同步讀取（這裡也可能會卡住！）
            values, errors, qualities, timestamps = self.opc_group.SyncRead(
                OPC_DS_CACHE,  # 先從 cache 讀（較快）
                len(self.server_handles),
                handles_with_index
            )

            # 組織結果
            results = []
            for i, tag in enumerate(self.tag_list):
                value = values[i]
                quality = get_quality_string(qualities[i])
                timestamp = str(timestamps[i])
                error = errors[i]

                results.append({
                    "tag": tag,
                    "value": value,
                    "quality": quality,
                    "timestamp": timestamp,
                    "error": error
                })

            return results

        except Exception as e:
            print(f"✗ 讀取失敗: {e}")
            import traceback
            traceback.print_exc()
            return None

    def disconnect(self):
        """斷開連接"""
        try:
            if self.opc_group and self.opc_client:
                self.opc_client.OPCGroups.Remove(self.opc_group.Name)
            if self.opc_client:
                self.opc_client.Disconnect()
            pythoncom.CoUninitialize()
            print("\n✓ 已斷開連接")
        except:
            pass


def setup_items(base_tags):
    """設定 OPC 資料點列表"""
    tags = []
    for i in range(START, END + 1):
        wtg_number = f"{i:02d}"
        for tag in base_tags:
            item_tag = tag.format(wtg_number)
            tags.append(item_tag)
    return tags


def process_and_display_data(results):
    """處理並顯示讀取的資料"""
    if not results:
        return None

    all_data = []
    print("-" * 80)

    for result in results:
        tag = result["tag"]
        raw_value = result["value"]
        quality = result["quality"]
        timestamp = result["timestamp"]

        # 提取設備代碼
        tag_parts = tag.split('.')
        device_suffix = tag_parts[1][-2:] if len(tag_parts) > 1 else "NA"
        device_code = f"CCIP_group01_dev0{device_suffix}"

        # 提取資料點名稱
        tag_name = re.split(r'[_.]', tag)[-1]

        # 處理特殊情況
        if raw_value is None and "Z72PLC__UI_Loc_WTUR_State_TurSt" in tag:
            value = "99"
        else:
            try:
                value = f"{float(raw_value):.2f}" if raw_value is not None else "NaN"
            except:
                value = str(raw_value) if raw_value is not None else "NaN"

        # 調整時間戳記
        formatted_time = get_adjusted_time(timestamp)

        # 組織資料
        data = {
            "DeviceCode": device_code,
            "Key": tag_name,
            "Value": value,
            "CreateTime": formatted_time,
            "FullTag": tag,
            "Quality": quality
        }
        all_data.append(data)

        # 顯示資料
        quality_info = f" [Q:{quality}]" if quality != "Good" else ""
        print(f"  {device_code:20s} | {tag_name:40s} | {value:>10s} | {formatted_time}{quality_info}")

    print("-" * 80)

    # 顯示摘要
    device_count = len(set(d["DeviceCode"] for d in all_data))
    nan_count = len([d for d in all_data if d["Value"] == "NaN"])
    bad_quality = len([d for d in all_data if d.get("Quality") != "Good"])

    print(
        f"[摘要] 設備數量: {device_count}, 總資料點: {len(all_data)}, "
        f"NaN 值: {nan_count}, 品質異常: {bad_quality}"
    )

    return all_data


def main_loop():
    """主迴圈"""
    print("\n" + "="*100)
    print("OPC 資料持續擷取程式 - 直接 COM 模式")
    print("伺服器: BACHMANN.OPCEnterpriseServer.2")
    print("="*100 + "\n")

    # 初始化客戶端
    client = DirectOpcClient()
    if not client.initialize():
        print("\n✗ 初始化失敗，程式終止")
        return

    # 準備標籤列表
    all_tags = setup_items(BASE_TAGS)
    print(f"\n準備讀取 {len(all_tags)} 個標籤")

    # 加入標籤
    if not client.add_tags(all_tags):
        print("\n✗ 加入標籤失敗，程式終止")
        client.disconnect()
        return

    print("\n" + "="*80)
    print(f"開始持續擷取資料，間隔 {SLEEP_TIME} 秒")
    print("按 Ctrl+C 可停止程式")
    print("="*80)

    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\n\n{'='*100}")
            print(f"[迴圈 #{iteration}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*100}\n")

            # 讀取資料
            results = client.read_values()

            if results:
                all_data = process_and_display_data(results)
                if all_data:
                    print(f"\n✓ 第 {iteration} 次擷取完成")
                else:
                    print(f"\n✗ 第 {iteration} 次資料處理失敗")
            else:
                print(f"\n✗ 第 {iteration} 次讀取失敗")

            print(f"\n等待 {SLEEP_TIME} 秒後進行下一次擷取...")
            time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        print("\n\n[!] 使用者中斷程式")
    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.disconnect()


if __name__ == '__main__':
    main_loop()
