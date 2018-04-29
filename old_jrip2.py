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
    h,p = hosts[i].split(":")
    temp = {}
    
    check = re.search('[a-zA-Z]', h)
    if check is not None:
        h = socket.gethostbyname(h)
    
    temp["neighbor"] = h+":"+p
    temp["cost"] = 0 
    cost_table["Data"]["RIPTable"].append(copy.deepcopy(temp))

cost_json = json.dumps(cost_table)


# change the window based on ACK received and resend new packets
# TODO ADJUST WINDOW SIZE AFTER PASSING 95 PACKETS ACK
def slide_window(hid):
    temp_window = []
    last = 0
    with lock:
        cop = ack_window[hid][:]

    win_size = len(cop) - 1
    if len(cop) <= 1:
        return
    change = int(cop[win_size])
    if change == -1:
        return
    last = cop[change][0]

    for _ in range(win_size-1):
        last = last+1
        if last < 100:
            temp_window.append([last, False])
    
    with lock:
        # update the receive window
        ack_window[hid] = copy.deepcopy(temp_window)
        ack_window[hid].append(-1)
        
# send packets from index to end of window
def send_packets(hid):
    ip, port = hid.split(":")
    win_size = 0
    drop = hid+"D"
    total = hid+"T"
    with lock:

        win_size = len(ack_window[hid]) - 1
        print(ack_window[hid])
        if len(ack_window[hid]) <= 1:
            return
        did_change = ack_window[hid][win_size]

        if did_change==-1:
            did_change = 0
        
        for i in range(did_change,win_size):
            rand = random.randint(0,100)
            if rand >= loss_rate:
                cost_table["SEQ"] = ack_window[hid][i][0]
                sock.sendto(json.dumps(cost_table).encode(), (ip,int(port)))
            else:
                ack_window[drop] = 1 + ack_window[drop]

            ack_window[total] = 1 + ack_window[total]

# thread that manages a specific connection
# TODO manage time outs
def neighbor_thread(d, host_id):
    while True:
        last = False
        with lock:
            if len(ack_window[host_id]) <= 1:
                last = True
        if last:
            drop = host_id+"D"
            total = host_id+"T"
            with lock:
                print("Goodput Rate at {} {}/100".format(host_id, int(100*(ack_window[drop]/ack_window[total]))))
            exit()
        
        events[host_id].wait(1)
        if not events[host_id].is_set():
            send_packets(host_id)

        slide_window(host_id)
        events[host_id].clear()
        send_packets(host_id)

        

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
    ip2 = ip+"A"
    ack_num = jrip_file["ACK"]-1
    if ack_num >= 100:
        with lock:
            ack_window[ip] = []
            ack_window[ip2] = True
        return
    copy_list = ack_window[ip][:]
    i = get_index_of_ack_num(ack_num, copy_list, 0, len(copy_list)-2)
    if i != -1 and copy_list[i][1] is False:
        with lock:
            win_size = len(ack_window[hid]) - 1 
            ack_window[ip][i] = [ack_window[ip][i][0], True]
            ack_window[ip][win_size] = i
            events[ip].set()
    slide_window(ip)   

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


# args is a dummy tuple
args = (0,0)
t = threading.Thread(target=listener_thread, args=args)
t.start()


# create a thread for every host given in command line
for k in cost_table["Data"]["RIPTable"]:
    with lock:
        hid = k["neighbor"]
        drop = hid+"D"
        total = hid+"T"
        ack_window[hid] = [[0,False],[1,False],[2,False],[3,False],[4,False], -1]
        ack_window[drop] = 0
        ack_window[total] = 0
        events[hid] = threading.Event()
    aargs = (0,hid)
    t = threading.Thread(target=neighbor_thread, args=aargs)
    t.start()
