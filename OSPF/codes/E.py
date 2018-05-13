from OSPF import OSPF
import time

ospfAAddress = ("127.0.0.1", 6785)
ospfBAddress = ("127.0.0.1", 6786)
ospfCAddress = ("127.0.0.1", 6787)
ospfDAddress = ("127.0.0.1", 6788)
ospfEAddress = ("127.0.0.1", 6789)
filename = input("Input the topology filename: ")
ospfE = OSPF(ospfEAddress, filename)
# time.sleep(2)
# while True:
#     print(ospfE.distanceVector)
#     print("")

#     for item in ospfE.adjMatrix:
#         print(item)
#         print(ospfE.adjMatrix[item])
#     print("")
#     time.sleep(2)