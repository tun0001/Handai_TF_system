import os
import json
from cli.real_time import *
import pandas as pd

if __name__ == "__main__":
    #url= "https://jaaf-shiga.com/results/2025/0712pch/shtml/TimeTable.html"
    #url="https://tsriku.stars.ne.jp/htmlR6/240727/shtml/SyozokuPlayer.html"
    #url="https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html"
    #url="http://nagoyatf.xyz/chita2/nans21v/shtml/TimeTable.html"
    #url="https://gold.jaic.org/jaic/icaak/record/2025/25_SANSHOSEN/kyougi.html"
    urls={
        #"https://gold.jaic.org/icaak/record/2024/24_%E9%98%AA%E7%A5%9E%E5%9B%9B%E5%A4%A7/kyougi.html",
        #"http://www.narariku.com/HTML/2024/kyouka/long1/kyougi.html",
        #"https://gold.jaic.org/icaak/record/2024/8_DISTANCE/kyougi.html",
        #"https://www.ui-techno.jp/kanjitsu/game/r_23/kirokukai/kyougi.html",
        #"https://gold.jaic.org/icaak/record/2024/24_SOSEISEN/kyougi.html"
        #"https://gold.jaic.org/icaak/record/2024/24_KEIHANSHIN/kyougi.html"
        #"http://www.narariku.com/HTML/2024/kyouka/kokuspo/kyougi.html"
        "https://gold.jaic.org/kagawa/2025/2025kokusupo/kyougi.html",
        "http://www.narariku.com/HTML/2025/2025-kyouka-kokuspo/kyougi.html",
        "https://gold.jaic.org/jaic/icaak/record/2025/25_DOSHISHAKYOTO/kyougi.html"

        }
    url= "https://www.ui-techno.jp/kanjitsu/game/r_23/kirokukai/kyougi.html"
    #山中　一凛
    #山中　一凜
    #TimeTable.htmlじゃないとむり    
    spread_sheet_ID_conference=os.getenv("SPREAD_SHEET_ID_CONFERENCE")
    spread_sheet_ID_member=os.getenv("SPREAD_SHEET_ID_MEMBER")
    creds_dict=os.getenv("GOOGLE_ACOUNT_KEY_SHEET_TF")
    creds_dict = json.loads(creds_dict)
    announce_discord = True

    # name_list={
    #     "柳瀬　宏志郎",
    #     "胗荑　宏志郎",
    #     "栁瀨　宏志郎"
    #     }
    # df_records=pd.DataFrame()
    # for name in name_list:
    #     time.sleep(1)
    #     df_record=load_sheet(
    #         spreadsheet_id=spread_sheet_ID_member,
    #         sheet_name=name,
    #         creds_dict=creds_dict
    #     )
    #     df_records=pd.concat([df_records, df_record], ignore_index=True)
    # print(df_records)
    # write_to_new_sheet(
    #     spreadsheet_id=spread_sheet_ID_member,
    #     sheet_name="柳瀬　宏志郎",
    #     data=df_records,
    #     cred_dict=creds_dict,
    # )
    # time.sleep(1)
    # process_sheet(
    #     spreadsheet_id=spread_sheet_ID_member,
    #     sheet_name="柳瀬　宏志郎",
    #     creds_dict=creds_dict
    # )

    #run_real_time_players(url=url, player_names="大名門　里歩", spread_sheet_ID_member=spread_sheet_ID_member, creds_dict=creds_dict, announce_discord=announce_discord)
    for url in urls:
        run_real_time_v2(url=url, univ="大阪大", spread_sheet_ID_conference=spread_sheet_ID_conference, spread_sheet_ID_member=spread_sheet_ID_member, creds_dict=creds_dict,announce_discord=announce_discord)