#!/usr/bin/env python

#################################
#          Ben Arbib            #
#             P2                #
#           JRIP34              #
#                               #
#          COMS 4119            #
#################################


import socket, time, json, random
import threading, sys, re
import argparse, json, copy

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

# flags for user input
parser = argparse.ArgumentParser()
parser.add_argument("-l", dest='loss_rate', type=float, help="loss rate")
parser.add_argument("-p", dest='port', type=int, help="port number")
parser.add_argument("hosts", nargs='+', help="HOSTS array")

args = parser.parse_args()

# handle input errors
if args.loss_rate is None or args.port is None:
    print("enter loss rate and port info")
    sys.exit()

if args.loss_rate > .99 or args.loss_rate < 0.0:
    print("loss rate should be between 0.0 - 0.99")
    sys.exit()

sock.bind(('', args.port))
hosts = args.hosts
table = cost_table(hosts)

# send the updated table to every neighbot
def broadcast_table():
    neighbors = table.get_all_neighbors()
    t = table.get_table()
    
    for n,d in neighbors:
        ip, port = n.split(":")
        sock.sendto(t, (ip, port))

# send the new JRIP to cost_table, and the broadcast
def handle_jrip(neighbor_table):
    table.update_table(neighbor_table)
    broadcat_table()

# listen for input
while True:
    data, addr = sock.recvfrom(4096)
    jrip_file = json.loads(data)
    args = (addr, jrip_file)
    if jrip_file["Type"] == "JRIP":
        handle_jrip(jrip_file)
    else:
        # this is not a jrip file, do nothing for now
        t = threading.Thread(target=, args=args)
        t.start()


