from bs4 import BeautifulSoup
import requests
import pathlib
import sys
import os
import config
import time
from datetime import datetime
from utils import strip_punctuation

FAIL_RUNE_ID = -500

def clean_role(role):
    if(role is None):
        return "Auto Role"
    cleaned_role = strip_punctuation(role.lower().strip())
    if cleaned_role == "middle" or cleaned_role == "mid":
        return "mid"
    elif cleaned_role == "bottom" or cleaned_role== "bot" or cleaned_role == "adc":
        return "bot"
    if cleaned_role == "jungle" or cleaned_role == "jg" or cleaned_role == "jung":
        return "jungle"
    elif cleaned_role == "top":
        return "top"
    elif cleaned_role == "support" or cleaned_role == "supp" or cleaned_role == 'utility':
        return "support"
    elif cleaned_role == "aram":
        return "aram"
    else:
        return None

def dump_rune_page(rune):
    print("[SCRAPER]: \tDUMPING PAGE")
    print("\t\t --- primary ---")
    for primary_rune in rune["primary"]:
        print("\t\t  ", config.RUNE_DATA["id_to_name"][str(primary_rune)]["raw_name"])
    print("\t\t --- secondary ---")
    for secondary_rune in rune["secondary"]:
        print("\t\t  ", config.RUNE_DATA["id_to_name"][str(secondary_rune)]["raw_name"])
    print("\t\t --- fragments ---")
    for fragment in rune["fragment"]:
        print("\t\t  ", config.RUNE_DATA["id_to_name"][str(fragment)]["raw_name"])

# scrapers have to implement and follow this API
class Scraper():
    def __init__(self):
        pass

    def get_best_runes(self, champ, role):
        # returns runes in the following format:
        # runes = {
        #   primary_type:     rune id int
        #   primary:          [rune id int (x4)]
        #   secondary_type:   rune id int
        #   secondary_type:   [rune id int (x2)]
        #   fragment:         [rune id int (x3)]
        #   champ:            str
        #   role:             str
        #   source:           str
        # }
        raise NotImplementedError

# TODO: refactor this entire thing, op.gg website got changed to scraping logic has to change
class OPGGScraper(Scraper):
    def __init__(self):
        super().__init__()
        self._raw_opgg_base_url = "https://www.op.gg/{}"
        self._aram_opgg_base_url = "https://www.op.gg/aram/{}/statistics"

    def get_best_runes(self, champ, role, debug=True, cache_available=True):
        if debug:
            start = time.time()
        runes = self._get_best_runes(champ, clean_role(role), debug, cache_available)
        if debug:
            end = time.time()
            print("[SCRAPER]:\t took {} time to scrape".format(end-start))
        return runes

    def _get_best_runes(self, champ, role, debug, cache_available):
        if cache_available:
            if champ+role in config.RUNE_CACHE:
                entry = config.RUNE_CACHE[champ+role]
                print("[SCRAPER]:\t Cache contains {} in role {}".format(champ, role))
                print("[SCRAPER]:\t Entry expires: {}".format(datetime.utcfromtimestamp(int(config.RUNE_CACHE.get_expiration_time(champ+role))).strftime('%Y-%m-%d %H:%M:%S')))
                dump_rune_page(entry)
                return entry

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        }
        if role == "aram":
            print("[SCRAPER]:\t aram", self._aram_opgg_base_url.format(champ))
            page = requests.get(self._aram_opgg_base_url.format(champ), headers=headers)
        else:
            print("[SCRAPER]:\t not aram", self._raw_opgg_base_url.format("champion/{}/statistics/".format(champ)))
            page = requests.get(self._raw_opgg_base_url.format("champion/{}/statistics/".format(champ)), headers=headers)
        page_soup = BeautifulSoup(page.text, 'html.parser')

        test = page_soup.find_all(class_="perk-page-wrap")
        best_runes_soup = test[0]
        primary_rune_soup = BeautifulSoup(str(best_runes_soup), 'html.parser')

        tree_types = primary_rune_soup.select('img[class*="perk-page__image tip"]')
        best_runes = primary_rune_soup.select('div[class*="perk-page__item--active"]')
        best_fragments = self._get_best_fragments(best_runes_soup)

        if debug:
            assert len(tree_types) == 2, "Incorrect number of rune subtree types (should be 2)"
            assert len(best_runes) == 6, "Incorrect number of runes (should be 6)"
            assert len(best_fragments) == 3, "Incorrect number of fragments (should be 3)"

        runes = {}
        runes["primary_type"], runes["secondary_type"] = self._get_primary_rune_ids(tree_types, "/lol/perkStyle/")
        primary_secondary_rune_ids = self._runes_to_id(best_runes, "/lol/perk/")
        runes["primary"] = primary_secondary_rune_ids[:4]
        runes["secondary"] = primary_secondary_rune_ids[4:]
        runes["fragment"] = self._get_fragment_type_ids(best_fragments, "/lol/perkShard/")
        runes["champ"] = champ
        runes["role"] = role
        runes["source"] = "OPGG"

        if cache_available:
            config.RUNE_CACHE[champ+role] = runes
        
        dump_rune_page(runes)

        return runes

    def _get_best_fragments(self, page_soup):
        fragment_soup = BeautifulSoup(str(page_soup), 'html.parser')
        fragments = fragment_soup.select('img[class*="active tip"]')
        return fragments

    def _get_primary_rune_ids(self, runes, prefix):
        return self._runes_to_id(runes, prefix)

    def _get_rune_type_ids(self, runes, prefix):
        return self._runes_to_id(runes, prefix)

    def _get_fragment_type_ids(self, runes, prefix):
        return self._runes_to_id(runes, prefix)

    def _runes_to_id(self, runes, prefix):
        runes_ids = []
        for rune in runes:
            rune_image_link = BeautifulSoup(str(rune), 'html.parser').find_all("img")
            rune_id = self._convert_image_link_to_rune_id(prefix, rune_image_link[0]["src"])
            runes_ids.append(rune_id)
        return runes_ids

    def _convert_image_link_to_rune_id(self, prefix, image_link):
        idx = image_link.index(prefix)
        if(idx < 0):
            return FAIL_RUNE_ID
        png_idx = image_link.index(".png")
        if(png_idx < 0):
            return FAIL_RUNE_ID
        return int(image_link[idx+len(prefix):png_idx])


class UGGScraper(Scraper):
    def __init__(self):
        super().__init__()
        self._aram_ugg_base_url = "https://u.gg/lol/champions/aram/{}"
        self._query_ugg_url = "https://u.gg/lol/champions/{}/runes?role={}" # champion, role

    def get_best_runes(self, champ, role, debug=True, cache_available=True):
        if debug:
            start = time.time()
        runes = self._get_best_runes(champ, clean_role(role), debug, cache_available)
        if debug:
            end = time.time()
            print("[SCRAPER]:\t took {} time to scrape".format(end-start))
        return runes

    def _get_best_runes(self, champ, role, debug, cache_available):
        if cache_available:
            if champ+role in config.RUNE_CACHE:
                entry = config.RUNE_CACHE[champ+role]
                print("[SCRAPER]:\t Cache contains {} in role {}".format(champ, role))
                print("[SCRAPER]:\t Entry expires: {}".format(datetime.utcfromtimestamp(int(config.RUNE_CACHE.get_expiration_time(champ+role))).strftime('%Y-%m-%d %H:%M:%S')))
                dump_rune_page(entry)
                return entry

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36',
        }
        if role == "aram":
            print("[SCRAPER]:\t aram", self._aram_ugg_base_url.format(champ))
            page = requests.get(self._aram_ugg_base_url.format(champ), headers=headers)
        else:
            print("[SCRAPER]:\t not aram", self._query_ugg_url.format(champ, role))
            page = requests.get(self._query_ugg_url.format(champ, role), headers=headers)
        page_soup = BeautifulSoup(page.text, 'html.parser')

        test = page_soup.find_all(class_="rune-trees-container-2 media-query media-query_MOBILE_LARGE__DESKTOP_LARGE")
        best_runes_soup = test[0]
        primary_rune_soup = BeautifulSoup(str(best_runes_soup), 'html.parser')

        tree_types = primary_rune_soup.select('div[class*="rune-image-container"]')
        best_runes = primary_rune_soup.select('div[class*="perk-active"]')
        best_fragments = self._get_best_fragments(best_runes_soup)

        if debug:
            assert len(tree_types) == 2, "Incorrect number of rune subtree types (should be 2)"
            assert len(best_runes) == 6, "Incorrect number of runes (should be 6)"
            assert len(best_fragments) == 3, "Incorrect number of fragments (should be 3)"

        runes = {}
        runes["primary_type"], runes["secondary_type"] = self._get_rune_types(tree_types)
        primary_secondary_rune_ids = self._get_rune_ids(best_runes)
        runes["primary"] = primary_secondary_rune_ids[:4]
        runes["secondary"] = primary_secondary_rune_ids[4:]
        runes["fragment"] = self._get_fragment_type_ids(best_fragments)
        runes["champ"] = champ
        runes["role"] = role
        runes["source"] = "UGG"

        if cache_available:
            config.RUNE_CACHE[champ+role] = runes
        
        dump_rune_page(runes)

        return runes

    def _get_best_fragments(self, page_soup):
        fragment_soup = BeautifulSoup(str(page_soup), 'html.parser')
        fragments = fragment_soup.select('div[class*="shard-active"]')
        return fragments

    def _get_rune_types(self, rune_type):
        assert len(rune_type) == 2
        rune_ids = []
        for rune in rune_type:
            rune_image_link = BeautifulSoup(str(rune), 'html.parser').find_all("img")
            rune_id = self._convert_image_link_to_rune_id("https://static.u.gg/assets/lol/runes/", rune_image_link[0]["src"])
            rune_ids.append(rune_id)
        return rune_ids

    def _get_rune_ids(self, best_runes):
        rune_ids = []
        for rune in best_runes:
            rune_image_link = BeautifulSoup(str(rune), 'html.parser').find_all("img")
            rune_name = rune_image_link[0]["alt"]
            #cleaned_rune_name = strip_punctuation(rune_name.lower().lstrip("the keystone").lstrip("rune").lstrip())
            cleaned_rune_name = self._parse_rune(rune_name)
            rune_ids.append(config.RUNE_DATA["name_to_id"][cleaned_rune_name])
        return rune_ids

    def _convert_image_link_to_rune_id(self, prefix, image_link):
        idx = image_link.index(prefix)
        if(idx < 0):
            return FAIL_RUNE_ID
        png_idx = image_link.index(".png")
        if(png_idx < 0):
            return FAIL_RUNE_ID
        return int(image_link[idx+len(prefix):png_idx])

    def _get_fragment_type_ids(self, fragments):
        assert len(fragments) == 3
        fragment_ids = []
        for rune in fragments:
            rune_image_link = BeautifulSoup(str(rune), 'html.parser').find_all("img")
            cleaned_fragment = self._parse_fragment(rune_image_link[0]["alt"])
            fragment_id = config.RUNE_DATA["name_to_id"][cleaned_fragment]
            fragment_ids.append(fragment_id)
        return fragment_ids

    def _parse_rune(self, word):
        stopwords = set(["keystone", "rune"])
        cleaned_rune = strip_punctuation(''.join([word for word in word.split(' ') if word.lower() not in stopwords]).lower())
        if (cleaned_rune[:3] == "the"):
            cleaned_rune = cleaned_rune[3:]
        return cleaned_rune

    def _parse_fragment(self, word):
        stopwords = set(["the", "force", "shard"])
        cleaned_fragment = strip_punctuation(''.join([word for word in word.split(' ') if word.lower() not in stopwords]).lower())
        if (cleaned_fragment == 'scalingcdr'):
            return 'cdrscaling'
        if (cleaned_fragment == 'scalingbonushealth'):
            return 'healthscaling'
        if (cleaned_fragment == 'magicresist'):
            return 'magicres'
        return cleaned_fragment