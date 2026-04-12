"""
Wind Farm SCADA Data Fetcher — 學生/研究者用範例腳本

功能：
  1. 即時快照（所有風機當前值）
  2. 單機歷史資料查詢（含 CSV 匯出）
  3. WebSocket 即時串流（持續接收資料）
  4. SCADA tag 清單查詢

使用方式：
  pip install requests websocket-client pandas
  python fetch_scada_data.py

修改 SERVER_URL 為風場伺服器的實際位址。
"""

import requests
import json
import time
import csv
import os
from datetime import datetime, timedelta

# ═══════════════════════════════════════════════════════════
# 設定區：修改這裡的 IP 和 Port
# ═══════════════════════════════════════════════════════════
SERVER_URL = "http://localhost:8100"  # 改成實際伺服器 IP，例如 "http://10.250.6.133:8100"
WS_URL = "ws://localhost:8100/ws/realtime"


def check_connection():
    """確認伺服器連線"""
    try:
        r = requests.get(f"{SERVER_URL}/api/health", timeout=5)
        data = r.json()
        print(f"[OK] 伺服器連線成功：{data['turbineCount']} 台風機, 模式={data['mode']}")
        return True
    except Exception as e:
        print(f"[ERROR] 無法連線到 {SERVER_URL}: {e}")
        return False


# ─────────────────────────────────────────────────────
# 範例 1：取得所有風機即時快照
# ─────────────────────────────────────────────────────
def fetch_realtime_snapshot():
    """取得所有風機的當前 SCADA 數據"""
    print("\n" + "=" * 60)
    print("範例 1：即時快照")
    print("=" * 60)

    r = requests.get(f"{SERVER_URL}/api/turbines")
    turbines = r.json()

    print(f"共 {len(turbines)} 台風機\n")
    print(f"{'ID':<8} {'Status':<12} {'Power(MW)':<12} {'Wind(m/s)':<12} {'RPM':<8} {'TwrMy(kNm)':<12} {'AlarmLv':<8}")
    print("-" * 72)

    for t in turbines:
        print(f"{t['turbineId']:<8} {t['status']:<12} {t['powerOutput']:<12.3f} "
              f"{t['windSpeed']:<12.2f} {t['rotorSpeed']:<8.1f} "
              f"{t.get('twrBsMy', 0):<12.1f} {t.get('vibAlarmOverall', 0):<8}")

    return turbines


# ─────────────────────────────────────────────────────
# 範例 2：取得單機完整 SCADA tags
# ─────────────────────────────────────────────────────
def fetch_single_turbine(turbine_id="WT001"):
    """取得單台風機的完整 74 個 SCADA tags"""
    print("\n" + "=" * 60)
    print(f"範例 2：{turbine_id} 完整 SCADA tags")
    print("=" * 60)

    r = requests.get(f"{SERVER_URL}/api/turbines/{turbine_id}")
    t = r.json()

    scada = t.get("scadaTags", {})
    print(f"共 {len(scada)} 個 SCADA tags\n")

    # 依子系統分組顯示
    subsystems = {}
    for tag_id, value in sorted(scada.items()):
        prefix = tag_id.split("_")[0]
        subsystems.setdefault(prefix, []).append((tag_id, value))

    for subsys, tags in subsystems.items():
        print(f"  [{subsys}]")
        for tag_id, value in tags:
            print(f"    {tag_id:<30} = {value}")
        print()

    return scada


# ─────────────────────────────────────────────────────
# 範例 3：取得 SCADA tag 完整定義（含 OPC/Modbus 映射）
# ─────────────────────────────────────────────────────
def fetch_tag_registry():
    """取得所有 SCADA tag 的完整定義"""
    print("\n" + "=" * 60)
    print("範例 3：SCADA Tag 定義清單")
    print("=" * 60)

    r = requests.get(f"{SERVER_URL}/api/i18n/tags/registry")
    tags = r.json()

    print(f"共 {len(tags)} 個 tags\n")
    print(f"{'Tag ID':<30} {'Unit':<8} {'Type':<8} {'Range':<15} {'Label'}")
    print("-" * 90)
    for tag in tags:
        rng = f"{tag['sim_min']}~{tag['sim_max']}"
        # 用 label_en 避免 Windows cp950 編碼問題
        print(f"{tag['id']:<30} {tag['unit']:<8} {tag['data_type']:<8} {rng:<15} {tag['label_en']}")

    return tags


# ─────────────────────────────────────────────────────
# 範例 4：定時抓取資料並存成 CSV
# ─────────────────────────────────────────────────────
def collect_to_csv(turbine_id="WT001", duration_sec=60, interval_sec=2,
                   output_file="scada_data.csv"):
    """定時抓取指定風機資料，存成 CSV 檔案

    Args:
        turbine_id: 風機 ID (WT001~WT014)
        duration_sec: 總收集時間（秒）
        interval_sec: 取樣間隔（秒），建議 >=2
        output_file: 輸出檔名
    """
    print("\n" + "=" * 60)
    print(f"範例 4：收集 {turbine_id} 資料 → {output_file}")
    print(f"  持續 {duration_sec} 秒，間隔 {interval_sec} 秒")
    print("=" * 60)

    rows = []
    start = time.time()
    count = 0

    while time.time() - start < duration_sec:
        try:
            r = requests.get(f"{SERVER_URL}/api/turbines/{turbine_id}", timeout=5)
            t = r.json()
            scada = t.get("scadaTags", {})

            row = {
                "timestamp": t["timestamp"],
                "status": t["status"],
                "turState": t["turState"],
            }
            row.update(scada)
            rows.append(row)
            count += 1

            elapsed = time.time() - start
            print(f"\r  [{count}] {elapsed:.0f}s — Power={t['powerOutput']:.3f}MW "
                  f"Wind={t['windSpeed']:.1f}m/s RPM={t['rotorSpeed']:.1f}", end="")

        except Exception as e:
            print(f"\n  [WARN] 抓取失敗: {e}")

        time.sleep(interval_sec)

    print(f"\n\n  收集完成：{len(rows)} 筆資料")

    if rows:
        # 寫入 CSV
        fieldnames = list(rows[0].keys())
        with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  已儲存至 {output_file}（{len(fieldnames)} 欄位）")

    return rows


# ─────────────────────────────────────────────────────
# 範例 5：WebSocket 即時串流
# ─────────────────────────────────────────────────────
def stream_realtime(duration_sec=30, turbine_filter="WT001"):
    """透過 WebSocket 接收即時資料串流

    Args:
        duration_sec: 監聽時間（秒）
        turbine_filter: 只顯示指定風機（None = 全部）
    """
    print("\n" + "=" * 60)
    print(f"範例 5：WebSocket 即時串流（{duration_sec}秒）")
    print("=" * 60)

    try:
        import websocket
    except ImportError:
        print("  需要安裝: pip install websocket-client")
        return

    ws = websocket.create_connection(WS_URL, timeout=10)
    print(f"  已連線到 {WS_URL}\n")

    start = time.time()
    count = 0

    try:
        while time.time() - start < duration_sec:
            msg = ws.recv()
            data = json.loads(msg)
            count += 1

            for t in data:
                if turbine_filter and t["turbineId"] != turbine_filter:
                    continue
                scada = t.get("scadaTags", {})
                print(f"  [{count}] {t['turbineId']} "
                      f"Power={t['powerOutput']:.3f}MW "
                      f"Wind={t['windSpeed']:.1f}m/s "
                      f"TwrMy={scada.get('WFAT_TwrBsMy', 0):.0f}kNm "
                      f"Alarm={scada.get('WVIB_AlarmOverall', 0)}")
    except KeyboardInterrupt:
        print("\n  使用者中斷")
    finally:
        ws.close()
        print(f"\n  共接收 {count} 筆廣播")


# ─────────────────────────────────────────────────────
# 範例 6：取得歷史資料（需先有運轉一段時間的資料）
# ─────────────────────────────────────────────────────
def fetch_history(turbine_id="WT001", limit=100):
    """取得風機歷史 SCADA 資料"""
    print("\n" + "=" * 60)
    print(f"範例 6：{turbine_id} 歷史資料（最近 {limit} 筆）")
    print("=" * 60)

    r = requests.get(f"{SERVER_URL}/api/turbines/{turbine_id}/history",
                     params={"limit": limit})
    data = r.json()

    readings = data.get("data", [])
    events = data.get("events", [])
    print(f"  歷史讀數：{len(readings)} 筆")
    print(f"  歷史事件：{len(events)} 筆")

    if readings:
        first = readings[0]
        last = readings[-1]
        print(f"  時間範圍：{first.get('timestamp', '?')} → {last.get('timestamp', '?')}")

    return data


# ─────────────────────────────────────────────────────
# 範例 7：匯出歷史 CSV（伺服器端產生）
# ─────────────────────────────────────────────────────
def export_history_csv(turbine_id="WT001", output_file="history_export.csv"):
    """直接從伺服器匯出歷史 CSV"""
    print("\n" + "=" * 60)
    print(f"範例 7：匯出 {turbine_id} 歷史 CSV")
    print("=" * 60)

    r = requests.get(f"{SERVER_URL}/api/export/history",
                     params={"turbine_id": turbine_id, "format": "csv", "limit": 500},
                     stream=True)

    with open(output_file, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

    size_kb = os.path.getsize(output_file) / 1024
    print(f"  已儲存至 {output_file}（{size_kb:.1f} KB）")


# ─────────────────────────────────────────────────────
# 範例 8：用 pandas 分析（需 pip install pandas）
# ─────────────────────────────────────────────────────
def analyze_with_pandas():
    """用 pandas 即時抓取並分析風場資料"""
    print("\n" + "=" * 60)
    print("範例 8：pandas 即時分析")
    print("=" * 60)

    try:
        import pandas as pd
    except ImportError:
        print("  需要安裝: pip install pandas")
        return

    r = requests.get(f"{SERVER_URL}/api/export/snapshot")
    data = r.json()

    # 展開 scadaTags 成 DataFrame
    rows = []
    for t in data["data"]:
        row = {"turbineId": t["turbineId"], "status": t["status"]}
        row.update(t.get("scadaTags", {}))
        rows.append(row)

    df = pd.DataFrame(rows)
    print(f"\n  DataFrame: {df.shape[0]} 台風機 × {df.shape[1]} 欄位\n")

    # 基本統計
    numeric_cols = ["WTUR_TotPwrAt", "WMET_WSpeedNac", "WROT_RotSpd",
                    "WFAT_TwrBsMy", "WFAT_BldRtMy", "WVIB_BandHfX"]
    avail_cols = [c for c in numeric_cols if c in df.columns]
    if avail_cols:
        print(df[avail_cols].describe().round(2).to_string())

    return df


# ═══════════════════════════════════════════════════════════
# 主程式
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Wind Farm SCADA Data Fetcher")
    print(f"Server: {SERVER_URL}\n")

    if not check_connection():
        print("\n請確認伺服器已啟動，或修改 SERVER_URL 為正確位址。")
        exit(1)

    # 依序執行各範例（可自行註解不需要的）
    fetch_realtime_snapshot()       # 1. 即時快照
    fetch_single_turbine("WT001")   # 2. 單機完整 tags
    fetch_tag_registry()            # 3. Tag 定義清單
    # collect_to_csv("WT001", duration_sec=20, interval_sec=2)  # 4. 定時收集 CSV
    # stream_realtime(duration_sec=10)  # 5. WebSocket 串流
    fetch_history("WT001", limit=10)  # 6. 歷史資料
    # export_history_csv("WT001")     # 7. 匯出歷史 CSV
    analyze_with_pandas()           # 8. pandas 分析
