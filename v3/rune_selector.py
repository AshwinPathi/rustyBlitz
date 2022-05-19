from client_interface import ClientInterface
from scraper import OPGGScraper, UGGScraper
import config

class RuneSelector():
    def __init__(self, lockfile_data):
        # support multiple scrapers in the future
        self.scraper = None
        self.client = ClientInterface(*lockfile_data)

    def populate_runes(self, champ, role, backend="ugg", dry_run=False, use_cache=True):
        self.scraper = self._backend_resolver(backend)
        assert self.scraper is not None, "Could not resolve scraper backend"
        rune_data = self.scraper.get_best_runes(champ, role, cache_available=use_cache)
        resp = None
        if not dry_run:
            resp = self.client.post_rune_page_data(rune_data)
            assert resp.status_code == 201
        return resp

    def _backend_resolver(self, backend_name):
        if (backend_name == "ugg"):
            return UGGScraper()
        elif (backend_name == "opgg"):
            return OPGGScraper()
        else:
            return None