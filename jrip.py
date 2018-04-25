#!/usr/bin/env python

import socket 
import time
import random
import json

UDP_IP = "127.0.0.1"
UDP_PORT = 5005
MESSAGE = "hello sir"
drop = input("enter drop rate out of 100: ")

sock = socket.socket(socket.AF_INET, # Internet
                             socket.SOCK_DGRAM) # UDP
data = ''
with open('mytable.json') as jrip:
    data = json.load(jrip)
#my_addr = sock.getsockname()

dropped = 0
send_amount = 5
for i in range(send_amount):
    n = random.randint(0,100)
    if int(drop) > int(n):
        print("Packet dropped")
        dropped = dropped + 1
    else:
        sock.sendto(bytes(json.dumps(data), 'utf-8'), (UDP_IP, UDP_PORT))
        print(sock.recvfrom(1024)[0])
    time.sleep(0.2)

print("{} paackets dropped out of {}  pings".format(dropped, send_amount))

sock.close()
