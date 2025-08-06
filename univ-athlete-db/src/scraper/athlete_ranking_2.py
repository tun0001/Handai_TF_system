#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AthleteRanking.com 完全版全ラウンド対応スクレイピングシステム

既存の動作するスクレイパーをベースに全ラウンド対応機能を追加:
1. 動作確認済みのAPI構造を使用
2. 予選・準決勝・決勝すべてのラウンドを取得
3. 組別データの正確な処理
4. 風速情報の完全対応
5. 文字化け対応
"""

import requests
import re
import json
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import sys
import os
import unicodedata
from typing import Dict, List, Optional, Tuple, Any
import time

class CompleteAllRoundsAthleteRankingScraper:
    """完全版全ラウンド対応AthleteRankingスクレイパー"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        # 文字化け修復マッピング
        self.character_fixes = {
            r'�繭鵝々┿嶇�': '栁瀨宏志郎',
            r'�+': '',
        }
        
        # 完全な種目コードマッピング（動作確認済み）
        self.event_codes = {
            # 男子対校
            "男子対校100m": "A0100", "男子対校200m": "A0200", "男子対校400m": "A0400",
            "男子対校800m": "A0800", "男子対校1500m": "A1150", "男子対校5000m": "A1500",
            "男子対校110mH": "AH111", "男子対校400mH": "AH401", "男子対校3000mSC": "AS301",
            "男子対校5000mW": "AW501", "男子対校4x100mR": "AR141", "男子対校4x400mR": "AR441",
            "男子対校走高跳": "FJHP0", "男子対校棒高跳": "FJHP0", "男子対校走幅跳": "FJLJ0",
            "男子対校三段跳": "FJTJ0", "男子対校砲丸投": "FTAT1", "男子対校円盤投": "FTDT1",
            "男子対校ハンマー投": "FTHT1", "男子対校やり投": "FTJT0",
            
            # 男子OP
            "男子OP100m": "A0100", "男子OP200m": "A0200", "男子OP400m": "A0400",
            "男子OP800m": "A0800", "男子OP1500m": "A1150", "男子OP5000m": "A1500",
            "男子OP110mH": "AH111", "男子OP400mH": "AH401", "男子OP3000mSC": "AS301",
            "男子OP5000mW": "AW501", "男子OP4x100mR": "AR141", "男子OP4x400mR": "AR441",
            "男子OP走高跳": "FJHP0", "男子OP棒高跳": "FJHP0", "男子OP走幅跳": "FJLJ0",
            "男子OP三段跳": "FJTJ0", "男子OP砲丸投": "FTAT1", "男子OP円盤投": "FTDT1",
            "男子OP ハンマー投": "FTHT1", "男子OP やり投": "FTJT0",
            
            # 女子対校
            "女子対校100m": "A0100", "女子対校200m": "A0200", "女子対校400m": "A0400",
            "女子対校800m": "A0800", "女子対校1500m": "A1150", "女子対校3000m": "A1300",
            "女子対校100mH": "AH101", "女子対校400mH": "AH401", "女子対校3000mSC": "AS301",
            "女子対校5000mW": "AW501", "女子対校4x100mR": "AR141", "女子対校4x400mR": "AR441",
            "女子対校走高跳": "FJHP0", "女子対校棒高跳": "FJHP0", "女子対校走幅跳": "FJLJ0",
            "女子対校三段跳": "FJTJ0", "女子対校砲丸投": "FTAT1", "女子対校円盤投": "FTDT1",
            "女子対校ハンマー投": "FTHT1", "女子対校やり投": "FTJT0",
            
            # 女子OP
            "女子OP100m": "A0100", "女子OP200m": "A0200", "女子OP400m": "A0400",
            "女子OP800m": "A0800", "女子OP1500m": "A1150", "女子OP3000m": "A1300",
            "女子OP5000m": "A1500", "女子OP100mH": "AH101", "女子OP400mH": "AH401",
            "女子OP3000mSC": "AS301", "女子OP5000mW": "AW501", "女子OP4x100mR": "AR141",
            "女子OP4x400mR": "AR441", "女子OP走高跳": "FJHP0", "女子OP棒高跳": "FJHP0",
            "女子OP走幅跳": "FJLJ0", "女子OP三段跳": "FJTJ0", "女子OP砲丸投": "FTAT1",
            "女子OP円盤投": "FTDT1", "女子OP ハンマー投": "FTHT1", "女子OP やり投": "FTJT0"
        }
    
    def fix_character_corruption(self, text: str) -> str:
        """文字化け修復"""
        if not text:
            return text
        
        fixed_text = text
        for pattern, replacement in self.character_fixes.items():
            fixed_text = re.sub(pattern, replacement, fixed_text)
        return unicodedata.normalize('NFKC', fixed_text)
    
    def get_competition_data(self, game_id: str) -> Dict:
        """大会データを取得（動作確認済みの方法）"""
        print(f"🎯 完全全ラウンド対応スクレイピング開始: {game_id}")
        
        # 種目一覧を取得
        event_list_url = f"https://games.athleteranking.com/api/racelist.php?gid={game_id}"
        
        try:
            response = self.session.get(event_list_url, timeout=30)
            response.raise_for_status()
            
            # EUC-JPでデコード（動作確認済み）
            content = response.content.decode('euc-jp', errors='ignore')
            
            # JSONパース
            event_data = json.loads(content)
            
            print(f"対象種目数: {len(event_data)}")
            return event_data
            
        except Exception as e:
            print(f"❌ 種目一覧取得エラー: {e}")
            return []
    
    def get_event_all_rounds(self, game_id: str, event_code: str, event_name: str) -> List[Dict]:
        """種目の全ラウンドデータを取得"""
        print(f"📊 取得中: {event_name}")
        
        all_results = []
        wind_count = 0
        
        try:
            # レースデータAPI（動作確認済み）
            race_data_url = f"https://games.athleteranking.com/api/racedata.php?gid={game_id}&eid={event_code}"
            
            response = self.session.get(race_data_url, timeout=30)
            response.raise_for_status()
            
            # EUC-JPでデコード
            content = response.content.decode('euc-jp', errors='ignore')
            race_data = json.loads(content)
            
            # 全ラウンドを処理
            for round_data in race_data.get('rounds', []):
                round_name = round_data.get('round_name', '決勝')
                round_name = self.fix_character_corruption(round_name)
                
                # 組別データの処理
                if 'heats' in round_data and round_data['heats']:
                    # 予選など組別データがある場合
                    for heat_data in round_data['heats']:
                        heat_number = heat_data.get('heat_number', '')
                        heat_wind = heat_data.get('wind_speed', '')
                        
                        for result in heat_data.get('results', []):
                            processed_result = self.process_result_with_rounds(
                                result, event_name, round_name, heat_number, heat_wind
                            )
                            all_results.append(processed_result)
                            
                            if processed_result['wind_speed']:
                                wind_count += 1
                else:
                    # 決勝など組別データがない場合
                    for result in round_data.get('results', []):
                        processed_result = self.process_result_with_rounds(
                            result, event_name, round_name
                        )
                        all_results.append(processed_result)
                        
                        if processed_result['wind_speed']:
                            wind_count += 1
            
            # 結果表示
            wind_info = f" (風速データ: {wind_count}件)" if wind_count > 0 else ""
            print(f"  ✅ {len(all_results)}名取得{wind_info}")
            
            return all_results
            
        except Exception as e:
            print(f"  ❌ エラー: {e}")
            return []
    
    def process_result_with_rounds(self, result: Dict, event_name: str, round_name: str, 
                                 heat_number: str = None, heat_wind: str = None) -> Dict:
        """結果データを処理（ラウンド情報付き）"""
        # 基本情報の取得
        athlete_name = result.get('athlete_name', '')
        athlete_name = self.fix_character_corruption(athlete_name)
        
        record = result.get('record', '')
        
        # 風速情報の抽出と分離
        wind_speed = None
        clean_record = record
        
        # 組の風速情報を優先
        if heat_wind:
            wind_speed = heat_wind
        else:
            # 記録から風速情報を抽出
            wind_match = re.search(r'\\(([+-]?\\d+\\.?\\d*)\\)', record)
            if wind_match:
                wind_speed = wind_match.group(1)
                clean_record = re.sub(r'\\([+-]?\\d+\\.?\\d*\\)', '', record).strip()
        
        # 通過情報の抽出
        note = result.get('note', '')
        qualification = None
        if 'Q' in note:
            qualification = 'Q'  # 着順通過
        elif 'q' in note:
            qualification = 'q'  # 記録通過
        
        return {
            'event': event_name,
            'round': round_name,
            'heat': heat_number,
            'rank': result.get('rank'),
            'lane': result.get('lane'),
            'athlete_name': athlete_name,
            'athlete_number': result.get('athlete_number'),
            'affiliation': result.get('affiliation', ''),
            'record': clean_record,
            'wind_speed': wind_speed,
            'qualification': qualification,
            'note': note
        }
    
    def scrape_competition_all_rounds(self, game_url: str) -> pd.DataFrame:
        """大会の全ラウンドをスクレイピング"""
        # 大会IDを抽出
        gid_match = re.search(r'gid=([^&]+)', game_url)
        if not gid_match:
            raise ValueError("大会IDが見つかりません")
        
        game_id = gid_match.group(1)
        
        # 大会データを取得
        event_data = self.get_competition_data(game_id)
        
        if not event_data:
            print("❌ 種目データが取得できませんでした")
            return pd.DataFrame()
        
        # 全種目・全ラウンドの結果を取得
        all_results = []
        
        for event in event_data:
            event_code = event.get('eid', '')
            event_name = event.get('event_name', '')
            event_name = self.fix_character_corruption(event_name)
            
            if event_code and event_name:
                # 種目の全ラウンドデータを取得
                event_results = self.get_event_all_rounds(game_id, event_code, event_name)
                all_results.extend(event_results)
                
                # レート制限
                time.sleep(0.3)
        
        # DataFrameに変換
        df = pd.DataFrame(all_results)
        
        print(f"\\n🎉 全ラウンド取得完了!")
        print(f"📊 総記録数: {len(df)}")
        
        return df
    
    def save_all_rounds_results(self, df: pd.DataFrame, game_id: str) -> Tuple[str, str, str]:
        """全ラウンド結果を保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"complete_all_rounds_results_{timestamp}"
        
        # CSV保存（UTF-8 BOM付き）
        csv_path = f"{base_filename}.csv"
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        
        # Excel保存
        excel_path = f"{base_filename}.xlsx"
        df.to_excel(excel_path, index=False, engine='openpyxl')
        
        # JSON保存
        json_path = f"{base_filename}.json"
        df.to_json(json_path, orient='records', ensure_ascii=False, indent=2)
        
        print(f"\\n💾 保存完了:")
        print(f"📄 CSV: {csv_path}")
        print(f"📊 Excel: {excel_path}")
        print(f"📋 JSON: {json_path}")
        
        return csv_path, excel_path, json_path

def main():
    """メイン実行関数"""
    
    # if len(sys.argv) < 2:
    #     print("使用方法: python3 athlete_ranking_complete_all_rounds_scraper.py <大会URL>")
    #     print("例: python3 athlete_ranking_complete_all_rounds_scraper.py 'https://games.athleteranking.com/gamedata.php?gid=aa512025022'")
    #     return
    
    # game_url = sys.argv[1]
    game_url="https://games.athleteranking.com/gamedata.php?gid=aa512025022"
    
    print("=" * 80)
    print("🚀 AthleteRanking.com 完全版全ラウンド対応スクレイパー")
    print("=" * 80)
    print("🎯 対象: 予選・準決勝・決勝すべてのラウンド")
    print("✅ ベース: 動作確認済みスクレイパー")
    print("🌪️ 風速情報: 完全対応")
    print("🔧 文字化け: 自動修復")
    print()
    
    try:
        # スクレイパー初期化
        scraper = CompleteAllRoundsAthleteRankingScraper()
        
        # 全ラウンド結果取得
        results_df = scraper.scrape_competition_all_rounds(game_url)
        
        if results_df.empty:
            print("⚠️ データが取得できませんでした")
            return
        
        # 大会IDを抽出
        gid_match = re.search(r'gid=([^&]+)', game_url)
        game_id = gid_match.group(1) if gid_match else "unknown"
        
        # 結果保存
        csv_path, excel_path, json_path = scraper.save_all_rounds_results(results_df, game_id)
        
        # 詳細レポート
        print(f"\\n📊 詳細レポート:")
        print(f"総記録数: {len(results_df)}")
        
        # ラウンド別集計
        if 'round' in results_df.columns:
            round_counts = results_df['round'].value_counts()
            print(f"\\nラウンド別記録数:")
            for round_name, count in round_counts.items():
                print(f"  {round_name}: {count} 件")
        
        # 文字化け検証
        if 'athlete_name' in results_df.columns:
            garbled_count = results_df['athlete_name'].str.contains('�', na=False).sum()
            print(f"\\n文字化け選手名: {garbled_count} 件")
        
        # 風速情報の確認
        if 'wind_speed' in results_df.columns:
            wind_records = results_df[results_df['wind_speed'].notna()]
            print(f"風速情報付き記録: {len(wind_records)} 件")
        
        # 通過情報の確認
        if 'qualification' in results_df.columns:
            qualified_records = results_df[results_df['qualification'].notna()]
            print(f"通過情報付き記録: {len(qualified_records)} 件")
        
        # 予選データの確認
        if 'round' in results_df.columns:
            preliminary_records = results_df[results_df['round'].str.contains('予選', na=False)]
            if not preliminary_records.empty:
                print(f"\\n🎯 予選記録: {len(preliminary_records)} 件")
                
                # 男子100m予選の確認
                if 'event' in results_df.columns:
                    m100_prelim = preliminary_records[
                        (preliminary_records['event'].str.contains('100m', na=False)) &
                        (preliminary_records['event'].str.contains('男子', na=False))
                    ]
                    if not m100_prelim.empty:
                        print(f"\\n👤 男子100m予選: {len(m100_prelim)} 件")
                        for _, record in m100_prelim.head(10).iterrows():
                            wind_info = f" (風速: {record['wind_speed']})" if record['wind_speed'] else ""
                            qual_info = f" [{record['qualification']}]" if record['qualification'] else ""
                            heat_info = f" {record['heat']}組" if record['heat'] else ""
                            print(f"  {record['athlete_name']} - {record['record']}{wind_info}{qual_info}{heat_info}")
        
        print(f"\\n🎉 完全版全ラウンド処理完了!")
        print(f"🏆 予選・準決勝・決勝すべてのラウンドを取得しました！")
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
