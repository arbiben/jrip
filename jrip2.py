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

lock = threading.Lock()   # lock variables from being accessed by more than one thread
ack_window = {}           # holds ack records for eack host 
ip_ack = {}               # every host is assigned an id
max_packet_seq = 100      # amount of pings we send to other servers
window = 6                # window size
events = {}               # dict of events per host
last_seq = {}             # dict of hosts who pinged me

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
loss_rate = args.loss_rate * 100

# create a dict object containing cost to neighbors
cost_table = {}
cost_table["SEQ"] = -1
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


# change the window based on ACK received and resend new packets
# TODO ADJUST WINDOW SIZE AFTER PASSING 95 PACKETS ACK
def slide_window(hid):
    temp_window = []
    last = 0
    with lock:
        change = int(ack_window[hid][5])
        if change == -1:
            return
        last = ack_window[hid][change][0]
    
    for _ in range(window-1):
        last = last+1
        temp_window.append([last, False])
    
    with lock:
        # update the receive window
        ack_window[hid] = copy.deepcopy(temp_window)
        ack_window[hid].append(-1)
        print("after swap {}".format(ack_window[hid]))

# send packets from index to end of window
def send_packets(hid):
    ip, port = hid.split(":")
    with lock:
        did_change = ack_window[hid][5]

    if did_change==-1:
        did_change = 0
    
    for i in range(did_change,window-1):
        rand = random.randint(0,100)
        if rand >= loss_rate:
            with lock:
                cost_table["SEQ"] =  ack_window[hid][i][0]
                sock.sendto(json.dumps(cost_table).encode(), (ip,int(port)))



# thread that manages a specific connection
# TODO manage time outs
def neighbor_thread(d, host_id):
    while True:
        events[host_id].wait(1)
        if not events[host_id].is_set():
            send_packets(host_id)
        else:
            slide_window(host_id)
            events[host_id].clear()

        

# binary search for index of packet in window
def get_index_of_ack_num(target, arr, l, r):
    if l>r:
        return -1
    mid = int((l+r)/2) 
    if arr[mid][0] == target:
        return mid
    if arr[mid][0] > target:
        return get_index_of_ack_num(target, arr, l, mid-1)

    return get_index_of_ack_num(target, arr, mid+1, r)
    

# gets an ACK packege and updates window associated with it
def handle_ack(addr, jrip_file):
    ip = addr[0]+":"+str(addr[1])
    ack_num = jrip_file["ACK"]-1
    copy_list = ack_window[ip][:]
    i = get_index_of_ack_num(ack_num, copy_list, 0, len(copy_list)-2)
    if i != -1 and copy_list[i][1] is False:
        with lock:
            ack_window[ip][i] = [ack_window[ip][i][0], True]
            ack_window[ip][5] = i
            events[ip].set()
            # print("{}".format(ack_window[ip]))
        

# gets data (ping) and responses with ACK if it comes in order
def handle_data(addr, jrip_file):
    seq_num = jrip_file["SEQ"]
    ack_pack = {}
    ack_pack["SEQ"] = -1
    ack_pack["ACK"] = ack_num
    ip, port = addr
    hid = ip+":"+port
    if hid not in last_seq:
        last_seq[hid] = 0
        
    if last_seq[hid] == seq_num:
        last_seq[hid] = last_seq[hid] + 1
        ack_pack = {}
        ack_pack["SEQ"] = -1
        ack_pack["ACK"] = last_seq[hid]
        ct = json.dumps(cost_table)
        sock.sendto(ct.encode(), (ip, int(port)))

# listens for all incoming packets and updates appropriate host handlers
def listener_thread(d1,d2):
    while True:
        data, addr = sock.recvfrom(4096)
        jrip_file = json.loads(data)
        args = (addr, jrip_file)
        if jrip_file["SEQ"] == -1:
            t = threading.Thread(target=handle_ack, args=args)
            t.start()
        else:
            t = threading.Thread(target=handle_data, args=args)
            t.start()

        #print(data)

# args is a dummy tuple
args = (0,0)
t = threading.Thread(target=listener_thread, args=args)
t.start()


# create a thread for every host given in command line
for k in cost_table["Data"]["RIPTable"]:
    with lock:
        ack_window[k["neighbor"]] = [[0,False],[1,False],[2,False],[3,False],[4,False], -1]
        events[k["neighbor"]] = threading.Event()
    aargs = (0,k["neighbor"])
    t = threading.Thread(target=neighbor_thread, args=aargs)
    t.start()
