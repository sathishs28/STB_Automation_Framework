from core.redrat.redrat_client import RedRat_Client

# print("Testing RedRat_Client...")


client = RedRat_Client()
list_devices = client.get_devices()
print(list_devices)


