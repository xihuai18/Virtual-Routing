from OSPF import OSPF
import time

ospfAAddress = ("127.0.0.1", 6785)
ospfBAddress = ("127.0.0.1", 6786)
ospfCAddress = ("127.0.0.1", 6787)
ospfDAddress = ("127.0.0.1", 6788)
ospfEAddress = ("127.0.0.1", 6789)

addresses = [ospfEAddress, ospfBAddress, ospfCAddress, ospfDAddress]

filename = input("Input the topology filename: ")
ospfA = OSPF(ospfAAddress, filename)
time.sleep(2)
routeGet = []
while(True):
    routeGet = []

    while(len(routeGet) < 4):
        # print(ospfA.distanceVector)
        # print("")

        # for item in ospfA.adjMatrix:
        #     print(item)
        #     print(ospfA.adjMatrix[item])
        # print("")

        for addr in addresses:
            if not addr in routeGet:
                if(ospfA.traceroute(addr)):
                    routeGet.append(addr)
                time.sleep(1)
