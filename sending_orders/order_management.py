from trading_ig import IGService
from trading_ig.config import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# if you need to cache to DB your requests
from datetime import timedelta
import requests_cache

from predefined_functions.initialisation import Initialisation

class Order_Management():
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.log = logging.getLogger(__name__)
        # set object and then set connection
        self.initial = Initialisation()
        self.initialise_connection()

    def initialise_connection(self):
        self.ig_service = self.initial.initialise_connection()
        self.ig_service.create_session()

    # limit orders
    def create_working_order(self, direction, epic, size, price, stop_distance,limit_distance,force_open=False):
        currency_code = "GBP"
        direction = direction
        epic = epic
        expiry = "DFB"
        if force_open == True:
            guaranteed_stop = False
        else:
            guaranteed_stop = True
        # entering price
        level = price
        # Pound per point size
        size = size
        time_in_force = "GOOD_TILL_CANCELLED"
        # LIMIT orders are now STOP
        order_type = "STOP"
        limit_distance = limit_distance
        stop_distance = stop_distance

        # currency_code = "GBP"
        # direction = "SELL"
        # epic = "CS.D.BITCOIN.TODAY.IP"
        # expiry = "DFB"
        # guaranteed_stop = False
        # # entering price
        # level = 13109
        # # Pound per point size
        # size = 0.50
        # time_in_force = "GOOD_TILL_CANCELLED"
        # order_type = "LIMIT"
        # limit_distance = 4000.0
        # stop_distance = 160.0

        # """Creates an OTC working order"""

        try:
            response = self.ig_service.create_working_order(
                currency_code=currency_code,
                direction=direction,
                epic=epic,
                expiry=expiry,
                guaranteed_stop=guaranteed_stop,
                level=level,
                size=size,
                time_in_force=time_in_force,
                order_type=order_type,
                limit_distance=limit_distance,
                stop_distance=stop_distance,
                force_open=force_open
            )

            return response
        except Exception as e:
            self.log.info(str(e) + " error occurred when creating a working order")
        return None

    # market orders
    def create_open_position(self, direction, epic, size, limit_distance, stop_distance, force_open):
        currency_code = "GBP"
        direction = direction
        epic = epic
        expiry = "DFB"
        # no matter what you are doing force open always has to be True other wise stop losses do not work
        force_open = force_open
        if force_open:
            guaranteed_stop = False
        else:
            guaranteed_stop = True

        stop_distance = stop_distance
        size = size
        trailing_stop = False
        trailing_stop_increment = None
        trailing_stop_distance = None
        time_in_force = "FILL_OR_KILL"
        order_type = "MARKET"
        limit_distance = limit_distance

        try:
            response = self.ig_service.create_open_position(
                currency_code=currency_code,
                direction=direction,
                epic=epic,
                expiry=expiry,
                # no matter what you are doing force open always has to be True other wise stop losses do not work
                force_open=True,
                guaranteed_stop=guaranteed_stop,
                stop_distance=stop_distance,
                size=size,
                trailing_stop=trailing_stop,
                trailing_stop_increment=trailing_stop_increment,
                # trailing_stop_distance = trailing_stop_distance,
                # time_in_force=time_in_force,
                order_type=order_type,
                limit_distance=limit_distance)

            return response
        except Exception as e:
            self.log.info(str(e) + " error occurred when opening a position")
        return None

    # market orders to close positions
    def close_open_position(self, position, size):
        # set randomly
        try:
            direction = "BUY"
            position_direction = position["direction"]
            if position_direction == "BUY":
                direction = "SELL"

            deal_id = position["dealId"]
            order_type = "MARKET"
            size = size

            response = self.ig_service.close_open_position(
                deal_id=deal_id,
                direction=direction,
                order_type=order_type,
                size=size)

            return response
        except Exception as e:
            self.log.info(str(e) + " error occurred when closing position")
        return None

    def delete_working_order(self, deal_id):
        try:
            deal_id = deal_id
            response = self.ig_service.delete_working_order(deal_id)
            return response
        except Exception as e:
            self.log.info(str(e) + " error occurred when deleting working order")
        return None


    def update_position(self, limit_level, stop_level, deal_id, guaranteed_stop):
        limit_level = limit_level
        guaranteed_stop = guaranteed_stop
        stop_level=stop_level
        deal_id=deal_id
        trailing_stop = False
        trailing_stop_distance = None
        trailing_stop_increment = None

        try:

            response = self.ig_service.update_open_position(
                limit_level=limit_level,
                stop_level=stop_level,
                # guaranteed_stop=guaranteed_stop,
                deal_id =deal_id,
                # trailing_stop=trailing_stop,
                # trailing_stop_distance=trailing_stop_distance,
                # trailing_stop_increment=trailing_stop_increment
            )

            return response

        except Exception as e:
            self.log.info(str(e) + " error occurred when updating position or maybe the order is no longer open")
        return None

    def get_open_positions(self):
        while(True):
            try:
                return self.ig_service.fetch_open_positions()
            except Exception as e:
                self.log.info(str(e) + " error occurred when getting open positions")
                # resets the connection
                self.initialise_connection()


    def get_working_orders(self):
        while(True):
            try:
                return self.ig_service.fetch_working_orders()
            except Exception as e:
                self.log.info(str(e) + " error occurred when getting working orders")
                self.initialise_connection()
