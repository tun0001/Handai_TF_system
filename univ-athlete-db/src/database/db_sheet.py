import gspread
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from pathlib import Path 
import os
import math
import re
import time


def load_com_urls() -> list[str]:
    # プロジェクトルートからの相対パス
    file_path = Path('univ-athlete-db/database/com_url.txt')
    with file_path.open(encoding='utf-8') as f:
        # 空行を除いて先頭・末尾の改行をstrip
        return [line.strip() for line in f if line.strip()]

def load_member_list(output_file="/workspaces/Handai_TF_system/univ-athlete-db/database/member_list.txt") -> list[str]:
    """
    指定されたファイルからメンバーリストを読み込み、リストとして返す。
    ファイルが存在しない場合は空のリストを返す。
    """
    if not os.path.exists(output_file):
        return []
    
    with open(output_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def add_member_list(name, output_file="/workspaces/Handai_TF_system/univ-athlete-db/database/member_list.txt"):
    """
    指定されたファイルにnameを一番上に追加する（重複があれば移動のみ）。
    """
    members = []
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            members = [line.strip() for line in f if line.strip()]
    # 既存リストからnameを除外し、先頭に追加
    members = [m for m in members if m != name]
    members.insert(0, name)
    with open(output_file, "w", encoding="utf-8") as f:
        for m in members:
            f.write(m + "\n")

def load_conference_list(output_file="/workspaces/Handai_TF_system/univ-athlete-db/database/conference_list.txt") -> list[str]:
    """
    指定されたファイルから大会リストを読み込み、リストとして返す。
    ファイルが存在しない場合は空のリストを返す。
    """
    if not os.path.exists(output_file):
        return []
    
    with open(output_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def add_conference_list(conference_name, output_file="/workspaces/Handai_TF_system/univ-athlete-db/database/conference_list.txt"):
    """
    指定されたファイルに大会名を一番上に追加する（重複があれば移動のみ）。
    """
    conferences = []
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            conferences = [line.strip() for line in f if line.strip()]
    # 既存リストからconference_nameを除外し、先頭に追加
    conferences = [c for c in conferences if c != conference_name]
    conferences.insert(0, conference_name)
    with open(output_file, "w", encoding="utf-8") as f:
        for c in conferences:
            f.write(c + "\n")

def load_event_list(output_file="/workspaces/Handai_TF_system/univ-athlete-db/database/event_list.txt") -> list[str]:
    """
    指定されたファイルから競技名リストを読み込み、リストとして返す。
    ファイルが存在しない場合は空のリストを返す。
    """
    if not os.path.exists(output_file):
        return []
    
    with open(output_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def add_event_list(event_name, output_file="/workspaces/Handai_TF_system/univ-athlete-db/database/event_list.txt"):
    """
    指定されたファイルに競技名を追加する。
    既に存在する場合は何もしない。
    """
    # 既存の競技名をセットとして読み込む
    existing_events = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                existing_events.add(line.strip())
    
    if event_name in existing_events:
        return  # 既に存在する場合は何もしない
    
    # ファイルに追記
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(event_name + "\n")

def reset_sheets(
    spreadsheet_id: str,
    sheet_names: list[str],
    cred_dict: dict | None = None,
):
    """
    指定されたスプレッドシートの指定シート以外をすべて削除する，
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    
    # すべてのワークシートを取得
    all_worksheets = sh.worksheets()
    
    for worksheet in all_worksheets:
        if worksheet.title not in sheet_names:
            time.sleep(0.5)  # API制限を避けるために少し待機
            sh.del_worksheet(worksheet)
            print(f"Deleted worksheet: {worksheet.title}")
        else:
            print(f"Kept worksheet: {worksheet.title}")

def deduplicate_sheet(
        spreadsheet_id: str,
        sheet_name: str,
        cred_dict: dict | None = None,
):
    """
    指定されたスプレッドシートの指定シートから重複行を削除する
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    
    try:
        worksheet = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{sheet_name}' not found in spreadsheet '{spreadsheet_id}'.")
        return

    # シートの全データ取得（2次元リスト）
    data = worksheet.get_all_values()
    
    if not data or len(data) < 2:
        print("No data to deduplicate.")
        return
    
    # ヘッダーを除いたデータ部分をDataFrameに変換
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # 重複行を削除する処理を関数化
    def remove_duplicates_from_df(df: pd.DataFrame) -> pd.DataFrame:
        return df.drop_duplicates()
    
    df_deduped = remove_duplicates_from_df(df)
    
    # 更新するデータをリスト形式に変換
    updated_data = [df_deduped.columns.tolist()] + df_deduped.values.tolist()
    
    # シートを更新
    worksheet.clear()  # 既存のデータをクリア
    worksheet.update('A1', updated_data)  # 新しいデータを書き込む

def check_sheet_exists(
    spreadsheet_id: str,
    sheet_name: str,
    cred_dict: dict | None = None,
) -> bool:
    """
    指定されたスプレッドシートに指定シートが存在するか確認する
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    
    try:
        sh.worksheet(sheet_name)
        return True
    except gspread.exceptions.WorksheetNotFound:
        return False

def delete_sheet(
    spreadsheet_id: str,
    sheet_name: str,
    cred_dict: dict | None = None,
):
    """
    指定されたスプレッドシートから指定シートを削除する
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    
    try:
        worksheet = sh.worksheet(sheet_name)
        sh.del_worksheet(worksheet)
        print(f"Worksheet '{sheet_name}' deleted successfully.")
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{sheet_name}' not found in spreadsheet '{spreadsheet_id}'.")

def merge_sheets(
    spreadsheet_id: str,
    source_sheet_name: str,
    target_sheet_name: str,
    cred_dict: dict | None = None,
):
    """
    指定されたスプレッドシートの source_sheet_name の内容を target_sheet_name にマージする
    cred_dict: 認証情報の辞書形式
    既存シートの場合はヘッダーがなければ追加し、データはヘッダー以外を追加する
    シートの既存ヘッダーとdataのカラムが異なる場合は、ヘッダーを拡張し、データを適切な列に格納する
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    
    try:
        source_worksheet = sh.worksheet(source_sheet_name)
        target_worksheet = sh.worksheet(target_sheet_name)
    except gspread.exceptions.WorksheetNotFound as e:
        print(f"Worksheet not found: {e}")
        return
    
    # ソースシートの全データ取得（2次元リスト）
    source_data = source_worksheet.get_all_values()
    if not source_data or len(source_data) < 2:
        print("No data to merge.")
        return
    source_header = source_data[0]
    source_df = pd.DataFrame(source_data[1:], columns=source_header)
    
    # ターゲットシートの全データ取得（2次元リスト）
    target_data = target_worksheet.get_all_values()
    if not target_data:
        # ヘッダーがなければ追加し、データはヘッダー以外を追加する
        merged_header = list(source_header)
        merged_df = source_df.copy()
    else:
        target_header = target_data[0]
        merged_header = list(target_header)
        # ヘッダー拡張
        for col in source_header:
            if col not in merged_header:
                merged_header.append(col)
        # ターゲットデータをDataFrameに
        target_df = pd.DataFrame(target_data[1:], columns=target_header)
        # カラムを拡張したヘッダー順に揃える
        target_df = target_df.reindex(columns=merged_header)
        source_df = source_df.reindex(columns=merged_header)
        # マージして重複排除
        merged_df = pd.concat([target_df, source_df], ignore_index=True).drop_duplicates()
    
    # NoneやNaNを空文字に変換
    merged_df = merged_df.fillna("")
    updated_data = [merged_header] + merged_df.values.tolist()
    target_worksheet.clear()
    target_worksheet.update('A1', updated_data)

def write_to_new_sheet(
    spreadsheet_id: str,
    sheet_name: str | int,
    data,
    cred_dict: dict | None = None,
    num_rows: int = 100,
    num_cols: int = 26,
):
    """
    新規シートを作成して data を一括で書き込む
    既にシートが存在する場合は作成せず、そのまま利用する
    既存シートの場合はヘッダーがなければ追加し、データはヘッダー以外を追加する
    data: list[list], pandas.DataFrame, または dict (pandasのdict構造) を受け付ける
    シートの既存ヘッダーとdataのカラムが異なる場合は、ヘッダーを拡張し、データを適切な列に格納する
    新規シートの場合は、シートの順番は変更しない
    既存シートでもデータ追加後、シートの順番は変更しない
    """
    # dataをlist[list]形式に変換
    if isinstance(data, pd.DataFrame):
        data_df = data.reset_index(drop=True).copy()
    elif isinstance(data, dict):
        if all(not isinstance(v, (list, tuple, pd.Series, pd.Index, pd.DataFrame)) for v in data.values()):
            data_df = pd.DataFrame([data])
        else:
            data_df = pd.DataFrame(data)
    else:
        data_df = pd.DataFrame(data[1:], columns=data[0]) if data and isinstance(data[0], list) else pd.DataFrame(data)

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)

    sheet_name = str(sheet_name)[:100] # シート名は最大100文字に制限

    def flatten_row(row):
        flat = []
        for cell in row:
            if isinstance(cell, (list, dict, pd.Series, pd.DataFrame)):
                flat.append(str(cell))
            elif isinstance(cell, float) and (math.isnan(cell) or math.isinf(cell)):
                flat.append("")
            else:
                flat.append("" if pd.isnull(cell) else str(cell))
        return flat

    try:
        worksheet = sh.worksheet(sheet_name)
        existing_values = worksheet.get_all_values()
        if existing_values:
            existing_header = existing_values[0]
            data_header = list(data_df.columns)
            merged_header = list(existing_header)
            for col in data_header:
                if col not in merged_header:
                    merged_header.append(col)
            if merged_header != existing_header:
                worksheet.update('A1', [merged_header])
            start_row = len(existing_values) + 1
            data_rows_df = data_df.reindex(columns=merged_header)
            data_rows = [flatten_row(list(row)) for row in data_rows_df.values.tolist()]
        else:
            merged_header = list(data_df.columns)
            worksheet.update('A1', [merged_header])
            start_row = 2
            data_rows = [flatten_row(list(row)) for row in data_df.values.tolist()]
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=sheet_name, rows=str(num_rows), cols=str(num_cols))
        merged_header = list(data_df.columns)
        data_rows = [flatten_row(list(row)) for row in data_df.values.tolist()]
        worksheet.update('A1', [merged_header] + data_rows)
        return

    if data_rows:
        rows = len(data_rows)
        cols = len(merged_header)
        worksheet.resize(rows=start_row + rows - 1, cols=cols)
        worksheet.update(f'A{start_row}', data_rows)


#--------------
def sort_dataframe_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    '日付'列から年・月・日を抽出して昇順ソートしたDataFrameを返す
    """
    df = df.copy()
    df['年'] = df['日付'].str.extract(r'(\d{4})年')
    df['月'] = df['日付'].str.extract(r'(\d{1,2})月')
    df['日'] = df['日付'].str.extract(r'(\d{1,2})日')
    df['年'] = df['年'].astype(int)
    df['月'] = df['月'].astype(int)
    df['日'] = df['日'].astype(int)
    df_sorted = df.sort_values(by=['年', '月', '日'], ascending=True)
    return df_sorted

def get_season(df: pd.DataFrame) -> pd.DataFrame:
    """
    '日付'列からシーズンを抽出してDataFrameを返す
    """
    if '年' in df.columns:
        def get_season_name(year,month):
            if month in [1,2,3]:
                return year-1
            else:
                return year
        #season_list=df['年'].unique().tolist()

        df['season'] = df.apply(lambda row: get_season_name(row['年'], row['月']), axis=1)
        return df
    else:
        return df

# 重複行を削除する処理を関数化
def remove_duplicates_from_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates()

def reorder_columns_by_priority(df: pd.DataFrame) -> pd.DataFrame:
        """
        優先カラムリストに従ってDataFrameのカラム順を並べ替える
        """
        priority_columns = ['日付', 'No.', '氏名', '氏名_2','学年','チーム／メンバー','チーム／メンバー_2','チーム／メンバー_3', '所属', '種目', 'ラウンド', 'レーン','組','記録', '風', 'コメント', '大会']
        columns = df.columns.tolist()
        ordered_priority = [col for col in priority_columns if col in columns]
        remaining = [col for col in columns if col not in ordered_priority]
        new_columns = ordered_priority + remaining
        return df.reindex(columns=new_columns)

def get_event_name(df: pd.DataFrame) -> pd.DataFrame:
    """
    '種目'列から競技名を抽出してDataFrameを返す
    """
    if '種目' in df.columns:
        # 正規表現で競技名を抽出（例: 100m, 走幅跳, 円盤投げ など）
        def extract_event_name(event_name_1,event_name_2, type):
            # 全角→半角変換（数字・英字）
            event_name = event_name_2.translate(str.maketrans(
            '０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ×',
            '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzx'
            ))
            event_track_list = [
            "100m", "200m", "300m", "400m", "800m", "1500m", "3000m", "5000m", "10000m",
            ]
            event_wark_list=[
                "5000mW", "10000mW", "20kW", "50kmW"
            ]
            event_hardle_list = [
            "110mH", "300mH", "400mH", "3000mSC"
            ]
            event_relay_list = [
            "4x100mR", "4x400mR", "4x200mR", "4x800mR"
            ]
            event_field_list = [
            "走高跳", "走幅跳", "三段跳", "棒高跳",
            "砲丸投", "円盤投", "ハンマー投", "やり投"
            ]
            event_multi_list = [
            "十種競技", "七種競技"
            ]
            event_half_list = [
            "ハーフマラソン"
            ]

            # タイプに応じてリストを選択
            if "Track" in type:
                #print(event_name)
                for ev in event_track_list:
                    if ev in event_name:
                        return ev
            elif "Walk" in type:
                for ev in event_wark_list:
                    if ev in event_name:
                        return ev
            elif "Hurdle" in type:
                for ev in event_hardle_list:
                    if ev in event_name:
                        return ev
            elif "Relay" in type:
                for ev in event_relay_list:
                    if ev in event_name:
                        return ev
            elif "Jump" in type or "Throw" in type:
                for ev in event_field_list:
                    if ev in event_name:
                        return ev
            elif "Score" in type:
                for ev in event_multi_list:
                    if ev in event_name_1:
                        return ev
            elif "Half" in type:
                for ev in event_half_list:
                    if ev in event_name:
                        return ev
            else:
                # 上記に該当しない場合はパターン抽出
                m = re.search(r'(\d+\.?\d*[mcm]|[^\d\s]+)', event_name)
                return m.group(0) if m else ""

            # event_name = event_name.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
            # # 競技名のパターン: 数字+単位、または文字列
            # m = re.search(r'(\d+\.?\d*[mcm]|[^\d\s]+)', event_name)
            # return m.group(0) if m else ""
        
        df['event'] = df.apply(lambda row: extract_event_name(row['種目'],row['競技'], row['type']) if '競技' in row and 'type' in row else "", axis=1)
        return df
    else:
        return df

def get_grade_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    '学年'列を抽出してDataFrameを返す
    """
    if '氏名' in df.columns:
        # 正規表現で学年を抽出（例: (1), (M1), (D3) など）
        # 全角・半角の数字、英字、丸括弧・カッコ両対応
        # 例: (1), （１）, (M1), （Ｍ１）, (D3), （Ｄ３）など

        # 全角数字・英字を半角に変換する関数
        def z2h(text):
            if not isinstance(text, str):
                return text
            # 全角数字→半角
            text = text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
            # 全角英字→半角
            text = text.translate(str.maketrans('ＭＤ', 'MD'))
            return text

        # 正規表現で学年を抽出（全角・半角カッコ、数字・英字対応）
        # 例: (1), （１）, (M1), （Ｍ１）, (D3), （Ｄ３）など
        # ただし、(01)や(02)など2桁数字は学年ではなく生まれ年とみなして除外
        # (M1), (D3), (1) などのみ学年として抽出
        def extract_grade(name):
            # 全角→半角変換
            name = z2h(name)
            # 学年パターン: (M1), (D3), (1) など
            m = re.search(r'[（(]([MD]?\d)[）)]', name, flags=re.IGNORECASE)
            if m:
                return m.group(1)
            return ""
        df.loc[:, '学年'] = df['氏名'].apply(extract_grade)
        return df
    else:
        return df

def extract_wind(record):
    # +または-の直後の数値（例: +2.0, -1.5）を抽出
    m = re.search(r'([+-]\d+(?:\.\d+)?)', record)
    return m.group(1) if m else None

def remove_wind_from_record(record):
    # 例: '10.33+0.2' -> '10.33', '6m70+0.2' -> '6m70'
    m = re.match(r'^(\d+(?:m\d+)?(?:\.\d+)?)[+-]\d+\.\d+', record)
    if m:
        return m.group(1)
    # 風の値が含まれていない場合はそのまま
    return record

def extract_record(record):
    # 例: '1:00.37[ 1:00.370]' → '1:00.37'
    # まず 1:00.37 のような形式を優先
    m = re.search(r'(\d+:\d+\.\d+)', record)
    if m:
        return m.group(1)
    # 15.20[44.4] のような場合は [ の前の値を優先
    m = re.match(r'^([0-9.]+)\[', record)
    if m:
        return m.group(1)
    # 次に [ ] 内の値があればそれを使う
    m = re.search(r'\[ *([0-9:.]+) *\]', record)
    if m:
        return m.group(1)
    # それ以外は従来通り
    m = re.search(r'(\d+(?:m\d+)?(?:\.\d+)?)', record)
    return m.group(1) if m else None

def get_event_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    '種目'列から競技種目を抽出してDataFrameを返す
    """
    if '種目' in df.columns:
        def determine_event_type(event_name_1,event_name_2):
            if '種' in event_name_1 or '種' in event_name_2:
                if '跳' in event_name_2 :
                    event_mid = 'Jump'
                elif '投' in event_name_2:
                    event_mid = 'Throw'
                elif 'h' in event_name_2 or 'ｈ' in event_name_2 or 'H' in event_name_2 or 'Ｈ' in event_name_2:
                    event_mid = 'Hurdle'
                elif 'm' in event_name_2 or 'ｍ' in event_name_2 or 'M' in event_name_2 or 'Ｍ' in event_name_2:
                    event_mid = 'Track'
                else :
                    event_mid = 'Score'
                event_type = 'Mult' + ' ' + event_mid
            elif '跳' in event_name_1:
                event_type = 'Jump'
            elif 'R' in event_name_1 or 'Ｒ' in event_name_1 or '×' in event_name_1 or'x' in event_name_1:
                event_type = 'Relay'
            elif '投' in event_name_1:
                event_type = 'Throw'
            elif 'ハーフ' in event_name_1:
                event_type = 'Half'
            elif 'h' in event_name_1 or 'H' in event_name_1 or 'ｈ' in event_name_1 or 'Ｈ' in event_name_1 or 'S' in event_name_1 or 's' in event_name_1 or 'Ｓ' in event_name_1 or 'ｓ' in event_name_1:
                event_type = 'Hurdle'
            elif 'w' in event_name_1 or 'W' in event_name_1 or 'ｗ' in event_name_1 or 'Ｗ' in event_name_1:
                event_type = 'Walk'
            else:
                event_type = 'Track'
            return event_type
        
        df['type'] = df.apply(lambda row: determine_event_type(row['種目'], row['競技']) if '競技' in df.columns else row['種目'], axis=1)
        return df
    else:
        return df

def get_true_record(df: pd.DataFrame) -> pd.DataFrame:
    """
    '記録'列から数値部分を抽出してDataFrameを返す
    """
    if '記録' in df.columns:
        # 正規表現で数値部分を抽出（例: 10.33, 6m70, 5.0 など）
        df['記録(公式)'] = df['記録']  # 元の記録を保持
        wind_values = df['記録'].apply(extract_wind)
        # 風の値を省いた記録値を抽出
        # '風'列の更新
        if '風' not in df.columns:
            df['風'] = ""
        mask = wind_values.notnull()
        df.loc[mask, '風'] = wind_values[mask]
        # '記録'列から風の値を除去
        df['記録'] = df['記録'].apply(remove_wind_from_record)
        record_values = df['記録'].apply(extract_record)
        # '記録'列の更新
        df['記録'] = record_values
        return df
    else:
        return df

def get_compare_record(df: pd.DataFrame) -> pd.DataFrame:
    """
    '記録'列から比較用の数値部分を抽出してDataFrameを返す
    例:
      - "17:09.17" → 1709.17
      - "6m70" → 670
      - "10.33" → 10.33
      - "44.4" → 44.4
    """
    def extract_compare_record(record):
        if not isinstance(record, str):
            return None
        record = record.strip()
        # 時間形式 (例: 17:09.17, 1:00.370)
        m = re.match(r'^(\d+):(\d+)\.(\d+)$', record)
        if m:
            min_, sec, ms = m.groups()
            # 秒・ミリ秒を2桁ずつに揃えて連結
            return float(f"{int(min_):02d}{int(sec):02d}.{ms[:2].ljust(2, '0')}")
        # 跳躍・投擲形式 (例: 6m70)
        m = re.match(r'^(\d+)m(\d+)$', record)
        if m:
            m1, m2 = m.groups()
            return float(f"{int(m1)}{int(m2):02d}")
        # 小数形式 (例: 10.33, 44.4)
        m = re.match(r'^(\d+)\.(\d+)$', record)
        if m:
            n1, n2 = m.groups()
            n2 = n2[:2].ljust(2, '0')
            return float(f"{int(n1)}.{n2}")
        # 整数形式
        m = re.match(r'^(\d+)$', record)
        if m:
            return float(f"{int(m.group(1))}.00")
        return None

    if '記録' in df.columns:
        df['記録(比較)'] = df['記録'].apply(extract_compare_record)
        return df
    else:
        return df

def process_sheet(
    spreadsheet_id: str,
    sheet_name: str,
    creds_dict: dict | None = None,
):
    """
    指定されたスプレッドシートの指定シートをソートする
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    
    try:
        worksheet = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{sheet_name}' not found in spreadsheet '{spreadsheet_id}'.")
        return

    # シートの全データ取得（2次元リスト）
    data = worksheet.get_all_values()
    
    if not data or len(data) < 2:
        print("No data to sort.")
        return
    
    # ヘッダーを除いたデータ部分をDataFrameに変換
    df = pd.DataFrame(data[1:], columns=data[0])
    if '記録(公式)' in df.columns:
        df["記録"]=df["記録(公式)"]

    
    df_1=remove_duplicates_from_df(df)  # 重複行を削除
    df_2=get_grade_column(df_1)  # 学年列を抽出
    
    df_3 = reorder_columns_by_priority(df_2)  # 優先カ
    df_4 = get_true_record(df_3)  # 記録列から数値部分を抽出,風速を抽出
    df_5 = get_event_type(df_4)  # 種目列から競技種目を抽出
    df_6 = sort_dataframe_by_date(df_5)  # 日付でソート
    df_7 = get_season(df_6)  # シーズンを抽出
    df_8 = get_event_name(df_7)  # 種目名を抽出
    df_9 = get_compare_record(df_8)  # 比較用の記録を抽出
    df_10 = add_pb_column(df_9)  # PB列を追加
    df_11 = add_sb_column(df_10)  # SB列を追加
    
    df_sorted = df_11
    # ソート用のカラムを削除
    #df_sorted = df_sorted.drop(columns=['年', '月', '日'])

    # NaNを空文字に変換
    df_sorted = df_sorted.where(pd.notnull(df_sorted), "")

    # 更新するデータをリスト形式に変換
    updated_data = [df_sorted.columns.tolist()] + df_sorted.values.tolist()
    
    # シートを更新
    worksheet.clear()  # 既存のデータをクリア
    worksheet.update('A1', updated_data)  # 新しいデータを書き込む

def add_pb_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameからPB（Personal Best）を抽出して新しい列を追加する
    """
    df_pb = df
    event_list = df['event'].unique()
    df['PB'] = ""
    for event in event_list:
        df_event = df_pb[df_pb['event'] == event]
        if not df_event.empty:
            # '記録(比較)' 列が存在するか確認
            if '記録(比較)' not in df_event.columns:
                print("'記録(比較)' column not found in the DataFrame.")
                continue
            # 最小の記録(比較)を取得
            #print(event)
            #print(df_event['type'])
            # 'type'列の値に"Jump", "Throw", "Score"が含まれている行が1つでもあれば最大値を使用
            if df_event['type'].astype(str).str.contains('Jump|Throw|Score').any():
                # 跳躍・投擲・複合競技の場合は最大値を使用
                #print("Using max for PB calculation")
                if df_event['記録(比較)'].notna().any():
                    pb_idx = df_event['記録(比較)'].idxmax()
                else:
                    pb_idx = None
            else:
                if df_event['記録(比較)'].notna().any():
                    pb_idx = df_event['記録(比較)'].idxmin()
                else:
                    pb_idx = None

            if pb_idx is not None and not pd.isnull(pb_idx):
                if 'PB' not in df.columns:
                    df['PB'] = ""
                df.at[pb_idx, 'PB'] = "PB"
    return df

def add_sb_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameからSB（Season Best）を抽出して新しい列を追加する
    """
    if '年' not in df.columns or 'event' not in df.columns:
        print("'年' or 'event' column not found in the DataFrame.")
        return df
    season_list = df['年'].unique()
    df['SB'] = ""
    for season in season_list:
        df_season = df[df['season'] == season]
        event_list = df_season['event'].unique()
        for event in event_list:
            df_event = df_season[df_season['event'] == event]
            if not df_event.empty:
                # '記録(比較)' 列が存在するか確認
                if '記録(比較)' not in df_event.columns:
                    print("'記録(比較)' column not found in the DataFrame.")
                    continue
                # 最小の記録(比較)を取得
                if df_event['type'].astype(str).str.contains('Jump|Throw|Score').any():
                    # 跳躍・投擲競技の場合は最大値を使用
                    if df_event['記録(比較)'].notna().any():
                        sb_idx = df_event['記録(比較)'].idxmax()
                    else:
                        sb_idx = None
                else:
                    if df_event['記録(比較)'].notna().any():
                        sb_idx = df_event['記録(比較)'].idxmin()
                    else:
                        sb_idx = None
                if sb_idx is not None and not pd.isnull(sb_idx):
                    if 'SB' not in df.columns:
                        df['SB'] = ""
                    df.at[sb_idx, 'SB'] = "SB"
            else:
                df.loc[df['event'] == event, 'SB'] = None
    return df


def sort_column(
    spreadsheet_id: str,
    sheet_name: str,
    cred_dict: dict | None = None
    ):
    """
    指定されたスプレッドシートの指定シートをソートする
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    try:
        worksheet = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{sheet_name}' not found in spreadsheet '{spreadsheet_id}'.")
        return
    # シートの全データ取得（2次元リスト）
    data = worksheet.get_all_values()
    if not data or len(data) < 2:
        print("No data to sort.")
        return
    # ヘッダーを除いたデータ部分をDataFrameに変換
    

    df = pd.DataFrame(data[1:], columns=data[0])
    df_sorted = reorder_columns_by_priority(df)

    # 更新するデータをリスト形式に変換
    updated_data = [df_sorted.columns.tolist()] + df_sorted.values.tolist()
    
    # シートを更新
    worksheet.clear()  # 既存のデータをクリア
    worksheet.update('A1', updated_data)  # 新しいデータを書き込む

def get_official_record(
    spreadsheet_id: str,
    sheet_name: str,
    cred_dict: dict | None = None,
):
    """
    指定されたスプレッドシートの指定シートから公式記録を取得する
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    
    try:
        worksheet = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{sheet_name}' not found in spreadsheet '{spreadsheet_id}'.")
        return None

    # シートの全データ取得（2次元リスト）
    data = worksheet.get_all_values()
    
    if not data or len(data) < 2:
        print("No data found in the sheet.")
        return None
    
    # ヘッダーを除いたデータ部分をDataFrameに変換
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # '記録' 列が存在するか確認
    if '記録' not in df.columns:
        print("'記録' column not found in the sheet.")
        return None
    
    # 公式記録を取得（ここでは例として '記録' 列が最小の行を選ぶ）
    official_record_row = df.loc[df['記録'].idxmin()]
    
    return official_record_row

def get_grade_record(
    spreadsheet_id: str,
    sheet_name: str,
    cred_dict: dict | None = None,
):
    """
    指定されたスプレッドシートの指定シートからグレード記録を取得する
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    
    try:
        worksheet = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{sheet_name}' not found in spreadsheet '{spreadsheet_id}'.")
        return None

    # シートの全データ取得（2次元リスト）
    data = worksheet.get_all_values()
    
    if not data or len(data) < 2:
        print("No data found in the sheet.")
        return None
    
    # ヘッダーを除いたデータ部分をDataFrameに変換
    df = pd.DataFrame(data[1:], columns=data[0])
    
    # '記録' 列が存在するか確認
    if '記録' not in df.columns:
        print("'記録' column not found in the sheet.")
        return None
    
    # グレード記録を取得（ここでは例として '記録' 列が最大の行を選ぶ）
    grade_record_row = df.loc[df['記録'].idxmax()]
    
    return grade_record_row


def get_PB_UB_SB(
        df: pd.DataFrame,
)-> pd.DataFrame:
    """
    DataFrameからPB（Personal Best）、UB（University Best）、SB（Season Best）を抽出して新しい列を追加する
    """
    if '記録' not in df.columns:
        print("'記録' column not found in the DataFrame.")
        return df
    #PB
    

    #UB

    #SB
    
        

    
    
    return df.reset_index(drop=True)

def choose_best_sheet(
    spreadsheet_id_member: str,
    spreadsheet_id_best: str,
    member_list: list[str],
    sheet_name: str,
    cred_dict: dict | None = None,
):
    """
    指定されたスプレッドシートの指定シートから最適なデータを選択し、別のスプレッドシートに書き込む
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    
    # メンバーシートからデータ取得
    sh_member = client.open_by_key(spreadsheet_id_member)
    try:
        worksheet_member = sh_member.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        print(f"Worksheet '{sheet_name}' not found in spreadsheet '{spreadsheet_id_member}'.")
        return
    
    data_member = worksheet_member.get_all_values()
    
    if not data_member or len(data_member) < 2:
        print("No data to choose from.")
        return
    
    # ヘッダーを除いたデータ部分をDataFrameに変換
    df_member = pd.DataFrame(data_member[1:], columns=data_member[0])
    
    # 最適なデータを選択（ここでは例として '記録' 列が最小の行を選ぶ）
    best_row = df_member.loc[df_member['記録'].idxmin()]
    
    # ベストシートに書き込み
    sh_best = client.open_by_key(spreadsheet_id_best)
    
    try:
        worksheet_best = sh_best.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        worksheet_best = sh_best.add_worksheet(title=sheet_name, rows="100", cols="20")
    
    # 既存のデータをクリアして新しいデータを書き込む
    worksheet_best.clear()
    worksheet_best.update('A1', [df_member.columns.tolist(), best_row.tolist()])

if __name__ == "__main__":
    # サンプルデータ: '氏名'と'記録'列を含む
    df = pd.DataFrame([
        {'氏名': "那木　悠右 (1)Yusuke NAGI (03)", '記録': '6m34+2.0 (追風)'},
        {'氏名': "小林  恒方(M3)", '記録': '333-1.5 (向風)'},
        {'氏名': "田中 太郎", '記録': '15.20[44.4]'},
        {'氏名': "", '記録': '10.94[10.933]'},
        {'氏名': "佐藤 花子", '記録': '1:00.37[ 1:00.370]', '風': '0.0'},
    ])
    #df = get_wind_from_record(df)
    df = get_grade_column(df)
    df = get_true_record(df)
    df = get_compare_record(df)
    print(df)
    