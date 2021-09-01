import time
import sys
import traceback
import logging
import math

from trading_ig import (IGService, IGStreamService)
from trading_ig.config import config
from trading_ig.lightstreamer import Subscription
from predefined_functions.initialisation import Initialisation

class Data_Retrieval_Historical:
    def __init__(self):
        self.data_map = {}
        self.ig_service = None
        self.initial = Initialisation()
        self.initialise_connection()

    def initialise_connection(self):
        while(True):
            try:
                self.ig_service = self.initial.initialise_connection()
                self.ig_service.create_session()
                return
            except Exception as e:
                print(e)



    def get_historical_data_based_date_range(self, epic, resolution, start_date, end_date):
        # start_date="2020-04-24"
        # end_date = "2020-05-01"
        response = None
        while (True):
            try:
                response = self.ig_service.fetch_historical_prices_by_epic_and_date_range(epic=epic, resolution=resolution, start_date=start_date, end_date=end_date)
                break
            except Exception as e:
                # print(e, " there was not data available")
                if (str(e) == "error.public-api.exceeded-account-historical-data-allowance") or (
                        str(e) == "error.security.generic") or (
                        str(e) == "error.public-api.exceeded-api-key-allowance"):
                    self.initialise_connection()
                    continue

                return None

        # print(response)
        data_frame_of_prices = response["prices"]

        return data_frame_of_prices

    def get_historical_data_based_num_points(self, epic, resolution, num_points):
        response = None
        while (True):
            try:
                response = self.ig_service.fetch_historical_prices_by_epic_and_num_points( epic, resolution, num_points)
                break
            except Exception as e:
                # print(e, " there was not data available")
                if (str(e) == "error.public-api.exceeded-account-historical-data-allowance") or (
                        str(e) == "error.security.generic") or (
                        str(e) == "error.public-api.exceeded-api-key-allowance"):
                    self.initialise_connection()
                    continue

                return None

        # print(response)
        data_frame_of_prices = response["prices"]

        return data_frame_of_prices