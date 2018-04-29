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
from cost_table import cost_table

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

# flags for user input
parser = argparse.ArgumentParser()
parser.add_argument("-p", dest='port', type=int, help="port number")
parser.add_argument("hosts", nargs='+', help="HOSTS array")

args = parser.parse_args()

# handle input errors
if args.port is None:
    print("enter port info")
    sys.exit()

sock.bind(('', args.port))
hosts = args.hosts
table = cost_table(hosts)
event = threading.Event()

def print_table():
    rip = table.get_table()["Data"]["RIPTable"]
    
    print("\nDestination\t\tDistance\tNext_Hop")
    for n in rip:
        print("{}\t{}\t{}".format(n["Dest"],n["Cost"], n["Next"]))
    

# send the updated table to every neighbot
def broadcast_table():
    while True:
        neighbors = table.get_all_neighbors()
        t = table.get_table()
        event.wait(2)
        for n in neighbors:
            ip, port = n.split(":")
            sock.sendto(json.dumps(t).encode(), (ip, int(port)))
        event.clear()
        print_table()

# send the new JRIP to cost_table, and the broadcast
def handle_jrip(neighbor_table):
    table.update_table(neighbor_table)
    event.set()

# start an indipendent thread that broadcasts the table
t = threading.Thread(target=broadcast_table)
t.start()

# listen for input
while True:
    data, addr = sock.recvfrom(4096)
    jrip_file = json.loads(data)
    if jrip_file["Type"] == "JRIP":
        handle_jrip(jrip_file)

