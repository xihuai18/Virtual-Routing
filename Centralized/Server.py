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
        # remember to reset the calllater handlers
        pass

    def __sendForwardTable(self):
        # send forwarding tables to all the neighbours
        pass

    def __updateVector(self, client, neighbourVector):
        # lock
        self.mapLock.acquire()
        self.map.update({client: neighbourVector})
        self.__floyd()
        self.mapLock.release()

    def __floyd(self):
        dist = copy.deepcopy(self.map)
        self.nextHopForRouters.clear()
        for i in self.map:
            self.nextHopForRouters[i] = {}
        for k in self.map:
            for i in self.map:
                for j in self.map:
                    if k in dist[i] and j in dist[k]:
                        if j not in dist[i] or dist[i][k] + dist[k][j] < dist[i][j]:
                            dist[i][j] = dist[i][k] + dist[k][j]
                            self.nextHopForRouters[i][j] = k
