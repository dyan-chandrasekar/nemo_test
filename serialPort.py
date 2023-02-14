import serial.tools.list_ports

ports = serial.tools.list_ports.comports()
serial_ports = []
description_list = []
hardware_list = []
for port, desc, hwid in sorted(ports):
    serial_ports.append(port)
    description_list.append(desc)
    hardware_list.append(hwid)
    print("{}: {} [{}]".format(port, desc, hwid))
# print(serial_ports)
# print(description_list)
# print(hardware_list.index('USB VID:PID=16C0:0483 SER=10733630 LOCATION=1-1'))
# inx = hardware_list.index('USB VID:PID=16C0:0483 SER=10733630 LOCATION=1-1')
# port = serial_ports[inx]
# print(port)