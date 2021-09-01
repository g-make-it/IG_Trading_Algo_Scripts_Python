from predefined_functions.initialisation import Initialisation
from predefined_functions.algo_opposing_position_on_sharp_price_changes_based_on_historical_data import Algo0

class Controller_Functionality:
    # def __init__(self):
    #     intial = Initialisation()
    #     self.initial = intial.initialise_connection()


    def run(self):
        algo = Algo0()
        algo.run()






if __name__ == '__main__':
    Controller_Functionality().run()