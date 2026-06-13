from core.redrat.redrat_client import RedRat_Client
from core.device_manager import Device_Manager

# print("Testing RedRat_Client...")

dm = Device_Manager()
ir = dm.startup

client = RedRat_Client()
list_devices = client.get_devices()
print(list_devices)


