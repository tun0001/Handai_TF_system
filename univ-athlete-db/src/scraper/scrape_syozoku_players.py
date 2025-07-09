#!/usr/bin/env python3
"""
所属選手ページ専用スクレイピングスクリプト

URL例: https://tsriku.stars.ne.jp/htmlR6/240727/shtml/SyozokuPlayer.html#!#syozoku_19
"""

import sys
import os
import json
import re
import time
from typing import List, Dict, Optional

# プロジェクトのパスを追加
sys.path.append('/workspaces/Handai_TF_system/univ-athlete-db/src')
from scraper.scrape_js import JavaScriptScraper

class SyozokuPlayerScraper(JavaScriptScraper):
    """所属選手ページ専用のスクレイピングクラス"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
        
    def scrape_syozoku_players(self, url: str, syozoku_id: str = None) -> List[Dict]:
        """
        所属選手ページから選手情報を取得
        
        Args:
            url: 所属選手ページのURL
            syozoku_id: 所属ID（URL から自動抽出可能）
            
        Returns:
            選手情報のリスト
        """
        # URLから所属IDを抽出
        if not syozoku_id:
            syozoku_id = self._extract_syozoku_id(url)
            
        print(f"🎯 所属選手ページをスクレイピング開始: {url}")
        print(f"🏫 所属ID: {syozoku_id}")
        
        # JSONデータを直接取得する方法を試行
        json_data = self._try_get_json_data(url)
        if json_data:
            return self._extract_players_from_json(json_data, syozoku_id)
        
        # フォールバック: 通常のページスクレイピング
        if self.driver:
            return self._scrape_players_selenium(url, syozoku_id)
        else:
            return self._scrape_players_requests(url, syozoku_id)
    
    def _extract_syozoku_id(self, url: str) -> str:
        """URLから所属IDを抽出"""
        match = re.search(r'syozoku_(\d+)', url)
        if match:
            return match.group(1)
        return "unknown"
    
    def _try_get_json_data(self, url: str) -> Optional[Dict]:
        """JSONデータの直接取得を試行"""
        try:
            # ベースURLを取得してJSONエンドポイントを構築
            base_url = url.split('#')[0]  # フラグメントを除去
            json_url = base_url.replace('.html', '.json')
            
            import requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': url
            }
            
            print(f"🔍 JSONエンドポイントを確認: {json_url}")
            response = requests.get(json_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ JSONデータを取得: {len(str(data))} 文字")
                print(f"📊 JSONキー: {list(data.keys())}")
                return data
            else:
                print(f"❌ JSONエンドポイント取得失敗: {response.status_code}")
                return None
                    
        except Exception as e:
            print(f"❌ JSON取得エラー: {e}")
            return None
    
    def _extract_players_from_json(self, json_data: Dict, syozoku_id: str) -> List[Dict]:
        """JSONデータから選手情報を抽出"""
        players = []
        
        try:
            # SyozokuListからデータを抽出
            if 'SyozokuList' in json_data:
                syozoku_list = json_data['SyozokuList']
                
                # 指定された所属IDの選手データを探す
                target_syozoku = None
                for syozoku in syozoku_list:
                    if str(syozoku.get('SYOZOKUNO', '')) == str(syozoku_id):
                        target_syozoku = syozoku
                        break
                
                if target_syozoku:
                    syozoku_name = target_syozoku.get('SYOZOKUMEI', '不明')
                    kyogisya_list = target_syozoku.get('KYOGISYA', [])
                    
                    print(f"🏫 所属名: {syozoku_name}")
                    print(f"👥 選手数: {len(kyogisya_list)}名")
                    
                    # 各選手のデータを正規化
                    for player_data in kyogisya_list:
                        normalized_player = self._normalize_syozoku_player_data(player_data)
                        normalized_player['syozoku_name'] = syozoku_name
                        normalized_player['syozoku_id'] = syozoku_id
                        players.append(normalized_player)
                        
                else:
                    print(f"⚠️ 所属ID {syozoku_id} が見つかりませんでした")
                    
                    # デバッグ用：利用可能な所属IDを表示
                    available_ids = [syozoku.get('SYOZOKUNO', 'N/A') for syozoku in syozoku_list[:5]]
                    print(f"📋 利用可能な所属ID（最初の5つ）: {available_ids}")
            
            else:
                print(f"⚠️ JSONデータに 'SyozokuList' キーが見つかりません")
                print(f"📊 利用可能なキー: {list(json_data.keys())}")
                
            print(f"✅ JSONから {len(players)}名の選手情報を抽出")
            return players
            
        except Exception as e:
            print(f"❌ JSON解析エラー: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def _scrape_players_selenium(self, url: str, syozoku_id: str) -> List[Dict]:
        """Seleniumを使って選手情報を取得"""
        try:
            print("🤖 Seleniumで選手データを取得中...")
            self.driver.get(url)
            time.sleep(3)
            
            # AngularJSアプリケーションの読み込み待機
            self._wait_for_angular_app()
            
            # 選手データを抽出
            players = self._extract_player_elements()
            
            print(f"✅ Seleniumで {len(players)}名の選手を取得")
            return players
            
        except Exception as e:
            print(f"❌ Selenium選手取得エラー: {e}")
            return []
    
    def _scrape_players_requests(self, url: str, syozoku_id: str) -> List[Dict]:
        """requestsを使って選手情報を取得"""
        try:
            print("🔄 requestsで選手データを取得中...")
            
            import requests
            from bs4 import BeautifulSoup
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # JavaScriptファイルから選手データのJSONを探す
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.get('src'):
                    js_url = self._resolve_url(url, script['src'])
                    js_content = self._get_javascript_content(js_url)
                    if js_content:
                        players = self._extract_players_from_js(js_content, syozoku_id)
                        if players:
                            return players
            
            # インライン script から選手データを探す
            for script in script_tags:
                if script.string and 'syozoku' in script.string.lower():
                    players = self._extract_players_from_js(script.string, syozoku_id)
                    if players:
                        return players
                        
            print("⚠️ 選手データが見つかりませんでした")
            return []
            
        except Exception as e:
            print(f"❌ requests選手取得エラー: {e}")
            return []
    
    def _wait_for_angular_app(self):
        """AngularJSアプリケーションの読み込み完了を待機"""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.by import By
            
            # AngularJSアプリケーションが読み込まれるまで待機
            wait = WebDriverWait(self.driver, 15)
            
            # ng-controller要素が表示されるまで待機
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[ng-controller]")))
            
            # さらに少し待機してAngularが完全に初期化されるのを待つ
            time.sleep(2)
            
            # JavaScriptでAngularの準備状況を確認
            self.driver.execute_script("""
                return new Promise((resolve) => {
                    if (window.angular) {
                        const interval = setInterval(() => {
                            const app = angular.element(document.body);
                            if (app.scope && app.scope()) {
                                clearInterval(interval);
                                resolve(true);
                            }
                        }, 100);
                        setTimeout(() => {
                            clearInterval(interval);
                            resolve(true);
                        }, 5000);
                    } else {
                        resolve(false);
                    }
                });
            """)
            
        except Exception as e:
            print(f"⚠️ Angular待機エラー: {e}")
    
    def _extract_player_elements(self) -> List[Dict]:
        """DOM要素から選手情報を抽出"""
        players = []
        
        try:
            from selenium.webdriver.common.by import By
            
            # よくある選手リストの要素を探す
            selectors = [
                'tr[ng-repeat*="player"]',
                'div[ng-repeat*="player"]', 
                'li[ng-repeat*="player"]',
                '.player-row',
                '.athlete-row',
                'tr.result-row'
            ]
            
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"🎯 選手要素を発見: {selector} ({len(elements)}件)")
                        for element in elements:
                            player_data = self._extract_player_from_element(element)
                            if player_data:
                                players.append(player_data)
                        break
                except:
                    continue
            
            # DOM内の JSON データを探す
            if not players:
                json_data = self.driver.execute_script("""
                    // Angular scope から選手データを取得
                    const body = angular.element(document.body);
                    if (body.scope && body.scope()) {
                        const scope = body.scope();
                        return scope.pResultSyozokuPlayer || scope.players || scope.data || null;
                    }
                    return null;
                """)
                
                if json_data:
                    print(f"🎯 Angularスコープからデータを取得: {type(json_data)}")
                    if isinstance(json_data, list):
                        for item in json_data:
                            players.append(self._normalize_player_data(item))
                    elif isinstance(json_data, dict):
                        players.append(self._normalize_player_data(json_data))
            
            return players
            
        except Exception as e:
            print(f"❌ DOM要素抽出エラー: {e}")
            return []
    
    def _extract_player_from_element(self, element) -> Optional[Dict]:
        """DOM要素から個別の選手情報を抽出"""
        try:
            # テキストコンテンツを取得
            text = element.text.strip()
            if not text:
                return None
            
            # 基本的な選手情報のパターンマッチング
            player_data = {
                'raw_text': text,
                'name': self._extract_name_from_text(text),
                'year': self._extract_year_from_text(text),
                'department': self._extract_department_from_text(text),
            }
            
            # 追加のデータ属性を確認
            attrs = element.get_property('attributes')
            if attrs:
                for attr in attrs:
                    if 'data-' in attr.get('name', ''):
                        player_data[attr['name']] = attr.get('value')
            
            return player_data
            
        except Exception as e:
            print(f"⚠️ 要素解析エラー: {e}")
            return None
    
    def _extract_name_from_text(self, text: str) -> str:
        """テキストから名前を抽出"""
        # 一般的な名前パターン（ひらがな、カタカナ、漢字）
        name_pattern = r'([ぁ-んァ-ヶ一-龯\s]+)'
        match = re.search(name_pattern, text)
        return match.group(1).strip() if match else ""
    
    def _extract_year_from_text(self, text: str) -> str:
        """テキストから学年を抽出"""
        year_patterns = [r'([１-４]年|[1-4]年|[１-４]回生|[1-4]回生)', r'([BMDS][1-4])']
        for pattern in year_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        return ""
    
    def _extract_department_from_text(self, text: str) -> str:
        """テキストから学部・学科を抽出"""
        dept_pattern = r'(工学部|文学部|理学部|法学部|経済学部|医学部|薬学部|農学部|教育学部|[^年\s]*学部|[^年\s]*学科)'
        match = re.search(dept_pattern, text)
        return match.group(1) if match else ""
    
    def _resolve_url(self, base_url: str, relative_url: str) -> str:
        """相対URLを絶対URLに変換"""
        from urllib.parse import urljoin
        return urljoin(base_url, relative_url)
    
    def _get_javascript_content(self, js_url: str) -> Optional[str]:
        """JavaScriptファイルの内容を取得"""
        try:
            import requests
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            response = requests.get(js_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.text
        except:
            pass
        return None
    
    def _extract_players_from_js(self, js_content: str, syozoku_id: str) -> List[Dict]:
        """JavaScriptコードから選手データを抽出"""
        players = []
        
        try:
            # JSON形式のデータを探す
            json_patterns = [
                r'var\s+\w*[Pp]layers?\s*=\s*(\[.*?\]);',
                r'var\s+\w*[Dd]ata\s*=\s*(\{.*?\});',
                r'syozoku\s*:\s*(\{.*?\})',
                r'players\s*:\s*(\[.*?\])',
            ]
            
            for pattern in json_patterns:
                matches = re.finditer(pattern, js_content, re.DOTALL)
                for match in matches:
                    try:
                        json_str = match.group(1)
                        data = json.loads(json_str)
                        
                        if isinstance(data, list):
                            for item in data:
                                players.append(self._normalize_player_data(item))
                        elif isinstance(data, dict):
                            # 所属IDでフィルタリング
                            if syozoku_id in data:
                                syozoku_data = data[syozoku_id]
                                if isinstance(syozoku_data, list):
                                    for item in syozoku_data:
                                        players.append(self._normalize_player_data(item))
                        
                        if players:
                            break
                    except json.JSONDecodeError:
                        continue
                        
                if players:
                    break
                    
        except Exception as e:
            print(f"⚠️ JavaScript解析エラー: {e}")
            
        return players
    
    def _normalize_player_data(self, raw_data) -> Dict:
        """選手データを正規化"""
        if isinstance(raw_data, str):
            return {'raw_text': raw_data}
        elif isinstance(raw_data, dict):
            # 共通のキー名に正規化
            normalized = {}
            
            # 名前の正規化
            for key in ['name', 'player_name', 'athlete_name', 'full_name', '氏名']:
                if key in raw_data:
                    normalized['name'] = raw_data[key]
                    break
            
            # 学年の正規化  
            for key in ['year', 'grade', 'school_year', '学年']:
                if key in raw_data:
                    normalized['year'] = raw_data[key]
                    break
            
            # 学部・学科の正規化
            for key in ['department', 'faculty', 'major', '学部', '学科']:
                if key in raw_data:
                    normalized['department'] = raw_data[key]
                    break
            
            # その他のデータも保持
            for key, value in raw_data.items():
                if key not in normalized:
                    normalized[key] = value
                    
            return normalized
        else:
            return {'raw_data': raw_data}
    
    def _normalize_syozoku_player_data(self, player_data: Dict) -> Dict:
        """所属選手データを正規化"""
        try:
            # 基本情報を抽出
            kyogisyamei = player_data.get('KYOGISYAMEI', '')
            
            # 名前と学年を分離（例: "ｵｵﾂｶ ﾘｮｳ</br>大塚　遼（D2）"）
            name_parts = kyogisyamei.split('</br>')
            kana_name = name_parts[0] if len(name_parts) > 0 else ''
            
            # 漢字名と学年を分離
            full_name_part = name_parts[1] if len(name_parts) > 1 else ''
            
            # 学年の抽出（括弧内）
            import re
            year_match = re.search(r'（([^）]+)）', full_name_part)
            year = year_match.group(1) if year_match else player_data.get('GAKUNEN', '')
            
            # 漢字名の抽出（学年部分を除去）
            kanji_name = re.sub(r'（[^）]+）', '', full_name_part).strip()
            
            # 正規化されたデータ
            normalized = {
                'player_id': player_data.get('KYOGISYANO', ''),
                'kana_name': kana_name.strip(),
                'kanji_name': kanji_name,
                'full_name': f"{kana_name} {kanji_name}".strip(),
                'year': year,
                'birth_year': player_data.get('SEINEN', ''),
                'gender': player_data.get('SEIBETU', ''),
                'event': player_data.get('KYOGIMEI', ''),
                'date': player_data.get('HIDUKE', ''),
                'record': player_data.get('KIROKU', ''),
                'rank': player_data.get('JYUNI', ''),
                'timerace_rank': player_data.get('TIMERACE_JYUNI', ''),
                'wind': player_data.get('KAZE', ''),
                'comment': player_data.get('RCOMMENT', ''),
                'result_link': player_data.get('LINK', ''),
                
                # 元のデータも保持
                'raw_data': player_data
            }
            
            return normalized
            
        except Exception as e:
            print(f"⚠️ 選手データ正規化エラー: {e}")
            return {
                'raw_data': player_data,
                'error': str(e)
            }

    def save_players_data(self, players: List[Dict], output_file: str = None):
        """選手データをJSONファイルに保存"""
        if not output_file:
            output_file = f"syozoku_players_{int(time.time())}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(players, f, ensure_ascii=False, indent=2)
            print(f"💾 選手データを保存: {output_file}")
        except Exception as e:
            print(f"❌ 保存エラー: {e}")

def main():
    """メイン実行関数"""
    # デフォルトのテストURL
    test_url = "https://jaaf-shiga.com/results/2025/0712pch/shtml/TimeTable.html"
    
    # コマンドライン引数があれば使用
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    print(f"🏃‍♀️ 所属選手スクレイピング開始")
    print(f"🎯 対象URL: {test_url}")
    
    # スクレイパーを初期化
    scraper = SyozokuPlayerScraper(headless=True)
    
    try:
        # 選手データを取得
        players = scraper.scrape_syozoku_players(test_url)
        
        print(f"\n📊 結果:")
        print(f"   取得選手数: {len(players)}名")
        
        if players:
            print(f"\n👥 選手一覧:")
            for i, player in enumerate(players[:10], 1):  # 最初の10名を表示
                name = player.get('kanji_name', player.get('kana_name', '不明'))
                year = player.get('year', '不明')
                event = player.get('event', '不明')[:30] + ('...' if len(player.get('event', '')) > 30 else '')  # イベント名を短縮
                print(f"   {i:2d}. {name} ({year}) - {event}")
            
            if len(players) > 10:
                print(f"   ... 他 {len(players) - 10}名")
            
            # データを保存
            scraper.save_players_data(players)
        else:
            print("⚠️ 選手データが取得できませんでした")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # リソースのクリーンアップ
        if scraper.driver:
            scraper.driver.quit()

if __name__ == "__main__":
    main()
