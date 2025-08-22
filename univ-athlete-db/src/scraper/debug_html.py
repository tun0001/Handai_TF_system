#!/usr/bin/env python3
"""
HTMLデータデバッグ用スクリプト
"""

import requests
from bs4 import BeautifulSoup

def debug_html_data():
    url = "https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    }
    
    try:
        print("🔍 HTMLデータ取得開始")
        print(f"URL: {url}")
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"ステータスコード: {response.status_code}")
        print(f"エンコーディング: {response.encoding}")
        
        if response.status_code == 200:
            # 文字エンコーディングを調整
            if response.encoding in ['ISO-8859-1', 'ascii']:
                response.encoding = 'utf-8'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            print("\n📄 HTMLデータ解析:")
            
            # titleタグ
            title = soup.find('title')
            if title:
                print(f"タイトル: {title.text.strip()}")
            
            # h1タグ
            h1_tags = soup.find_all('h1')
            print(f"\nH1タグ ({len(h1_tags)}個):")
            for i, h1 in enumerate(h1_tags):
                print(f"  {i+1}: {h1.text.strip()}")
            
            # h2タグ
            h2_tags = soup.find_all('h2')
            print(f"\nH2タグ ({len(h2_tags)}個):")
            for i, h2 in enumerate(h2_tags):
                print(f"  {i+1}: {h2.text.strip()}")
            
            # h3タグ
            h3_tags = soup.find_all('h3')
            print(f"\nH3タグ ({len(h3_tags)}個):")
            for i, h3 in enumerate(h3_tags):
                print(f"  {i+1}: {h3.text.strip()}")
                
            # metaタグ
            meta_tags = soup.find_all('meta')
            print(f"\nメタタグ:")
            for meta in meta_tags:
                name = meta.get('name', '')
                content = meta.get('content', '')
                if name and content:
                    print(f"  {name}: {content}")
            
            # bodyの最初の部分
            body = soup.find('body')
            if body:
                body_text = body.get_text()[:1000]
                print(f"\nBODY先頭部分:\n{body_text}")
            
            # HTMLをファイルに保存
            with open('debug_html_output.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            print(f"\n✅ HTMLデータをdebug_html_output.htmlに保存しました")
            
            return soup
        else:
            print(f"❌ HTML取得失敗: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

if __name__ == "__main__":
    debug_html_data()
