#!/usr/bin/env python

#################################
#          Ben Arbib            #
#             P2                #
#            JRIP               #
#      GBN protocol model       #
#          COMS 4119            #
#################################


import socket, time, json
import threading, sys, re
import argparse, json, copy

ack_window = {}     # holds ack records for eack host 
ip_ack = {}         # every host is assigned an id
max_packet_seq = 100  # amount of pings we send to other servers
window = 5          # window size

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

# change the window based on ACK received and resend new packets
# TODO ADJUST WINDOW SIZE AFTER PASSING 95 PACKETS ACK

def slide_window(hid, ct, index):
    win = ack_window[hid]
    ip, port = hid.split(":")
    temp_window = []
    last = win[window-1][0] if index == window -1 else win[index+1][0]

    new_packets = index + 1
    
    for i in range (window):
        temp_window.append((last,False))
        last = last+1
    
    # update the receive window
    ack_window[hid] = copy.deepcopy(temp_window)
    index = window - new_packets

    # send packets based on new window
    send_packets(hid, ip, port, ct, index)



# send packets from index to end of window
# ct - copy of the jrip table
def send_packets(hid, ct, index):
    win = ack_window[hid]
    ip, port = hid.split(":")
    for i in range(index, window):
        seq = win[i][0]
        ct["SEQ"] = seq
        sock.sendto("{}".format(ct).encode(), (ip, int(port)))
    


# thread that manages a specific connection
def neighbor_thread(h, host_id):
    window_size = 5
    last_packet_sent = -1
    #print(ip_ack[host_id])
    send_packets(host_id, copy.deepcopy(cost_table), 0) 
    

# binary search for index of packet in window
def get_index_of_ack_num(target, arr, l, r):
    if l>r:
        return -1

    mid = int((l+r)/2)
    if arr[mid] == target:
        return mid

    if arr[mid] > target:
        return get_index_of_ack_num(target, arr, l, mid-1)

    return get_index_of_ack_num(target, arr, mid+1, r):
    



# gets an ACK packege and updates window associated with it
def handle_ack(addr, jrip_file):
    ip = addr[0]+":"+addr[1]
    ack_num = jrip_file["ACK"]-1
    i = get_index_of_ack_num(ack_num, ack_window[ip], 0, len(ack_window[ip])-1)
    if i != -1 and ack[ip][1] is False:
        ack_window[ip][i] = (ack_window[ip][i][0], True)
        slide_window(ip, copy.deepcopy(cost_table), i)
        

# gets data (ping) and responses with ACK
def handle_data(addr, jrip_file):
    ack_num = jrip_file["SEQ"] + 1
    ack_pack = {}
    ack_pack["SEQ"] = -1
    ack_pack["ACK"] = ack_num
    ip, port = addr
    sock.sendto("{}".format(ack_sock).encode(), (ip, int(port)))


# listens for all incoming packets and updates appropriate host handlers
def listener_thread(d1,d2):
    while True:
        data, addr = sock.recvfrom(4096)
        jrip_file = json.loads(data)
        if jrip_file["SEQ"] == -1:
            handle_ack(addr, jrip_file)
        else:
            handle_data(addr, jrip_file)

        print(data)


# create a thread for every host given in command line
for k in cost_table["Data"]["RIPTable"]:
    ack_window[k["neighbor"]] = [(0,False),(1,False),(2,False),(3,False),(4,False)]
    args = (0, k["neighbor"])
    t = threading.Thread(target=neighbor_thread, args=args)
    t.start()
    t.join()


# args is a dummy tuple
args = (0,0)
t = threading.Thread(target=listener_thread, args=args)
t.start()
t.join()

