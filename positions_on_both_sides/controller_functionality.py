# from predefined_functions.defined_functionality import Defined_Functionality
from predefined_functions.initialisation import Initialisation
# from predefined_functions.algo_ten_minute import Algo0     -- old one
# from predefined_functions.algo_minute_on_quotes import Algo0  -- old one
from predefined_functions.algo_positions_on_both_sides import Algo0
# from predefined_functions.algo_catch_trends_from_different_markets import Algo0
# from predefined_functions.algo_arbitration_between_two_instruments import Algo0

class Controller_Functionality:
    def __init__(self):
        intial = Initialisation()
        self.initial = intial.initialise_connection()


    def run(self):
        algo = Algo0()
        algo.run()
        pass










if __name__ == '__main__':

    Controller_Functionality().run()