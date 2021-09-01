from trading_ig import IGService
from trading_ig.config import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# if you need to cache to DB your requests
from datetime import timedelta
import requests_cache

import time
import json
import math
import pandas as pd
from predefined_functions.initialisation import Initialisation

class Position_Management():
    def __init__(self):
        # set object then connection
        self.initial = Initialisation()
        self.initialise_connection()
        self.initialise_data()

    def initialise_connection(self):
        self.ig_service = self.initial.initialise_connection()

    def initialise_data(self):
        # this should change to be more dynamic
        # self.instrument_data = pd.read_csv("D:/Data/IG_Data/instruments_new_filtered.csv")
        # self.instrument_data.drop("Unnamed: 0", axis=1, inplace=True)
        pass

    def initialise(self):
        logging.basicConfig(level=logging.DEBUG)

        expire_after = timedelta(hours=1)
        session = requests_cache.CachedSession(
            cache_name='cache', backend='sqlite', expire_after=expire_after
        )
        # set expire_after=None if you don't want cache expiration
        # set expire_after=0 if you don't want to cache queries

        # config = IGServiceConfig()

        # no cache
        self.ig_service = IGService(
            config.username, config.password, config.api_key, config.acc_type
        )
        # if you want to globally cache queries
        # ig_service = IGService(config.username, config.password, config.api_key, config.acc_type, session)
        self.ig_service.create_session()

    def get_margin_min_distance_from_position_stop(self, dealing_rules, current_price, guaranteed_stop):
        # for controlled risk, guaranteed stop loss thing - keep to this one - worst case scenario -
        if guaranteed_stop:
            map_of_items = dealing_rules["minControlledRiskStopDistance"]
        else:
            #normal stop loss
            map_of_items = dealing_rules["minNormalStopOrLimitDistance"]

        # single_row = self.instrument_data[self.instrument_data["epic"] == epic]
        # the mam produces back the actual value and not the dataframe
        # map_of_items = json.loads(single_row["minControlledRiskStopDistance"].max())

        difference_required = map_of_items["value"]
        # otherwise the unit is POINTS
        if map_of_items["unit"] == "PERCENTAGE":
            difference_required = difference_required / 100
            return (difference_required)*current_price

        return difference_required

    def get_margin_min_max_distance_from_position_limit(self, dealing_rules, current_price, min_limit_stop):
        # for controlled risk, guaranteed stop loss thing - keep to this one - worst case scenario
        if min_limit_stop:
            map_of_items = dealing_rules["minNormalStopOrLimitDistance"]
        else:
            map_of_items = dealing_rules["maxStopOrLimitDistance"]

        # single_row = self.instrument_data[self.instrument_data["epic"] == epic]
        # the mam produces back the actual value and not the dataframe
        # map_of_items = json.loads(single_row["minControlledRiskStopDistance"].max())

        difference_required = map_of_items["value"]
        # otherwise the unit is POINTS
        if map_of_items["unit"] == "PERCENTAGE":
            difference_required = difference_required / 100
            return (difference_required)*current_price

        return difference_required


    def is_new_levels_better_and_generate(self, direction,stop_distance, current_price, entered_price, limit_distance, local, old_stop_level_price=None):
        stop_level = 0
        limit_level = 0
        # going short
        if direction == "SELL":
            # unlikely as we would always have a stop loss
            if old_stop_level_price == None:
                # have to do this as the stop level might not work spread moving too quickly
                stop_level = current_price + (stop_distance * 10)
                limit_level = entered_price - limit_distance

                return stop_level, limit_level

            # can't do this as the price might miss the stop loss
            # --------------------------------------------------------------------------------
            # # setting the stop price at the entry point - as we are in profit
            # elif (current_price < entered_price) and (old_stop_level_price > entered_price):
            #     return entered_price, None
            # --------------------------------------------------------------------------------

            # get the distance between the edge that we can place the stop loss and the old stop loss and meet it half way
            """
            This way you stop loss will that edge very closely 
            """

            stop_loss_edge = current_price + stop_distance
            half_distance = (old_stop_level_price - stop_loss_edge)/2.0
            stop_level = current_price + half_distance
            # stop loss is being missed on exchange increasing value
            if old_stop_level_price > (stop_level+0.1):
                return stop_level , None

            return None
        else:

            # put the stop loss at the entered price
            if (old_stop_level_price == None) :
                stop_level = current_price - (stop_distance * 10)
                limit_level = entered_price + limit_distance

                return stop_level, limit_level
            # # we are in profit -  put the stop loss on the entered price
            # ---------------------------------------------------------------------------------
            # elif (current_price > entered_price) and (old_stop_level_price < entered_price):
            #     return entered_price, None
            # ---------------------------------------------------------------------------------
            # get the distance between the edge that we can place the stop loss and the old stop loss and meet it half way
            """
            This way you stop loss will that edge very closely 
            """
            stop_loss_edge = current_price - stop_distance
            half_distance = (stop_loss_edge - old_stop_level_price)/2.0
            stop_level = current_price - half_distance
            # stop_loss is missing on exchange
            if old_stop_level_price < (stop_level - 0.1):
                return stop_level, None

            return None

    # generated stop loss levels (numbers, not really implemented)
    def generate_levels_if_none_exists(self, direction, stop_distance, current_price, entered_price, limit_distance):
        stop_level = 0
        limit_level = 0
        if direction == "SELL":
            stop_level = stop_distance + current_price
            limit_level = entered_price - limit_distance
            return stop_level,limit_level

        else:
            stop_level = stop_distance - current_price
            limit_level = entered_price + limit_distance
            return stop_level,limit_level
