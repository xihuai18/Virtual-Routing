import socket
import struct


def ip2int(ip):
    return sum([256**j * int(i) for j, i in enumerate(ip.split('.')[::-1])])


def int2ip(ip):
    return socket.inet_ntoa(struct.pack("i", socket.htonl(ip)))
