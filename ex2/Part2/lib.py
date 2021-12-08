
import socket
import os
import time

MSG_LEN_NUM_BYTES = 4
decode_next_msg = True

def is_dir(relative_path):
    abs_path = os.path.abspath(relative_path)
    return os.path.isdir(abs_path)


def get_abs_path(path):
    return os.path.abspath(path)


def send_token(socket, args, encode=True):
    #assert len(args) > 0, "send_token: length of args in send_token must be > 0"
    if encode:
        for arg in args:
            encoded = arg.encode()
            len_bytes = len(encoded).to_bytes(MSG_LEN_NUM_BYTES, 'little')
            #print("Sending message: ", msg)
            socket.sendall(len_bytes + encoded)
    # in case its pure data and not files or dirs
    else:
        assert len(args) == 1, "send_token: encode=False but len(args) != 1"

        socket.sendall(args[0])
        #socket.sendall(SEP_CHAR.encode())

def get_token(socket, buff, decode=True, num_bytes_to_read=-1):
    global decode_next_msg
    # If buffer is empty, must read from socket
    if len(buff) == 0:
        if num_bytes_to_read >= 0:
            data = socket.recv(num_bytes_to_read)
            buff.append(data)
        else:
            msg_len = socket.recv(MSG_LEN_NUM_BYTES)
            num_bytes_to_read = int.from_bytes(msg_len, 'little')
            data = socket.recv(num_bytes_to_read)
            #print('Got raw: ', msg_len, data.decode())
            try:
                decoded = data.decode()
                if decode_next_msg:
                    buff.append(decoded)
                else:
                    buff.append(data)
            except:
                buff.append(data)
                #print('Uh oh... tried to decode:', decoded[:15], '...', decoded[-15:])

        print('Got message: ', num_bytes_to_read, buff[-1][:15], '...', buff[-1][-15:])
       # buff.extend(final_chunks)


    # whether its empty or not, we want to return one command_token from the buff list we have 😀'
    if len(buff) > 0:
       # print("Already have something", buff, buff[0])
        return buff, buff.pop(0)
    return buff, None

def send_file(my_socket, cmd, full_file_path, relative_path):
    file_size = str(os.path.getsize(full_file_path))
    send_token(my_socket, [cmd, relative_path, file_size])

    with open(full_file_path, 'rb') as f:
        data = f.read(2048)
        while len(data) > 0:
            send_token(my_socket, [data], encode=False)
            #my_socket.sendall(data)
            data = f.read(2048)

def rcv_file(my_socket, my_buff, abs_path):
    my_buff, size = get_token(my_socket, my_buff)

    size = int(size)
    while size > 0:
        chunk_size = min(size, 2048)
        size -= chunk_size
        my_buff, data = get_token(my_socket, my_buff, decode=False, num_bytes_to_read=chunk_size)
        #data = my_socket.recv(2048)
        # Read content and write to file
        size -= len(data)
        print('Need ', size, ' expected, ', chunk_size, ' got: ', len(data))
        print('Trying to write: ', data[:20], '...', data[-20:])
        write_data(abs_path, data)
    
        
def write_data(abs_path, data):
    with open(abs_path, 'ab') as f:
        f.write(data)

def create_file(abs_path):
    f = open(abs_path, 'w')
    f.close()
    
def remove_last_path_element(path):
    return path.split(os.path.sep)[-1], path[:path.rfind(os.path.sep)]

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
Given a folder, deletes the folders and all elements inside it.
'''
def deep_delete(top_root):
    for root, d_names, f_names in os.walk(top_root, topdown=False):
        for file in f_names:
            os.remove(os.path.join(root, file))
        for folder in d_names:    
            os.rmdir(os.path.join(root, folder))
    os.rmdir(top_root)

'''
Moves a folder that is either empty or unempty
'''
def move_folder(move_dir_path, new_path):
    # If folder doesn't exist, return
    if not os.path.exists(move_dir_path):
        return

    # If folder is empty, simply rename it
    if len(os.listdir(move_dir_path)) == 0:
        os.renames(move_dir_path, new_path)
        return

    # Get name of dir to be moved, as well as path of its parent dir
    move_dir_name, root_dir = remove_last_path_element(move_dir_path)
    # Get parent folder at destination
    _, dest_parent = remove_last_path_element(new_path)
    
    # Make empty folder at dest location
    os.mkdir(new_path)
    
    # Loop through contents
    for root, d_names, f_names in os.walk(move_dir_path, topdown=True):
        for file in f_names:
            # Move file
            os.renames(os.path.join(root, file), os.path.join(new_path, file))
        for folder in d_names:    
            # Move folder recursively
            move_folder(os.path.join(root, folder), os.path.join(new_path, folder))
     


def send_all_dirs_and_files(socket, dirs, files, dest_folder):
    for rel_path in (dirs + files):
        abs_path = os.path.join(dest_folder, rel_path)
        if rel_path in dirs:
            send_token(socket, ['mkdir', rel_path])
        else:
            send_file(socket, 'mkfile', abs_path, rel_path)

