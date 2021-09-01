from predefined_functions.initialisation import Initialisation
from predefined_functions.algo_creating_working_orders_at_open_on_both_side_quick_functions import Algo0

class Controller_Functionality:
    # def __init__(self):
    #     intial = Initialisation()
    #     self.initial = intial.initialise_connection()


    def run(self):
        algo = Algo0()
        algo.run()






if __name__ == '__main__':
    Controller_Functionality().run()