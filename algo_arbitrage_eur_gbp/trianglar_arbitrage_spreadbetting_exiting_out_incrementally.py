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
import winsound

# the newest one where you make market order base on price movements 5 or more and try to catch the trend

class Algo0:
    def __init__(self, GBPEUR, EURGBP):
        self.set_of_outcomes = set()
        logging.basicConfig(level=logging.INFO)
        self.df = Defined_Functionality()


        self.GBP_EUR = GBPEUR
        self.EUR_GBP = EURGBP

        self.trigger_value = 0

        self.instruments = [self.GBP_EUR, self.EUR_GBP]
        list_of_epics = [self.GBP_EUR, self.EUR_GBP]

        self.df.set_epics_to_look_for(epic_list=self.instruments)

        self.map_epic_data_minute = {}
        self.map_epic_data_minute_average = {}

        self.size_of_our_position = {}
        for epic in self.instruments:
            self.map_epic_data_minute[epic] = []
            self.map_epic_data_minute_average[epic] = []
            # working initial size of the entry and when to stop if half of it has been filled
            self.size_of_our_position[epic] = 1

        self.first_timestamp = None
        self.high = None
        self.low = None

        self.closing_increments = []

        self.initial_position_size_limit = 0

        self.df.start_data_from_market_data_socket(list_of_epics)
        self.df.start_data_from_account_and_trade_data_socket()
        # time to build up some data

        self.flag = False
        self.previous_string= ""


    def run(self):
        # build up data
        # time.sleep(10)

        while (True):
            try:
                position = self.df.get_open_positions()

                result = self.gather_data_create_signals_close_positions(position)
                # if result != None:
                    # position = self.create_initial_position(result=result)

            except Exception as e:
                print(e, "   error in the algo")

                # traceback.print_exc()

    def gather_data_create_signals_close_positions(self, positions):
        # new
        EUR_GBP_data = self.df.get_quote_data_from_socket(epic=self.EUR_GBP)
        GBP_EUR_data = self.df.get_quote_data_from_socket(epic=self.GBP_EUR)

        market_data = [GBP_EUR_data, EUR_GBP_data]

        if positions != None:
            list_closing_positions = []
            for instrument in self.instruments:
                positions = self.df.find_open_position_by_epic(epic=instrument)
                if len(positions) == 0:continue

                # if len(positions) >= 2:
                #     first_size = positions[0]["position"]["dealSize"]
                #     second_size = positions[1]["position"]["dealSize"]
                #
                #     half_size = (self.size_of_our_position[instrument] / 2.0)
                #
                #     if first_size <= half_size and second_size <= half_size:
                #         self.size_of_our_position[instrument] = half_size
                #
                #     # excluding the position for which the other need to balance for
                #     if first_size <= half_size:
                #         # get the second position in list form
                #         positions = positions[1:]
                #     elif second_size <= half_size:
                #         # gets the first position in list form with only one item in it
                #         positions = positions[:1]

                for single_position in positions:
                    epic = single_position["market"]["epic"]
                    if not epic in self.instruments:
                        continue
                    index_place = self.instruments.index(epic)
                    # closing position handled by the stop algo - for now
                    closing = self.check_position_closing(single_position, market_data[index_place])
                    # if closing != None:
                    #     print(closing)
            # time.sleep(10)
            return None

        # old
        EUR_GBP_data_old = self.df.get_old_quote_data_from_socket(epic=self.EUR_GBP)
        if EUR_GBP_data_old == None: return None
        GBP_EUR_data_old = self.df.get_old_quote_data_from_socket(epic=self.GBP_EUR)
        if GBP_EUR_data_old == None: return None

        # new
        EUR_GBP_data["mid"] = (EUR_GBP_data["BID"] + EUR_GBP_data["OFFER"]) / 2.0
        GBP_EUR_data["mid"] = (GBP_EUR_data["BID"] + GBP_EUR_data["OFFER"]) / 2.0


        # old
        EUR_GBP_data_old["mid"] = (EUR_GBP_data_old["BID"] + EUR_GBP_data_old["OFFER"]) / 2.0
        GBP_EUR_data_old["mid"] = (GBP_EUR_data_old["BID"] + GBP_EUR_data_old["OFFER"]) / 2.0

        spread_g =GBP_EUR_data["OFFER"] - GBP_EUR_data["BID"]
        sperad_ratio_g = spread_g/GBP_EUR_data["mid"]

        spread_e =EUR_GBP_data["OFFER"] - EUR_GBP_data["BID"]
        spread_ratio_e= spread_e/EUR_GBP_data["mid"]

        sub_list = [sperad_ratio_g, spread_ratio_e]

        index_value = sub_list.index(max(sub_list))
        # gives you the other currency value for you to work out the smallest spread needed since there is two items 1 -
        spread = sub_list[index_value] * market_data[1-index_value]["mid"]

        EUR_GBP_deduced = (1/GBP_EUR_data["mid"] )*100000000
        EUR_GBP_actual = EUR_GBP_data["mid"]

        string = "EUR_GBP_deduced: " + str(EUR_GBP_deduced) +  " EUR_GBP_actual: " + str(EUR_GBP_actual)

        if self.previous_string == string: return

        print(string)
        self.previous_string = string

        outcome = EUR_GBP_actual - EUR_GBP_deduced

        # this section has been edited to look for the signals we buy and sell with to check alpha and beta are okay
        self.set_of_outcomes.add(round(outcome,2))
        # commented this out for the time being - to test orders can be set across
        if abs(outcome) < spread:
            return
        winsound.Beep(440, 500)

        # they are opposites so need to make positions in the opposite direction as they are the inverse of each other's market
        if outcome > spread:
        #     actual is higher and short
        #     deduced is lower long
            result = {
                "SELL": self.GBP_EUR,
                "BUY": self.EUR_GBP
            }
        elif outcome < (-1*spread):
        #     actual is lower long
        #     deduced is higher short
            result = {
                "SELL" : self.EUR_GBP,
                "BUY" : self.GBP_EUR
            }

        self.create_initial_position(result=result)



    def check_position_closing(self, position, market_data):
        spread = 1
        direction = position["position"]["direction"]

        # long
        if direction == "BUY":
            #     we sell at the bid
            if (market_data["BID"] - position["position"]["openLevel"]) > spread:
                #close
                return self.close_position_incrementally(position)
        elif direction == "SELL":
            if (position["position"]["openLevel"] - market_data["OFFER"]) > spread:
                #close
                return self.close_position_incrementally(position)


    def create_initial_positions_on_both_sides(self, instrument):
        self.size_of_our_position = 1
        position = self.df.find_open_position_by_epic(epic=instrument)

        if position == "error":
            print(position)
            return
        # because we are making positions on both side for one instrument
        if len(position) >= 2:
            print(position)
            return
        position = self.df.create_open_position(epic=instrument, direction="BUY", size=self.size_of_our_position, limits=False, force_open=True)
        position = self.df.create_open_position(epic=instrument, direction="SELL", size=self.size_of_our_position,limits=False, force_open=True)

    def create_initial_position(self, result):
        self.size_of_our_position = 1
        for direction in result.keys():
            position = self.df.find_open_position_by_epic(epic=result[direction])

            if position == "error":
                print(position)
                continue

            # because we are making positions on both side for one instrument
            if len(position) >= 2:
                print(position)
                continue

            if direction == "BUY":
                position = self.df.create_open_position(epic=result[direction], direction="BUY", size=self.size_of_our_position, limits=True, force_open=False)
            else:
                position = self.df.create_open_position(epic=result[direction], direction="SELL", size=self.size_of_our_position,limits=True, force_open=False)



    def create_working_orders(self, result, price_b, price_o, spread):
        for direction in result.keys():

            average_price = round((price_b + price_o)/2.0, 2)
            half_spread = round(spread/2.0 , 2)
            spread_reduced = spread - 0.2
            # gives a buffer for orders to be filled
            average_price += 2

            if direction == "BUY":
                # entry_price = average_price + (spread/2)
                order = self.df.create_working_order( epic=result[direction], direction=direction, price_order_level=average_price, size=0.5, limits=False)
            elif direction == "SELL":
                # entry_price = average_price - (spread/2)
                order = self.df.create_working_order( epic=result[direction], direction=direction, price_order_level=average_price, size=0.5, limits=False)


    def close_position_incrementally(self, position):

        if len(position) == 0:
            self.initial_position_size_limit = 0
            return

        size = 0.1
        closing = self.df.close_position(size=size, position=position[0])

        return closing


