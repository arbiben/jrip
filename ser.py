#!/usr/bin/env python

import socket, time, json
import threading, sys, random
last =-1
#data = json.load(open('mytable.json'))
UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind(('', UDP_PORT))

cost_table = {}
cost_table["SEQ"] = 1
cost_table["ACK"] = 0
cost_table["Data"] = {}
cost_table["Data"]["Type"] = "JRIP"
cost_table["Data"]["RIPTable"] = []

def on_new_connection(data, addr):
    global last
 #   print(data)
    jrip_file = json.loads(data)
    jrip_type = jrip_file["Data"]["Type"]
    seq_num = jrip_file["SEQ"]
    #print("last pack num is {}".format(last)) 
    if jrip_type == "JRIP":
        print(last)
        if seq_num <= last+1:
            last = last + 1
            cost_table["ACK"] = seq_num+1
            cost_table["SEQ"] = -1
            ct = json.dumps(cost_table)
            print("sent ACK for {}".format(last-1))
            sock.sendto(ct.encode(), (addr[0], addr[1]))
                #print("sent ACK {} to {}".format(seq_num+1, addr))
        #else:
            #print("got packet {}".format(seq_num))
    else:
        print("trace aruluuuu")
   
    #print("got msg from {}".format(addr))
    #sock.sendto(bytes("got it",'utf-8'), (addr[0], addr[1]))


if __name__=='__main__':
 
    while True:
        data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
        args = (data, addr)
        t = threading.Thread(target=on_new_connection, args=args)
        t.start()
        t.join()
