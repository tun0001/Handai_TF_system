import gspread
from google.oauth2.service_account import Credentials
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from pathlib import Path 
import os
import math
import re
import time

def get_database_dir():
    """
    環境に依存しない形でデータベースディレクトリのパスを取得する
    """
    # Dockerコンテナ内の場合は絶対パス
    if os.path.exists('/univ-athlete-db/database'):
        return Path('/univ-athlete-db/database')
    
    # srcディレクトリからの相対パスを使用している場合
    elif os.path.exists('/app/univ-athlete-db/database'):
        return Path('/app/univ-athlete-db/database')
    
    # その他の環境（開発環境など）
    else:
        # カレントディレクトリからの相対パス
        current_dir = Path.cwd()
        # カレントディレクトリにsrcが含まれている場合は2階層上に移動
        if 'src' in str(current_dir):
            return (current_dir.parent.parent / 'univ-athlete-db/database').resolve()
        else:
            # それ以外の場合は直接相対パスを使用
            return Path('univ-athlete-db/database').resolve()

def load_com_urls() -> list[str]:
    # プロジェクトルートからの相対パス
    #file_path = Path('univ-athlete-db/database/com_url.txt')
    file_path = get_database_dir() / 'com_url.txt'
    with file_path.open(encoding='utf-8') as f:
        # 空行を除いて先頭・末尾の改行をstrip
        return [line.strip() for line in f if line.strip()]

def load_member_list(spreadsheet_ID_member, creds_dict) -> list[str]:
    member_list = load_sheet(
        spreadsheet_id=spreadsheet_ID_member,
        sheet_name="部員一覧",
        creds_dict=creds_dict
    )[['member_name']]
    return member_list['member_name'].tolist()

def add_member_list(name):
    """
    メンバーリストにnameを一番上に追加する（重複があれば移動のみ）。
    """
    #file_path = Path('.../univ-athlete-db/database/member_list.txt')
    
    file_path = get_database_dir() / 'member_list.txt'
    members = []
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as f:
            members = [line.strip() for line in f if line.strip()]
    # 既存リストからnameを除外し、先頭に追加
    members = [m for m in members if m != name]
    members.insert(0, name)
    with file_path.open("w", encoding="utf-8") as f:
        for m in members:
            f.write(m + "\n")

def load_conference_list() -> list[str]:
    """
    大会リストを読み込み、リストとして返す。
    ファイルが存在しない場合は空のリストを返す。
    """
    file_path = Path('univ-athlete-db/database/conference_list.txt')
    #file_path = get_database_dir() / 'conference_list.txt'
    try:
        with file_path.open(encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def add_conference_list(conference_name):
    """
    大会リストに大会名を一番上に追加する（重複があれば移動のみ）。
    """
    file_path = Path('univ-athlete-db/database/conference_list.txt')
    #file_path = get_database_dir() / 'conference_list.txt'
    conferences = []
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as f:
            conferences = [line.strip() for line in f if line.strip()]
    # 既存リストからconference_nameを除外し、先頭に追加
    conferences = [c for c in conferences if c != conference_name]
    conferences.insert(0, conference_name)
    with file_path.open("w", encoding="utf-8") as f:
        for c in conferences:
            f.write(c + "\n")

def load_event_list() -> list[str]:
    """
    競技名リストを読み込み、リストとして返す。
    ファイルが存在しない場合は空のリストを返す。
    """
    file_path = Path('univ-athlete-db/database/event_list.txt')
    #file_path = get_database_dir() / 'event_list.txt'
    try:
        with file_path.open(encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return []

def add_event_list(event_name):
    """
    競技名リストに競技名を追加する。
    既に存在する場合は何もしない。
    """
    #file_path = Path('univ-athlete-db/database/event_list.txt')
    file_path = get_database_dir() / 'event_list.txt'
    # 既存の競技名をセットとして読み込む
    existing_events = set()
    if file_path.exists():
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                existing_events.add(line.strip())
    
    if event_name in existing_events:
        return  # 既に存在する場合は何もしない
    
    # ファイルに追記
    with file_path.open("a", encoding="utf-8") as f:
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

def set_member_active(
    spreadsheet_id: str,
    member_name: str,
    cred_dict: dict | None = None,
    ):
    """
    スプレッドシートの部員一覧シートで指定されたメンバーのActiveカラムを"Active"に設定する
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)

    try:
        worksheet = sh.worksheet("部員一覧")
    except gspread.exceptions.WorksheetNotFound:
        # Worksheet not found, create it
        worksheet = sh.add_worksheet(title="部員一覧", rows="100", cols="20")
        print(f"Created new worksheet '部員一覧' in spreadsheet '{spreadsheet_id}'.")

    # シートの全データ取得
    data = worksheet.get_all_values()

    # if not data or len(data) < 2:
    #     print("No data found in the sheet.")
    #     return

    # DataFrameに変換
    df = pd.DataFrame(data[1:], columns=data[0])

    # member_nameカラムが存在するか確認
    if 'member_name' not in df.columns:
        # member_name column doesn't exist, create it with header
        df = pd.DataFrame(columns=['member_name'])
        print("Created new 'member_name' column in the sheet.")

    # Activeカラムが存在しない場合は追加
    if 'Active' not in df.columns:
        df['Active'] = ""

    # 指定されたメンバーのActiveカラムを"Active"に設定
    member_found = False
    for idx, row in df.iterrows():
        if row['member_name'] == member_name:
            df.at[idx, 'Active'] = "Active"
            member_found = True
            # メンバーの行を一番上に移動
            
            break

    if not member_found:
        # メンバーが見つからない場合は新しい行として追加
        new_row = pd.DataFrame({'member_name': [member_name], 'Active': ['Active']})
        df = pd.concat([new_row, df], ignore_index=True)
        print(f"Added new member '{member_name}' and set as Active.")
        #return
    
    member_row = df.loc[df['member_name'] == member_name].copy()
    df_without_member = df.loc[df['member_name'] != member_name].copy()
    df = pd.concat([member_row, df_without_member], ignore_index=True)
    # シートを更新
    print(df)
    # NaNを空文字に変換
    df = df.fillna("")
    updated_data = [df.columns.tolist()] + df.values.tolist()
    worksheet.clear()
    worksheet.update('A1', updated_data)
    print(f"Set '{member_name}' as Active in the member list.")

def write_member_record_to_sheet(
    spreadsheet_id: str,
    sheet_name: str | int,
    data,
    univ_name: str,
    cred_dict: dict | None = None,
    ):
    #-------------
    #部員一覧のsheet_nameをアクティブにする
    set_member_active(
        spreadsheet_id=spreadsheet_id,
        member_name=sheet_name,
        cred_dict=cred_dict
    )
    time.sleep(1)

    #----------------
    write_to_new_sheet(
        spreadsheet_id=spreadsheet_id,
        sheet_name=sheet_name,
        data=data,
        cred_dict=cred_dict
    )
    time.sleep(1)
    print(sheet_name)


    process_sheet(
        spreadsheet_id=spreadsheet_id,
        sheet_name=sheet_name,
        creds_dict=cred_dict,
        univ_name=univ_name
    )


def write_to_new_sheet(
    spreadsheet_id: str,
    sheet_name: str | int,
    data,
    cred_dict: dict | None = None,
    num_rows: int = 100,
    num_cols: int = 50,
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

def member_best_to_sheet(
    spreadsheet_id_member: str,
    spreadsheet_id_best: str,
    creds_dict: dict | None = None
    ):
    """
    メンバーシートからベスト記録シートにデータを転記する
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # メンバーシートを開く
    member_sheets = client.open_by_key(spreadsheet_id_member)
    member_list= load_member_list()
    df_best = pd.DataFrame()
    for member in member_list:
        try:
            member_sheet = member_sheets.worksheet(member)
            print(member)
            time.sleep(2)  # API制限を避けるために少し待機
        except gspread.exceptions.WorksheetNotFound:
            print(f"Member sheet '{member}' not found in spreadsheet '{spreadsheet_id_member}'.")
            continue
        data = member_sheet.get_all_values()
        df_member = pd.DataFrame(data[1:], columns=data[0])
        df_member['member_name'] = member  # メンバー名を追加
        
        # Check if 'event' column exists, if not, add processing to handle it
        if 'event' not in df_member.columns:
            # Try to create event column from other columns if available
            if 'type' in df_member.columns and '種目' in df_member.columns:
                df_member = get_event_type(df_member)
                df_member = get_event_name(df_member)
            elif '種目' in df_member.columns:
                # Create a simple event column using the '種目' column
                df_member['event'] = df_member['種目']
            else:
                # Skip this member if no event information is available
                print(f"Skipping member {member}: No event information found")
                continue
                
        event_list = df_member['event'].unique()
        for event in event_list:
            df_event = df_member[df_member['event'] == event]
            #SB（シーズンベスト）を抽出
            if 'SB' in df_event.columns:
                df_event = df_event[df_event['SB'] != ""]
                if not df_event.empty:
                    df_best = pd.concat([df_best, df_event], ignore_index=True)
    print(df_best['member_name'].unique())
    for season in df_best['season'].unique():
        df_season = df_best[df_best['season'] == season]
        df_season_records = pd.DataFrame(columns=df_season.columns)
        for name in df_season['member_name'].unique():
            #print(name)
            df_name = df_best[df_best['member_name'] == name]
            #print(df_name[])
            if not df_name.empty:
                df_season_records = pd.concat([df_season_records, df_name], ignore_index=True)
        df_season_records = df_season_records[(df_season_records['season']==season) | (df_season_records['PB'] != "")]
        sheet_name= f"{season}_member_best"
        #df_season_recordsを加工する
        # 特定のカラムだけを選択して書き出す
        selected_columns = ['member_name','年','season', 'event', '記録(公認)', '風(公認)', 'PB', 'SB']
        df_season_records = df_season_records[selected_columns]

        # Create a pivot table style dataframe with one row per member
        pivot_records = pd.DataFrame(columns=['member_name'])
        pivot_records['member_name'] = df_season_records['member_name'].unique()

        # For each unique member and event, extract PB and SB records with their year and wind info
        for member in df_season_records['member_name'].unique():
            member_data = df_season_records[df_season_records['member_name'] == member]
            print(f"Processing member: {member} for season: {season}")
            print(member_data['season'].unique())
            for event in member_data['event'].unique():
                event_data = member_data[member_data['event'] == event]
                
                # Get rows with PB and SB
                pb_row = event_data[event_data['PB'] == 'PB']
                sb_row = event_data[(event_data['SB'] == 'SB') & (event_data['season'] == season)]
                
                # Add SB record only if it matches the current season in the loop
                if not sb_row.empty:
                    if str(sb_row.iloc[0]['season']) == str(season):
                        record_sb = sb_row.iloc[0]['記録(公認)']
                        wind_sb = f" ({sb_row.iloc[0]['風(公認)']})" if '風(公認)' in sb_row.columns and not pd.isna(sb_row.iloc[0]['風(公認)']) and sb_row.iloc[0]['風(公認)'] != "" else ""
                        year_sb = f" [{sb_row.iloc[0]['年']}]" if '年' in sb_row.columns and not pd.isna(sb_row.iloc[0]['年']) else ""
                        
                        # Combine record, wind, and year into a single formatted column
                        pivot_records.loc[pivot_records['member_name'] == member, f"{event}SB(風)年月"] = f"{record_sb}{wind_sb}{year_sb}"
                
                # Add PB record with combined format for wind and year
                if not pb_row.empty:
                    record_pb = pb_row.iloc[0]['記録(公認)']
                    wind_pb = f" ({pb_row.iloc[0]['風(公認)']})" if '風(公認)' in pb_row.columns and not pd.isna(pb_row.iloc[0]['風(公認)']) and pb_row.iloc[0]['風(公認)'] != "" else ""
                    year_pb = f" [{pb_row.iloc[0]['年']}]" if '年' in pb_row.columns and not pd.isna(pb_row.iloc[0]['年']) else ""
                    
                    # Combine record, wind, and year into a single formatted column
                    pivot_records.loc[pivot_records['member_name'] == member, f"{event}PB(風)年月"] = f"{record_pb}{wind_pb}{year_pb}"

        # Use pivot_records instead of merging with original data
        df_season_records = pivot_records


        overwrite_sheet(
            spreadsheet_id=spreadsheet_id_best,
            sheet_name=sheet_name,
            data=df_season_records,
            cred_dict=creds_dict
        )


        # write_to_new_sheet(
        #     spreadsheet_id=spreadsheet_id_best,
        #     sheet_name=sheet_name,
        #     data=df_season_records,
        #     cred_dict=creds_dict
        # )

def member_sb_to_sheet(
    spreadsheet_id_member: str,
    spreadsheet_id_sb: str,
    creds_dict: dict | None = None,
    season: int = 2025
    ):
    """
    メンバーシートから指定年のSB（シーズンベスト）記録を抽出してSBシートに転記する
    さらに各種目毎のワークシートを作成してSBランキングを作成する
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # メンバーシートを開く
    member_sheets = client.open_by_key(spreadsheet_id_member)
    #member_list_active = load_member_list()
    df_sb = pd.DataFrame()
    df_sb_pre = load_sheet(
        spreadsheet_id=spreadsheet_id_sb,
        sheet_name="member_sb_all",
        creds_dict=creds_dict
    )
    
    # Handle case where load_sheet returns None
    if df_sb_pre is None:
        df_sb_pre = pd.DataFrame()

    member_list = load_sheet(
        spreadsheet_id=spreadsheet_id_member,
        sheet_name="部員一覧",
        creds_dict=creds_dict
    )[['member_name', 'Active']]
    member_list_active = member_list[member_list['Active'] == 'Active']['member_name'].tolist()
    print(member_list_active)

    event_list_active = []
    for member in member_list_active:
        try:
            member_sheet = member_sheets.worksheet(member)
            print(f"Processing member: {member}")
            time.sleep(2)  # API制限を避けるために少し待機
        except gspread.exceptions.WorksheetNotFound:
            print(f"Member sheet '{member}' not found in spreadsheet '{spreadsheet_id_member}'.")
            continue
            
        data = member_sheet.get_all_values()
        df_member = pd.DataFrame(data[1:], columns=data[0])
        df_member['member_name'] = member  # メンバー名を追加
        
        # Check if 'event' column exists, if not, add processing to handle it
        if 'event' not in df_member.columns:
            # Try to create event column from other columns if available
            if 'type' in df_member.columns and '種目' in df_member.columns:
                df_member = get_event_type(df_member)
                df_member = get_event_name(df_member)
            elif '種目' in df_member.columns:
                # Create a simple event column using the '種目' column
                df_member['event'] = df_member['種目']
            else:
                # Skip this member if no event information is available
                print(f"Skipping member {member}: No event information found")
                continue
        
        # 指定年のデータのみをフィルタリング
        if 'season' in df_member.columns:
            df_member = df_member[df_member['season'].astype(str) == str(season)]
        
        if df_member.empty:
            print(f"No data found for year {season} for member {member}")
            continue
        
        event_list = df_member['event'].unique()
        for event in event_list:
            df_event = df_member[df_member['event'] == event]
            # SB（シーズンベスト）を抽出
            if 'SB' in df_event.columns:
                df_event = df_event[df_event['SB'] != ""]
                if not df_event.empty:
                    df_sb = pd.concat([df_sb, df_event], ignore_index=True)
        event_list_active.extend(event_list)
    # event_list_activeの重複を削除
    event_list_active = list(set(event_list_active))
    if df_sb.empty:
        print(f"No SB records found for year {season}")
        return
    
    print(f"Found SB records for members: {df_sb['member_name'].unique()}")
    
    # 各種目毎のランキングシートを作成
    # 性別を'種別'カラムから取得
    if '種別' in df_sb.columns:
        df_sb = add_gender_column(df_sb)
    else:
        df_sb['gender'] = '不明'  # 種別カラムがない場合のフォールバック
    # member_list_activeに含まれるmemberをdf_sb_preから削除
    if not df_sb_pre.empty and 'member_name' in df_sb_pre.columns:
        df_sb_pre = df_sb_pre[~df_sb_pre['member_name'].isin(member_list_active)]

    # 削除したdf_sb_preとdf_sbを結合させて最新のdf_sbにする
    df_sb = pd.concat([df_sb, df_sb_pre], ignore_index=True)

    # Create a pivot table style dataframe with one row per member and gender as the second column
    pivot_records = pd.DataFrame({
        'member_name': df_sb['member_name'].unique()
    })
    # Add gender column aligned with member_name
    pivot_records['gender'] = pivot_records['member_name'].map(
        df_sb.drop_duplicates('member_name').set_index('member_name')['gender']
    ).fillna('不明')

    # For each unique member and event, extract SB records with their wind info
    for member in df_sb['member_name'].unique():
        member_data = df_sb[df_sb['member_name'] == member]
        print(f"Processing member: {member} for year: {season}")
        
        for event in member_data['event'].unique():
            event_data = member_data[member_data['event'] == event]
            
            # Get rows with SB
            sb_row = event_data[event_data['SB'] == 'SB']
            
            # Add SB record for the specified year
            if not sb_row.empty:
                record_sb = sb_row.iloc[0]['記録(公認)']
                wind_sb = f" ({sb_row.iloc[0]['風(公認)']})" if '風(公認)' in sb_row.columns and not pd.isna(sb_row.iloc[0]['風(公認)']) and sb_row.iloc[0]['風(公認)'] != "" else ""
                
                # Combine record and wind into a single formatted column (only add wind if it exists)
                if wind_sb:
                    pivot_records.loc[pivot_records['member_name'] == member, f"{event}(風)"] = f"{record_sb}{wind_sb}"
                else:
                    pivot_records.loc[pivot_records['member_name'] == member, f"{event}"] = record_sb

    # Use pivot_records as the final data
    df_year_records = pivot_records
    sheet_name = f"{season}_member_sb"

    overwrite_sheet(
        spreadsheet_id=spreadsheet_id_sb,
        sheet_name=sheet_name,
        data=df_year_records,
        cred_dict=creds_dict
    )
    df_sb['post_title'] = df_sb['member_name'].str.replace('　', '', regex=False)
    df_sb = reorder_by_event(df_sb)
    overwrite_sheet(
        spreadsheet_id=spreadsheet_id_sb,
        sheet_name="member_sb_all",
        data=df_sb,
        cred_dict=creds_dict
    )
    
    # 各種目毎のランキングシートを作成
    # 性別を'種別'カラムから取得
    if '種別' in df_sb.columns:
        df_sb=add_gender_column(df_sb)
        #df_sb['gender'] = df_sb['種別'].apply(extract_gender)
    else:
        df_sb['gender'] = '不明'  # 種別カラムがない場合のフォールバック
    # member_list_activeに含まれるmemberをdf_sb_preから削除
    if not df_sb_pre.empty and 'member_name' in df_sb_pre.columns:
        df_sb_pre = df_sb_pre[~df_sb_pre['member_name'].isin(member_list_active)]

    # # 削除したdf_pb_preとdf_pbを結合させて最新のdf_pbにする
    # df_sb = pd.concat([df_sb, df_sb_pre], ignore_index=True)

    # 各種目・性別毎にランキングシートを作成
    #events = df_sb['event'].unique()
    genders = df_sb['gender'].unique()
    event_list=[
            "100m", "200m", "300m", "400m", "800m", "1500m", "3000m", "5000m", "10000m",
            "5000mW", "10000mW","10kmW", "20kmW", "50kmW",
            "110mH", "100mH", "300mH", "400mH", "3000mSC",
            "4x100mR", "4x400mR", "4x200mR", "4x800mR",
            "走高跳", "走幅跳", "三段跳", "棒高跳",
            "砲丸投", "円盤投", "ハンマー投", "やり投",
            "十種競技", "七種競技",
            "ハーフマラソン", "フルマラソン"
        ]
    print(event_list_active)
    for event in event_list_active:
        for gender in genders:
            # 該当する種目・性別のデータを抽出
            event_gender_data = df_sb[(df_sb['event'] == event) & (df_sb['gender'] == gender)]
            
            if event_gender_data.empty:
                continue
            
            # ランキング用のデータを準備
            ranking_data = []
            for _, row in event_gender_data.iterrows():
                ranking_data.append({
                    '順位': '',  # 後で設定
                    '氏名': row['post_title'],
                    '性別': row['gender'],
                    '記録': row['記録(公認)'],
                    '記録_比較': row['記録(比較)'],
                    '風': row.get('風(公認)', ''),
                    '大会': row.get('大会', ''),
                    '日付': row.get('日付', '')
                })
            
            # データフレームに変換
            ranking_df = pd.DataFrame(ranking_data)
            
            if ranking_df.empty:
                continue
            
            # 記録でソート（跳躍・投擲は降順、それ以外は昇順）
            try:
                # 記録を比較用の数値に変換
                #ranking_df['記録_比較'] = ranking_df['記録'].apply(lambda x: extract_compare_record(x) if pd.notna(x) else float('inf'))
                
                # 種目のタイプを判定
                event_type = event_gender_data['type'].iloc[0] if 'type' in event_gender_data.columns else ''
                #print(event_type)
                
                # 記録_比較を数値に変換してソート
                ranking_df['記録_比較_numeric'] = pd.to_numeric(ranking_df['記録_比較'], errors='coerce')
                
                if any(event_type_check in event_type for event_type_check in ['Jump', 'Throw', 'Score']):
                    # 跳躍・投擲・複合競技は降順（大きい値が良い）
                    #print(f"Sorting {event_type}")
                    #print(ranking_df['記録_比較'])
                    ranking_df = ranking_df.sort_values('記録_比較_numeric', ascending=False)
                    #print(ranking_df['記録_比較'])

                else:
                    # トラック競技は昇順（小さい値が良い）
                    ranking_df = ranking_df.sort_values('記録_比較_numeric', ascending=True)
                
                # 一時的な数値カラムを削除
                ranking_df = ranking_df.drop('記録_比較_numeric', axis=1)
                
                # 順位を設定
                ranking_df['順位'] = range(1, len(ranking_df) + 1)
                
                # 比較用カラムを削除
                ranking_df = ranking_df.drop('記録_比較', axis=1)
                
            except Exception as e:
                print(f"Error sorting records for {event} {gender}: {e}")
                # ソートに失敗した場合はそのまま順位を設定
                ranking_df['順位'] = range(1, len(ranking_df) + 1)
            
            # シート名を作成（文字数制限を考慮）
            sheet_name_ranking = f"{season}_{gender}_{event}"[:100]
            
            # ランキングシートに書き込み
            try:
                overwrite_sheet(
                    spreadsheet_id=spreadsheet_id_sb,
                    sheet_name=sheet_name_ranking,
                    data=ranking_df,
                    cred_dict=creds_dict
                )
                print(f"Created ranking sheet: {sheet_name_ranking}")
                time.sleep(1)  # API制限を避けるため
            except Exception as e:
                print(f"Error creating ranking sheet {sheet_name_ranking}: {e}")

def member_pb_to_sheet(
    spreadsheet_id_member: str,
    spreadsheet_id_pb: str,
    creds_dict: dict | None = None
    ):
    """
    メンバーシートから各部員のPB（パーソナルベスト）記録を抽出してPBシートに転記する
    さらに各種目毎のワークシートを作成してPBランキングを作成する
    cred_dict: 認証情報の辞書形式
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    
    # メンバーシートを開く
    member_sheets = client.open_by_key(spreadsheet_id_member)
    # member_list_active = load_member_list()
    # member_list=member_list_active.copy()
    df_pb_pre = load_sheet(
        spreadsheet_id=spreadsheet_id_pb,
        sheet_name="member_pb_all",
        creds_dict=creds_dict
    )
    
    # Handle case where load_sheet returns None
    if df_pb_pre is None:
        df_pb_pre = pd.DataFrame()
    df_pb =pd.DataFrame()

    member_list = load_sheet(
        spreadsheet_id=spreadsheet_id_member,
        sheet_name="部員一覧",
        creds_dict=creds_dict
    )[['member_name', 'Active']]
    member_list_active = member_list[member_list['Active'] == 'Active']['member_name'].tolist()
    print(member_list_active)
    event_list_active = []
    for member in member_list_active:
        try:
            member_sheet = member_sheets.worksheet(member)
            print(f"Processing member: {member}")
            time.sleep(2)  # API制限を避けるために少し待機
        except gspread.exceptions.WorksheetNotFound:
            print(f"Member sheet '{member}' not found in spreadsheet '{spreadsheet_id_member}'.")
            continue
            
        data = member_sheet.get_all_values()
        df_member = pd.DataFrame(data[1:], columns=data[0])
        df_member['member_name'] = member  # メンバー名を追加
        
        # Check if 'event' column exists, if not, add processing to handle it
        if 'event' not in df_member.columns:
            # Try to create event column from other columns if available
            if 'type' in df_member.columns and '種目' in df_member.columns:
                df_member = get_event_type(df_member)
                df_member = get_event_name(df_member)
            elif '種目' in df_member.columns:
                # Create a simple event column using the '種目' column
                df_member['event'] = df_member['種目']
            else:
                # Skip this member if no event information is available
                print(f"Skipping member {member}: No event information found")
                continue
        
        event_list = df_member['event'].unique()
        event_list_active.extend(event_list)
        last_season = df_member['season'].max()

        # 同じeventにPBとPB_highがある場合、PB_highを削除する
        for event in event_list:
            event_mask = df_member['event'] == event
            event_data = df_member[event_mask]
            
            # PBとPB_highの両方が存在するかチェック
            has_pb = (event_data['PB'] == 'PB').any()
            has_pb_high = (event_data['PB'] == 'PB_high').any()
            
            if has_pb and has_pb_high:
            # PB_highを削除（空文字にする）
                pb_high_indices = event_data[event_data['PB'] == 'PB_high'].index
                df_member.loc[pb_high_indices, 'PB'] = ''
        for event in event_list:
            df_event = df_member[df_member['event'] == event]
            # PB（パーソナルベスト）を抽出
            if 'PB' in df_event.columns:
                df_event = df_event[df_event['PB'] != ""]
                if not df_event.empty:
                    df_event["last_season"]=last_season
                    df_pb = pd.concat([df_pb, df_event], ignore_index=True)
    # event_list_activeの重複を削除
    event_list_active = list(set(event_list_active))
    if df_pb.empty:
        print("No PB records found")
        return
    
    print(f"Found PB records for members: {df_pb['member_name'].unique()}")
    
    

    # 性別を'種別'カラムから取得
    if '種別' in df_pb.columns:
        df_pb = add_gender_column(df_pb)
    else:
        df_pb['gender'] = '不明'  # 種別カラムがない場合のフォールバック
    # 全角スペースを削除
    # member_list_activeに含まれるmemberをdf_pb_preから削除
    if not df_pb_pre.empty and 'member_name' in df_pb_pre.columns:
        df_pb_pre = df_pb_pre[~df_pb_pre['member_name'].isin(member_list_active)]

    # 削除したdf_pb_preとdf_pbを結合させて最新のdf_pbにする
    df_pb = pd.concat([df_pb, df_pb_pre], ignore_index=True)
    

    # Create a pivot table style dataframe with one row per member and gender as the second column
    pivot_records = pd.DataFrame({
        'member_name': df_pb['member_name'].unique()
    })
    # Add last_season by mapping the max last_season for each member
    pivot_records['last_season'] = pivot_records['member_name'].map(
        df_pb.groupby('member_name')['last_season'].max()
    )
    # Add gender column aligned with member_name
    pivot_records['gender'] = pivot_records['member_name'].map(
        df_pb.drop_duplicates('member_name').set_index('member_name')['gender']
    ).fillna('不明')
    event_list_all=[
            "100m", "200m", "300m", "400m", "800m", "1500m", "3000m", "5000m", "10000m",
            "5000mW", "10000mW","10kmW", "20kmW", "50kmW",
            "110mH", "100mH", "300mH", "400mH", "3000mSC",
            "4x100mR", "4x400mR", "4x200mR", "4x800mR",
            "走高跳", "走幅跳", "三段跳", "棒高跳",
            "砲丸投", "円盤投", "ハンマー投", "やり投",
            "十種競技", "七種競技",
            "ハーフマラソン", "フルマラソン"
        ]

    # For each unique member and event, extract PB records with their wind and year info
    for member in df_pb['member_name'].unique():
        member_data = df_pb[df_pb['member_name'] == member]
        print(f"Processing member: {member} for PB records")
        
        for event in event_list_all:
            event_data = member_data[member_data['event'] == event]
            
            # Get rows with PB
            pb_row = event_data[(event_data['PB'] == 'PB') | (event_data['PB'] == 'PB_high')]

            # Add PB record with combined format for wind and year
            if not pb_row.empty:
                record_pb = pb_row.iloc[0]['記録(公認)']
                wind_pb = f" ({pb_row.iloc[0]['風(公認)']})" if '風(公認)' in pb_row.columns and not pd.isna(pb_row.iloc[0]['風(公認)']) and pb_row.iloc[0]['風(公認)'] != "" else ""
                year_pb = f" [{pb_row.iloc[0]['年']}]" if '年' in pb_row.columns and not pd.isna(pb_row.iloc[0]['年']) else ""
                
                # Combine record, wind, and year into a single formatted column
                if wind_pb:
                    pivot_records.loc[pivot_records['member_name'] == member, f"{event}PB(風)年月"] = f"{record_pb}{wind_pb}{year_pb}"
                else:
                    pivot_records.loc[pivot_records['member_name'] == member, f"{event}PB年月"] = f"{record_pb}{year_pb}"

    # Use pivot_records as the final data
    df_pb_records = pivot_records
    # Insert the Active column as the 3rd column (index 2)
    active_column = pd.Series("Non-Active", index=df_pb_records.index, name="Active")
    # Sort by last_season in descending order
    df_pb_records = df_pb_records.sort_values('last_season', ascending=False)
    df_pb_records.insert(2, "Active", active_column)
    
    
    sheet_name = "member_pb"

    overwrite_sheet(
        spreadsheet_id=spreadsheet_id_pb,
        sheet_name=sheet_name,
        data=df_pb_records,
        cred_dict=creds_dict
    )
    overwrite_sheet(
        spreadsheet_id=spreadsheet_id_member,
        sheet_name="部員一覧",
        data=df_pb_records,
        cred_dict=creds_dict
    )
    df_pb_all= df_pb.copy()
    df_pb_all['post_title'] = df_pb_all['member_name'].str.replace('　', '', regex=False)
    #df_pb_all = reorder_by_event(df_pb_all)
    overwrite_sheet(
        spreadsheet_id=spreadsheet_id_pb,
        sheet_name="member_pb_all",
        data=df_pb_all,
        cred_dict=creds_dict
    )
    #df_pb['member_name'] = df_pb['member_name'].str.replace('　', '', regex=False)
    # 各種目毎のランキングシートを作成
    events = df_pb['event'].unique()
    genders = df_pb['gender'].unique()
    
    
    for event in event_list_active:
        for gender in genders:
            # 該当する種目・性別のデータを抽出
            event_gender_data = df_pb[(df_pb['event'] == event) & (df_pb['gender'] == gender)]
            
            if event_gender_data.empty:
                continue
            
            # ランキング用のデータを準備
            ranking_data = []
            for _, row in event_gender_data.iterrows():
                ranking_data.append({
                    '順位': '',  # 後で設定
                    '氏名': row['member_name'],
                    '性別': row['gender'],
                    '記録': row['記録(公認)'],
                    '記録_比較': row['記録(比較)'],
                    '風': row.get('風(公認)', ''),
                    '大会': row.get('大会', ''),
                    '日付': row.get('日付', '')
                })
            
            # データフレームに変換
            ranking_df = pd.DataFrame(ranking_data)
            
            if ranking_df.empty:
                continue
            
            # 記録でソート（跳躍・投擲は降順、それ以外は昇順）
            try:
                # 種目のタイプを判定
                event_type = event_gender_data['type'].iloc[0] if 'type' in event_gender_data.columns else ''
                
                # 記録_比較を数値に変換してソート
                ranking_df['記録_比較_numeric'] = pd.to_numeric(ranking_df['記録_比較'], errors='coerce')
                
                if any(event_type_check in event_type for event_type_check in ['Jump', 'Throw', 'Score']):
                    # 跳躍・投擲・複合競技は降順（大きい値が良い）
                    ranking_df = ranking_df.sort_values('記録_比較_numeric', ascending=False)
                else:
                    # トラック競技は昇順（小さい値が良い）
                    ranking_df = ranking_df.sort_values('記録_比較_numeric', ascending=True)
                
                # 一時的な数値カラムを削除
                ranking_df = ranking_df.drop('記録_比較_numeric', axis=1)
                
                # 順位を設定
                ranking_df['順位'] = range(1, len(ranking_df) + 1)
                
                # 比較用カラムを削除
                ranking_df = ranking_df.drop('記録_比較', axis=1)
                
            except Exception as e:
                print(f"Error sorting records for {event} {gender}: {e}")
                # ソートに失敗した場合はそのまま順位を設定
                ranking_df['順位'] = range(1, len(ranking_df) + 1)
            
            # シート名を作成（文字数制限を考慮）
            sheet_name_ranking = f"PB_{gender}_{event}"[:100]
            
            # ランキングシートに書き込み
            try:
                overwrite_sheet(
                    spreadsheet_id=spreadsheet_id_pb,
                    sheet_name=sheet_name_ranking,
                    data=ranking_df,
                    cred_dict=creds_dict
                )
                print(f"Created PB ranking sheet: {sheet_name_ranking}")
                time.sleep(1)  # API制限を避けるため
            except Exception as e:
                print(f"Error creating PB ranking sheet {sheet_name_ranking}: {e}")

def overwrite_sheet(
    spreadsheet_id: str,
    sheet_name: str,
    data: pd.DataFrame | list[list],
    cred_dict: dict,
    num_rows: int = 100,
    num_cols: int = 50,
    ):
    """
    シートを丸ごとクリアして data を上書きします。
    • data: pandas.DataFrame または list[list]（1行目がヘッダー）
    """
    # DataFrame以外は list[list] とみなす
    if isinstance(data, pd.DataFrame):
        df = data.reset_index(drop=True)
        df = df.where(pd.notnull(df), "")
        payload = [df.columns.tolist()] + df.values.tolist()
    else:
        payload = data

    # 認証
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(cred_dict, scope)
    client = gspread.authorize(creds)

    # シート取得 or 作成
    sh = client.open_by_key(spreadsheet_id)
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        ws = sh.add_worksheet(title=str(sheet_name), rows=str(num_rows), cols=str(num_cols))

    # 上書き（クリア→更新）
    ws.clear()
    ws.update("A1", payload)

#--------------
def sort_dataframe_by_date(df: pd.DataFrame) -> pd.DataFrame:
    """
    '日付'列から年・月・日を抽出して昇順ソートしたDataFrameを返す
    YYYY年MM月DD日形式とYYYY/MM/DD形式の両方に対応
    """
    df = df.copy()
    
    # Extract year, month, day components
    # Handle both formats: "YYYY年MM月DD日" and "YYYY/MM/DD"
    def extract_year(date_str):
        if not isinstance(date_str, str):
            return None
        # Try Japanese format first
        jp_match = re.search(r'(\d{4})年', date_str)
        if jp_match:
            return int(jp_match.group(1))
        # Try slash format
        slash_match = re.search(r'(\d{4})/\d{1,2}/\d{1,2}', date_str)
        if slash_match:
            return int(slash_match.group(1))
        return None
    
    def extract_month(date_str):
        if not isinstance(date_str, str):
            return None
        # Try Japanese format first
        jp_match = re.search(r'(\d{1,2})月', date_str)
        if jp_match:
            return int(jp_match.group(1))
        # Try slash format
        slash_match = re.search(r'\d{4}/(\d{1,2})/\d{1,2}', date_str)
        if slash_match:
            return int(slash_match.group(1))
        return None
    
    def extract_day(date_str):
        if not isinstance(date_str, str):
            return None
        # Try Japanese format first
        jp_match = re.search(r'(\d{1,2})日', date_str)
        if jp_match:
            return int(jp_match.group(1))
        # Try slash format
        slash_match = re.search(r'\d{4}/\d{1,2}/(\d{1,2})', date_str)
        if slash_match:
            return int(slash_match.group(1))
        return None
    
    # Apply the extraction functions
    df['年'] = df['日付'].apply(extract_year)
    df['月'] = df['日付'].apply(extract_month)
    df['日'] = df['日付'].apply(extract_day)
    
    # Convert to numeric and handle NaN values
    df['年'] = pd.to_numeric(df['年'], errors='coerce').fillna(0).astype(int)
    df['月'] = pd.to_numeric(df['月'], errors='coerce').fillna(0).astype(int)
    df['日'] = pd.to_numeric(df['日'], errors='coerce').fillna(0).astype(int)
    # Sort the DataFrame by date components
    df_sorted = df.sort_values(by=['年', '月', '日'], ascending=True)
    return df_sorted

def affiliation_contains_univ(univ_val: str, target_univ: str) -> bool:
    """
    所属（univ_val）に target_univ が含まれるか判定する。
    • 基本は部分一致だが、「大阪大」の場合は
      “大阪大”を含むが“東大阪大”“大阪体育大”等を除外。
    """
    # 空白を統一
    text = univ_val
    if not text or not target_univ:
        return False

    if target_univ == '大阪大':
        # “大阪大”を含み、以下の大学は除外
        excludes = ['東大阪大', '大阪体育大', '大阪大谷', '大阪大阪桐蔭']
        if '大阪大' in text and not any(exc in text for exc in excludes):
            return True
        return False

    # それ以外は単純部分一致
    return target_univ in text

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

def remove_duplicates_from_df_excluding_pb_sb_ub(df: pd.DataFrame) -> pd.DataFrame:
    """
    PB, SBカラムを除いた要素で重複行を削除する
    """
    # PB, SBカラムを除いたカラムリストを作成
    columns_to_check = [col for col in df.columns if col not in ['PB', 'SB' ,'UB']]
    
    # 指定したカラムのみで重複を削除
    return df.drop_duplicates(subset=columns_to_check)
def remove_duplicates_from_df(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates()

def clear_dataframe_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    入力されたDataFrameの書式をクリアして返す関数
    セル内の値を文字列として統一し、NaN値を空文字に変換する
    """
    df_cleared = df.copy()
    
    # NaN値を空文字に変換
    df_cleared = df_cleared.fillna("")
    
    # 全ての値を文字列に変換（数値や日付などの書式をクリア）
    for col in df_cleared.columns:
        df_cleared[col] = df_cleared[col].astype(str)
    
    # "nan"文字列を空文字に変換（fillna後に文字列変換した場合の対応）
    df_cleared = df_cleared.replace("nan", "")
    
    return df_cleared


def reorder_by_event(df: pd.DataFrame) -> pd.DataFrame:
    """
    'event'列の値に基づいてDataFrameを並べ替える
    """
    order_list=[
        "100m", "200m", "300m", "400m", "800m", "1500m", "3000m", "5000m", "10000m",
        "5000mW", "10000mW", "20kW", "50kmW",
        "110mH", "100mH", "300mH", "400mH", "3000mSC",
        "4x100mR", "4x400mR", "4x200mR", "4x800mR",
        "走高跳", "走幅跳", "三段跳", "棒高跳",
        "砲丸投", "円盤投", "ハンマー投", "やり投",
        "十種競技", "七種競技",
        "ハーフマラソン", "フルマラソン"
    ]
    if 'event' in df.columns:
        # order_listに基づいてDataFrameを並べ替え
        # order_listにない種目は最後に配置
        def get_order_index(event):
            try:
                return order_list.index(event)
            except ValueError:
                return len(order_list)  # order_listにない場合は最後に配置
        
        return df.sort_values(by='event', key=lambda x: x.map(get_order_index))
    else:
        return df

def reorder_columns_by_priority(df: pd.DataFrame) -> pd.DataFrame:
        """
        優先カラムリストに従ってDataFrameのカラム順を並べ替える
        """
        priority_columns = ['日付','氏名','学年','チーム／メンバー','チーム／メンバー_2','チーム／メンバー_3', '所属', 'event','記録(公認)','風(公認)','PB','UB','SB', '大会', 'ラウンド', 'レーン','組',  'コメント']
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
            # 事前にint型からstr型に変換
            #print()
            #print(event_name_1)
            if isinstance(event_name_2, int):
                event_name_2 = str(event_name_2)
            if isinstance(event_name_1, int):
                event_name_1 = str(event_name_1)
            # event_name_2優先、なければevent_name_1
            event_name = event_name_2 if event_name_2 else event_name_1
            #print(event_name)
            # 全角→半角変換（数字・英字・記号）
            event_name = event_name.translate(str.maketrans(
                '０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ×',
                '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzx'
            ))
            event_track_list = [
                "100m", "200m", "300m", "400m", "800m", "1500m", "3000m", "5000m", "10000m",
            ]
            event_wark_list=[
                "5000mW", "10000mW", "10kmW","20kmW", "50kmW"
            ]
            event_hardle_list = [
            "110mH","100mH", "300mH", "400mH", "3000mSC"
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
            "ハーフマラソン","フルマラソン"
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
        # 例: (1), （１）, (M1), （Ｍ１）, (D3), （Ｄ３）, 嘉藤　和真(4):617 など
        # ただし、(01)や(02)など2桁数字は学年ではなく生まれ年とみなして除外
        # (M1), (D3), (1) などのみ学年として抽出
        def extract_grade(name):
            # 全角→半角変換
            name = z2h(name)
            # 学年パターン: (M1), (D3), (1) などに加えて、コロンの前の括弧内数字も対応
            # 例: 嘉藤　和真(4):617 -> 4
            m = re.search(r'[（(]([MD]?\d)[）)]:?\d*', name, flags=re.IGNORECASE)
            if m:
                return m.group(1)
            return ""
        # Create the column if it doesn't exist
        if '学年' not in df.columns:
            df['学年'] = ""
        
        # Only apply extract_grade to rows where 学年 is empty
        mask = (df['学年'] == "") | (df['学年'].isna())
        df.loc[mask, '学年'] = df.loc[mask, '氏名'].apply(extract_grade)
        return df
    else:
        return df

def get_univ_name(df: pd.DataFrame, univ_name: str) -> pd.DataFrame:
    """
    '所属'列から大学名を抽出してDataFrameを返す
    """
    if '所属' in df.columns:
        # 所属から大学、高校、中学を判定する関数
        def extract_univ_name(affiliation):
            if not isinstance(affiliation, str):
                return ""
            
            # 大学名が含まれているか確認
            if affiliation_contains_univ(affiliation, univ_name):
                return univ_name
            else:
                return "その他"
        
        df['大学名'] = df['所属'].apply(extract_univ_name)
        return df
    else:
        return df

def extract_wind(record):
    # 公認:記録(風) の形式に対応
    m = re.search(r'公認:\d+(?:m\d+)?(?:\.\d+)?\(([+-]?\d+(?:\.\d+)?)\)', record)
    if m:
        return m.group(1)
    
    # +または-の直後の数値（例: +2.0, -1.5）を抽出
    m = re.search(r'([+-]\d+(?:\.\d+)?)', record)
    return m.group(1) if m else None

def remove_wind_from_record(record):
    # 例: '10.33+0.2' -> '10.33', '6m70+0.2' -> '6m70'
    # 公認:4.69(1.0) -> '4.69'
    
    # 公認:記録(風) の形式に対応
    m = re.match(r'^公認:(\d+(?:m\d+)?(?:\.\d+)?)\([+-]?\d+\.\d+\)', record)
    if m:
        return m.group(1)
    
    # +風や-風が直接記録に含まれている場合
    m = re.match(r'^(\d+(?:m\d+)?(?:\.\d+)?)[+-]\d+\.\d+', record)
    if m:
        return m.group(1)
    
    # 風の値が含まれていない場合はそのまま
    return record

def extract_record(record):
    # 例: '1:00.37[ 1:00.370]' → '1:00.37'
    # まず 1:10:30 のような時間形式を優先
    m = re.search(r'(\d+:\d+:\d+)', record)
    if m:
        return m.group(1)
    
    # 次に 1:00.37 のような形式を優先
    m = re.search(r'(\d+:\d+\.\d+)', record)
    if m:
        return m.group(1)
    # 次に 52:10 のような分:秒形式を追加
    m = re.search(r'(\d+:\d+)', record)
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
        
        df['type'] = df.apply(lambda row: determine_event_type(row['種目'], row['競技']) if '競技' in df.columns else determine_event_type(row['種目'], row['種目']), axis=1)
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

def get_official_record(df: pd.DataFrame) -> pd.DataFrame:
    """
    記録から公認記録を抽出し、それに対応する風速の値も"風(公認)"列に追加する
    """

    if '記録' in df.columns:
        # 風(公認)列を追加
        df['風(公認)'] = ""
        
        def extract_official_record(record, wind):
            # If wind is not a string or empty, return the original record
            if not isinstance(wind, str) or not wind:
                return record
            
            try:
                # Convert wind value to float for comparison
                wind_value = float(wind)
                
                # If wind is <= +2.0, the record is official
                if wind_value <= 2.0:
                    return record
                else:
                    # For wind > +2.0, mark as wind-aided (not official)
                    return ""
            except ValueError:
                # If wind can't be converted to float, return the original record
                return record

        # Apply the function row by row
        df['記録(公認)'] = df.apply(
            lambda row: extract_official_record(row['記録'], row['風']), 
            axis=1
        )
        
        # 公認記録がある場合、風(公認)にも風の値をセット
        mask = df['記録(公認)'] != ""
        df.loc[mask, '風(公認)'] = df.loc[mask, '風']
        
        # For long jump and triple jump, check for valid records in attempt columns when official record is empty
        if '記録(公認)' in df.columns and 'event' in df.columns:
            mask = (df['記録(公認)'] == "") & ((df['event'] == "走幅跳") | (df['event'] == "三段跳"))
            
            for idx in df[mask].index:
                best_record = None
                best_record_value = 0
                best_wind = None
                
                # Check all attempt columns
                for attempt_col in ['1回','2回', '3回', '4回', '5回', '6回','備考']:
                    if attempt_col in df.columns and pd.notna(df.at[idx, attempt_col]) and df.at[idx, attempt_col] != "":
                        attempt = df.at[idx, attempt_col]
                        # Extract wind value from the attempt
                        wind_value = extract_wind(attempt)
                        
                        # Extract record from the attempt
                        record_value = extract_record(remove_wind_from_record(attempt))
                        
                        # If wind value is <= 2.0 or not present, consider it as official
                        if record_value and (wind_value is None or float(wind_value) <= 2.0):
                            # Convert to numeric for comparison
                            try:
                                # For jump events, extract meters and centimeters (e.g., "6m73" -> 6.73)
                                if 'm' in record_value:
                                    m_part = float(record_value.split('m')[0])
                                    cm_part = float(record_value.split('m')[1]) / 100
                                    numeric_value = m_part + cm_part
                                else:
                                    numeric_value = float(record_value)
                                
                                # Keep the best record
                                if numeric_value > best_record_value:
                                    best_record_value = numeric_value
                                    best_record = record_value
                                    best_wind = wind_value
                            except (ValueError, IndexError):
                                pass  # Skip invalid formats
                
                # Use the best valid record found
                if best_record:
                    df.at[idx, '記録(公認)'] = best_record
                    if best_wind:
                        df.at[idx, '風(公認)'] = best_wind
                
        return df
    else:
        return df

def get_compare_record(df: pd.DataFrame) -> pd.DataFrame:
    """
    '記録'列から比較用の数値部分を抽出してDataFrameを返す
    例:
      - "17:09.17" → 1709.17
      - "6m70" → 6.70
      - "10.33" → 10.33
      - "44.4" → 44.4
    """
    def extract_compare_record(record):
        if not isinstance(record, str):
            return None
        record = record.strip()
        # 時間形式 (例: 1:10:30)
        m = re.match(r'^(\d+):(\d+):(\d+)$', record)
        if m:
            hour, min_, sec = m.groups()
            # 時間・分・秒を2桁ずつに揃えて連結
            return float(f"{int(hour):01d}{int(min_):02d}{int(sec):02d}")
        # 分:秒形式 (例: 52:10)
        m = re.match(r'^(\d+):(\d+)$', record)
        if m:
            min_, sec = m.groups()
            # 分・秒を2桁ずつに揃えて連結
            return float(f"{int(min_):02d}{int(sec):02d}")
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
            return float(f"{int(m1)}.{int(m2):02d}")
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
        df['記録(比較)'] = df['記録(公認)'].apply(extract_compare_record)
        return df
    else:
        return df

def change_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameのカラム名を変更する
    """
    # カラム名の変更マッピング
    column_mapping = {
        '選手名（漢字）': '氏名',
        '風速': '風',
        '競技名': '種目',
        '性別': '種別',
        '競技種別': 'ラウンド',
        '学年': '学年',
        'コメント': 'ｺﾒﾝﾄ'
    }
    
    # カラム名を変更
    df = df.rename(columns=column_mapping)
    # DNS, DNF, DQ カラムが存在する場合、Trueの要素があればコメントにカラム名を追加
    #print(df.columns)
    # for col in ['DNS', 'DNF', 'DQ']:
    #     if col in df.columns:
    #         # コメントカラムがなければ作成
    #         if '' not in df.columns:
    #             df['ｺﾒﾝﾄ'] = ""
    #         # Trueの行にカラム名を追加
    #         #print(df)
    #         mask = df[col] == True
    #         df.loc[mask, 'ｺﾒﾝﾄ'] = df.loc[mask, 'ｺﾒﾝﾄ'].astype(str) + (df.loc[mask, 'ｺﾒﾝﾄ'].apply(lambda x: " " if x else "")) + col
    #         # カラムを削除
    df = df.drop(columns=['DNS', 'DNF', 'DQ'], errors='ignore')
    # "日付"列の "YYYY-MM-DD" を "YYYY年M月D日" に変換
    


    if '日付' in df.columns:
        def convert_date_format(date_str):
            # Handle pandas Timestamp objects
            if isinstance(date_str, pd.Timestamp):
                y = date_str.year
                m = date_str.month
                d = date_str.day
                return f"{y}年{m}月{d}日"
            # Only convert if format is YYYY-MM-DD or YYYY-M-D
            if isinstance(date_str, str) and re.match(r'^\d{4}-\d{1,2}-\d{1,2}$', date_str):
                try:
                    y, m, d = date_str.split('-')
                    return f"{int(y)}年{int(m)}月{int(d)}日"
                except Exception:
                    return date_str
            return date_str
        df['日付'] = df['日付'].apply(convert_date_format)
    
    # "年度"列が存在し、値が指定リストに含まれる場合は"学年"列を作成・更新
    grade_values = ['1', '2', '3', '4', '5', '6', '7', '8', 'M1', 'M2', 'M3', 'D1', 'D2', 'D3', '農地']
    if '年度' in df.columns:
        # "学年"列がなければ作成
        if '学年' not in df.columns:
            df['学年'] = ""
        # "年度"がgrade_valuesに含まれる場合のみ"学年"にセット
        df['学年'] = df.apply(
            lambda row: row['年度'] if str(row['年度']) in grade_values else row['学年'],
            axis=1
        )
    df["競技"]=df["種目"]
    return df

def return_record_status(df_all: pd.DataFrame,df_record: pd.Series,univ_name: str) -> pd.DataFrame:
    # df_allの0番目からdf_recordと一致する要素までの配列をdf_all_by_recordと定義
    # df_recordをDataFrame型に変換
    if isinstance(df_record, pd.Series):
        df_record = df_record.to_frame().T
    elif not isinstance(df_record, pd.DataFrame):
        # その他の型の場合、空のDataFrameを作成
        df_record = pd.DataFrame()
    df_record=process_df(df_record,univ_name)
    if df_all is not None and not df_all.empty and not df_record.empty:
        # df_recordの最初の行と一致する行をdf_allから探す
        match_found = False
        match_index = 0
        
        for i, row in df_all.iterrows():
            # 主要なカラムで一致を確認（例：氏名、日付、記録など）
            match_cols = ['日付','大会','event','ラウンド'] if all(col in df_all.columns and col in df_record.columns for col in ['日付','大会','event','ラウンド']) else df_all.columns.intersection(df_record.columns)
            print(match_cols)

            if len(match_cols) > 0 and not df_record.empty:
                # df_recordの最初の行と比較
                is_match = True
                for col in match_cols:
                    # print(row[col], df_record.iloc[0][col])
                    # print(row)
                    # if row[col]==None:
                    #print(df_all.iloc[i])
                    #print("-----how-----")
                    if str(row[col]) != str(df_record.iloc[0][col]):
                        #print(row[col], df_record.iloc[0][col])
                        is_match = False
                        break
                
                if is_match:
                    match_index = i
                    print("match")
                    match_found = True
                    break
        #print(match_cols)
        if match_found:
            # 最初のデータからマッチした要素までの配列を取得
            df_all_by_record = df_all.iloc[0:match_index+1].copy()
        else:
            # マッチしない場合は最初のデータからdf_recordまでのすべてのデータを返す
            df_all_by_record = df_all.copy()
    else:
        df_all_by_record = pd.DataFrame()
    #print(df_record)
    #print(df_all_by_record)
    df_all_by_record = process_df(df_all_by_record,univ_name)
    df_all_by_record = change_to_send_format(df_all_by_record)

    if not df_all_by_record.empty:
        df_record = df_all_by_record.iloc[-1]
    else:
        df_record = pd.Series()
    
    #df_record=change_to_send_format(df_record)


    return df_record

def change_to_send_format(df: pd.DataFrame) -> pd.DataFrame:
    # 送信フォーマットに変換する処理を実装
    df_send = df.copy()
    # 必要なカラムだけを残す
    # PB, UB, SB カラムに要素が入っていれば、備考カラムにそのカラム名を入れる
    if '備考' not in df_send.columns:
        df_send['備考'] = ""

    for col in ['PB', 'UB', 'SB']:
        if col in df_send.columns:
            # PBまたはUBに値がある行を特定
            has_pb_or_ub = ((df_send['PB'].notna()) & (df_send['PB'] != "")) | \
                          ((df_send['UB'].notna()) & (df_send['UB'] != ""))
            
            # SBの場合、PBまたはUBがある行は除外
            if col == 'SB':
                mask = (df_send[col].notna()) & (df_send[col] != "") & (~has_pb_or_ub)
            else:
                mask = (df_send[col].notna()) & (df_send[col] != "")
            
            # 既存の備考にカラム名を追加（既に備考がある場合はスペースで区切る）
            df_send.loc[mask, '備考'] = df_send.loc[mask, '備考'].astype(str).apply(
                lambda x: x + " " + col if x and x != "nan" else col
            )
    # 送信に必要なカラムを定義
    required_columns = ['種目','競技','ラウンド','ﾚｰﾝ','氏名', '学年','gender' ,'記録','風','順位','備考','ｺﾒﾝﾄ']
    
    # 存在するカラムのみを選択
    available_columns = [col for col in required_columns if col in df_send.columns]
    df_send = df_send[available_columns]
    return df_send

def process_df(df: pd.DataFrame, univ_name: str) -> pd.DataFrame:

    if '記録(公式)' in df.columns:
        # Only update records where 記録(公式) has a value (is not empty)
        mask = (df['記録(公式)'].notna()) & (df['記録(公式)'] != "")
        df.loc[mask, "記録"] = df.loc[mask, "記録(公式)"]

    
    
    df=get_grade_column(df)  # 学年列を抽出
    
    #df_3 = reorder_columns_by_priority(df_2)  # 優先カ
    df = get_true_record(df)  # 記録列から数値部分を抽出,風速を抽出
    
    df = get_event_type(df)  # 種目列から競技種目を抽出
    
    df = sort_dataframe_by_date(df)  # 日付でソート
    
    df = get_season(df)  # シーズンを抽出
    
    df = get_event_name(df)  # 種目名を抽出
    
    df = get_official_record(df)  # 公認記録を抽出
    df = get_compare_record(df)  # 比較用の記録を抽出
    df = get_univ_name(df,univ_name)  # 大学名を抽出
    #df_12 = get_grade_column(df_11)
    df=remove_duplicates_from_df_excluding_pb_sb_ub(df)  # 重複行を削除
    df = add_pb_column(df)  # PB列を追加
    df = add_sb_column(df)  # SB列を追加
    df = add_ub_column(df)  # UB列を追加
    df = add_gender_column(df)  # 性別列を追加
    df = reorder_columns_by_priority(df)  # 優先カ
    return df

def process_sheet(
    spreadsheet_id: str,
    sheet_name: str,
    univ_name: str = "大阪大",
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
    df_sorted = process_df(df,univ_name)  # DataFrameを処理してソート

    # NaNを空文字に変換
    df_sorted = df_sorted.where(pd.notnull(df_sorted), "")

    # 更新するデータをリスト形式に変換
    updated_data = [df_sorted.columns.tolist()] + df_sorted.values.tolist()
    
    # シートを更新
    worksheet.clear()  # 既存のデータをクリア
    worksheet.update('A1', updated_data)  # 新しいデータを書き込む


def add_gender_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    '種別'列から性別を抽出して新しい列を追加する
    """
    if '種別' in df.columns:
        # 性別を抽出する関数
        def extract_gender(category):
            if not isinstance(category, str):
                return ""
            if "男" in category:
                return "男子"
            elif "女" in category:
                return "女子"
            else:
                return ""
        
        df = df.copy()
        df['gender'] = df['種別'].apply(extract_gender)
        return df
    else:
        return df

def add_pb_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameからPB（Personal Best）を抽出して新しい列を追加する
    """
    df_pb = df
    event_list = df['event'].unique()
    df.loc[:,'PB'] = ""
    df_other = df[df['大学名']=='その他']
    for event in event_list:
        df_event = df_pb[df_pb['event'] == event]
        if not df_event.empty:
            # '記録(比較)' 列が存在するか確認
            if '記録(比較)' not in df_event.columns:
                print("'記録(比較)' column not found in the DataFrame.")
                continue
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
        # 'univ'が"その他"の行もPBを設定
        df_event_other = df_other[df_other['event'] == event]
        if not df_event_other.empty:
            if '記録(比較)' not in df_event_other.columns:
                print("'記録(比較)' column not found in the DataFrame.")
                continue
            # 'type'列の値に"Jump", "Throw", "Score"が含まれている行が1つでもあれば最大値を使用
            if df_event_other['type'].astype(str).str.contains('Jump|Throw|Score').any():
                # 跳躍・投擲・複合競技の場合は最大値を使用
                #print("Using max for PB calculation")
                if df_event_other['記録(比較)'].notna().any():
                    pb_idx = df_event_other['記録(比較)'].idxmax()
                else:
                    pb_idx = None
            else:
                if df_event_other['記録(比較)'].notna().any():
                    pb_idx = df_event_other['記録(比較)'].idxmin()
                else:
                    pb_idx = None

            if pb_idx is not None and not pd.isnull(pb_idx):
                if 'PB' not in df.columns:
                    df['PB'] = ""
                df.at[pb_idx, 'PB'] = "PB_high"
    return df

def add_ub_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameからUB（University Best）を抽出して新しい列を追加する
    """
    df = df.copy()
    df_ub = df
    event_list = df['event'].unique()
    df.loc[:, 'UB'] = ""
    for event in event_list:
        df_event = df_ub[df_ub['event'] == event]
        # Filter records where PB contains a value (not empty)
        df_event_with_pb = df_event[df_event['PB'].notna() & (df_event['PB'] != "")]
        # Check if there are one or fewer records with PB values
        df_event = df_event[df_event['大学名']!= 'その他']
        if len(df_event_with_pb) == 1 and df_event_with_pb['PB'].iloc[0] == "PB_high":
            if not df_event.empty:
            # '記録(比較)' 列が存在するか確認
                if '記録(比較)' not in df_event.columns:
                    print("'記録(比較)' column not found in the DataFrame.")
                    continue
                # 最小の記録(比較)を取得
                if df_event['type'].astype(str).str.contains('Jump|Throw|Score').any():
                    # 跳躍・投擲・複合競技の場合は最大値を使用
                    if df_event['記録(比較)'].notna().any():
                        ub_idx = df_event['記録(比較)'].idxmax()
                    else: 
                        ub_idx = None
                else:
                    if df_event['記録(比較)'].notna().any():
                        ub_idx = df_event['記録(比較)'].idxmin()
                    else:
                        ub_idx = None

                if ub_idx is not None and not pd.isnull(ub_idx):
                    if 'UB' not in df.columns:
                        df['UB'] = ""
                    # 安全な値の比較
                    try:
                        pb_value = float(df_event_with_pb['記録(比較)'].iloc[0])
                        ub_value = float(df.at[ub_idx, '記録(比較)'])
                        print(f"PB Value: {pb_value}, UB Value: {ub_value}")
                        
                        # 競技タイプによって比較条件を変える
                        if df.at[ub_idx, 'type'].lower().strip() in ['jump', 'throw', 'score']:
                            # 跳躍・投擲・得点競技は大きい値が良い記録
                            is_better = pb_value > ub_value
                        else:
                            # トラック競技は小さい値が良い記録
                            is_better = pb_value < ub_value
                            
                        if is_better:
                            print(f"Setting UB for index {ub_idx} with value {ub_value}")
                            df.at[ub_idx, 'UB'] = "UB"
                    except (ValueError, TypeError):
                        # 数値に変換できない場合は処理をスキップ
                        pass
    return df

def add_sb_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    DataFrameからSB（Season Best）を抽出して新しい列を追加する
    """
    if 'season' not in df.columns or 'event' not in df.columns:
        print("'season' or 'event' column not found in the DataFrame.")
        return df
    season_list = df['season'].unique()
    df.loc[:, 'SB'] = ""
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

def load_sheet(
    spreadsheet_id: str,
    sheet_name: str,
    creds_dict: dict | None = None,
    ):
    """
    指定されたスプレッドシートの指定シートを読み込む
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
        return None
    
    # シートの全データ取得（2次元リスト）
    data = worksheet.get_all_values()
    
    if not data or len(data) < 2:
        print("No data found in the sheet.")
        return None
    
    # ヘッダーを除いたデータ部分をDataFrameに変換
    df = pd.DataFrame(data[1:], columns=data[0])
    
    return df

if __name__ == "__main__":
    # サンプルデータ: '氏名'と'記録'列を含む
    df = pd.DataFrame([
        {'氏名': "那木　悠右 (1)Yusuke NAGI (03)", '記録': '6m34+2.0 (追風)','日付': '2024/05/01', '種目': '走幅跳'},
        {'氏名': "小林  恒方(M3)",'event':'三段跳', '記録': 'w4.73 (+2.0)','2回':'公認:4.69(1.0)','3回':'6m74+2.1','日付':'2024年4月39日'},
        {'氏名': "嘉藤　和真(4):617", '記録': '15.20[44.4]'},
        {'氏名': "", '記録': '10.94[10.933]'},
        {'氏名': "佐藤 花子", '記録': '1:00.37[ 1:00.370]', '風': '0.0', '1回': '公認:4.69(1.0)'},
    ])
    #df = get_wind_from_record(df)
    df = sort_dataframe_by_date(df)  # 日付でソート
    df = get_grade_column(df)
    df = get_true_record(df)
    df = get_official_record(df)
    df = get_compare_record(df)

    print(df["学年"])
    
    print(df)
