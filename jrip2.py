#!/usr/bin/env python

import socket, time, json
import threading, sys, re
import argparse, json, copy

acks = {}     # holds ack records for eack host 
ip_ack = {}   # every host is assigned an id
thread_id = 0 
window = 5    # window size

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP

# flags for user input
parser = argparse.ArgumentParser()
parser.add_argument("-l", dest='loss_rate', type=float, help="loss rate")
parser.add_argument("-p", dest='port', type=int, help="port number")
parser.add_argument("hosts", nargs='+', help="HOSTS array")

args = parser.parse_args()

if args.loss_rate is None or args.port is None:
    print("enter loss rate and port info")
    sys.exit()

hosts = args.hosts
loss_rate = args.loss_rate

# create a dict object containing cost to neighbors
cost_table = {}
cost_table["SEQ"] = 1
cost_table["ACK"] = 0
cost_table["Data"] = {}
cost_table["Data"]["Type"] = "JRIP"
cost_table["Data"]["RIPTable"] = []

for i in range(len(hosts)):
    h,p,c = hosts[i].split(":")
    temp = {}
    
    check = re.search('[a-zA-Z]', h)
    if check is not None:
        h = socket.gethostbyname(h)
    
    temp["neighbor"] = h+":"+p
    temp["cost"] = c
    cost_table["Data"]["RIPTable"].append(copy.deepcopy(temp))

cost_json = json.dumps(cost_table)

sock.bind(('', args.port))

def sendFive(hid, ip, port, cj):
    win = acks[hid]
    for i in range(window):
        seq = win[i][0]
        print(seq)
        #sock.sendto("{}".format(cost_json).encode(), (ip, int(port)))
    


# thread that manages a specific connection
def neighbor_thread(h, host_id):
    window_size = 5
    last_packet_sent = -1
    #print(ip_ack[host_id])
    ip, port = ip_ack[host_id].split(":")
    sendFive(host_id, ip, port, cost_jason.copy()) 
    


# create a thread for every host given in command line
for k in cost_table["Data"]["RIPTable"]:
    acks[thread_id] = [(0,False),(1,False),(2,False),(3,False),(4,False)]
    args = (0, thread_id)
    ip_ack[thread_id] = k["neighbor"]
    thread_id = thread_id + 1
    t = threading.Thread(target=neighbor_thread, args=args)
    t.start()
    t.join()

def listener_thread(d1,d2):
    while True:
        data, addr = sock.recvfrom(4096)
        print(data)
    

# args is a dummy tuple
args = (0,0)
t = threading.Thread(target=listener_thread, args=args)
t.start()
t.join()

