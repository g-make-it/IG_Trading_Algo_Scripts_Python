from trading_ig.config import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# if you need to cache to DB your requests
from datetime import timedelta
import requests_cache
from getting_realtime_data.data_retrieval import Data_Retrieval
from sending_orders.order_management import Order_Management
from management_of_position.position_management import Position_Management
from predefined_functions.initialisation import Initialisation
from get_data.get_market_data import Get_Market_Data
import time
from datetime import datetime, timedelta, date
from predefined_functions.defined_functionality import Defined_Functionality
import traceback
import pandas as pd
import sys
import math

# the newest one where you make market order base on price movements 5 or more and try to catch the trend

class Algo0:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.df = Defined_Functionality()




    def run(self):

        while(True):

            try:

                start_time = datetime.now()
                self.check_all_working_orders()
                end_time = datetime.now() - start_time
                print(end_time)

            except Exception as e:
                print(e, "traceback back in custom algo frame work")
                traceback.print_exc()

    def check_all_working_orders(self):
        # check if opening market has passed , if we have a position in it then close all other orders, or if only one of that order remains
        orders = self.df.get_working_orders()
        for epic in orders["epic"].unique():
            self.checking_working_order_is_present_under_epic_and_amend_orders(epic=epic)



    def checking_working_order_is_present_under_epic_and_amend_orders(self, epic):
        # check there are two orders for each epic
        created_order = True
        while(True):
            orders = self.df.get_working_orders_by_epic(epic=epic)
            if orders.index.size == 2:
                directions = orders["direction"].to_list()
                if ("BUY" in directions and "SELL" in directions):
                    data = self.df.get_market_data(epic=epic)

                    if data == None:
                        continue
                    # market is still open
                    map_of_time = data["instrument"]["openingHours"]
                    if map_of_time == None:
                        break
                    single_time = map_of_time["marketTimes"][0]["openTime"]
                    opening_market_time = datetime.strptime(single_time, '%H:%M').time()
                    diff_in_time = datetime.combine(date.today(), opening_market_time) - datetime.now()

                    # if the time is bigger than x second then we can still put orders in place
                    total_seconds = diff_in_time.total_seconds()
                    # -1 seconds
                    if total_seconds < -(0.2):
                        # delete the orders if any are pending
                        break

                    position = self.df.find_open_position_by_epic(epic=epic)
                    if len(position) != 0:
                        break

                    print("market is not open yet and orders are in place nothing needs to be done yet")
                    return created_order

            break

        print("delete orders")
        self.df.cancel_orders_by_epic(epic=epic)
        created_order = False

        return created_order

            
            
        
        

