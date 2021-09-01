from predefined_functions.defined_functionality import Defined_Functionality


df = Defined_Functionality()

orders = df.get_working_orders()

df.cancel_orders_by_epic("IX.D.NASDAQ.CASH.IP")

print("stop")
