import sys
import os
import pathlib
import argparse
import json
from utils import initialize_league_location
from rune_selector import RuneSelector
from websocket_driver import websocket_runner
import config

def runeSelectionRunner():
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--champion", help="The champion you are currently playing")
    parser.add_argument("-r", "--role", choices=["mid", "bot", "jungle", "top", "support", "aram"],
                        help="Specify a role you want to play.")
    parser.add_argument("-s", "--scan", type=bool, help="Whether or not to scan process list", default=True)

    parser.add_argument('--dryrun', dest='dryrun', action='store_true', 
        help="Run the rune selector in dry run mode, which just shows you what runes you would populate without populating it. Dry run mode is OFF by default")
    parser.add_argument('--no-dryrun', dest='dryrun', action='store_false', help="Disable dry run functionality")
    parser.set_defaults(dryrun=False)

    parser.add_argument('--cache', dest='cache', action='store_true', help="Use the in cache to quickly get runes of recently played champions. Enabled by default")
    parser.add_argument('--no-cache', dest='cache', action='store_false', help="Disable the cache")
    parser.set_defaults(cache=True)
    args = parser.parse_args()
    
    champ = args.champion
    role = args.role
    should_scan = args.scan
    dry_run = args.dryrun
    use_cache = args.cache
    is_automatic = champ == None and role == None
    print("[CLI]:\t\t champ:", champ)
    print("[CLI]:\t\t role:", role)
    print("[CLI]:\t\t dry run mode:", dry_run)
    print("[CLI]:\t\t use cache:", use_cache)
    print("[CLI]:\t\t automatic:", is_automatic)
    
    if (not dry_run):
        lockfile_data = initialize_league_location(args.scan)
    else:
        lockfile_data = ("", "", "")

    if (not is_automatic):
        rs = RuneSelector(lockfile_data)
        resp = rs.populate_runes(champ, role, dry_run=dry_run, use_cache=use_cache)
    else:
        websocket_runner(lockfile_data, dry_run=dry_run, use_cache=use_cache)

    if (use_cache):
        config.RUNE_CACHE._write_to_disk()

if __name__ == "__main__":
    runeSelectionRunner()