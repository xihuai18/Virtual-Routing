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
        self.__boardcast(3)

    def __initDistanceVector(self):
        with open(self.topologyFileName, 'r') as fileReader:
            line = fileReader.readline()
            (ip, port) = line.split(",")[0:2]
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

    def __boardcast(self, command):
        if command == 3:
            for addr in self.neighbour:
                self.__sendRequestPacket(addr)
        elif command == 4:
            for addr in self.neighbour:
                self.__sendResponsePacket(addr)
        threading.Timer(30, self.__boardcast, args=[4]).start()

    def __listenUDP(self):
        (self.buffer, preHop) = self.recvSocket.recvfrom(1024)
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
        pass

    def __responsePacketReceived(self, data):
        pass
    
    # complete data!
    # RPF
    def __boardcastReceived(self, data, preHop):
        addr = struct.unpack("!HI", data[4:10])
        addr[0] = utils.int2ip(addr[0])
        bestHop = self.distanceVector[addr].nextHop
        if(bestHop != preHop):
            return
        for addr in self.neighbour:
            if(addr != preHop):
                self.__sendPacket(data, addr)

    def send(self, data, address):
        src = self.address
        packet = struct.pack("!2BHIHIH%ds" % len(data), 0,
                             self.version, 0, utils.ip2int(src[0]), src[1], utils.ip2int(address[0]), address[1], data)
        self.__sendPacket(packet, address)

    def __sendPacket(self, packet, address):
        # determine where to send
        pass

    def __sendNormalPacket(self, data, address):
        pass

    def __sendRequestPacket(self, address):
        pass

    def __sendResponsePacket(self, address):
        pass

    def __updateVector(self, neighbourVector):
        pass

    def __BellmanFord(self):
        pass
