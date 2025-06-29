import os
from pathlib import Path
import argparse
import json
from datetime import datetime, date
from scraper.fetcher import *
from scraper.parser import *
import gspread
import argparse
from scraper.fetcher import fetch_html, fetch_url_univ
#from database.db import save_results
from scraper.parser import *
from urllib.parse import urljoin, urlparse
import pandas as pd
from pathlib import Path
import requests
import os
import asyncio
from discord_poster import send_to_thread
import time

def run_real_time_v2(url, univ, spread_sheet_ID_conference, spread_sheet_ID_member, creds_dict, announce_discord=True):
    """
    競技のリアルタイム情報を取得し、スプレッドシートに更新する関数
    """
    base_url= get_base_url(url)
    #  Get Url and HTML "競技者一覧画面""
    url_kyougisya_itirann = urljoin(base_url, 'master.html')
    
    # Get url and HTML ”競技別一覧表(開始時刻)"
    url_kyougi_betsu_itiran = urljoin(base_url, 'tt.html')
    if check_url_exists(url_kyougi_betsu_itiran) is None:
        print(f"⚠️ URL が存在しません: {url_kyougi_betsu_itiran}")
        return
    
    # プロジェクトルートから database/realtime フォルダを指す
    realtime_dir = Path(__file__).parent.parent.parent / 'database' / 'realtime'
    # Webhook URL を環境変数から取得（または直書きしてもOK）
    #WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
    """
    1.url->htmlを取得
    2.大会名を取得
    2.1.大会名のフォルダを作成
    ・なければ作る．

    
    ・あれば，履歴を確保
    """
    html= fetch_html(url_kyougi_betsu_itiran)
    if html is None:
        print(f"⚠️ html が存在しません: {url_kyougi_betsu_itiran}")
        return
    
    conference_name=parse_conference_title(html)
    add_conference_list(conference_name)
    events_name= parse_each_event_name_kaisizikoku(html)
    print(f"大会名: {conference_name}")
    #print(f"競技名: {events_name}")
    # df_status_new= pd.DataFrame(events_name)
    # print(df_status_new)


    conference_dir = realtime_dir / conference_name
    status_path = conference_dir / "event_status.json"
    results_path = conference_dir / "results.json"
    
    # # 認証スコープ
    # scope = ['https://www.googleapis.com/auth/spreadsheets']
    # #creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    # client = gspread.authorize(creds_dict)
    # worksheet_conference = client.open_by_key(spread_sheet_ID_conference).sheet1
    # worksheet_member = client.open_by_key(spread_sheet_ID_member).sheet1
    
    
    #----------------------------------------------------
    if not conference_dir.exists():
        df_status= pd.DataFrame(events_name)
        df_status["status"] = "未完了"
        print(df_status)
        conference_dir.mkdir(parents=True, exist_ok=True)
        df_status.to_json(str(status_path), orient="records", lines=True)
        df_results= pd.DataFrame([])
        df_results.to_json(str(results_path), orient="records", lines=True)
        print(f"大会フォルダを作成しました: {conference_dir}")
    
    else:
        df_status = pd.read_json(str(status_path), orient="records", lines=True)
        df_results=pd.read_json(str(results_path), orient="records", lines=True)
        #df_results= pd.DataFrame([])
        #print(df_status)
    #----------------------------------------------------
    now_result=parse_each_event_name_kaisizikoku(html)
    df_now_result = pd.DataFrame(now_result)
    df_status['状況']=df_now_result['状況']
    #df_status['type']=df_now_result['type']
    #print(df_status[df_status['状況'] != "結果"])
    df_peding= df_status[df_status["status"] == "未完了"]
    #print(df_status)
    if df_peding.empty:
        time.sleep(1)  # API制限対策のため1秒待機
        if check_sheet_exists(
            spreadsheet_id=spread_sheet_ID_conference,
            sheet_name=conference_name,
            cred_dict=creds_dict
        ):
            print("ℹ️ すでにすべての種目が完了しています。")
        else:
            # NaNやinfを空文字列に置換してからupdate()を呼ぶ
            cleaned_results = df_results.replace([float('inf'), float('-inf')], pd.NA)
            values=[cleaned_results.columns.tolist()] + cleaned_results.fillna('').values.tolist()
            #print(cleaned_results)
            #print(len(cleaned_results))
            write_to_new_sheet(
                spreadsheet_id=spread_sheet_ID_conference,
                sheet_name=conference_name,
                data=values,
                cred_dict=creds_dict,
                num_rows=len(cleaned_results)+1,  # データがある場合のみシートを作成
                num_cols=len(cleaned_results.columns)+1  # 列数も指定
            )
            #print("ℹ️ すべての種目が完了しています。")
        return
    
    
    for index, row in df_peding.iterrows():
        #まず，種目の完了を判断
        #print(row)
        #print(row["種目"])
        if row['状況']== "結果":
        # finish,urls=parse_all_event_finish(html=html, 
        #                    event_name=row["種目"], 
        #                    kubun=row["レース区分"],
        #                    betsu=row["種別"])
            #print("種目:", row["種目"],row["種別"],row["レース区分"])
            
            
            url=row['url']
            # for url in urls:
            #種目のURLを取得
            #print("種目のURL:", url)
            event_url = urljoin(base_url, url)
            #大学名で探索して，速報を取得．
            html_event= fetch_html(event_url)
            #種目の詳細を取得
            result=parse_event_detail(html_event,player_name=None,univ=univ)
            df_result=pd.DataFrame(result)
            if result is not None:
                #print(df_result)
                #print(df_status.at[index, "status"])
                if '種目' in row:
                    df_result['種目'] = row['種目']
                if '種別' in row:
                    df_result['種別'] = row['種別']
                df_results = pd.concat([df_results, df_result], ignore_index=True)
                for idx in range(len(df_result)):
                    # スプレッドシートに書き込む
                    #print(df_result)
                    #print(df_result.iloc[idx])
                    # "種目"と"種別"カラムが存在しない場合は追加
                    if '種目' in row:
                        df_result.at[idx, '種目'] = row['種目']
                    if '種別' in row:
                        df_result.at[idx, '種別'] = row['種別']
                    
                    if row['type'] == 'Relay':
                        if '種別' in row:
                            if '男' in str(row['種別']):
                                name = "男子リレー"
                            elif '女' in str(row['種別']):
                                name = "女子リレー"
                            else:
                                name = "リレー"
                        else:
                            name = "リレー"
                    else:
                        # 氏名から全角スペースを除いた文字列でmember_listから一致するものをnameとする

                        member_list = load_member_list()
                        player_name = parse_player_name(str(df_result.iloc[idx]['氏名']))
                        player_name = player_name.replace('　', '').replace(' ', '')
                        name = None
                        for member in member_list:
                            #print(f"比較: {player_name} vs {member.replace('　', '').replace(' ', '')}")
                            if player_name == member.replace('　', '').replace(' ', ''):
                                
                                name = member
                                break
                        if name is None:
                            name = parse_player_name(str(df_result.iloc[idx]['氏名']))
                        
                    add_member_list(name)
                    add_event_list(row['種目'])
                    print(f"選手名: {name}, 種目: {row['種目']}")
                    #print(name)
                    time.sleep(1)  # API制限対策のため1秒待機
                    write_to_new_sheet(
                        spreadsheet_id=spread_sheet_ID_member,
                        sheet_name=name,
                        data=df_result.iloc[idx].to_dict(),
                        cred_dict=creds_dict
                    )
                    #--------
                    time.sleep(1)  # API制限対策のため1秒待機
                    # delete_sheet(
                    #     spreadsheet_id=spread_sheet_ID_conference,
                    #     sheet_name=name,
                    #     cred_dict=creds_dict
                    # )
                    if announce_discord:    
                        if not df_result.empty:
                            # content: 各列名:値 形式で整形
                            #------
                            process_sheet( 
                                spreadsheet_id=spread_sheet_ID_member,
                                sheet_name=name,
                                creds_dict=creds_dict
                            )
                            df_all=load_sheet(
                                spreadsheet_id=spread_sheet_ID_member,
                                sheet_name=name,
                                creds_dict=creds_dict
                            )
                            df_result_send = df_all[df_all['大会'] == conference_name]
                            if not df_result_send.empty:
                                df_result_send = df_result_send.iloc[[-1]]  # Get the last row as a dataframe
                            else:
                                df_result_send = df_all.iloc[[-1]]  # Fallback to the last row of the original dataframe
                            print(df_result_send)
                            # Remove columns that contain only NaN values or empty strings
                            df_result_send = df_result_send.dropna(axis=1, how='all')
                            df_result_send = df_result_send.loc[:, ~(df_result_send == '').all()]
                            print(df_result_send)

                            #------
                            lines = []
                            for _, row in df_result_send.iterrows():
                                for col in df_result_send.columns:
                                    lines.append(f"{col}: {row[col]}")
                                lines.append("")  # 行間を空ける
                            # コードブロックで囲んで Discord に送信
                            content = "```text\n" + "\n".join(lines) + "```"
                            # thread_name: 大会名をスレッド名に
                            thread_name = conference_name
                            # channel_id, token は環境変数から取得
                            #hannel_id = int(os.environ["DISCORD_CHANNEL_ID"])
                            channel_id = int(1380200984256450751)
                            token = os.environ["DISCORD_BOT_TOKEN"]
                            print(f"▶️ Discord に投稿: channel={channel_id}, thread={thread_name}")
                            # 非同期関数を実行
                            asyncio.run(send_to_thread(
                                token=token,
                                channel_id=channel_id,
                                thread_name=thread_name,
                                content=content
                            ))
                        else:

                            print("ℹ️ 新規結果なし。Discord 送信をスキップします。")

                    #-------
                    # write_to_new_sheet(
                    #     spreadsheet_id=spread_sheet_ID_conference,
                    #     sheet_name=conference_name,
                    #     data=df_result.iloc[idx].to_dict(),
                    #     cred_dict=creds_dict
                    # )
            df_status.at[index, "status"] = "完了"
            df_status.to_json(str(status_path), orient="records", lines=True)
            df_results.to_json(str(results_path), orient="records", lines=True)


    # ─── Discord へ結果をポスト ─────────────────────────────────────
            
    #---------------------------------------------------
    #print(df_results)
    df_status.to_json(str(status_path), orient="records", lines=True)
    df_results.to_json(str(results_path), orient="records", lines=True)

def run_real_time_players(url, spread_sheet_ID_member,player_names, creds_dict, announce_discord=True):
    """
    競技のリアルタイム情報を取得し、スプレッドシートに更新する関数
    """
    base_url= get_base_url(url)
    #  Get Url and HTML "競技者一覧画面""
    url_kyougisya_itirann = urljoin(base_url, 'master.html')
    
    # Get url and HTML ”競技別一覧表(開始時刻)"
    url_kyougi_betsu_itiran = urljoin(base_url, 'tt.html')
    if check_url_exists(url_kyougi_betsu_itiran) is None:
        print(f"⚠️ URL が存在しません: {url_kyougi_betsu_itiran}")
        return
    
    # プロジェクトルートから database/realtime フォルダを指す
    realtime_dir = Path(__file__).parent.parent.parent / 'database' / 'realtime'
    # Webhook URL を環境変数から取得（または直書きしてもOK）
    #WEBHOOK_URL = os.environ["DISCORD_WEBHOOK"]
    """
    1.url->htmlを取得
    2.大会名を取得
    2.1.大会名のフォルダを作成
    ・なければ作る．

    
    ・あれば，履歴を確保
    """
    html= fetch_html(url_kyougi_betsu_itiran)
    if html is None:
        print(f"⚠️ html が存在しません: {url_kyougi_betsu_itiran}")
        return
    
    #conference_name=parse_conference_title(html)
    #add_conference_list(conference_name)
    events_name= parse_each_event_name_kaisizikoku(html)
    #print(f"大会名: {conference_name}")
    #print(f"競技名: {events_name}")
    # df_status_new= pd.DataFrame(events_name)
    # print(df_status_new)


    #conference_dir = realtime_dir / conference_name
    #status_path = conference_dir / "event_status.json"
    #results_path = conference_dir / "results.json"
    
    # # 認証スコープ
    # scope = ['https://www.googleapis.com/auth/spreadsheets']
    # #creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    # client = gspread.authorize(creds_dict)
    # worksheet_conference = client.open_by_key(spread_sheet_ID_conference).sheet1
    # worksheet_member = client.open_by_key(spread_sheet_ID_member).sheet1
    df_status= pd.DataFrame(events_name)
    df_status["status"] = "未完了"
    df_results= pd.DataFrame([])
    #----------------------------------------------------
    # if not conference_dir.exists():
    #     df_status= pd.DataFrame(events_name)
    #     df_status["status"] = "未完了"
    #     print(df_status)
    #     conference_dir.mkdir(parents=True, exist_ok=True)
    #     df_status.to_json(str(status_path), orient="records", lines=True)
    #     df_results= pd.DataFrame([])
    #     df_results.to_json(str(results_path), orient="records", lines=True)
    #     print(f"大会フォルダを作成しました: {conference_dir}")
    
    # else:
    #     df_status = pd.read_json(str(status_path), orient="records", lines=True)
    #     df_results=pd.read_json(str(results_path), orient="records", lines=True)
    #     #df_results= pd.DataFrame([])
    #     #print(df_status)
    #----------------------------------------------------
    #now_result=parse_each_event_name_kaisizikoku(html)
    #df_now_result = pd.DataFrame(now_result)
    #df_status['状況']=df_now_result['状況']
    #df_status['type']=df_now_result['type']
    #print(df_status[df_status['状況'] != "結果"])
    df_peding= df_status[df_status["status"] == "未完了"]
    if df_peding.empty:
        time.sleep(1)  # API制限対策のため1秒待機
        # if check_sheet_exists(
        #     spreadsheet_id=spread_sheet_ID_conference,
        #     sheet_name=conference_name,
        #     cred_dict=creds_dict
        # ):
        #     print("ℹ️ すでにすべての種目が完了しています。")
        # else:
        #     # NaNやinfを空文字列に置換してからupdate()を呼ぶ
        #     cleaned_results = df_results.replace([float('inf'), float('-inf')], pd.NA)
        #     values=[cleaned_results.columns.tolist()] + cleaned_results.fillna('').values.tolist()
        #     #print(cleaned_results)
        #     #print(len(cleaned_results))
        #     write_to_new_sheet(
        #         spreadsheet_id=spread_sheet_ID_conference,
        #         sheet_name=conference_name,
        #         data=values,
        #         cred_dict=creds_dict,
        #         num_rows=len(cleaned_results)+1,  # データがある場合のみシートを作成
        #         num_cols=len(cleaned_results.columns)+1  # 列数も指定
        #     )
        #     #print("ℹ️ すべての種目が完了しています。")
        return
    
    
    for index, row in df_peding.iterrows():
        #まず，種目の完了を判断
        #print(row)
        #print(row["種目"])
        if row['状況']== "結果":
        # finish,urls=parse_all_event_finish(html=html, 
        #                    event_name=row["種目"], 
        #                    kubun=row["レース区分"],
        #                    betsu=row["種別"])
            print("種目:", row["種目"],row["種別"],row["レース区分"])
            
            
            url=row['url']
            # for url in urls:
            #種目のURLを取得
            #print("種目のURL:", url)
            event_url = urljoin(base_url, url)
            #大学名で探索して，速報を取得．
            html_event= fetch_html(event_url)
            #種目の詳細を取得
            for player_name in player_names:
                result=parse_event_detail(html_event,player_name=player_name,univ=None)
                if result is not None:
                    # Convert to list if result is not already a list
                    if isinstance(result, dict):
                        result = [result]
                    df_result=pd.DataFrame(result)
                    #print(df_result)
                    #print(df_status.at[index, "status"])
                    if '種目' in row:
                        df_result['種目'] = row['種目']
                    if '種別' in row:
                        df_result['種別'] = row['種別']
                    df_results = pd.concat([df_results, df_result], ignore_index=True)
                    for idx in range(len(df_result)):
                        # スプレッドシートに書き込む
                        #print(df_result)
                        #print(df_result.iloc[idx])
                        # "種目"と"種別"カラムが存在しない場合は追加
                        if '種目' in row:
                            df_result.at[idx, '種目'] = row['種目']
                        if '種別' in row:
                            df_result.at[idx, '種別'] = row['種別']
                        
                        if row['type'] == 'Relay':
                            if '種別' in row:
                                if '男' in str(row['種別']):
                                    name = "男子リレー"
                                elif '女' in str(row['種別']):
                                    name = "女子リレー"
                                else:
                                    name = "リレー"
                            else:
                                name = "リレー"
                        else:
                            # 氏名から全角スペースを除いた文字列でmember_listから一致するものをnameとする

                            member_list = load_member_list()
                            player_name = parse_player_name(str(df_result.iloc[idx]['氏名']))
                            player_name = player_name.replace('　', '').replace(' ', '')
                            name = None
                            for member in member_list:
                                #print(f"比較: {player_name} vs {member.replace('　', '').replace(' ', '')}")
                                if player_name == member.replace('　', '').replace(' ', ''):
                                    
                                    name = member
                                    break
                            if name is None:
                                name = parse_player_name(str(df_result.iloc[idx]['氏名']))
                            
                        add_member_list(name)
                        add_event_list(row['種目'])
                        print(name)
                        print(row["種目"])
                        time.sleep(1)  # API制限対策のため1秒待機
                        write_to_new_sheet(
                            spreadsheet_id=spread_sheet_ID_member,
                            sheet_name=name,
                            data=df_result.iloc[idx].to_dict(),
                            cred_dict=creds_dict
                        )
                        #--------
                        # time.sleep(1)  # API制限対策のため1秒待機
                        # delete_sheet(
                        #     spreadsheet_id=spread_sheet_ID_conference,
                        #     sheet_name=name,
                        #     cred_dict=creds_dict
                        # )

                        #-------
                        # write_to_new_sheet(
                        #     spreadsheet_id=spread_sheet_ID_conference,
                        #     sheet_name=conference_name,
                        #     data=df_result.iloc[idx].to_dict(),
                        #     cred_dict=creds_dict
                        # )
            # df_status.at[index, "status"] = "完了"
            # df_status.to_json(str(status_path), orient="records", lines=True)
            # df_results.to_json(str(results_path), orient="records", lines=True)


    # # ─── Discord へ結果をポスト ─────────────────────────────────────
    #         if announce_discord:    
    #             if not df_result.empty:
    #                 # content: 各列名:値 形式で整形
    #                 lines = []
    #                 for _, row in df_result.iterrows():
    #                     for col in df_result.columns:
    #                         lines.append(f"{col}: {row[col]}")
    #                     lines.append("")  # 行間を空ける
    #                 # コードブロックで囲んで Discord に送信
    #                 content = "```text\n" + "\n".join(lines) + "```"
    #                 # thread_name: 大会名をスレッド名に
    #                 thread_name = conference_name
    #                 # channel_id, token は環境変数から取得
    #                 channel_id = int(os.environ["DISCORD_CHANNEL_ID"])
    #                 token = os.environ["DISCORD_BOT_TOKEN"]
    #                 print(f"▶️ Discord に投稿: channel={channel_id}, thread={thread_name}")
    #                 # 非同期関数を実行
    #                 asyncio.run(send_to_thread(
    #                     token=token,
    #                     channel_id=channel_id,
    #                     thread_name=thread_name,
    #                     content=content
    #                 ))
    #             else:

    #                 print("ℹ️ 新規結果なし。Discord 送信をスキップします。")
    # #---------------------------------------------------
    # print(df_results)
    # df_status.to_json(str(status_path), orient="records", lines=True)
    # df_results.to_json(str(results_path), orient="records", lines=True)



