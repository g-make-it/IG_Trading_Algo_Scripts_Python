from predefined_functions.defined_functionality import Defined_Functionality
from datetime import datetime
import pandas as pd

class Algo0:
    def __init__(self):
        self.df = Defined_Functionality()

        self.list_of_epics = ['IX.D.DOW.DAILY.IP']
        self.df.set_epics_to_look_for(epic_list=self.list_of_epics)

        self.map_epic_data_minute={}
        for epic in self.list_of_epics:
            self.map_epic_data_minute[epic] = []

        self.first_timestamp = None



    def run(self):

        while(True):
            try:
                epic = self.list_of_epics[0]
                signals = self.signal_generation(epic)
                self.create_positions(epic=epic, signals_levels=signals)
                self.closing_positions(epic=epic, signals= signals)

            except Exception as e:
                print(e, "   error in the looping for the defined_functionality")

    def closing_positions(self, epic, signals):
        position = self.df.find_open_position_by_epic(epic=epic)

        if len(position) == 0:
            return

        if isinstance(position[0],pd.core.series.Series):
            if signals == None:
                return

            if (signals["BUY"] != None and (position[0]["position"]["direction"] != "BUY")):
                self.df.close_position(position=position[0])

            elif (signals["SELL"] != None and (position[0]["position"]["direction"] != "SELL")):
                self.df.close_position(position=position[0])

    def create_positions(self, epic, signals_levels):
        if signals_levels == None:
            return
        key = None
        if signals_levels["BUY"] != None:
            key = "BUY"
        elif signals_levels["SELL"] != None:
            key = "SELL"


        position = self.df.find_open_position_by_epic(epic=epic)

        if len(position) != 0:
            return position


        create_position = self.df.create_open_position(epic=epic, direction=key, size=0.5)

        return create_position


    def signal_generation(self, epic):
        signals_levels = None
        # minute_10 = 60 * 10
        # minute_10 = 60
        minute_10 = 1
        datetime_now = datetime.now()
        data = None

        if (self.first_timestamp != None):
            difference = (datetime_now - self.first_timestamp)

            if (difference.seconds > minute_10):
                data = self.df.get_market_data(epic=epic)
                self.first_timestamp = datetime_now
                self.map_epic_data_minute[epic].append(data)

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

            # if offer_diff > 0.1:
            buy_level = 1
            # elif bid_diff < -0.1:
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


