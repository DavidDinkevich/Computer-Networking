#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import socket


def read_unit_from_file(file, unit_id):
    print("Called")
    # Read 90 bytes from the file
    data = file.read(90)
    # Convert counter to bytes
    id_str = unit_id.to_bytes(10, 'little')
    print(id_str)
    # Put together package
    return id_str + data

def verify_message(original, received):
    return original == received
        


if __name__ == "__main__":    
    # Get program arguments
    args_arr = sys.argv[1:]
    num_expected_args = 3
    
    # Check that we got the right num of args
    while len(args_arr) != num_expected_args:
        inp = input('Please enter exactly three arguments: ')
        args_arr = inp.split(' ')
    
    # Extract arguments    
    ip = args_arr[0]
    port_num = int(args_arr[1])
    file_name = args_arr[2]
    
    # Open file and read procedurally
    file = open(file_name, 'rb')    
    
    # Open socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    
    counter = 0 # Tracks message ID
    message = read_unit_from_file(file, counter)
    # While we can still extract units of data from the file
    while message == None or len(message) > 10:
        # Keep sending messages until it is received successfully
        data = None
        while data == None or not verify_message(message, data):
            # Send message
            s.sendto(message, (ip, port_num))
            
            # Get return message
            data, addr = s.recvfrom(1024)
            #print(str(data), addr)

        # Increase message ID
        counter += 1
        # Read next package from file
        message = read_unit_from_file(file, counter)        

    s.close() # Close socket
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    