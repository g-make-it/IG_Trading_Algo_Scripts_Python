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
        self.dataframe = self.setup_dataframe()

        self.number_orders = 40

    def setup_dataframe(self):
        # add this to this machine
        path = "D:/Stock_Analysis/ig-markets-api-python-library-master/Data/SpreadBetting/All_instrument_data_added.csv"
        dataframe = pd.read_csv(path)
        dataframe.rename(columns={"Unnamed: 0": "Number"},inplace=True)
        dataframe = dataframe.set_index("Number")
        sorted_data = dataframe

        sorted_data["average"] = (sorted_data["bid"] + sorted_data["offer"]) / 2.0
        sorted_data["spread"] = sorted_data["offer"] - sorted_data["bid"]
        sorted_data["diff_high-low"] = sorted_data["high"] - sorted_data["low"]
        sorted_data["percent_spread-hl"] = (sorted_data["spread"] / sorted_data["diff_high-low"] * 100)
        # the 1 at the end is the position size we will be taking
        sorted_data["margin_required_simple"] = sorted_data["average"] * (sorted_data["marginFactor"]/100) * 1
        # FTSE indice instrument - don't allow you to close your positions
        sorted_data["percent_spread_offer"] = sorted_data["spread"] / sorted_data["offer"] * 100

        # sorted_data = sorted_data[~((sorted_data["name"].str.contains("CALL")) | (sorted_data["name"].str.contains("PUT")) | (sorted_data["name"].str.contains("Leverage")) | (sorted_data["name"].str.contains("Boost")) | (sorted_data["name"].str.contains("FTSE")) )]
        # could look into options when they are about to expire the price movements for them should be high
        sorted_data = sorted_data[~( (sorted_data["name"].str.contains("FTSE")) )]

        sorted_data = sorted_data[(sorted_data["percent_spread_offer"] != 0)]
        sorted_data = sorted_data.sort_values(by="percent_spread_offer")
        sorted_data = sorted_data[(sorted_data["percent_spread_offer"] < 0.05)]



        # final_table = sorted_data[(sorted_data["margin_required_simple"] != 0)
        #                           & (sorted_data["margin_required_simple"] < 10000)
        #                           & (sorted_data["percent_spread-hl"] < 10)
        #                           & (sorted_data["percent_spread-hl"] > 0 )
        #                           & (sorted_data["percent_spread_offer"] > 0)
        #                           & (sorted_data["percent_spread_offer"] < 0.05)]

        final_table = sorted_data[(sorted_data["margin_required_simple"] < 1000)
                    & (sorted_data["percent_spread_offer"] < 0.3)]

        return final_table


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

        # print("delete orders")
        self.df.cancel_orders_by_epic(epic=epic)
        created_order = False

        return created_order


    def signal_generation(self):

        data = self.dataframe
        final_df = pd.DataFrame()
        # filtering the dataframe
        times = data["openingHours"].unique()
        times_list = times.tolist()

        for index in range(len(times_list)):
            # removing nan values
            if not isinstance(times_list[index], str):
                del(times_list[index])
                break

        times_list.sort()
        nearest_time_interval = None
        previous_time = sys.maxsize

        details_to_create_orders_for = []

        for interval in times_list:

            map_of_time = eval(interval)
            single_time = map_of_time["marketTimes"][0]["openTime"]
            opening_market_time = datetime.strptime(single_time, '%H:%M').time()
            diff_in_time = datetime.combine(date.today(), opening_market_time) - datetime.now()
            # if the time is bigger than x second then we can still put orders in place

            total_seconds = diff_in_time.total_seconds()
            if previous_time < total_seconds:
                break
            # 5 minutes before the market opens, orders can be placed
            if total_seconds > 300:
                nearest_time_interval = single_time
                previous_time = diff_in_time.total_seconds()

        if nearest_time_interval != None:
            sub_data = data[data["openingHours"].str.contains("{'openTime': '" + nearest_time_interval, na=False)]


            # """ for some reason Ig think these markets open again """
            single_time = "09:00"
            time_interval_limit = datetime.strptime(single_time, '%H:%M').time()
            diff_in_time = datetime.combine(date.today(), time_interval_limit) - datetime.now()

            if diff_in_time.total_seconds() < 0:
                sub_data = sub_data[~((sub_data["name"].str.contains("All Sessions")) )]


            sub_data = sub_data.sort_values(by="percent_spread_offer", ascending=True)
            # also maybe remove NON DFB instruments
            # sort the dataframe by percentage spread and margin required, that way larger moving instruments with low prices are chosen first



            for index in range(sub_data["epic"].size):

                epic = sub_data.iloc[index]["epic"]

                orders_present = self.checking_working_order_is_present_under_epic_and_amend_orders(epic=epic)
                if orders_present == True:
                    continue
                try:
                    price_data = self.df.get_market_data(epic=epic)
                except Exception as e:
                    print(e)
                    continue


                if price_data == None: continue
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
                    continue

                if spread == 0:
                    data = self.df.get_historical_data_via_num_points(epic=epic,resolution="1Min", num_points=1)

                    if not isinstance(data, pd.core.frame.DataFrame):
                        continue

                    if not ("last" in data and "bid" in data):
                        continue

                    ask = data["last"]["Close"].max()
                    bid = data["bid"]["Close"].max()

                    if (math.isnan(ask) or math.isnan(bid)):
                        continue

                # ideal size margin - original was : 200 - stay with 200 , 400 doesn't have the same affect
                ideal_margin_for_each_order = 200

                spread = ask - bid
                spread_to_quotes = (spread / ask)*100
                average = (ask+bid) /2.0
                margin_required = smallest_size * average * margin_factor
                if margin_factor == 0 or average == 0 or smallest_size == 0:
                    print("stop")
                size_required = (ideal_margin_for_each_order/margin_factor)/average
                size_required = round(size_required,2)

                if (size_required < smallest_size):
                    continue
                # we are increasing the size to see if the profit increases if the position size increases whilst keeping  the instruments the same
                size_required *= 2


                # was 0.1
                if spread_to_quotes < 0.3:

                    # info might not be useful at all ----------------------------------------------------------------- -do some work on this
                    # data = self.df.get_historical_data_via_num_points(epic=epic, resolution="1D", num_points=20)
                    #
                    # if not isinstance(data, pd.core.frame.DataFrame):
                    #     continue
                    #
                    # if not ("last" in data and "bid" in data):
                    #     continue
                    # data["bid", "previous_day_close"] = data["bid"]["Close"].shift(1)
                    # data["bid", "diff_of_price_change"] = (data["bid", "Open"] - data["bid", "previous_day_close"])
                    # # 1 used to get rid of nan value at the front
                    # positive_diff = abs(data["bid", "diff_of_price_change"][1:])
                    # does_price_move_more_than_spread = (positive_diff > (spread)).all()
                    #
                    # if does_price_move_more_than_spread == False:
                    #     continue
                    #  - might not be useful at all -------------------------------------------------------------------
                    #instrument is good to trade



                    # 4 weeks of data
                    """need to change the end number to 20"""
                    data = self.df.get_historical_data_via_num_points(epic=epic, resolution="1D", num_points=20)

                    if not isinstance(data, pd.core.frame.DataFrame):
                        continue

                    if not ("last" in data and "bid" in data):
                        continue
                    data["bid", "previous_day_close"] = data["bid"]["Close"].shift(1)
                    data["bid", "diff_of_price_change"] = (data["bid", "Open"] - data["bid", "previous_day_close"])
                    # 1 used to get rid of nan value at the front
                    positive_diff = abs(data["bid", "diff_of_price_change"][1:])
                    
                    # percentage_opening_moving_larger_than_spread = (positive_diff[positive_diff > (spread)].index.size / positive_diff.index.size) * 100
                    """we are timings spread by 2 here """
                    percentage_opening_moving_larger_than_spread = (positive_diff[positive_diff > (spread * 1.1)].index.size / positive_diff.index.size) * 100

                    print(percentage_opening_moving_larger_than_spread)
                    # if the percentage is bigger than 80% then we can say this happens frequently and so we can place working orders here
                    # if percentage_opening_moving_larger_than_spread < 90:
                    #     continue
                    # making the spread wider use to be 10 - dividing by a smaller number means the spread is larger
                    bid = bid - (spread/5)
                    ask = ask + (spread/5)

                    object_map ={
                                "epic": epic,
                                "bid": bid,
                                "ask": ask,
                                # to make the sizes for this larger but still keep these small instruments
                                "size": size_required,
                                "percent_opening_close": percentage_opening_moving_larger_than_spread
                            }

                    details_to_create_orders_for.append(object_map)

                # # this part is taking way to long to go through too many instruments ---------------------------------------------------


            diff_in_time = datetime.combine(date.today(), opening_market_time) - datetime.now()

            # if there is 2 minutes left until the market opens then stop placeing orders incase the section above take too long to process
            if diff_in_time.total_seconds() > 120:

                final_df = pd.DataFrame(details_to_create_orders_for)
                if final_df.index.size == 0:
                    return final_df
                final_df = final_df.sort_values(by="percent_opening_close", ascending=False)
                final_df = final_df[:self.number_orders]
                # temp_df = temp_df[temp_df["percent_opening_close"] > 60]



        return final_df

            
            
        
        

