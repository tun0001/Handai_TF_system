import os
import json
from cli.real_time_spa import *


if __name__ == "__main__":
    #url= "https://jaaf-shiga.com/results/2025/0712pch/shtml/TimeTable.html"
    #url="https://tsriku.stars.ne.jp/htmlR6/240727/shtml/SyozokuPlayer.html"
    #url="https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html"
    url="http://nagoyatf.xyz/chita2/nans21v/shtml/TimeTable.html"
    #TimeTable.htmlじゃないとむり    
    spread_sheet_ID_conference=os.getenv("SPREAD_SHEET_ID_CONFERENCE")
    spread_sheet_ID_member=os.getenv("SPREAD_SHEET_ID_MEMBER")
    creds_dict=os.getenv("GOOGLE_ACCOUNT_KEY")
    creds_dict = json.loads(creds_dict)
    run_real_time_spa(url=url, univ="大阪大", spread_sheet_ID_conference=spread_sheet_ID_conference, spread_sheet_ID_member=spread_sheet_ID_member, creds_dict=creds_dict)