import socket, time, json
import threading, sys

#data = json.load(open('mytable.json'))

UDP_IP = "127.0.0.1"
UDP_PORT = 5005

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind(('', UDP_PORT))

def on_new_connection(data, addr):
    '''jrip_file = json.loads(data)
    jrip_type = jrip_file["Data"]["Type"]
    ack_num = jrip_file["ACK"]
    
    if jrip_type == "JRIP":
        print("jrip ya'll")
        print(jrip_file["SEQ"])
    else:
        print("trace aruluuuu")
    '''
    print("got it!")
    sock.sendto(bytes("got it",'utf-8'), (addr[0], addr[1]))
    '''
    if int(ack_num) == 0:
        return
    '''

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    args = (data, addr)
    t = threading.Thread(target=on_new_connection, args=args)
    t.start()
    t.join()

