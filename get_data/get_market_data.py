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

from predefined_functions.initialisation import Initialisation

class Get_Market_Data():

    def __init__(self):
        self.initial = Initialisation()
        self.initialise_connection()

    def initialise_connection(self):
        self.ig_service = self.initial.initialise_connection()
        self.ig_service.create_session()

    def get_node_to_node_data(self,node):
        while(True):
            try:
                map_dataframe = self.ig_service.fetch_sub_nodes_by_node(node=node)
                return map_dataframe
            except Exception as e:
                print(e)
                self.initialise_connection()
                # time.sleep(1)

    def get_details_about_epic(self, epic):
        try:
            map_of_data = self.ig_service.fetch_market_by_epic(epic)
            data_string = json.dumps(map_of_data)
            data = json.loads(data_string)

            return data
        except Exception as e:
            print(e)
            self.initialise_connection()
            # time.sleep(1)


