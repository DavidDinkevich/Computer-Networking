#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket
import os

SEP_CHAR = '|'

lang = {
    "su": (0, 1),
    "pull": (1, 0),
    "mkfile": (2, 0),
    "movfile": (2, 0),
    "movdir": (2, 0),
    "rmf": (1, 0),
    "rmdir": (1, 0),  # Recursive
    "data": (1, 0),
    "fin": (0, 0)
}


def sendToken(socket, cmd, args):
    msg = cmd + SEP_CHAR + SEP_CHAR.join(args)
    if len(args) > 0:
        msg += SEP_CHAR

    print("Sending message to client: ", msg)
    socket.send(msg.encode('utf8'))


def getToken(socket, buff):
    '''
    we check if the buffer is empty.
    if its empty then we want to pull more data from the socket.
    '''
    if len(buff) == 0:
        # need to check buffer limit, if there is still data left to pull.
        data = socket.recv(1024)
        str_data = data.decode('utf8')
        temp = str_data.split(SEP_CHAR)[:-1]
        buff = buff + temp
        # print('this is the buff after splitting:', buff)
    # 'whether its empty or not, we want to return one command_token from the buff list we have 😀'
    if len(buff) > 0:
        return buff, buff.pop(0)
    return buff, None


def creat_file(path_name, file_name):
    path = os.path.join(path_name, file_name)
    open(path, 'w')


def send_data(socket, file_path):
    with open(file_path, 'rb') as f:
        data = f.read(1024)
        while data:
            sendToken(socket, 'data', [data.decode('utf8')])
            data = f.read(1024)


# get the bytes from server/client and write them into an existed file
def write_data(file_path, data):
    with open(file_path, 'r+b') as f:
        f.write(data)
