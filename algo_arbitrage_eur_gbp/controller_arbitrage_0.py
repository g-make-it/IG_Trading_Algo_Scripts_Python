from predefined_functions.initialisation import Initialisation
# from algo_arbitrage.trianglar_arbitrage_spreadbetting import Algo0
from algo_arbitrage_eur_gbp.trianglar_arbitrage_spreadbetting_exiting_out_incrementally import Algo0

class Controller_Functionality:
    # def __init__(self):
    #     intial = Initialisation()
    #     self.initial = intial.initialise_connection()


    def run(self):
        EURGBP = "CS.D.EURGBP.TODAY.IP"
        GBPEUR = "CS.D.GBPEUR.TODAY.IP"
        algo = Algo0(EURGBP=EURGBP, GBPEUR=GBPEUR)
        algo.run()






if __name__ == '__main__':
    Controller_Functionality().run()