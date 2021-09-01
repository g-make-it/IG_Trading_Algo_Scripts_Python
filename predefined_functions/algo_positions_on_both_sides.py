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
import pandas
import traceback


# the newest one where you make market order base on price movements 5 or more and try to catch the trend

class Algo0:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.df = Defined_Functionality()

        # list_of_epics = ['IX.D.DOW.DAILY.IP']
        list_of_epics = ['IX.D.SPTRD.DAILY.IP']
        # list_of_epics = ['CS.D.ETHUSD.TODAY.IP']

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

        self.average_closing_price= {
            "SELL":0,
            "BUY":0
        }

        self.opening_price = {
            "SELL":0,
            "BUY":0
        }

        self.initial_position_size_limit = 0

        self.df.start_data_from_market_data_socket(list_of_epics[-1])
        self.df.start_data_from_account_and_trade_data_socket()
        # time to build up some data
        time.sleep(5)

    # def setup(self):
    #     # not required as we are not trailing any losses
    #     # time.sleep(2)
    #     # self.df.update_stop_level_bands()

    def run(self):

        while (True):
            try:
                # self.setup()
                # stop for a 10 minute for data to be more impact full
                time.sleep(60*10)

                for epic in self.map_epic_data_minute.keys():

                    position = self.create_initial_position(epic=epic)
                    signals_and_levels = self.signal_generation(epic=epic)
                    if position == "error": continue
                    self.closing_incrments(position=position,signals=signals_and_levels)

            except Exception as e:
                print(e, "   error in the algo")

                traceback.print_exc()




    def create_initial_position(self, epic):
        position = self.df.find_open_position_by_epic(epic=epic)

        if position == "error":
            return position

        if len(position) == 1:
            return position

        if self.initial_position_size_limit != 0:
            return position

        if len(position) >= 2:
            if self.average_closing_price["SELL"] == 0:
                for single_position in position:
                    direction = single_position["position"]["direction"]
                    epic = single_position["market"]["epic"]
                    opening_price = single_position["position"]["openLevel"]
                    self.opening_price[direction] = opening_price

                    if direction == "SELL":
                        self.average_closing_price["SELL"] = opening_price
                    elif direction == "BUY":
                        self.average_closing_price["BUY"] = opening_price
                self.initial_position_size_limit = position[0]["position"]["dealSize"]/2.0
            return position


        create_position_sell = self.df.create_open_position(epic=epic, direction="SELL", size=1, limits=False,force_open=True)
        create_position_buy = self.df.create_open_position(epic=epic, direction="BUY", size=1, limits=False, force_open=True)
        self.closing_increments = []

        position = self.df.find_open_position_by_epic(epic=epic)

        for single_position in position:
            direction = single_position["position"]["direction"]
            epic = single_position["market"]["epic"]
            opening_price = single_position["position"]["openLevel"]
            self.opening_price[direction] = opening_price

            # if direction == "SELL":
            #     self.average_closing_price["SELL"] = opening_price
            # elif direction == "BUY":
            #     self.average_closing_price["BUY"] = opening_price

        self.initial_position_size_limit = position[0]["position"]["dealSize"]/2.0

        return position


    def closing_incrments(self, position, signals):

        if signals == None: return
        boolean2 = False
        spacer = 0.60
        spacer_multiplier ={
            "BUY":1,
            "SELL":1
        }
        closing_size = 0.05

        if len(position) == 0:
            self.initial_position_size_limit = 0
            return

        data = self.df.get_quote_data_from_socket(epic=position[0]["market"]["epic"])

        if len(position) < 2:
            size = position[0]["position"]["dealSize"]
            closing_increment = self.df.close_position(size=size, position=position[0])
            self.closing_increments.append(closing_increment)
            self.calculate_average_closed()



        if len(position) > 1:
            size_0 = position[0]["position"]["dealSize"]
            direction_0 = position[0]["position"]["direction"]
            size_1 = position[1]["position"]["dealSize"]
            direction_1 = position[1]["position"]["direction"]
            # smaller than half and smaller then the other increase spacer
            if (size_1 < self.initial_position_size_limit) or (size_0 < self.initial_position_size_limit):
                if size_0 == size_1:
                    self.initial_position_size_limit = self.initial_position_size_limit/2.0

                abs_size_diff = abs(size_1 - size_0) * 10
                if (size_1 > size_0):
                    spacer_multiplier[direction_0] = 10 * abs_size_diff
                elif (size_0 > size_1):
                    spacer_multiplier[direction_1] = 10 * abs_size_diff



        for single_position in position:
            direction = single_position["position"]["direction"]
            # epic = single_position["market"]["epic"]
            # opening_price = single_position["position"]["openLevel"]
            #
            # size = single_position["position"]["dealSize"]

            # # if you have exit hal way wait for the other side and if you both have met half way miss one opportunity
            # if size <= self.initial_position_size_limit:
            #     boolean_met_size_limit = boolean_met_size_limit and True
            #     continue
            # else:
            #     boolean_met_size_limit = False

            # data = self.df.get_market_data(epic=epic)
            bid = data["BID"]
            offer = data["OFFER"]

            closing_increment = None

            # going long
            if direction == "BUY":
                # as you want to exit out of the direction you are in
                boolean1 = signals["SELL"]
                '''
                This tells us if the new exit ordered fills are low enough as a average that we can still make profit exiting out 
                '''
                # boolean3 = self.average_closing_price["BUY"] < (bid - spread)

                if boolean1:
                    if len(self.closing_increments) != 0:
                        previous_closing_increments = self.closing_increments[-1]
                        if previous_closing_increments["level"] < (bid-(spacer*spacer_multiplier[direction]) ):
                            closing_increment = self.df.close_position(size=closing_size, position=single_position)
                    else:
                        if self.opening_price[direction] < (bid-(spacer*spacer_multiplier[direction]) ):
                            closing_increment = self.df.close_position(size=closing_size,position=single_position)
                    if closing_increment != None:
                        # as we are closing with a sell fill
                        self.closing_increments.append(closing_increment)
                        self.calculate_average_closed()

            # shorting
            elif direction == "SELL":
                # as you want to exit out of the direction you are in
                boolean1 = signals["BUY"]

                '''
                This tells us if the new exit ordered fills are high enough as a average that we can still make profit exiting out 
                '''
                # boolean3 = self.average_closing_price["SELL"] > (offer + spread)

                if boolean1 :
                    if len(self.closing_increments) != 0:
                        previous_closing_increments = self.closing_increments[-1]
                        if previous_closing_increments["level"] > (offer+(spacer*spacer_multiplier[direction]) ):
                            closing_increment = self.df.close_position(size=closing_size, position=single_position)
                    else:
                        if self.opening_price[direction] > (offer+(spacer*spacer_multiplier[direction]) ):
                            closing_increment = self.df.close_position(size=closing_size,position=single_position)
                    if closing_increment != None:
                        # as we are closing with a buy fill
                        self.closing_increments.append(closing_increment)
                        self.calculate_average_closed()

        # if boolean_met_size_limit:
            # self.initial_position_size_limit = (self.initial_position_size_limit/2.0)
        return None

    def calculate_average_closed(self):
        list_of_closing_fills = self.closing_increments
        total_volume = 0
        total_price = 0
        total_profit = 0
        total_price_volume = 0
        for fill in list_of_closing_fills:
            total_profit += fill["profit"]
            total_price += fill["level"]
            total_volume += fill["size"]
            total_price_volume += (fill["size"] * fill["level"])

        print(total_profit)




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






