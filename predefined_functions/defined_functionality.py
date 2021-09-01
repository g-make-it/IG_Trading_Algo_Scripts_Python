from trading_ig import IGService
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
from getting_historical_data.data_retrieval_historical import Data_Retrieval_Historical
from predefined_functions.initialisation import Initialisation
from get_data.get_market_data import Get_Market_Data
import time
import json
import math
import pandas


class Defined_Functionality:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.initialise_objects()

    def initialise_objects(self):
        # websockets
        self.a_dr = Data_Retrieval()
        self.t_dr = Data_Retrieval()
        self.m_dr = Data_Retrieval()
        # websockets

        self.data_map = dict()
        self.new_data_map = dict()

        self.start_distance = 100
        self.limit_distance = 0
        self.stop_distance = 10
        # when the object are created their connections are also created
        self.om = Order_Management()
        self.po = Position_Management()
        self.md = Get_Market_Data()
        self.drh = Data_Retrieval_Historical()

        self.map_epic_data = {}

    def set_epics_to_look_for(self, epic_list):
        self.map_epic_data = {}
        for item in epic_list:
            self.map_epic_data[item] = []

    def start_data_from_market_data_socket(self, list_of_epics):
        self.m_dr.create_subscription_market_data(list_of_epics)

    def start_data_from_account_and_trade_data_socket(self):
        self.a_dr.create_subscription_account()
        self.t_dr.create_subscription_trade()

    def get_quote_data_from_socket(self, epic):
        return self.m_dr.get_market_data(epic)

    def get_old_quote_data_from_socket(self, epic):
        return self.m_dr.get_old_market_data(epic)

    def get_historical_data_via_num_points(self, epic, resolution, num_points):
        return self.drh.get_historical_data_based_num_points(epic, resolution, num_points)

    def get_historical_data_historical_via_date_range(self, epic, resolution, start_date, end_date):
        return self.drh.get_historical_data_based_date_range(epic, resolution, start_date, end_date)


    def get_market_data(self, epic=None):
        data = None

        list_of_epics = self.map_epic_data.keys()
        if epic != None:
            list_of_epics = [epic]
            self.map_epic_data[epic] = []

        for epic in list_of_epics:

            data = self.md.get_details_about_epic(epic=epic)
            if data == None: continue

            self.map_epic_data[epic].append(data)

            if len(self.map_epic_data[epic]) > 20:
                self.map_epic_data[epic].pop(0)
            else:
                # anything smaller will be skipped - to get more data
                continue

        if (data != None) and (epic != None):
            return data

    # def create_working_orders(self, epic, direction):
    #     data_epic = self.md.get_details_about_epic(epic=epic)
    #     bid = data_epic["snapshot"]["bid"]
    #     offer = data_epic["snapshot"]["offer"]
    #     dealing_rules = data_epic["dealingRules"]
    #     # use offer as that's the largest
    #     stop_distance = self.po.get_margin_amount(dealing_rules=dealing_rules, current_price=offer)
    #     limit_distance = self.limit_distance
    #     size = 0.5
    #
    #     if direction == "BUY":
    #         buy_order = self.om.create_working_order(direction="BUY", epic=epic, size=size, price=bid,limit_distance=limit_distance, stop_distance=stop_distance)
    #         print(buy_order)
    #     elif direction == "SELL":
    #         sell_order = self.om.create_working_order(direction="SELL", epic=epic, size=size, price=offer, limit_distance=limit_distance, stop_distance=stop_distance)
    #         print(sell_order)
    #
    #     print("stop")


    def create_working_order(self, epic, direction, force_open, price_order_level = None, size=0.5, limits =True):
        if limits:
            data_epic = self.get_market_data(epic=epic)

            if data_epic == None:
                return None

            dealing_rules = data_epic["dealingRules"]

            if price_order_level == None:
                bid = data_epic["snapshot"]["bid"]
                ask = data_epic["snapshot"]["offer"]

                # when making a sell order you have to hit the bid here in this instance
                if direction == "SELL":
                    price_order_level = bid
                else:
                    # if we are making a buy order we have to hit the ask order - not normal limit orders
                    price_order_level = ask


            limit_distance = None
            stop_distance = None
            stop_distance = self.po.get_margin_min_distance_from_position_stop(dealing_rules=dealing_rules, current_price=price_order_level, guaranteed_stop=True)
            stop_distance += self.stop_distance
            # limit_distance = self.po.get_margin_min_distance_from_position_limit(dealing_rules=dealing_rules,current_price=price_order_level)
            # limit_distance += self.limit_distance

            if direction == "BUY":
                order = self.om.create_working_order(direction="BUY", epic=epic, size=size, price=price_order_level, limit_distance=limit_distance, stop_distance=stop_distance, force_open=force_open)
                print(order)
            elif direction == "SELL":
                order = self.om.create_working_order(direction="SELL", epic=epic, size=size, price=price_order_level, limit_distance=limit_distance, stop_distance=stop_distance, force_open=force_open)
                print(order)
        else:

            if direction == "BUY":
                order = self.om.create_working_order(direction="BUY", epic=epic, size=size, price=price_order_level, limit_distance=None, stop_distance=None,force_open=True)
                print(order)
            elif direction == "SELL":
                order = self.om.create_working_order(direction="SELL", epic=epic, size=size, price=price_order_level, limit_distance=None, stop_distance=None,force_open=True)
                print(order)

        return order



    def create_open_position(self, epic, direction, size=0.5, limits=True, force_open=False, min_limit_stop=True, guaranteed_stop=True):
        data_epic = self.md.get_details_about_epic(epic=epic)

        size = round(size, 2)

        dealing_rules = data_epic["dealingRules"]
        price_at_present = None
        if direction == "SELL":
        #     we are hitting the bid
            price_at_present = data_epic["snapshot"]["bid"]
        else:
            price_at_present = data_epic["snapshot"]["offer"]

        stop_distance = self.po.get_margin_min_distance_from_position_stop(dealing_rules=dealing_rules, current_price=price_at_present, guaranteed_stop=guaranteed_stop)
        limit_distance = self.po.get_margin_min_max_distance_from_position_limit(dealing_rules=dealing_rules, current_price=price_at_present, min_limit_stop=min_limit_stop)
        if limits:
            # stop_distance += self.stop_distance
            # for WallSt -> have changed it but didn't change the API
            # stop_distance = 15
            # limit_distance = self.limit_distance
            pass
        else:
            stop_distance = None
            limit_distance = None


        if direction == "BUY":
            position_entry = self.om.create_open_position(direction="BUY", epic=epic, size=size, limit_distance=limit_distance, stop_distance=stop_distance, force_open=force_open)
            print(position_entry)
        elif direction == "SELL":
            position_entry = self.om.create_open_position(direction="SELL", epic=epic, size=size, limit_distance=limit_distance, stop_distance=stop_distance, force_open=force_open)
            print(position_entry)
        return position_entry



    # check the local dict on the machine tracking the stop loss order - logic needs to change here
    def get_position_details(self):
        self.new_data_map = {}
        data = self.om.get_open_positions()
        if not (isinstance(data,pandas.core.series.Series) or isinstance(data,pandas.core.frame.DataFrame)):
                return data

        for i in range(data.index.size):
            data_temp = data.iloc[i]
            deal_id = data_temp["position"]["dealId"]
            self.new_data_map[deal_id] = data_temp

        # as we always add in the update or create function you only need to remove here
        keys_to_remove = (self.data_map.keys()) - (self.new_data_map.keys())
        for key in keys_to_remove:
            del(self.data_map[key])



    def find_open_position_by_epic(self,epic):
        output = self.get_position_details()
        if output == "error":
            raise Exception("error in find open position by epic")

        position_list = []
        for deal_id in self.new_data_map.keys():
            position = self.new_data_map[deal_id]
            if (position["market"]["epic"] == epic):
                position_list.append(position)

        return position_list

    def get_open_positions(self):
        output = self.get_position_details()
        if output == "error":  return output
        position_list = []
        for deal_id in self.new_data_map.keys():
            position = self.new_data_map[deal_id]
            position_list.append(position)

        return position_list

    def update_or_create_trailing_stop_loss_local_machine(self, deal_id):
        dealing_object = self.new_data_map[deal_id]
        direction = ""
        if dealing_object["position"]["direction"] ==  "SELL":
            direction = "offer"
        else:
            direction = "bid"

        price = dealing_object["market"][direction]

        if deal_id in self.data_map:
            dealing_object = self.new_data_map[deal_id]



            dealing_object["local"] = self.data_map[deal_id]["local"]

            old_price = dealing_object["local"]["price_level"]
            # if our price has gone up and we are shorting - then we need the stop limit to stay in place and so reduce the distance
            if price != old_price:

                opening_price = dealing_object["position"]["openLevel"]


                if (direction == "offer"):

                    if (price > old_price):

                        # if we are lossing money reduce the buffer
                        dealing_object["local"]["current_distance"] -= (price - old_price)

                    # gaining money keep the buffer the same and move with the price
                    dealing_object["local"]["price_level"] = price
                    new_stop_level = (price + dealing_object["local"]["current_distance"])
                    dealing_object["local"]["current_stop_level"] = new_stop_level
                    # made so when in profit the gap closes quicker to close the position
                    if opening_price > price:
                        # locking in profits
                        dealing_object = self.lockin_profits(dealing_object=dealing_object, price=price)

                # shorting
                elif (direction == "bid"):

                    if (price < old_price):
                        # if we are lossing money reduce the buffer
                        dealing_object["local"]["current_distance"] -= (old_price - price)
                    # gaining money keep the buffer the same and move with the price
                    dealing_object["local"]["price_level"] = price
                    new_stop_level = (price - dealing_object["local"]["current_distance"])
                    dealing_object["local"]["current_stop_level"] = new_stop_level
                    # made so when in profit the gap closes quicker to close the position
                    if opening_price < price:
                        dealing_object = self.lockin_profits(dealing_object=dealing_object,price=price)


        else:
            dealing_object = self.new_data_map[deal_id]
            start_distance = self.start_distance
            if direction == "offer":
                stop_level = price + start_distance
            else:
                stop_level = price - start_distance

            dealing_object["local"] = {
                "start_distance": start_distance,
                "current_distance": start_distance,
                "price_level": price,
                "current_stop_level": stop_level,
                "profit": False
            }
        print(dealing_object["local"]["current_distance"], dealing_object["market"])

        if (dealing_object["local"]["current_distance"] <= 0) :
            print("close position")
            self.close_position(deal_id=deal_id)

        return dealing_object
    # check if the local stop loss is in profit
    def lockin_profits(self, dealing_object, price):

        opening_price = dealing_object["position"]["openLevel"]
        if dealing_object["position"]["direction"] ==  "SELL":

            new_stop_level = price - dealing_object["local"]["current_distance"]
            if new_stop_level > opening_price:
                opening_price -= 0.2
                dealing_object["local"]["current_distance"] = opening_price - price
                dealing_object["local"]["current_stop_level"] = opening_price
                dealing_object["local"]["profit"] = True
        else:

            new_stop_level = price - dealing_object["local"]["current_distance"]
            if new_stop_level < opening_price:
                opening_price += 0.2
                dealing_object["local"]["current_distance"] = price - opening_price
                dealing_object["local"]["current_stop_level"] = opening_price
                dealing_object["local"]["profit"] = True

        return dealing_object



    def update_stop_level_bands(self):
        self.get_position_details()

        # for deal_id in self.new_data_map.keys():

        for key in self.new_data_map:
            # this contains the data that is saved short term
            position = self.new_data_map[key]["position"]

            self.data_map[key] = self.update_or_create_trailing_stop_loss_local_machine(deal_id=position["dealId"])
            # this contains the data that is saved long term
            object_map = self.data_map[key]
            position = object_map["position"]
            market = object_map["market"]
            local = object_map["local"]

            epic = market["epic"]

            if not(epic in self.map_epic_data) or (len(self.map_epic_data[epic]) == 0):
                self.get_market_data(epic=epic)

            direction = position["direction"]
            entered_level = position["openLevel"]
            current_price = 0
            if direction == "SELL":
                current_price = (market["offer"])
            else:
                current_price = (market["bid"])

            dealing_rules = self.map_epic_data[epic][-1]["dealingRules"]

            stop_distance = self.po.get_margin_min_distance_from_position_stop(dealing_rules=dealing_rules, current_price=current_price, guaranteed_stop=False)


            # increases its distance away
            # stop_distance = stop_distance + self.stop_distance
            limit_distance = self.po.get_margin_min_max_distance_from_position_limit(dealing_rules=dealing_rules, current_price=current_price, min_limit_stop=False)
            # true if the new price is better we amend the position
            new_levels = self.po.is_new_levels_better_and_generate(direction=direction, old_stop_level_price=position["stopLevel"], stop_distance=stop_distance, current_price=current_price, entered_price=entered_level, limit_distance=limit_distance, local=local)
            if new_levels == None:
                continue

            dealId = position["dealId"]
            limit_level = new_levels[1]
            stop_level = new_levels[0]
            # guaranteed_stop - is not implemented in this update function as it's commented out
            response = self.om.update_position(limit_level=limit_level ,stop_level=stop_level, deal_id=dealId, guaranteed_stop=False)

            print(response)
            # stop over loading on requests
            # time.sleep(1)

    def close_position(self, deal_id=None,size=None, position=None):
        if isinstance(position,pandas.core.series.Series):
            position = position["position"]

        if position != None:
            size = position["dealSize"]
        elif size == None:
            dealing_object = self.data_map[deal_id]
            position = dealing_object["position"]
            size = position["dealSize"]
        else:
            size = round(size,2)
        response = self.om.close_open_position(position=position,size=size)

        if response == None:
            print("the position has either been filled or a connection is at fault")
        print(response)
        return response

    def get_working_orders_by_epic(self, epic):
        data = self.om.get_working_orders()
        data = data[data["epic"] == epic]
        return data

    def get_working_orders(self):
        data = self.om.get_working_orders()
        return data

    def cancel_orders_by_epic(self, epic):
        data = self.om.get_working_orders()
        data = data[data["epic"] == epic]
        for deal_id in data["dealId"]:
            response = self.om.delete_working_order(deal_id=deal_id)
            print(response)


    def close_all_position(self):
        data = self.get_open_positions()
        if len(data) == 0:
            return None

        for i in range(len(data)):
            data_temp = data[i]
            response = self.close_position(position=data_temp)
            print(response)





