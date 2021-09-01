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
        self.map_epic_data_minute={}
        # this way we can record the time the data was take for a particular instrument
        self.first_timestamp = {}

        self.high = None
        self.low = None
        self.time_interval = 5
        # self.dataframe = self.setup_dataframe()

        self.number_orders = 40


    def setup(self):
        self.df.update_stop_level_bands()


    def run(self):

        while(True):

            try:
                # setup is running in another program
                # self.setup()
                start_time = datetime.now()
                self.check_all_working_orders()
                details_required_to_create_orders = self.signal_generation()
                self.create_orders(required_order_details = details_required_to_create_orders)

                # for epic in self.map_epic_data_minute.keys():
                end_time = datetime.now() - start_time
                print(end_time)

            except Exception as e:
                print(e, "   error in the looping for the defined_functionality")
                traceback.print_exc()

    def check_all_working_orders(self):
        # check if opening market has passed , if we have a position in it then close all other orders, or if only one of that order remains
        orders = self.df.get_working_orders()
        for epic in orders["epic"].unique():
            self.checking_working_order_is_present_under_epic_and_amend_orders(epic=epic)


    # all sessions mean the market opens at 9 am
    def create_orders(self, required_order_details):

        if not isinstance(required_order_details, pd.core.frame.DataFrame):
            return

        if required_order_details.index.size == 0:
            return

        map_of_orders = None

        for index in range(required_order_details.index.size):

            orders = self.df.get_working_orders()
            if (orders.index.size) >= self.number_orders:
                # print("order limit met")
                return map_of_orders


            single_detail = required_order_details.iloc[index]
            epic = single_detail["epic"]

            position = self.df.find_open_position_by_epic(epic=epic)

            if len(position) != 0:
                # make sure you do no have order under a position
                self.df.cancel_orders_by_epic(epic=epic)
                print(position[0])
                continue

            # as we are placing a buy above the quotes as we are betting
            # force open == True here means when you place a trade of the opposite type your position will not close when the price meets it, another position will open
            order_buy = self.df.create_working_order(epic=epic, direction="BUY", price_order_level=single_detail["ask"], size=single_detail["size"], force_open=True)
            # we are placing sell orders below the quotes as we are betting when the price goes down
            order_sell = self.df.create_working_order(epic=epic, direction="SELL", price_order_level=single_detail["bid"], size=single_detail["size"],force_open=True)
            map_of_orders = {
                epic: [order_buy, order_sell]
            }

            #check there are two orders for each epic
            orders_present = self.checking_working_order_is_present_under_epic_and_amend_orders(epic=epic)

            # if you don't have enough funds then don't make more trades
            if orders_present == False:

                for single_order in map_of_orders[epic]:

                    if (single_order == None) or (single_order["reason"] == 'INSUFFICIENT_FUNDS'):
                        # double check that all those orders under that epic were delete as IG api can miss it
                        print("delete orders")
                        self.df.cancel_orders_by_epic(epic=epic)
                        return map_of_orders

        return map_of_orders


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

                    position = self.df.find_open_position_by_epic(epic=epic)
                    if len(position) != 0:
                        break

                    print("market is not open yet and orders are in place nothing needs to be done yet")
                    return created_order

            break

        # print("delete orders")
        self.df.cancel_orders_by_epic(epic=epic)
        created_order = False

        return created_order


    def signal_generation(self):

        details_to_create_orders_for = []
        final_df = pd.DataFrame()
        # change this to 13:30 after
        opening_market_time = datetime.strptime("08:00", '%H:%M').time()
        diff_in_time = datetime.combine(date.today(), opening_market_time) - datetime.now()

        total_seconds = diff_in_time.total_seconds()
        if -0.1 > total_seconds > -10:
            epic = "UD.D.TSLA.DAILY.IP"
            # epic = "IX.D.NASDAQ.CASH.IP"
            orders_present = self.checking_working_order_is_present_under_epic_and_amend_orders(epic=epic)
            if orders_present:
                return None

            try:
                price_data = self.df.get_market_data(epic=epic)
            except Exception as e:
                print(e)
                return None


            if price_data == None: return None

            ask = price_data["snapshot"]["offer"]
            bid = price_data["snapshot"]["bid"]
            delay_time = price_data["snapshot"]["delayTime"]
            # min dealing size
            if price_data["dealingRules"]["minDealSize"]["unit"] == "POINTS":
                smallest_size = price_data["dealingRules"]["minDealSize"]["value"]
            else:
                smallest_size = 1
            # getting the margin factor
            if price_data["instrument"]["marginFactorUnit"] == 'PERCENTAGE':
                if price_data["instrument"]["marginFactor"] == 0:
                    factor = 20
                else:
                    factor = price_data["instrument"]["marginFactor"]
                margin_factor = factor/100.0
            else:
                margin_factor = price_data["instrument"]["marginFactorUnit"]


            spread = ask - bid
            if delay_time > 0:
                return

            if spread == 0:
                data = self.df.get_historical_data_via_num_points(epic=epic,resolution="1Min", num_points=1)

                if not isinstance(data, pd.core.frame.DataFrame):
                    return

                if not ("last" in data and "bid" in data):
                    return

                ask = data["last"]["Close"].max()
                bid = data["bid"]["Close"].max()

                if (math.isnan(ask) or math.isnan(bid)):
                    return

            bid = bid - spread/2.0
            ask = ask + spread/2.0

            object_map ={
                        "epic": epic,
                        "bid": round(bid,2),
                        "ask": round(ask,2),
                        # to make the sizes for this larger but still keep these small instruments
                        "size": 1.0
                    }

            details_to_create_orders_for.append(object_map)

            final_df = pd.DataFrame(details_to_create_orders_for)
            if final_df.index.size == 0:
                return final_df

        return final_df

            
            
        
        

