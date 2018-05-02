#!/usr/bin/env python

#################################
#          Ben Arbib            #
#             P2                #
#            JRIP               #
#                               #
#          COMS 4119            #
#################################


import socket
import json
import random
import threading
import sys
import datetime
import argparse
import json
import copy
from cost_table import cost_table

# flags for user input
parser = argparse.ArgumentParser()
parser.add_argument("-p", dest='port', type=int, help="port number")
parser.add_argument("-l", dest='loss_rate', type=float, help="loss rate")
parser.add_argument("hosts", nargs='+', help="HOSTS array")

args = parser.parse_args()

# handle input errors
if args.port is None or args.loss_rate is None:
    print("enter port info")
    sys.exit()


if args.loss_rate > 1 or args.loss_rate < 0:
    print("loss rate 0<l<1")
    sys.exit()

loss_rate = int(args.loss_rate * 100)
sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

sock.bind(('', args.port))

hosts = args.hosts
my_address = socket.gethostbyname(socket.gethostname())
event = threading.Event()
lock = threading.Lock()

def handle_host(d,hid):
    ip, port, _ = hid.split(":")
    print(my_address)
    for _ in range (100):
        sock.sendto(my_address.encode(), (ip, int(port)))

for host in args.hosts:
    args = (0,host)
    t = threading.Thread(target=handle_host, args=args)
    t.start()

#listen for input
while True:
    print("listening")
    data, addr = sock.recvfrom(4096)
    print(data)
