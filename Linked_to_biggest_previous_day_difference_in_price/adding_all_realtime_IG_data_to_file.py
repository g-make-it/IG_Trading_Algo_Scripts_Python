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


counter = -1
ig_service = None



def login():
    expire_after = timedelta(hours=1)
    session = requests_cache.CachedSession(
        cache_name='cache', backend='sqlite', expire_after=expire_after
    )
    api_key = increment_api_key()

    global ig_service

    # no cache
    ig_service = IGService(
        config.username, config.password, api_key, config.acc_type
    )
    ig_service.create_session()



def main():

    login()

    date = "2020-12-10_2021-02-10"
    # date = "2020-09-10_2020-12-10"
    time_interval = "5Min"
    get_data(date, time_interval)



def get_data(date, time_interval):

    histroical_path_location = "D:\Data\IG_Instrument\historical_data\\" + time_interval + "\\" + date


    holding_list = []

    files = os.listdir(histroical_path_location)

    for f in files:
        # save the data
        try:
            name = f
            epic = name.split("_ID_")[1]
            data = get_details_about_epic(epic)
            # get the magin requirement from here ---------------------------------------------------------------------------------------------
            data = json.loads(json.dumps(data))
            #
            # map_of_items =  {
            #     "value" : data["instrument"]["marginFactor"],
            #     "unit" : data["instrument"]["marginFactorUnit"]}
            #
            # difference_required = map_of_items["value"]
            # # otherwise the unit is POINTS
            # if map_of_items["unit"] == "PERCENTAGE":
            #     difference_required = difference_required / 100
            #
            # difference_required * current_price
            temp = data["instrument"].copy()
            temp.update(data["dealingRules"])
            temp.update(data["snapshot"])
            temp["file_name"] = name


            whole_file_location = os.path.join(histroical_path_location, name)
            historical_data = pd.read_csv(whole_file_location, header=[0, 1], index_col=0)
            historical_data.index = pd.to_datetime(historical_data.index)

            bid = historical_data.iloc[0]["bid"]["Close"]
            ask = historical_data.iloc[0]["ask"]["Close"]
            spread = ask - bid

            temp["spread"] = spread
            temp["average"] = (bid + ask) / 2.0
            temp["diff_high-low"] = historical_data["bid"]["High"].max() - historical_data["bid"]["Low"].min()
            # could divide by zero and cause an error but would be caught by try and except clause
            temp["percent_spread-hl"] = (temp["spread"] / temp["diff_high-low"] * 100)


            holding_list.append(temp)



        except Exception as e:
            print(e)
    dataframe = pd.DataFrame(holding_list)

    dataframe.to_csv("D:\Stock_Analysis\IG_Data_Fixing\Results\All_instrument_data_added.csv")

def get_details_about_epic(epic):
    global ig_service
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
            # has 12000 api keys
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
