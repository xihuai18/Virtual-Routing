import random
import socket
import threading
import time
import struct
import os
os.path.append("../utils/")
import utils


class VectorItem(object):

    def __init__(self, Dest, nextHop, metric):
        self.Dest = Dest
        self.nextHop = nextHop
        self.metric = metric


class RIPv2(object):
    version = 2
    addFamily = 2
    tag = 0
    boardcastIP = "224.0.0.9"
    topologyFileName = "topo.txt"
    UpdateInterval = 30
    InvalidInterval = 180
    FlushInterval = 240
    HolddownInterval = 180

    DistanceVectorLock = threading.Lock()

    def __init__(self, address, port, netmask):
        self.address = address
        self.port = port
        self.netmask = netmask
        self.buffer = b''
        self.summit = b''
        self.routeTimer = {}
        self.holddwonTimer = {}
        self.neighbour = []
#        self.neighbourVector = {}
        self.distanceVector = {}
        self.neighbourTimer = {}
        self.recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recvSocket.bind((self.address))

        self.__initDistanceVector()
        self.__begin()

    def __begin(self):
        self.listenUDPThread = threading.Thread(target=self.listenUDP)
        self.listenUDPThread.start()
        self.__boardcast(1)

    def __initDistanceVector(self):
        with open(self.topologyFileName, 'r') as fileReader:
            lines = fileReader.readlines()
            for line in lines:
                (ip, port) = line.split(",")[0:2]
                port = int(port)
                if (ip, port) == self.address:
                    for i in range(2, len(line.split(",")), 2):
                        (ip, port) = line.split(",")[i:i+1]
                        port = int(port)
                        self.addNeighbour(VectorItem((ip, port), (ip, port), 1))

    def __addNeighbour(self, neighbourItem, neighbourVector):
        self.distanceVector.update(neighbourItem.Dest, neighbourItem)
        self.neighbour.append(neighbourItem.Dest)
        self.neighbourVector.update(neighbourItem.Dest, {})
        self.neighbourTimer.update(neighbourItem.Dest, threading.Timer(
            180, self.__removeNeighbour, args=[neighbourItem.Dest]))
        self.neighbourTimer[neighbourItem.Dest].start()

    def __removeNeighbour(self, neighubour):
        def __realRemove(self, neighubour):
            self.neighbour.remove(neighubour)
            self.distanceVector.pop(neighubour)
        self.neighbourTimer.pop(neighubour)
        threading.Timer(60, __realRemove, args=[self, neighubour]).start()

    def __multicast(self, command):
        '''
        command = 1 : multicast request
        command = 2 : multicast response
        '''
        if command == 1:
            for addr in self.neighbour:
                self.__sendRequestPacket(addr)
        elif command == 2:
            for addr in self.neighbour:
                self.__sendResponsePacket(addr)
                
        threading.Timer(30, self.__boardcast, args=[2]).start()
        
#    def __boardcast(self, command):
#        if command == 3:
#            for addr in self.neighbour:
#                self.__sendRequestPacket(addr)
#        elif command == 4:
#            for addr in self.neighbour:
#                self.__sendResponsePacket(addr)
#        threading.Timer(30, self.__boardcast, args=[4]).start()

    def __listenUDP(self):
        (self.buffer,) = self.recvSocket.recv(1024)
        command = struct.unpack("!B", self.buffer[:1])
        if command == 0:
            self.__normalPacketReceived(self.buffer[2:])
        elif command == 1:
            self.__requestPacketReceived(self.buffer[2:])
        else:
            self.__responsePacketReceived(self.buffer[2:])

    def __normalPacketReceived(self, data):
        self.summit = data

    def __requestPacketReceived(self, data):
        # TODO 提取报文中的各项
        ip, port = struct.unpack("!IH", data[2:8])
        address = (utils.int2ip(ip), port)
        self.__sendResponsePacket(address)

    def __responsePacketReceived(self, data):
        neighbourVector = {}
        # TODO 提取报文中的各项
        data = data[32:]
        for i in range(0, len(data), 20):
            DestIp, DestPort, nextHopIp, nextHopPort, metric = struct.unpack("!IHIHI", data[i:i+20])
            item = VectorItem((DestIp, DestPort), (nextHopIp, nextHopPort), metric)
            neighbourVector.update(item)

    
#    # complete data!
#    # RPF
#    def __boardcastReceived(self, data, preHop):
#        addr = struct.unpack("!HI", data[4:10])
#        addr[0] = utils.int2ip(addr[0])
#        bestHop = self.distanceVector[addr].nextHop
#        if(bestHop != preHop):
#            return
#        for addr in self.neighbour:
#            if(addr != preHop):
#                self.__sendPacket(data, addr)

    def send(self, data, address):
        src = self.address
        packet = struct.pack("!2BHIHIH%ds" % len(data), 0,
                             self.version, 0, utils.ip2int(src[0]), src[1], utils.ip2int(address[0]), address[1], data)
        self.__sendPacket(packet, address)

    def __sendPacket(self, packet, address):
        # determine where to send
        nextHop = None
        for item in self.distanceVector:
            if item.Dest == address:
                nextHop = item.nextHop
                break
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(packet, nextHop)
        s.close()

#    def __sendNormalPacket(self, data, address):
#        pass

    def __sendRequestPacket(self, address):
        packet = struct.pack("!2BHIHHHIHIHI", 1, 0, 0, utils.ip2int(self.address[0]), 
                                self.address[1], 2, 0, utils.ip2int(address[0]),
                                address[1], 0, 0, 16)
        self.__sendPacket(packet, address)

    def __sendResponsePacket(self, address):
        packet = struct.pack("!2BHIHHHIHIIHI", 2, 0, 0, utils.ip2int(self.address[0]),
                                self.address[1], 2, 0, utils.ip2int(address[0]),
                                address[1], utils.ip2int("255.255.255.0"), 0, 0, 16) 
        for item in self.distanceVector:
            DestIp = utils.ip2int(item.Dest[0])
            DestPort = item.Dest[1]
            nextHopIp = utils.ip2int(item.nextHop[0])
            nextHopPort = item.nextHop
            packet += struct.pack("!IHIHI", DestIp, DestPort, nextHopIp, nextHopPort, item.metric)
        self.__sendPacket(packet, address)

    def __updateVector(self, neighbour, neighbourVector):
        pass

#    def __BellmanFord(self):
#        pass
