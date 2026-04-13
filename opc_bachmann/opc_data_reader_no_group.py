#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPC 資料持續擷取程式 - 不使用群組模式
完全不使用 OPCGroup 和 AddItems，直接讀取單一標籤
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


class SimpleOpcClient:
    """簡化的 OPC 客戶端 - 不使用群組，直接讀取屬性"""

    def __init__(self):
        self.opc_client = None
        self.connected = False

    def initialize(self):
        """初始化 COM 和 OPC 客戶端"""
        print("="*80)
        print("初始化 OPC 客戶端（無群組模式）")
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
            print("    ✓ 連接成功")
            print(f"    ServerName: {self.opc_client.ServerName}")
            print(f"    ServerState: {self.opc_client.ServerState}")

            print("\n✓ 初始化完成（跳過群組建立）")
            return True

        except Exception as e:
            print(f"    ✗ 初始化失敗: {e}")
            import traceback
            traceback.print_exc()
            return False

    def read_single_tag_properties(self, tag):
        """使用 GetItemProperties 讀取單一標籤的屬性（包含值）"""
        try:
            # 屬性 ID：
            # 1 = Item Canonical DataType
            # 2 = Item Value
            # 3 = Item Quality
            # 4 = Item Timestamp
            property_ids = [2, 3, 4]  # Value, Quality, Timestamp

            values, errors = self.opc_client.GetItemProperties(
                tag,
                len(property_ids),
                [0] + property_ids
            )

            if errors[0] != 0 or errors[1] != 0 or errors[2] != 0:
                return None

            value = values[0]      # Item Value
            quality = values[1]    # Item Quality
            timestamp = values[2]  # Item Timestamp

            return {
                "tag": tag,
                "value": value,
                "quality": get_quality_string(quality) if isinstance(quality, int) else "Unknown",
                "timestamp": str(timestamp),
                "error": 0
            }

        except Exception:
            return None

    def read_tags(self, tags):
        """逐一讀取標籤的屬性"""
        results = []
        failed_count = 0

        print(f"\n正在讀取 {len(tags)} 個標籤...")

        for i, tag in enumerate(tags, 1):
            try:
                result = self.read_single_tag_properties(tag)

                if result:
                    results.append(result)
                else:
                    failed_count += 1

                # 每 10 個標籤顯示一次進度
                if i % 10 == 0:
                    print(f"  進度: {i}/{len(tags)} ({len(results)} 成功, {failed_count} 失敗)")

            except Exception as e:
                failed_count += 1
                if i <= 5:  # 只顯示前 5 個錯誤
                    print(f"  ✗ {tag}: {e}")

        print(f"\n讀取完成: {len(results)} 成功, {failed_count} 失敗")
        return results

    def disconnect(self):
        """斷開連接"""
        try:
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
    print("\n" + "-" * 80)

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
    print("OPC 資料持續擷取程式 - 無群組模式")
    print("伺服器: BACHMANN.OPCEnterpriseServer.2")
    print("方法: 使用 GetItemProperties 直接讀取，不使用 OPCGroup 和 AddItems")
    print("="*100 + "\n")

    # 初始化客戶端
    client = SimpleOpcClient()
    if not client.initialize():
        print("\n✗ 初始化失敗，程式終止")
        return

    # 準備標籤列表
    all_tags = setup_items(BASE_TAGS)
    print(f"\n準備讀取 {len(all_tags)} 個標籤")

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
            print(f"{'='*100}")

            # 讀取資料
            start_time = time.time()
            results = client.read_tags(all_tags)
            elapsed = time.time() - start_time

            if results:
                all_data = process_and_display_data(results)
                if all_data:
                    print(f"\n✓ 第 {iteration} 次擷取完成（耗時 {elapsed:.2f} 秒）")
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
