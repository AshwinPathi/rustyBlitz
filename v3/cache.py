from collections import defaultdict, OrderedDict
import time
import pathlib
import sys
import os
from utils import write_dict_to_file, read_json_file, get_next_patch_date
from datetime import datetime


# by default expire each cache item after every Wednesday since patches occur wednesday
def get_cache_expiration_time():
    d = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    next_patch_date = get_next_patch_date(d, 2) # 0 = Monday, 1=Tuesday, 2=Wednesday...
    return int(next_patch_date.timestamp())

# cache that keeps most recent champ runes in memory for quicker access
# ideally writes back to disk when program exits
# maintains a LRU cache of the last max_size champions
# modified from https://github.com/stucchio/Python-LRU-cache
class Cache():
    def __init__(self, path=None, max_size=15, expiration=None):
        self.max_size = max_size
        self.expiration = expiration
        assert self.max_size > 0
        assert self.expiration is None or ((self.expiration is not None) and (self.expiration > 0))

        self._values = {}
        self._expire_times = OrderedDict()
        self._access_times = OrderedDict()

        self.path = path

        if self.path is not None:
            self._read_from_disk()

    def size(self):
        return len(self._values)

    def __contains__(self, key):
        try:
            tmp = self.__getitem__(key)
            return True
        except KeyError as e:
            return False
        #return self._has_key(key)

    def _has_key(self, key):
        return key in self._values

    def __setitem__(self, key, value):
        t = int(time.time())
        self.__delitem__(key)
        self._values[key] = value
        self._access_times[key] = t
        self._expire_times[key] = t + self.expiration if self.expiration is not None else get_cache_expiration_time()
        self._cleanup()

    def __getitem__(self, key):
        t = int(time.time())
        del self._access_times[key]
        self._access_times[key] = t
        self._cleanup()
        return self._values[key]

    def __delitem__(self, key):
        if key in self._values:
            del self._values[key]
            del self._expire_times[key]
            del self._access_times[key]

    def get_expiration_time(self, key):
        if key in self._expire_times:
            return self._expire_times[key]
        return None

    def _cleanup(self):
        t = int(time.time())
        keys_to_delete = []
        next_expire = None
        for k in self._expire_times:
            if self._expire_times[k] < t:
                keys_to_delete.append(k)
            else:
                next_expire = self._expire_times[k]
                break
        while keys_to_delete:
            self.__delitem__(keys_to_delete.pop())

        while (len(self._values) > self.max_size):
            keys_to_delete = []
            for k in self._access_times:
                keys_to_delete.append(k)
                break
            while keys_to_delete:
                self.__delitem__(keys_to_delete.pop())
        if not (next_expire is None):
            return next_expire - t
        else:
            return None

    def _write_to_disk(self):
        print("[CACHE]:\t Writing cache to disk")
        d = {}
        for key, value in self._values.items():
            d[key] = {
                "value" : value, 
                "last_access_time" : self._access_times[key],
                "expire_time" : self._expire_times[key] 
            }
        write_dict_to_file(d, self.path)
    
    def _read_from_disk(self):
        print("[CACHE]:\t Reading cache from disk")
        if pathlib.Path(self.path).is_file():
            d = read_json_file(self.path)
            for key, value in d.items():
                self._values[key] = value["value"]
                self._access_times[key] = value["last_access_time"]
                self._expire_times[key] = value["expire_time"]