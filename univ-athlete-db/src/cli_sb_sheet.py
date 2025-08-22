import os
import json
from database.db_sheet import *


if __name__ == "__main__":
    #url= "https://jaaf-shiga.com/results/2025/0712pch/shtml/TimeTable.html"
    #url="https://tsriku.stars.ne.jp/htmlR6/240727/shtml/SyozokuPlayer.html"
    #url="https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html"
    #url="http://nagoyatf.xyz/chita2/nans21v/shtml/TimeTable.html"
    url="https://dp17057472.lolipop.jp/HP/0621/shtml/TimeTable.html"
    #TimeTable.htmlじゃないとむり    
    spread_sheet_ID_conference=os.getenv("SPREAD_SHEET_ID_CONFERENCE")
    spread_sheet_ID_member=os.getenv("SPREAD_SHEET_ID_MEMBER")
    spread_sheet_ID_sb=os.getenv("SPREAD_SHEET_ID_SB")
    creds_dict=os.getenv("GOOGLE_ACCOUNT_KEY")
    creds_dict = json.loads(creds_dict)



    member_sb_to_sheet(
        spreadsheet_id_member=spread_sheet_ID_member,
        spreadsheet_id_sb=spread_sheet_ID_sb,
        creds_dict=creds_dict,
        season=2025
    )
    #run_real_time_spa(url=url, univ="大阪大", spread_sheet_ID_conference=spread_sheet_ID_conference, spread_sheet_ID_member=spread_sheet_ID_member, creds_dict=creds_dict)