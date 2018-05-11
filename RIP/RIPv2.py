import random
import socket
import threading
import time
import struct
import sys
import copy
sys.path.append("../utils/")
import utils

INF = 16

class VectorItem(object):

    def __init__(self, Dest, nextHop, metric):
        # all is a tulple contain string ip and int port
        self.Dest = Dest
        self.nextHop = nextHop
        self.metric = metric


class RIPv2(object):
    version = 2
    addrFamily = 2
    tag = 0
    topologyFileName = "topo.txt"
    UpdateInterval = 30
    InvalidInterval = 180
    FlushInterval = 240
    HolddownInterval = 180
    summit = b''
    path = b''
    DistanceVectorLock = threading.Lock()
    summitLock = threading.Lock()

    def __init__(self, address):
        self.address = address
        self.buffer = b''

        self.holddownTimer = {}
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
                        (ip, port) = line.split(",")[i:i+2]
                        port = int(port)
                        self.__addNeighbour(VectorItem((ip, port), (ip, port), 1))

    def __addNeighbour(self, neighbourItem):
        self.distanceVector.update({neighbourItem.Dest: neighbourItem})
        self.neighbour.append(neighbourItem.Dest)
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
        

    def __handleData(self, data):
        command, = struct.unpack("!B", self.buffer[:1])            
        if command == 0 or command == 3:
            (ip, port) = struct.unpack("!IH", self.buffer[7:13])
            DestAddress = (utils.int2ip(ip), port)
            # print(DestAddress)
            if DestAddress != self.address:
                self.__sendPacket(self.buffer, DestAddress)
                return
            else:
                (sourIp, sourPort) = struct.unpack("!IH", self.buffer[1:7])
                sourceAddress = (utils.int2ip(sourIp),sourPort)
                if command == 0:
                    self.__normalPacketReceived(sourceAddress, self.buffer[13:])
                    self.__sendEcho(sourceAddress)
                if command == 3:
                    self.path += self.buffer[1:7]
                
        elif command == 1:
            self.__requestPacketReceived(self.buffer)
        elif command == 2:
            self.__responsePacketReceived(self.buffer)
            

    def __listenUDP(self):
        while(True):
            self.buffer = self.recvSocket.recv(1024)
            threading.Thread(target=self.__handleData, args=[self.buffer]).start()



    def __normalPacketReceived(self, sourceAddress, data):
        # print(data)
        self.summitLock.acquire()
        self.summit += data
        self.summitLock.release()


    def __requestPacketReceived(self, data):
        ip, port = struct.unpack("!IH", data[4:10])
        address = (utils.int2ip(ip), port)
        self.distanceVector.update({address:VectorItem(address, address, 1)})
        self.__sendResponsePacket(address)

    def __responsePacketReceived(self, data):
        neighbourVector = {}
        # print(data)
        sourceIp, sourcePort = struct.unpack("!IH", data[4:10])
        sourceIp = utils.int2ip(sourceIp)
        sourceAddress = (sourceIp, sourcePort)
        data = data[10:]
        for i in range(0, len(data), 17):
            DestIp, DestPort, nextHopIp, nextHopPort, metric = struct.unpack("!IHIHB", data[i+4:i+17])
            DestIp = utils.int2ip(DestIp)
            nextHopIp = utils.int2ip(nextHopIp)
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
        # data is binary-object
        packet = struct.pack("!BIHIH%ds" % len(data), 0,
                             utils.ip2int(src[0]), src[1], utils.ip2int(address[0]), address[1], data)
        self.__sendPacket(packet, address)

    def __sendEcho(self, sourceAddress):
        packet = struct.pack("!BIHIH", 3, utils.ip2int(self.address[0]), self.address[1],
                                utils.ip2int(sourceAddress[0]), sourceAddress[1])
        self.__sendPacket(packet, sourceAddress)

    def __sendPacket(self, packet, address):
        # determine where to send
        nextHop = None
        dest = self.distanceVector[address]
        if(dest.metric != INF):
            nextHop = dest.nextHop
        else:
            print("Destination unreachable")
            return 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(packet, nextHop)
        s.close()

    def __sendVectorPacket(self, vector, address):
        packet = struct.pack("!2BHIH", 2, self.version, 0, utils.ip2int(self.address[0]),
                                self.address[1]) 
        for item in vector.values():
            DestIp = utils.ip2int(item.Dest[0])
            DestPort = item.Dest[1]
            nextHopIp = utils.ip2int(item.nextHop[0])
            nextHopPort = item.nextHop[1]
            packet += struct.pack("!HHIHIHB", 2, 0, DestIp, DestPort, nextHopIp, nextHopPort, item.metric)
        self.__sendPacket(packet, address)


    def __sendNormalPacket(self, data, address):
        packet = struct.pack("!BIHIH", 0, utils.ip2int(self.address[0]), self.address[1],
                                utils.ip2int(address[0]), address[1]) 
        packet += struct.pack("!%ds" % len(data), data)
        self.__sendPacket(packet, address)

    def __sendRequestPacket(self, address):
        packet = struct.pack("!2BHIHHHIHIHB", 1, self.version, 0, utils.ip2int(self.address[0]), 
                                self.address[1], 2, 0, utils.ip2int(address[0]),
                                address[1], utils.ip2int(self.address[0]), 
                                self.address[1], 1)
        self.__sendPacket(packet, address)

    def __sendResponsePacket(self, address):
        responseVector = {}
        for (DestAddress, item) in self.distanceVector.items():
            if item.nextHop == address:
                item.metric = INF       # Split-horizon routing with poison reverse
            responseVector.update({DestAddress:item})
        self.__sendVectorPacket(responseVector, address)

    def recv(self, buffersize):
        while(len(self.summit) <= 0):
            pass
        size = min(buffersize,len(self.summit))
        buffer = self.summit[:size]
        self.summit = self.summit[size:]
        return buffer

    def __removeHolddownTimer(self, DestAddress):
        self.holddownTimer.pop(DestAddress)
    
    def __updateVector(self, neighbour, neighbourVector):
        triggeredUpdateVector = {}
        DistanceVectorLock.acquire()
        for (DestAddress, item) in neighbourVector.items():
            if DestAddress in self.holddownTimer:
                continue
            if DestAddress in self.distanceVector: 
                curItem = self.distanceVector[DestAddress]
                if curItem.nextHop == neighbour:
                    if curItem.metric < INF and item.metric == INF:
                        self.distanceVector[DestAddress].metric = INF
                        triggeredUpdateVector.update({DestAddress:self.distanceVector[DestAddress]})
                        t = threading.Timer(self.HolddownInterval, self.__removeHolddownTimer,
                                            args=[DestAddress])
                        self.holddownTimer.update({DestAddress:t})
                        t.start()
                    else:
                        self.distanceVector[DestAddress].metric = item.metric + 1
                else:
                    if curItem.metric > item.metric + 1:
                        self.distanceVector[DestAddress].metric = item.metric + 1
                        self.distanceVector[DestAddress].nextHop = neighbour
                        # triggeredUpdateVector.update({DestAddress:self.distanceVector[DestAddress]})
            else:
                newItem = VectorItem(DestAddress, neighbour, min(item.metric + 1, INF))
                self.distanceVector.update({DestAddress:newItem})
        DistanceVectorLock.release()
        if len(triggeredUpdateVector) > 0:
            for neighbourDest in self.neighbour:
                self.__sendVectorPacket(triggeredUpdateVector)

if __name__ == '__main__':
    rip1Address = ("127.0.0.1", 6789)
    rip2Address = ("127.0.0.1", 6788)
    rip3Address = ("127.0.0.1", 6787)
    rip1 = RIPv2(rip1Address)
    
    time.sleep(5)
    rip1.send(b'\x01', rip3Address)
    
    time.sleep(5)
    # print(rip1.summit)
    print(struct.unpack("!B",rip1.summit[0:1])[0])
    print(rip1Address,"->", end="")
    rip1.summit = rip1.summit[1:]
    
    for i in range(0, len(rip1.path), 6):
        ip, port = struct.unpack("!IH", rip1.path[i:i+6])
        ip = utils.int2ip(ip)
        print((ip, port))
        if(i != len(rip1.path)-6):
            print("->")