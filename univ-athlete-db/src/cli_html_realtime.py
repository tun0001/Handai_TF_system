import os
import json
from cli.real_time import *
import pandas as pd
import time

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
        # "https://gold.jaic.org/kagawa/2025/2025kokusupo/kyougi.html",
        # "http://www.narariku.com/HTML/2025/2025-kyouka-kokuspo/kyougi.html",
        # "https://gold.jaic.org/jaic/icaak/record/2025/25_DOSHISHAKYOTO/kyougi.html",
        # "https://gold.jaic.org/jaic/icaak/record/2025/8_GK1/kyougi.html",
        "https://gold.jaic.org/jaic/icaak/record/2025/25_HANSHIN4/tt.html"
        # "https://gold.jaic.org/jaic/icaak/record/2025/25_NISHINIHON/kyougi.html"
        # "https://gold.jaic.org/tokushima/250811/kyougi.html",
        # "https://www.oaaa.jp/results/r_25/osk_champ/kyougi.html",
        # #"http://npo-kochi.sports.coocan.jp/taikaikekka/23/07kokutaiU16/kyougi.html",
        # "https://gold.jaic.org/jaic/icaak/record/2025/7_1stLONG/kyougi.html",
        #"https://gold.jaic.org/jaic/member/kagosima/2025/result/ishigaku2/kyougi.html"

        }
    url= "https://www.ui-techno.jp/kanjitsu/game/r_23/kirokukai/kyougi.html"
    #山中　一凛
    #山中　一凜
    #TimeTable.htmlじゃないとむり
    # spread_sheet_ID_OSAKA=os.getenv("SPREAD_SHEET_ID_OSAKA")
    # spread_sheet_ID_OSAKA = json.loads(spread_sheet_ID_OSAKA)
    # print(spread_sheet_ID_OSAKA)
    # spread_sheet_ID_conference= spread_sheet_ID_OSAKA["CONFERENCE"]
    # spread_sheet_ID_member=spread_sheet_ID_OSAKA["MEMBER"]
    # spread_sheet_ID_sb=spread_sheet_ID_OSAKA["SB"]
    # spread_sheet_ID_pb=spread_sheet_ID_OSAKA["PB"]
    # univ_name=spread_sheet_ID_OSAKA["UNIV_NAME"]
    # print(univ_name)
    # spread_sheet_ID_conference=os.getenv("SPREAD_SHEET_ID_CONFERENCE")
    # spread_sheet_ID_member=os.getenv("SPREAD_SHEET_ID_MEMBER")
    creds_dict=os.getenv("GOOGLE_ACOUNT_KEY_SHEET_TF")
    
    creds_dict = json.loads(creds_dict)
    spread_sheet_dict = os.getenv("SPREAD_SHEET_UNIVS")
    print(spread_sheet_dict)
    spread_sheet_dict = json.loads(spread_sheet_dict)
    spread_sheet_dict = pd.DataFrame(spread_sheet_dict).to_dict(orient='list')
    announce_discord = False
    print(spread_sheet_dict)

    spread_sheet_ID_member=spread_sheet_dict["MEMBER"][0]
    spread_sheet_ID_pb=spread_sheet_dict["PB"][0]
    spread_sheet_ID_sb=spread_sheet_dict["SB"][0]
    spread_sheet_ID_member_kobe=spread_sheet_dict["MEMBER"][1]
    spread_sheet_ID_pb_kobe=spread_sheet_dict["PB"][1]
    spread_sheet_ID_sb_kobe=spread_sheet_dict["SB"][1]

    print(spread_sheet_ID_pb)
    # #  # テスト用のダミーデータ
    # # name="川﨑　雄介"
    

    # # # #run_real_time_players(url=url, player_names="大名門　里歩", spread_sheet_ID_member=spread_sheet_ID_member, creds_dict=creds_dict, announce_discord=announce_discord)
    while True:
        for url in urls:
            run_real_time_v2(url=url, spread_sheet_dict=spread_sheet_dict, creds_dict=creds_dict,announce_discord=announce_discord)
        member_sb_to_sheet(
            spreadsheet_id_member=spread_sheet_ID_member_kobe,
            spreadsheet_id_sb=spread_sheet_ID_sb_kobe,
            creds_dict=creds_dict,
            season=2025
        )

        member_pb_to_sheet(
            spreadsheet_id_member=spread_sheet_ID_member_kobe,
            spreadsheet_id_pb=spread_sheet_ID_pb_kobe,
            creds_dict=creds_dict
        )


        
        # 30分（1800秒）待機
        time.sleep(1800)