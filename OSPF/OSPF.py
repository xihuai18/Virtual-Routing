import random
import socket
import threading
import time
import struct
import sys
import copy
sys.path.append("../utils/")
import utils
import hashlib
import math


class OSPF(object):
    version = 2
    helloInterval = 10 // 5
    deadInterval = 60
    random.seed(math.ceil(time.time() * 207))
    broadcastInterval = random.randint(20, 30) // 5
    TraceRouteInterval = 5
    summit = b''
    path = {}
    DistanceVectorLock = threading.Lock()
    summitLock = threading.Lock()
    md5Lock = threading.Lock()

    def __init__(self, address, filename):
        self.address = address
        self.topoFilename = filename
        self.buffer = b''
        self.traceRouteList = []
        self.neighbour = {}  # address:cost
        self.forwardPacket = []
        self.forwardPacketIndex = 0
        self.traceRouteResult = {}
        self.distanceVector = {}
        self.neighbourTimer = {}
        self.recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recvSocket.bind((self.address))
        # dictionary of dictionary
        self.adjMatrix = {}
        self.__begin()

    def __begin(self):
        def __broadcastAndTimer(self):
            self.__broadcast()
            threading.Timer(self.broadcastInterval,
                            __broadcastAndTimer, args=[self]).start()
        self.__initDistanceVector()
        threading.Thread(target=self.__listenUDP).start()
        # say hello to neighbors
        self.__hello()
        __broadcastAndTimer(self)
        # self.listenUDPThread = threading.Thread(target=self.__listenUDP)
        # self.listenUDPThread.start()

    def __initDistanceVector(self):
        # source neighbor(IP,port) cost ... last 2 terms repeated
        self.adjMatrix[self.address] = {}
        with open(self.topoFilename, 'r') as fileReader:
            lines = fileReader.readlines()
            for line in lines:
                items = line.split(',')
                sourceAddress = (items[0], int(items[1]))
                if sourceAddress == self.address:
                    for i in range(2, len(items), 3):
                        destAddress = (items[i], int(items[i + 1]))
                        cost = int(items[i + 2])
                        self.__addNeighbour((destAddress, cost), {})

    def __addNeighbour(self, neighbourItem, neighbourLS):
        self.distanceVector[neighbourItem[0]] = [neighbourItem[0], ]
        self.neighbour.update({neighbourItem[0]: neighbourItem[1]})
        self.adjMatrix.update({neighbourItem[0]: neighbourLS})
        self.adjMatrix[self.address].update(
            {neighbourItem[0]: neighbourItem[1]})
        self.neighbourTimer.update({neighbourItem[0]: threading.Timer(
            self.deadInterval, self.__removeNeighbour,
            args=[neighbourItem[0]])})
        self.neighbourTimer[neighbourItem[0]].start()

    def __removeNeighbour(self, neighbour):
        def __realRemove(self, neighbour):
            self.DistanceVectorLock.acquire()
            self.neighbour.pop(neighbour)
            if neighbour in self.adjMatrix[self.address]:
                self.adjMatrix[self.address].pop(neighbour)
            if self.address in self.adjMatrix[neighbour]:
                self.adjMatrix[neighbour].pop(self.address)
            self.DistanceVectorLock.release()
            self.__updateVector()
        self.neighbourTimer.pop(neighbour)
        __realRemove(self, neighbour)

    def __listenUDP(self):
        while True:
            self.buffer = self.recvSocket.recv(1024)
            threading.Thread(target=self.__handleData,
                             args=[self.buffer]).start()

    def __handleData(self, data):
        (command, ip, port) = struct.unpack("!BIH", data[0:7])
        sourceAddress = (utils.int2ip(ip), port)
        if command == 0:
            (ip, port) = struct.unpack("!IH", data[7:13])
            destAddress = (utils.int2ip(ip), port)
            if destAddress != self.address:
                m = hashlib.md5()
                m.update(data)
                md5 = m.hexdigest()
                md5Lock.acquire()
                if md5 not in self.forwardPacket:
                    self.__sendPacket(data, destAddress)
                    if len(self.forwardPacket) < 10:
                        self.forwardPacket.append(md5)
                    else:
                        self.forwardPacket[self.forwardPacketIndex] = md5
                        self.forwardPacketIndex = (
                            self.forwardPacketIndex + 1) % 10
                md5Lock.release()
                return
            elif destAddress == self.address:
                self.__normalPacketReceived(sourceAddress, data[13:])
        elif command == 1:
            self.__helloReceived(sourceAddress, data[7:])
        elif command == 2:
            self.__LSUReceived(sourceAddress, data[13:])
            (ip, port) = struct.unpack("!IH", data[7:13])
            transmitAddress = (utils.int2ip(ip), port)
            self.__broadcastReceived(transmitAddress, sourceAddress, data)
        elif command == 3:
            self.__tracerouteReceived(data)
        elif command == 4:
            if sourceAddress != self.address:
                self.__sendPacket(data, sourceAddress)
                return
            else:
                self.__EchoReceived(data)

    # data contains only the data of the normal packet
    def __normalPacketReceived(self, data):
        self.summitLock.acquire()
        self.summit += data
        self.summitLock.release()

    # data contains only the metric from sourceAddress
    def __helloReceived(self, sourceAddress, data):
        metric = struct.unpack("!H", data)
        if not sourceAddress in self.neighbour.keys():
            self.__addNeighbour((sourceAddress, metric), {})
        else:
            if self.neighbourTimer[sourceAddress].isAlive():
                self.neighbourTimer[sourceAddress].cancel()
                self.neighbourTimer.update({sourceAddress: threading.Timer(
                    self.deadInterval, self.__removeNeighbour, args=[sourceAddress])})
                self.neighbourTimer[sourceAddress].start()
            else:
                # if the hello is received simultaneous!!
                while sourceAddress in self.neighbour.keys():
                    pass
                self.__addNeighbour((sourceAddress, metric), {})

    # data contains only the neighbour of the sourceAddress
    def __LSUReceived(self, sourceAddress, data):
        sourceAddressNeighbour = {}
        for i in range(0, len(data), 8):
            (ip, port, metric) = struct.unpack("!IHH", data[i:i + 8])
            address = (utils.int2ip(ip), port)
            sourceAddressNeighbour.update({address: metric})
        self.__updateVector(sourceAddress, sourceAddressNeighbour)

    # entire packet
    def __tracerouteReceived(self, packet):
        (ip, port) = struct.unpack("!IH", packet[1:7])
        sourceAddress = (utils.int2ip(ip), port)
        (ip, port, count) = struct.unpack("!IHB", packet[7:14])
        destAddress = (utils.int2ip(ip), port)
        count = count - 1
        if count > 0 and destAddress != self.address:
            packet = packet[0:-1] + struct.pack("!B", count)
            self.__sendPacket(packet, destAddress)
        elif count == 0:  # send Echo packet
            EchoPacket = struct.pack("!BIHIHIH", 4, utils.ip2int(sourceAddress[0]),
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

    def __broadcastReceived(self, transmitAddress, sourceAddress, packet):
        if not sourceAddress in self.distanceVector:
            return
        bestHop = self.distanceVector[sourceAddress]
        # Reverse Path First
        # bestHop may be multiple
        if transmitAddress in bestHop:
            for addr in self.neighbour:
                if addr != transmitAddress:
                    self.__sendLSU(addr, packet)

    def recv(self, buffersize):
        while(len(self.summit) <= 0):
            pass
        size = min(buffersize, len(self.summit))
        buffer = self.summit[:size]
        self.summit = self.summit[size:]
        return buffer

    def send(self, data, address):
        packet = struct.pack("!BIHIH%ds" % len(data), 0,
                             utils.ip2int(self.address[0]), self.address[1], utils.ip2int(address[0]), address[1], data)
        self.__sendPacket(packet, address)

    def traceroute(self, address):
        self.traceRouteResult[address] = 0
        self.path[address] = []

        for i in range(1, 32 + 1):
            packet = struct.pack("!BIHIHB", 3, utils.ip2int(self.address[0]),
                                 self.address[1], utils.ip2int(address[0]),
                                 address[1], i)
            self.__sendPacket(packet, address)
        threading.Timer(self.TraceRouteInterval,
                        self.__traceRouteExceed, args=[address]).start()
        while(self.traceRouteResult[address] == 0):
            pass
        return self.traceRouteResult[address] == 1

    def __hello(self):
        for addr in self.neighbour.keys():
            self.__sendHello(addr)
        threading.Timer(self.helloInterval, self.__hello).start()

    def __traceRouteExceed(self, dest):
        if not dest in self.traceRouteList:
            print("Traceroute to ", dest, ": Time Limit Exceeded")
            self.path.pop(dest)
            self.traceRouteResult[dest] = 2

    def __sendPacket(self, packet, address):
        # check the existence
        if not address in self.distanceVector:
            # print("Destination unreachable")
            return False
        # print("self.distanceVector = ", self.distanceVector)
        bestHop = self.distanceVector[address]
        nextHop = bestHop[random.randint(0, len(bestHop) - 1)]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(packet, nextHop)
        s.close()

    def __broadcast(self):
        for addr in self.neighbour:
            self.__sendLSU(addr)

    def __sendNormalPacket(self, data, address):
        packet = struct.pack("!BIHIH%ds" % (len(data)), 0, utils.ip2int(self.address[0]),
                             self.address[1], utils.ip2int(address[0]),
                             address[1], data)
        self.__sendPacket(packet, address)

    def __sendHello(self, address):
        packet = struct.pack("!BIHH", 1, utils.ip2int(self.address[0]),
                             self.address[1], 1)
        self.__sendPacket(packet, address)

    def __sendLSU(self, address, packet=None):
        if packet == None:
            packet = struct.pack("!BIHIH", 2, utils.ip2int(self.address[0]),
                                 self.address[1], utils.ip2int(
                                     self.address[0]),
                                 self.address[1])
            for item in self.neighbour.keys():
                packet += struct.pack("!IHH", utils.ip2int(item[0]), item[1],
                                      self.neighbour[item])
        else:
            packet = packet[0:7] + struct.pack("!IH", utils.ip2int(self.address[0]),
                                               self.address[1]) + packet[13:]
        self.__sendPacket(packet, address)

    def __dijkstra(self, neighbour):
        dist = {neighbour: 0}
        dist.update(self.adjMatrix[neighbour])
        s = set([neighbour])
        t = set(self.adjMatrix[neighbour].keys())
        # print('initial t:', t)
        while len(t) > 0:
            min_dist = None
            nearest_dest = None
            for dest in t:
                if min_dist is None or dist[dest] < min_dist:
                    min_dist = dist[dest]
                    nearest_dest = dest
            s.add(nearest_dest)
            t.remove(nearest_dest)
            # print('nearest_dest:', nearest_dest)
            if nearest_dest in self.adjMatrix:
                for (dest, dist_nd) in self.adjMatrix[nearest_dest].items():
                    if dest not in s:
                        # print('add to t:', dest)
                        t.add(dest)
                        if dest not in dist or min_dist + dist_nd < dist[dest]:
                            dist[dest] = min_dist + dist_nd
        return dist

    def __updateVector(self, neighbour=None, neighbourVector=None):
        # print("update:", neighbour, neighbourVector)
        # print("before:", self.distanceVector)
        # print("")
        self.DistanceVectorLock.acquire()
        if neighbour is not None:
            self.adjMatrix[neighbour] = neighbourVector
        # print("adjMatrix of", self.address)
        # for nb in self.adjMatrix:
        #     print(nb, self.adjMatrix[nb])
        # print('')
        neighbourDist = {}
        selfDist = {}
        for (nb, dist_nb) in self.neighbour.items():
            neighbourDist[nb] = self.__dijkstra(nb)
            # print(nb, neighbourDist)
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
        # print("after:", self.distanceVector, end='\n\n')
        self.DistanceVectorLock.release()
