import os
import json
from cli.real_time_athlete import *


if __name__ == "__main__":
    #url="https://games.athleteranking.com/gamedata.php?gid=ay022025010"
    #url="https://games.athleteranking.com/gamedata.php?gid=aa512025022"
    #TimeTable.htmlじゃないとむり
    url="https://games.athleteranking.com/gamedata.php?gid=ap112025005"
    spread_sheet_ID_conference=os.getenv("SPREAD_SHEET_ID_CONFERENCE")
    spread_sheet_ID_member=os.getenv("SPREAD_SHEET_ID_MEMBER")
    creds_dict=os.getenv("GOOGLE_ACOUNT_KEY_SHEET_TF")
    creds_dict = json.loads(creds_dict)
    announce_discord = True
    run_real_time_athlete(url=url, univ="大阪大", spread_sheet_ID_conference=spread_sheet_ID_conference, spread_sheet_ID_member=spread_sheet_ID_member, creds_dict=creds_dict, announce_discord=announce_discord)