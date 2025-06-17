import os, json
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
from database.db_sheet import *
from datetime import date, datetime
from cli.real_time import *
from pathlib import Path
import time




def main():
    # Secrets から読み込んだ JSON をデコード
    # creds_json = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    creds_env = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    # 環境変数から取得した場合は文字列 → dict に変換
    creds_str = creds_env.replace('\\n', '\n')
    creds_dict = json.loads(creds_str)
        # 直接コードにベタ書きした dict を使う場合
    
    # creds_json = creds_json.replace('\\n', '\n')
    # creds_dict = json.loads(creds_json)
    # print(creds_json)

    # 認証スコープ
    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # スプレッドシートを開く
    #SPREADSHEET_ID_CONFERENCE = os.getenv('SPREADSHEET_ID')
    #SPREADSHEET_ID_CONFERENCE = os.getenv('SPREADSHEET_ID_CONFERENCE')
    SPREADSHEET_ID_CONFERENCE = '1yAI2wwNWBWdWfrbaiXA5EvjuKoHCztwjAnUYRkNNbPw'
    SPREADSHEET_ID_MEMBER = '1vN-qqu4RB-Ukp2tR5WDQJB9P-uRPgGp3L6MDz2XfPAE'

    worksheet_conference = client.open_by_key(SPREADSHEET_ID_CONFERENCE).sheet1
    worksheet_member = client.open_by_key(SPREADSHEET_ID_MEMBER).sheet1
    
    # シートの全データ取得（2次元リスト）
    data = worksheet_conference.get_all_values()

    write_to_new_sheet(
        spreadsheet_id=SPREADSHEET_ID_CONFERENCE,
        sheet_name='試合ステータス',
        data=data,
        cred_dict=creds_dict  # ここでは直接 creds_dict を使うので None
        )


    # 1行目（ヘッダー）に「ステータス」「担当者」を追加
    headers = data[0]
    if "試合ステータス" not in headers:
        headers += ["試合ステータス", "結果作成"]
        worksheet_conference.update('A1', [headers])  # 1行目だけ更新
    print(headers)
    # 日付文字列を date 型に変換してステータス更新
    idx_start = headers.index("日付(開始日)")     # 0-based
    idx_end   = headers.index("日付(終了日)")
    idx_status = headers.index("試合ステータス")
    idx_result = headers.index("結果作成")
    # today = date.today()
    # デバッグ用に固定値で「今日」を設定したい場合:
    # ───────────────────────────────────────────────
    # 本番ではコメントアウトして下行を有効にし、
    # デバッグ時のみ固定日付で動作させます。
    today = date(2025, 7, 5)  # YYYY, M, D の形式で固定日付に設定
    #today = date.today()     # ← 本番はこっちを使う

    for idx_row, row in enumerate(data[1:], start=2):
        # row: list of str
        try:
            start = datetime.strptime(row[idx_start], "%Y/%m/%d").date()
            end   = datetime.strptime(row[idx_end],   "%Y/%m/%d").date()
        except Exception:
            status = "ERROR"
        else:
            if start <= today <= end:
                status = "DOING"
            elif today < start:
                status = "TODO"
            else:
                status = "DONE"
            print(f"Row {idx_row}: {start} ~ {end} → {status}")
        #結果作成が空欄なら"TODO"にする
        if row[idx_result] == "":
            status_result = "TODO"
            worksheet_conference.update_cell(idx_row, idx_result+1, status_result)  # 結果作成も初期化
        worksheet_conference.update_cell(idx_row, idx_status+1, status)
    #---------------------------------------------------------------------------------------------
    # 全ステータス更新後、シートを「日付(開始日)」列で降順にソート
    # gspread.sort() には (カラム番号, 昇順=True/False) のタプルを渡します
    #worksheet.sort(idx_start + 1, 'desc')  # 0-based indexなので+1

    # シートの全データ取得（2次元リスト）
    values = worksheet_conference.get_all_values()
    if values:
        columns = values[0]
        records = values[1:]
        df_comp = pd.DataFrame(records, columns=columns)
    else:
        df_comp = pd.DataFrame()

    # 「日付(開始日)」を datetime に変換して降順ソート
    df_comp['日付(開始日)'] = pd.to_datetime(
        df_comp['日付(開始日)'], format='%Y/%m/%d', errors='coerce'
    )
    df_comp.sort_values('日付(開始日)', ascending=False, inplace=True)
    df_comp.reset_index(drop=True, inplace=True)

    # 日付(開始日)を 'YYYY/MM/DD' 形式の文字列に変換
    df_comp['日付(開始日)'] = df_comp['日付(開始日)'].dt.strftime('%Y/%m/%d')

    # --------------------------------------------
    # ソート済み DataFrame をシートにも反映（A2以降に書き戻し）
    values_to_write = df_comp.astype(str).values.tolist()
    #print(values_to_write[:10])  # 最初の10行を表示
    worksheet_conference.update('A2', values_to_write)
    # --------------------------------------------

    #print(df_comp[df_comp['試合ステータス']=="DOING"])  # ステータスの集計
    # 「DOING」か、または「DONE」かつ「TODO」の行を抽出
    df_todo = df_comp[
        (df_comp['試合ステータス'] == "DOING")
        | (
            (df_comp['試合ステータス'] == "DONE")
            & (df_comp['結果作成'] != "DONE" )
        )
    ]
    print(df_todo.head(10))  # 最初の10行を表示
    
    member_list= load_member_list()
    print(member_list)
    # for member in member_list:
    #     #p#rint(f"メンバー: {member['name']}, ID: {member['id']}, Discord: {member['discord']}")
    #     time.sleep(1)  # API制限対策のため1秒待機
    #     print(f"メンバー: {member}")
    #     deduplicate_sheet(
    #         spreadsheet_id=SPREADSHEET_ID_MEMBER,
    #         sheet_name=member,
    #         cred_dict=creds_dict
    #     )

    urls = load_com_urls()
    for url in urls:
        run_real_time_v2(
            url=url,
            univ='大阪大',
            spread_sheet_ID_conference=SPREADSHEET_ID_CONFERENCE,
            spread_sheet_ID_member=SPREADSHEET_ID_MEMBER,
            creds_dict=creds_dict,
            announce_discord=False
        )

    for index, row in df_todo.iterrows():
        #print(f"大会名: {row['大会名']}, 開始日: {row['日付(開始日)']}, 終了日: {row['日付(終了日)']}")
        url= row['競技url']
        finsih_comp=run_real_time_v2(
            url=url,
            univ='大阪大',
            spread_sheet_ID_conference=SPREADSHEET_ID_CONFERENCE,
            spread_sheet_ID_member=SPREADSHEET_ID_MEMBER,
            creds_dict=creds_dict,
            announce_discord=False
        )
        if finsih_comp:
            # ステータスを更新
            #worksheet.update_cell(index+2, idx_status+1, "DONE")
            worksheet_conference.update_cell(index+2, idx_result+1, "DONE")
            #print(f"大会名: {row['大会名']} の競技結果を取得しました。")
        else:
            # ステータスを更新
            worksheet_conference.update_cell(index+2, idx_result+1, "DOING")
            #print(f"大会名: {row['大会名']} の競技結果はまだ取得できませんでした。")



if __name__ == "__main__":
    main()