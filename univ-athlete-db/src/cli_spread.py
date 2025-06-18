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
    # creds_env = os.getenv('GOOGLE_SHEETS_CREDENTIALS')
    # # 環境変数から取得した場合は文字列 → dict に変換
    # creds_str = creds_env.replace('\\n', '\n')
    # creds_dict = json.loads(creds_str)
    #     # 直接コードにベタ書きした dict を使う場合
    creds_dict = {
    "type": "service_account",
    "project_id": "handai-tf-system-control",
    "private_key_id": "25d03592b23b146791d7ee8279e2a06063c6fcd0",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCqIxSvKeKap8Ud\ndWgNPMfHyMBV639EK5st38PdBTwXxOEsFybb/laqD2UcBKOC2UTFlhkQuwuUwrVy\n8DgfIIOAXAvkvpCjciP+MiIL2qNJSVKPB+F6JqQe8FPOflG4kmt9Q/RWIjP2g7n1\n0eAshh7+CIkHx0uuTL8WTc3hrNMB9HVB/YhTD4Y4f4qbta4Hw/I7viFNhQdSWKJp\nzfpkY9e9dJr+pvKsbXdo5Ni7P7yx/kC6isNm0vuygigLsfPrPyXPnG7su5DqkuYl\n1Q6WcHUdA0whXwTqGD4hXLwpxI4Ln1dGa3d9XENkVV2JN9Lms7bvI8RX4tMTh+GP\nZvGFetDVAgMBAAECggEABSrcmXddtRHMaFklCGXksXo08UceTe0/INUPh1p92UD3\nD9ZCLWNbsX2XNhMj/jjoIFIvP7VWpDWHuk52feeIZvEkwVVSYkx4sGNIanDBDdxG\nwCZeoE2lJXVqLjbi94am8h6KwMT4LBATKVavBtsp/NA4jT5t24TkNuK1EpojrIb5\n+q9cRk3OplmXeHp7Ee0zU70OCEVmEiP6o2b3qiKfIMGfNfrf6Zat1KAwXVegmJa2\n2XQ2UEphjDGnPsfmseNcAZ4MRDF+DbszT6wKxDm4fvd3Ph6F/qBDpj1WhG2rywDr\nmcaYnslihs9bxIVGnR0+QlLd1WIVpC7SjONVWUhKzwKBgQDoS7guSkp6CLV0jCjR\nE6CPSWzo0/RC8wdUYLc6rOvhWaELziRAsnOM7RorA9MtQPbfkr3xzkpvvPnPKNyk\n2eufLYF9ru0s5uXX0gWG7bN9sf2NUbKOQmsB3G2UahMnGwg9HuJ+70buJrGh+1JZ\nZK3g9f+O+hMUt61OHQPY6Wqr4wKBgQC7f5Vqy/2T+sVJTZx7q+NvLCSfQeLG4Az6\nAOiRqSfuwNghFeCH3HLBnENyCXqWOuh04Cfnt3Bz9qoNFBKH4GICGkkAACsWXnFP\njKzxBXffusQgevL97zcinGQofHg0wlPCzWr0Igys/h7eGhOg8PfVYsd1tD+hxdV3\nQQP1Ogsd5wKBgHRu552ELTpnvRPy4M6TKOpJIma9PnSEPgtEAvNNE1o7w6YYKEGp\ncJOVkIU5AJNxOYysj7pw7Qx+yzPTxmx2skxx0bL+h/D2twPrSEvuPwZkvbMk3PvD\nPMGNC/vVA06ZlRKVtW9sXcAm8ug/AXK/LQxSIUs3+3Jp8lrx3ijOLmKDAoGARc3v\nA86kPoZ7EppZatWIm+gUTlJKKn5Zdm4GJ8yROFsFW/P4Hryc4KXbmkYbJHkT+AdH\n9AWgURwBHVNevsVz15KPoPdvEyngB5y4+hZuFZZD1E/RzWZU4YbV5xjH6+R5KKov\namqOy4zkUw3kRuPPcNsQpSqREhpEKdzDq3WLk/sCgYBcQTtjHXxnaq0GM3YYrHb0\nTfgX9mz9reyC7qhFQ0U1CGMZGahtD88TjgM56h5MdSsqf7uQmRG3/PZ2vPjhYInC\nNwpxq9QRT19VyO6mZ0VJX8KJz21LAEQQDXCi/QKyvc1zXqj0PBl9PcuuR8zwNg2s\nHWK3Jw+gCnblu1SnopbAiw==\n-----END PRIVATE KEY-----\n",
    "client_email": "edit-tf-schedule@handai-tf-system-control.iam.gserviceaccount.com",
    "client_id": "115271653994163090816",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/edit-tf-schedule%40handai-tf-system-control.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
    }


    # 認証スコープ

    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # スプレッドシートを開く
    SPREADSHEET_ID_MEMBER = os.getenv('SPREADSHEET_ID_MEMBER')
    SPREADSHEET_ID_CONFERENCE = os.getenv('SPREADSHEET_ID_CONFERENCE')
    SPREADSHEET_ID_MEMBER="1vN-qqu4RB-Ukp2tR5WDQJB9P-uRPgGp3L6MDz2XfPAE"
    SPREADSHEET_ID_CONFERENCE="1yAI2wwNWBWdWfrbaiXA5EvjuKoHCztwjAnUYRkNNbPw"
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
    #---
    conference_title=["リアルタイム競技会一覧"]
    member_title=["記録申請フォーム"]
    # reset_sheets(
    #     spreadsheet_id=SPREADSHEET_ID_CONFERENCE,
    #     sheet_names=conference_title,
    #     cred_dict=creds_dict
    # )
    # reset_sheets(
    #     spreadsheet_id=SPREADSHEET_ID_MEMBER,
    #     sheet_names=member_title,
    #     cred_dict=creds_dict
    # )

    #---


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
    #print(member_list)
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