import gspread
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from pathlib import Path 
import os
import math

def load_com_urls() -> list[str]:
    # プロジェクトルートからの相対パス
    file_path = Path('univ-athlete-db/database/com_url.txt')
    with file_path.open(encoding='utf-8') as f:
        # 空行を除いて先頭・末尾の改行をstrip
        return [line.strip() for line in f if line.strip()]

def load_member_list(output_file="/workspaces/Handai_TF_system/univ-athlete-db/database/mamber_list.txt") -> list[str]:
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
            sh.del_worksheet(worksheet)
            print(f"Deleted worksheet: {worksheet.title}")
        else:
            print(f"Kept worksheet: {worksheet.title}")

def sort_sheet_byday(
    spreadsheet_id: str,
    sheet_name: str,
    cred_dict: dict | None = None,
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

    # '日付'列から年、月、日を抽出し、それぞれ新たなカラム '年', '月', '日' を作成
    df['年'] = df['日付'].str.extract(r'(\d{4})年')
    df['月'] = df['日付'].str.extract(r'(\d{1,2})月')
    df['日'] = df['日付'].str.extract(r'(\d{1,2})日')
    
    # ソート（ここでは例として1列目で昇順ソート）
    df_sorted = df.sort_values(by=df.columns[0], ascending=True)
    
    # 更新するデータをリスト形式に変換
    updated_data = [df_sorted.columns.tolist()] + df_sorted.values.tolist()
    
    # シートを更新
    worksheet.clear()  # 既存のデータをクリア
    worksheet.update('A1', updated_data)  # 新しいデータを書き込む

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
    
    # 重複行を削除
    df_deduped = df.drop_duplicates()
    
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
