from Client import Client

import time

clientAAddress = ("127.0.0.1", 6785)
clientBAddress = ("127.0.0.1", 6786)
clientCAddress = ("127.0.0.1", 6787)
clientDAddress = ("127.0.0.1", 6788)
clientEAddress = ("127.0.0.1", 6789)

serverAddress = ("127.0.0.1", 51000)

addresses = [clientEAddress, clientBAddress, clientCAddress, clientDAddress]

filename = input("Input the topology filename: ")
clientB = Client(clientBAddress, serverAddress, filename)
while(True):
    pass
