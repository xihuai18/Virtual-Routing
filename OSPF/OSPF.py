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
        self.neighbour = {}
        self.traceRouteResult = {}
        self.distanceVector = {}
        self.neighbourTimer = {}
        self.recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recvSocket.bind((self.address))
        self.adjMatrix = {}


 
    def __begin(self):
        self.__initDistanceVector()

    def __initDistanceVector(self):
        pass

    def __addNeighbour(self, neighbourItem):
        pass

    def __removeNeighbour(self, neighbour):
        def __realRemove(self, neighbour):
            self.neighbour.remove(neighbour)
            # self.distanceVector.pop(neighbour)
            self.adjMatrix[self.address].pop(neighbour)
            self.adjMatrix[neighbour].pop(self.address)
            self.__updateVector()
        pass
    
    def __listenUDP(self):
        while True:
            self.buffer = self.recvSocket.recv(1024)
            threading.Thread(target=self.__handleData,
                             args=[self.buffer]).start()

    def __handleData(self, data):
        command = struct.unpack("!B", data[0:1])
        if command == 1:
            # TODO
            # self.__normalPacketReceived(data[:])
        elif command == 2:
            # TODO
            # self.__helloReceived(data[:])
        elif command == 3:
            # TODO
            # self.__LSUReceived(data[:])
        elif command == 4:
            self.__tracerouteReceived(data)
        elif command == 5:
            (ip, port) = struct.unpack("!IH", self.buffer[1:7])
            sourceAddress = (utils.int2ip(ip), port)
            if sourceAddress != self.address:
                self.__sendPacket(data, sourceAddress)
                return
            else:
                self.__EchoReceived(data)

    def __normalPacketReceived(self, sourceAddress, data):
        pass

    def __helloReceived(self, sourceAddress, data):
        pass

    def __LSUReceived(self, sourceAddress, data):
        pass

    def __tracerouteReceived(self, packet):
        (ip, port) = struct.unpack("!IH", packet[1:7])
        sourceAddress = (utils.int2ip(ip), port)
        (ip, port) = struct.unpack("!IH", packet[7:13])
        destAddress = (utils.int2ip(ip), port)
        count, = struct.unpack("!B", packet[-1:])
        count = count - 1
        if count > 0:
            packet = packet[0:-1] + struct.pack("!B", count)
            # packet = struct.pack("!BIHIHB", 4, utils.ip2int(sourceAddress[0]),
            #                      sourceAddress[1], utils.ip2int(
            #                          destAddress[0]),
            #                      destAddress[1], count)
            self.__sendPacket(packet, destAddress)
        else:  # send Echo packet
            EchoPacket = struct.pack("!BIHIHIH", 5, utils.ip2int(sourceAddress[0]),
                                     sourceAddress[1], utils.ip2int(
                                         destAddress[0]),
                                     destAddress[1], utils.ip2int(
                                         self.address[0]),
                                     self.address[1])
            self.__sendPacket(EchoPacket, sourceAddress)
              
    def __EchoReceived(self, packet):
        (ip, port) = struct.unpack("!IH", packet[7:13])
        destAddress = (utils.int2ip(ip), port)
        (ip, port) = struct.unpack("!IH", packet[13:19])
        pathAddress = (utils.int2ip(ip), port)
        if destAddress not in self.path:
            self.path[destAddress] = [pathAddress, ]
        else:
            self.path[destAddress].append(pathAddress)
        if pathAddress == destAddress:  # print the path
            print("(%s:%d)" % (self.address[0], self.address[1]), end='')
            for item in self.path[destAddress]:
                print("->(%s:%d)" % (item[0], item[1]), end='')
            print("")
            self.path.pop(destAddress)
            self.traceRouteList.append(destAddress)
            self.traceRouteResult[destAddress] = 1
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
        # for i in range(1, metric + 1):
        #     packet = struct.pack("!BIHIHB", 4, utils.ip2int(self.address[0]),
        #                             self.address[1], utils.ip2int(address[0]),
        #                             address[1], i)
        #     self.__sendPacket(packet, address)
        pass
              
    def __traceRouteExceed(self, dest):
        # if not dest in self.traceRouteList:
        #     print("Traceroute to ", dest, ": Time Limit Exceeded")
        #     self.path.pop(dest)
        #     self.traceRouteResult[dest] = 2
        pass
            
    def __sendPacket(self, packet, address):
        bestHop = None
        # TODO
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(packet, bestHop)
        s.close()

    def __broadcast(self):
        for addr in self.neighbour:
            self.__sendLSU(addr)

    def __sendNormalPacket(self, data, address):
        packet = struct.pack("!BIHIH%ds" % (len(data)), 1, utils.ip2int(self.address[0]),
                                self.address[1], utils.ip2int(address[0]), 
                                address[1], data)
        self.__sendPacket(packet, address)

    def __sendHello(self, address):
        packet = struct.pack("!BIHH", 2, utils.ip2int(self.address[0]),
                                self.address[1], 1)
        self.__sendPacket(packet, address)
              
    def __sendLSU(self, address):
        # packet = struct.pack("!BIHIHIH", 3, utils.ip2int(self.address[0]),
        #                         self.address[1], utils.ip2int(transmit address ip ?),
        #                         transmit address port ?, utils.ip2int(address[0]),
        #                         address[1], metric ?)
        self.__sendPacket(packet, address)
                  
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
                    dist[dest] = min_dist + dist_nd
        return dist
        
    def __updateVector(self, neighbour=None, neighbourVector=None):
        self.DistanceVectorLock.acquire()
        if neighbour is not None:
            self.adjMatrix[neighbour] = neighbourVector
        neighbourDist = {}
        selfDist = {}
        for (nb, dist_nb) in self.neighbour.items():
            neighbourDist[nb] = self.__dijkstra(nb)
            for (dest, dist) in neighbourDist[nb].items():
                if dest not in selfDist or dist_nb + dist < selfDist[dest]:
                    selfDist[dest] = dist_nb + dist
        self.distanceVector.clear()
        for dest in selfDist:
            self.distanceVector[dest] = []
        for (nb, dist_nb) in self.neighbour.items():
            nbDist = neighbourDist[nb]
            for (dest, dist) in nbDist.items():
                if selfDist[dest] == dist_nb + dist:
                    self.distanceVector[dest].append(nb)
        self.DistanceVectorLock.release()
