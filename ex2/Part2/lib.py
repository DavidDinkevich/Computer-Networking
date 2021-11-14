#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

SEP_CHAR = '|'

lang = {
    "su": (0, 1),
    "pull": (1, 0),
    "mkfile": (2, 0),
    "movfile": (2, 0),
    "movdir": (2, 0),
    "rmf": (1, 0),
    "rmdir": (1, 0)  # Recursive
}


def sendToken(socket, cmd, args):
    msg = cmd + SEP_CHAR + SEP_CHAR.join(args)
    if len(args) > 0:
        msg += SEP_CHAR

    print("Sending message to client: ", msg)
    socket.send(msg.encode())


def getToken(socket, buff):
    '''
    we check if the buffer is empty.
    if its empty then we want to pull more data from the socket.
    '''
    if len(buff) == 0:
        data = socket.recv(1024)
        str_data = data.decode('utf8')
        temp = str_data.split(SEP_CHAR)[:-1]
        buff = buff + temp
        print('this is the buff after splitting:', buff)
    'whether its empty or not, we want to return one command_token from the buff list we have 😀'
    if len(buff) > 0:
        return buff, buff.pop(0)
    return buff, None
