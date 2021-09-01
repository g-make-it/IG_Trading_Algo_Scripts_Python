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
    paths = [

        # "diff_from_morning_minus_afternoon_2020-12-01_2020-12-02_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-02_2020-12-03_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-03_2020-12-04_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-04_2020-12-05_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-05_2020-12-06_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-06_2020-12-07_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-07_2020-12-08_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-08_2020-12-09_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-09_2020-12-10_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-10_2020-12-11_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-11_2020-12-12_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-14_2020-12-15_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-15_2020-12-16_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-16_2020-12-17_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-17_2020-12-18_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-18_2020-12-19_1Min",
        # "diff_from_morning_minus_afternoon_2020-12-21_2020-12-22_1Min",
        # "diff_from_morning_minus_afternoon_" + date + "_" + time_interval
        "diff_from_start_minus_end_" + date + "_" + time_interval
    ]

    for path in paths:
        get_data(path, date, time_interval)



def get_data(file_name, date, time_interval):

    path = r"D:\Stock_Analysis\IG_Data_Fixing\Results\morning_afternoon_diffs\\"+file_name+".csv"
    dataframe = pd.read_csv(path)
    dataframe.rename(columns={"Unnamed: 0": "Datetime"}, inplace=True)
    Instrument_Data = dataframe.set_index("Datetime").T

    histroical_path_location = "D:\Data\IG_Instrument\historical_data\\" + time_interval + "\\" + date

    holding_list = []

    for index in range(Instrument_Data.index.size):
        # save the data
        try:


            name = Instrument_Data.iloc[index].name
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
            temp["diff_score_across_time"] = Instrument_Data[Instrument_Data.columns[0]].iloc[index]


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

            dataframe = pd.DataFrame(holding_list)

            dataframe.to_csv("D:\Stock_Analysis\IG_Data_Fixing\Results\morn_after_diffs_instrument_data_added\\"+file_name+"_instrument_data_added.csv")

        except Exception as e:
            print(e)


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
