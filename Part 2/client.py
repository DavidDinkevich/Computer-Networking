#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import socket


def validate_input(args):
    # Check that we got the right num of args
    num_expected_args = 3
    if len(args) != num_expected_args:
        print('Please enter exactly three arguments: ')
        sys.exit(1)  # Exit

    # VALIDATE GIVEN INPUT
    bad_input = False
    
    # Validate IP
    try:
        socket.inet_aton(args[0])
        # If we got here, IP is legal
    except socket.error:
        # IP is illegal
        print('Invalid IP address')
        bad_input = True

    # Validate port number
    # Checks if user inputted port number is valid
    if not args[1].isdigit() or int(args[1]) < 1 or int(args[1]) > 65535:
        print("Invalid port number")
        bad_input = True
        
    # Validate file name
    file = None
    try:
        file = open(args[2], 'rb')
        file.close()
    except:
        print('Given file does not exist')
        bad_input = True        
    
    if bad_input:
        print('Try executing the program again. Terminating...')
        sys.exit(1)
    


def read_unit_from_file(file, unit_id):
    # Read 90 bytes from the file
    data = file.read(90)
    # Convert counter to bytes
    id_str = unit_id.to_bytes(10, 'little')
    # Put together package
    return id_str + data


def verify_message(original, received):
    return original == received


if __name__ == "__main__":
    # Get program arguments (ip, port_num, file_name)
    args_arr = sys.argv[1:]
    validate_input(args_arr) # Validate input

    # Extract arguments    
    ip = args_arr[0]
    port_num = int(args_arr[1])
    file_name = args_arr[2]

    # Open file and read procedurally
    file = open(file_name, 'rb')

    # Open socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(15)
    counter = 0  # Tracks message ID
    message = read_unit_from_file(file, counter)
    # While we can still extract units of data from the file
    while message == None or len(message) > 10:
        # Keep sending messages until it is received successfully
        data = None
        while data == None or not verify_message(message, data):
            # Trying to Send a message
            try:
                s.sendto(message, (ip, port_num))

                # Get return message
                # we define a new protocol which says:
                # if the message didnt arrive in atmost 500 MS, the message will
                # be sent again
                data, addr = s.recvfrom(1024)

            except socket.timeout:
                continue

        # Increase message ID
        counter += 1
        # Read next package from file
        message = read_unit_from_file(file, counter)

    s.close()  # Close socket
