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


class Client(object):
    HELLOINTERVAL = 5
    LSINTERVAL = 10
    DEADLINE = 15

    forwardTableLock = threading.Lock()
    summitLock = threading.Lock()

    def __init__(self, address, serverAddress, filename):
        self.address = address
        self.serverAddress = serverAddress
        self.topoFileName = filename
        self.forwardTable = {}  # address:nexthop
        self.summit = b''
        self.buffer = b''
        self.neighbour = {}  # address:cost
        self.neighbourTimer = {}
        self.recvSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.recvSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.recvSocket.bind((self.address))

    def __begin(self):
        self.__initNeighbour()
        threading.Thread(target=self.__listenUDP).start()
        self.__hello()
        self.__sendLSToServer()

    def __initNeighbour(self):
        with open(self.topoFilename, 'r') as fileReader:
            lines = fileReader.readlines()
            for line in lines:
                items = line.split(',')
                sourceAddress = (items[0], int(items[1]))
                if sourceAddress == self.address:
                    for i in range(2, len(items), 3):
                        destAddress = (items[i], int(items[i+1]))
                        cost = int(items[i+2])
                        self.__addNeighbour((destAddress, cost), {})

    def __addNeighbour(self, neighbourItem):
        # SET TIMER
        self.neighbour.update({neighbourItem[0]: neighbourItem[1]})
        self.neighbourTimer.update({neighbourItem[0]: threading.Timer(
            self.deadInterval, self.__removeNeighbour,
            args=[neighbourItem[0]])})
        self.neighbourTimer[neighbourItem[0]].start()

    def __removeNeighbour(self, neighbour):
        self.neighbourTimer.pop(neighbour)
        self.neighbour.remove(neighbour)

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
                self.__sendPacket(data, destAddress)
                return
            self.__normalPacketReceived(sourceAddress, data[13:])
        elif command == 1:
            self.__helloReceived(sourceAddress, data[7:])
        elif command == 3:
            self.__forwardTableReceived(data[1:])

    def __sendLS(self, address):
        packet = struct.pack("!BIH", 2, utils.ip2int(
            self.address[0]), self.address[1])
        for addr, cost in self.neighbour.items():
            packet += struct.pack("!IHH", utils.ip2int(
                addr[0]), addr[1], cost)
        self.__sendPacket(packet, address)

    def __sendLSToServer(self):
        # Timer inside
        self.__sendLS(self.serverAddress)
        threading.Timer(self.LSINTERVAL, self.__sendLSToServer).start()

    def __sendHello(self, address):
        packet = struct.pack("!BIHH", 1, utils.ip2int(
            self.address[0]), self.address[1], self.neighbour[address])
        self.__sendPacket(packet, address)

    def __hello(self):
        # Timer inside
        for addr in self.neighbour:
            self.__sendHello(addr)
        threading.Timer(self.HELLOINTERVAL, self.__hello).start()

    def __sendPacket(self, packet, address):
        if address not in self.distanceVector:
            print("Destination unreachable")
        nextHop = self.distanceVector[address]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.sendto(packet, nextHop)
        s.close()

    # metric only
    def __helloReceived(self, sourceAddress, data):
        metric = struct.unpack("!H", data)
        self.neighbour.update({sourceAddress: metric})
        if sourceAddress not in self.neighbour:
            self.__addNeighbour((sourceAddress, metric))
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
                self.__addNeighbour((sourceAddress, metric))

    # payload is put in data
    def __normalPacketReceived(self, data):
        self.summitLock.acquire()
        self.summit += data
        self.summitLock.release()

    # data contains only the neighbour of the sourceAddress
    def __forwardTableReceived(self, data):
        self.forwardTableLock.acquire()
        for i in range(0, len(data), 12):
            destIp, destPort, nextHopIp, nextHopPort = struct.unpack(
                "!IHIH", data[i:i+12])
            destIp = utils.int2ip(destIp)
            nextHopIp = utils.int2ip(nextHopIp)
            self.forwardTable.update(
                {(destIp, destPort): (nextHopIp, nextHopPort)})
        self.forwardTableLock.release()

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
