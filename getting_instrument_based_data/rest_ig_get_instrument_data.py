#!/usr/bin/env python
# -*- coding:utf-8 -*-

import pandas as pd

from trading_ig import IGService
from trading_ig.config import config

from datetime import timedelta
import requests_cache
import time
import os
import json


counter = -1
ig_service = None
list_of_instruments = []


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
    map_dataframe = ig_service.fetch_top_level_navigation_nodes()
    # list_of_stringNodes = (map_dataframe["nodes"])["id"].tolist()
    template_recurse(map_dataframe, ig_service)



def template_recurse(map_dataframe, ig_service):
    node_list = map_dataframe["nodes"]["id"].tolist()
    # node_list = ["97601","195235"]
    name_list = map_dataframe["nodes"]["name"].tolist()
    # name_list = ["Indices","Forex"]
    set_nodes = set()

    recurse_overNodes(name_list, node_list, set_nodes, ig_service, [])

def recurse_overNodes(name_list, node_list, set_nodes, ig_service, current_name):
    while len(node_list) != 0 :
        # needs to be -1 as the last item gets popped
        node = node_list[-1]

        if node in set_nodes:
            node_list.pop()
            name_list.pop()
            continue

        current_name.append(name_list[-1])

        set_nodes.add(node)
        map_dataframe = get_node_to_node_data(ig_service, node)

        if (map_dataframe["nodes"].size == 0):

            # save the data
            try:
                epic_id = map_dataframe["markets"]["epic"][0]
                if epic_id == "":
                    raise Exception("No id")
                # save data
                map_data = get_details_about_epic(ig_service, epic_id)
                map_data["instrument"]["location"] = "_".join(current_name)
                # data_string = json.dumps(map_data)

                temp = map_data["instrument"].copy()
                temp.update(map_data["dealingRules"])
                temp.update(map_data["snapshot"])

                global list_of_instruments
                list_of_instruments.append(temp)
                save_to_file(list_of_instruments)

            except Exception as e:
                print(e)

            current_name.pop()

        else:
            temp_names = map_dataframe["nodes"]["name"].tolist()
            temp_id = map_dataframe["nodes"]["id"].tolist()
            recurse_overNodes(temp_names, temp_id, set_nodes, ig_service , current_name)
            current_name.pop()




def get_node_to_node_data(ig_service,node):
    while(True):
        try:

            map_dataframe = ig_service.fetch_sub_nodes_by_node(node=node)
            return map_dataframe
        except Exception as e:
            print(e)
            login()

def get_details_about_epic(ig_service, epic):
    while(True):
        try:
            map_of_data = ig_service.fetch_market_by_epic(epic)
            return map_of_data
        except Exception as e:
            print(e)
            login()
            # time.sleep(2)

def save_to_file(data):

    try:
        directory = r"D:/Stock_Analysis/ig-markets-api-python-library-master/Data/SpreadBetting/"

        if not os.path.exists(directory):
            os.mkdir(directory)

        file = "instruments_new.csv"
        filename= directory+file
        df = pd.DataFrame(data)
        df.to_csv(filename)

    except Exception as e:
        print("failed to write to file " + str(e))


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
