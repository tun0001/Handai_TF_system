#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
所属選手情報スクレイピングスクリプト
SyozokuPlayer.htmlから選手情報を取得
"""

from scrape_js import JavaScriptScraper
import pandas as pd
import json
import time
import re
from typing import List, Dict, Optional

class SyozokuPlayerScraper(JavaScriptScraper):
    def __init__(self, headless: bool = True, wait_timeout: int = 15):
        """
        所属選手情報専用のスクレイパー
        
        Args:
            headless: ヘッドレスモードで実行するか
            wait_timeout: 要素の読み込み待機時間（秒）
        """
        super().__init__(headless, wait_timeout)
        
    def scrape_syozoku_player(self, url: str) -> List[Dict]:
        """
        所属選手ページからデータを取得
        
        Args:
            url: スクレイピング対象のURL
            
        Returns:
            取得したデータのリスト
        """
        print(f"🏃 所属選手情報の取得を開始: {url}")
        
        if self.driver:
            return self._scrape_syozoku_with_selenium(url)
        else:
            return self._scrape_syozoku_with_requests(url)
    
    def _scrape_syozoku_with_selenium(self, url: str) -> List[Dict]:
        """Seleniumを使用して所属選手情報をスクレイピング"""
        try:
            print(f"🌐 Seleniumで所属選手ページにアクセス中: {url}")
            
            self.driver.get(url)
            self._wait_for_page_load()
            time.sleep(5)  # ページ読み込み完了を待機
            
            # ページのJavaScriptが実行されるまで待機
            print("⏳ JavaScriptの実行完了を待機中...")
            
            # 選手データの取得を試行
            data = []
            
            # 1. ネットワークリクエストからのデータ取得
            print("🔍 ネットワークリクエストからデータを取得中...")
            network_data = self._capture_network_requests_selenium(url)
            if network_data:
                data.extend(network_data)
                print(f"✅ ネットワークから {len(network_data)}件のデータを取得")
            
            # 2. DOM要素からの選手情報取得
            print("🔍 DOM要素から選手情報を取得中...")
            dom_data = self._extract_player_data_from_dom()
            if dom_data:
                data.extend(dom_data)
                print(f"✅ DOMから {len(dom_data)}件のデータを取得")
            
            # 3. JavaScriptファイルからのデータ取得
            print("🔍 JavaScriptファイルからデータを取得中...")
            js_data = self._extract_player_data_from_js(url)
            if js_data:
                data.extend(js_data)
                print(f"✅ JavaScriptから {len(js_data)}件のデータを取得")
            
            return data
            
        except Exception as e:
            print(f"❌ Selenium所属選手スクレイピングエラー: {e}")
            print("🔄 フォールバックモードに切り替えます...")
            return self._scrape_syozoku_with_requests(url)
    
    def _scrape_syozoku_with_requests(self, url: str) -> List[Dict]:
        """requests + BeautifulSoupを使用して所属選手情報をスクレイピング"""
        try:
            print(f"🔄 requestsで所属選手ページを取得中: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            import requests
            from bs4 import BeautifulSoup
            
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            print(f"📄 レスポンス取得成功 (Status: {response.status_code})")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = []
            
            # 1. HTMLからJavaScriptファイルを発見
            print("\n🔍 HTMLからJavaScriptファイルを検索...")
            base_url = url.replace('/SyozokuPlayer.html#!#syozoku_19', '')
            js_files = self._find_javascript_files(soup, base_url)
            
            # 2. 見つかったJavaScriptファイルを解析
            for js_url in js_files:
                print(f"\n🎯 JavaScript解析: {js_url}")
                try:
                    js_response = session.get(js_url, headers=headers, timeout=10)
                    print(f"📡 レスポンス: {js_response.status_code}")
                    
                    if js_response.status_code == 200:
                        js_content = js_response.text
                        
                        # 選手データ関連のJavaScriptを探す
                        if any(keyword in js_content.lower() for keyword in ['player', 'syozoku', '選手', 'athlete']):
                            print(f"\n📄 選手関連JavaScript発見: {js_url}")
                            print("=" * 50)
                            print(js_content[:1000])  # 最初の1000文字を表示
                            print("=" * 50)
                            
                            # JavaScriptからデータを抽出
                            js_data = self._extract_player_data_from_javascript(js_content, base_url, session, headers)
                            data.extend(js_data)
                        
                except Exception as e:
                    print(f"❌ JavaScript取得エラー ({js_url}): {e}")
            
            # 3. 特定のJavaScriptファイルを直接取得（所属選手用）
            print("\n🎯 所属選手専用JavaScriptファイルを検索...")
            player_js_urls = [
                f"{base_url}/SyozokuPlayer.js",
                f"{base_url}/js/SyozokuPlayer.js", 
                f"{base_url}/scripts/SyozokuPlayer.js",
                f"{base_url}/PlayerData.js",
                f"{base_url}/js/PlayerData.js"
            ]
            
            for js_url in player_js_urls:
                try:
                    print(f"🔍 {js_url} をチェック中...")
                    js_response = session.get(js_url, headers=headers, timeout=10)
                    
                    if js_response.status_code == 200:
                        print(f"✅ 発見: {js_url}")
                        js_content = js_response.text
                        
                        print(f"\n📄 {js_url} の内容:")
                        print("=" * 80)
                        print(js_content[:2000])  # 最初の2000文字を表示
                        print("=" * 80)
                        
                        # JavaScriptからデータを抽出
                        js_data = self._extract_player_data_from_javascript(js_content, base_url, session, headers)
                        data.extend(js_data)
                        
                except requests.exceptions.RequestException as e:
                    print(f"❌ {js_url} 取得失敗: {e}")
            
            # 4. 静的HTMLからのデータ抽出
            if not data:
                print("📄 静的HTMLからの選手データ抽出を試行...")
                data = self._extract_static_player_data(soup)
            
            print(f"✅ 合計 {len(data)}件の所属選手データを取得")
            return data
        
        except Exception as e:
            print(f"❌ requests所属選手スクレイピングエラー: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_player_data_from_dom(self) -> List[Dict]:
        """DOM要素から選手データを抽出"""
        if not self.driver:
            return []
            
        data = []
        
        try:
            # 選手テーブルを探す
            player_tables = self.driver.find_elements("css selector", "table")
            
            if player_tables:
                print(f"📊 {len(player_tables)}個のテーブルを発見")
                
                for i, table in enumerate(player_tables):
                    print(f"🔍 テーブル {i+1} を解析中...")
                    
                    # テーブルのHTMLを確認
                    table_html = table.get_attribute('outerHTML')
                    print(f"📄 テーブル {i+1} HTML (一部): {table_html[:500]}")
                    
                    # 選手データらしいテーブルかチェック
                    if any(keyword in table_html.lower() for keyword in ['選手', 'player', '氏名', 'name', '学年', 'grade']):
                        print(f"✅ 選手データテーブルを発見: テーブル {i+1}")
                        table_data = self._parse_player_table(table, i)
                        data.extend(table_data)
            
            # div要素での選手リストも探す
            player_divs = self.driver.find_elements("css selector", "div[class*='player'], div[class*='選手'], div[id*='player']")
            
            if player_divs:
                print(f"📋 {len(player_divs)}個の選手関連div要素を発見")
                
                for i, div in enumerate(player_divs):
                    div_text = div.text.strip()
                    if div_text:
                        data.append({
                            'type': 'player_div',
                            'index': i,
                            'content': div_text,
                            'html': div.get_attribute('innerHTML')[:500]
                        })
                        
        except Exception as e:
            print(f"❌ DOM選手データ抽出エラー: {e}")
            
        return data
    
    def _parse_player_table(self, table, table_index: int) -> List[Dict]:
        """選手テーブルを解析"""
        table_data = []
        
        try:
            # ヘッダー行を取得
            headers = []
            header_elements = table.find_elements("tag name", "th")
            if header_elements:
                headers = [th.text.strip() for th in header_elements]
            else:
                # thがない場合、最初の行をヘッダーとして使用
                first_row = table.find_elements("tag name", "tr")[0] if table.find_elements("tag name", "tr") else None
                if first_row:
                    headers = [td.text.strip() for td in first_row.find_elements("tag name", "td")]
            
            print(f"📝 選手テーブル {table_index + 1} ヘッダー: {headers}")
            
            # データ行を取得
            rows = table.find_elements("tag name", "tr")
            
            for row_index, row in enumerate(rows[1:], 1):  # ヘッダー行をスキップ
                cells = row.find_elements("tag name", "td")
                
                if cells:
                    row_data = {
                        "table_index": table_index,
                        "row_index": row_index,
                        "data_type": "player_info"
                    }
                    
                    for i, cell in enumerate(cells):
                        header = headers[i] if i < len(headers) else f"column_{i}"
                        cell_text = cell.text.strip()
                        row_data[header] = cell_text
                        
                        # 特定の情報を個別に抽出
                        if any(keyword in header.lower() for keyword in ['氏名', 'name', '名前']):
                            row_data['player_name'] = cell_text
                        elif any(keyword in header.lower() for keyword in ['学年', 'grade', '年']):
                            row_data['grade'] = cell_text
                        elif any(keyword in header.lower() for keyword in ['学科', 'department', '専攻']):
                            row_data['department'] = cell_text
                    
                    table_data.append(row_data)
                    print(f"  選手情報: {row_data.get('player_name', 'N/A')} ({row_data.get('grade', 'N/A')})")
                    
        except Exception as e:
            print(f"❌ 選手テーブル解析エラー: {e}")
            
        return table_data
    
    def _extract_player_data_from_javascript(self, js_content: str, base_url: str, session, headers) -> List[Dict]:
        """JavaScriptから選手データを抽出"""
        data = []
        
        try:
            print("🔍 JavaScriptから選手データパターンを検索中...")
            
            # 選手データのパターンを検索
            patterns = [
                r'SyozokuList[^=]*=\s*({.*?});',
                r'PlayerList[^=]*=\s*({.*?});',
                r'選手[^=]*=\s*({.*?});',
                r'var\s+\w*[Pp]layer\w*\s*=\s*({.*?});',
                r'var\s+\w*[Ss]yozoku\w*\s*=\s*({.*?});',
                r'data\s*=\s*({.*?"選手".*?});',
                r'({.*?"氏名".*?})',
                r'({.*?"学年".*?})',
            ]
            
            for i, pattern in enumerate(patterns):
                print(f"  パターン {i+1}: {pattern}")
                matches = re.findall(pattern, js_content, re.DOTALL | re.MULTILINE)
                
                if matches:
                    print(f"✅ パターン {i+1} で {len(matches)}件のマッチを発見")
                    
                    for j, match in enumerate(matches):
                        try:
                            # JSONとして解析を試行
                            player_data = json.loads(match)
                            
                            # 選手データの構造を解析
                            processed_data = self._process_player_json_data(player_data, f"pattern_{i+1}_match_{j+1}")
                            data.extend(processed_data)
                            
                        except json.JSONDecodeError as e:
                            print(f"  ❌ JSON解析エラー (パターン {i+1}, マッチ {j+1}): {e}")
                            print(f"  📄 マッチ内容 (最初の200文字): {match[:200]}")
            
            # 配列形式のデータも検索
            array_patterns = [
                r'SyozokuList[^=]*=\s*(\[.*?\]);',
                r'PlayerList[^=]*=\s*(\[.*?\]);',
                r'var\s+\w*[Pp]layer\w*\s*=\s*(\[.*?\]);',
            ]
            
            for i, pattern in enumerate(array_patterns):
                print(f"  配列パターン {i+1}: {pattern}")
                matches = re.findall(pattern, js_content, re.DOTALL | re.MULTILINE)
                
                if matches:
                    print(f"✅ 配列パターン {i+1} で {len(matches)}件のマッチを発見")
                    
                    for j, match in enumerate(matches):
                        try:
                            player_array = json.loads(match)
                            
                            if isinstance(player_array, list):
                                for k, item in enumerate(player_array):
                                    if isinstance(item, dict):
                                        processed_item = self._process_player_json_data(item, f"array_pattern_{i+1}_match_{j+1}_item_{k+1}")
                                        data.extend(processed_item)
                                        
                        except json.JSONDecodeError as e:
                            print(f"  ❌ 配列JSON解析エラー (パターン {i+1}, マッチ {j+1}): {e}")
            
        except Exception as e:
            print(f"❌ JavaScript選手データ抽出エラー: {e}")
            import traceback
            traceback.print_exc()
            
        return data
    
    def _process_player_json_data(self, json_data: Dict, source: str) -> List[Dict]:
        """JSON形式の選手データを処理"""
        processed_data = []
        
        try:
            print(f"🔧 {source} からJSONデータを処理中...")
            
            # データ構造に応じて処理
            if isinstance(json_data, dict):
                # 直接選手情報が含まれている場合
                if any(key in json_data for key in ['氏名', 'name', '学年', 'grade', '選手']):
                    player_info = json_data.copy()
                    player_info['source'] = source
                    player_info['data_type'] = 'player_direct'
                    processed_data.append(player_info)
                    print(f"  ✅ 直接選手データ: {player_info.get('氏名', player_info.get('name', 'N/A'))}")
                
                # ネストされた構造を探索
                for key, value in json_data.items():
                    if isinstance(value, dict):
                        nested_data = self._process_player_json_data(value, f"{source}_{key}")
                        processed_data.extend(nested_data)
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                nested_data = self._process_player_json_data(item, f"{source}_{key}_{i}")
                                processed_data.extend(nested_data)
            
        except Exception as e:
            print(f"❌ JSON選手データ処理エラー ({source}): {e}")
            
        return processed_data
    
    def _extract_static_player_data(self, soup) -> List[Dict]:
        """静的HTMLから選手データを抽出"""
        data = []
        
        try:
            print("🔍 静的HTMLから選手データを抽出中...")
            
            # テーブルから選手情報を抽出
            tables = soup.find_all('table')
            
            for i, table in enumerate(tables):
                print(f"📊 テーブル {i+1} を解析中...")
                
                # テーブルに選手関連の内容があるかチェック
                table_text = table.get_text().lower()
                if any(keyword in table_text for keyword in ['選手', '氏名', '学年', 'player', 'name', 'grade']):
                    print(f"✅ 選手データテーブルを発見: テーブル {i+1}")
                    
                    table_data = self._parse_bs4_player_table(table, i)
                    data.extend(table_data)
            
            # div要素からも選手情報を探す
            player_divs = soup.find_all('div', class_=lambda x: x and any(keyword in x.lower() for keyword in ['player', '選手']))
            
            for i, div in enumerate(player_divs):
                div_text = div.get_text().strip()
                if div_text:
                    data.append({
                        'type': 'player_div',
                        'index': i,
                        'content': div_text,
                        'html': str(div)[:500]
                    })
            
        except Exception as e:
            print(f"❌ 静的HTML選手データ抽出エラー: {e}")
            
        return data
    
    def _parse_bs4_player_table(self, table, table_index: int) -> List[Dict]:
        """BeautifulSoupで選手テーブルを解析"""
        table_data = []
        
        try:
            print(f"🔍 選手テーブル {table_index + 1} の詳細解析を開始...")
            
            # ヘッダー行を取得
            headers = []
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text().strip())
        
            print(f"📝 選手テーブルヘッダー: {headers}")
            
            # 全ての行を取得
            all_rows = table.find_all('tr')
            print(f"📊 選手テーブル内の行数: {len(all_rows)}")
            
            # データ行を取得（ヘッダー以外）
            data_rows = all_rows[1:] if len(all_rows) > 1 else []
            
            for j, row in enumerate(data_rows):
                cells = row.find_all(['td', 'th'])
                
                if cells:
                    row_data = {
                        'table_index': table_index,
                        'row_index': j,
                        'data_type': 'player_info'
                    }
                    
                    for k, cell in enumerate(cells):
                        header = headers[k] if k < len(headers) else f'column_{k}'
                        cell_text = cell.get_text().strip()
                        row_data[header] = cell_text
                        
                        # 特定の情報を個別に抽出
                        if any(keyword in header.lower() for keyword in ['氏名', 'name', '名前']):
                            row_data['player_name'] = cell_text
                        elif any(keyword in header.lower() for keyword in ['学年', 'grade', '年']):
                            row_data['grade'] = cell_text
                        elif any(keyword in header.lower() for keyword in ['学科', 'department', '専攻']):
                            row_data['department'] = cell_text
                
                    # 空でない行のみ追加
                    non_empty_values = [v for k, v in row_data.items() 
                                      if k not in ['table_index', 'row_index', 'data_type'] and v.strip()]
                    
                    if non_empty_values:
                        table_data.append(row_data)
                        print(f"  ✅ 選手: {row_data.get('player_name', 'N/A')} ({row_data.get('grade', 'N/A')})")
                        
        except Exception as e:
            print(f"❌ BeautifulSoup選手テーブル解析エラー: {e}")
            
        return table_data

def main():
    """メイン実行関数"""
    print("🚀 所属選手情報スクレイピングを開始...")
    
    url = "https://tsriku.stars.ne.jp/htmlR6/240727/shtml/SyozokuPlayer.html#!#syozoku_19"
    scraper = SyozokuPlayerScraper()
    
    try:
        # データを取得
        print(f"📡 URL: {url}")
        extracted_data = scraper.scrape_syozoku_player(url)
        
        if not extracted_data:
            print("❌ 選手データが取得できませんでした")
            return
        
        # データを保存
        scraper.save_to_csv(extracted_data, 'syozoku_player_data.csv')
        
        print("\n✅ 所属選手スクレイピング処理が完了しました！")
        print("📄 取得した選手データは以下のファイルに保存されました:")
        print("  - syozoku_player_data.csv (選手データ)")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Seleniumドライバーが存在する場合のみクローズ
        if hasattr(scraper, 'driver') and scraper.driver:
            scraper.driver.quit()

if __name__ == "__main__":
    main()
