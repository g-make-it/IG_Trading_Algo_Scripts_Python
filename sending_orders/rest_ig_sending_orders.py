#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
IG Markets REST API sample with Python
2015 FemtoTrader
"""

from trading_ig import IGService
from trading_ig.config import config
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# if you need to cache to DB your requests
from datetime import timedelta
import requests_cache


def main():
    logging.basicConfig(level=logging.DEBUG)

    expire_after = timedelta(hours=1)
    session = requests_cache.CachedSession(
        cache_name='cache', backend='sqlite', expire_after=expire_after
    )
    # set expire_after=None if you don't want cache expiration
    # set expire_after=0 if you don't want to cache queries

    #config = IGServiceConfig()

    # no cache
    ig_service = IGService(
        config.username, config.password, config.api_key, config.acc_type
    )

    # if you want to globally cache queries
    #ig_service = IGService(config.username, config.password, config.api_key, config.acc_type, session)

    ig_service.create_session()

    accounts = ig_service.fetch_accounts()
    print("accounts:\n%s" % accounts)
    """
    # - as it is set to default ift no longer needed gets the account to the spread betting one , the one specified in the config file
    ig_service.switch_account(account_id=config.acc_number, default_account=True)
    """

    #open_positions = ig_service.fetch_open_positions()
    #print("open_positions:\n%s" % open_positions)

    print("")

    working_orders = ig_service.fetch_working_orders()
    print("working_orders:\n%s" % working_orders)

    print("")

    currency_code = "GBP"
    direction = "BUY"
    epic = "IX.D.FTSE.DAILY.IP"
    expiry = "DFB"
    guaranteed_stop = False
    # entering price
    level = 6801.3
    # Pound per point size
    size = 1
    time_in_force = "GOOD_TILL_CANCELLED"
    # limit orders are now called STOP
    order_type = "STOP"
    limit_distance = None
    stop_distance = 160

    # """Creates an OTC working order"""
    response = ig_service.create_working_order(
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
        stop_distance=stop_distance
    )

    # ig_service.create_working_order(
    #     currency_code="GBP",
    #     direction="BUY",
    #     epic="CS.D.BITCOIN.TODAY.IP",
    #     expiry="DFB",
    #     force_open=True,
    #     guaranteed_stop=True,
    #     stop_distance=1100.0,
    #     size=0.50,
    #     time_in_force="GOOD_TILL_CANCELLED",
    #     order_type="LIMIT",
    #     limit_distance=1000.0,
    #     level=1000.0)


    print("")

    working_orders = ig_service.fetch_working_orders()
    print("working_orders:\n%s" % working_orders)


    # response is a dict -> response["price"] -> DataFrame (Multi-level df)-> so df = response["price"]
    # df -> df["ask"] -> Open,High,Low,Close
    # df -> df["bid"] -> Open,High,Low,Close
    # df -> df["last"] -> but these are usually None values = (Open,High,Low,Close)
    print(response)
    # Exception: error.public-api.exceeded-account-historical-data-allowance

    # if you want to cache this query
    #response = ig_service.fetch_historical_prices_by_epic_and_num_points(epic, resolution, num_points, session)

    #df_ask = response['prices']['ask']
    #print("ask prices:\n%s" % df_ask)

    #(start_date, end_date) = ('2015-09-15', '2015-09-28')
    #response = ig_service.fetch_historical_prices_by_epic_and_date_range(epic, resolution, start_date, end_date)

    # if you want to cache this query
    #response = ig_service.fetch_historical_prices_by_epic_and_date_range(epic, resolution, start_date, end_date, session)
    #df_ask = response['prices']['ask']
    #print("ask prices:\n%s" % df_ask)



    # check this out and see what you can do to get all the market data information



if __name__ == '__main__':
    main()
