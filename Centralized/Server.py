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

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor


class ServerProtocol(DatagramProtocol):
    DEADINTERVAL = 30
    mapLock = threading.Lock()

    def __init__(self, address):
        self.address = address  # address : (ip, port)
        self.map = {}  # map that contains the whole routes map
        # map that contains a complete map that indicates the nexthops of each router
        self.nextHopForRouters = {}

    def datagramReceived(self, recvPacket, recvAddr):
        pass

    def __LSReceived(self, neighbourVector):
        # remeber to reset the calllater handlers
        pass

    def __sendForwardTable(self):
        # send forwarding tables to all the neighbours
        pass

    def __updateVector(self, neighbourVector):
        # lock
        pass

    def __floyd(self):
        pass
