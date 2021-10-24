#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 21 16:32:46 2021

@author: david
"""

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                         # IPV4

# Bind the IP address and the port number
s.bind(('', 12345))

while True:
    # Wait and listen for info, max data size 1024
    data, addr = s.recvfrom(1024)
    print("Server: ", str(data), addr)
    s.sendto(b'Server: Hello ' + data.upper(), addr)
    