#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Oct 24 21:12:17 2021
@author: Roei Gehasi and David Dinkevich
"""

import sys
import socket

# Checks if user inputted port number is valid
def validate_input(given_port):
    if not given_port.isdigit() or int(given_port) < 1 or int(given_port) > 65535:
        print("Invalid port number, try again. Terminating program...")
        sys.exit(1)
        
# Entry point for program
if __name__ == "__main__":
    # Get program args
    validate_input(sys.argv[1])
    port_num = int(sys.argv[1])
    
    # Open socket 
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # IPV4
    # Bind the IP address and the port number
    s.bind(('', port_num))
    previous_number = -1
    previous_data = None
    while True:
        # Wait and listen for info, max data size 1024
        data, addr = s.recvfrom(1024)
        current_number = int.from_bytes(data[0:10], 'little')
        if current_number == previous_number + 1:
            # Print what we received
            print(data.decode('UTF-8'), end="")
            previous_number = current_number
            previous_data = data
            # Return exactly what we received
            s.sendto(data, addr)
        else:
            s.sendto(previous_data, addr)
