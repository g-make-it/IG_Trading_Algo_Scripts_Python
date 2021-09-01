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
import time
from datetime import datetime, timedelta
from predefined_functions.defined_functionality import Defined_Functionality
import pandas as pd
import traceback
import time
import matplotlib.pyplot as plt
import os
# the newest one where you make market order base on price movements 5 or more and try to catch the trend

class Algo0:
    def __init__(self, instrument_1, instrument_2, instrument_3, index):
        self.set_of_outcomes = set()
        logging.basicConfig(level=logging.INFO)
        self.df = Defined_Functionality()


        self.EUR_USD = instrument_1
        self.GBP_USD = instrument_2
        self.EUR_GBP = instrument_3
        self.index = index

        self.instrument_df = {
            instrument_1:[],
            instrument_2:[],
            instrument_3:[]
        }

        self.diffs_df = {
            instrument_1:[],
            instrument_2:[],
            instrument_3:[]
        }

        self.old_prices = {
            instrument_1:0,
            instrument_2:0,
            instrument_3:0
        }


        # self.EUR_USD = "CS.D.EURUSD.TODAY.IP"
        # self.GBP_USD = "CS.D.GBPUSD.TODAY.IP"
        # self.EUR_GBP = "CS.D.EURGBP.TODAY.IP"

        self.trigger_value = 0

        list_of_epics = [self.GBP_USD, self.EUR_USD , self.EUR_GBP]

        self.df.set_epics_to_look_for(epic_list=list_of_epics)

        self.map_epic_data_minute = {}
        self.map_epic_data_minute_average = {}
        self.triggers = {
            "down": False,
            "down_up":False,
            "up":False,
            "up_down":False
        }
        for epic in list_of_epics:
            self.map_epic_data_minute[epic] = []
            self.map_epic_data_minute_average[epic] = []

        self.first_timestamp = None
        self.high = None
        self.low = None

        self.closing_increments = []




        self.initial_position_size_limit = 0

        self.df.start_data_from_market_data_socket(list_of_epics)
        self.df.start_data_from_account_and_trade_data_socket()
        # time to build up some data

        self.flag = False
        self.timestamp = 121


    def run(self):
        # build up data
        # time.sleep(10)

        while (True):
            try:
                position = self.df.get_open_positions()

                result = self.gather_data_create_signals_close_positions(position)
                if result != None:
                    position = self.create_initial_position(result=result)

            except Exception as e:
                print(e, "   error in the algo")

                # traceback.print_exc()

    def gather_data_create_signals_close_positions(self, positions):
        instruments = [self.EUR_USD, self.EUR_GBP, self.GBP_USD]
        # new
        EUR_GBP_data = self.df.get_quote_data_from_socket(epic=self.EUR_GBP)
        EUR_USD_data = self.df.get_quote_data_from_socket(epic=self.EUR_USD)
        GBP_USD_data = self.df.get_quote_data_from_socket(epic=self.GBP_USD)

        market_data = [EUR_USD_data, EUR_GBP_data, GBP_USD_data]

        if positions != None:
            list_closing_positions = []
            for single_position in positions:
                epic = single_position["market"]["epic"]
                if not epic in instruments:
                    continue
                index_place = instruments.index(epic)
                # closing position handled by the stop algo - for now
                closing = self.check_position_closing(single_position, market_data[index_place])
                if closing != None:
                    print(closing)
            return None

        # old
        EUR_GBP_data_old = self.df.get_old_quote_data_from_socket(epic=self.EUR_GBP)
        if EUR_GBP_data_old == None: return None
        EUR_USD_data_old = self.df.get_old_quote_data_from_socket(epic=self.EUR_USD)
        if EUR_USD_data_old == None: return None
        GBP_USD_data_old = self.df.get_old_quote_data_from_socket(epic=self.GBP_USD)
        if GBP_USD_data_old == None: return None

        # new
        EUR_GBP_data["mid"] = (EUR_GBP_data["BID"] + EUR_GBP_data["OFFER"]) / 2.0
        EUR_USD_data["mid"] = (EUR_USD_data["BID"] + EUR_USD_data["OFFER"]) / 2.0
        GBP_USD_data["mid"] = (GBP_USD_data["BID"] + GBP_USD_data["OFFER"]) / 2.0

        # old
        EUR_GBP_data_old["mid"] = (EUR_GBP_data_old["BID"] + EUR_GBP_data_old["OFFER"]) / 2.0
        EUR_USD_data_old["mid"] = (EUR_USD_data_old["BID"] + EUR_USD_data_old["OFFER"]) / 2.0
        GBP_USD_data_old["mid"] = (GBP_USD_data_old["BID"] + GBP_USD_data_old["OFFER"]) / 2.0
        if self.index == 0:
            # EURUSD
            # GBPUSD
            # EURGBP
            # outcome = 1/EUR_USD_data["mid"]*EUR_GBP_data["mid"]*GBP_USD_data["mid"]
            outcome = 1/EUR_USD_data["mid"]*EUR_GBP_data["mid"]*GBP_USD_data["mid"]
        elif self.index == 1:
            # USDJPY
            # GBPUSD
            # GBPJPY
            outcome = 1 * EUR_USD_data["mid"] / EUR_GBP_data["mid"] * GBP_USD_data["mid"]

        # this section has been edited to look for the signals we buy and sell with to check alpha and beta are okay
        self.set_of_outcomes.add(round(outcome,2))

        if 9999 < outcome < 10001:
            return


        diff_1 = EUR_USD_data["mid"]/ EUR_USD_data_old["mid"]
        diff_2 = EUR_GBP_data["mid"]/ EUR_GBP_data_old["mid"]
        diff_3 = GBP_USD_data["mid"]/ GBP_USD_data_old["mid"]

        diffs_org = [diff_1,diff_2,diff_3]
        # min is going long
        min_index = diffs_org.index(min(diffs_org))
        # max is short
        max_index = diffs_org.index(max(diffs_org))

        result = {
            "BUY": instruments[min_index],
            "SELL" : instruments[max_index]
        }
        return result


    def check_position_closing(self, position, market_data):
        spread = 1
        direction = position["position"]["direction"]
        # long
        if direction == "BUY":
            #     we sell at the bid
            if (market_data["BID"] - position["position"]["openLevel"]) > spread:
                #close
                return self.close_position(position)
        elif direction == "SELL":
            if (position["position"]["openLevel"] - market_data["OFFER"]) > spread:
                #close
                return self.close_position(position)





    def create_initial_position(self, result):
        for direction in result.keys():

            position = self.df.find_open_position_by_epic(epic=result[direction])

            if position == "error":
                print(position)
                continue

            if len(position) >= 1:
                print(position)
                continue


            if direction == "BUY":
                position = self.df.create_open_position(epic=result[direction], direction="BUY", size=1)
            else:
                position = self.df.create_open_position(epic=result[direction], direction="SELL", size=1)


    def close_position(self, position):

        if len(position) == 0:
            self.initial_position_size_limit = 0
            return

        size = position["position"]["dealSize"]
        closing = self.df.close_position(size=size, position=position[0])

        return closing



    def signal_generation(self, epic):
        signals_levels = None
        # minute_10 = 60 * 10
        # minute_10 = 60
        minute_10 = 6
        datetime_now = datetime.now()
        data = None
        if (self.first_timestamp != None):
            difference = (datetime_now - self.first_timestamp)
            data = self.df.get_quote_data_from_socket(epic=epic)
            # self.finding_lows_highs(data=data)

            if (difference.seconds > minute_10):
                data = self.df.get_quote_data_from_socket(epic=epic)
                self.first_timestamp = datetime_now
                self.map_epic_data_minute[epic].append(data)
                # self.finding_lows_highs(data=data, reset=True)

        else:
            data = self.df.get_quote_data_from_socket(epic=epic)
            self.first_timestamp = datetime_now

            self.map_epic_data_minute[epic].append(data)
            # self.finding_lows_highs(data=data)

        if len(self.map_epic_data_minute[epic]) > 3:
            self.map_epic_data_minute[epic].pop(0)

            sell_level = None
            buy_level = None

            object_epic_data = self.map_epic_data_minute[epic][-1]
            bid = object_epic_data["BID"]
            offer = object_epic_data["OFFER"]
            high = object_epic_data["HIGH"]
            low = object_epic_data["LOW"]

            object_epic_data = self.map_epic_data_minute[epic][-2]
            bid_second = object_epic_data["BID"]
            offer_second = object_epic_data["OFFER"]
            high_second = object_epic_data["HIGH"]
            low_second = object_epic_data["LOW"]

            # object_epic_data = self.map_epic_data_minute[epic][-3]
            # bid_third = object_epic_data["snapshot"]["bid"]
            # offer_third = object_epic_data["snapshot"]["offer"]
            # high_third = object_epic_data["snapshot"]["high"]
            # low_third = object_epic_data["snapshot"]["low"]
            # # the price is going down there you should buy
            # if offer_third > offer_second > offer:
            #     buy_level = 1
            # #     the price is going up therefore you should sell
            # elif bid_third < bid_second < bid:
            #     sell_level = 1

            # instead here we are using bid/offer


            bid_offer_second_average = (bid_second + offer_second)/2.0
            self.map_epic_data_minute_average[epic].append(bid_offer_second_average)

            bid_offer_average = (bid + offer)/2.0
            self.map_epic_data_minute_average[epic].append(bid_offer_average)

            if len(self.map_epic_data_minute_average[epic]) > 10:
                self.map_epic_data_minute_average[epic].pop(0)


            if self.triggers["down"] == True:
                # sudden change up
                if bid_offer_second_average < bid_offer_average:
                    self.triggers["down_up"] = True

            elif self.triggers["up"] == True:
                # sudden change down
                if bid_offer_second_average > bid_offer_average:
                    self.triggers["up_down"] = True



            # going down - trailing
            if (self.triggers["up"] != True) and bid_offer_second_average > bid_offer_average:
                self.triggers["down"] = True
                self.triggers["up"] = False
            # going up - trailing
            if (self.triggers["down"] != True) and bid_offer_second_average < bid_offer_average:
                self.triggers["up"] = True
                self.triggers["down"] = False

            # we are going down and found a downwards peak as the price rises up
            if self.triggers["down"] and self.triggers["down_up"]:
                sell_level = 1
                self.triggers = {
                    "down": False,
                    "down_up": False,
                    "up": False,
                    "up_down": False
                }


            elif self.triggers["up"] and self.triggers["up_down"]:
                buy_level = 1
                self.triggers = {
                    "down": False,
                    "down_up": False,
                    "up": False,
                    "up_down": False
                }




            if (sell_level == None) and (buy_level == None):
                return None

            signals_levels = {
                "SELL": sell_level,
                "BUY": buy_level
            }

        return signals_levels

    def finding_lows_highs(self, data, reset=False):

        bid = data["snapshot"]["bid"]
        offer = data["snapshot"]["offer"]

        if reset:
            epic = data["instrument"]["epic"]
            object_dict = self.map_epic_data_minute[epic][-1]
            object_dict["snapshot"]["high"] = self.high
            object_dict["snapshot"]["low"] = self.low
            self.map_epic_data_minute[epic][-1] = object_dict
        # start looking at the new interval
        if self.high == None or reset:
            self.high = offer
        if self.low == None or reset:
            self.low = bid

        if bid < self.low:
            self.low = bid
        if offer > self.high:
            self.high = offer






