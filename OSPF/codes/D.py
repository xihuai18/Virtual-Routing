from OSPF import OSPF
import time

ospfAAddress = ("127.0.0.1", 6785)
ospfBAddress = ("127.0.0.1", 6786)
ospfCAddress = ("127.0.0.1", 6787)
ospfDAddress = ("127.0.0.1", 6788)
ospfEAddress = ("127.0.0.1", 6789)
filename = input("Input the topology filename: ")
ospfD = OSPF(ospfDAddress, filename)
# time.sleep(2)
# while True:
#     print(ospfD.distanceVector)
#     print("")

#     for item in ospfD.adjMatrix:
#         print(item)
#         print(ospfD.adjMatrix[item])
#     print("")
#     time.sleep(2)