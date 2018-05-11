import random
import socket
import threading
import time
import struct
import sys
import copy
sys.path.append("../utils/")
import utils

class OSPF(object):
    version = 2
    helloInterval = 30
    deadInterval = 180
    TraceRouteInterval = 5
    summit = b''
    path = {}
    DistanceVectorLock = threading.Lock()
    summitLock = threading.Lock()
    def __init__(self, address, filename):
        self.address = address
        self.topoFilename = filename
        self.buffer = b''
        self.traceRouteList = []
        self.neighbour = []
        self.traceRouteResult = {}
        self.distanceVector = {}
        self.neighbourTimer = {}
        self.recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recvSocket.bind((self.address))

    
    def __begin(self):
        pass

    def __initDistanceVector(self):
        pass

    def __addNeighbour(self, neighbourItem):
        pass

    def __removeNeighbour(self, neighubour):
        def __realRemove(self, neighubour):
            self.neighbour.remove(neighubour)
            self.distanceVector.pop(neighubour)
        pass
    
    def __listenUDP(self):
        pass

    def __handleData(self, data):
        pass

    def __normalPacketReceived(self, sourceAddress, data):
        pass

    def __helloReceived(self, sourceAddress, data):
        pass

    def __LSUReceived(self, sourceAddress, data):
        pass

    def __tracerouteReceived(self, packet):
        pass
              
    def __EchoReceived(self, packet):
        pass

    def __broadcastReceived(self, sourceAddress, data):
        pass
                  
    def recv(self, buffersize):
        pass
              
    def send(self, data, address):
        pass
              
    def traceroute(self, address):
        pass
              
    def __traceRouteExceed(self, dest):
        pass
            
    def __sendPacket(self, packet, address):
        pass

    def __broadcast(self, command=3):
        pass

    def __sendNormalPacket(self, data, address):
        pass
              
    def __sendHello(self, address):
        pass
              
    def __sendLSU(self, address):
        pass
                  
    def __updateVector(self, neighbour, neighbourVector):
        pass
                  