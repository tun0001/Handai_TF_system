from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import pandas as pd
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
import re

class JavaScriptScraper:
    def __init__(self, headless: bool = True, wait_timeout: int = 10):
        """
        JavaScriptが有効なWebページをスクレイピングするクラス
        
        Args:
            headless: ヘッドレスモードで実行するか
            wait_timeout: 要素の読み込み待機時間（秒）
        """
        self.wait_timeout = wait_timeout
        self.driver = None
        self.wait = None
        
        # Seleniumの初期化を試行
        try:
            self.driver = self._setup_driver(headless)
            self.wait = WebDriverWait(self.driver, wait_timeout)
            print("✅ Seleniumが正常に初期化されました")
        except Exception as e:
            print(f"⚠️ Selenium初期化失敗: {e}")
            print("🔄 フォールバックモード（requests + BeautifulSoup）を使用します")
    
    def _setup_driver(self, headless: bool) -> webdriver.Chrome:
        """Chrome WebDriverをセットアップ"""
        # まずChromeがインストールされているかチェック
        import shutil
        chrome_path = shutil.which('google-chrome') or shutil.which('chrome') or shutil.which('chromium')
        
        if not chrome_path:
            raise Exception("Chrome browser not found. Please install Chrome or use fallback mode.")
        
        options = Options()
        if headless:
            options.add_argument('--headless')
    
        # 基本的な安全オプション
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        # JavaScriptを有効にする（無効にしていたのを修正）
        # options.add_argument('--disable-javascript')  # この行をコメントアウト
        options.add_argument('--window-size=1920,1080')
        
        # ユーザーデータディレクトリの問題を回避
        import tempfile
        import os
        temp_dir = tempfile.mkdtemp()
        options.add_argument(f'--user-data-dir={temp_dir}')
        options.add_argument('--profile-directory=Default')
    
        # User-Agentを設定
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Chrome バイナリのパスを明示的に指定
        if chrome_path:
            options.binary_location = chrome_path
        
        try:
            # ChromeDriverのパスを明示的に指定
            from selenium.webdriver.chrome.service import Service
            
            # ChromeDriverが利用可能かチェック
            chromedriver_path = shutil.which('chromedriver')
            
            if chromedriver_path:
                print(f"🔧 ChromeDriverを発見: {chromedriver_path}")
                service = Service(chromedriver_path)
                return webdriver.Chrome(service=service, options=options)
            else:
                print("🔧 ChromeDriverが見つかりません。webdriver-managerを使用します...")
                # webdriver-managerを使用してChromeDriverを自動ダウンロード
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                return webdriver.Chrome(service=service, options=options)
                
        except Exception as e:
            print(f"❌ Chrome WebDriverの初期化エラー: {e}")
            raise
    
    def scrape_timetable(self, url: str) -> List[Dict]:
        """
        タイムテーブルページからデータを取得
        
        Args:
            url: スクレイピング対象のURL
            
        Returns:
            取得したデータのリスト
        """
        if self.driver:
            return self._scrape_with_selenium(url)
        else:
            return self._scrape_with_requests(url)
    
    def _scrape_with_selenium(self, url: str) -> List[Dict]:
        """Seleniumを使用してスクレイピング"""
        try:
            print(f"🌐 Seleniumでページにアクセス中: {url}")
            
            # 1. ネットワークリクエストをキャプチャ
            data = self._capture_network_requests_selenium(url)
            
            if data:
                print(f"✅ ネットワークキャプチャで {len(data)}件のデータを取得")
                return data
            
            # 2. 従来のDOM解析
            self.driver.get(url)
            self._wait_for_page_load()
            time.sleep(3)
            
            data = self._extract_timetable_data()
            
            print(f"✅ DOM解析で {len(data)}件のデータを取得しました")
            return data
            
        except Exception as e:
            print(f"❌ Seleniumスクレイピングエラー: {e}")
            print("🔄 フォールバックモードに切り替えます...")
            return self._scrape_with_requests(url)
    
    def _scrape_with_requests(self, url: str) -> List[Dict]:
        """requests + BeautifulSoupを使用してスクレイピング"""
        try:
            print(f"🔄 requestsでページを取得中: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
                'Accept-Encoding': 'gzip, deflate',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            print(f"📄 レスポンス取得成功 (Status: {response.status_code})")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            data = []
            # 1. HTMLからJavaScriptファイルを発見
            print("\n🔍 HTMLからJavaScriptファイルを検索...")
            js_files = self._find_javascript_files(soup, url.replace('/TimeTable.html', ''))
            
            # 2. 見つかったJavaScriptファイルを解析
            for js_url in js_files:
                print(f"\n🎯 JavaScript解析: {js_url}")
                try:
                    js_response = session.get(js_url, headers=headers, timeout=10)
                    print(f"📡 レスポンス: {js_response.status_code}")
                    
                    if js_response.status_code == 200:
                        js_content = js_response.text
                        print(f"\n📄 {js_url} の内容:")
                        print("=" * 80)
                        print(js_content)
                        print("=" * 80)
                        
                        # JavaScriptからデータを抽出
                        js_data = self._extract_data_from_javascript(js_content, url.replace('/TimeTable.html', ''), session, headers)
                        data.extend(js_data)
                        
                except Exception as e:
                    print(f"❌ JavaScript取得エラー ({js_url}): {e}")
            
            # 3. TimeTable.jsを詳細解析（フォールバック）
            if not data:
                print("\n🎯 TimeTable.jsを詳細解析...")
                data = self._analyze_timetable_js_detailed(url, session, headers)
            
            # 4. 静的HTMLからのデータ抽出（最終フォールバック）
            if not data:
                print("📄 静的HTMLからのデータ抽出を試行...")
                data = self._extract_static_data(soup)
            
            print(f"✅ フォールバックで {len(data)}件のデータを取得")
            return data
        
        except Exception as e:
            print(f"❌ requestsスクレイピングエラー: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _parse_bs4_table(self, table, table_index: int) -> List[Dict]:
        """BeautifulSoupでテーブルを解析"""
        table_data = []
        
        try:
            print(f"🔍 テーブル {table_index + 1} の詳細解析を開始...")
            
            # テーブル全体のHTMLを表示
            print(f"📄 テーブル {table_index + 1} のHTML:")
            print(str(table)[:500])  # 最初の500文字
            print("=" * 50)
            
            # ヘッダー行を取得
            headers = []
            header_row = table.find('tr')
            if header_row:
                for th in header_row.find_all(['th', 'td']):
                    headers.append(th.get_text().strip())
        
            print(f"📝 ヘッダー: {headers}")
            
            # 全ての行を取得
            all_rows = table.find_all('tr')
            print(f"📊 テーブル内の行数: {len(all_rows)}")
            
            # データ行を取得（ヘッダー以外）
            data_rows = all_rows[1:] if len(all_rows) > 1 else []
            print(f"📊 データ行数: {len(data_rows)}")
            
            for j, row in enumerate(data_rows):
                print(f"  🔍 行 {j+1} を解析中...")
                
                # 行のHTMLを表示
                print(f"    📄 行のHTML: {str(row)[:200]}")
                
                cells = row.find_all(['td', 'th'])
                print(f"    📊 セル数: {len(cells)}")
                
                if cells:
                    row_data = {
                        'table_index': table_index,
                        'row_index': j
                    }
                    
                    for k, cell in enumerate(cells):
                        header = headers[k] if k < len(headers) else f'column_{k}'
                        cell_text = cell.get_text().strip()
                        
                        print(f"      📝 セル {k+1} ({header}): '{cell_text}'")
                        
                        row_data[header] = cell_text
                
                    # 空でない行のみ追加
                    non_empty_values = [v for k, v in row_data.items() 
                                      if k not in ['table_index', 'row_index'] and v.strip()]
                    
                    print(f"    📊 空の値の数: {len(non_empty_values)}")
                    
                    if non_empty_values:
                        table_data.append(row_data)
                        print(f"    ✅ 行を追加: {row_data}")
                    else:
                        print(f"    ❌ 空の行のためスキップ")
                else:
                    print(f"    ❌ セルが見つかりません")
                    
            print(f"🎯 テーブル {table_index + 1} から {len(table_data)}件のデータを抽出")
            
        except Exception as e:
            print(f"❌ BeautifulSoupテーブル解析エラー: {e}")
            import traceback
            traceback.print_exc()
            
        return table_data
    
    def _extract_bs4_alternative_data(self, soup) -> List[Dict]:
        """BeautifulSoupで代替データ構造を探す"""
        data = []
        
        try:
            # 様々なセレクターでデータを探す
            selectors = [
                '.time-slot', '.schedule-item', '.event',
                '[class*="time"]', '[class*="schedule"]', '[class*="event"]',
                '.row', '.item', '.entry'
            ]
            
            for selector in selectors:
                elements = soup.select(selector)
                if elements:
                    print(f"🔍 {selector} で {len(elements)}個の要素を発見")
                    
                    for i, element in enumerate(elements):
                        data.append({
                            'selector': selector,
                            'index': i,
                            'text': element.get_text().strip(),
                            'html': str(element)[:200]  # HTMLの最初の200文字
                        })
                    break
                    
        except Exception as e:
            print(f"❌ 代替データ抽出エラー: {e}")
            
        return data
    
    # Seleniumメソッドは既存のものを使用...
    def _wait_for_page_load(self):
        """ページの読み込み完了を待機"""
        if not self.driver:
            return
            
        try:
            # 一般的な読み込み完了の条件をチェック
            self.wait.until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # テーブルやデータコンテナの存在を確認
            possible_selectors = [
                "table",
                ".timetable",
                "#timetable", 
                ".schedule",
                ".data-table",
                "[class*='time']",
                "[class*='table']"
            ]
            
            for selector in possible_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    print(f"📋 テーブル要素を発見: {selector}")
                    break
                except TimeoutException:
                    continue
            
        except TimeoutException:
            print("⚠️ ページの読み込みがタイムアウトしました")
    
    def _extract_timetable_data(self) -> List[Dict]:
        """タイムテーブルデータを抽出"""
        if not self.driver:
            return []
            
        data = []
        
        try:
            # まずはページのHTMLを確認
            page_source = self.driver.page_source
            print("📄 ページソースの一部:")
            print(page_source[:1000])  # 最初の1000文字を表示
            
            # テーブル要素を探す
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            
            if tables:
                print(f"📊 {len(tables)}個のテーブルを発見")
                
                for i, table in enumerate(tables):
                    print(f"🔍 テーブル {i+1} を解析中...")
                    table_data = self._parse_table(table, i)
                    data.extend(table_data)
            else:
                print("❌ テーブル要素が見つかりません")
                # 他の方法でデータを探す
                data = self._extract_alternative_data()
                
        except Exception as e:
            print(f"❌ データ抽出エラー: {e}")
            
        return data
    
    def _parse_table(self, table, table_index: int) -> List[Dict]:
        """個別のテーブルを解析"""
        table_data = []
        
        try:
            # ヘッダー行を取得
            headers = []
            header_elements = table.find_elements(By.TAG_NAME, "th")
            if header_elements:
                headers = [th.text.strip() for th in header_elements]
            else:
                # thがない場合、最初の行をヘッダーとして使用
                first_row = table.find_elements(By.TAG_NAME, "tr")[0] if table.find_elements(By.TAG_NAME, "tr") else None
                if first_row:
                    headers = [td.text.strip() for td in first_row.find_elements(By.TAG_NAME, "td")]
            
            print(f"📝 ヘッダー: {headers}")
            
            # データ行を取得
            rows = table.find_elements(By.TAG_NAME, "tr")
            
            for row_index, row in enumerate(rows[1:], 1):  # ヘッダー行をスキップ
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if cells:
                    row_data = {
                        "table_index": table_index,
                        "row_index": row_index,
                    }
                    
                    for i, cell in enumerate(cells):
                        header = headers[i] if i < len(headers) else f"column_{i}"
                        row_data[header] = cell.text.strip()
                    
                    table_data.append(row_data)
                    
        except Exception as e:
            print(f"❌ テーブル解析エラー: {e}")
            
        return table_data
    
    def _extract_alternative_data(self) -> List[Dict]:
        """テーブル以外の方法でデータを抽出"""
        if not self.driver:
            return []
            
        data = []
        
        try:
            # divやspan要素でのデータ構造を探す
            possible_selectors = [
                ".time-slot",
                ".schedule-item", 
                ".event",
                "[class*='time']",
                "[class*='schedule']",
                "[class*='event']"
            ]
            
            for selector in possible_selectors:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"🔍 {selector} で {len(elements)}個の要素を発見")
                    
                    for i, element in enumerate(elements):
                        data.append({
                            "selector": selector,
                            "index": i,
                            "text": element.text.strip(),
                            "html": element.get_attribute("innerHTML")
                        })
                    break
                    
        except Exception as e:
            print(f"❌ 代替データ抽出エラー: {e}")
            
        return data
    
    def save_to_csv(self, data: List[Dict], filename: str):
        """データをCSVファイルに保存"""
        if data:
            df = pd.DataFrame(data)
            df.to_csv(filename, index=False, encoding='utf-8-sig')
            print(f"💾 データを {filename} に保存しました")
            
            # データの詳細表示
            print(f"📊 保存されたデータ: {len(data)}行, {len(df.columns)}列")
            print(f"📝 列名: {list(df.columns)}")
            
            # ネストされたデータの展開と保存
            self._expand_and_save_nested_data(data, filename)
        else:
            print("❌ 保存するデータがありません")

    def _expand_and_save_nested_data(self, data: List[Dict], base_filename: str):
        """ネストされたデータを展開して個別のCSVファイルとして保存"""
        try:
            base_name = base_filename.replace('.csv', '')
            
            for i, item in enumerate(data):
                print(f"\n🔍 データ項目 {i+1} の展開を開始...")
                
                # TimeTableListの展開
                if 'TimeTableList' in item and isinstance(item['TimeTableList'], dict):
                    print("📅 TimeTableListを展開中...")
                    self._expand_timetable_list(item['TimeTableList'], f"{base_name}_detailed_timetable.csv")
                
                # KyogiListの展開
                if 'KyogiList' in item and isinstance(item['KyogiList'], (dict, list)):
                    print("🏃 KyogiListを展開中...")
                    self._expand_kyogi_list(item['KyogiList'], f"{base_name}_kyogi_list.csv")
                
                # SyozokuListの展開
                if 'SyozokuList' in item and isinstance(item['SyozokuList'], (dict, list)):
                    print("🏫 SyozokuListを展開中...")
                    self._expand_syozoku_list(item['SyozokuList'], f"{base_name}_syozoku_list.csv")
                
                # NitteiListの展開
                if 'NitteiList' in item and isinstance(item['NitteiList'], (dict, list)):
                    print("📋 NitteiListを展開中...")
                    self._expand_nittei_list(item['NitteiList'], f"{base_name}_nittei_list.csv")
                
                # SyumokuBetsuListの展開
                if 'SyumokuBetsuList' in item and isinstance(item['SyumokuBetsuList'], (dict, list)):
                    print("🏆 SyumokuBetsuListを展開中...")
                    self._expand_syumoku_betsu_list(item['SyumokuBetsuList'], f"{base_name}_syumoku_betsu_list.csv")

        except Exception as e:
            print(f"❌ ネストデータ展開エラー: {e}")
            import traceback
            traceback.print_exc()

    def _expand_timetable_list(self, timetable_list: Dict, filename: str):
        """TimeTableListの詳細展開"""
        try:
            expanded_data = []
            
            for date, date_data in timetable_list.items():
                print(f"📅 日付 {date} の処理中...")
                
                if isinstance(date_data, dict):
                    for shumoku_key, shumoku_data in date_data.items():
                        if isinstance(shumoku_data, dict):
                            for seibetsu_key, seibetsu_data in shumoku_data.items():
                                if isinstance(seibetsu_data, dict) and 'TimeTable' in seibetsu_data:
                                    timetable = seibetsu_data['TimeTable']
                                    if isinstance(timetable, list):
                                        for event in timetable:
                                            if isinstance(event, dict):
                                                # 階層情報を追加
                                                event_data = event.copy()
                                                event_data['Date'] = date
                                                event_data['ShumokuKey'] = shumoku_key
                                                event_data['SeibetsuKey'] = seibetsu_key
                                                expanded_data.append(event_data)
            
            if expanded_data:
                df = pd.DataFrame(expanded_data)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"✅ 詳細タイムテーブルを {filename} に保存 ({len(expanded_data)}件)")
                
                # データサンプルを表示
                print("📊 保存されたタイムテーブルのサンプル:")
                for i, sample in enumerate(expanded_data[:3]):
                    print(f"  {i+1}: {sample.get('KyogiMei', 'N/A')} - {sample.get('KaishiJikan', 'N/A')} ({sample.get('Date', 'N/A')})")
            else:
                print("⚠️ 展開できるタイムテーブルデータが見つかりませんでした")

        except Exception as e:
            print(f"❌ TimeTableList展開エラー: {e}")
            import traceback
            traceback.print_exc()

    def _expand_kyogi_list(self, kyogi_list, filename: str):
        """KyogiListの展開"""
        try:
            expanded_data = []
            
            if isinstance(kyogi_list, dict):
                for key, value in kyogi_list.items():
                    if isinstance(value, dict):
                        value['KyogiKey'] = key
                        expanded_data.append(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                item['KyogiKey'] = key
                                expanded_data.append(item)
            elif isinstance(kyogi_list, list):
                expanded_data = kyogi_list
            
            if expanded_data:
                df = pd.DataFrame(expanded_data)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"✅ 競技リストを {filename} に保存 ({len(expanded_data)}件)")
        
        except Exception as e:
            print(f"❌ KyogiList展開エラー: {e}")

    def _expand_syozoku_list(self, syozoku_list, filename: str):
        """SyozokuListの展開"""
        try:
            expanded_data = []
            
            if isinstance(syozoku_list, dict):
                for key, value in syozoku_list.items():
                    if isinstance(value, dict):
                        value['SyozokuKey'] = key
                        expanded_data.append(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                item['SyozokuKey'] = key
                                expanded_data.append(item)
            elif isinstance(syozoku_list, list):
                expanded_data = syozoku_list
            
            if expanded_data:
                df = pd.DataFrame(expanded_data)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"✅ 所属リストを {filename} に保存 ({len(expanded_data)}件)")
        
        except Exception as e:
            print(f"❌ SyozokuList展開エラー: {e}")

    def _expand_nittei_list(self, nittei_list, filename: str):
        """NitteiListの展開"""
        try:
            expanded_data = []
            
            if isinstance(nittei_list, dict):
                for key, value in nittei_list.items():
                    if isinstance(value, dict):
                        value['NitteiKey'] = key
                        expanded_data.append(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                item['NitteiKey'] = key
                                expanded_data.append(item)
            elif isinstance(nittei_list, list):
                expanded_data = nittei_list
            
            if expanded_data:
                df = pd.DataFrame(expanded_data)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"✅ 日程リストを {filename} に保存 ({len(expanded_data)}件)")
        
        except Exception as e:
            print(f"❌ NitteiList展開エラー: {e}")

    def _expand_syumoku_betsu_list(self, syumoku_betsu_list, filename: str):
        """SyumokuBetsuListの展開"""
        try:
            expanded_data = []
            
            if isinstance(syumoku_betsu_list, dict):
                for key, value in syumoku_betsu_list.items():
                    if isinstance(value, dict):
                        value['SyumokuBetsuKey'] = key
                        expanded_data.append(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                item['SyumokuBetsuKey'] = key
                                expanded_data.append(item)
            elif isinstance(syumoku_betsu_list, list):
                expanded_data = syumoku_betsu_list
            
            if expanded_data:
                df = pd.DataFrame(expanded_data)
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"✅ 種目別リストを {filename} に保存 ({len(expanded_data)}件)")
        
        except Exception as e:
            print(f"❌ SyumokuBetsuList展開エラー: {e}")
    
    def _find_javascript_files(self, soup, base_url: str) -> List[str]:
        """HTMLからJavaScriptファイルのURLを抽出"""
        js_files = []
        
        try:
            # script要素からJavaScriptファイルを探す
            script_tags = soup.find_all('script', src=True)
            
            for script in script_tags:
                src = script.get('src')
                if src:
                    # 相対パスを絶対パスに変換
                    if src.startswith('//'):
                        js_url = f"https:{src}"
                    elif src.startswith('/'):
                        js_url = f"{base_url}{src}"
                    elif src.startswith('http'):
                        js_url = src
                    else:
                        js_url = f"{base_url}/{src}"
                    
                    js_files.append(js_url)
                    print(f"  📁 発見: {js_url}")
            
            # 一般的なJavaScriptファイル名も追加で試行
            common_js_files = [
                'TimeTable.js',
                'SyozokuPlayer.js',
                'PlayerData.js',
                'data.js',
                'main.js',
                'app.js'
            ]
            
            for js_file in common_js_files:
                js_url = f"{base_url}/{js_file}"
                if js_url not in js_files:
                    js_files.append(js_url)
                    print(f"  🔍 推測: {js_url}")
            
        except Exception as e:
            print(f"❌ JavaScriptファイル検索エラー: {e}")
        
        return js_files
    
    def _extract_data_from_javascript(self, js_content: str, base_url: str, session, headers) -> List[Dict]:
        """JavaScriptからデータを抽出"""
        data = []
        
        try:
            print("🔍 JavaScriptからデータパターンを検索中...")
            
            # データのパターンを検索
            patterns = [
                r'TimeTableList[^=]*=\s*({.*?});',
                r'KyogiList[^=]*=\s*({.*?});',
                r'SyozokuList[^=]*=\s*({.*?});',
                r'NitteiList[^=]*=\s*({.*?});',
                r'var\s+\w*List\w*\s*=\s*({.*?});',
                r'data\s*=\s*({.*?});',
                r'({.*?"TimeTable".*?})',
                r'({.*?"Kyogi".*?})',
            ]
            
            for i, pattern in enumerate(patterns):
                print(f"  パターン {i+1}: {pattern}")
                matches = re.findall(pattern, js_content, re.DOTALL | re.MULTILINE)
                
                if matches:
                    print(f"✅ パターン {i+1} で {len(matches)}件のマッチを発見")
                    
                    for j, match in enumerate(matches):
                        try:
                            # JSONとして解析を試行
                            json_data = json.loads(match)
                            
                            # データの構造を保持して追加
                            processed_data = {
                                'source': f'javascript_pattern_{i+1}_match_{j+1}',
                                'pattern': pattern,
                                'match_index': j,
                                'data': json_data
                            }
                            
                            # ネストされたデータを展開
                            if isinstance(json_data, dict):
                                for key, value in json_data.items():
                                    processed_data[key] = value
                            
                            data.append(processed_data)
                            
                        except json.JSONDecodeError as e:
                            print(f"  ❌ JSON解析エラー (パターン {i+1}, マッチ {j+1}): {e}")
                            print(f"  📄 マッチ内容 (最初の200文字): {match[:200]}")
            
            # 配列形式のデータも検索
            array_patterns = [
                r'TimeTableList[^=]*=\s*(\[.*?\]);',
                r'KyogiList[^=]*=\s*(\[.*?\]);',
                r'var\s+\w*List\w*\s*=\s*(\[.*?\]);',
            ]
            
            for i, pattern in enumerate(array_patterns):
                print(f"  配列パターン {i+1}: {pattern}")
                matches = re.findall(pattern, js_content, re.DOTALL | re.MULTILINE)
                
                if matches:
                    print(f"✅ 配列パターン {i+1} で {len(matches)}件のマッチを発見")
                    
                    for j, match in enumerate(matches):
                        try:
                            array_data = json.loads(match)
                            
                            if isinstance(array_data, list):
                                for k, item in enumerate(array_data):
                                    processed_item = {
                                        'source': f'javascript_array_pattern_{i+1}_match_{j+1}_item_{k+1}',
                                        'pattern': pattern,
                                        'array_index': k,
                                        'data': item
                                    }
                                    
                                    if isinstance(item, dict):
                                        for key, value in item.items():
                                            processed_item[key] = value
                                    
                                    data.append(processed_item)
                                    
                        except json.JSONDecodeError as e:
                            print(f"  ❌ 配列JSON解析エラー (パターン {i+1}, マッチ {j+1}): {e}")
            
        except Exception as e:
            print(f"❌ JavaScript データ抽出エラー: {e}")
            import traceback
            traceback.print_exc()
            
        return data
    
    def _analyze_timetable_js_detailed(self, url: str, session, headers) -> List[Dict]:
        """TimeTable.jsを詳細解析"""
        data = []
        
        try:
            base_url = url.replace('/TimeTable.html', '').replace('/SyozokuPlayer.html#!#syozoku_19', '')
            
            # TimeTable.jsの可能なパスを試行
            timetable_js_urls = [
                f"{base_url}/TimeTable.js",
                f"{base_url}/js/TimeTable.js",
                f"{base_url}/scripts/TimeTable.js",
                f"{base_url}/data/TimeTable.js"
            ]
            
            for js_url in timetable_js_urls:
                try:
                    print(f"🔍 {js_url} をチェック中...")
                    js_response = session.get(js_url, headers=headers, timeout=10)
                    
                    if js_response.status_code == 200:
                        print(f"✅ 発見: {js_url}")
                        js_content = js_response.text
                        
                        # データを抽出
                        js_data = self._extract_data_from_javascript(js_content, base_url, session, headers)
                        data.extend(js_data)
                        
                        break  # 最初に見つかったファイルを使用
                        
                except Exception as e:
                    print(f"❌ {js_url} 取得失敗: {e}")
                    
        except Exception as e:
            print(f"❌ TimeTable.js詳細解析エラー: {e}")
            
        return data
    
    def _extract_static_data(self, soup) -> List[Dict]:
        """静的HTMLからのデータ抽出"""
        data = []
        
        try:
            print("🔍 静的HTMLからデータを抽出中...")
            
            # テーブルからデータを抽出
            tables = soup.find_all('table')
            
            for i, table in enumerate(tables):
                print(f"📊 テーブル {i+1} を解析中...")
                table_data = self._parse_bs4_table(table, i)
                data.extend(table_data)
            
            # 代替データ構造も探す
            if not data:
                print("🔍 代替データ構造を検索中...")
                alt_data = self._extract_bs4_alternative_data(soup)
                data.extend(alt_data)
            
        except Exception as e:
            print(f"❌ 静的データ抽出エラー: {e}")
            
        return data
    
    def _capture_network_requests_selenium(self, url: str) -> List[Dict]:
        """Seleniumを使用してネットワークリクエストをキャプチャ"""
        data = []
        
        try:
            if not self.driver:
                return data
                
            print("🌐 ネットワークリクエストのキャプチャを開始...")
            
            # Chrome DevTools Protocolを有効にして、ネットワークログを取得
            self.driver.execute_cdp_cmd('Network.enable', {})
            
            # ページにアクセス
            self.driver.get(url)
            self._wait_for_page_load()
            time.sleep(5)
            
            # ネットワークログを取得
            logs = self.driver.get_log('performance')
            
            for log in logs:
                message = json.loads(log['message'])
                
                if message['message']['method'] == 'Network.responseReceived':
                    response = message['message']['params']['response']
                    request_url = response['url']
                    
                    # JavaScriptファイルやJSONレスポンスを探す
                    if any(ext in request_url.lower() for ext in ['.js', '.json', 'data', 'api']):
                        print(f"🔍 ネットワークリクエスト発見: {request_url}")
                        
                        # レスポンスの内容を取得を試行
                        try:
                            response_body = self.driver.execute_cdp_cmd('Network.getResponseBody', 
                                                                       {'requestId': message['message']['params']['requestId']})
                            
                            if response_body.get('body'):
                                content = response_body['body']
                                
                                # JSONとして解析を試行
                                try:
                                    json_data = json.loads(content)
                                    data.append({
                                        'source': 'network_capture',
                                        'url': request_url,
                                        'data': json_data
                                    })
                                    print(f"✅ JSONデータを取得: {request_url}")
                                except json.JSONDecodeError:
                                    # JavaScriptファイルの場合
                                    js_data = self._extract_data_from_javascript(content, url, None, None)
                                    data.extend(js_data)
                                    
                        except Exception as e:
                            print(f"❌ レスポンス取得エラー ({request_url}): {e}")
            
        except Exception as e:
            print(f"❌ ネットワークキャプチャエラー: {e}")
            
        return data

def main():
    """メイン実行関数"""
    print("🚀 JavaScriptスクレイピングを開始...")
    
    url = "https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html"
    scraper = JavaScriptScraper()
    
    try:
        # データを取得
        print(f"📡 URL: {url}")
        extracted_data = scraper.scrape_timetable(url)
        
        if not extracted_data:
            print("❌ データが取得できませんでした")
            return
        
        # データを保存
        scraper.save_to_csv(extracted_data, 'timetable_data.csv')
        
        # 既存の本番データからの詳細展開機能を追加
        print("\n🔧 既存データからの詳細展開を実行中...")
        try:
            import pandas as pd
            existing_df = pd.read_csv('timetable_data.csv', encoding='utf-8-sig')
            existing_data = existing_df.to_dict('records')
            
            print(f"📊 既存データ: {len(existing_data)}行")
            scraper._expand_and_save_nested_data(existing_data, 'timetable_data.csv')
            
        except FileNotFoundError:
            print("⚠️ 既存のCSVファイルが見つかりません")
        except Exception as e:
            print(f"❌ 既存データ展開エラー: {e}")
        
        print("\n✅ スクレイピング処理が完了しました！")
        print("📄 取得したデータは以下のファイルに保存されました:")
        print("  - timetable_data.csv (メインデータ)")
        print("  - timetable_data_detailed_timetable.csv (詳細タイムテーブル)")
        print("  - timetable_data_kyogi_list.csv (競技リスト)")
        print("  - timetable_data_syozoku_list.csv (所属リスト)")
        print("  - その他のデータリスト...")
        
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