import os
import json
from cli.form_change import *
import time


if __name__ == "__main__":
    #url="https://games.athleteranking.com/gamedata.php?gid=ay022025010"
    url="https://games.athleteranking.com/gamedata.php?gid=aa512025022"
    #TimeTable.htmlじゃないとむり   
    creds_dict=os.getenv("GOOGLE_ACOUNT_KEY_SHEET_TF")
    
    creds_dict = json.loads(creds_dict)
    spread_sheet_dict = os.getenv("SPREAD_SHEET_UNIVS")
    print(spread_sheet_dict)
    spread_sheet_dict = json.loads(spread_sheet_dict)
    spread_sheet_dict = pd.DataFrame(spread_sheet_dict).to_dict(orient='list')
    announce_discord = True
    print(spread_sheet_dict)

    spread_sheet_ID_member=spread_sheet_dict["MEMBER"][0]
    spread_sheet_ID_pb=spread_sheet_dict["PB"][0]
    spread_sheet_ID_sb=spread_sheet_dict["SB"][0]
    spread_sheet_ID_member_kobe=spread_sheet_dict["MEMBER"][1]
    spread_sheet_ID_pb_kobe=spread_sheet_dict["PB"][1]
    spread_sheet_ID_sb_kobe=spread_sheet_dict["SB"][1]
    spread_sheet_ID_form_kobe=spread_sheet_dict["FORM"][1]
    spread_sheet_dict_kobe = {
        "UNIV_NAME": [spread_sheet_dict["UNIV_NAME"][1]],
        "CONFERENCE": [spread_sheet_dict["CONFERENCE"][1]],
        "MEMBER": [spread_sheet_dict["MEMBER"][1]],
        "PB": [spread_sheet_dict["PB"][1]],
        "SB": [spread_sheet_dict["SB"][1]],
        "FORM": [spread_sheet_dict["FORM"][1]]
    }
    # #spread_sheet_ID_conference=os.getenv("SPREAD_SHEET_ID_CONFERENCE")
    # spread_sheet_ID_member=os.getenv("SPREAD_SHEET_ID_MEMBER")
    # spread_sheet_ID_form=os.getenv("SPREAD_SHEET_ID_FORM")
    # creds_dict=os.getenv("GOOGLE_ACOUNT_KEY_SHEET_TF")
    # creds_dict = json.loads(creds_dict)

    member_data=load_sheet(spreadsheet_id=spread_sheet_ID_member_kobe, sheet_name="部員一覧", creds_dict=creds_dict)
    member_list=member_data["member_name"].dropna().tolist()
    for member in member_list:
        print(member)
        time.sleep(2)
        process_sheet(
            spreadsheet_id=spread_sheet_ID_member_kobe,
            sheet_name=member,
            univ_name="神戸大",
            creds_dict=creds_dict
        )
    # process_sheet(
    #     spreadsheet_id=spread_sheet_ID_member_kobe,
    #     sheet_name="平尾　瑛",
    #     univ_name="神戸大",
    #     creds_dict=creds_dict
    # )
    # process_sheet(
    #     spreadsheet_id=spread_sheet_ID_member_kobe,
    #     sheet_name="反保　美雅",
    #     univ_name="神戸大",
    #     creds_dict=creds_dict
    # )
    

    # # announce_discord = False
    # run_form_change(spread_sheet_ID_dict=spread_sheet_dict_kobe, creds_dict=creds_dict)