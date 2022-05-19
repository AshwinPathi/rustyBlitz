import requests
from requests.auth import HTTPBasicAuth

from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Manages the actual posting/getting of optimal rune data to the league client
class ClientInterface():
    def __init__(self, port, password, scheme):
        self.port, self.password, self.scheme = port, password, scheme
        self.base_url = "{}://127.0.0.1:{}".format(self.scheme, str(self.port))
        self.auth_header = HTTPBasicAuth('riot', self.password)

    def post_rune_page_data(self, best_runes):
        post_data, page_id = self._form_request(best_runes)
        client_post_url = (self.base_url+"{}").format("/lol-perks/v1/pages/{}".format(str(page_id)))
        r = requests.put(client_post_url, verify=False, auth=self.auth_header, json=post_data)
        return r

    def _form_request(self, best_runes):
        page_id = self._get_current_rune_page_data()["id"]
        data = {}
        data["name"] =  best_runes["source"] + ": " + best_runes["champ"] +" "+ best_runes["role"]
        data["primaryStyleId"] = best_runes["primary_type"]
        data["subStyleId"] = best_runes["secondary_type"]
        all_perks = best_runes["primary"][:]
        all_perks.extend(best_runes["secondary"])
        all_perks.extend(best_runes["fragment"])
        data["selectedPerkIds"] = all_perks
        data["current"] = True
        data["isActive"] = True
        return data, page_id

    def _get_current_rune_page_data(self):
        # endpoint to edit rune pages: /lol-perks/v1/pages/{id}
        formed_url = (self.base_url+"{}").format("/lol-perks/v1/currentpage")
        r = requests.get(formed_url, verify=False, auth=self.auth_header)
        return r.json()