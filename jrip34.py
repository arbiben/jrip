#!/usr/bin/env python

#################################
#          Ben Arbib            #
#             P2                #
#           JRIP34              #
#                               #
#          COMS 4119            #
#################################


import socket, json, random
import threading, sys, datetime 
import argparse, json, copy
from cost_table import cost_table
from requests import get

# flags for user input
parser = argparse.ArgumentParser()
parser.add_argument("-p", dest='port', type=int, help="port number")
parser.add_argument("hosts", nargs='+', help="HOSTS array")

args = parser.parse_args()

# handle input errors
if args.port is None:
    print("enter port info")
    sys.exit()

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

sock.bind(('', args.port))

hosts = args.hosts
my_ip = get('https://api.ipify.org').text
my_address = str(my_ip+":"+str(args.port))
table = cost_table(hosts, my_address)
event = threading.Event()
lock = threading.Lock()
tr_ip = ''
tr_port = 0

def print_table():
    with lock:
        rip = table.get_table()["Data"]["RIPTable"][:]
    
    print("\nDestination\t\tDistance\tNext_Hop")
    for n in rip:
        print("{}\t{}\t\t{}".format(n["Dest"],n["Cost"], n["Next"]))
    

# send the updated table to every neighbot
def broadcast_table():
    while True:
        with lock:
            neighbors = table.get_all_neighbors()[:]
            t = copy.deepcopy(table.get_table())
        event.wait(10)
        for n in neighbors:
            ip, port = n.split(":")
            sock.sendto(json.dumps(t).encode(), (ip, int(port)))
        event.clear()

# send the new JRIP to cost_table, and the broadcast
def handle_jrip(neighbor_table, addr):
    change = False
    with lock:
        change = table.update_table(neighbor_table, addr[0]+":"+str(addr[1]))
    
    # if changes were made - print the table and ping neighbors
    if change:
        for n in change:
            now = datetime.datetime.now()
            print("\n{} {}\n".format(now.strftime("%a %b %d %H:%M:%S UTC %Y"),n))
        print_table() # maybe remove?
        event.set()

def handle_trace(jrip_file, addr):
    if not jrip_file["Data"]["TRACE"]:
        tr_ip = addr[0]
        tr_port = int(addr[1])

    if jrip_file["Data"]["TRACE"] and jrip_file["Data"]["TRACE"][0]== my_address:
        sock.sendto(json.dumps(jrip_file).encode(), (tr_ip, tr_port))
        
    else:
        # append my_ip to the trace list
        jrip_file["Data"]["TRACE"].append(my_address)

        if jrip_file["Data"]["Destination"] != my_address:
            ip, port = table.get_next_hop(jrip_file["Data"]["Destination"])
        
        elif jrip_file["Data"]["Destination"] == my_address:   
            ip, port = jrip_file["Data"]["Origin"].split(":")

        socket.sendto(json.dumps().encode(), (ip, str(port)))
        

# start an indipendent thread that broadcasts the table
t = threading.Thread(target=broadcast_table)
t.start()

print_table()

#listen for input
while True:
    data, addr = sock.recvfrom(4096)
    jrip_file = json.loads(data)
    if jrip_file["Data"]["Type"] == "JRIP":
        handle_jrip(jrip_file, addr)
    
    if jrip_file["Data"]["Type"] == "TRACE":
        handle_trace(jrip_file, addr)

