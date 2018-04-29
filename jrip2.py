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
import json, copy, argparse

lock = threading.Lock()   # lock variables from being accessed by more than one thread
ack_window = {}           # holds ack records for eack host
events = {}               # dict of events per host
pinging_me = {}           # dict of hosts who pinged me


sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

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
    h, p = hosts[i].split(":")
    temp = {}

    check = re.search('[a-zA-Z]', h)
    if check is not None:
        h = socket.gethostbyname(h)

    temp["neighbor"] = h+":"+p
    temp["cost"] = 0
    cost_table["Data"]["RIPTable"].append(copy.deepcopy(temp))

cost_json = json.dumps(cost_table)

def listener_thread():
    while True:
        print("listening")
        data, addr = sock.recvfrom(4096)
        jrip_file = json.loads(data)
        args = (addr, jrip_file)
        print("ack:{} seq:{} from: {}".format(jrip_file["ACK"],jrip_file["SEQ"],  addr))
        if jrip_file["SEQ"] == -1:
            print("going to handle the ack")
            t = threading.Thread(target=handle_ack, args=args)
            t.start()
        else:
            print("going to handle the ping")
            t = threading.Thread(target=handle_ping, args=args)
            t.start()

def handle_ping(addr, jrip_file):
    hid = str(addr[0])+":"+str(addr[1])
    seq_num = jrip_file["SEQ"]
    
    with lock:
        if hid not in pinging_me:
            pinging_me[hid] = 0
        
        expecting = pinging_me[hid]
        if expecting <= seq_num:
            pinging_me[hid] = expecting + 1 if int(expecting) == int(seq_num) else expecting
            cost_table["ACK"] = pinging_me[hid]
            cost_table["SEQ"] = -1
            sock.sendto(json.dumps(cost_table).encode(), (addr[0], int(addr[1])))


def handle_ack(addr, jrip_file):
    print("handeling ack ")
    hid = str(addr[0])+":"+str(addr[1])
    ack_num = jrip_file["ACK"] - 1
    if ack_num <= 100:
        print("ack num is {}".format(ack_num))
        with lock:
            win_copy = copy.deepcopy(ack_window[hid])
        
        win_copy = win_copy[:-1]

        i = get_index_ack(ack_num, win_copy, 0, len(win_copy)-1)
        if i != -1 and win_copy[i][1] is False:
            print("i is {}".format(i))
            win_copy[i] = [win_copy[i][0],True]
            win_copy.append(i)
            print("made changes")
            with lock:
                ack_window[hid] = copy.deepcopy(win_copy)
                print("original table is {}".format(ack_window[hid))

            events[hid].set()

def get_index_ack(target, arr, l, r):
    if l>r:
        return -1
    
    mid = int((l+r)/2)
    if target == arr[mid][0]:
        return mid
    
    if target > arr[mid][0]:
        return get_index_ack(target,arr, l, mid-1)
    
    return get_index_ack(target, arr, mid+1, r)

def send_packets(hid):
    with lock:
        win_copy = copy.deepcopy(ack_window[hid])
        win_copy = win_copy[:-1]
        last = 0 + ack_window[hid][-1:][0]
        dic = dict(cost_table)

    if len(win_copy) >= 1:
        ip, port = hid.split(":")
        change = 0 if last == -1 else last
        #print("sending packets {}-{} to {}".format(change, change+4, hid))
        for i in range(change, len(win_copy)):
            if random.randint(0,100) >= loss_rate:
                dic["SEQ"] = win_copy[i][0]
                sock.sendto(json.dumps(dic).encode(), (ip, int(port)))
            else:
                with lock:
                    ack_window[hid+"D"] = ack_window[hid+"D"] + 1
            with lock:
                ack_window[hid+"T"] = ack_window[hid+"T"] + 1

def slide_window(hid):
    with lock:
        win_copy = copy.deepcopy(ack_window[hid])
        win_copy = win_copy[:-1]
        change = ack_window[hid][-1]
    
    if len(win_copy) > 0 and change > -1:

        curr = win_copy[change][0]+1
        win_copy = []
        for i in range(curr, curr+5):
            if i<100:
                win_copy.append([i,False])
    
    win_copy.append(-1)
    
    with lock:
        ack_window[hid] = copy.deepcopy(win_copy)


def neighbor_thread(a, hid):
    while True:
        with lock:
            if len(ack_window[hid]) <= 1:
                drop = ack_window[hid+"D"]
                total = ack_window[hid+"T"]
                rate = int(((total-drop)/total)*100)
                print("Goodput Rate at {} {}/100".format(hid, rate))
                exit()

        
        events[hid].wait(0.5)
        if not events[hid].is_set():
            send_packets(hid)

        slide_window(hid)
        events[hid].clear()
        send_packets(hid)

# call listenning thread
t = threading.Thread(target=listener_thread)
t.start()


# create a thread for every host given in command line
for k in cost_table["Data"]["RIPTable"]:
    with lock:
        hid = str(k["neighbor"])
        ack_window[hid] = [[0, False], [1, False],[2, False], [3, False], [4, False], -1]
        ack_window[hid+"D"] = 0 # drop rate
        ack_window[hid+"T"] = 0 # total sent
        events[hid] = threading.Event()
    args=(True, hid)
    t = threading.Thread(target=neighbor_thread, args=args)
    t.start()
