import time
import sys
import traceback
import logging
import math

from trading_ig import (IGService, IGStreamService)
from trading_ig.config import config
from trading_ig.lightstreamer import Subscription
from predefined_functions.initialisation import Initialisation

class Data_Retrieval:
    def __init__(self):
        logging.basicConfig(level=logging.INFO)
        self.log = logging.getLogger(__name__)
        self.ig_stream_service = []
        self.data_map = {}
        self.initial = Initialisation()

    def initialise_connection(self, number_of_subscriptions):
        # logging.basicConfig(level=logging.DEBUG)
        for index in range(number_of_subscriptions):
            while(True):
                try:
                    ig_service = self.initial.initialise_connection()

                    self.ig_stream_service.append(IGStreamService(ig_service))
                    ig_session = self.ig_stream_service[index].create_session()
                    self.accountId = config.acc_number
                    self.ig_stream_service[index].connect(self.accountId)
                    # it will automatically create the account connection
                    break
                except Exception as e:
                    print(e, " data retrieval error login")


    def restart_service(self):
        while(True):
            try:
                self.ig_stream_service.unsubscribe_all()
                self.initialise_connection()
                return
            except Exception as e:
                self.log.info(str(e) + "  connection error")


    # market data based info
    def create_subscription_market_data(self, data):
        number_of_subscriptions = math.ceil(len(data)/30)
        if number_of_subscriptions > 38:
            raise Exception("your account could be blocked, too many subscriptions ")
        self.initialise_connection(number_of_subscriptions)
        list_of_epics_in_sets_30 = list(self.chunks(data, 30))

        for index in range(len(list_of_epics_in_sets_30)):
            self.create_individual_subscription_market_data(list_of_epics_in_sets_30[index], index)


    def chunks(self,lst, n):
        """Yield successive n-sized chunks from lst."""
        for i in range(0, len(lst), n):
            yield lst[i:i + n]


    def create_individual_subscription_market_data(self,data,index):
        # if len(self.ig_stream_service.ls_client._subscriptions) > 0:
        #     #reset everything market data based
        #     self.restart_service()

        subscription_holding = self.create_subscription_subPrice(data)
        self.ig_stream_service[index].ls_client.subscribe(subscription_holding)


    # account and trade based info
    def create_subscription_account(self):
        self.initialise_connection(1)
        subscription_holding = self.create_subscription_subAccount()
        self.ig_stream_service[0].ls_client.subscribe(subscription_holding)

    def create_subscription_trade(self):
        self.initialise_connection(1)
        subscription_holding = self.create_subscription_subTradeInfo()
        self.ig_stream_service[0].ls_client.subscribe(subscription_holding)


    # done like this for debugging purposes
    def register_subscription(self, subscription):
        sub_key_prices = self.ig_stream_service.ls_client.subscribe(subscription)
        return sub_key_prices



    # subscription functions
    def create_subscription_subAccount(self):

        subscription_account = Subscription(
            mode="MERGE",
            items=['ACCOUNT:' + self.accountId],
            fields=[
                "AVAILABLE_CASH",
                "PNL",
                "PNL_LR",
                "PNL_NLR",
                "FUNDS",
                "MARGIN",
                "MARGIN_LR",
                "AVAILABLE_TO_DEAL",
                "EQUITY",
                "EQUITY_USED"],
        )

        #    #adapter="QUOTE_ADAPTER")

        # Adding the "on_balance_update" function to Subscription
        subscription_account.addlistener(self.on_account_update)
        return subscription_account

    def create_subscription_subTradeInfo(self):

        subscription_trade = Subscription(

            mode="DISTINCT",
            items=['TRADE:' + self.accountId],
            fields=[
                "CONFIRMS",
                "OPU",
                "WOU"],
        )

        subscription_trade.addlistener(self.on_trade_update)
        return subscription_trade

    def create_subscription_subPrice(self, epic_temp):
        # Making a new Subscription in MERGE mode
        epic_list = list.copy(epic_temp)
        for index in range(len(epic_list)):
            epic_list[index] = "L1:"+epic_list[index]

        subscription_prices = Subscription(
            mode="MERGE",
            items=epic_list,
            fields=["UPDATE_TIME",
                    "BID",
                    "OFFER",
                    "CHANGE",
                    "MARKET_STATE",
                    "MID_OPEN",
                    "HIGH",
                    "LOW",
                    "CHANGE",
                    "CHANGE_PCT",
                    "MARKET_DELAY"]
        )
        #
        # CHANGE_PCT
        # UPDATE_TIME
        # MARKET_DELAY    Delayed price (0=false, 1=true)
        # MARKET_STATE

        subscription_prices.addlistener(self.on_prices_update)
        return subscription_prices


    # function to catch update in events
    def on_prices_update(self, item_update):
        # print("price: %s " % item_update)
        name = item_update["name"].split(":")[1]

        if not name in self.data_map:
            self.data_map[name] = []
        for items in item_update["values"]:
            try:
                item_update["values"][items] = float(item_update["values"][items])
            except:
                pass

        self.data_map[name].append(item_update["values"])

        if len(self.data_map[name]) > 20:
            # remove only keep the latest 20 items
            self.data_map[name] = self.data_map[name][-20:]


        # print("{stock_name:<19}: Time {UPDATE_TIME:<8} - "
        #       "Bid {BID:>5} - Ask {OFFER:>5}".format(
        #     stock_name=item_update["name"], **item_update["values"]
        # ))

    def on_account_update(self, balance_update):
        name = "account"
        if not name in self.data_map:
            self.data_map[name] = []
            self.data_map[name].append(balance_update)

        if len(self.data_map[name]) > 20:
            # remove only keep the latest 20 items
            self.data_map[name] = self.data_map[name][-20:]

        # print("balance: %s " % balance_update)

    def on_trade_update(self, trade_update):
        name = "trade"
        if not name in self.data_map:
            self.data_map[name] = []
            self.data_map[name].append(trade_update)

        if len(self.data_map[name]) > 20:
            # remove only keep the latest 20 items
            self.data_map[name] = self.data_map[name][-20:]

        # print("trade: %s " % trade_update)


    # get the latest data
    def get_market_data(self, epic):
        if epic in self.data_map:
            return self.data_map[epic][-1]

    def get_old_market_data(self, epic):
        if epic in self.data_map:
            if len(self.data_map[epic]) >= 19:
                return self.data_map[epic][0]

    def get_trade_data(self):
        if "trade" in self.data_map:
            return self.data_map["trade"][-1]
        else:
            return None

    def get_account_data(self):
        if "account" in self.data_map:
            return self.data_map["account"][-1]
        else:
            return None