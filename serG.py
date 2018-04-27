#!/usr/bin/env python
from time import sleep
import socket, sys, argparse, json

def send(sock, data, host, port):
        sock.connect((host,port))
        sock.sendall(data)
        print "[{}] --> {}".format((host,port), data)

if __name__ == '__main__':
        parse = argparse.ArgumentParser()
        parse.add_argument('--host', required=True, dest='host')
        parse.add_argument('-p', required=True, dest='port')
        parse.add_argument('target')
        args = vars(parse.parse_args())

        host = args['host']
        port = int(args['port'])
        sys.stdout.write("Host: {}\nPort: {}\n".format(host, port))
        print "target: {}".format(args['target'])

        while (1):
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.bind((host,port))
            data, addr = sock.recvfrom(4096)
            #data = data.replace("'","\"")
            #jason = json.loads(data)
            data = str(data).replace('seq','ack')
            print data
            sys.stdout.write("Received data from {} --> {}\n".format(addr, data))
            tmp = args['target'].split(':')
            host = tmp[0]
            port = tmp[1]
            send(sock, data, host, int(port))
            sock.close()