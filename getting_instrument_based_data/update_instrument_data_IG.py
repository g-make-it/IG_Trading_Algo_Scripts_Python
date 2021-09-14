#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
IG Markets REST API sample with Python
2015 FemtoTrader
"""

from trading_ig import IGService
from trading_ig.config import config
import logging
# format to
# # from folder.file import class
# from getting_instrument_based_data.navigate_tree import NavigateTree

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# if you need to cache to DB your requests
from datetime import timedelta
import requests_cache
import time
import os
import json
import pandas as pd
pd.options.mode.chained_assignment = None  # default='warn'


def main():
    ig_service = login()

    get_data(ig_service)

def login():
    expire_after = timedelta(hours=1)
    session = requests_cache.CachedSession(
        cache_name='cache', backend='sqlite', expire_after=expire_after
    )
    api_key = increment_api_key()

    # no cache
    ig_service = IGService(
        config.username, config.password, api_key, config.acc_type
    )
    ig_service.create_session()

    return ig_service



def get_data(ig_service):
    Instrument_Data = pd.read_csv("D:\Stock_Analysis\ig-markets-api-python-library-master\Data\SpreadBetting\instruments_new.csv")
    Instrument_Data.drop("Unnamed: 0", axis=1, inplace=True)

    for index in range(Instrument_Data.index.size):
        # save the data
        try:
            data = get_data_required(Instrument_Data, index, ig_service)
            # if data ==  None:
            #     continue
            temp = data["instrument"].copy()
            temp.update(data["dealingRules"])
            temp.update(data["snapshot"])

            data = temp
            put_in_right_column(data=data, Instrument_Data=Instrument_Data, index=index)

            Instrument_Data.to_csv("D:\Stock_Analysis\ig-markets-api-python-library-master\Data\SpreadBetting\instruments_new_updated.csv")

        except Exception as e:
            print(e)


    print("finished")


def get_data_required(Instrument_Data, index, ig_service):
    try:
        row = Instrument_Data.iloc[index]
        epic_id = row["epic"]
        # save data
        map_data = get_details_about_epic(ig_service, epic_id)
        data_string = json.dumps(map_data)
        data = json.loads(data_string)
        return data
    except Exception as e:
        print(e)
        return None


def put_in_right_column(data, Instrument_Data, index):
    object_df = Instrument_Data.loc[index]
    for key in data.keys():
        object_df[key] = data[key]
    Instrument_Data.loc[index] = object_df
    print("stop")


def get_details_about_epic(ig_service, epic):
    while(True):
        try:
            map_of_data = ig_service.fetch_market_by_epic(epic)
            return map_of_data
        except Exception as e:
            print(e)
            login()


def increment_api_key():
    key = ""
    global counter
    flag = True
    while (flag):
        try:
            counter += 1
            fp = open("D:\Stock_Analysis\ig-markets-api-python-library-master\generate_api_keys\IG_api_keys_raw.txt")
            for i, line in enumerate(fp):
                if i == counter:
                    key = line.split("\n")[0]
                    flag = False
                    break

            fp.close()
        except:
            counter = -1

    return key




if __name__ == '__main__':
    main()
