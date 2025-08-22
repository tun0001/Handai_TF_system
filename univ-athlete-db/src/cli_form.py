import os
import json
from cli.form_change import *


if __name__ == "__main__":
    #url="https://games.athleteranking.com/gamedata.php?gid=ay022025010"
    url="https://games.athleteranking.com/gamedata.php?gid=aa512025022"
    #TimeTable.htmlじゃないとむり    
    #spread_sheet_ID_conference=os.getenv("SPREAD_SHEET_ID_CONFERENCE")
    spread_sheet_ID_member=os.getenv("SPREAD_SHEET_ID_MEMBER")
    spread_sheet_ID_form=os.getenv("SPREAD_SHEET_ID_FORM")
    creds_dict=os.getenv("GOOGLE_ACOUNT_KEY_SHEET_TF")
    creds_dict = json.loads(creds_dict)

    process_sheet(
        spreadsheet_id=spread_sheet_ID_member,
        sheet_name="松井　天",
        creds_dict=creds_dict
    )

    # announce_discord = False
    #run_form_change(spread_sheet_ID_member=spread_sheet_ID_member, spread_sheet_ID_form=spread_sheet_ID_form, creds_dict=creds_dict)