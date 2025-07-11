#!/usr/bin/env python3
"""
大会結果スクレイピングスクリプト

指定された大会URLと大学名から、その大学の選手の結果をすべて取得します。

使用例:
python scrape_university_results.py "https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html" "大阪大"
"""

import sys
import os
import json
import re
import time
import requests
import pandas as pd
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

# プロジェクトのパスを追加
sys.path.append('/workspaces/Handai_TF_system/univ-athlete-db/src')
from scraper.scrape_js import JavaScriptScraper

class UniversityResultsScraper(JavaScriptScraper):
    """大会結果から特定大学の選手データを取得するクラス"""
    
    def __init__(self, headless: bool = True):
        super().__init__(headless=headless)
        
    def scrape_university_results(self, timetable_url: str, university_name: str) -> List[Dict]:
        """
        大会から特定大学の選手結果を取得
        
        Args:
            timetable_url: 大会のタイムテーブルURL
            university_name: 大学名（例: "大阪大", "大阪大学"）
            
        Returns:
            選手結果のリスト
        """
        print(f"🏆 大会結果スクレイピング開始")
        print(f"🎯 大会URL: {timetable_url}")
        print(f"🏫 対象大学: {university_name}")
        
        # Step 1: 大学IDを探す
        university_id = self._find_university_id(timetable_url, university_name)
        if not university_id:
            print(f"❌ 大学「{university_name}」のIDが見つかりませんでした")
            return []
        
        print(f"✅ 大学ID発見: {university_id}")
        
        # Step 2: 所属選手ページのURLを構築
        syozoku_url = self._build_syozoku_url(timetable_url, university_id)
        print(f"🔗 所属選手ページURL: {syozoku_url}")
        
        # Step 3: 選手データを取得
        players = self._get_players_data(syozoku_url, university_id)
        
        # Step 4: 結果データを充実化
        enriched_results = self._enrich_results_data(players, timetable_url)
        
        print(f"🎉 取得完了: {len(enriched_results)}名の選手結果を取得")
        return enriched_results
    
    def _find_university_id(self, timetable_url: str, university_name: str) -> Optional[str]:
        """大学名から大学IDを検索"""
        try:
            print(f"🔍 大学ID検索中: {university_name}")
            
            # 所属選手ページのJSONから大学IDを探す
            base_url = timetable_url.replace('TimeTable.html', 'SyozokuPlayer.html')
            json_url = base_url.replace('.html', '.json')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': timetable_url
            }
            
            response = requests.get(json_url, headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"⚠️ 所属データ取得失敗: {response.status_code}")
                return None
            
            data = response.json()
            syozoku_list = data.get('SyozokuList', [])
            
            print(f"📋 検索対象の所属数: {len(syozoku_list)}")
            
            # 大学名の正規化パターン
            normalized_names = self._normalize_university_name(university_name)
            
            # 所属リストから大学名を検索（精密マッチング）
            exact_matches = []
            partial_matches = []
            
            for syozoku in syozoku_list:
                syozoku_name = syozoku.get('SYOZOKUMEI', '')
                syozoku_id = syozoku.get('SYOZOKUNO', '')
                
                # 完全一致を最優先
                for normalized_name in normalized_names:
                    if syozoku_name == normalized_name:
                        exact_matches.append((syozoku_name, syozoku_id))
                        break
                else:
                    # 部分一致（大学系のみ対象）
                    for normalized_name in normalized_names:
                        if (normalized_name in syozoku_name and 
                            ('大学' in syozoku_name or '大' in syozoku_name) and
                            not any(word in syozoku_name for word in ['高校', '中学', '小学', '企業', '実業', 'ガス', '電力', '銀行', '会社'])):
                            partial_matches.append((syozoku_name, syozoku_id))
                            break
            
            # 完全一致があれば最優先
            if exact_matches:
                syozoku_name, syozoku_id = exact_matches[0]
                print(f"🎯 大学発見（完全一致）: {syozoku_name} (ID: {syozoku_id})")
                return syozoku_id
            
            # 部分一致があれば次の候補
            if partial_matches:
                syozoku_name, syozoku_id = partial_matches[0]
                print(f"🎯 大学発見（部分一致）: {syozoku_name} (ID: {syozoku_id})")
                if len(partial_matches) > 1:
                    print("⚠️ 複数の候補が見つかりました:")
                    for name, id_ in partial_matches[:3]:
                        print(f"   - {name} (ID: {id_})")
                return syozoku_id
            
            # 見つからない場合、利用可能な所属を表示
            print(f"❌ 大学「{university_name}」が見つかりません")
            print("📋 利用可能な所属:")
            for i, syozoku in enumerate(syozoku_list[:10]):
                syozoku_name = syozoku.get('SYOZOKUMEI', '')
                syozoku_id = syozoku.get('SYOZOKUNO', '')
                print(f"   {i+1:2d}. {syozoku_name} (ID: {syozoku_id})")
            
            if len(syozoku_list) > 10:
                print(f"   ... 他 {len(syozoku_list) - 10}件")
            
            return None
            
        except Exception as e:
            print(f"❌ 大学ID検索エラー: {e}")
            return None
    
    def _normalize_university_name(self, university_name: str) -> List[str]:
        """大学名を正規化（複数パターン生成）"""
        patterns = []
        
        # 入力された名前をそのまま
        patterns.append(university_name)
        
        # 「大」→「大学」の変換
        if university_name.endswith('大'):
            patterns.append(university_name + '学')
        
        # 「大学」→「大」の変換
        if university_name.endswith('大学'):
            patterns.append(university_name[:-1])
        
        # 重複を除去
        return list(set(patterns))
    
    def _build_syozoku_url(self, timetable_url: str, university_id: str) -> str:
        """所属選手ページのURLを構築"""
        base_url = timetable_url.replace('TimeTable.html', 'SyozokuPlayer.html')
        return f"{base_url}#!#syozoku_{university_id}"
    
    def _get_players_data(self, syozoku_url: str, university_id: str) -> List[Dict]:
        """所属選手ページから選手データを取得"""
        try:
            # JSONデータを直接取得
            json_data = self._try_get_json_data(syozoku_url)
            if json_data:
                return self._extract_players_from_json(json_data, university_id)
            else:
                print("⚠️ JSONデータ取得失敗、フォールバック処理を実行")
                return []
                
        except Exception as e:
            print(f"❌ 選手データ取得エラー: {e}")
            return []
    
    def _try_get_json_data(self, url: str) -> Optional[Dict]:
        """JSONデータの直接取得"""
        try:
            base_url = url.split('#')[0]
            json_url = base_url.replace('.html', '.json')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': url
            }
            
            response = requests.get(json_url, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"❌ JSON取得エラー: {e}")
            return None
    
    def _extract_players_from_json(self, json_data: Dict, university_id: str) -> List[Dict]:
        """JSONデータから選手情報を抽出"""
        players = []
        
        try:
            if 'SyozokuList' in json_data:
                syozoku_list = json_data['SyozokuList']
                
                # 指定された大学IDの選手データを探す
                target_syozoku = None
                for syozoku in syozoku_list:
                    if str(syozoku.get('SYOZOKUNO', '')) == str(university_id):
                        target_syozoku = syozoku
                        break
                
                if target_syozoku:
                    syozoku_name = target_syozoku.get('SYOZOKUMEI', '不明')
                    kyogisya_list = target_syozoku.get('KYOGISYA', [])
                    
                    print(f"🏫 所属名: {syozoku_name}")
                    print(f"👥 選手数: {len(kyogisya_list)}名")
                    
                    # 各選手のデータを正規化
                    for player_data in kyogisya_list:
                        normalized_player = self._normalize_player_data(player_data)
                        normalized_player['syozoku_name'] = syozoku_name
                        normalized_player['syozoku_id'] = university_id
                        players.append(normalized_player)
                        
            return players
            
        except Exception as e:
            print(f"❌ JSON解析エラー: {e}")
            return []
    
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
    
    def _enrich_results_data(self, players: List[Dict], timetable_url: str) -> List[Dict]:
        """結果データを充実化（追加情報を付与）"""
        try:
            # 大会情報を取得
            competition_info = self._get_competition_info(timetable_url)
            
            # 各選手データに大会情報を追加
            enriched_results = []
            for player in players:
                enriched_player = player.copy()
                enriched_player.update(competition_info)
                enriched_results.append(enriched_player)
            
            return enriched_results
            
        except Exception as e:
            print(f"⚠️ データ充実化エラー: {e}")
            return players
    
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
                if part.startswith('html') and len(part) > 4:
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
    
    def save_results_data(self, results: List[Dict], university_name: str, output_file: str = None):
        """結果データをJSONファイルに保存"""
        if not output_file:
            # ファイル名を生成
            safe_univ_name = re.sub(r'[^\w\-_.]', '_', university_name)
            timestamp = int(time.time())
            output_file = f"university_results_{safe_univ_name}_{timestamp}.json"
        
        try:
            # 保存データの構造
            save_data = {
                'university_name': university_name,
                'total_athletes': len(results),
                'scraping_timestamp': int(time.time()),
                'scraping_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'results': results
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print(f"💾 結果データを保存: {output_file}")
            
            # 結果の概要を表示
            self._display_results_summary(results)
            
        except Exception as e:
            print(f"❌ 保存エラー: {e}")
    
    def _display_results_summary(self, results: List[Dict]):
        """結果の概要を表示"""
        if not results:
            return
        
        print(f"\n📊 結果概要:")
        
        # 種目別集計
        events = {}
        genders = {}
        record_types = {}
        
        for result in results:
            event = result.get('event_name', '不明')
            gender = result.get('gender', '不明')
            record_type = result.get('record_type', '不明')
            
            events[event] = events.get(event, 0) + 1
            genders[gender] = genders.get(gender, 0) + 1
            record_types[record_type] = record_types.get(record_type, 0) + 1
        
        print(f"\n🏃‍♂️ 性別:")
        for gender, count in genders.items():
            print(f"   {gender}: {count}名")
        
        print(f"\n🏆 主要種目 (上位5種目):")
        sorted_events = sorted(events.items(), key=lambda x: x[1], reverse=True)
        for event, count in sorted_events[:5]:
            print(f"   {event}: {count}名")
        
        print(f"\n📋 記録状況:")
        for record_type, count in record_types.items():
            if record_type in ['DNS', 'DNF', 'DQ']:
                print(f"   {record_type}: {count}名")
    
    def results_to_dataframe(self, results: List[Dict]) -> pd.DataFrame:
        """結果データをpandas DataFrameに変換"""
        if not results:
            return pd.DataFrame()
        
        # DataFrameに適した形式に変換
        df_data = []
        for result in results:
            df_row = {
                '選手ID': result.get('player_id', ''),
                '選手名（かな）': result.get('kana_name', ''),
                '選手名（漢字）': result.get('kanji_name', ''),
                '年度': result.get('year', ''),
                '生年': result.get('birth_year', ''),
                '性別': result.get('gender', ''),
                '競技名': result.get('event_name', ''),
                '競技種別': result.get('event_type', ''),
                '記録': result.get('record', ''),
                '順位': result.get('rank', ''),
                '風速': result.get('wind', ''),
                'コメント': result.get('comment', ''),
                '日付': result.get('competition_date', ''),
                'DNS': result.get('is_dns', False),
                'DNF': result.get('is_dnf', False),
                'DQ': result.get('is_dq', False)
            }
            df_data.append(df_row)
        
        df = pd.DataFrame(df_data)
        
        # データ型の調整
        if '生年' in df.columns:
            df['生年'] = pd.to_numeric(df['生年'], errors='coerce')
        if '日付' in df.columns:
            df['日付'] = pd.to_datetime(df['日付'], errors='coerce')
            
        return df

def scrape_univ_results_to_dataframe(timetable_url: str, university_name: str, headless: bool = True) -> Tuple[str, Optional[pd.DataFrame]]:
    """
    選手の結果を取得してDataFrameとして返す
    
    Args:
        timetable_url: 大会のタイムテーブルURL
        player_name: 選手名
        headless: Seleniumをヘッドレスモードで実行するか
        
    Returns:
        Tuple[str, Optional[pd.DataFrame]]: (大会名, 結果DataFrame)
    """
    print(f"🏆 大学別結果取得システム")
    print(f"📅 対象大会: {timetable_url}")
    print(f"🏫 対象大学: {university_name}")
    print()
    
    # スクレイパーを初期化
    scraper = UniversityResultsScraper(headless=True)
    
    try:
        # 大学の結果を取得
        results = scraper.scrape_university_results(timetable_url, university_name)
        
        if results:
            print(f"\n✅ 取得成功: {len(results)}名の選手結果を取得")
            
            # DataFrame出力オプション
            try:
                df = scraper.results_to_dataframe(results)
                print(df[df['記録']==""])  # 記録がある選手のみ表示
                #csv_filename = f"university_results_{university_name}_{int(time.time())}.csv"
                #df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                #print(f"📊 CSVファイルも保存: {csv_filename}")
                
                # 簡単な統計表示
                print(f"\n📈 DataFrame概要:")
                print(f"   行数: {len(df)}")
                print(f"   列数: {len(df.columns)}")
                if len(df) > 0:
                    print(f"   競技種目数: {df['event_name'].nunique()}")
            except Exception as e:
                print(f"⚠️ DataFrame処理エラー: {e}")
            
            # JSONデータを保存
            scraper.save_results_data(results, university_name)
        else:
            print("❌ 結果データが取得できませんでした")
            
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # リソースのクリーンアップ
        if scraper.driver:
            scraper.driver.quit()




def main():
    """メイン実行関数"""
    # コマンドライン引数のチェック
    if len(sys.argv) < 3:
        print("使用方法:")
        print(f"python {sys.argv[0]} <大会URL> <大学名>")
        print("")
        print("例:")
        print(f'python {sys.argv[0]} "https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html" "大阪大"')
        sys.exit(1)
    
    timetable_url = sys.argv[1]
    university_name = sys.argv[2]
    
    print(f"🏆 大学別結果取得システム")
    print(f"📅 対象大会: {timetable_url}")
    print(f"🏫 対象大学: {university_name}")
    print()
    
    # スクレイパーを初期化
    scraper = UniversityResultsScraper(headless=True)
    
    try:
        # 大学の結果を取得
        results = scraper.scrape_university_results(timetable_url, university_name)
        
        if results:
            print(f"\n✅ 取得成功: {len(results)}名の選手結果を取得")
            
            # DataFrame出力オプション
            try:
                df = scraper.results_to_dataframe(results)
                print(df[df['記録']==""])  # 記録がある選手のみ表示
                csv_filename = f"university_results_{university_name}_{int(time.time())}.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"📊 CSVファイルも保存: {csv_filename}")
                
                # 簡単な統計表示
                print(f"\n📈 DataFrame概要:")
                print(f"   行数: {len(df)}")
                print(f"   列数: {len(df.columns)}")
                if len(df) > 0:
                    print(f"   競技種目数: {df['event_name'].nunique()}")
            except Exception as e:
                print(f"⚠️ DataFrame処理エラー: {e}")
            
            # JSONデータを保存
            scraper.save_results_data(results, university_name)
        else:
            print("❌ 結果データが取得できませんでした")
            
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
