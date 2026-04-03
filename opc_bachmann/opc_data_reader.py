#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OPC 資料持續擷取程式
基於 openopc2 專案，從 BACHMANN.OPCEnterpriseServer.2 伺服器持續擷取資料並即時顯示。
提供診斷模式，可依序驗證：列出 OPC Server → 連線 → 瀏覽標籤 → 讀取測試。
"""

import argparse
import time
import re
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root / "openopc2-0.1.18"))

from datetime import datetime, timedelta
from typing import List, Optional, Sequence, Tuple
import pytz
from openopc2.da_client import OpcDaClient
from openopc2.config import OpenOpcConfig
from openopc2.utils import get_opc_da_client
from opc_common import import_openopc

# ==================== 配置部分 ====================
# OPC 伺服器設定
OPC_SERVER = "BACHMANN.OPCEnterpriseServer.2"
OPC_GATEWAY_HOST = "localhost"
OPC_CLASS = "Graybox.OPC.DAWrapper"
OPC_MODE = "com"
READ_TIMEOUT_MS = 10000  # 防止 SyncRead 無限等待
DIAG_BROWSE_PATTERN = "Z72.*"
DIAG_BROWSE_LIMIT = 20
DIAG_GROUP_PREVIEW = 5

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

# ==================== 參數解析 ====================


def parse_args():
    parser = argparse.ArgumentParser(
        description="Bachmann OPC 資料擷取與診斷工具"
    )
    parser.add_argument(
        "--diag-only",
        action="store_true",
        help="僅執行診斷步驟（列出伺服器/瀏覽/讀取），不進入持續擷取迴圈。",
    )
    parser.add_argument(
        "--skip-diagnostics",
        action="store_true",
        help="跳過診斷步驟，直接進入持續擷取迴圈。",
    )
    parser.add_argument(
        "--browse-pattern",
        default=DIAG_BROWSE_PATTERN,
        help=f"診斷步驟第 3 階段要瀏覽的 OPC 標籤 pattern（預設：{DIAG_BROWSE_PATTERN}）。",
    )
    parser.add_argument(
        "--browse-limit",
        type=int,
        default=DIAG_BROWSE_LIMIT,
        help="瀏覽步驟最多顯示多少筆資料（0 表示全部顯示）。",
    )
    parser.add_argument(
        "--browse-recursive",
        action="store_true",
        help="在瀏覽標籤時使用遞迴模式（可能會較慢）。",
    )
    parser.add_argument(
        "--sample-tag",
        help="診斷步驟第 4 階段用來測試『單一讀取』的標籤名稱（預設使用第一個 BASE_TAGS）。",
    )
    parser.add_argument(
        "--sample-group-size",
        type=int,
        default=DIAG_GROUP_PREVIEW,
        help="診斷步驟第 4 階段『群組讀取』要測試的標籤數量。",
    )
    parser.add_argument(
        "--debug-opc",
        action="store_true",
        help="啟用 OpcDaClient trace 訊息，協助調試 COM 呼叫。",
    )
    return parser.parse_args()

# ==================== 函式定義 ====================

def add_eight_hours(original_time):
    """將時間增加 8 小時（UTC+8）"""
    return original_time + timedelta(hours=8)


def get_adjusted_time(tag_time_str):
    """
    調整時間戳記，將 UTC 時間轉換為 UTC+8
    """
    try:
        tag_time = datetime.strptime(tag_time_str, '%Y-%m-%d %H:%M:%S.%f%z')
    except (ValueError, TypeError):
        tag_time = datetime.now(pytz.utc)
    adjusted_time = add_eight_hours(tag_time)
    return adjusted_time.strftime('%Y-%m-%d %H:%M:%S')


def opc_config():
    """
    初始化 OPC 配置
    """
    print("[*] 初始化 DCOM...")
    time.sleep(1)
    try:
        config = OpenOpcConfig()
        config.OPC_SERVER = OPC_SERVER
        config.OPC_HOST = OPC_GATEWAY_HOST
        config.OPC_GATEWAY_HOST = OPC_GATEWAY_HOST
        config.OPC_CLASS = OPC_CLASS
        config.OPC_MODE = OPC_MODE
        print("[✓] DCOM 初始化成功！")
        return config
    except Exception as e:
        print(f"[✗] DCOM 初始化失敗: {e}")
        return None


def setup_client(config, *, enable_trace=False):
    """
    設定並連接 OPC 客戶端
    """
    print("[*] 連接 OPC 客戶端...")
    time.sleep(1)
    try:
        client = get_opc_da_client(config)
        if enable_trace and hasattr(client, "set_trace"):
            client.set_trace(lambda msg: print(f"[TRACE] {msg}"))
        if not getattr(client, "connected", False):
            client.connect(config.OPC_SERVER, config.OPC_HOST)
        print(f"[✓] OPC 客戶端連線成功（伺服器: {config.OPC_SERVER}, 主機: {config.OPC_HOST}）")
        time.sleep(1)
        return client
    except Exception as e:
        print(f"[✗] OPC 客戶端連接失敗: {e}")
        return None


def setup_items(base_tags):
    """
    設定 OPC 資料點列表
    """
    tags = []
    time.sleep(1)
    print("[*] 初始化 OPC 資料點...")
    try:
        for i in range(START, END + 1):
            wtg_number = f"{i:02d}"
            for tag in base_tags:
                item_tag = tag.format(wtg_number)
                tags.append(item_tag)
        print(f"[✓] OPC 資料點設定成功！共 {len(tags)} 個資料點")
        return tags
    except Exception as e:
        print(f"[✗] OPC 資料點設定失敗: {e}")
        return None


def _format_value(raw_value):
    """將 OPC 讀值轉成字串避免格式錯誤"""
    if raw_value is None:
        return "NaN"
    try:
        return f"{float(raw_value):.2f}"
    except (TypeError, ValueError):
        return str(raw_value)


def safe_disconnect(client):
    """安全地斷線，避免多次拋錯"""
    if not client:
        return
    try:
        client.disconnect()
        print("[✓] OPC 客戶端已斷開連接")
    except Exception as exc:
        print(f"[✗] 斷線時發生錯誤: {exc}")


def _print_step(title: str):
    line = "-" * 100
    print(f"\n{line}\n{title}\n{line}")


def list_available_servers(opc_host: str) -> List[str]:
    """步驟 1：列出目前主機可見的 OPC Server"""
    _print_step("[步驟 1] 掃描 OPC Server")
    host = opc_host or "localhost"
    servers: List[str] = []

    def _print_servers(found: List[str]):
        if found:
            print(f"[✓] 在 '{host}' 找到 {len(found)} 個 OPC Server：")
            for idx, server in enumerate(found, start=1):
                marker = " (目標)" if server == OPC_SERVER else ""
                print(f"    {idx:02d}. {server}{marker}")
        else:
            print(f"[✗] 在 '{host}' 未找到任何 OPC Server")

    # 嘗試使用 opc_common 的 import_openopc（若環境有安裝 OpenOPC/OpenOPC2 模組可直接使用）
    diag_client = None
    try:
        OpenOPC = import_openopc()
        diag_client = OpenOPC.client()
        try:
            servers = diag_client.servers(host)
        except TypeError:
            servers = diag_client.servers()
        _print_servers(servers)
        return servers
    except SystemExit as exc:
        print(f"[!] OpenOPC 模組未就緒：{exc}. 將改用內建 OpcDaClient 嘗試列出。")
    except Exception as exc:
        print(f"[!] 使用 OpenOPC 列出伺服器失敗：{exc}，改用 OpcDaClient。")
    finally:
        if diag_client:
            try:
                diag_client.close()
            except Exception:
                pass

    # 後援方案：直接建立 OpcDaClient 並呼叫 servers()
    fallback_client = None
    try:
        fallback_config = OpenOpcConfig()
        fallback_config.OPC_CLASS = OPC_CLASS
        fallback_config.OPC_MODE = OPC_MODE
        fallback_config.OPC_HOST = host
        fallback_config.OPC_GATEWAY_HOST = host
        fallback_client = OpcDaClient(fallback_config)
        servers = fallback_client.servers(host)
        _print_servers(servers)
    except Exception as exc:
        print(f"[✗] 無法列出 OPC Server（OpcDaClient）：{exc}")
    finally:
        if fallback_client:
            try:
                fallback_client.close()
            except Exception:
                pass
    return servers


def browse_sample_tags(client: OpcDaClient, pattern: str, limit: int, recursive: bool) -> Optional[List[str]]:
    """步驟 3：瀏覽標籤列表"""
    _print_step("[步驟 3] 瀏覽 OPC 標籤 (list)")
    try:
        tags = client.list(paths=pattern, recursive=recursive, flat=True)
    except TypeError:
        tags = client.list(pattern)
    except Exception as exc:
        print(f"[✗] 瀏覽標籤失敗：{exc}")
        return False

    tags = [t for t in tags if t]
    if not tags:
        print("[✗] pattern 沒有回傳任何標籤，請嘗試調整 pattern 或 recursive 參數。")
        return None

    preview = tags if limit <= 0 else tags[:limit]
    print(f"[✓] 共取得 {len(tags)} 筆標籤，顯示前 {len(preview)} 筆（pattern={pattern}）：")
    for tag in preview:
        print(f"    - {tag}")
    if len(tags) > len(preview):
        print(f"    ...（尚有 {len(tags) - len(preview)} 筆未顯示）")
    return tags


def _preview_tags(label: str, tags: Sequence[str], limit: int = 5) -> None:
    truncated = list(tags[:limit])
    suffix = "" if len(tags) <= limit else f"...（共 {len(tags)} 筆）"
    print(f"    ⋅ {label}：{', '.join(truncated)} {suffix}")


def _read_tags_individually(client: OpcDaClient, tags: Sequence[str]) -> bool:
    print("    → 正在逐一讀取以找出問題標籤...")
    any_success = False
    for tag in tags:
        try:
            result = client.read(
                tag,
                sync=True,
                source="device",
                timeout=READ_TIMEOUT_MS,
                include_error=True,
            )
        except Exception as exc:
            print(f"       [✗] {tag}: 讀取失敗 - {exc}")
            continue

        if len(result) == 4:
            raw_value, quality, timestamp, error_msg = result
        else:
            raw_value, quality, timestamp = result
            error_msg = ""
        value = "99" if (raw_value is None and "WTUR_State_TurSt" in tag) else _format_value(raw_value)
        formatted_time = get_adjusted_time(timestamp if timestamp else None)
        diag = []
        if quality != "Good":
            diag.append(f"Q={quality}")
        if error_msg:
            diag.append(f"Err={error_msg}")
        diag_text = f" ({', '.join(diag)})" if diag else ""
        print(f"       [✓] {tag} -> {value} @ {formatted_time}{diag_text}")
        any_success = True
    return any_success


def _read_and_print(client: OpcDaClient, tags: Sequence[str], label: str) -> bool:
    tags = list(tags)
    if not tags:
        print(f"[✗] {label} 沒有可讀取的標籤列表")
        return False

    _preview_tags(label, tags)

    print(
        f"    → 使用 SyncRead（source=device, timeout={READ_TIMEOUT_MS}ms）",
        flush=True,
    )
    try:
        results = client.read(
            tags,
            sync=False,
            source="device",
            timeout=READ_TIMEOUT_MS,
            include_error=True,
        )
    except Exception as exc:
        print(f"[✗] {label} 讀取失敗：{exc}")
        return _read_tags_individually(client, tags)

    if not results:
        print(f"[✗] {label} 沒有收到任何資料（read 回傳空集合）")
        return _read_tags_individually(client, tags)

    print(f"[✓] {label} 讀取 {len(results)} 筆資料：")
    for entry in results:
        if len(entry) == 5:
            full_tag, raw_value, quality, timestamp, error_msg = entry
        else:
            full_tag, raw_value, quality, timestamp = entry
            error_msg = ""
        value = "99" if (raw_value is None and "WTUR_State_TurSt" in full_tag) else _format_value(raw_value)
        formatted_time = get_adjusted_time(timestamp if timestamp else None)
        diag = []
        if quality != "Good":
            diag.append(f"Q={quality}")
        if error_msg:
            diag.append(f"Err={error_msg}")
        diag_text = f" ({', '.join(diag)})" if diag else ""
        print(f"    - {full_tag} -> {value} @ {formatted_time}{diag_text}")
    return True


def read_sample_tags(client: OpcDaClient, sample_tag: str, group_tags: Sequence[str]) -> bool:
    """步驟 4：使用單一與群組兩種方式讀取，確認流程"""
    _print_step("[步驟 4] 讀取測試 (read)")
    if not sample_tag:
        print("[✗] 未提供 sample tag，無法執行單一讀取")
        return False

    single_ok = _read_and_print(client, [sample_tag], "單一標籤")

    group_ok = True
    if group_tags:
        group_ok = _read_and_print(client, group_tags, f"群組標籤（前 {len(group_tags)} 筆）")
    else:
        print("[!] 未提供群組標籤，略過群組讀取測試。")

    return single_ok and group_ok


def run_diagnostics(config: OpenOpcConfig, all_tags: List[str], args) -> Tuple[bool, Optional[OpcDaClient]]:
    """整合四個步驟的診斷流程"""
    diag_ok = True

    servers = list_available_servers(config.OPC_HOST)
    diag_ok &= bool(servers)

    client = setup_client(config, enable_trace=args.debug_opc)
    if not client:
        return False, None

    available_tags = browse_sample_tags(
        client,
        pattern=args.browse_pattern,
        limit=args.browse_limit,
        recursive=args.browse_recursive,
    )
    diag_ok &= bool(available_tags)

    sample_tag = args.sample_tag or (all_tags[0] if all_tags else "")
    candidate_pool = available_tags or all_tags
    if candidate_pool:
        fallback_tag = candidate_pool[0]
        if sample_tag and sample_tag not in candidate_pool:
            print(f"[!] 指定的 sample tag 不在伺服器清單內：{sample_tag}")
            print(f"    將改用 {fallback_tag} 當作測試標籤，或使用 --sample-tag 重新指定。")
            sample_tag = fallback_tag
        elif not sample_tag:
            sample_tag = fallback_tag

    group_size = args.sample_group_size if args.sample_group_size > 0 else DIAG_GROUP_PREVIEW
    group_source = candidate_pool if candidate_pool else all_tags
    group_tags = (group_source or [])[:group_size]
    read_ok = read_sample_tags(client, sample_tag, group_tags)
    diag_ok &= read_ok

    return diag_ok, client


def read_values(client, all_tags):
    """
    讀取所有 OPC 資料點的值
    """
    all_data = []
    try:
        all_values = client.read(
            all_tags,
            sync=True,
            source="device",
            timeout=READ_TIMEOUT_MS,
            include_error=True,
        )
        dtob = datetime.fromtimestamp(time.time())
        fmt_date = dtob.strftime('%Y-%m-%d %H:%M:%S')
        print(f"\n[✓] 成功讀取 {len(all_values)} 個資料點 [{fmt_date}]")
        print("-" * 100)
        
        for tag in all_values:
            if len(tag) == 5:
                full_tag, raw_value, quality, timestamp, error_msg = tag
            else:
                full_tag, raw_value, quality, timestamp = tag
                error_msg = ""

            # 提取設備代碼（例如：Z72.H13 -> H13）
            tag_parts = full_tag.split('.')
            device_suffix = tag_parts[1][-2:] if len(tag_parts) > 1 else "NA"
            device_code = f"CCIP_group01_dev0{device_suffix}"
            
            # 提取資料點名稱（最後一個 . 或 _ 之後的部分）
            tag_name = re.split(r'[_.]', full_tag)[-1]
            
            # 處理特殊情況：如果值為 None 且是渦輪狀態標籤，設為 "99"
            if raw_value is None and "Z72PLC__UI_Loc_WTUR_State_TurSt" in full_tag:
                value = "99"
            else:
                value = _format_value(raw_value)
            
            # 調整時間戳記
            formatted_time = get_adjusted_time(timestamp if timestamp else None)
            
            # 組織資料
            data = {
                "DeviceCode": device_code,
                "Key": tag_name,
                "Value": value,
                "CreateTime": formatted_time,
                "FullTag": full_tag,  # 完整的 OPC 標籤名稱
                "Quality": quality,
                "Error": error_msg,
            }
            all_data.append(data)
            
            # 即時顯示資料
            diagnostic = ""
            if quality != "Good":
                diagnostic += f" Q:{quality}"
            if error_msg:
                diagnostic += f" Err:{error_msg}"
            print(f"  {device_code:20s} | {tag_name:40s} | {value:>10s} | {formatted_time}{diagnostic}")
        
        print("-" * 100)
        return all_data
    except Exception as e:
        print(f"[✗] 讀取 OPC 資料點失敗: {e}")
        return None


def display_summary(all_data):
    """
    顯示資料摘要統計
    """
    if not all_data:
        return
    
    device_count = len(set(d["DeviceCode"] for d in all_data))
    nan_count = len([d for d in all_data if d["Value"] == "NaN"])
    bad_quality = len([d for d in all_data if d.get("Quality") != "Good"])
    error_tags = len([d for d in all_data if d.get("Error")])
    
    print(
        f"\n[摘要] 設備數量: {device_count}, 總資料點: {len(all_data)}, "
        f"NaN 值: {nan_count}, 品質異常: {bad_quality}, OPC 錯誤: {error_tags}"
    )


def main_loop(args):
    """
    主迴圈：可選診斷 + 持續擷取 OPC 資料
    """
    print("\n" + "=" * 100)
    print("OPC 資料持續擷取程式")
    print("伺服器: BACHMANN.OPCEnterpriseServer.2")
    print("=" * 100 + "\n")

    config = opc_config()
    if not config:
        print("[✗] 無法初始化配置，程式終止")
        return

    all_tags = setup_items(BASE_TAGS)
    if not all_tags:
        print("[✗] 無法設定資料點，程式終止")
        return

    client = None
    try:
        if not args.skip_diagnostics:
            diag_ok, client = run_diagnostics(config, all_tags, args)
            if not diag_ok:
                print("[✗] 診斷未通過，請先排除問題後再執行擷取。")
                return
            if args.diag_only:
                print("[*] 診斷步驟已完成（diag-only），程式結束。")
                return

        if client is None:
            client = setup_client(config, enable_trace=args.debug_opc)
            if not client:
                print("[✗] 無法連接客戶端，程式終止")
                return

        print(f"\n[*] 開始持續擷取資料，間隔 {SLEEP_TIME} 秒\n")

        iteration = 0
        while True:
            iteration += 1
            print(f"\n{'='*100}")
            print(f"[迴圈 #{iteration}] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*100}")

            all_data = read_values(client, all_tags)

            if all_data:
                display_summary(all_data)

            print(f"\n[*] 等待 {SLEEP_TIME} 秒後進行下一次擷取...\n")
            time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        print("\n\n[!] 使用者中斷程式")
    except Exception as e:
        print(f"\n[✗] 發生錯誤: {e}")
    finally:
        safe_disconnect(client)


def main():
    args = parse_args()
    main_loop(args)


if __name__ == '__main__':
    main()

