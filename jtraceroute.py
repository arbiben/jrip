#!/usr/bin/env python

#################################
#          Ben Arbib            #
#             P2                #
#         JTRACEROUT            #
#                               #
#          COMS 4119            #
#################################


import socket 
import json
import sys 
import argparse

# flags for user input
parser = argparse.ArgumentParser()
parser.add_argument("-p", dest='port', type=int, help="port number")
parser.add_argument("hosts", nargs=2, help="HOSTS array")

args = parser.parse_args()

# handle input errors
if args.port is None:
    print("enter port info")
    sys.exit()


sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

sock.bind(('', args.port))
hosts = args.hosts

table = {}
data = {}

data["Type"] = "TRACE"
data["Destination"] = hosts[1]
data["Origin"] = hosts[0]
data["TRACE"] = []

table["uni"] = "ba2490"
table["SEQ"] = 0
table["ACK"] = 0
table["Data"] = data

ip, port = hosts[0].split(":")
sock.sendto(json.dumps(table).encode(), (ip, int(port)))

def print_trace(jrip_file):
    trace_list = jrip_file["Data"]["TRACE"]
    
    for addr in trace_list:
        print(addr)

#listen for input
while True:
    data, addr = sock.recvfrom(4096)
    addr_id = addr[0]+":"+str(addr[1])
    if addr_id == hosts[0]:
        jrip_file = json.loads(data)
        if jrip_file["Data"]:
            if jrip_file["Data"]["Type"] == "TRACE":
                print_trace(jrip_file)
                sock.close()
                sys.exit()
