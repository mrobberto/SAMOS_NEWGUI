#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 14 22:21:25 2023

@author: robberto

from:
https://forums.ni.com/t5/LabVIEW/Python-client-to-unflatten-received-string-from-TCP-Labview/td-p/3353270/page/4
"""

import struct
import socket
import numpy as np

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

#bind_ip = get_ip()

print("\n\n[*] Current ip is %s" % (get_ip()))
bind_ip = ''
bind_port = 6502

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((bind_ip,bind_port))  

print("[*] Ready to receive UDP on %s:%d" % (bind_ip,bind_port))

while True:
    data, address = server.recvfrom(1024)
    print('[*] Received %s bytes from %s:' % (len(data), address))

    arrLen = struct.unpack('>i', data[:4])[0]
    print('[*] Received array of %d doubles:' % (arrLen,))
    x = []
    elt = struct.iter_unpack('>d', data[4:])
    while True:
        try:
            x.append(next(elt)[0])
            print(x[-1])
        except StopIteration:
            break
    x = np.array(x)
    y = x+1 # np.sin(x)
    msg = data[:4]
    for item in y:
        msg += struct.pack('>d', item)
    print(msg)
    A = (address[0], 6503)
    server.sendto(msg, A)
    break

server.close()
print('[*] Server closed')
print('[*] Done')