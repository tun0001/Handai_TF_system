import os
from pathlib import Path
import argparse
import json
from datetime import datetime, date
from scraper.fetcher import *
from scraper.parser import *
import gspread
from scraper.fetcher import fetch_html, fetch_url_univ
#from database.db import save_results
from scraper.athlete_ranking_adaptive_scraper import *
from scraper.parser import *
from urllib.parse import urljoin, urlparse
import pandas as pd
from pathlib import Path
import requests
import os
import asyncio
from discord_poster import send_to_thread
import time

def run_form_change(spread_sheet_ID_member, spread_sheet_ID_form, creds_dict):
    """
    Formの変更を行う関数
    """
    # Google Sheets APIの認証
    gc = gspread.service_account_from_dict(creds_dict)
    
    # スプレッドシートの取得
    sh_member = gc.open_by_key(spread_sheet_ID_member)
    sh_form = gc.open_by_key(spread_sheet_ID_form)
    
    
    # シートの取得
    #worksheet_member = sh_member.sheet1
    worksheet_form = sh_form.sheet1
    # ヘッダー行（1行目）を列名として使用
     # 【修正】正しい方法でDataFrameを作成
    all_values = worksheet_form.get_all_values()
    headers = all_values[0]
    data_rows = all_values[1:]  # データ行（2行目以降）
    if not data_rows:
        print("シートにデータがありません")
        return
    # DataFrameを作成
    #df_results = pd.DataFrame(data_rows, columns=headers)
    # DataFrameを作成
    df_results = pd.DataFrame(data_rows, columns=headers)
    # ここにフォーム変更のロジックを追加
    print("フォーム変更処理を実行中...")
    #df_results = pd.DataFrame(worksheet_form.get_all_values())
    
    # 例: メンバーシートからデータを取得してフォームシートに書き込む
    #print(df_results)
    for index, df_result in df_results.iterrows():
        df_result['競技']=df_result['種別']+ df_result['種目']
        event_name = df_result['種目']

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
        df_result['type'] = event_type
        if event_type == 'Relay':
            if '男' in event_name:
                name = "男子リレー"
            elif '女' in event_name:
                name = "女子リレー"
            else:
                name = "リレー"
            
            if df_result['記録']=="":
                # 先頭行を削除して次へ
                worksheet_form.delete_rows(2)  # 2行目（ヘッダーの次）を削除
                continue
        else:
            player_name = parse_player_name(str(df_result['氏名']))
            name = player_name
            add_member_list(name)
        
        print(f"選手名: {name}, 種目: {event_name}, 種別: {event_type}")
        #print(df_result)
        time.sleep(1)  # API制限対策のため1秒待機
        #print(df_result['完了'])
        write_member_record_to_sheet(
            spreadsheet_id=spread_sheet_ID_member,
            sheet_name=name,
            data=df_result.to_dict(),  # Seriesを辞書に変換
            cred_dict=creds_dict,
            univ_name=df_result['所属']
        )
        time.sleep(1)  # API制限対策のため1秒待機
        write_to_new_sheet( 
            spreadsheet_id=spread_sheet_ID_form,
        
            sheet_name="申請ログ",
            data=df_result.to_dict(),  # Seriesを辞書に変換
            cred_dict=creds_dict
        )
        #print(worksheet_form.get_all_records())
        # Check if there are more than one data rows before deleting
        current_rows = len(worksheet_form.get_all_values())
        if current_rows > 2:  # Header + at least 2 data rows
            worksheet_form.delete_rows(2)  # +2 because index is 0-based and row 1 is header
        else:
            # Clear the content of the last row instead of deleting it
            worksheet_form.batch_clear(['A2:Z2'])  # Clear a reasonable range of columns
        #print(worksheet_form.get_all_records())
        
    
    print("フォーム変更が完了しました。")

