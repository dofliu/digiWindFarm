#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPC 資料持續擷取程式 - 簡化版
基於可運作的 CKVOBOPCGetandPass 程式，使用簡化的 read() 參數
"""

import time
import re
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root / "openopc2-0.1.18"))

from datetime import datetime, timedelta
import pytz
from openopc2.config import OpenOpcConfig
from openopc2.utils import get_opc_da_client

# ==================== 配置部分 ====================
OPC_SERVER = "BACHMANN.OPCEnterpriseServer.2"
OPC_GATEWAY_HOST = "localhost"
OPC_CLASS = "Graybox.OPC.DAWrapper"
OPC_MODE = "com"

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


def get_adjusted_time(tag_time_str):
    """調整時間戳記，將 UTC 時間轉換為 UTC+8"""
    try:
        tag_time = datetime.strptime(tag_time_str, '%Y-%m-%d %H:%M:%S.%f%z')
    except (ValueError, TypeError):
        tag_time = datetime.now(pytz.utc)
    adjusted_time = add_eight_hours(tag_time)
    return adjusted_time.strftime('%Y-%m-%d %H:%M:%S')


def opc_config():
    """初始化 OPC 配置"""
    print("DCOM Initialing...")
    time.sleep(1)
    try:
        config = OpenOpcConfig()
        config.OPC_SERVER = OPC_SERVER
        config.OPC_GATEWAY_HOST = OPC_GATEWAY_HOST
        config.OPC_CLASS = OPC_CLASS
        config.OPC_MODE = OPC_MODE
        print("DCOM Initialize OK!")
        return config
    except Exception as e:
        print(f"DCOM Failed!: {e}")
        return None


def setup_client(config):
    """設定並連接 OPC 客戶端"""
    print("OPC Client Connecting...")
    time.sleep(1)
    try:
        client = get_opc_da_client(config)
        client.connect(config.OPC_SERVER, config.OPC_GATEWAY_HOST)
        print("OPC Client Connect OK!")
        time.sleep(1)
        return client
    except Exception as e:
        print(f"OPC Client Connect Failed!{e}")
        import traceback
        traceback.print_exc()
        return None


def setup_items(base_tags):
    """設定 OPC 資料點列表"""
    tags = []
    time.sleep(1)
    print("OPC Item Initialing...")
    try:
        for i in range(START, END + 1):
            wtg_number = f"{i:02d}"
            for tag in base_tags:
                item_tag = tag.format(wtg_number)
                tags.append(item_tag)
        print(f"OPC Item Setup OK! Total {len(tags)} tags")
        return tags
    except Exception as e:
        print(f"OPC Item Append Failed! {e}")
        return None


def read_values(client, all_tags):
    """
    讀取所有 OPC 資料點的值
    使用簡化的參數（與可運作的版本相同）
    """
    all_data = []
    try:
        print("\n" + "="*80)
        print("開始讀取 OPC 資料...")
        print("="*80)

        # 關鍵：只使用 sync=True，不加其他參數
        # 這樣會使用預設的 source="hybrid", timeout=5000, include_error=False
        print(f"正在讀取 {len(all_tags)} 個標籤...")
        all_values = client.read(all_tags, sync=True)

        dtob = datetime.fromtimestamp(time.time())
        fmt_date = dtob.strftime('%Y-%m-%d %H:%M:%S')
        print(f"✓ OPC Tag {len(all_values)} Values Read OK! [{fmt_date}]")
        print("-" * 80)

        for tag in all_values:
            # 提取設備代碼（例如：Z72.H13 -> H13）
            tag_parts = tag[0].split('.')
            device_suffix = tag_parts[1][-2:] if len(tag_parts) > 1 else "NA"
            device_code = f"CCIP_group01_dev0{device_suffix}"

            # 提取資料點名稱
            tag_name = re.split(r'[_.]', tag[0])[-1]

            # 處理特殊情況：如果值為 None 且是渦輪狀態標籤，設為 "99"
            if tag[1] is None and "Z72PLC__UI_Loc_WTUR_State_TurSt" in tag[0]:
                value = "99"
            else:
                value = f"{tag[1]:.2f}" if tag[1] is not None else "NaN"

            # 調整時間戳記
            formatted_time = get_adjusted_time(tag[3] if tag[3] else None)

            # 組織資料
            data = {
                "DeviceCode": device_code,
                "Key": tag_name,
                "Value": value,
                "CreateTime": formatted_time,
                "FullTag": tag[0],
                "Quality": tag[2] if len(tag) > 2 else "Unknown"
            }
            all_data.append(data)

            # 即時顯示資料
            quality_info = f" [Q:{tag[2]}]" if len(tag) > 2 and tag[2] != "Good" else ""
            print(f"  {device_code:20s} | {tag_name:40s} | {value:>10s} | {formatted_time}{quality_info}")

        print("-" * 80)
        return all_data

    except Exception as e:
        print(f"✗ OPC Tag Values Read Error: {e}")
        import traceback
        traceback.print_exc()
        return None


def display_summary(all_data):
    """顯示資料摘要統計"""
    if not all_data:
        return

    device_count = len(set(d["DeviceCode"] for d in all_data))
    nan_count = len([d for d in all_data if d["Value"] == "NaN"])
    bad_quality = len([d for d in all_data if d.get("Quality") != "Good"])

    print(
        f"\n[摘要] 設備數量: {device_count}, 總資料點: {len(all_data)}, "
        f"NaN 值: {nan_count}, 品質異常: {bad_quality}"
    )


def main_loop():
    """主迴圈：持續擷取 OPC 資料"""
    print("\n" + "="*100)
    print("OPC 資料持續擷取程式 - 簡化版")
    print("伺服器: BACHMANN.OPCEnterpriseServer.2")
    print("="*100 + "\n")

    config = opc_config()
    if not config:
        print("✗ 無法初始化配置，程式終止")
        return

    client = setup_client(config)
    if not client:
        print("✗ 無法連接客戶端，程式終止")
        return

    all_tags = setup_items(BASE_TAGS)
    if not all_tags:
        print("✗ 無法設定資料點，程式終止")
        return

    print(f"\n開始持續擷取資料，間隔 {SLEEP_TIME} 秒")
    print("按 Ctrl+C 可停止程式\n")

    iteration = 0
    try:
        while True:
            iteration += 1
            print(f"\n{'='*100}")
            print(f"[迴圈 #{iteration}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*100}")

            all_data = read_values(client, all_tags)

            if all_data:
                display_summary(all_data)
                print(f"\n✓ 第 {iteration} 次擷取完成")
            else:
                print(f"\n✗ 第 {iteration} 次擷取失敗")

            print(f"\n等待 {SLEEP_TIME} 秒後進行下一次擷取...")
            time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        print("\n\n[!] 使用者中斷程式")
    except Exception as e:
        print(f"\n✗ 發生錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            client.disconnect()
            print("✓ OPC 客戶端已斷開連接")
        except:
            pass


if __name__ == '__main__':
    main_loop()
