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

def main():

    starttime = time.time()

    logging.basicConfig(level=logging.DEBUG)

    expire_after = timedelta(hours=1)
    session = requests_cache.CachedSession(
        cache_name='cache', backend='sqlite', expire_after=expire_after
    )
    # set expire_after=None if you don't want cache expiration
    # set expire_after=0 if you don't want to cache queries

    #config = IGServiceConfig()

    # no cache
    ig_service = IGService(
        config.username, config.password, config.api_key, config.acc_type
    )

    # if you want to globally cache queries
    #ig_service = IGService(config.username, config.password, config.api_key, config.acc_type, session)

    ig_service.create_session()

    get_data(ig_service)




def get_data(ig_service):
    Instrument_Data = pd.read_csv("D:/Data/IG_Data/Current_09_03_2020/IG_Liquid_LSE_Common_Shares.csv")
    Instrument_Data.drop("Unnamed: 0", axis=1, inplace=True)

    do_again_list = []

    for index in range(Instrument_Data.index.size):
        # save the data
        try:
            data = get_data_required(Instrument_Data, index, ig_service)
            if data ==  None:
                do_again_list.append(index)
                continue
            temp = data["instrument"].copy()
            temp.update(data["dealingRules"])
            temp.update(data["snapshot"])

            data = temp
            put_in_right_column(data=data, Instrument_Data=Instrument_Data, index=index)


            print("stop")


        except Exception as e:
            print(e)

    while len(do_again_list) > 0:
        try:
            index = do_again_list.pop()
            data = get_data_required(Instrument_Data, index, ig_service)
            if data == None:
                do_again_list.append(index)
                continue
            temp = data["instrument"].copy()
            temp.update(data["dealingRules"])
            temp.update(data["snapshot"])

            data = temp
            put_in_right_column(data=data, Instrument_Data=Instrument_Data, index=index)

            print("stop")


        except Exception as e:
            print(e)

    Instrument_Data.to_csv("D:/Data/IG_Data/Current_09_03_2020/IG_Liquid_LSE_Common_Shares.csv")
    print("stop")


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
    try:
        map_of_data = ig_service.fetch_market_by_epic(epic)
        return map_of_data
    except Exception as e:
        print(e)

def save_to_file(string_of_data):

    try:
        directory = r"D:/Data/IG_Data/Current_09_03_2020/"

        if not os.path.exists(directory):
            os.mkdir(directory)

        file = "instruments.txt"
        filename= directory+file

        file=open(file=filename, mode="a+")
        writiable_string = string_of_data+"\n"
        file.write(writiable_string)
        file.close()
    except Exception as e:
        print("failed to write to file " + str(e))




if __name__ == '__main__':
    main()
