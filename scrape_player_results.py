#!/usr/bin/env python3
"""
選手別結果スクレイピングスクリプト

指定された大会URLと選手名から、その選手の結果をすべて取得します。

使用例:
python scrape_player_results.py "http://nagoyatf.xyz/chita2/nans21v/shtml/TimeTable.html" "吉田隼人"
"""

import sys
import os
import json
import re
import time
import requests
import pandas as pd
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

# プロジェクトのパスを追加
sys.path.append('/workspaces/Handai_TF_system/univ-athlete-db/src')
from scraper.scrape_js import JavaScriptScraper

class PlayerResultsScraper(JavaScriptScraper):
    """大会結果から特定選手のデータを取得するクラス"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
    
    def get_meet_name(self, timetable_url: str) -> str:
        """
        大会名を取得
        
        Args:
            timetable_url: 大会のタイムテーブルURL
            
        Returns:
            大会名
        """
        try:
            # Seleniumが利用可能な場合
            if self.driver:
                # ベースURLを取得
                base_url = timetable_url.rsplit('/', 1)[0] + '/'
                
                # ページにアクセスして大会名を取得
                self.driver.get(timetable_url)
                
                # 大会名の取得を試行（様々なセレクターを試す）
                meet_name_selectors = [
                    'h1',  # メインタイトル
                    '.title',  # タイトルクラス
                    '#title',  # タイトルID
                    'title',  # ページタイトル
                    '.meet-title',  # 大会タイトル
                    '.header h1',  # ヘッダー内のh1
                    '.content h1',  # コンテンツ内のh1
                ]
                
                meet_name = None
                
                for selector in meet_name_selectors:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if element and element.text.strip():
                            meet_name = element.text.strip()
                            # "TimeTable"など関係ない文字列が含まれていない場合に採用
                            if 'TimeTable' not in meet_name and len(meet_name) > 5:
                                break
                    except:
                        continue
                
                # Seleniumで取得できない場合は、ページタイトルから取得
                if not meet_name:
                    try:
                        meet_name = self.driver.title
                        if meet_name and meet_name != "TimeTable":
                            # タイトルをクリーンアップ
                            meet_name = meet_name.replace("TimeTable", "").strip()
                            meet_name = re.sub(r'\s+', ' ', meet_name)
                    except:
                        pass
                        
                if meet_name:
                    return meet_name
            
            # フォールバックモード: requestsでページを取得
            try:
                import requests
                from bs4 import BeautifulSoup
                
                response = requests.get(timetable_url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 様々なセレクターで大会名を検索
                meet_name_selectors = ['h1', '.title', '#title', 'title']
                
                for selector in meet_name_selectors:
                    element = soup.select_one(selector)
                    if element and element.get_text().strip():
                        meet_name = element.get_text().strip()
                        # テンプレート変数や関係ない文字列が含まれていない場合に採用
                        if ('TimeTable' not in meet_name and 
                            '{{' not in meet_name and 
                            len(meet_name) > 5 and 
                            len(meet_name) < 100):
                            return meet_name
                
                # タイトルタグから取得
                title_element = soup.find('title')
                if title_element:
                    title = title_element.get_text().strip()
                    if (title and title != "TimeTable" and 
                        '{{' not in title and 
                        len(title) > 5 and len(title) < 100):
                        title = title.replace("TimeTable", "").strip()
                        title = re.sub(r'\s+', ' ', title)
                        if title:
                            return title
                            
            except Exception as e:
                print(f"⚠️ requests/BeautifulSoupでの大会名取得に失敗: {e}")
            
            # URLから推測（より詳細な解析）
            try:
                url_parts = timetable_url.split('/')
                
                # ドメイン名から地域を推測
                domain_info = ""
                if 'nagoyatf' in timetable_url:
                    domain_info = "名古屋"
                elif 'osaka' in timetable_url or 'handai' in timetable_url:
                    domain_info = "大阪"
                elif 'kansai' in timetable_url:
                    domain_info = "関西"
                
                # URLのパス部分から大会名を推測
                path_parts = []
                for part in url_parts:
                    if part and part not in ['http:', 'https:', '', 'shtml', 'TimeTable.html', 'html']:
                        # ドメイン名をスキップ
                        if '.' not in part or part.endswith('.xyz') or part.endswith('.com'):
                            if not part.endswith('.xyz') and not part.endswith('.com'):
                                path_parts.append(part)
                
                if path_parts:
                    # 最後の意味のある部分を使用
                    meet_id = path_parts[-1]
                    
                    # よくあるパターンで変換
                    if 'nans' in meet_id.lower():
                        year_match = re.search(r'(\d{2})v?$', meet_id)
                        if year_match:
                            year = "20" + year_match.group(1)
                            return f"{domain_info}学生陸上競技会 {year}"
                    
                    return f"{domain_info}陸上競技大会 ({meet_id})"
                
                return f"{domain_info}陸上競技大会" if domain_info else "陸上競技大会"
                
            except Exception as e:
                print(f"⚠️ URLからの大会名推測に失敗: {e}")
            
            return "不明な大会"
            
        except Exception as e:
            print(f"⚠️ 大会名の取得に失敗: {e}")
            return "不明な大会"
        
    def scrape_player_results(self, timetable_url: str, player_name: str) -> List[Dict]:
        """
        大会から特定選手の結果を取得
        
        Args:
            timetable_url: 大会のタイムテーブルURL
            player_name: 選手名（例: "吉田隼人", "大塚遼"）
            
        Returns:
            選手結果のリスト
        """
        print(f"🏃‍♂️ 選手別結果スクレイピング開始")
        print(f"🎯 大会URL: {timetable_url}")
        print(f"👤 対象選手: {player_name}")
        
        # Step 1: 全所属の選手データを取得
        all_players_data = self._get_all_players_data(timetable_url)
        if not all_players_data:
            print("❌ 選手データの取得に失敗しました")
            return []
        
        # Step 2: 選手名で検索
        matching_results = self._search_player_by_name(all_players_data, player_name)
        
        # Step 3: 結果データを充実化
        enriched_results = self._enrich_player_results(matching_results, timetable_url)
        
        print(f"🎉 取得完了: {len(enriched_results)}件の結果を取得")
        return enriched_results
    
    def _get_all_players_data(self, timetable_url: str) -> List[Dict]:
        """全所属の選手データを取得"""
        try:
            print(f"🔍 全選手データを取得中...")
            
            # 所属選手ページのJSONを取得
            base_url = timetable_url.replace('TimeTable.html', 'SyozokuPlayer.html')
            json_url = base_url.replace('.html', '.json')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': timetable_url
            }
            
            response = requests.get(json_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ 所属データ取得失敗: {response.status_code}")
                return []
            
            data = response.json()
            syozoku_list = data.get('SyozokuList', [])
            
            print(f"📋 対象所属数: {len(syozoku_list)}")
            
            # 全所属から選手データを収集
            all_players = []
            total_athletes = 0
            
            for syozoku in syozoku_list:
                syozoku_name = syozoku.get('SYOZOKUMEI', '不明')
                syozoku_id = syozoku.get('SYOZOKUNO', '')
                kyogisya_list = syozoku.get('KYOGISYA', [])
                
                total_athletes += len(kyogisya_list)
                
                # 各選手のデータを正規化
                for player_data in kyogisya_list:
                    normalized_player = self._normalize_player_data(player_data)
                    normalized_player['syozoku_name'] = syozoku_name
                    normalized_player['syozoku_id'] = syozoku_id
                    all_players.append(normalized_player)
            
            print(f"✅ 全選手データ取得完了: {total_athletes}名")
            return all_players
            
        except Exception as e:
            print(f"❌ 全選手データ取得エラー: {e}")
            return []
    
    def _search_player_by_name(self, all_players: List[Dict], target_name: str) -> List[Dict]:
        """選手名で検索"""
        try:
            print(f"🔍 選手名検索中: {target_name}")
            
            # 検索パターンを生成
            search_patterns = self._generate_name_patterns(target_name)
            print(f"🔍 検索パターン: {search_patterns}")
            
            matching_results = []
            name_matches = {}  # 重複チェック用
            
            for player in all_players:
                # 複数の名前フィールドをチェック
                player_names = [
                    player.get('kanji_name', ''),
                    player.get('kana_name', ''),
                    player.get('full_name', ''),
                ]
                
                # 各検索パターンと照合
                found_match = False
                for pattern in search_patterns:
                    for player_name in player_names:
                        if self._name_matches(pattern, player_name):
                            # 重複チェック（同じ選手の複数種目を区別）
                            match_key = f"{player.get('kanji_name', '')}_{player.get('syozoku_name', '')}_{player.get('event_full', '')}"
                            
                            if match_key not in name_matches:
                                name_matches[match_key] = True
                                matching_results.append(player)
                                print(f"🎯 選手発見: {player.get('kanji_name', '')} ({player.get('syozoku_name', '')}) - {player.get('event_name', '')}")
                            found_match = True
                            break
                    if found_match:
                        break
            
            if not matching_results:
                print(f"❌ 選手「{target_name}」が見つかりませんでした")
                self._suggest_similar_names(all_players, target_name)
            else:
                print(f"✅ {len(matching_results)}件の結果を発見")
            
            return matching_results
            
        except Exception as e:
            print(f"❌ 選手検索エラー: {e}")
            return []
    
    def _generate_name_patterns(self, target_name: str) -> List[str]:
        """選手名の検索パターンを生成"""
        patterns = []
        
        # 入力された名前をそのまま
        patterns.append(target_name)
        
        # スペースを除去
        patterns.append(target_name.replace(' ', '').replace('　', ''))
        
        # ひらがな・カタカナ変換
        hiragana_name = self._convert_katakana_to_hiragana(target_name)
        katakana_name = self._convert_hiragana_to_katakana(target_name)
        
        if hiragana_name != target_name:
            patterns.append(hiragana_name)
        if katakana_name != target_name:
            patterns.append(katakana_name)
        
        # 姓名分離パターン（スペースがある場合）
        if ' ' in target_name or '　' in target_name:
            name_parts = re.split(r'[\s　]+', target_name)
            if len(name_parts) >= 2:
                patterns.append(name_parts[0])  # 姓のみ
                patterns.append(name_parts[1])  # 名のみ
        
        # 重複を除去
        return list(set([p for p in patterns if p.strip()]))
    
    def _convert_katakana_to_hiragana(self, text: str) -> str:
        """カタカナをひらがなに変換"""
        result = ""
        for char in text:
            if 'ァ' <= char <= 'ヶ':
                result += chr(ord(char) - ord('ァ') + ord('ぁ'))
            else:
                result += char
        return result
    
    def _convert_hiragana_to_katakana(self, text: str) -> str:
        """ひらがなをカタカナに変換"""
        result = ""
        for char in text:
            if 'ぁ' <= char <= 'ゖ':
                result += chr(ord(char) - ord('ぁ') + ord('ァ'))
            else:
                result += char
        return result
    
    def _name_matches(self, pattern: str, player_name: str) -> bool:
        """名前パターンの照合"""
        if not pattern or not player_name:
            return False
        
        # 完全一致
        if pattern == player_name:
            return True
        
        # 部分一致（両方向）
        if pattern in player_name or player_name in pattern:
            return True
        
        # スペース・記号を除去して比較
        clean_pattern = re.sub(r'[\s　\-\(\)（）]', '', pattern)
        clean_player = re.sub(r'[\s　\-\(\)（）]', '', player_name)
        
        if clean_pattern == clean_player:
            return True
        
        if clean_pattern in clean_player or clean_player in clean_pattern:
            return True
        
        return False
    
    def _suggest_similar_names(self, all_players: List[Dict], target_name: str):
        """類似する選手名を提案"""
        try:
            print("💡 類似する選手名:")
            
            # 名前の一部が一致する選手を探す
            suggestions = []
            target_chars = set(target_name)
            
            for player in all_players:
                kanji_name = player.get('kanji_name', '')
                if kanji_name and len(kanji_name) > 1:
                    player_chars = set(kanji_name)
                    # 文字の一致度を計算
                    common_chars = target_chars & player_chars
                    if len(common_chars) >= 1 and len(common_chars) / len(target_chars) >= 0.5:
                        suggestions.append((kanji_name, player.get('syozoku_name', '')))
            
            # 重複除去
            unique_suggestions = list(set(suggestions))
            
            for i, (name, syozoku) in enumerate(unique_suggestions[:10], 1):
                print(f"   {i:2d}. {name} ({syozoku})")
            
            if len(unique_suggestions) > 10:
                print(f"   ... 他 {len(unique_suggestions) - 10}名")
                
        except Exception as e:
            print(f"⚠️ 類似名前提案エラー: {e}")
    
    def _normalize_player_data(self, player_data: Dict) -> Dict:
        """選手データを正規化"""
        try:
            # 基本情報を抽出
            kyogisyamei = player_data.get('KYOGISYAMEI', '')
            
            # 名前と学年を分離（例: "ｵｵﾂｶ ﾘｮｳ</br>大塚　遼（D2）"）
            name_parts = kyogisyamei.split('</br>')
            kana_name = name_parts[0] if len(name_parts) > 0 else ''
            
            # 漢字名と学年を分離
            full_name_part = name_parts[1] if len(name_parts) > 1 else ''
            
            # 学年の抽出（括弧内）
            year_match = re.search(r'（([^）]+)）', full_name_part)
            year = year_match.group(1) if year_match else player_data.get('GAKUNEN', '')
            
            # 漢字名の抽出（学年部分を除去）
            kanji_name = re.sub(r'（[^）]+）', '', full_name_part).strip()
            
            # 種目情報の詳細解析
            event_info = self._parse_event_info(player_data.get('KYOGIMEI', ''))
            
            # 記録情報の詳細解析
            record_info = self._parse_record_info(
                player_data.get('KIROKU', ''),
                player_data.get('JYUNI', ''),
                player_data.get('RCOMMENT', '')
            )
            
            # 正規化されたデータ
            normalized = {
                'player_id': player_data.get('KYOGISYANO', ''),
                'kana_name': kana_name.strip(),
                'kanji_name': kanji_name,
                'full_name': f"{kana_name} {kanji_name}".strip(),
                'year': year,
                'birth_year': player_data.get('SEINEN', ''),
                'gender': player_data.get('SEIBETU', ''),
                
                # 種目情報
                'event_full': player_data.get('KYOGIMEI', ''),
                'event_category': event_info.get('category', ''),
                'event_name': event_info.get('name', ''),
                'event_type': event_info.get('type', ''),
                
                # 結果情報
                'record': player_data.get('KIROKU', ''),
                'rank': player_data.get('JYUNI', ''),
                'timerace_rank': player_data.get('TIMERACE_JYUNI', ''),
                'wind': player_data.get('KAZE', ''),
                'comment': player_data.get('RCOMMENT', ''),
                'result_link': player_data.get('LINK', ''),
                
                # 記録情報の解析結果
                'record_type': record_info.get('type', ''),
                'record_value': record_info.get('value', ''),
                'is_dns': record_info.get('is_dns', False),
                'is_dnf': record_info.get('is_dnf', False),
                'is_dq': record_info.get('is_dq', False),
                
                # 大会情報
                'date': player_data.get('HIDUKE', ''),
                'competition_date': self._format_date(player_data.get('HIDUKE', '')),
                
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
    
    def _parse_event_info(self, event_string: str) -> Dict:
        """種目情報を詳細解析"""
        try:
            event_info = {
                'category': '',
                'name': '',
                'type': ''
            }
            
            if not event_string:
                return event_info
            
            # カテゴリ抽出（オープン、一般など）
            if 'ｵｰﾌﾟﾝ' in event_string:
                event_info['category'] = 'オープン'
            elif '一般' in event_string:
                event_info['category'] = '一般'
            
            # 種目名抽出
            # 例: "ｵｰﾌﾟﾝ男子100m　ﾀｲﾑﾚｰｽ20組"
            event_parts = event_string.split('　')
            if len(event_parts) > 0:
                main_event = event_parts[0]
                # "ｵｰﾌﾟﾝ男子100m" から "男子100m" を抽出
                if 'ｵｰﾌﾟﾝ' in main_event:
                    event_info['name'] = main_event.replace('ｵｰﾌﾟﾝ', '').strip()
                elif '一般' in main_event:
                    event_info['name'] = main_event.replace('一般', '').strip()
                else:
                    event_info['name'] = main_event
            
            # 競技形式抽出（決勝、予選、タイムレースなど）
            if 'ﾀｲﾑﾚｰｽ' in event_string:
                event_info['type'] = 'タイムレース'
            elif '決' in event_string and '勝' in event_string:
                event_info['type'] = '決勝'
            elif '予' in event_string and '選' in event_string:
                event_info['type'] = '予選'
            elif '準決勝' in event_string:
                event_info['type'] = '準決勝'
            
            return event_info
            
        except Exception as e:
            print(f"⚠️ 種目情報解析エラー: {e}")
            return {'category': '', 'name': '', 'type': ''}
    
    def _parse_record_info(self, record: str, rank: str, comment: str) -> Dict:
        """記録情報を詳細解析"""
        try:
            record_info = {
                'type': '',
                'value': record,
                'is_dns': False,
                'is_dnf': False,
                'is_dq': False
            }
            
            # 特殊記録の判定
            if 'DNS' in comment.upper():
                record_info['is_dns'] = True
                record_info['type'] = 'DNS'
            elif 'DNF' in comment.upper():
                record_info['is_dnf'] = True
                record_info['type'] = 'DNF'
            elif 'DQ' in comment.upper():
                record_info['is_dq'] = True
                record_info['type'] = 'DQ'
            elif record:
                # 記録のタイプを判定
                if ':' in record:
                    record_info['type'] = 'time'  # タイム記録
                elif 'm' in record.lower():
                    record_info['type'] = 'distance'  # 距離記録
                elif 'p' in record.lower():
                    record_info['type'] = 'points'  # ポイント記録
                else:
                    record_info['type'] = 'other'
            
            return record_info
            
        except Exception as e:
            print(f"⚠️ 記録情報解析エラー: {e}")
            return {'type': '', 'value': record, 'is_dns': False, 'is_dnf': False, 'is_dq': False}
    
    def _format_date(self, date_string: str) -> str:
        """日付フォーマットを整形"""
        try:
            if len(date_string) == 8:  # YYYYMMDD形式
                year = date_string[:4]
                month = date_string[4:6]
                day = date_string[6:8]
                return f"{year}-{month}-{day}"
            return date_string
        except:
            return date_string
    
    def _enrich_player_results(self, results: List[Dict], timetable_url: str) -> List[Dict]:
        """選手結果データを充実化（追加情報を付与）"""
        try:
            # 大会情報を取得
            competition_info = self._get_competition_info(timetable_url)
            
            # 各結果データに大会情報を追加
            enriched_results = []
            for result in results:
                enriched_result = result.copy()
                enriched_result.update(competition_info)
                enriched_results.append(enriched_result)
            
            return enriched_results
            
        except Exception as e:
            print(f"⚠️ データ充実化エラー: {e}")
            return results
    
    def _get_competition_info(self, timetable_url: str) -> Dict:
        """大会情報を取得"""
        try:
            # URLから大会情報を推測
            parsed_url = urlparse(timetable_url)
            path_parts = parsed_url.path.split('/')
            
            competition_info = {
                'competition_url': timetable_url,
                'competition_id': '',
                'competition_name': '',
                'competition_year': '',
                'scraping_timestamp': int(time.time())
            }
            
            # URLパスから大会IDを抽出
            for part in path_parts:
                if 'html' in part.lower() or 'nans' in part.lower():
                    competition_info['competition_id'] = part
                    # 年度を抽出
                    year_match = re.search(r'(\d{4})', part)
                    if year_match:
                        competition_info['competition_year'] = year_match.group(1)
                    break
            
            return competition_info
            
        except Exception as e:
            print(f"⚠️ 大会情報取得エラー: {e}")
            return {}
    
    def save_player_results(self, results: List[Dict], player_name: str, output_file: str = None):
        """選手結果データをJSONファイルに保存"""
        if not output_file:
            # ファイル名を生成
            safe_player_name = re.sub(r'[^\w\-_.]', '_', player_name)
            timestamp = int(time.time())
            output_file = f"player_results_{safe_player_name}_{timestamp}.json"
        
        try:
            # 保存データの構造
            save_data = {
                'player_name': player_name,
                'total_results': len(results),
                'scraping_timestamp': int(time.time()),
                'scraping_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'results': results
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"💾 結果データを保存: {output_file}")
            
            # 結果の概要を表示
            self._display_player_summary(results, player_name)
            
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
    
    def _display_player_summary(self, results: List[Dict], player_name: str):
        """選手結果の概要を表示"""
        if not results:
            return
        
        print(f"\n📊 {player_name}さんの結果概要:")
        
        # 所属の確認
        syozokus = set()
        events = {}
        records_with_time = []
        
        for result in results:
            syozoku = result.get('syozoku_name', '不明')
            event = result.get('event_name', '不明')
            record = result.get('record', '')
            
            syozokus.add(syozoku)
            events[event] = events.get(event, 0) + 1
            
            if record and not result.get('is_dns', False):
                records_with_time.append({
                    'event': event,
                    'record': record,
                    'rank': result.get('rank', ''),
                    'type': result.get('event_type', '')
                })
        
        print(f"🏫 所属: {', '.join(syozokus)}")
        print(f"🏃‍♂️ 出場種目数: {len(events)}")
        
        print(f"\n🏆 種目別出場回数:")
        for event, count in sorted(events.items()):
            print(f"   {event}: {count}回")
        
        if records_with_time:
            print(f"\n⏱️ 記録一覧:")
            for i, record in enumerate(records_with_time, 1):
                rank_info = f" (順位: {record['rank']})" if record['rank'] else ""
                type_info = f" [{record['type']}]" if record['type'] else ""
                print(f"   {i:2d}. {record['event']}: {record['record']}{rank_info}{type_info}")
        
        # DNS/DNF/DQの統計
        dns_count = sum(1 for r in results if r.get('is_dns', False))
        dnf_count = sum(1 for r in results if r.get('is_dnf', False))
        dq_count = sum(1 for r in results if r.get('is_dq', False))
        
        if dns_count + dnf_count + dq_count > 0:
            print(f"\n📋 特殊記録:")
            if dns_count > 0:
                print(f"   DNS (欠場): {dns_count}回")
            if dnf_count > 0:
                print(f"   DNF (途中棄権): {dnf_count}回")
            if dq_count > 0:
                print(f"   DQ (失格): {dq_count}回")


def scrape_player_results_to_dataframe(timetable_url: str, player_name: str, headless: bool = True) -> Tuple[str, Optional[pd.DataFrame]]:
    """
    選手の結果を取得してDataFrameとして返す
    
    Args:
        timetable_url: 大会のタイムテーブルURL
        player_name: 選手名
        headless: Seleniumをヘッドレスモードで実行するか
        
    Returns:
        Tuple[str, Optional[pd.DataFrame]]: (大会名, 結果DataFrame)
    """
    scraper = None
    try:
        scraper = PlayerResultsScraper(headless=headless)
        
        # 大会名を取得
        meet_name = scraper.get_meet_name(timetable_url)
        print(f"🏆 大会名: {meet_name}")
        
        # 選手の結果を取得
        results = scraper.scrape_player_results(timetable_url, player_name)
        
        if not results:
            print("❌ 結果データが取得できませんでした")
            return meet_name, None
        
        print(f"✅ 取得成功: {len(results)}件の結果を取得")
        
        # DataFrameに変換
        df = pd.DataFrame(results)
        
        # カラムの順序を整理
        columns_order = [
            'syozoku_name', 'player_name', 'event_name', 'event_type',
            'record', 'rank', 'lane', 'bib', 'wind', 'heat_info',
            'is_dns', 'is_dnf', 'is_dq', 'is_final', 'is_preliminary'
        ]
        
        # 存在するカラムのみを使用
        available_columns = [col for col in columns_order if col in df.columns]
        df = df[available_columns]
        
        # 基本統計を表示
        print(f"\n📊 {player_name}さんの結果概要:")
        print(f"🏫 所属: {', '.join(df['syozoku_name'].unique()) if 'syozoku_name' in df.columns else '不明'}")
        print(f"🏃‍♂️ 出場種目数: {df['event_name'].nunique() if 'event_name' in df.columns else 0}")
        
        if 'event_name' in df.columns:
            event_counts = df['event_name'].value_counts()
            print(f"\n🏆 種目別出場回数:")
            for event, count in event_counts.items():
                print(f"   {event}: {count}回")
        
        return meet_name, df
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return "不明な大会", None
        
    finally:
        if scraper and scraper.driver:
            scraper.driver.quit()


def main():
    """コマンドライン実行用のメイン関数"""
    # コマンドライン引数のチェック
    if len(sys.argv) < 3:
        print("使用方法:")
        print(f"python {sys.argv[0]} <大会URL> <選手名>")
        print("")
        print("例:")
        print(f'python {sys.argv[0]} "http://nagoyatf.xyz/chita2/nans21v/shtml/TimeTable.html" "吉田隼人"')
        print(f'python {sys.argv[0]} "http://nagoyatf.xyz/chita2/nans21v/shtml/TimeTable.html" "大塚遼"')
        sys.exit(1)
    
    timetable_url = sys.argv[1]
    player_name = sys.argv[2]
    
    print(f"👤 選手別結果取得システム")
    print(f"📅 対象大会: {timetable_url}")
    print(f"🏃‍♂️ 対象選手: {player_name}")
    print()
    
    try:
        # 新しいDataFrame対応関数を使用
        meet_name, df = scrape_player_results_to_dataframe(timetable_url, player_name)
        
        if df is not None:
            # データを従来形式でも保存（互換性のため）
            results = df.to_dict('records')
            scraper = PlayerResultsScraper(headless=True)
            try:
                scraper.save_player_results(results, player_name)
            finally:
                if scraper.driver:
                    scraper.driver.quit()
            
            # DataFrameの基本情報を表示
            print(f"\n📋 DataFrameの詳細:")
            print(f"   行数: {len(df)}")
            print(f"   列数: {len(df.columns)}")
            print(f"   列名: {', '.join(df.columns.tolist())}")
            
        else:
            print("❌ 結果データが取得できませんでした")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
