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

class ServerProtocol(DatagramProtocol):
    def datagramReceived(self, recvPacket, recvAddr):
        pass
