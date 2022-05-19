from scraper import OPGGScraper, UGGScraper
from pprint import pprint
import time
import pathlib
import sys
import os
import config
from utils import get_next_patch_date, find_process_with_name_bash
from datetime import datetime
from cache import Cache

curr_dir_path = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
data_directory = str(curr_dir_path) + "/data"

def testScraper():
    cache_on = False
    s = UGGScraper()
    #res = s.get_best_runes("yone", "top", cache_available=True)
    #res = s.get_best_runes("vi", "jungle", cache_available=True)
    res = s.get_best_runes("jinx", "bot", debug=True, cache_available=cache_on)
    pprint(config.RUNE_CACHE._expire_times)
    pprint(config.RUNE_CACHE._access_times)

    if cache_on:
        config.RUNE_CACHE._write_to_disk()

def testNextWeekday():
    d = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    next_monday = get_next_patch_date(d, 2) # 0 = Monday, 1=Tuesday, 2=Wednesday...
    print(int(next_monday.timestamp()))

def testProcessScaning():
    client_proc = "LeagueClientUx.exe"
    print(find_process_with_name_bash(client_proc))

def testCache():
    c = Cache(expiration = 19)
    c["test"] = 1
    time.sleep(2)
    print("test" in c)


if __name__ == "__main__":
    testScraper()