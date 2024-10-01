from sprotocol import device

gf40 = device.mfc('COM3') 
gf40.get_address()


gf40.write_setpoint(0)