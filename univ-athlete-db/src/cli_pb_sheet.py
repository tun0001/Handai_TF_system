import os
import json
from database.db_sheet import *
import pandas as pd

if __name__ == "__main__":
    #url= "https://jaaf-shiga.com/results/2025/0712pch/shtml/TimeTable.html"
    #url="https://tsriku.stars.ne.jp/htmlR6/240727/shtml/SyozokuPlayer.html"
    #url="https://tsriku.stars.ne.jp/htmlR6/240727/shtml/TimeTable.html"
    #url="http://nagoyatf.xyz/chita2/nans21v/shtml/TimeTable.html"
    url="https://dp17057472.lolipop.jp/HP/0621/shtml/TimeTable.html"
    #TimeTable.htmlじゃないとむり    
    spread_sheet_ID_conference=os.getenv("SPREAD_SHEET_ID_CONFERENCE")
    spread_sheet_ID_member=os.getenv("SPREAD_SHEET_ID_MEMBER")
    spread_sheet_ID_pb=os.getenv("SPREAD_SHEET_ID_PB")
    spread_sheet_ID_best = os.getenv('SPREAD_SHEET_ID_BEST')
    spread_sheet_ID_sb=os.getenv("SPREAD_SHEET_ID_SB")
    creds_dict=os.getenv("GOOGLE_ACOUNT_KEY_SHEET_TF")
    creds_dict = json.loads(creds_dict)
    
    # member_best_to_sheet(
    #     spreadsheet_id_member=spread_sheet_ID_member,
    #     spreadsheet_id_best=spread_sheet_ID_best,
    #     creds_dict=creds_dict
    # )
    # df_pb_all=load_sheet(
    #     spreadsheet_id=spread_sheet_ID_pb,
    #     sheet_name="member_pb",
    #     creds_dict=creds_dict
    # )

    # overwrite_sheet(
    #     spreadsheet_id=spread_sheet_ID_member,
    #     sheet_name="部員一覧",
    #     data=df_pb_all,
    #     cred_dict=creds_dict
    # )
    #member_list = load_member_list()
    # for member in member_list:
    #     print(f"Setting member '{member}' as active.")
    #     # 部員をアクティブに設定
    #     time.sleep(1.5)
    #     set_member_active(
    #         spreadsheet_id=spread_sheet_ID_member,
    #         member_name=member,
    #         cred_dict=creds_dict
    #     )
    # set_member_active(
    #     spreadsheet_id=spread_sheet_ID_member,
    #     member_name="大阪大",
    #     creds_dict=creds_dict
    # )
    member_sb_to_sheet(
        spreadsheet_id_member=spread_sheet_ID_member,
        spreadsheet_id_sb=spread_sheet_ID_sb,
        creds_dict=creds_dict,
        season=2025
    )

    member_pb_to_sheet(
        spreadsheet_id_member=spread_sheet_ID_member,
        spreadsheet_id_pb=spread_sheet_ID_pb,
        creds_dict=creds_dict
        )
    


    # member_pb_to_sheet(
    #     spreadsheet_id_member=spread_sheet_ID_member,
    #     spreadsheet_id_pb=spread_sheet_ID_pb,
    #     creds_dict=creds_dict
    #     )
    #run_real_time_spa(url=url, univ="大阪大", spread_sheet_ID_conference=spread_sheet_ID_conference, spread_sheet_ID_member=spread_sheet_ID_member, creds_dict=creds_dict)