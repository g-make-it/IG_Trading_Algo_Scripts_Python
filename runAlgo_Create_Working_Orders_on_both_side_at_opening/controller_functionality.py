from predefined_functions.initialisation import Initialisation
from predefined_functions.algo_creating_working_orders_at_open_on_both_side import Algo0

class Controller_Functionality:
    # def __init__(self):
    #     intial = Initialisation()
    #     self.initial = intial.initialise_connection()


    def run(self):
        algo = Algo0()
        algo.run()






if __name__ == '__main__':
    # run these program independently:
    # runAlgoStopLoss: - risk management
    # runAlgo_Create_Working_Orders_on_both_side_at_opening.controller_functionality_quick_function: make's sure all orders are balanced incase the program below take too long
    # and this one    -   creates the orders and works out the signal and instruments that we create orders for
    Controller_Functionality().run()