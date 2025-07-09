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
    #creds_env = os.getenv('GOOGLE_ACCOUNT_KEY')
    creds_dict={
    "type": "service_account",
    "project_id": "handai-tf-system-control",
    "private_key_id": "ab0ab0cb57e3284ae505af098928106f6c332bd7",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDNC+Wc3rmcf30u\n5p5MvM2jUT4VigO0XoiTMqJatBLN4kHSZjSX6K4Tpk708s9rsAgiWKHJ0KoZqx4X\nO2IfJM6PllhrZTuqlG3Ny9nEd9eVv6yTNsP66a1b2xKeRTSLMAyGY6EQIBRdfjIY\nA83lNLZeE6V7s5VeKn0AS0EcCoQJMb64AomqM630L4GBiHK1NF7Dag0g11H3fvSR\nawQMzaD6N8pyS80GRpx7YwoIBsmV4obRdZHXDiUz6Vgrwrm/5NECgt7QVal0kCp8\nriOOacSV8PviYJw3fmYCdeq6fMDMkunZVqU61aCPWTPW49TJFHkCOCRFhFgK53gY\nOx2cpqY7AgMBAAECggEAFMvrGvEAFF5d3P7o+VGA7dqUmGyqGYYpBfzxuI9hBN64\n3FUfanTgCwAoK/HglcSB3rHsnuJ6DiZr4+FS/2OlS6ztBN98oL1zMZdGXAXnqLmL\nEFdSo0VGHvXmOoU8Yg2ah5rdQBxw1FazT/o6zM9+26XUd+pr8OQQT5JSZTyvzZq+\ncU5jcLDPKTWx3D2NY2vyE4sxh990tJGFu7n8NWoT+zqlRtn+JIToymG3POGasZAy\nbdkWT3uWh/ACNAs0XmWPFHoY/ip5GAva8fxyYs5cshH7f6FMHRx+R9DlfEvr9h7x\nCc3vfb0P6Mk+Z+FneA6EwQh+V//w6SSq54ZO40J3mQKBgQD0iWgYNtYAtyPjtjc5\nQLWj6TpSIYoVZhAp9AAxpBW6knMmHqwCL9BlPzJt3a6f2JV/YTctEK5YshowqeCX\nciK30RTiVAD8GmUfGQlEV0FgIAeRC+a6LglO271U8icBey+mpIuP/ubmZ4tBzOyh\nqzI9RvaDNk0x99nHqxZyW6psvQKBgQDWqJUZe4VtsLUS1u64jQ3J7ke4uPAWoZmH\nqy1vB05vO33pUuuqFNoR08KNgdp4kgQLyewLoefd7vl5sYJL1jb4CA8lzPXYvLAb\n/qVvcG/ucC+HWlDqEg+hZzl6geqXr46pRu8oqFO5MtA/t1KeFv2CHPSz81vuxABS\ntx6lG7qaVwKBgQCLbESTecBuS/0EegHmfMSTngiIh2LpbHXO1bW+l+VjqNhKZbaA\n0K4q6+texMQpkx05sT36TcZ5/6H7GQBamNK+p1EW8fpVwt7g6i9kbbNykRB/XJ/C\nizj3Y0YBxscCiy/R/YMtKJKRz3uQmrxYOPm+AlXO3gkJcl0TALMdpLH4qQKBgCMP\nRcrzscdIpUp+cF8UKrxgfrZc/lmz6y+Ndc48k0L3pIkHUhZlcXiX7Z7PJq+qqZ6D\nTFpaB1ToQzbtFyrrwe6g4lh6MW1E5D6uSLb61k1LZXfl+HFCoerqwSiRL4+2zMY5\nH7a0R3hoJDtD5eqMNruZnx4FEW7d9G+OGSM+dCvhAoGBAO49AOIUu3sZCIjPNbvw\n3P4afVy7WT/BkhQOECgMkucKKeg3rMPn/7cAOIIFqFh+z+5yNsDn4YiYztCTten7\nvceWxYThIR85fqpEPWtXVNC6HEm/TmdqK0geoaf4MdSy0GWhtkjB+TxWmEBy1zES\nQ+CtH2ADdK5WibsH/j3QgZxw\n-----END PRIVATE KEY-----\n",
    "client_email": "edit-tf-schedule@handai-tf-system-control.iam.gserviceaccount.com",
    "client_id": "115271653994163090816",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/edit-tf-schedule%40handai-tf-system-control.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
    }


    # if not creds_env:
    #     print("❌ 環境変数 GOOGLE_SHEETS_CREDENTIALS が設定されていません。")
    #     return
        
    # try:
    #     # creds_envがすでに正しいJSON文字列の場合、そのままロード
    #     creds_dict = json.loads(creds_env)
    # except json.JSONDecodeError as e:
    #     print(f"❌ 認証情報のJSONデコードに失敗しました: {e}")
    #     return


    # 認証スコープ

    scope = ['https://www.googleapis.com/auth/spreadsheets']
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)

    # スプレッドシートを開く
    SPREADSHEET_ID_MEMBER = os.getenv('SPREADSHEET_ID_MEMBER')
    SPREADSHEET_ID_CONFERENCE = os.getenv('SPREADSHEET_ID_CONFERENCE')
    SPREADSHEET_ID_BEST = os.getenv('SPREADSHEET_ID_BEST')
    SPREADSHEET_ID_MEMBER="1vN-qqu4RB-Ukp2tR5WDQJB9P-uRPgGp3L6MDz2XfPAE"
    SPREADSHEET_ID_CONFERENCE="1yAI2wwNWBWdWfrbaiXA5EvjuKoHCztwjAnUYRkNNbPw"
    SPREADSHEET_ID_BEST="1ODPNaPIrphI1NV8ZXI5MLM6arKjKnVa7RxounPeX9CM"
    worksheet_conference = client.open_by_key(SPREADSHEET_ID_CONFERENCE).sheet1
    worksheet_member = client.open_by_key(SPREADSHEET_ID_MEMBER).sheet1
    
    # シートの全データ取得（2次元リスト）
    
    urls = load_com_urls()
    print(urls)
    member_to_find=['国吉　遼河','百濃　隼大','中嶋　遼']
    # urls=[
    #     "https://gold.jaic.org/icaak/record/2024/14_SHUMOKU/kyougi.html",
    #      "https://gold.jaic.org/icaak/record/2023/14_SHUMOKU/kyougi.html"
    #      ]
    urls_high=[
        #"https://www.oaaa.jp/kotairen/12chiku/startlist/2024/240504/kyougi.html",
        #"https://www.oaaa.jp/kotairen/12chiku/startlist/2024/240504/kyougi.html",
        #"http://www.haaa.jp/~kobe/2023/03long3/web/kyougi.html",
        #"http://www.haaa.jp/~kobe/2022/12ih/web/kyougi.html",
        #"https://jaaftokushima.com/2022/koukousoutai/kyougi.html",
        
        #"https://gold.jaic.org/kagawa/2023/2023kagawaCh/kyougi.html",
        # "https://gold.jaic.org/kagawa/2023/2023koukou/2023shikokusoutai/tt.html",
        # "https://gold.jaic.org/kagawa/2023/2023kirokukai/tt.html",
        
        #"https://gold.jaic.org/kagawa/2024/2025touteki/tt.html",
        
        #"https://jaaftokushima.com/2021/anancity/open/kyougi.html",
        #"http://www.haaa.jp/~koukou/2021/ih/html/rel063.html",
        #"https://oaaa.jp/kotairen/results/2024/2_kiroku2/kyougi.html",
        #"https://www.oaaa.jp/kotairen/12chiku/startlist/2023/231104/kyougi.html"
        #"https://gold.jaic.org/osaka/2023/osk_champ/tt.html",
        #"https://www.oaaa.jp/kotairen/12chiku/startlist/2023/230827/tt.html"
        # "http://breaking.sagarikujyo.jp/R06/R06_kokspo/rel064.html",
        # "http://seibanrikujou.g1.xrea.com/r6/tikubetu/html/tt.html",
        # "http://seibanrikujou.g1.xrea.com/r6/seibanIH/html/kyougi.html",
        # "http://www.haaa.jp/2022/hyo/web/tt.html",
        "https://www.oaaa.jp/kotairen/12chiku/startlist/2023/230827/kyougi.html",
        "https://www.oaaa.jp/results/r_24/1kai_ban/rel046.html"

    ]
    member_high=[
        #"吉川　諒音",
        #"石川　慎翔",
        #"南本　寛茂",
        # "柳瀬　宏志郎",
        # "栁瀨　宏志郎"
        #"藤村　修冬",
        #"小川　真帆",
        # "中島　壮一朗",
        # "山田　翔悟",
        "堀田　悠介"
        #"後藤　耀"
    ]
    # # # for url in urls:
    # for url in urls[:0]:
    #         #print(f"競技URL: {url}")
    #         # time.sleep(2)  # API制限対策のため1秒待機
    #         # 競技結果を取得
    #         #print(f"競技結果を取得中: {url}")
    #         #finsih_comp=run_real_time_v2(url=url, univ='大阪大', spread_sheet_ID_conference=SPREADSHEET_ID_CONFERENCE, spread_sheet_ID_member=SPREADSHEET_ID_MEMBER, creds_dict=creds_dict)
    #         #print(f"競技結果取得完了: {url}")
    #     finsih_comp=run_real_time_v2(
    #         url=url,
    #         univ='大阪大',
    #         spread_sheet_ID_conference=SPREADSHEET_ID_CONFERENCE,
    #         spread_sheet_ID_member=SPREADSHEET_ID_MEMBER,
    #         creds_dict=creds_dict,
    #         announce_discord=False
    #    )
    # for url in urls_high:
    #     finsih_comp=run_real_time_players(
    #         url=url,
    #         player_names=member_high,
    #         spread_sheet_ID_member=SPREADSHEET_ID_MEMBER,
    #         creds_dict=creds_dict,
    #         announce_discord=False
    #     )

    # member_list= load_member_list()
    # print(member_list)
    # for member in member_list[:30]:
    #     #p#rint(f"メンバー: {member['name']}, ID: {member['id']}, Discord: {member['discord']}")
    #     time.sleep(2)  # API制限対策のため1秒待機
    #     print(f"メンバー: {member}")
    #     process_sheet(
    #         spreadsheet_id=SPREADSHEET_ID_MEMBER,
    #         sheet_name=member,
    #         creds_dict=creds_dict
    #     )
    # member_best_to_sheet(
    #     spreadsheet_id_member=SPREADSHEET_ID_MEMBER,
    #     spreadsheet_id_best=SPREADSHEET_ID_BEST,
    #     creds_dict=creds_dict
    # )
    while True:
        data = worksheet_conference.get_all_values()

        # write_to_new_sheet(
        #     spreadsheet_id=SPREADSHEET_ID_CONFERENCE,
        #     sheet_name='試合ステータス',
        #     data=data,
        #     cred_dict=creds_dict  # ここでは直接 creds_dict を使うので None
        #     )
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
        #print(headers)
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
        #today = date(2025, 7, 5)  # YYYY, M, D の形式で固定日付に設定
        today = date.today()     # ← 本番はこっちを使う

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
                #print(f"Row {idx_row}: {start} ~ {end} → {status}")
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
        time.sleep(10)  # API制限対策のため1秒待機
        worksheet_conference.update('A2', values_to_write)
        # --------------------------------------------

        #print(df_comp[df_comp['試合ステータス']=="DOING"])  # ステータスの集計
        # 「DOING」か、または「DONE」かつ「TODO」の行を抽出
        
        #print(df_todo.head(10))  # 最初の10行を表示


        df_todo = df_comp[
            (df_comp['試合ステータス'] == "DOING")
            | (
                (df_comp['試合ステータス'] == "DONE")
                & (df_comp['結果作成'] != "DONE" )
            )
        ]

        for index, row in df_todo.iterrows():
            #print(f"大会名: {row['大会名']}, 開始日: {row['日付(開始日)']}, 終了日: {row['日付(終了日)']}")
            url= row['競技url']
            finsih_comp=run_real_time_v2(
                url=url,
                univ='大阪大',
                spread_sheet_ID_conference=SPREADSHEET_ID_CONFERENCE,
                spread_sheet_ID_member=SPREADSHEET_ID_MEMBER,
                creds_dict=creds_dict,
                announce_discord=True
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
        return

if __name__ == "__main__":
    main()