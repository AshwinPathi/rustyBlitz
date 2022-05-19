import pathlib
import sys
import os
import cache
from utils import write_dict_to_file, read_json_file, strip_punctuation
import requests
import datetime

print("[CONFIG]:\t --- IMPORTED CONFIG ---")

# for champ id --> name
# https://ddragon.leagueoflegends.com/cdn/11.23.1/data/en_US/champion.json

# for rune id --> name
# https://raw.communitydragon.org/latest/plugins/rcp-be-lol-game-data/global/default/v1/perks.json

# get latest patch version
# http://ddragon.leagueoflegends.com/api/versions.json

curr_dir_path = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
data_directory = str(curr_dir_path) + "/data"
sys.path.append(data_directory)

def get_latest_patch_version():
    url = "http://ddragon.leagueoflegends.com/api/versions.json"
    r = requests.get(url).json()
    return r[0]

CURR_PATCH_CDRAGON = "latest"
CURR_PATCH_DDRAGON = get_latest_patch_version()
print("[CONFIG]:\t CDRAGON Patch Value: ", CURR_PATCH_CDRAGON)
print("[CONFIG]:\t DDRAGON Patch Value: ", CURR_PATCH_DDRAGON)

def load_champ_data(champ_data_file_name="/champ_data.json"):
    print("[CONFIG]:\t Loading champ data")
    champ_data_file_path = data_directory+"/"+champ_data_file_name
    champ_data_file = pathlib.Path(champ_data_file_path)
    if champ_data_file.is_file():
        print("[CONFIG]:\t\t Attempting to load champ data from DISK")
        champ_data_dict = read_json_file(champ_data_file_path)
        if "patch" in champ_data_dict and champ_data_dict["patch"] == CURR_PATCH_DDRAGON:
            print("[CONFIG]:\t\t\t Loading champ data from DISK")
            return champ_data_dict

    print("[CONFIG]:\t\t Loading champ data from CDN")
    champ_data_dict = {
        "patch": CURR_PATCH_DDRAGON,
        "id_to_name": {},
        "name_to_id": {}
    }
    url = "https://ddragon.leagueoflegends.com/cdn/{}/data/en_US/champion.json".format(CURR_PATCH_DDRAGON)
    r = requests.get(url).json()
    for champ_name, champ_data in r["data"].items():
        champ_name_cleaned = champ_name.lower() # this has champion aliases like "monkeyking" for wukong
        champ_ingame_name = strip_punctuation(champ_data["name"]).lower()  # has in game champion names
        champ_id = champ_data["key"]

        champ_data_dict["id_to_name"][champ_id] = {"name": champ_name_cleaned, "alias": champ_ingame_name}
        champ_data_dict["name_to_id"][champ_ingame_name] = champ_id

    print("[CONFIG]:\t\t file path", champ_data_file_path)
    write_dict_to_file(champ_data_dict, champ_data_file_path)
    return champ_data_dict

def load_rune_data(rune_data_file_name="/rune_data.json"):
    print("[CONFIG]:\t Loading rune data")
    rune_data_file_path = data_directory+"/"+rune_data_file_name
    rune_data_file = pathlib.Path(rune_data_file_path)
    if rune_data_file.is_file():
        print("[CONFIG]:\t\t Attempting to load rune data from DISK")
        rune_data_dict = read_json_file(rune_data_file_path)
        if "patch" in rune_data_dict and rune_data_dict["patch"] == CURR_PATCH_DDRAGON:
            print("[CONFIG]:\t\t\t Loading rune data from DISK")
            return rune_data_dict

    print("[CONFIG]:\t\t Loading rune data from CDN")
    rune_data_dict = {
        "patch": CURR_PATCH_DDRAGON,
        "id_to_name": {},
        "name_to_id": {}
    }
    url = "https://raw.communitydragon.org/{}/plugins/rcp-be-lol-game-data/global/default/v1/perks.json".format(CURR_PATCH_CDRAGON)
    r = requests.get(url).json()

    for rune in r:
        item_id = rune['id']
        cleaned_name = strip_punctuation(rune['name']).lower()
        if (item_id not in rune_data_dict['id_to_name']):
            rune_data_dict['id_to_name'][item_id] = {}
        rune_data_dict['id_to_name'][item_id]["cleaned_name"] = cleaned_name
        rune_data_dict['id_to_name'][item_id]["raw_name"] = rune['name']
        rune_data_dict['name_to_id'][cleaned_name] = item_id

    print("[CONFIG]:\t\t file path", rune_data_file_path)
    write_dict_to_file(rune_data_dict, rune_data_file_path)
    return rune_data_dict

RUNE_CACHE = cache.Cache(path=data_directory+"/cache.json")
CHAMP_DATA = load_champ_data()
RUNE_DATA = load_rune_data()
ROLES = ["top", "jungle", "mid", "bot", "support", "aram"]
BACKENDS = ["u.gg", "op.gg"]