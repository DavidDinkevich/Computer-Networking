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
    "fin": (0, 0),
}


def sendToken(socket, cmd, args, encode=True):
    # msg = cmd.encode('utf8') + SEP_CHAR
    if encode:
        msg = cmd + SEP_CHAR + SEP_CHAR.join(args)
        if len(args) > 0:
            msg += SEP_CHAR
        print("Sending message to client: ", msg)
        socket.send(msg.encode('utf8'))
    # in case its pure data and not files or dirs
    else:
        socket.send(args[0])
        socket.send(SEP_CHAR.encode('utf8'))


def getToken(socket, buff, decode=True):
    '''
    we check if the buffer is empty.
    if its empty then we want to pull more data from the socket.
    '''
    if len(buff) == 0:
        # need to check buffer limit, if there is still data left to pull.
        data = socket.recv(1024)
        if decode:
            str_data = data.decode('utf8')
            temp = str_data.split(SEP_CHAR)[:-1]
            buff = buff + temp
        else:
            buff.append(data)
    # 'whether its empty or not, we want to return one command_token from the buff list we have 😀'
    if len(buff) > 0:
        return buff, buff.pop(0)
    return buff, None


def create_file(path_name, file_name):
    path = os.path.join(path_name, file_name)
    f = open(path, 'w')
    f.close()


def send_data(socket, file_path):
    with open(file_path, 'rb') as f:
        data = f.read(1024)
        sendToken(socket, 'data', [])
        while data:
            sendToken(socket, 'data', [data], False)
            data = f.read(1024)


# get the bytes from server/client and write them into an existed file
def write_data(file_path, data):
    with open(file_path, 'r+b') as f:
        f.write(data)
        
'''
Returns two arrays, the first containing all of the subdirectories
(of all depths) of top_root, and the second containing all of the files
(of all depths) of top_root. All paths do not begin with top_root.
'''
def get_dirs_and_files(top_root):
    dirs = []
    files = []
    for root, d_names, f_names in os.walk(top_root):
        dirs_then_names = d_names + f_names
        for item in dirs_then_names:
            whole_path = os.path.join(root, item)
            whole_path = whole_path[len(top_root) + 1:]
            if item in d_names:
                dirs.append(whole_path)
            else:
                files.append(whole_path)
    return dirs, files

'''
Receives four arrays:
    1) An array of the subdirectories (of all depths) in directory 1
    2) An array of the files (of all depths) in directory 1
    1) An array of the subdirectories (of all depths) in directory 2
    1) An array of the files (of all depths) in directory 2
Returns two arrays, the first containing all of the directories and files 
that dir1 contains and dir2 doesn't contain (starting with files, and
then directories). The second contains all of the directories and files that dir2
contains and dir1 does not contain (starting with directories, and then
files)
'''
def diff(dir1_dirs, dir1_files, dir2_dirs, dir2_files):
    
    to_remove = list(set(dir1_files) - set(dir2_files)) + list(set(dir1_dirs) - set(dir2_dirs))    
    to_add = list(set(dir2_dirs) - set(dir1_dirs)) + list(set(dir2_files) - set(dir1_files))
    
    return to_remove, to_add

