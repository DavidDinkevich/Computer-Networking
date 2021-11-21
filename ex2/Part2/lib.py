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
##need to move into lib library
def create_dir(abs_path):
    if not os.path.exists(abs_path):
        os.mkdir(abs_path)

def remove_all_files_and_dirs(to_remove,serv_client_path):
    for item in to_remove:
        local_path = os.path.join(serv_client_path, item)
        # Check if exists, just in case
        if not os.path.exists(local_path):
            continue
        # Delete if file
        if os.path.isfile(local_path):
            os.remove(local_path)
        else:  # Delete if directory
            os.rmdir(local_path)

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



'''
sending data from client to server and vice versa
we assume that file path is the full path of the file(includes the server/client's path accordingly)
'''


def send_data(my_socket, full_file_path, relative_path):
    sendToken(my_socket, 'mkfile', [relative_path])
    # modtime is the last time the file has been modified
    modtime = os.stat(full_file_path)[7]
    #sendToken(my_socket, 'modtime', [str(modtime)])
    with open(full_file_path, 'rb') as f:
        data = f.read(1024)
        if len(data) > 0:
            sendToken(my_socket, 'data', [])
            while data:
                sendToken(my_socket, 'data', [data], False)
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

def rcv_file(my_socket, my_buff, abs_path):
    while True:
        # Extract token and update
        my_buff, command_token = getToken(my_socket, my_buff)
        # Exit condition
        if command_token != 'data' or command_token is None:
            my_buff.insert(0, command_token)
            break
        # Read content and write to file
        my_buff, content_token = getToken(my_socket, my_buff)
        write_data(abs_path, content_token.encode('utf8'))