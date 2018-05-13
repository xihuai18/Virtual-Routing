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
from twisted.internet import task


class ServerProtocol(DatagramProtocol):
    DEADINTERVAL = 30
    mapLock = threading.Lock()

    def __init__(self, address, reactor):
        self.address = address  # address : (ip, port)
        self.reactor = reactor
        self.map = {}  # map that contains the whole routes map
        # map that contains a complete map that indicates the nexthops of each router
        self.nextHopForRouters = {}
        self.callLaterHandles = {}

    def __removeClient(self, client):
        self.map.pop(client)
        self.nextHopForRouters.pop(client)
        self.callLaterHandles.pop(client)

    def datagramReceived(self, data, addr):
        print(data)
        command = struct.unpack("!B", data[0:1])
        if command == 2:  # LS
            (ip, port) = struct.unpack("!IH", data[1:7])
            client = (utils.int2ip(ip), port)
            self.__LSReceived(client, data[7:])

    def __LSReceived(self, client, data):
        neighbourVector = {}
        for i in range(0, len(data), 8):
            (ip, port, metric) = struct.unpack("!IHH", data[i:i+8])
            destAddress = (utils.int2ip(ip), port)
            neighbourVector[destAddress] = metric
        self.__updateVector(client, neighbourVector)
        if client in self.callLaterHandles:
            self.callLaterHandles[client].cancel()
        self.callLaterHandles[client] = self.reactor.callLater(self.DEADINTERVAL,
                                                               self.__removeClient,
                                                               args=[client])

    def __sendForwardTable(self):
        # send forwarding tables to all the neighbours
        for client in self.map:
            packet = struct.pack('!B', 3)
            for item in self.nextHopForRouters[client].items():
                packet += struct.pack("!IHIH", utils.ip2int(item[0][0]),
                                      item[0][1], utils.ip2int(item[1][0]),
                                      item[1][1])
            self.transport.write(packet, client)

    def __updateVector(self, client, neighbourVector):
        self.mapLock.acquire()
        if client not in self.map or neighbourVector != self.map[client]:
            self.map[client] = neighbourVector
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

    def getRoute(self, source, dest):
        route = [source]
        node = source
        while node != dest:
            if node not in self.nextHopForRouters:
                return None
            if dest not in self.nextHopForRouters[node]:
                return None
            node = self.nextHopForRouters[node][dest]
            route.append(node)
        return route


def printRoute(server):
    for (source, LS) in server.map.items():
        print(source)
        print(LS)
            
    routers = server.map.keys()
    print("Printing")
    for source in routers:
        for dest in routers:
            if source != dest:
                route = server.getRoute(source, dest)
                if route is None:
                    print("Nonexistent path")
                else:
                    for router in route[0:-1]:
                        print(router, end="->")
                    print(route[-1])


SERVER_PORT = 51000


def main():
    server = ServerProtocol(("127.0.0.1", SERVER_PORT), reactor)
    reactor.listenUDP(SERVER_PORT, server, "127.0.0.1")
    task.LoopingCall(printRoute, server).start(5)
    reactor.run()


if __name__ == '__main__':
    main()
