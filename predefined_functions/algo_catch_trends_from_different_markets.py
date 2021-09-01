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



        # list_of_epics = ['IX.D.DOW.DAILY.IP']
        # list_of_epics = ['IX.D.SPTRD.DAILY.IP']
        # list_of_epics = ['CS.D.EURUSD.TODAY.IP']
        list_of_epics = [
            'IX.D.DOW.DAILY.IP',
            'IX.D.SPTRD.DAILY.IP',
            'IX.D.FTSE.DAILY.IP'
        ]

        self.df.set_epics_to_look_for(epic_list=list_of_epics)

        self.tradeable_epic = ['IX.D.DOW.DAILY.IP']

        self.map_epic_data_minute = {}
        for epic in list_of_epics:
            self.map_epic_data_minute[epic] = []

        self.first_timestamp = None
        self.high = None
        self.low = None

    def setup(self):
        self.df.initialise_connection()
        # not required as we are not trailing any losses
        # time.sleep(2)
        # self.df.get_market_data()
        # self.df.update_stop_level_bands()

    def run(self):

        while (True):
            try:
                self.setup()

                for epic in self.tradeable_epic:

                    signals_and_levels = self.signal_generation(epic_list=self.map_epic_data_minute.keys())
                    position = self.create_position(signal=signals_and_levels, epic=epic)
                    if position == "error": continue
                    self.closing_incrments(position=position,signals=signals_and_levels)

            except Exception as e:
                print(e, "   error in the looping for the defined_functionality")

                traceback.print_exc()




    def create_position(self, signal, epic):
        position = self.df.find_open_position_by_epic(epic=epic)

        if position == "error": return position
        if len(position) >= 1: return position
        if signal == None: return None

        key=None
        if signal["BUY"]:
            key = "BUY"
        elif signal["SELL"]:
            key = "SELL"

        if key == None: return None

        position = self.df.create_open_position(epic=epic, direction=key, size=0.5)
        return position


    def closing_incrments(self, position, signals):
        position = position[0]
        direction = position["position"]["direction"]
        epic = position["market"]["epic"]
        opening_price = position["position"]["openLevel"]

        data = self.df.get_market_data(epic=epic)
        bid = data["snapshot"]["bid"]
        offer = data["snapshot"]["offer"]

        spread = offer - bid

        boolean_close_buy = False
        boolean_close_sell = False

        if direction == "BUY":
            boolean_close_buy = opening_price < (bid - spread)

        elif direction == "SELL":
            boolean_close_sell = opening_price > (offer + spread)

        if boolean_close_buy or boolean_close_sell:
            closing_increment = self.df.close_position(size=0.01,position=position)
            return closing_increment
        return None



    def signal_generation(self, epic_list):
        signals_levels = None
        # minute_10 = 60 * 10
        # minute_10 = 60
        minute_10 = 6
        datetime_now = datetime.now()
        limit = 3
        data = None

        signal_matrix = {}

        capture_time = False

        for epic in epic_list:

            if (self.first_timestamp != None):
                difference = (datetime_now - self.first_timestamp)
                # appending data into df map_epic_data
                data = self.df.get_market_data(epic=epic)
                # self.finding_lows_highs(data=data)

                if (difference.seconds > minute_10):
                    capture_time = True
                    data = self.df.get_market_data(epic=epic)
                    self.map_epic_data_minute[epic].append(data)
                    # self.finding_lows_highs(data=data, reset=True)

            else:
                data = self.df.get_market_data(epic=epic)
                capture_time = True
                self.map_epic_data_minute[epic].append(data)
                # self.finding_lows_highs(data=data)

            if len(self.map_epic_data_minute[epic]) > limit:
                self.map_epic_data_minute[epic].pop(0)

                sell_level = None
                buy_level = None

                object_epic_data = self.map_epic_data_minute[epic][-1]
                bid = object_epic_data["snapshot"]["bid"]
                offer = object_epic_data["snapshot"]["offer"]
                high = object_epic_data["snapshot"]["high"]
                low = object_epic_data["snapshot"]["low"]

                object_epic_data = self.map_epic_data_minute[epic][-2]
                bid_second = object_epic_data["snapshot"]["bid"]
                offer_second = object_epic_data["snapshot"]["offer"]
                high_second = object_epic_data["snapshot"]["high"]
                low_second = object_epic_data["snapshot"]["low"]

                object_epic_data = self.map_epic_data_minute[epic][-3]
                bid_third = object_epic_data["snapshot"]["bid"]
                offer_third = object_epic_data["snapshot"]["offer"]
                high_third = object_epic_data["snapshot"]["high"]
                low_third = object_epic_data["snapshot"]["low"]
                # the price is going down there you should buy
                if offer_third > offer_second > offer:
                    buy_level = 1
                #     the price is going up therefore you should sell
                elif bid_third < bid_second < bid:
                    sell_level = 1

                signal_matrix[epic] = {
                    "SELL": sell_level,
                    "BUY": buy_level
                }

        if capture_time:
            self.first_timestamp = datetime_now

        key = list(self.map_epic_data_minute.keys())[0]
        # because up above you remove one item from the list

        if (not key in signal_matrix) or (len(signal_matrix) == 0):
            return None

        sell_level = signal_matrix[key]["SELL"]
        buy_level = signal_matrix[key]["BUY"]
        for epic in signal_matrix.keys():
            sell_level = sell_level and signal_matrix[epic]["SELL"]
            buy_level = buy_level and signal_matrix[epic]["BUY"]

        # once you have a signal_matrix made you need to find if a signal exists
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






