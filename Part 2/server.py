#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 24 21:12:17 2021

@author: Roei Gehasi and David Dinkevich
"""

import sys
import socket

# Get program args
port_num = int(sys.argv[1])

# Open socket 
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                         # IPV4

# Bind the IP address and the port number
s.bind(('', port_num))

while True:
    # Wait and listen for info, max data size 1024
    data, addr = s.recvfrom(1024)
    # Print what we received
    print("Server: ", data, addr)
    # Return exactly what we received
    s.sendto(data, addr)
    