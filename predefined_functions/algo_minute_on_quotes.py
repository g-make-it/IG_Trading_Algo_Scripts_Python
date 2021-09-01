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
from datetime import datetime, timedelta
from predefined_functions.defined_functionality import Defined_Functionality
import pandas
import traceback

# the newest one where you make market order base on price movements 5 or more and try to catch the trend

class Algo0:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.df = Defined_Functionality()

        list_of_epics = ['IX.D.DOW.DAILY.IP']
        # list_of_epics = ['CS.D.EURUSD.TODAY.IP']

        self.df.set_epics_to_look_for(epic_list=list_of_epics)

        self.map_epic_data_minute={}
        for epic in list_of_epics:
            self.map_epic_data_minute[epic] = []


        self.first_timestamp = None
        self.high = None
        self.low = None

    def setup(self):
        self.df.initialise_connection()
        time.sleep(2)
        self.df.get_market_data()
        self.df.update_stop_level_bands()


    def run(self):

        while(True):
            try:
                self.setup()

                for epic in self.map_epic_data_minute.keys():
                    signals_and_levels = self.signal_generation(epic=epic)
                    self.create_orders(epic=epic, signals_levels=signals_and_levels)

            except Exception as e:
                print(e, "   error in the looping for the defined_functionality")
                traceback.print_exc()


    def create_orders(self, epic, signals_levels):
        if signals_levels == None:
            return
        key = None
        if signals_levels["BUY"] != None:
            key = "BUY"
        elif signals_levels["SELL"] != None:
            key = "SELL"


        position = self.df.find_open_position_by_epic(epic=epic)

        if isinstance(position,pandas.core.series.Series):
            print("position already exists", position)
            return position

        create_position = self.df.create_open_position(epic=epic, direction=key, size=0.5)

        return create_position
        

    def signal_generation(self, epic):
        signals_levels = None
        # minute_10 = 60 * 10
        # minute_10 = 60
        minute_10 = 6
        datetime_now = datetime.now()
        data = None
        if (self.first_timestamp != None):
            difference = (datetime_now - self.first_timestamp)
            data = self.df.get_market_data(epic=epic)
            # self.finding_lows_highs(data=data)

            if (difference.seconds > minute_10):
                data = self.df.get_market_data(epic=epic)
                self.first_timestamp = datetime_now
                self.map_epic_data_minute[epic].append(data)
                # self.finding_lows_highs(data=data, reset=True)

        else:
            data = self.df.get_market_data(epic=epic)
            self.first_timestamp = datetime_now

            self.map_epic_data_minute[epic].append(data)
            # self.finding_lows_highs(data=data)

        if len(self.map_epic_data_minute[epic]) > 3:
            self.map_epic_data_minute[epic].pop(0)


            sell_level = None
            buy_level = None
    
            object_epic_data = self.map_epic_data_minute[epic][-1]
            bid = object_epic_data["snapshot"]["bid"]
            offer = object_epic_data["snapshot"]["offer"]
            high = object_epic_data["snapshot"]["high"]
            low = object_epic_data["snapshot"]["low"]

            object_epic_data = self.map_epic_data_minute[epic][-2]
            bid_old = object_epic_data["snapshot"]["bid"]
            offer_old = object_epic_data["snapshot"]["offer"]
            high_old = object_epic_data["snapshot"]["high"]
            low_old = object_epic_data["snapshot"]["low"]

            offer_diff = offer - offer_old
            bid_diff = bid - bid_old
            # as we are following the trends
            # # if offer_diff > 5:
            # if offer_diff > 0:
            #     buy_level = 1
            # # elif offer_diff < -5:
            # elif offer_diff < 0:
            #     sell_level = 1

            if offer_diff > 10:
                buy_level = 1
            elif bid_diff < -10:
                sell_level = 1
                
            self.map_epic_data_minute[epic] = []
            # instead here we are using bid/offer

            if (sell_level == None) and (buy_level == None):
                return None
                
            signals_levels = {
                "SELL": sell_level,
                "BUY": buy_level
            }
            
        return signals_levels

    def finding_lows_highs(self, data, reset = False):

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
            
            
            
        
        

