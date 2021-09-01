from trading_ig import IGService
from trading_ig.config import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# if you need to cache to DB your requests
from datetime import timedelta
import requests_cache


class Initialisation():
    def __init__(self):
        logging.basicConfig(level=logging.INFO)


        self.counter = -1
        self.initialise_connection()

    def initialise_connection(self):

        key = self.increment_api_key()

        # expire_after = timedelta(hours=1)
        # session = requests_cache.CachedSession(
        #     cache_name='cache', backend='sqlite', expire_after=expire_after
        # )
        # set expire_after=None if you don't want cache expiration
        # set expire_after=0 if you don't want to cache queries

        # no cache
        ig_service = IGService(
            config.username, config.password, key, config.acc_type
        )
        # if you want to globally cache queries
        # ig_service = IGService(config.username, config.password, config.api_key, config.acc_type, session)
        return ig_service
    # make sure once the object is received to the place were it is needed you createSession() to initialise the session

    def increment_api_key(self):
        key = ""
        while (True):
            try:
                self.counter += 1
                # has 12000 api keys
                fp = open("D:\Stock_Analysis\ig-markets-api-python-library-master\generate_api_keys\IG_api_keys_raw.txt")
                for i, line in enumerate(fp):
                    if i == self.counter:
                        key = line.split("\n")[0]
                        fp.close()
                        return key
                raise Exception("file has surpassed the last api key")
            except:
                fp.close()
                self.counter = -1
