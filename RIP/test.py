from RIPv2 import RIPv2
import time
import struct
import sys
sys.path.append("../utils/")
import utils

rip1Address = ("127.0.0.1", 6789)
rip2Address = ("127.0.0.1", 6788)
rip3Address = ("127.0.0.1", 6787)
rip3 = RIPv2(rip3Address)
time.sleep(5)
rip3.send(b'\x03', rip1Address)
rip3.send(b'\x03', rip2Address)
time.sleep(5)
print(struct.unpack("!B",rip3.summit[0:1])[0])
rip3.summit = rip3.summit[1:]
print(rip3Address,"->",end="")
# print(len(rip2.summit))
for i in range(0, len(rip3.path), 6):
    ip, port = struct.unpack("!IH", rip3.path[i:i+6])
    ip = utils.int2ip(ip)
    print((ip, port))
    if(i != len(rip3.path)-6):
        print("->")