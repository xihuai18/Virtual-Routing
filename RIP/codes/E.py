from RIPv2 import RIPv2
import time

ripAAddress = ("127.0.0.1", 6785)
ripBAddress = ("127.0.0.1", 6786)
ripCAddress = ("127.0.0.1", 6787)
ripDAddress = ("127.0.0.1", 6788)
ripEAddress = ("127.0.0.1", 6789)

filename = input("Input the topology filename: ")
ripE = RIPv2(ripEAddress, filename)
