#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AthleteRanking.com 完全適応型スクレイパー
動的種目検出機能により任意の大会に対応
"""

import requests
import json
import sys
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import re
from urllib.parse import urljoin
#aa512025022@1@0@0@AW500@ALL
# 包括的種目コードマッピング（全発見種目を統合）
COMPREHENSIVE_EVENT_CODES = {
    # 男子対校種目 (@1@0@0@)
    "男子対校100m": "A0100",
    # "男子対校200m": "A0200", 
    # "男子対校400m": "A0400",
    # "男子対校800m": "A0800",
    # "男子対校1500m": "A1150",
    # "男子対校5000m": "A1500",
    # "男子対校110mH": "AH111",
    # "男子対校400mH": "AH401",
    # "男子対校3000mSC": "AS301",
    # "男子対校5000mW": "AW500",
    # "男子対校4x100mR": "D0400",
    # "男子対校4x400mR": "D1600",
    # "男子対校走高跳": "FJHJ0",
    # "男子対校棒高跳": "FJHP0",
    # "男子対校走幅跳": "FJLJ0",
    # "男子対校三段跳": "FJTJ0",
    # "男子対校砲丸投": "FTAT1",
    # "男子対校円盤投": "FTDT1",
    # "男子対校ハンマー投": "FTHT1",
    # "男子対校やり投": "FTJT1",
    
    # # 女子対校種目 (@2@0@0@) - 関西医科学生大会で新発見
    # "女子対校100m": "A0100",
    # "女子対校200m": "A0200",  # 🎯 新発見！
    # "女子対校400m": "A0400",
    # "女子対校800m": "A0800",
    # "女子対校1500m": "A1150", # 🎯 新発見！
    # "女子対校3000m": "A1300",
    # "女子対校5000m": "A1500",
    # "女子対校100mH": "AH101",
    # "女子対校400mH": "AH401",
    # "女子対校3000mSC": "AS301",
    # "女子対校5000mW": "AW500",
    # "女子対校4x100mR": "D0400",
    # "女子対校4x400mR": "D1600",
    # "女子対校走高跳": "FJHJ0",
    # "女子対校走幅跳": "FJLJ0",
    # "女子対校砲丸投": "FTAT6",
    # "女子対校円盤投": "FTDT3",
    # "女子対校ハンマー投": "FTHT3",
    # "女子対校やり投": "FTJT3",
    
    # 男子OP種目 (@1@1@0@)
    "男子OP100m": "A0100",
    # "男子OP400m": "A0400",
    # "男子OP1500m": "A1150",
    # "男子OP5000m": "A1500",
    # "男子OP5000mW": "AW500",
    # "男子OP4x400mR": "D1600",
    # "男子OP棒高跳": "FJHP0",
    # "男子OP走幅跳": "FJLJ0",
    # "男子OP砲丸投": "FTAT1",
    # "男子OP円盤投": "FTDT1",
    # "男子OPハンマー投": "FTHT1",
    # "男子OPやり投": "FTJT1",
    
    # # 女子OP種目 (@2@1@0@)
    # "女子OP100m": "A0100",
    # "女子OP400m": "A0400",
    # "女子OP1500m": "A1150",
    # "女子OP5000m": "A1500",
    # "女子OP5000mW": "AW500",
    # "女子OP4x400mR": "D1600",
    # "女子OP走幅跳": "FJLJ0",
    # "女子OP砲丸投": "FTAT6",
    # "女子OP円盤投": "FTDT3",
    # "女子OPハンマー投": "FTHT3",
    # "女子OPやり投": "FTJT3",
    
    # # 非公認種目 (@1@2@0@, @2@2@0@)
    # "男子非公認4x400mR": "D1600",
    # "女子非公認4x400mR": "D1600",
}

def get_category_code(event_name):
    """種目名からカテゴリコードを取得"""
    if "男子対校" in event_name:
        return "1@0@0"
    elif "女子対校" in event_name:
        return "2@0@0"
    elif "男子OP" in event_name:
        return "1@1@0"
    elif "女子OP" in event_name:
        return "2@1@0"
    elif "男子非公認" in event_name:
        return "1@2@0"
    elif "女子非公認" in event_name:
        return "2@2@0"
    else:
        return "1@0@0"  # デフォルト

def extract_gid_from_url(url):
    """URLから大会IDを抽出"""
    if "gid=" in url:
        return url.split("gid=")[1].split("&")[0]
    return None

def detect_available_events_from_browser(gid):
    """ブラウザアクセスによる動的種目検出"""
    print("🔍 動的種目検出を開始...")
    
    session = requests.Session()
    detected_events = {}
    
    try:
        # 競技結果ページにアクセス
        race_url = f"https://games.athleteranking.com/gamedata.php?gid={gid}"
        response = session.get(race_url, timeout=30)
        response.raise_for_status()
        
        # タイムテーブル・結果ページを探す
        soup = BeautifulSoup(response.text, 'html.parser')
        timetable_link = None
        
        for link in soup.find_all('a'):
            if 'タイムテーブル' in link.get_text() and '結果' in link.get_text():
                href = link.get('href')
                if href:
                    timetable_link = urljoin(race_url, href)
                    break
        
        if not timetable_link:
            print("⚠️ タイムテーブル・結果ページが見つかりません")
            return detected_events
        
        # 競技結果ページにアクセス
        response = session.get(timetable_link, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 種目リンクを解析
        event_links = soup.find_all('a')
        event_count = 0
        
        for link in event_links:
            link_text = link.get_text().strip()
            href = link.get('href')
            
            # 種目名のパターンマッチング
            if re.match(r'^(100m|200m|400m|800m|1500m|3000m|5000m|110mH|100mH|400mH|3000mSC|5000mW|4x100mR|4x400mR|走高跳|棒高跳|走幅跳|三段跳|砲丸投|円盤投|ハンマー投|やり投)$', link_text):
                # 男子・女子の判定（前後のコンテキストから）
                parent_text = link.parent.get_text() if link.parent else ""
                
                # 男子セクションか女子セクションかを判定
                if "男子" in parent_text or any("男子" in sibling.get_text() for sibling in link.parent.find_previous_siblings() if sibling.name):
                    event_name = f"男子対校{link_text}"
                elif "女子" in parent_text or any("女子" in sibling.get_text() for sibling in link.parent.find_previous_siblings() if sibling.name):
                    event_name = f"女子対校{link_text}"
                else:
                    continue
                
                # 種目コードを取得
                if event_name in COMPREHENSIVE_EVENT_CODES:
                    detected_events[event_name] = COMPREHENSIVE_EVENT_CODES[event_name]
                    event_count += 1
                    print(f"  ✅ 検出: {event_name} ({COMPREHENSIVE_EVENT_CODES[event_name]})")
        
        print(f"🎯 動的検出完了: {event_count}種目を発見")
        return detected_events
        
    except Exception as e:
        print(f"⚠️ 動的検出エラー: {e}")
        return detected_events

def get_event_results(session, gid, event_name, event_code):
    """指定された種目の結果を取得（全ラウンド対応）"""
    category_code = get_category_code(event_name)
    base_event_id = f"{gid}@{category_code}@{event_code}"
    
    # 複数のラウンドを試行するためのパターン
    round_patterns = [
        "@5@1",     # 予選11〜11組
        "@5@11",      # 予選1〜10組
        "@5@21",
        "@5@31",
        "@5@41",
        "@5",        # 予選（総合結果）
        "@2@1",      # 準決勝1〜3組
        "@2@11"
        "@2",        # 準決勝（総合結果）
        "@1@1",      # 決勝
        "@1@11",
        "@1@21",
        "@ALL"       # 全結果
    ]
    
    
    all_results = []
    
    for pattern in round_patterns:
        event_id = base_event_id + pattern
        
        api_url = "https://games.athleteranking.com/resultdata.php"
        
        data = {
            'id': event_id,
            'pref': '',
            'year_s': '',
            'year_e': '',
            'month_s': '',
            'month_e': '',
            'rec_use': ''
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': f'https://games.athleteranking.com/gamedata.php?gid={gid}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        try:
            response = session.post(api_url, data=data, headers=headers, timeout=30)
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            #print(response.encoding)
            forbit_code_list={
                "iso8859_13",
                "CP949",
                "big5hkscs",
                "ISO-8859-5",
                "iso8859_16"
            }


            if response.encoding in forbit_code_list:
                response.encoding = "euc_jis_2004"
                #response.encoding = "euc-jp"

            if len(response.text) < 1000:
                continue
                
            soup = BeautifulSoup(response.text, 'html.parser')
            tables = soup.find_all('table')
            #print(soup)
            
            if len(tables) < 2:
                continue
                
            result_table = None
            for table in tables:
                rows = table.find_all('tr')
                if len(rows) > 2:
                    result_table = table
                    break
            
            if not result_table:
                continue
                
            rows = result_table.find_all('tr')
            if len(rows) <= 2:
                continue
                
            results = parse_results_from_table(rows, event_name, pattern)
            if results:
                all_results.extend(results)
                print(f"  ✅ {pattern}: {len(results)}名取得")
                
        except Exception as e:
            continue
            
        time.sleep(0.1)  # API負荷軽減
    
    # 重複除去（同じ選手の同じラウンドのデータ）
    unique_results = []
    seen = set()
    
    for result in all_results:
        key = (result['氏名'], result['ラウンド'], result.get('組', ''))
        if key not in seen:
            seen.add(key)
            unique_results.append(result)
    print(unique_results)
    return unique_results if unique_results else None

def parse_results_from_table(rows, event_name, pattern):
    """テーブルから結果データを解析"""
    results = []
    current_round = "決勝"
    current_group = ""
    wind_info = ""
    
    def extract_wind_info_from_rows(rows):
        """競技結果のHTMLから風速情報を抽出"""
        for row in rows:
            cells = row.find_all(['td', 'th'])
            for cell in cells:
                cell_text = cell.get_text().strip()
                wind_pattern = r'(\+|\-)?(\d+\.\d+)\)'
                if '組' in cell_text and ('(+' in cell_text or '(-' in cell_text):
                    match = re.search(wind_pattern, cell_text)
                    if match:
                        sign = match.group(1) if match.group(1) else '+'
                        value = match.group(2)
                        return f"{sign}{value}"
        return ""
    
    wind_info = extract_wind_info_from_rows(rows)
    
    for row in rows:
        cells = row.find_all(['td', 'th'])
        
        if len(cells) < 4:
            continue
        
        # ラウンド情報の判定
        if len(cells) == 1:
            cell_text = cells[0].get_text().strip()
            if any(keyword in cell_text for keyword in ['決勝', '準決勝', '予選']):
                current_round = cell_text
                continue
        
        # 組情報の判定
        if len(cells) >= 3:
            cell_text = cells[0].get_text().strip()
            if '組' in cell_text and ('(' in cell_text or '+' in cell_text or '-' in cell_text):
                current_group = cell_text
                # 風速情報を再抽出
                wind_pattern = r'(\+|\-)?(\d+\.\d+)\)'
                match = re.search(wind_pattern, cell_text)
                if match:
                    sign = match.group(1) if match.group(1) else '+'
                    value = match.group(2)
                    wind_info = f"{sign}{value}"
                continue
        
        # 結果データの解析
        if len(cells) >= 6:
            try:
                rank_text = cells[0].get_text().strip()
                # 順位が数字でない場合（DNS、DNF等）をスキップ
                # if not rank_text.replace('.', '').isdigit():
                #     continue
                    
                rank = int(float(rank_text)) if rank_text.replace('.', '').isdigit() else rank_text
                
                lane_text = cells[1].get_text().strip()
                lane = int(lane_text) if lane_text.isdigit() else lane_text
                
                athlete_info = cells[2].get_text().strip()
                athlete_number = cells[3].get_text().strip()
                affiliation = cells[4].get_text().strip()
                record = cells[5].get_text().strip()
                note = cells[6].get_text().strip() if len(cells) > 6 else ""
                
                # ラウンド情報をパターンから推定
                if "@1@" in pattern:
                    round_name = "決勝"
                elif "@2@" in pattern or "@2" == pattern:
                    round_name = "準決勝"
                elif "@5@" in pattern or "@5" == pattern:
                    round_name = "予選"
                else:
                    round_name = current_round
                
                results.append({
                    '種目': event_name,
                    '競技': event_name,
                    '種別': event_name,
                    'ラウンド': round_name,
                    '組': current_group,
                    '順位': rank,
                    'ﾚｰﾝ': lane,
                    '風': wind_info,
                    '氏名': athlete_info,
                    '所属': athlete_number,
                    '記録': affiliation,
                    '備考': record,
                    'note': note
                })
            except (ValueError, IndexError) as e:
                continue
                
    return results
def extract_competition_info(soup):
    """大会詳細ページから基本情報を抽出"""
    competition_info = {
        'name': None,
        'date': None,
        'venue': None
    }
    
    try:
        # 大会名を取得
        title_div = soup.find('div', class_='game_title')
        if title_div:
            competition_info['name'] = title_div.get_text().strip()
        
        # 大会データテーブルから期日と会場を取得
        game_table = soup.find('table', class_='gamedata')
        if game_table:
            rows = game_table.find_all('tr')
            
            for row in rows:
                th = row.find('th', class_='g_d_th')
                td = row.find('td')
                
                if th and td:
                    header_text = th.get_text().strip()
                    cell_text = td.get_text().strip()
                    
                    # 期日を取得
                    if header_text == '期日':
                        competition_info['date'] = cell_text
                    
                    # 会場を取得
                    elif header_text == '会場':
                        # リンクがある場合はリンクテキストを、ない場合は通常のテキストを取得
                        venue_link = td.find('a')
                        if venue_link:
                            competition_info['venue'] = venue_link.get_text().strip()
                        else:
                            competition_info['venue'] = cell_text
        
        print(f"🏆 大会名: {competition_info['name']}")
        print(f"📅 期日: {competition_info['date']}")
        print(f"🏟️ 会場: {competition_info['venue']}")
        
        return competition_info
        
    except Exception as e:
        print(f"❌ 大会情報抽出エラー: {e}")
        return competition_info


def get_adaptive_competition_results(url):
    """完全適応型：任意の大会の競技結果を取得"""
    print("🚀 AthleteRanking.com 完全適応型スクレイパー開始")
    print("🎯 動的種目検出により任意の大会に対応")
    print(f"🌐 対象URL: {url}")
    
    # pandasの利用可能性確認
    try:
        import pandas as pd
        pandas_available = True
        print("✅ pandas利用可能")
    except ImportError:
        pandas_available = False
        print("⚠️ pandas利用不可")
    
    gid = extract_gid_from_url(url)
    if not gid:
        print("❌ 大会IDを抽出できませんでした")
        return None
    
    session = requests.Session()
    
    # 大会詳細ページにアクセス
    try:
        response = session.get(url, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        #print(soup)
        # 大会名を取得
        competition_info = extract_competition_info(soup)
        # title_element = soup.find('h1') or soup.find('title')
        # competition_name = title_element.get_text().strip() if title_element else "陸上競技大会"
        
        print(f"🎯 大会ID: {gid}")
        print(f"🏆 大会名: {competition_info['name']}")
        print(f"📅 期日: {competition_info['date']}")
        print(f"🏟️ 会場: {competition_info['venue']}")

    except Exception as e:
        print(f"❌ 大会詳細ページのアクセスに失敗: {e}")
        return None
    
    # 動的種目検出
    detected_events = detect_available_events_from_browser(gid)
    
    # 検出された種目がない場合は包括的マッピングを使用
    if not detected_events:
        print("⚠️ 動的検出失敗、包括的マッピングを使用")
        detected_events = COMPREHENSIVE_EVENT_CODES
    
    all_results = []
    success_count = 0
    total_events = len(detected_events)
    new_discoveries = []
    
    print(f"🎯 対象種目数: {total_events}")
    print("🔥 完全適応型で最高の取得率を目指します！")
    
    for i, (event_name, event_code) in enumerate(detected_events.items(), 1):
        print(f"[{i}/{total_events}] 🎯 取得中: {event_name}")
        
        results = get_event_results(session, gid, event_name, event_code)
        
        if results:
            success_count += 1
            participant_count = len(results)
            
            # 新発見種目の判定
            if event_name in ["女子対校200m", "女子対校1500m"]:
                new_discoveries.append(event_name)
                print(f"  ✅ 成功 ({participant_count}名) 🎉🎉 **新発見種目！** 🎉🎉")
            else:
                print(f"  ✅ 成功 ({participant_count}名)")
            
            # 大会情報を各結果に追加
            for result in results:
                result['大会'] = competition_info['name']
                result['日付'] = competition_info['date']
                result['競技場'] = competition_info['venue']
            
            all_results.extend(results)
        else:
            print(f"  ❌ データなし")
        
        time.sleep(0.1)
    
    if not all_results:
        print("❌ 取得できた結果がありません")
        return None
    
    # ファイル保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # # JSON保存
    # json_filename = f"adaptive_results_{timestamp}.json"
    # with open(json_filename, 'w', encoding='utf-8') as f:
    #     json.dump(all_results, f, ensure_ascii=False, indent=2)
    # print(f"💾 JSON結果を {json_filename} に保存しました")
    
    if pandas_available:
        df = pd.DataFrame(all_results)
        
        # # CSV保存
        # csv_filename = f"adaptive_results_{timestamp}.csv"
        # df.to_csv(csv_filename, index=False, encoding='utf-8')
        # print(f"📊 CSV結果を {csv_filename} に保存しました")
        
        # # Excel保存
        # excel_filename = f"adaptive_results_{timestamp}.xlsx"
        # with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        #     df.to_excel(writer, sheet_name='全結果', index=False)
            
        #     for event in df['event'].unique():
        #         event_df = df[df['event'] == event]
        #         safe_sheet_name = event.replace('/', '_')[:31]
        #         event_df.to_excel(writer, sheet_name=safe_sheet_name, index=False)
        
        # print(f"📈 Excel結果を {excel_filename} に保存しました")
    
    # 結果サマリー
    current_success_rate = success_count/total_events*100
    # print(f"\n🚀 完全適応型取得結果")
    # print("=" * 60)
    # print(f"🏆 大会名: {competition_name}")
    # print(f"📅 期日: 2025年6月29日")
    # print(f"🏟️ 会場: 皇子山総合運動公園陸上競技場")
    # print(f"📊 取得統計:")
    # print(f"  対象種目数: {total_events}")
    # print(f"  成功取得: {success_count}")
    # print(f"  失敗: {total_events - success_count}")
    # print(f"  成功率: {current_success_rate:.1f}%")
    
    # # 新発見種目の報告
    # if new_discoveries:
    #     print(f"🎉🎉 **新発見種目 ({len(new_discoveries)}/2):**")
    #     for discovery in new_discoveries:
    #         print(f"  ✅ {discovery}")
    
    # # 成功率による評価
    # if current_success_rate >= 95.0:
    #     print("🎉🎉🎉 **95%以上達成！完全適応型で最高の成果！** 🎉🎉🎉")
    # elif current_success_rate >= 90.0:
    #     print("🎉🎉 **90%以上達成！完全適応型で素晴らしい成果！** 🎉🎉")
    # elif current_success_rate >= 85.0:
    #     print("🎉 **85%以上達成！完全適応型で優秀な成果！** 🎉")
    
    # # 取得成功種目の詳細
    # print(f"📋 取得成功種目:")
    # event_summary = {}
    # for result in all_results:
    #     event = result['event']
    #     if event not in event_summary:
    #         event_summary[event] = []
    #     event_summary[event].append(result)
    
    # for event, results in event_summary.items():
    #     rounds = set(r['round'] for r in results)
    #     round_info = "(" + ", ".join(f"{r}({len([res for res in results if res['round'] == r])}名)" for r in rounds) + ")"
        
    #     if event in new_discoveries:
    #         print(f"  ✅ {event}: {len(results)}名 {round_info} 🎉 **新発見！**")
    #     else:
    #         print(f"  ✅ {event}: {len(results)}名 {round_info}")
        
    #     # 優勝者情報
    #     winners = [r for r in results if r['rank'] == 1]
    #     if winners:
    #         winner = winners[0]
    #         print(f"    🥇 {winner['round']}優勝: {winner['athlete_name']} ({winner['affiliation']}) - {winner['record']}")
    
    # print(f"👥 総選手数: {len(all_results)}名")
    
    # if pandas_available:
    #     print(f"📊 pandas DataFrame: {df.shape[0]}行 × {df.shape[1]}列")
    
    # print("✅ 完全適応型処理完了")
    return all_results

def scrape_athlete_ranking(url,univ):
    """AthleteRanking.comの競技結果をスクレイピング"""
    print(f"🚀 AthleteRanking.com スクレイピング開始: {url}")
    
    results = get_adaptive_competition_results(url)
    df = pd.DataFrame(results) if results else None
    df_univ = df[df['所属'].str.contains(univ, na=False)] if df is not None else None
    if results:
        print(f"🎉 競技結果取得成功: {len(results)}件")
        return df_univ
    else:
        print("❌ 競技結果取得失敗")
        return None

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://games.athleteranking.com/gamedata.php?gid=ay022025010"
    
    results = get_adaptive_competition_results(url)
    df_result = pd.DataFrame(results) if results else None
    if results:
        print(f"\n🚀 最終結果: {len(results)}件の競技結果を取得しました")
        print(df_result[:5])  # 最初の5件を表示
        print(df_result.describe(include='all'))  # データの概要を表示
        #print(df_result['athlete_number'].unique())
        print(df_result[df_result['所属'] == "大阪大"])  # 優勝者の情報を表示
        #print(df_result['備考'].unique())
        #print(df_result['note'].unique)  # 新発見種目の情報を表示
        # success_rate = len(set(r['event'] for r in results)) / len(COMPREHENSIVE_EVENT_CODES) * 100
        # if success_rate >= 95.0:
        #     print("🎉🎉🎉 **完全適応型で95%以上の最高成果を達成！** 🎉🎉🎉")
        # elif success_rate >= 90.0:
        #     print("🎉🎉 **完全適応型で90%以上の素晴らしい成果を達成！** 🎉🎉")
        # else:
        #     print(f"📈 成功率: {success_rate:.1f}% - 完全適応型での貴重なデータ取得です！")
    else:
        print("\n❌ 結果の取得に失敗しました")

