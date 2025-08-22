#!/usr/bin/env python3
"""
大会名取得スクリプト

指定された大会URLから大会名を取得します。

使用例:
python get_competition_name.py "https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html"
"""

import sys
import re
import requests
from typing import Optional, Dict
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


def get_competition_info(timetable_url: str) -> Optional[Dict]:
    """
    大会URLから大会情報を取得
    
    Args:
        timetable_url: 大会のタイムテーブルURL
        
    Returns:
        大会情報の辞書（取得できない場合はNone）
        {
            'name': str,         # 大会名
            'date': str,         # 開催日
            'year': int,         # 開催年
            'source': str,       # 情報取得元（'json', 'html', 'url'）
            'url': str          # 元のURL
        }
    """
    print(f"🏆 大会情報取得開始")
    print(f"🔗 対象URL: {timetable_url}")
    
    try:
        # 複数の方法で大会情報を取得を試行
        
        # 方法1: JSONデータから取得
        competition_info = _get_info_from_json(timetable_url)
        if competition_info:
            competition_info['source'] = 'json'
            competition_info['url'] = timetable_url
            print(f"✅ JSONから大会情報取得成功: {competition_info['name']}")
            return competition_info
        
        # 方法2: HTMLページから取得
        competition_info = _get_info_from_html(timetable_url)
        if competition_info:
            competition_info['source'] = 'html'
            competition_info['url'] = timetable_url
            print(f"✅ HTMLから大会情報取得成功: {competition_info['name']}")
            return competition_info
        
        # 方法3: URLパスから推測
        competition_info = _get_info_from_url(timetable_url)
        if competition_info:
            competition_info['source'] = 'url'
            competition_info['url'] = timetable_url
            print(f"✅ URLから大会情報推測成功: {competition_info['name']}")
            return competition_info
        
        print("❌ 大会情報を取得できませんでした")
        return None
        
    except Exception as e:
        print(f"❌ 大会情報取得エラー: {e}")
        return None


def get_competition_name(timetable_url: str) -> Optional[str]:
    """
    後方互換性のための関数（大会名のみ返す）
    """
    info = get_competition_info(timetable_url)
    return info['name'] if info else None


def _get_info_from_json(timetable_url: str) -> Optional[Dict]:
    """JSONデータから大会情報を取得"""
    try:
        # URLが既にJSONファイルの場合とHTMLファイルの場合の両方に対応
        if timetable_url.endswith('.json'):
            # 既にJSONファイルのURL
            if 'TimeTable.json' in timetable_url:
                # TimeTable.jsonの場合、Taikai.jsonも試す
                taikai_json_url = timetable_url.replace('TimeTable.json', 'Taikai.json')
                json_url = timetable_url
            else:
                # その他のJSONファイル（例：Taikai.json）
                taikai_json_url = timetable_url
                json_url = timetable_url.replace('Taikai.json', 'TimeTable.json')
        else:
            # HTMLファイルのURL
            taikai_json_url = timetable_url.replace('TimeTable.html', 'Taikai.json')
            json_url = timetable_url.replace('.html', '.json')
        
        # 方法1: Taikai.jsonから大会情報を取得（最優先）
        print(f"🔍 Taikai.json URL: {taikai_json_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': timetable_url
        }
        
        response = requests.get(taikai_json_url, headers=headers, timeout=10)
        if response.status_code == 200:
            taikai_data = response.json()
            print(f"📋 Taikai.jsonキー: {list(taikai_data.keys())}")
            print(f"📄 Taikai.json全体データ:")
            import json
            print(json.dumps(taikai_data, ensure_ascii=False, indent=2))
            
            # Taikai.jsonから大会情報を抽出
            competition_info = {
                'name': None,
                'date': None,
                'year': None
            }
            
            # TaikaiMeiまたはTaikaiMeiKikanから大会名を取得
            if 'TaikaiMei' in taikai_data and taikai_data['TaikaiMei']:
                competition_info['name'] = _clean_competition_name(taikai_data['TaikaiMei'])
                print(f"🎯 Taikai.jsonから大会名取得: {competition_info['name']}")
            elif 'TaikaiMeiKikan' in taikai_data and taikai_data['TaikaiMeiKikan']:
                # TaikaiMeiKikanから大会名部分を抽出（日付部分を除去）
                full_name = taikai_data['TaikaiMeiKikan']
                # 日付パターンを除去して大会名のみを取得
                cleaned_name = re.sub(r'\s*\d{4}/\d{1,2}/\d{1,2}.*$', '', full_name)
                competition_info['name'] = _clean_competition_name(cleaned_name)
                print(f"🎯 Taikai.jsonのTaikaiMeiKikanから大会名取得: {competition_info['name']}")
            
            # Kikanから日程を取得
            if 'Kikan' in taikai_data and taikai_data['Kikan']:
                date_str = taikai_data['Kikan']
                formatted_date = _format_date(date_str)
                if formatted_date:
                    competition_info['date'] = formatted_date
                    # 年を抽出
                    year_match = re.search(r'(\d{4})', formatted_date)
                    if year_match:
                        competition_info['year'] = int(year_match.group(1))
                    print(f"📅 Taikai.jsonから日程取得: {competition_info['date']}")
            
            # 大会名が取得できた場合は即座に返す
            if competition_info['name']:
                return competition_info
        else:
            print(f"⚠️ Taikai.json取得失敗: {response.status_code}")
        
        # 方法2: TimeTable.jsonから大会情報を取得
        print(f"🔍 JSON URL: {json_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': timetable_url
        }
        
        response = requests.get(json_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ JSON取得失敗: {response.status_code}")
            return None
        
        data = response.json()
        print(f"📋 JSONキー: {list(data.keys()) if isinstance(data, dict) else 'リスト形式'}")
        
        # JSONデータの全体を表示（デバッグ用）
        import json
        print(f"📄 JSON全体データ:")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        # 大会情報を格納する辞書
        competition_info = {
            'name': None,
            'date': None,
            'year': None
        }
        
        # 大会名の候補となるフィールドを確認
        possible_name_fields = [
            'TAIKAI_NAME', 'TAIKAIMEI', 'COMPETITION_NAME', 'TITLE', 'NAME', 
            'TAIKAI', 'CompetitionName', 'KYOGIKAIMEI', 'MEET_NAME', 'EVENT_NAME'
        ]
        
        # 日程の候補となるフィールドを確認
        possible_date_fields = [
            'DATE', 'HIDUKE', 'KAISAIBI', 'NITTEI', 'START_DATE', 'EVENT_DATE'
        ]
        
        # トップレベルのフィールドを検索
        for field in possible_name_fields:
            if field in data and data[field] and not competition_info['name']:
                name = str(data[field]).strip()
                print(f"🎯 大会名候補発見 ({field}): {name}")
                if name and len(name) > 1:
                    competition_info['name'] = _clean_competition_name(name)
        
        for field in possible_date_fields:
            if field in data and data[field] and not competition_info['date']:
                date = str(data[field]).strip()
                print(f"📅 日程候補発見 ({field}): {date}")
                formatted_date = _format_date(date)
                if formatted_date:
                    competition_info['date'] = formatted_date
                    # 年を抽出
                    year_match = re.search(r'(\d{4})', formatted_date)
                    if year_match:
                        competition_info['year'] = int(year_match.group(1))
        
        # 全てのキーを表示してデバッグ
        if isinstance(data, dict):
            print(f"📝 利用可能なキー:")
            for key, value in data.items():
                if isinstance(value, str) and len(value) > 0 and len(value) < 200:
                    print(f"   {key}: {value[:100]}...")
                elif isinstance(value, dict):
                    print(f"   {key}: {{dict with {len(value)} keys}}")
                elif isinstance(value, list):
                    print(f"   {key}: [list with {len(value)} items]")
        
        # NitteiListから大会情報を探す
        if 'NitteiList' in data and isinstance(data['NitteiList'], list):
            for i, nittei in enumerate(data['NitteiList']):
                if isinstance(nittei, dict):
                    print(f"📅 日程情報 {i}: {nittei}")
                    
                    # 全てのキーから文字列を探す
                    for key, value in nittei.items():
                        if isinstance(value, str) and value.strip():
                            value = value.strip()
                            print(f"   📝 {key}: {value}")
                            
                            # 大会名らしい文字列を探す
                            if not competition_info['name'] and _looks_like_competition_name(value):
                                print(f"🎯 大会名候補発見 (NitteiList[{i}].{key}): {value}")
                                competition_info['name'] = _clean_competition_name(value)
                    
                    # 日程情報から日付を探す
                    for field in ['DATE', 'HIDUKE', 'KAISAIBI', 'NITTEI']:
                        if field in nittei and nittei[field] and not competition_info['date']:
                            date = str(nittei[field]).strip()
                            print(f"📅 日程から日付候補発見 ({field}): {date}")
                            formatted_date = _format_date(date)
                            if formatted_date:
                                competition_info['date'] = formatted_date
                                year_match = re.search(r'(\d{4})', formatted_date)
                                if year_match:
                                    competition_info['year'] = int(year_match.group(1))
        
        # TimeTableListから大会情報を探す
        if 'TimeTableList' in data and isinstance(data['TimeTableList'], dict):
            timetable_data = data['TimeTableList']
            print(f"⏰ タイムテーブル情報: {list(timetable_data.keys())}")
            for key, value in timetable_data.items():
                if isinstance(value, str) and len(value) > 3:
                    print(f"🎯 タイムテーブルから候補 ({key}): {value}")
                    if not competition_info['name'] and _looks_like_competition_name(value):
                        competition_info['name'] = _clean_competition_name(value)
        
        # KyogiListの全ての要素から大会情報を探す
        if 'KyogiList' in data and isinstance(data['KyogiList'], list) and len(data['KyogiList']) > 0:
            print(f"🏃 競技リスト要素数: {len(data['KyogiList'])}")
            
            # 最初の数個の要素を詳しく調べる
            for i, kyogi in enumerate(data['KyogiList'][:3]):
                if isinstance(kyogi, dict):
                    print(f"🏃 競技情報 {i}: {list(kyogi.keys())}")
                    
                    # 全てのキーから文字列を探す
                    for key, value in kyogi.items():
                        if isinstance(value, str) and value.strip():
                            value = value.strip()
                            if len(value) > 3:
                                print(f"   📝 {key}: {value}")
                                
                                # 大会名らしい文字列を探す
                                if not competition_info['name'] and _looks_like_competition_name(value):
                                    print(f"🎯 大会名候補発見 (KyogiList[{i}].{key}): {value}")
                                    competition_info['name'] = _clean_competition_name(value)
                    
                    # 日付情報も探す
                    for field in ['DATE', 'HIDUKE', 'KAISAIBI']:
                        if field in kyogi and kyogi[field] and not competition_info['date']:
                            date = str(kyogi[field]).strip()
                            print(f"📅 競技から日付候補発見 ({field}): {date}")
                            formatted_date = _format_date(date)
                            if formatted_date:
                                competition_info['date'] = formatted_date
                                year_match = re.search(r'(\d{4})', formatted_date)
                                if year_match:
                                    competition_info['year'] = int(year_match.group(1))
        
        # ネストされたオブジェクトからも検索
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, dict):
                    for field in possible_name_fields:
                        if field in value and value[field] and not competition_info['name']:
                            name = str(value[field]).strip()
                            print(f"🎯 ネスト大会名候補発見 ({key}.{field}): {name}")
                            if name and len(name) > 1:
                                competition_info['name'] = _clean_competition_name(name)
                    
                    for field in possible_date_fields:
                        if field in value and value[field] and not competition_info['date']:
                            date = str(value[field]).strip()
                            print(f"📅 ネスト日付候補発見 ({key}.{field}): {date}")
                            formatted_date = _format_date(date)
                            if formatted_date:
                                competition_info['date'] = formatted_date
                                year_match = re.search(r'(\d{4})', formatted_date)
                                if year_match:
                                    competition_info['year'] = int(year_match.group(1))
        
        # 大会名が取得できた場合のみ返す
        if competition_info['name']:
            return competition_info
        
        return None
        
    except Exception as e:
        print(f"❌ JSON解析エラー: {e}")
        return None


def _get_info_from_html(timetable_url: str) -> Optional[Dict]:
    """HTMLページから大会情報を取得"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(timetable_url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"⚠️ HTML取得失敗: {response.status_code}")
            return None
        
        # 文字エンコーディングを調整
        if response.encoding in ['ISO-8859-1', 'ascii']:
            response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        competition_info = {
            'name': None,
            'date': None,
            'year': None
        }
        
        # titleタグから取得
        title = soup.find('title')
        if title and title.text and not competition_info['name']:
            title_text = title.text.strip()
            # タイトルから大会名部分を抽出
            cleaned_title = _extract_competition_name_from_title(title_text)
            if cleaned_title:
                competition_info['name'] = cleaned_title
        
        # h1タグから取得（ナビゲーション要素を除外）
        h1_tags = soup.find_all('h1')
        for h1 in h1_tags:
            if h1.text and h1.text.strip() and not competition_info['name']:
                name = h1.text.strip()
                # ナビゲーション要素を除外
                if _is_navigation_text(name):
                    continue
                cleaned_name = _clean_competition_name(name)
                if cleaned_name and len(cleaned_name) > 5:
                    competition_info['name'] = cleaned_name
        
        # h2タグから取得（ナビゲーション要素を除外）
        h2_tags = soup.find_all('h2')
        for h2 in h2_tags:
            if h2.text and h2.text.strip() and not competition_info['name']:
                name = h2.text.strip()
                # ナビゲーション要素を除外
                if _is_navigation_text(name):
                    continue
                cleaned_name = _clean_competition_name(name)
                if cleaned_name and len(cleaned_name) > 5:
                    competition_info['name'] = cleaned_name
        
        # h3タグからも検索
        h3_tags = soup.find_all('h3')
        for h3 in h3_tags:
            if h3.text and h3.text.strip() and not competition_info['name']:
                name = h3.text.strip()
                if _is_navigation_text(name):
                    continue
                cleaned_name = _clean_competition_name(name)
                if cleaned_name and len(cleaned_name) > 8:  # h3はより厳しい条件
                    competition_info['name'] = cleaned_name
        
        # メタタグから取得
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            if meta.get('name') in ['description', 'title', 'og:title'] and not competition_info['name']:
                content = meta.get('content', '')
                if content:
                    cleaned_content = _extract_competition_name_from_title(content)
                    if cleaned_content and len(cleaned_content) > 5:
                        competition_info['name'] = cleaned_content
        
        # class名に'title'や'name'が含まれる要素から取得（ナビゲーション除外）
        for class_name in ['title', 'name', 'competition', 'taikai', 'event', 'header']:
            if competition_info['name']:
                break
            elements = soup.find_all(class_=lambda x: x and class_name in x.lower())
            for element in elements:
                if element.text and element.text.strip() and not competition_info['name']:
                    name = element.text.strip()
                    if _is_navigation_text(name):
                        continue
                    cleaned_name = _clean_competition_name(name)
                    if cleaned_name and len(cleaned_name) > 8:
                        competition_info['name'] = cleaned_name
                        break
        
        # 日付情報をHTMLから探す
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})/(\d{1,2})/(\d{1,2})',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
        ]
        
        html_text = soup.get_text()
        for pattern in date_patterns:
            if not competition_info['date']:
                matches = re.findall(pattern, html_text)
                if matches:
                    year, month, day = matches[0]
                    competition_info['date'] = f"{year}年{int(month)}月{int(day)}日"
                    competition_info['year'] = int(year)
                    break
        
        # 大会名が取得できた場合のみ返す
        if competition_info['name']:
            return competition_info
        
        return None
        
    except Exception as e:
        print(f"❌ HTML解析エラー: {e}")
        return None


def _get_info_from_url(timetable_url: str) -> Optional[Dict]:
    """URLパスから大会情報を推測"""
    try:
        parsed_url = urlparse(timetable_url)
        path_parts = parsed_url.path.split('/')
        
        # URLパスから年度と月日を抽出
        year = None
        date_part = None
        full_year = None
        month = None
        day = None
        
        for part in path_parts:
            # 年度情報の抽出 (htmlR6など)
            year_match = re.search(r'html[A-Z]?(\d+)', part)
            if year_match:
                year_num = int(year_match.group(1))
                if year_num >= 1:  # R1以降
                    year = 2018 + year_num  # R1=2019, R2=2020, ...
                continue
            
            # 日付情報の抽出 (240727など)
            if re.match(r'^\d{6}$', part):  # YYMMDD形式
                year_part = int(part[:2])
                month = int(part[2:4])
                day = int(part[4:6])
                
                # 年の推測（20XX年代）
                if year_part < 50:
                    full_year = 2000 + year_part
                else:
                    full_year = 1900 + year_part
                
                date_part = f"{full_year}年{month}月{day}日"
                if not year:  # 他で年度が取得できていない場合
                    year = full_year
        
        # 大会情報を構築
        competition_info = {
            'name': None,
            'date': date_part,
            'year': year or full_year
        }
        
        # 基本的な大会名を構築
        if year and date_part:
            competition_info['name'] = f"{year}年度大会"
        elif year:
            competition_info['name'] = f"{year}年度大会"
        elif date_part:
            competition_info['name'] = "大会"
        
        if competition_info['name']:
            return competition_info
        
        return None
        
    except Exception as e:
        print(f"❌ URL解析エラー: {e}")
        return None


def _extract_competition_name_from_title(title_text: str) -> Optional[str]:
    """タイトルテキストから大会名部分を抽出"""
    try:
        # 不要な部分を除去
        cleaned = title_text
        
        # 一般的な不要文字列を除去
        remove_patterns = [
            r'\s*-\s*タイムテーブル.*$',
            r'\s*-\s*TimeTable.*$',
            r'\s*タイムテーブル.*$',
            r'\s*TimeTable.*$',
            r'\s*-\s*結果.*$',
            r'\s*結果.*$',
            r'^\s*陸上競技\s*',
            r'\s*陸上競技.*$',
            r'\s*-\s*大会結果.*$',
            r'\s*大会結果.*$',
            r'\s*記録.*$',
            r'\s*リザルト.*$',
            r'\s*Result.*$',
            r'\s*競技結果.*$'
        ]
        
        for pattern in remove_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = cleaned.strip()
        
        # ナビゲーション要素でないかチェック
        if _is_navigation_text(cleaned):
            return None
        
        if len(cleaned) > 5:  # 最低限の長さがある場合のみ返す
            return _clean_competition_name(cleaned)
        
        return None
        
    except Exception as e:
        print(f"❌ タイトル解析エラー: {e}")
        return None


def _clean_competition_name(name: str) -> str:
    """大会名をクリーンアップ"""
    try:
        # HTMLエンティティのデコード
        name = name.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        name = name.replace('&nbsp;', ' ').replace('&#8203;', '')
        
        # 余分な空白を除去
        name = re.sub(r'\s+', ' ', name).strip()
        
        # 前後の不要な文字を除去
        name = name.strip('- \t\n\r')
        
        return name
        
    except Exception as e:
        print(f"❌ 名前クリーンアップエラー: {e}")
        return name


def _is_navigation_text(text: str) -> bool:
    """テキストがナビゲーション要素かどうかを判定"""
    if not text:
        return True
    
    # ナビゲーションによく使われるキーワードパターン
    navigation_patterns = [
        r'全て\s+ﾄﾗｯｸ\s+跳躍',  # 「全て ﾄﾗｯｸ 跳躍」
        r'男子\s+女子',  # 「男子 女子」
        r'ﾀｲﾑﾚｰｽ集計',  # 「ﾀｲﾑﾚｰｽ集計」
        r'混成集計',
        r'対抗戦集計',
        r'ｺﾝﾃﾞｨｼｮﾝ',
        r'投てき',
        r'^(全て|男子|女子|ﾄﾗｯｸ|跳躍|投てき)(\s+(全て|男子|女子|ﾄﾗｯｸ|跳躍|投てき))*$',
    ]
    
    # ナビゲーション要素の特徴
    navigation_features = [
        len(text.split()) > 8,  # 単語数が多すぎる
        'ﾄﾗｯｸ' in text and '跳躍' in text and '投てき' in text,  # 競技種目の羅列
        text.count('集計') >= 2,  # 「集計」が複数回出現
        all(word in text for word in ['全て', '男子', '女子']),  # フィルタ要素
    ]
    
    # パターンマッチング
    for pattern in navigation_patterns:
        if re.search(pattern, text):
            return True
    
    # 特徴による判定
    if any(navigation_features):
        return True
    
    return False


def _format_date(date_string: str) -> str:
    """日付フォーマットを整形"""
    try:
        if not date_string:
            return ""
        
        # YYYYMMDD形式
        if len(date_string) == 8 and date_string.isdigit():
            year = date_string[:4]
            month = date_string[4:6]
            day = date_string[6:8]
            return f"{year}年{int(month)}月{int(day)}日"
        
        # YYYY-MM-DD形式
        if re.match(r'^\d{4}-\d{2}-\d{2}$', date_string):
            year, month, day = date_string.split('-')
            return f"{year}年{int(month)}月{int(day)}日"
        
        # YYYY/MM/DD形式
        if re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', date_string):
            year, month, day = date_string.split('/')
            return f"{year}年{int(month)}月{int(day)}日"
        
        # 既に日本語形式の場合
        if '年' in date_string and '月' in date_string and '日' in date_string:
            return date_string
        
        return date_string
        
    except:
        return date_string


def _looks_like_competition_name(text: str) -> bool:
    """文字列が大会名らしいかどうかを判定"""
    if not text or len(text) < 4:
        return False
    
    # 明らかに大会名でないものを除外
    exclude_patterns = [
        r'^\d+$',  # 純粋な数字
        r'^[A-Z]+$',  # 大文字のみ
        r'^[a-z]+$',  # 小文字のみ
        r'^[\d\-/]+$',  # 日付のみ
        r'^(男子|女子)$',  # 性別のみ
        r'^(予選|決勝|準決勝)$',  # ラウンドのみ
        r'^(ﾄﾗｯｸ|跳躍|投てき)$',  # 種目カテゴリのみ
        r'^(タイムレース|ﾀｲﾑﾚｰｽ)$',  # 競技形式のみ
    ]
    
    for pattern in exclude_patterns:
        if re.match(pattern, text):
            return False
    
    # 大会名によく含まれるキーワード
    competition_keywords = [
        '大会', '選手権', '競技会', '記録会', '陸上', 'Championships',
        '学生', '関西', '全国', '地区', '県', '市', '町', '学連',
        '新人', 'ルーキー', 'チャレンジ', 'オープン', '招待',
        '春季', '夏季', '秋季', '冬季', '第', '回'
    ]
    
    # キーワードが含まれているかチェック
    for keyword in competition_keywords:
        if keyword in text:
            return True
    
    # 年と何らかの大会らしい文字が含まれている
    if re.search(r'\d{4}', text) and len(text) > 8:
        return True
    
    # 漢字が多く含まれていて、一定の長さがある
    kanji_count = len(re.findall(r'[\u4e00-\u9faf]', text))
    if kanji_count >= 3 and len(text) >= 6:
        return True
    
    return False


def main():
    """メイン実行関数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print(f"python {sys.argv[0]} <大会URL>")
        print("")
        print("例:")
        print(f'python {sys.argv[0]} "https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html"')
        sys.exit(1)
    
    timetable_url = sys.argv[1]
    
    print(f"🏆 大会情報取得システム")
    print(f"🔗 対象URL: {timetable_url}")
    print()
    
    competition_info = get_competition_info(timetable_url)
    
    if competition_info:
        print(f"\n🎉 大会情報取得成功!")
        print(f"📅 大会名: {competition_info['name']}")
        if competition_info['date']:
            print(f"📆 開催日: {competition_info['date']}")
        if competition_info['year']:
            print(f"🗓️  開催年: {competition_info['year']}")
        print(f"🔍 情報取得元: {competition_info['source']}")
        
        # JSON形式でも出力
        print(f"\n📋 JSON形式:")
        import json
        print(json.dumps(competition_info, ensure_ascii=False, indent=2))
    else:
        print("\n❌ 大会情報を取得できませんでした")


if __name__ == "__main__":
    main()
