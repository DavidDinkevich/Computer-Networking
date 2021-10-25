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
previous_number=-1
previous_data=None
while True:
        # Wait and listen for info, max data size 1024
        data, addr = s.recvfrom(1024)
        current_number=int.from_bytes(data[0:10],'little')
        print(current_number)
        if current_number == previous_number+1:
            # Print what we received
            print("Server: ", data, addr)
            previous_number=current_number
            # Return exactly what we received
            s.sendto(data, addr)
            previous_data=data
        else:
            s.sendto(previous_data,addr)
            

    