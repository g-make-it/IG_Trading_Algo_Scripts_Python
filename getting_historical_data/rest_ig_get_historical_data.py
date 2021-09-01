#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
IG Markets REST API sample with Python
2015 FemtoTrader
"""

from trading_ig import IGService
from trading_ig.config import config
import logging
import pandas as pd
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# if you need to cache to DB your requests
from datetime import datetime, timedelta
import requests_cache
import math
import numpy as np
import time

counter = -1


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


def main():
    logging.basicConfig(level=logging.DEBUG)
    #
    # expire_after = timedelta(hours=1)
    # session = requests_cache.CachedSession(
    #     cache_name='cache', backend='sqlite', expire_after=expire_after
    # )
    # # set expire_after=None if you don't want cache expiration
    # # set expire_after=0 if you don't want to cache queries
    #
    # #config = IGServiceConfig()
    #
    # # no cache
    # ig_service = IGService(
    #     config.username, config.password, config.api_key, config.acc_type
    # )
    #
    # # if you want to globally cache queries
    # #ig_service = IGService(config.username, config.password, config.api_key, config.acc_type, session)
    #
    # ig_service.create_session()

    # accounts = ig_service.fetch_accounts()
    # print("accounts:\n%s" % accounts)

    # account_info = ig_service.switch_account(config.acc_number, False)
    # print(account_info)

    # open_positions = ig_service.fetch_open_positions()
    # print("open_positions:\n%s" % open_positions)

    ig_service = login()

    print("")

    # working_orders = ig_service.fetch_working_orders()
    # print("working_orders:\n%s" % working_orders)

    print("")

    # strimming data ----------------------
    # instrument_data = pd.read_csv("D:/Data/IG_Data/instruments.csv")
    # instrument_data.drop("Unnamed: 0", axis=1, inplace=True)
    #
    # instrument_data["average"] = (instrument_data["bid"] + instrument_data["offer"]) / 2
    # instrument_data["margin_in_pounds_required"] = instrument_data["average"] * 0.5 * instrument_data["margin"]
    #
    # # Cheap_Shares = instrument_data[(instrument_data["margin_in_pounds_required"] < 2)
    # #                                & (instrument_data["location"].str.contains("Shares - ")
    # #                                   & (instrument_data["margin_in_pounds_required"] > 1))]
    #
    # # Cheap_Shares = instrument_data[(instrument_data["margin_in_pounds_required"] < 10)
    # #                                & (instrument_data["location"].str.contains("Shares - ")
    # #                                   & (instrument_data["average"] > 1))]
    #
    # # gets rid of small averages
    # # gets rid of small averages
    # list_of_items_to_remove = []
    # for index in range(instrument_data.index.size):
    #     #     print(instrument_data["average"].iloc[index])
    #
    #     if (instrument_data["average"].iloc[index] < 0.5) or (math.isnan(instrument_data["average"].iloc[index]) or (
    #     instrument_data["location"].str.contains("Option").iloc[index])):
    #         list_of_items_to_remove.append(instrument_data.index[index])
    #
    # for item in list_of_items_to_remove:
    #     instrument_data.drop(index=item, axis=0, inplace=True)
    # strimming data ----------------------

    instrument = pd.read_csv("D:/Stock_Analysis/ig-markets-api-python-library-master/Data/SpreadBetting/Instruments.csv")
    instrument.drop("Unnamed: 0", axis=1, inplace=True)

    list_of_epics = instrument["epic"].to_list()
    list_names = instrument["name"].to_list()


    resolution = '5Min'


    for date_counter in range(1):

        # start_date = "2020-11-%02d" % date_counter
        # end_date = "2020-11-%02d" % (date_counter + 1)
        start_date = "2021-05-10"
        end_date = "2021-05-12"

        for index in range(len(list_of_epics)):

            epic = list_of_epics[index]
            name = list_names[index]
            # epic = 'CS.D.EURUSD.MINI.IP'
            # epic = 'IX.D.ASX.IFM.IP'  # US (SPY) - mini

            # resolution = 'D'
            # see from pandas.tseries.frequencies import to_offset
            # resolution = 'H'
            # resolution = '1Min'

            num_points = 9000
            print(name)
            response = None

            while (True):
                try:
                    # response = ig_service.fetch_historical_prices_by_epic_and_num_points(
                    #     epic, resolution, num_points
                    # )
                    response = ig_service.fetch_historical_prices_by_epic_and_date_range(
                        epic=epic, resolution=resolution, start_date=start_date, end_date=end_date
                    )
                    break
                except Exception as e:
                    print(e, " there was not data available")

                    if (str(e) == "error.public-api.exceeded-account-historical-data-allowance") or (str(e) == "error.security.client-token-invalid") or (str(e) == "error.security.generic") or (str(e) == "error.public-api.exceeded-api-key-allowance"):
                        ig_service = login()
                        continue
                    else:
                        print(e, "exception not know")

                    break

            if response == None:
                continue

            print(response)
            print("\n \n")
            data_frame_of_prices = response["prices"]
            save_to_file(data_frame_of_prices, name,resolution, start_date, end_date,epic)




def save_to_file(dataframe, name, resolution, start_date, end_date, epic):

    try:
        name = name.replace("/", "-")
        directory = r"D:/Data/IG_Instrument/historical_data/"+resolution+"/"+start_date+"_"+end_date
        if not os.path.exists(directory):
            try:
                semi_directory = r"D:/Data/IG_Instrument/historical_data/"+resolution
                os.mkdir(semi_directory)
            except Exception as e:
                print(e)

            os.mkdir(directory)

        full_path = directory+"/"+name+"_"+resolution+"_ID_"+epic+"_ID_.csv"

        dataframe.to_csv(full_path)
    except Exception as e:
        print("failed to write to file " + str(e))



def increment_api_key():
    key = ""
    global counter
    flag = True
    while (flag):
        try:
            counter += 1
            # has 12000 api keys
            fp = open("D:/Stock_Analysis/ig-markets-api-python-library-master/generate_api_keys/IG_api_keys_raw.txt")
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
