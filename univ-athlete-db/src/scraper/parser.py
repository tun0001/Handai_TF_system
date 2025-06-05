from bs4 import BeautifulSoup

"""
• parser  
  – HTML → Python データ構造への変換  
     • 競技者一覧ページの解析（parse_results_from_univ）  
     • 種目詳細ページの解析（parse_event_detail_for_player(_track)）  
     • 必要に応じたデータ整形・分類（コメントや風速、種目タイプの付与など）  
     – データの抽出・変換（extract_athlete_data）
    
ポイントは「fetcher は“どこから”取ってくるか」「parser は“どう読み解く”か」に専念させることです。これによりテストや保守がしやすくなります。
"""
def parse_event_finish(html, event_name, betsu, kubun):
    """
    指定した種目(event_name)、種別(betsu)、レース区分(kubun)の全行が
    「状況」列で '結果' になっているかを返す。
    """
    soup = BeautifulSoup(html, 'html.parser')
    found = False
    for table in soup.find_all('table'):
        #print(table)
        #print(table.get_text(strip=True))
        header = table.find('tr')
        if not header:
            continue
        cols = [th.get_text(strip=True) for th in header.find_all('th')]
        # 「種目」「種別」「レース区分」「状況」が揃っているテーブルのみ
        if not all(x in cols for x in ('種目','種別','レース区分','状況')):
            #print(cols)
            continue
        idx_event    = cols.index('種目')
        idx_betsu    = cols.index('種別')
        idx_division = cols.index('レース区分')
        idx_status   = cols.index('状況')
        #print(idx_betsu)
        #print(cols)

        statuses = []
        cur_name = cur_bet = cur_div = None
        for row in table.find_all('tr')[1:]:
            # colspan を考慮して列位置を再構築
            row_cells = []
            for td in row.find_all('td'):
                text = td.get_text(strip=True)
                span = int(td.get('colspan', 1))
                row_cells.extend([text] * span)
            # Status 列が存在しなければスキップ
            if idx_status >= len(row_cells):
                continue
            # rowspan の継承: 空文字出現時は前行の値を使用
            if idx_event < len(row_cells) and row_cells[idx_event]:
                cur_name = row_cells[idx_event]
            if idx_betsu < len(row_cells) and row_cells[idx_betsu]:
                cur_bet = row_cells[idx_betsu]
            if idx_division < len(row_cells) and row_cells[idx_division]:
                cur_div = row_cells[idx_division]
            # 該当条件なら status を記録
            if cur_name == event_name and cur_bet == betsu and cur_div == kubun:
                #print(f"Found: {cur_name}, {cur_bet}, {cur_div},{row_cells}")
                statuses.append(row_cells[idx_status])
        # 見つかった行があれば判定
        if statuses:
            found = True
            if any(s != '結果' for s in statuses):
                return False
    # 一度でも該当行があり、すべて「結果」なら True
    return found

def parse_conference_title(html):
    """
    競技者索引ページ(HTML)から大会名を取得して返す
    """
    soup = BeautifulSoup(html, 'html.parser')
    # <h1>タグのテキストを取得
    title_h3 = soup.find('table', class_='title').find('h3').get_text(separator=' ', strip=True)
    if not title_h3:
        raise ValueError("大会名が見つかりません")
    return title_h3

def parse_all_event_name_kyougi_itiran(html):
    """
    大会種目一覧ページ(HTML)から「種目」「種別」「レース区分」列を持つテーブルを探し、
    {'種目':…, '種別':…} のリストを返す
    """
    soup = BeautifulSoup(html, 'html.parser')
    events = []
    # 「種目」「種別」ヘッダーを持つテーブルだけを抽出し、
    # 各テーブルの最初のデータ行（[1]）から種目を取得
    for table in soup.find_all('table'):
        header = table.find('tr')
        if not header:
            continue
        cols = [th.get_text(strip=True) for th in header.find_all('th')]
        if '種目' not in cols or '種別' not in cols or '順位' in cols:
            continue
        idx_shumoku = cols.index('種目')
        idx_shubetsu = cols.index('種別')
        rows = table.find_all('tr')
        if len(rows) < 2:
            continue
        first = rows[1].find_all('td')
        if len(first) <= idx_shumoku:
            continue
        event_name = first[idx_shumoku].get_text(separator=' ', strip=True)
        a = first[idx_shumoku].find('a', href=True)
        href = a['href'].strip() if a else ''
        betsu = first[idx_shubetsu].get_text(strip=True)
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
            '種目': event_name,
            '種別': betsu,
            'type': event_type
        })
    # テーブルごとに1件ずつ、重複を気にせず返す
    return events

def parse_event_detail_for_player_track(html, player_name):
    """
    競技ページ(HTML)から指定選手(player_name)のレース情報を取得して辞書で返す
    取得項目: 順位、大会, 日付, 競技, ラウンド, 選手名, 記録, 風，コメント
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
    """
    競技者索引大学ページ(HTML)から指定大学(university_name)の競技結果テーブルを抽出してリストを返す
    """
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

def parse_all_event_name_kaisizikoku(html):
    """
    大会開始時刻ページ(HTML)から
    「種目」「種別」「レース区分」「開始時刻」列を持つテーブルを探し、
    各行を辞書で返す
    戻り値: [{'種目':…, '種別':…, 'レース区分':…, '開始時刻':…}, …]
    """
    soup = BeautifulSoup(html, 'html.parser')
    events = []
    # 全テーブルを走査
    for table in soup.find_all('table'):
        header = table.find('tr')
        if not header:
            continue
        cols = [th.get_text(strip=True) for th in header.find_all('th')]
        # 「種目」「レース区分」「開始時刻」全てを持つテーブルのみ
        if '種目' not in cols or 'レース区分' not in cols or '開始時刻' not in cols:
            continue
        idx_shumoku  = cols.index('種目')
        idx_kubun    = cols.index('レース区分')
        # 種別列はあれば取得
        idx_shubetsu = cols.index('種別') if '種別' in cols else None

        # データ行をパース
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            # 必要なカラム（種目・レース区分・開始時刻・（種別））が
            # すべて存在しない行はスキップ
            max_idx = max(
                idx_shumoku,
                idx_kubun,
                idx_shubetsu or 0
            )
            if len(cells) <= max_idx:
                continue
            event_name       = cells[idx_shumoku].get_text(strip=True)
            # 安全にレース区分・種別を取得
            kubun = cells[idx_kubun].get_text(strip=True) if idx_kubun < len(cells) else ''
            betsu = (
                cells[idx_shubetsu].get_text(strip=True)
                if idx_shubetsu is not None and idx_shubetsu < len(cells)
                else ''
            )
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
                '種目':       event_name,
                '種別':       betsu,
                'レース区分': kubun,
                'type' : event_type
            })
    return events

def find_university_link_and_count(html, university_name):
    """
    競技者索引(HTML)から指定された大学名(university_name)のリンクと人数を取得（完全一致）
    """
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

