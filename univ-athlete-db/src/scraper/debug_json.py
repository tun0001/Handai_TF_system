#!/usr/bin/env python3
"""
JSONデータデバッグ用スクリプト
"""

import requests
import json

def debug_json_data():
    url = "https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    }
    
    try:
        print("🔍 JSONデータ取得開始")
        print(f"URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            print("\n📋 JSONデータの構造:")
            if isinstance(data, dict):
                print(f"辞書形式 - キー数: {len(data)}")
                print(f"キー一覧: {list(data.keys())}")
                
                print("\n📄 JSON全体データ:")
                formatted_json = json.dumps(data, ensure_ascii=False, indent=2)
                print(formatted_json)
                
                # ファイルにも保存
                with open('debug_json_output.txt', 'w', encoding='utf-8') as f:
                    f.write("JSONデータ全体:\n")
                    f.write(formatted_json)
                
                print(f"\n✅ JSONデータをdebug_json_output.txtに保存しました")
                
            elif isinstance(data, list):
                print(f"リスト形式 - 要素数: {len(data)}")
                print(json.dumps(data, ensure_ascii=False, indent=2))
            
            return data
        else:
            print(f"❌ JSON取得失敗: HTTP {response.status_code}")
            print(f"レスポンステキスト: {response.text[:500]}...")
            return None
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

if __name__ == "__main__":
    debug_json_data()
