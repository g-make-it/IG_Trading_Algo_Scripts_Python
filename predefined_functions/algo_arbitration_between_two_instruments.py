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
        # Wall St
        self.instrument_1 = 'IX.D.DOW.DAILY.IP'
        # Us500
        self.instrument_2 = 'IX.D.SPTRD.DAILY.IP'

        list_of_epics = [
            self.instrument_1,
            self.instrument_2
        ]

        self.df.set_epics_to_look_for(epic_list=list_of_epics)

        self.tradeable_epic = {
            self.instrument_1:0,
            self.instrument_2:0
        }

        self.map_epic_data_minute = {}
        for epic in list_of_epics:
            self.map_epic_data_minute[epic] = []

        self.first_timestamp = None
        self.high = None
        self.low = None
        # Wallst
        self.previous_day_high_instrument = {}
        self.previous_day_high_instrument[self.instrument_1] = 23475.5
        # Us500
        self.previous_day_high_instrument[self.instrument_2] = 2845.80


        self.required_size = {}
        self.required_size[self.instrument_1] = 0
        self.required_size[self.instrument_2] = 0

        self.initial_size = 3

        self.starting_diff_rate = 0

    # def setup(self):

    #     # not required as we are not trailing any losses
    #     # time.sleep(2)
    #     # self.df.get_market_data()
    #     # self.df.update_stop_level_bands()

    def run(self):

        while (True):
            try:
                # self.setup()

                signal_matrix = self.signal_generation(epic_list=self.map_epic_data_minute.keys())
                sizes = self.create_size()

                positions = self.create_position(signal_matrix=signal_matrix, sizes=sizes)
                if positions == "error" or positions == None: continue
                self.closing_incrments(position=positions, signal_matrix=signal_matrix)

            except Exception as e:
                print(e, "   error in the looping for the defined_functionality")

                traceback.print_exc()
    def create_size(self):

        sizes={
            self.instrument_1:0,
            self.instrument_2:0
        }

        instrument_1_price = self.map_epic_data_minute[self.instrument_1][-1]["snapshot"]["offer"]
        instrument_2_price = self.map_epic_data_minute[self.instrument_2][-1]["snapshot"]["offer"]
        largest = max(instrument_1_price, instrument_2_price)
        smallest = min(instrument_1_price, instrument_2_price)

        rate = largest/smallest

        if instrument_1_price == largest:
            sizes[self.instrument_1] = self.initial_size
            sizes[self.instrument_2] = self.initial_size * rate
        else:
            sizes[self.instrument_2] = self.initial_size
            sizes[self.instrument_1] = self.initial_size * rate

        return sizes


    def calculate_pnl(self, position):
        market = position["market"]
        bid = market["bid"]
        offer = market["offer"]
        position = position["position"]
        open_level = position["openLevel"]
        direction = position["direction"]
        rate = 0
        if direction == "SELL":
            rate = open_level - bid
        else:
            rate = offer - open_level

        pnl = rate * position["dealSize"]
        spread = offer - bid
        pnl -= (spread * position["dealSize"])
        return pnl



    def create_position(self, signal_matrix, sizes):
        positions = {}
        position_1 = self.df.find_open_position_by_epic(epic=self.instrument_1)
        positions[self.instrument_1] = position_1
        position_2 = self.df.find_open_position_by_epic(epic=self.instrument_2)
        positions[self.instrument_2] = position_2

        if position_1 == "error" or position_2 =="error": return "error"
        if len(position_1) >= 1 or len(position_2) >= 1:
            open_level_1 = position_1[0]["position"]["openLevel"]
            open_level_2 = position_2[0]["position"]["openLevel"]
            ratio_1 = open_level_1/self.previous_day_high_instrument[self.instrument_1]
            ratio_2 = open_level_2/self.previous_day_high_instrument[self.instrument_2]
            # only use if the trade was made on the day
            diff_ratio = ratio_1 - ratio_2
            self.starting_diff_rate = diff_ratio

            return positions
        if signal_matrix == None: return None

        key = "BUY" if signal_matrix[self.instrument_1]["BUY"] else "SELL"
        size = sizes[self.instrument_1]
        position_1 = self.df.create_open_position(epic=self.instrument_1, direction=key, size=size, limits=False, force_open=True)

        key = "BUY" if signal_matrix[self.instrument_2]["BUY"] else "SELL"
        size = sizes[self.instrument_2]
        position_2 = self.df.create_open_position(epic=self.instrument_2, direction=key, size=size,limits=False, force_open=True)

        self.starting_diff_rate = signal_matrix["rate"]

        positions[self.instrument_1] = position_1
        positions[self.instrument_2] = position_2

        return positions


    def closing_incrments(self, position, signal_matrix):

        reducing_amount = 0.01
        single_position_data_1 = position[self.instrument_1][0]
        pnl_1 = self.calculate_pnl(position=single_position_data_1)
        single_position_data_2 = position[self.instrument_2][0]
        pnl_2 = self.calculate_pnl(position=single_position_data_2)

        total_pnl = (pnl_1 + pnl_2)

        print("total_pnl: ", total_pnl)
        # if bigger than 0.00
        if not total_pnl > 0:
            return None



        # if signal_matrix == None or signal_matrix["rate"] == None:
        #     return None
        #
        # rate = signal_matrix["rate"]
        # if not rate < (self.starting_diff_rate - 0.0004):
        #     return None

        list_closing_increments = []

        size_1 = single_position_data_1["position"]["dealSize"]
        offer_1 = single_position_data_1["market"]["offer"]
        # data = self.df.get_market_data(epic=self.instrument_1)
        # offer_1 = data["snapshot"]["offer"]

        size_2 = single_position_data_2["position"]["dealSize"]
        offer_2 = single_position_data_2["market"]["offer"]
        # data = self.df.get_market_data(epic=self.instrument_2)
        # offer_2 = data["snapshot"]["offer"]

        if offer_1 > offer_2:
            # if the price is higher a smaller position is take out
            number_of_closing_trades = size_1/reducing_amount
            size_1_of_closing = reducing_amount
            size_2_of_closing = size_2/number_of_closing_trades
        else:
            number_of_closing_trades = size_2/reducing_amount
            size_1_of_closing = size_1/number_of_closing_trades
            size_2_of_closing = reducing_amount


        closing_increment = self.df.close_position(size=size_1_of_closing,position=single_position_data_1)
        list_closing_increments.append(closing_increment)
        closing_increment = self.df.close_position(size=size_2_of_closing,position=single_position_data_2)
        list_closing_increments.append(closing_increment)

        return list_closing_increments





    def signal_generation(self, epic_list):
        # minute_10 = 60 * 10
        # minute_10 = 60
        minute_10 = 6
        datetime_now = datetime.now()
        limit = 3
        data = None

        signal_matrix = {}
        capture_time = False

        ratio = {}

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

                object_epic_data = self.map_epic_data_minute[epic][-1]
                bid = object_epic_data["snapshot"]["bid"]
                offer = object_epic_data["snapshot"]["offer"]
                high = object_epic_data["snapshot"]["high"]
                low = object_epic_data["snapshot"]["low"]
                # try using the current high as stated by the IG's api
                ratio[epic] = offer/self.previous_day_high_instrument[epic]
                ratio[epic+"1"] = offer/high

        if capture_time:
            self.first_timestamp = datetime_now

        if not ((self.instrument_1 in ratio) and (self.instrument_2 in ratio)):
            return None


        rate_diff = ratio[self.instrument_1] - ratio[self.instrument_2]
        rate_diff_1 = ratio[self.instrument_1+"1"] - ratio[self.instrument_2+"1"]

        print("rate_diff_previous_day :", rate_diff ,", rate_diff :", rate_diff_1 )

        if not abs(rate_diff) > 0.0019:
            return None


        output = rate_diff < 0
        signal_matrix[self.instrument_1] = {
                "BUY": output,
                "SELL": not output
        }

        signal_matrix[self.instrument_2] = {
                "BUY": not output,
                "SELL": output
        }

        signal_matrix["rate"] = rate_diff

        return signal_matrix

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






