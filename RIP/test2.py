from RIPv2 import RIPv2
import time
import struct
import sys
sys.path.append("../utils/")
import utils

rip1Address = ("127.0.0.1", 6789)
rip2Address = ("127.0.0.1", 6788)
rip2 = RIPv2(rip2Address)
#time.sleep(5)
#rip2.send(b'\x02', rip1Address)
#time.sleep(2)
#print(struct.unpack("!B",rip2.summit[0:1])[0])
#rip2.summit = rip2.summit[1:]
#print(rip2Address,"->",end="")
## print(len(rip2.summit))
#for i in range(0, len(rip2.path), 6):
#    ip, port = struct.unpack("!IH", rip2.path[i:i+6])
#    ip = utils.int2ip(ip)
#    print((ip, port))
#    if(i != len(rip2.path)-6):
#        print("->")