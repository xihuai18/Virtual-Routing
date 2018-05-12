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
        self.adjMatrix = {}

    
    def __begin(self):
        pass

    def __initDistanceVector(self):
        pass

    def __addNeighbour(self, neighbourItem):
        pass

    def __removeNeighbour(self, neighbour):
        def __realRemove(self, neighbour):
            self.neighbour.remove(neighbour)
            self.distanceVector.pop(neighbour)
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

    def __broadcastReceived(self, transmitAddress, sourceAddress, data):
        bestHop = self.distanceVector[sourceAddress]
        #bestHop may be multiple
        if transmitAddress in bestHop:
            for addr in self.neighbour:
                if addr != transmitAddress:
                    self.__sendLSU(addr)
                  
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

    def __broadcast(self):
        for addr in self.neighbour:
            self.__sendLSU(addr)

    def __sendNormalPacket(self, data, address):
        pass
              
    def __sendHello(self, address):
        pass
              
    def __sendLSU(self, address):
        pass
                  
    def __dijkstra(self, neighbour):
        dist = {neighbour:0}
        dist.update(self.adjMatrix[neighbour])
        # s = set([neighbour])
        t = set(self.adjMatrix[neighbour].keys())
        while len(t) > 0:
            min_dist = None
            nearest_dest = None
            for dest in t:
                if min_dist is None or dist[dest] < min_dist:
                    min_dist = dist[dest]
                    nearest_dest = dest
            # s.add(nearest_dest)
            t.remove(nearest_dest)
            for (dest, dist_nd) in self.adjMatrix[nearest_dest]:
                t.add(dest)
                if dest not in dist or min_dist + dist_nd < dist[dest]:
                    dest = min_dist + dist_nd
        return dist

    def __updateVector(self, neighbour, neighbourVector):
        self.DistanceVectorLock.acquire()
        self.adjMatrix[neighbour] = neighbourVector
        neighbourDist = {}
        selfDist = {}
        for (nb, dist_nb) in self.neighbour.items():
            neighbourDist[nb] = self.__dijkstra(nb)
            for (dest, dist) in neighbourDist[nb].items():
                if dest not in selfDist or dist_nb + dist < selfDist[dest]:
                    selfDist[dest] = dist_nb + dist
        for dest in selfDist:
            self.distanceVector[dest] = []
        for (nb, dist_nb) in self.neighbour.items():
            nbDist = neighbourDist[nb]
            for (dest, dist) in nbDist.items():
                if selfDist[dest] == dist_nb + dist:
                    self.distanceVector[dest].append(nb)
        self.DistanceVectorLock.release()
                  