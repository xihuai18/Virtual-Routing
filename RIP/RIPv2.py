import random
import socket
import threading
import time
import struct
import sys
sys.path.append("../utils/")
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

    def __init__(self, address):
        self.address = address
        self.buffer = b''
        self.summit = b''
        self.routeTimer = {}
        self.holddwonTimer = {}
        self.neighbour = []
        self.distanceVector = {}
        self.neighbourTimer = {}
        self.recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recvSocket.bind((self.address))

        self.__initDistanceVector()
        self.__begin()

    def __begin(self):
        self.listenUDPThread = threading.Thread(target=self.__listenUDP)
        self.listenUDPThread.start()
        self.__multicast(1)

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
        self.distanceVector.update({neighbourItem.Dest: neighbourItem})
        self.neighbour.append(neighbourItem.Dest)
        self.neighbourVector.update({neighbourItem.Dest:{}})
        self.neighbourTimer.update({neighbourItem.Dest:threading.Timer(
            180, self.__removeNeighbour, args=[neighbourItem.Dest])})
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
                
        threading.Timer(30, self.__multicast, args=[2]).start()
        

    def __listenUDP(self):
        (self.buffer,) = self.recvSocket.recv(1024)
        command = struct.unpack("!B", self.buffer[:1])
        if command == 0:
            (ip, port) = struct.unpack("!IH", self.buffer[7:13])
            DestAddress = (utils.int2ip(ip), port)
            if DestAddress != self.address:
                self.__sendPacket(self.buffer, DestAddress)
                return
            else:
                self.__normalPacketReceived(self.buffer[1:])
        elif command == 1:
            self.__requestPacketReceived(self.buffer[2:])
        else:
            self.__responsePacketReceived(self.buffer[2:])

    def __normalPacketReceived(self, data):
        self.summit = data[13:]

    def __requestPacketReceived(self, data):
        ip, port = struct.unpack("!IH", data[4:10])
        address = (utils.int2ip(ip), port)
        self.__sendResponsePacket(address)

    def __responsePacketReceived(self, data):
        neighbourVector = {}
        sourceIp, sourcePort = struct.unpack("!IH", data[4:10])
        sourceIp = utils.int2ip(sourceIp)
        sourceAddress = (sourceIp, sourcePort)
        data = data[10:]
        for i in range(0, len(data), 17):
            DestIp, DestPort, nextHopIp, nextHopPort, metric = struct.unpack("!IHIHB", data[i+4:i+17])
            DestIp = utils.int2ip(DestIp)
            nextHopIp = utils.int2ip(nextHopPort)
            item = VectorItem((DestIp, DestPort), (nextHopIp, nextHopPort), metric)
            neighbourVector.update({(DestIp, DestPort):item})
        if(self.neighbourTimer[sourceAddress].isAlive()):
            self.neighbourTimer[sourceAddress].cancel()
            self.neighbourTimer.update({sourceAddress:threading.Timer(
            180, self.__removeNeighbour, args=[sourceAddress])})
            self.neighbourTimer[sourceAddress].start()
        else:
            if sourceAddress in self.neighbour:
                threading.Timer(60, self.neighbour.append, args=[sourceAddress]).start()
                threading.Timer(60, self.distanceVector.update, args=[{sourceAddress:neighbourVector}]).start()
            else:
                self.neighbour.append(sourceAddress)
                self.distanceVector.update({sourceAddress:neighbourVector})
        self.__updateVector((sourceIp, sourcePort), neighbourVector)


    def send(self, data, address):
        src = self.address
        packet = struct.pack("!BHIHIH%ds" % len(data), 0,
                             utils.ip2int(src[0]), src[1], utils.ip2int(address[0]), address[1], data)
        self.__sendPacket(packet, address)

    def __sendPacket(self, packet, address):
        # determine where to send
        for item in self.distanceVector:
            if item.Dest == address:
                nextHop = (utils.int2ip(item.nextHop[0]), item.nextHop[1])
                break
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(packet, nextHop)
        s.close()

    def __sendNormalPacket(self, data, address):
        packet = struct.pack("!BIHIH", 0, utils.ip2int(self.address[0]), self.address[1],
                                utils.ip2int(address[0]), address[1]) 
        packet += struct.pack("!%ds" % len(data), data)
        self.__sendPacket(packet, address)

    def __sendRequestPacket(self, address):
        packet = struct.pack("!2BHIHHHIHIHIB", 1, self.version, 0, utils.ip2int(self.address[0]), 
                                self.address[1], 2, 0, utils.ip2int(address[0]),
                                address[1], utils.ip2int(self.address[0]), 
                                self.address[1], 1)
        self.__sendPacket(packet, address)

    def __sendResponsePacket(self, address):
        packet = struct.pack("!2BHIH", 2, self.version, 0, utils.ip2int(self.address[0]),
                                self.address[1]) 
        for item in self.distanceVector:
            DestIp = utils.ip2int(item.Dest[0])
            DestPort = item.Dest[1]
            nextHopIp = utils.ip2int(item.nextHop[0])
            nextHopPort = item.nextHop[1]
            packet += struct.pack("!IHIHB", DestIp, DestPort, nextHopIp, nextHopPort, item.metric)
        self.__sendPacket(packet, address)

    def __updateVector(self, neighbourVector):
        pass

