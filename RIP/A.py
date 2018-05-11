from RIPv2 import RIPv2
import time

ripAAddress = ("127.0.0.1", 6785)
ripBAddress = ("127.0.0.1", 6786)
ripCAddress = ("127.0.0.1", 6787)
ripDAddress = ("127.0.0.1", 6788)
ripEAddress = ("127.0.0.1", 6789)

addresses = [ripEAddress, ripBAddress, ripCAddress, ripDAddress]

ripA = RIPv2(ripAAddress)
time.sleep(2)
routeGet = []
while(len(routeGet) < 4):
    for addr in addresses:
        if not addr in routeGet:
            if(ripA.traceroute(addr)):            
                routeGet.append(addr)
            time.sleep(1)