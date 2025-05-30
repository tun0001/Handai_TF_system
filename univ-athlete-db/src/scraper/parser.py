from bs4 import BeautifulSoup


def parse_event_detail_for_player(html, player_name):
    """
    HTMLから指定選手のレース情報を取得して辞書で返す
    取得項目: 大会, 日付, 競技, ラウンド, 選手名, 記録, 風
    """
    soup = BeautifulSoup(html, 'html.parser')
    # 大会情報
    title_h3 = soup.find('table', class_='title').find('h3').get_text(separator=' ', strip=True)
    # 日付（<p class="h3-align">の最初のテキストノードを取得）
    p = soup.find('p', class_='h3-align')
    if not p:
        date_text = ''
    else:
        # 最初に現れる文字列を取得（改行や余白を除去）
        date_text = p.find(text=True).strip()

    # 競技とラウンド（<h1>を分割）
    h1 = soup.find('h1').get_text(strip=True)
    comps = h1.rsplit(' ', 1)
    competition = comps[0]
    round_ = comps[1] if len(comps) > 1 else ''
    # 風速と結果テーブル取得
    wind_div = soup.find('div', class_='wind')
    if wind_div:
        wind = wind_div.get_text(strip=True).replace('風:', '')
        table = wind_div.find_next_sibling('table')
    else:
        # 風速情報がない場合
        wind = ''
        # <a name="CONTENTS"> の次にある<table>を結果テーブルとみなす
        anchor = soup.find('a', attrs={'name': 'CONTENTS'})
        table = anchor.find_next_sibling('table') if anchor else soup.find('table')
    # カラムインデックス: [順位, レーン, No., 氏名(JP), 氏名(EN), 所属, 記録, コメント]
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if not cols:
            continue
        # 順位を取得
        rank = cols[0].get_text(strip=True)
        name_jp = cols[3].get_text(strip=True)
        if name_jp == player_name:
            record = cols[6].get_text(strip=True)
            comment = cols[7].get_text(strip=True)
            return {
                '順位': rank,
                '大会': title_h3,
                '日付': date_text,
                '競技': competition,
                'ラウンド': round_,
                '選手名': name_jp,
                '記録': record,
                'コメント': comment,
                '風': wind
            }
    raise ValueError(f"選手 '{player_name}' の結果が見つかりません")

def parse_results_from_univ(html, university_name):
    """HTMLから指定大学の競技結果テーブルを抽出してリストを返す"""
    soup = BeautifulSoup(html, 'html.parser')
    # 大学名を含む<div class="syozoku">を検索
    div_target = next(
        (d for d in soup.find_all('div', class_='syozoku')
         if university_name in d.get_text(strip=True)),
        None
    )
    if not div_target:
        raise ValueError(f"大学名 '{university_name}' の索引が見つかりません")
    # 対応する<table>タグを取得
    table = div_target.find_next_sibling('table')
    if not table:
        raise ValueError(f"大学名 '{university_name}' の結果テーブルが見つかりません")

    print(f"Found table with {len(table.find_all('tr'))} rows.")
    print(f"Table header: {table.find('tr').get_text(strip=True)}")

    results = []  # ヘッダー行を追加
    # テーブルの行を取得
    rows = table.find_all('tr')[0:]  # ヘッダー行をスキップ
    for row in rows:
        cols = row.find_all('td')
        if not cols:
            continue

        # 各列のデータを抽出
        athlete_number = cols[0].get_text(strip=True)
        name = cols[1].get_text(strip=True)
        gender = cols[3].get_text(strip=True)
        # 出場種目名とリンクを辞書で取得（Relay/Other分類追加）
        events = []
        for a in cols[4].find_all('a'):
            event_name = a.get_text(strip=True)
            href = a.get('href')
            # 跳を含む場合はJump、R/Ｒを含む場合はRelay、それ以外はOther
            if '種' in event_name:
                event_type = 'Mult'
            elif '跳' in event_name:
                event_type = 'Jump'
            elif 'R' in event_name or 'Ｒ' in event_name:
                event_type = 'Relay'
            
            elif '投' in event_name:
                event_type = 'Throw'
            elif 'ハーフ' in event_name:
                event_type = 'Half'
            else:
                event_type = 'Other'
            events.append({
                'name': event_name,
                'href': href,
                'type': event_type
            })

        results.append({
            '番号': athlete_number,
            '氏名': name,
            '性別': gender,
            '出場種目': events
        })

    return results


def find_university_link_and_count(html, university_name):
    """HTMLから指定された大学名のリンクと人数を取得（完全一致）"""
    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    if len(tables) < 2:
        raise ValueError("テーブルが見つかりません")
    
    table = tables[1]
    for row in table.find_all('tr'):
        # 完全一致で大学名を含む<a>タグを探す
        link = row.find('a', string=lambda txt: txt and txt.strip() == university_name)
        if link:
            href = link['href']
            cols = row.find_all('td')
            count = cols[-1].get_text(strip=True) if cols else None
            return href, count

    raise ValueError(f"大学名 '{university_name}' が見つかりません")

def extract_athlete_data(results):
    """選手の名前、種目、記録を抽出して辞書のリストを返す"""
    athlete_data = []
    for result in results:
        athlete_info = {
            'name': result.get('氏名') or result.get('選手'),
            'event': result.get('種目'),
            'record': result.get('記録')
        }
        athlete_data.append(athlete_info)
    return athlete_data