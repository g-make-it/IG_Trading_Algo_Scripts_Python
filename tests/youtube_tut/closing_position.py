from predefined_functions.defined_functionality import Defined_Functionality


df = Defined_Functionality()


position = df.create_open_position(epic="IX.D.NASDAQ.CASH.IP", direction="BUY",size=1, force_open=True, guaranteed_stop=False, min_limit_stop=False)
positions = df.get_open_positions()
print("stop")
output = df.close_position(position=positions[0])
print("stop")
