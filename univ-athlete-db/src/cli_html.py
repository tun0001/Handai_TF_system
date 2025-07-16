import os
import json
from cli.real_time import *


if __name__ == "__main__":
    #url= "https://jaaf-shiga.com/results/2025/0712pch/shtml/TimeTable.html"
    #url="https://tsriku.stars.ne.jp/htmlR6/240727/shtml/SyozokuPlayer.html"
    #url="https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html"
    #url="http://nagoyatf.xyz/chita2/nans21v/shtml/TimeTable.html"
    url="https://gold.jaic.org/jaic/icaak/record/2025/25_SANSHOSEN/kyougi.html"
    #山中　一凛
    #山中　一凜
    #TimeTable.htmlじゃないとむり    
    spread_sheet_ID_conference=os.getenv("SPREAD_SHEET_ID_CONFERENCE")
    spread_sheet_ID_member=os.getenv("SPREAD_SHEET_ID_MEMBER")
    creds_dict=os.getenv("GOOGLE_ACCOUNT_KEY")
    creds_dict = json.loads(creds_dict)
    run_real_time_v2(url=url, univ="大阪大", spread_sheet_ID_conference=spread_sheet_ID_conference, spread_sheet_ID_member=spread_sheet_ID_member, creds_dict=creds_dict)