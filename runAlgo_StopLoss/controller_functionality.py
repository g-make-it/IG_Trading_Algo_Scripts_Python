from predefined_functions.initialisation import Initialisation
from predefined_functions.algo_close_positons_in_profit import Algo0

class Controller_Functionality:
    # def __init__(self):
    #     intial = Initialisation()
    #     self.initial = intial.initialise_connection()


    def run(self):
        algo = Algo0()
        algo.run()






if __name__ == '__main__':
    Controller_Functionality().run()