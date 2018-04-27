#!/usr/bin/env python

#################################
#          Ben Arbib            #
#             P2                #
#            JRIP               #
#      GBN protocol model       #
#          COMS 4119            #
#################################


import socket, time, json, random
import threading, sys, re
import argparse, json, copy

lock = threading.Lock # lock variables from being accessed by more than one thread
ack_window = {}       # holds ack records for eack host 
ip_ack = {}           # every host is assigned an id
max_packet_seq = 100  # amount of pings we send to other servers
window = 6            # window size

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

if args.loss_rate > .99 or args.loss_rate < 0.0:
    print("loss rate should be between 0.0 - 0.99")
    sys.exit()


hosts = args.hosts
loss_rate = args.loss_rate * 100

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
def slide_window(hid):
    with lock:    
        win = ack_window[hid]
        temp_window = []
        last = 4
        while last > -1 and win[last] is False:
            last = last - 1
        
        if last == -1:
            return
        
        if last = 4:
            last = win[last][0] + 1
            for i in range (window-1):
                temp_window.append((last,False))
                last = last+1
        else:
            last = win[last+1][0]
            for i in range(window-1):
                temp_window.append((last, False))
                last = last+1
        
        # update the receive window
        ack_window[hid] = copy.deepcopy(temp_window)
        ack_window[hid][5] = -1

# send packets from index to end of window
# ct - copy of the jrip table
def send_packets(hid, ct):
    win = ack_window[hid]
    ip, port = hid.split(":")
    index = 4

    while index > 0 and win[index][1] is False:
        if win[index-1][1] is True:
            break
        index = index - 1

    for i in range(index, window-1):
        rand = random.randint(0, 100)
        
        if rand >= loss_rate:
            seq = win[i][0]
            ct["SEQ"] = seq
            temp_json = json.dumps(ct)
            sock.sendto("{}".format(temp_json).encode(), (ip, int(port)))
            print("packet {} sent".format(seq))
        else:
            print("packet lost")

# thread that manages a specific connection
# TODO manage time outs
def neighbor_thread(h, host_id):
    while True:
        send_packets(host_id, copy.deepcopy(cost_table)) 

        t = threading.Timer(3.0, send_packets(host_id, copy.deepcopy(cost_table)))
        t.start()
        while ack_window[host_id][5] == -1:
            print("checking if packets were change...")
            # do nothing
        t.cancel()
        slide_window(host_id)



# binary search for index of packet in window
def get_index_of_ack_num(target, arr, l, r):
    if l>r:
        return -1

    mid = int((l+r)/2)
    with lock:
        if arr[mid][0] == target:
            return mid
        if arr[mid][0] > target:
            return get_index_of_ack_num(target, arr, l, mid-1)

    return get_index_of_ack_num(target, arr, mid+1, r)
    

# gets an ACK packege and updates window associated with it
def handle_ack(addr, jrip_file):
    ip = addr[0]+":"+str(addr[1])
    ack_num = jrip_file["ACK"]-1
    i = get_index_of_ack_num(ack_num, ack_window[ip], 0, len(ack_window[ip])-1)
    
    if i != -1 and ack_window[ip][i][1] is False:
        with lock:
            ack_window[ip][i][1] = True
            ack_window[ip][5] = i
        

# gets data (ping) and responses with ACK
def handle_data(addr, jrip_file):
    ack_num = jrip_file["SEQ"] + 1
    ack_pack = {}
    ack_pack["SEQ"] = -1
    ack_pack["ACK"] = ack_num
    ip, port = addr
    #sock.sendto(.encode(), (ip, int(port)))
    print("got a data file - not ACK")

# listens for all incoming packets and updates appropriate host handlers
def listener_thread(d1,d2):
    while True:
        data, addr = sock.recvfrom(4096)
        jrip_file = json.loads(data)
        args = (addr, jrip_file)
        if jrip_file["SEQ"] == -1:
            t = threading.Thread(target=handle_ack, args=args)
            t.start()
            t.join()
        else:
            t = threading.Thread(target=handle_data, args=args)
            t.start()
            t.join()


        print(data)


# create a thread for every host given in command line
for k in cost_table["Data"]["RIPTable"]:
#    print(cost_table["Data"])
    ack_window[k["neighbor"]] = [(0,False),(1,False),(2,False),(3,False),(4,False), -1]
    args = (0, k["neighbor"])
    t = threading.Thread(target=neighbor_thread, args=args)
    t.start()
    t.join()


# args is a dummy tuple
args = (0,0)
t = threading.Thread(target=listener_thread, args=args)
t.start()
t.join()

