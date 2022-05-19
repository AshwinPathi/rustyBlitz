import json
import requests
from subprocess import check_output
import pathlib
import sys
import os
import datetime
import time

def write_dict_to_file(d, path):
    with open(path, 'w') as fp:
        json.dump(d, fp, sort_keys=True, indent=4)

def read_json_file(path):
    with open(path, 'r') as fp:
        d = json.load(fp)
    return d

def strip_punctuation(s):
    return ''.join(e for e in s if e.isalnum())

def get_next_patch_date(d, weekday):
    # https://stackoverflow.com/questions/6558535/find-the-date-for-the-first-monday-after-a-given-date

    days_ahead = weekday - d.weekday()
    if days_ahead <= 0: # Target day already happened this week
        days_ahead += 7
    return d + datetime.timedelta(days_ahead)

def find_process_with_name_bash(process_name):
    try:
        out = check_output(["wmic.exe", "process", "where", "caption=\"{}\"".format(process_name), "get", "executablepath"]).decode(sys.stdout.encoding)
        raw_windows_path = out.strip().split("\n")[1].strip()
        posix_path = check_output(["wslpath", "-a", raw_windows_path]).decode(sys.stdout.encoding)
        root_league_dir = pathlib.Path(posix_path.strip()).parent
        return root_league_dir
    except:
        return ""

def get_lockfile_data(lockfile_path):
    with open(lockfile_path, 'r') as f:
        data = f.readline().strip().split(':')
        # port, password, scheme
        return data[2], data[3], data[4]

# manual loading of path from settings json file
def load_settings_from_file():
    curr_dir_path = pathlib.Path(os.path.dirname(os.path.abspath(__file__)))
    data_directory = str(curr_dir_path) + "/data"
    settings_file_loc = data_directory+"/settings.json"
    if not pathlib.Path(settings_file_loc).is_file():
        print("[CLI]:\t Input the install location of your League of Legends Instance.")
        print("[CLI]:\t This can be found by going to task manager --> League of legends --> dropdown --> right click --> properties --> location\n")
        league_path = input("Input your League path here -->\t")
        data = {'league_path':league_path.strip()}
        with open(settings_file_loc, 'w') as fp:
            json.dump(data, fp, sort_keys=True, indent=4)
            print("[CLI]:\t\t Settings file did not exist before, creating new settings file...")
            print("[CLI]:\t\t You can change the path of your League directory at this file: {}".format(settings_file_loc))
        lockfile_data = (get_lockfile_data(league_path+"/lockfile"))
    else:
        print('[CLI]:\t Settings file exists, loading in data from lockfile...')
        with open(settings_file_loc, 'r') as fp:
            data = json.load(fp)
        lockfile_data = (get_lockfile_data(data['league_path'].strip().rstrip("/")+"/lockfile"))
    return lockfile_data

# find lockfile location either automatically or manually
def initialize_league_location(process_scanning=False):
    # attempt to automatically find the league process, else just prompt the user to input the path manually and set the settings file
    # might only work if its run on WSL
    if process_scanning:
        print("[CLI]:\t Scanning process list to find running league instance...")
        auto_find_league_process = str(find_process_with_name_bash("LeagueClientUx.exe")).strip()
        if auto_find_league_process != "":
            print('[CLI]:\t\t Found process successfully')
            return (get_lockfile_data(auto_find_league_process+"/lockfile"))
        else:
            print("[CLI]:\t\t Failed to find a running league instance via process scanning, loading from settings file instead")
            return load_settings_from_file()
    else:
        return load_settings_from_file()
