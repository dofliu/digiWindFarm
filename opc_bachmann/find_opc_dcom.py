#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
尋找 OPC 相關的 DCOM 物件
"""

import sys
import winreg
from pathlib import Path

repo_root = Path(__file__).resolve().parent
sys.path.insert(0, str(repo_root / "openopc2-0.1.18"))

import pythoncom
import win32com.client

OPC_CLASS = "Graybox.OPC.DAWrapper"
OPC_SERVER = "BACHMANN.OPCEnterpriseServer.2"

print("\n" + "="*80)
print("尋找 OPC 相關的 DCOM 物件")
print("="*80)

# 方法 1: 從 ProgID 找 CLSID
print("\n[方法 1] 從 ProgID 查詢 CLSID")
print(f"ProgID: {OPC_CLASS}")

try:
    pythoncom.CoInitialize()

    # 取得 CLSID
    clsid = pythoncom.CLSIDFromProgID(OPC_CLASS)
    clsid_str = str(clsid)
    print(f"✓ 找到 CLSID: {clsid_str}")

    # 查詢註冊表中的名稱
    print("\n[查詢註冊表資訊]")
    try:
        key_path = f"CLSID\\{clsid_str}"
        key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key_path)

        # 讀取預設值（通常是物件的描述名稱）
        default_value, _ = winreg.QueryValueEx(key, "")
        print(f"  預設名稱: {default_value}")

        # 讀取 AppID（如果有）
        try:
            appid, _ = winreg.QueryValueEx(key, "AppID")
            print(f"  AppID: {appid}")

            # 從 AppID 找 DCOM 設定名稱
            appid_key_path = f"AppID\\{appid}"
            appid_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, appid_key_path)
            appid_name, _ = winreg.QueryValueEx(appid_key, "")
            print(f"  AppID 名稱: {appid_name}")
            print(f"\n✓ 在 dcomcnfg 中應該找這個名稱: {appid_name}")
            winreg.CloseKey(appid_key)
        except FileNotFoundError:
            print("  [!] 沒有 AppID（可能不是 DCOM 物件）")

        winreg.CloseKey(key)

    except Exception as e:
        print(f"  [!] 查詢註冊表失敗: {e}")

except Exception as e:
    print(f"✗ 無法取得 CLSID: {e}")

# 方法 2: 搜尋所有 OPC 相關的 DCOM 物件
print("\n" + "="*80)
print("[方法 2] 搜尋所有 OPC 相關的 DCOM 物件")
print("="*80)

opc_objects = []

try:
    # 搜尋 CLSID
    print("\n搜尋 HKEY_CLASSES_ROOT\\CLSID...")
    clsid_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "CLSID")

    i = 0
    while True:
        try:
            clsid_name = winreg.EnumKey(clsid_key, i)
            i += 1

            # 開啟每個 CLSID
            try:
                key = winreg.OpenKey(clsid_key, clsid_name)

                # 讀取預設名稱
                try:
                    default_name, _ = winreg.QueryValueEx(key, "")

                    # 檢查是否包含 OPC 或 Graybox 或 Bachmann
                    if any(keyword.lower() in default_name.lower()
                           for keyword in ["opc", "graybox", "bachmann", "wrapper"]):

                        # 檢查是否有 AppID
                        try:
                            appid, _ = winreg.QueryValueEx(key, "AppID")
                            has_appid = True
                        except:
                            appid = None
                            has_appid = False

                        opc_objects.append({
                            "clsid": clsid_name,
                            "name": default_name,
                            "appid": appid,
                            "is_dcom": has_appid
                        })
                except:
                    pass

                winreg.CloseKey(key)
            except:
                pass

        except OSError:
            break

    winreg.CloseKey(clsid_key)

    if opc_objects:
        print(f"\n找到 {len(opc_objects)} 個 OPC 相關物件：")
        print("-" * 80)
        for idx, obj in enumerate(opc_objects, 1):
            print(f"\n{idx}. {obj['name']}")
            print(f"   CLSID: {obj['clsid']}")
            if obj['is_dcom']:
                print(f"   AppID: {obj['appid']}")
                print(f"   ✓ 這是 DCOM 物件（應該出現在 dcomcnfg 中）")
            else:
                print(f"   ✗ 不是 DCOM 物件（不會出現在 dcomcnfg 中）")
    else:
        print("\n未找到任何 OPC 相關物件")

except Exception as e:
    print(f"搜尋失敗: {e}")

# 方法 3: 搜尋 AppID（直接搜尋 DCOM 物件）
print("\n" + "="*80)
print("[方法 3] 直接搜尋 DCOM 物件（AppID）")
print("="*80)

dcom_objects = []

try:
    print("\n搜尋 HKEY_CLASSES_ROOT\\AppID...")
    appid_key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, "AppID")

    i = 0
    while True:
        try:
            appid_name = winreg.EnumKey(appid_key, i)
            i += 1

            # 跳過 GUID 格式的子鍵，只看有名稱的
            if not appid_name.startswith("{"):
                try:
                    key = winreg.OpenKey(appid_key, appid_name)

                    # 讀取 AppID GUID
                    try:
                        appid_guid, _ = winreg.QueryValueEx(key, "AppID")

                        # 檢查名稱
                        if any(keyword.lower() in appid_name.lower()
                               for keyword in ["opc", "graybox", "bachmann", "wrapper"]):
                            dcom_objects.append({
                                "name": appid_name,
                                "appid": appid_guid
                            })
                    except:
                        pass

                    winreg.CloseKey(key)
                except:
                    pass
        except OSError:
            break

    winreg.CloseKey(appid_key)

    if dcom_objects:
        print(f"\n找到 {len(dcom_objects)} 個 OPC 相關 DCOM 物件：")
        print("-" * 80)
        for idx, obj in enumerate(dcom_objects, 1):
            print(f"\n{idx}. {obj['name']}")
            print(f"   AppID: {obj['appid']}")
            print(f"   ✓ 這個名稱應該出現在 dcomcnfg → DCOM Config 中")
    else:
        print("\n未找到任何 OPC 相關 DCOM 物件")
        print("\n這可能表示：")
        print("  1. Graybox OPC Wrapper 沒有註冊為 DCOM 物件")
        print("  2. 使用的是 in-process server（DLL）而非 out-of-process（EXE）")
        print("  3. 權限問題不在 DCOM 層級，而在其他地方")

except Exception as e:
    print(f"搜尋失敗: {e}")

# 方法 4: 測試實際建立物件
print("\n" + "="*80)
print("[方法 4] 測試建立 OPC 物件")
print("="*80)

try:
    print(f"\n嘗試建立 {OPC_CLASS}...")
    opc = win32com.client.Dispatch(OPC_CLASS)
    print("✓ 成功建立物件")

    # 取得物件資訊
    print("\n物件資訊：")
    try:
        print(f"  Type: {type(opc)}")
        print(f"  CLSID: {opc._oleobj_.GetTypeInfo().GetTypeAttr().iid}")
    except:
        pass

    # 測試連接
    print(f"\n嘗試連接到 {OPC_SERVER}...")
    try:
        opc.Connect(OPC_SERVER, "localhost")
        print("✓ 連接成功")
        print(f"  ServerName: {opc.ServerName}")
        opc.Disconnect()
    except Exception as e:
        print(f"✗ 連接失敗: {e}")

except Exception as e:
    print(f"✗ 無法建立物件: {e}")

# 總結建議
print("\n" + "="*80)
print("總結與建議")
print("="*80)

print("""
根據上述檢查結果：

1. 如果找到了 AppID 名稱：
   → 在 dcomcnfg 中搜尋該名稱
   → 按照「修正AddItems卡住問題.md」設定權限

2. 如果沒有找到任何 DCOM 物件：
   → Graybox.OPC.DAWrapper 可能是 in-process server (DLL)
   → 不需要設定 DCOM 權限
   → 問題可能在於：
      a) DLL 檔案權限
      b) 註冊表權限
      c) 防毒軟體阻擋

3. 可以嘗試的解決方案：
   a) 以系統管理員身分執行 Python
   b) 檢查 Windows 事件檢視器中的錯誤
   c) 暫時停用防毒軟體測試
   d) 檢查 gbda_aut.dll 的檔案權限

4. 下一步診斷：
   → 執行 diagnose_additems.py 以系統管理員身分
   → 如果成功，問題就是權限
   → 如果還是失敗，問題在其他地方
""")

try:
    pythoncom.CoUninitialize()
except:
    pass

print("\n" + "="*80)
