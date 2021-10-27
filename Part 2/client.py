#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import socket


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
    # Get program arguments
    args_arr = sys.argv[1:]
    num_expected_args = 3

    # Check that we got the right num of args
    if len(args_arr) != num_expected_args:
        print('Please enter exactly three arguments: ')
        sys.exit(1)  # Exit

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
