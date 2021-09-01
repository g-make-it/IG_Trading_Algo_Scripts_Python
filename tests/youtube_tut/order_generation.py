from predefined_functions.defined_functionality import Defined_Functionality


df = Defined_Functionality()

order = df.create_working_order(epic="IX.D.NASDAQ.CASH.IP", direction="BUY",size=1, force_open=True)
# if you have force_open == True = limits for your orders will not work - and it will throw you an error - order being rejected
print("stop")
