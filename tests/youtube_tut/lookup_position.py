from predefined_functions.defined_functionality import Defined_Functionality
import time


df = Defined_Functionality()

# # order = df.create_open_position(epic="IX.D.NASDAQ.CASH.IP", direction="BUY",size=1, force_open=True)
# order = df.create_open_position(epic="IX.D.NASDAQ.CASH.IP", direction="BUY",size=1, force_open=True, guaranteed_stop=False, min_limit_stop=False)
# # if you have force_open == True = limits for your orders will not work - and it will throw you an error - order being rejected
#
# print("stop")

positions_list = df.get_open_positions()

print("stop")


# while(True):
#     positions_list = df.get_open_positions()
#     print((positions_list[0])["position"]["openLevel"] - (positions_list[0])["market"]["offer"])
#     time.sleep()