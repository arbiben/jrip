#!/usr/bin/env python

#################################
#          Ben Arbib            #
#             P2                #
#            JRIP               #
#                               #
#          COMS 4119            #
#################################


import socket, json, random
import threading, sys, datetime
import argparse, copy, time
from cost_table import cost_table
from requests import get

ip = get('https://api.ipify.org').text

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
my_address = socket.gethostbyname(socket.gethostname()) + " is my address"
event = threading.Event()
lock = threading.Lock()

def handle_host(d,hid):
    ip, port, _ = hid.split(":")
    dropped = 0
    for _ in range (100):
        if random.randint(0,100) > loss_rate:
            sock.sendto(my_address.encode(), (ip, int(port)))
        else:
            dropped = dropped + 1
    
    time.sleep(1)
    print("sent {}/100".format(100-dropped))

for host in args.hosts:
    args = (0,host)
    t = threading.Thread(target=handle_host, args=args)
    t.start()

#listen for input
while True:
    data, addr = sock.recvfrom(4096)
    print(data.decode())
