import random
import socket
import threading
import time
import struct
import sys
import copy
sys.path.append("../utils/")
import utils
import json


class Client(object):
    HELLOINTERVAL = 5
    LSINTERVAL = 10
    DEADLINE = 15

    fowardTableLock = threading.Lock()
    summitLock = threading.Lock()

    def __init__(self, address, serverAddress, filename):
        self.address = address
        self.serverAddress = serverAddress
        self.topoFileName = filename
        self.forwardTable = {}  # address:nexthop
        self.summit = b''
        self.buffer = b''
        self.neighbour = {}  # address:cost
        self.neighbourTimer = {}
        self.recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recvSocket.bind((self.address))

    def __begin(self):
        pass

    def __initNeighbour(self):
        pass

    def __addNeighbour(self, neighbourItem):
        pass

    def __removeNeighbour(self, neighbour):
        self.neighbourTimer.pop(neighbour)
        self.neighbour.remove(neighbour)

    def __sendLSToServer(self):
        pass

    def __sendHello(self, address):
        pass

    def __hello(self, address):
        pass

    def __sendPacket(self, address):
        pass

    # metric only
    def __helloReceived(self, sourceAddress, data):
        pass

    # payload is put in data
    def __normalPacketReceived(self, data):
        pass
    
    # data contains only the neighbour of the sourceAddress
    def __forwardTableReceived(self, data):
        pass

    def send(self, data, address):
        pass

    def recv(self, buffersize):
        pass
