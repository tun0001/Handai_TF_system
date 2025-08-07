from database.db_sheet import *
import os
import json
import time
# # process_sheetを呼び出す
# def main():
    
if __name__ == "__main__":
    #url="https://games.athleteranking.com/gamedata.php?gid=ay022025010"
    url="https://games.athleteranking.com/gamedata.php?gid=aa512025022"
    #TimeTable.htmlじゃないとむり    
    #spread_sheet_ID_conference=os.getenv("SPREAD_SHEET_ID_CONFERENCE")
    spread_sheet_ID_member=os.getenv("SPREAD_SHEET_ID_MEMBER")
    spread_sheet_ID_form=os.getenv("SPREAD_SHEET_ID_FORM")
    creds_dict=os.getenv("GOOGLE_ACOUNT_KEY_SHEET_TF")
    creds_dict = json.loads(creds_dict)

    # process_sheetの実行例
    member_list=load_member_list()
    for member in member_list[:3]:
        print(f"Processing member: {member}")
        time.sleep(1.5)  # API制限対策のため1秒待機
        process_sheet(
            spreadsheet_id=spread_sheet_ID_member,
            sheet_name=member,
            creds_dict=creds_dict
        )
    
