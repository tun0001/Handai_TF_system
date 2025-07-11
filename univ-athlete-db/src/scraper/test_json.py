#!/usr/bin/env python3
"""
テスト用の詳細なスクリプト
"""

import requests
import json

url = "https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.json"

try:
    print(f"Requesting: {url}")
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Keys: {list(data.keys())}")
        
        # NitteiListの詳細を確認
        if 'NitteiList' in data:
            print(f"\n=== NitteiList ===")
            for i, nittei in enumerate(data['NitteiList']):
                print(f"Nittei {i}: {nittei}")
        
        # TimeTableListの詳細を確認
        if 'TimeTableList' in data:
            print(f"\n=== TimeTableList ===")
            print(f"TimeTableList: {data['TimeTableList']}")
        
        # KyogiListの最初の要素を確認
        if 'KyogiList' in data and len(data['KyogiList']) > 0:
            print(f"\n=== KyogiList[0] ===")
            first_kyogi = data['KyogiList'][0]
            print(f"First Kyogi keys: {list(first_kyogi.keys()) if isinstance(first_kyogi, dict) else first_kyogi}")
    
except Exception as e:
    print(f"Error: {e}")
