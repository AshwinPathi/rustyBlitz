import ssl
import asyncio
import websockets
import json
from rune_selector import RuneSelector
from config import CHAMP_DATA

SUBSCRIBE = 5

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

EVERYTHING_EVENT = json.dumps([SUBSCRIBE, "OnJsonApiEvent"])
SUB_CHAMP_SELECT_SESSION_EVENT = json.dumps([SUBSCRIBE, "OnJsonApiEvent_lol-champ-select_v1_session"])
CHAMP_SELECT_CURRENT_CHAMPION_EVENT = json.dumps([SUBSCRIBE, "OnJsonApiEvent_lol-champ-select_v1_current-champion"])

def get_champ_name_from_id(champ_id):
    return CHAMP_DATA["id_to_name"][str(champ_id)]["alias"]

def get_data_from_response(response):
    player_pos = response[2]["data"]["localPlayerCellId"]%5
    if(player_pos != -1):
        phase = response[2]["data"]["timer"]["phase"]
        is_final_pick = False
        if(phase == "FINALIZATION" or len(response[2]["data"]["actions"]) == 0):
            is_final_pick = True
        else:
            is_final_pick = response[2]["data"]["actions"][0][player_pos]["completed"]

        champ_id = response[2]["data"]["myTeam"][player_pos]["championId"]
        assigned_role = response[2]["data"]["myTeam"][player_pos]["assignedPosition"]
    
    return player_pos, champ_id, assigned_role, phase, is_final_pick

def websocket_runner(lockfile_data, dry_run=False, use_cache=True):
    password = lockfile_data[1]
    port = lockfile_data[0]
    url = "wss://{}:{}@127.0.0.1:{}/".format('riot', password, str(port))
    print("[WEBSOCKET]:\t  Listening for champ select events")
    rs = RuneSelector(lockfile_data)
    gamemode = None

    async def run():
        async with websockets.connect(url, ssl=ssl_context) as websocket:
            await websocket.send(EVERYTHING_EVENT)
            prev_champ_role = ("", "")
            while(True):
                try:
                    resp = await websocket.recv()
                    if(resp.strip() == ""):
                        continue
                    response = json.loads(resp)
                    if (response is None or not isinstance(response, list)):
                        continue
                    if (len(response) < 3):
                        continue
                    if ('data' in response[2] and isinstance(response[2]['data'], dict) and 'gameMode' in response[2]['data'].get('lol', [])):
                        gamemode = response[2]['data']['lol']['gameMode'].lower()
                    if ('uri' in response[2] and isinstance(response[2]['uri'], str) and response[2]['uri'] == '/lol-champ-select/v1/session'):
                        if(response[2]['eventType'] == "Update"):
                            print(response)
                            print()
                            player_pos, champ_id, assigned_role, phase, is_final_pick = get_data_from_response(response)
                            if (champ_id == 0):
                                continue
                            if (gamemode == "aram"):
                                assigned_role = gamemode
                            champ_name = get_champ_name_from_id(champ_id)
                            if(assigned_role is not None and assigned_role.strip() != "" and is_final_pick == True and prev_champ_role != (champ_name, assigned_role)):
                                print("[WEBSOCKET]:\t Finalized pick:\n\t\t\tChamp: {}\n\t\t\tRole: {}".format(champ_name, assigned_role))
                                prev_champ_role = (champ_name, assigned_role)
                                resp = rs.populate_runes(champ_name, assigned_role, dry_run=dry_run, use_cache=use_cache)

                except json.decoder.JSONDecodeError as e:
                    pass

    asyncio.get_event_loop().run_until_complete(run())
    asyncio.get_event_loop().run_forever()