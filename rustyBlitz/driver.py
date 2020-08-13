from rune_selector import RuneSelector
import pprint
pp = pprint.PrettyPrinter(depth=6)
import sys
from scraper import OPGGScraper


def fully_manual_rune_select(lockfile_data, champ, role, no_confirm=False):
    if(role == ""):
        role = None
    rs = RuneSelector(*lockfile_data)
    if(role == None):
        print("automatically selecting best runes for: {}".format(champ))
    else:
        print("New rune page for {} @ {}".format(champ, role))
    scraper = OPGGScraper()
    best_runes = scraper.get_best_runes(champ, role_override=role)
    if best_runes == None:
        print("Failed to get runes")
        return
    post_data, page_id = rs.form_request(best_runes)

    if not no_confirm:
        agree = input("Make rune page changes to this rune page (yes/y to confirm)?\t")
        if agree.strip().lower() == "y" or agree.strip().lower() == "yes":
            print("Setting up new rune page...")
            r = rs.post_rune_page_data(post_data, page_id)
        else:
            print('Selection not confirmed')
    else:
        print("Setting up new rune page...")
        r = rs.post_rune_page_data(post_data, page_id)
        print("New rune page set.")