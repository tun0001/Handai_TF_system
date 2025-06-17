import gspread
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from pathlib import Path 
import os

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

def add_member_list(name,output_file="/workspaces/Handai_TF_system/univ-athlete-db/database/mamber_list.txt"):

    # 既存のURLをセットとして読み込む
    existing_member = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                existing_member.add(line.strip())
    #print(existing_member)
    if name in existing_member:
        return
    # ファイルに追記（重複なし）
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(name + "\n")
    return

def add_conference_list(conference_name, output_file="/workspaces/Handai_TF_system/univ-athlete-db/database/conference_list.txt"):
    """
    指定されたファイルに大会名を追加する。
    既に存在する場合は何もしない。
    """
    # 既存の大会名をセットとして読み込む
    existing_conferences = set()
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            for line in f:
                existing_conferences.add(line.strip())
    
    if conference_name in existing_conferences:
        return  # 既に存在する場合は何もしない
    
    # ファイルに追記
    with open(output_file, "a", encoding="utf-8") as f:
        f.write(conference_name + "\n")

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

def sort_sheet(
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

def write_to_new_sheet(
    spreadsheet_id: str,
    sheet_name: str,
    data: list[list] | pd.DataFrame | dict,
    cred_dict: dict | None = None,
):
    """
    新規シートを作成して data を一括で書き込む
    既にシートが存在する場合は作成せず、そのまま利用する
    既存シートの場合はヘッダーがなければ追加し、データはヘッダー以外を追加する
    data: list[list], pandas.DataFrame, または dict (pandasのdict構造) を受け付ける
    シートの既存ヘッダーとdataのカラムが異なる場合は、ヘッダーを拡張し、データを適切な列に格納する
    """
    # dataをlist[list]形式に変換
    if isinstance(data, pd.DataFrame):
        data_df = data.copy()
    elif isinstance(data, dict):
        # Check if all values are scalars (not list/Series/array-like)
        if all(not isinstance(v, (list, tuple, pd.Series, pd.Index, pd.DataFrame)) for v in data.values()):
            data_df = pd.DataFrame([data])
        else:
            data_df = pd.DataFrame(data)
    else:
        # Assume list[list]
        data_df = pd.DataFrame(data[1:], columns=data[0]) if data and isinstance(data[0], list) else pd.DataFrame(data)

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    import time
    from gspread.exceptions import APIError

    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)
    time.sleep(1)

    # Retry logic for quota exceeded errors
    # for attempt in range(5):
    #     try:
    #         
    #         break
    #     except APIError as e:
    #         if "429" in str(e):
    #             wait_time = 20 * (attempt + 1)
    #             print(f"Quota exceeded. Retrying in {wait_time} seconds...")
    #             time.sleep(wait_time)
    #         else:
    #             raise
    # else:
    #     raise RuntimeError("Failed to open spreadsheet due to repeated quota errors.")

    # Ensure sheet_name is a string
    if isinstance(sheet_name, (pd.Series, pd.DataFrame)):
        sheet_name = str(sheet_name.values[0]) if hasattr(sheet_name, 'values') else str(sheet_name)
    else:
        sheet_name = str(sheet_name)

    try:
        worksheet = sh.worksheet(sheet_name)
        existing_values = worksheet.get_all_values()
        if existing_values:
            existing_header = existing_values[0]
            data_header = list(data_df.columns)
            # ヘッダーを統合
            merged_header = list(existing_header)
            for col in data_header:
                if col not in merged_header:
                    merged_header.append(col)
            # 必要ならヘッダーを更新
            if merged_header != existing_header:
                worksheet.update('A1', [merged_header])
            start_row = len(existing_values) + 1
            # データをmerged_header順に並べ替え
            data_rows = data_df.reindex(columns=merged_header)
            data_rows = data_rows.where(pd.notnull(data_rows), "").values.tolist()
        else:
            # ヘッダーがなければ追加
            merged_header = list(data_df.columns)
            worksheet.update('A1', [merged_header])
            start_row = 2
            data_rows = data_df.where(pd.notnull(data_df), "").values.tolist()
    except gspread.exceptions.WorksheetNotFound:
        worksheet = sh.add_worksheet(title=sheet_name, rows="100", cols="26")
        merged_header = list(data_df.columns)
        data_rows = data_df.where(pd.notnull(data_df), "").values.tolist()
        worksheet.update('A1', [merged_header] + data_rows)
        return

    # データがあれば追加
    if data_rows:
        rows = len(data_rows)
        cols = len(merged_header)
        worksheet.resize(rows=start_row + rows - 1, cols=cols)
        cell_range = gspread.utils.rowcol_to_a1(start_row, 1)
        worksheet.update(cell_range, data_rows)
