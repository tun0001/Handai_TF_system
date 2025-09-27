import os
from pathlib import Path
import argparse
import json
from datetime import datetime, date
from scraper.scrape_player_results import *
from scraper.scrape_university_results import *
from scraper.get_competition_name import *
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
from database.db_sheet import *

def run_real_time_spa(url, univ, spread_sheet_ID_conference, spread_sheet_ID_member, creds_dict, announce_discord=True):
    """
    競技のリアルタイム情報を取得し、スプレッドシートに更新する関数
    """
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
    # html= fetch_html(url_kyougi_betsu_itiran)
    # if html is None:
    #     print(f"⚠️ html が存在しません: {url_kyougi_betsu_itiran}")
    #     return
    
    conference_info = get_competition_info(url)
    print(conference_info)
    #add_conference_list(conference_name)
    #events_name= parse_each_event_name_kaisizikoku(html)
    #print(f"大会名: {conference_name}")
    #print(f"競技名: {events_name}")
    # df_status_new= pd.DataFrame(events_name)
    # print(df_status_new)
    df_events = scrape_univ_results_to_dataframe(timetable_url=url, university_name=univ)
    print(df_events[-9:])

    df_events_change=change_column_names(df_events)
    conference_name = conference_info['name']
    df_events_change['大会'] = conference_info['name']
    df_events_change['所属'] = univ
    df_events_change['大学名'] = univ
    print(df_events_change[-9:])

    for index, row in df_events_change.iterrows():
        time.sleep(2)
        
        event_name = df_events_change.at[index, '種目']
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
        df_events_change.at[index, 'type'] = event_type
        if event_type == 'Relay':
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
            player_name = parse_player_name(str(row['氏名']))
            name = player_name
            add_member_list(name)
        #print(name)
        print(f"選手名: {name}, 種目: {row['種目']}")
        # write_member_record_to_sheet(
        #     spreadsheet_id=spread_sheet_ID_member,
        #     sheet_name=name,
        #     data=row.to_dict(),
        #     cred_dict=creds_dict,
        #     univ_name=univ
        # )
        time.sleep(1)
        df_all=load_sheet(
            spreadsheet_id=spread_sheet_ID_member,
            sheet_name=name,
            creds_dict=creds_dict
        )
        df_result_send = return_record_status(df_all,row, univ)
        # if not df_result_send.empty:
        #     df_result_send = df_result_send.iloc[[-1]]  # Get the last row as a dataframe
        # else:
        #     df_result_send = df_all.iloc[[-1]]  # Fallback to the last row of the original dataframe
        print(df_result_send)
        # write_to_new_sheet(
        #     spreadsheet_id=spread_sheet_ID_conference,
        #     sheet_name=conference_name,
        #     data=df_result_send.to_dict(),
        #     cred_dict=creds_dict
        # )
        time.sleep(2)  # API制限対策のため1秒待機
        # df_all=load_sheet(
        #     spreadsheet_id=spread_sheet_ID_member
        #     sheet_name=name,
        #     creds_dict=creds_dict
        # )
        # df_result_send = return_record_status(df_all, df_results.iloc[idx], df_results.at[idx, 'univ'])
        # df_result_send['氏名'] = name
        # print(df_result_send)
        # time.sleep(3)  # API制限対策のため1秒待機
        # write_to_new_sheet(
        #     spreadsheet_id=spread_sheet_dict["CONFERENCE"][univ_index],
        #     sheet_name=conference_name,
        #     data=df_result_send.to_dict(),
        #     cred_dict=creds_dict
        # )
        if announce_discord:    
            if not df_result_send.empty and univ=="大阪大":
                # content: 各列名:値 形式で整形
                #------
                # process_sheet( 
                #     spreadsheet_id=spread_sheet_ID_member,
                #     sheet_name=name,
                #     creds_dict=creds_dict
                # )
                # df_all=load_sheet(
                #     spreadsheet_id=spread_sheet_ID_member,
                #     sheet_name=name,
                #     creds_dict=creds_dict
                # )
                # df_result_send = df_all[df_all['大会'] == conference_name]
                # if not df_result_send.empty:
                #     df_result_send = df_result_send.iloc[[-1]]  # Get the last row as a dataframe
                # else:
                #     df_result_send = df_all.iloc[[-1]]  # Fallback to the last row of the original dataframe
                # print(df_result_send)
                # # Remove columns that contain only NaN values or empty strings
                # df_result_send = df_result_send.dropna(axis=1, how='all')
                # df_result_send = df_result_send.loc[:, ~(df_result_send == '').all()]
                # print(df_result_send)

                #------
                lines = []
                if isinstance(df_result_send, pd.Series):
                    df_result_send = df_result_send.to_frame().T
                for _, row2 in df_result_send.iterrows():
                    for col in df_result_send.columns:
                        lines.append(f"{col}: {row2[col]}")
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
