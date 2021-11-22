import os
import random
import socket
import string
import sys

import lib as lib
import time

port = int(sys.argv[1])
SERVER_DIR = "server_dir"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##this is about to be deleted when we submit
while True:
    try:
        server.bind(('', port))
        break
    except:
        print("Couldn't open server, trying again")
        time.sleep(3)
server.listen()
client_buff = []
account_map = {}
changes_map = {}
curr_client_id = None
curr_client_inst = None


def add_changes(key_tuple, value_tuple):
    for key in changes_map:
        # makes changes only if same id
        if key_tuple[0] == key[0] and key_tuple[1] != key[1]:
            # make the change for every other pc
            changes_map[key].append(value_tuple)


def generate_id():
    return str(''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10)))


def create_dir(path_name):
    path = os.path.join(SERVER_DIR, path_name)
    if not os.path.exists(path):
        os.mkdir(os.path.join(SERVER_DIR, path_name))


def identify_new_client():
    global client_buff, curr_client_id, curr_client_inst
    client_buff, curr_client_id = lib.getToken(client_socket, client_buff)
    client_buff, curr_client_inst = lib.getToken(client_socket, client_buff)
    if curr_client_inst == '-1':
        new_inst_id = str(account_map[curr_client_id] + 1)
        lib.sendToken(client_socket, new_inst_id, [])


# need to adjust client to its file when client is making any changes.
def process_command(command):
    global last_file_created
    global client_buff
    if command == 'identify':
        identify_new_client()
    elif command == 'de':
        get_de()
    elif command == 'su':
        get_su()
    elif command == 'pull':
        get_pull()
    elif command_token == 'mkdir':
        mk_dir()
    elif command_token == 'mkfile':
        rcv_file()
    elif command_token == 'rmdir' or command_token == 'rmfile':
        ##operate remove dir, creat array and send it to the fucntion in utils.
        rm_dir_or_file()


'''
rn_dir_or_file:
function is based on util's func, which removes dir or files from given's path
'''


def rm_dir_or_file():
    global client_buff
    client_buff, folder_name = lib.getToken(client_socket, client_buff)
    abs_path = os.path.join(SERVER_DIR, curr_client_id)
    lib.remove_all_files_and_dirs([folder_name], abs_path)
    # add it to queue for all other computers
    # check if its file or path and send command token accordingly
    if os.path.isdir(abs_path):
        add_changes((curr_client_id, curr_client_inst), ('rmdir', folder_name))
    elif os.path.isfile(abs_path):
        add_changes((curr_client_id, curr_client_inst), ('rmfile', folder_name))


def get_de():
    client_folder = os.path.join(SERVER_DIR, curr_client_id)
    lib.get_dirs_and_files(client_folder)
    dirs, files = lib.get_dirs_and_files(client_folder)
    for item in (dirs + files):
        original_path = os.path.join(client_folder, item)
        if item in dirs:
            lib.sendToken(client_socket, 'mkdir', [item])
        else:
            lib.send_data(client_socket, original_path, item)
    lib.sendToken(client_socket, 'eoc', [])


def get_su():
    client_id = generate_id()
    # Add client to accounts map
    account_map[client_id] = 0
    # Add client to changes map
    changes_map[(client_id, '0')] = []

    # Create client's directory
    creat_dir(client_id)
    # Send client their new ID
    lib.sendToken(client_socket, client_id, [])


def mk_dir():
    global client_buff
    client_buff, folder_name = lib.getToken(client_socket, client_buff)
    folder_path = os.path.join(curr_client_id, folder_name)
    lib.create_dir(os.path.join(SERVER_DIR, folder_path))
    add_changes((curr_client_id, curr_client_inst), ('mkdir', folder_name))


def dequeue_all(queue):
    while len(queue) > 0:
        # item= tuple= (command_token,relative_path)
        item = queue.pop(0)
        # send the token to the client
        lib.sendToken(client_socket, item[0], [item[1]])
        # in case command is mkfile
        # need to test it
        if item[0] == 'mkfile':
            abs_path = os.path.join(SERVER_DIR, item[1])
            lib.send_data(client_socket, abs_path, item[1])


'''
get_pull()
operating pull by client request.
updating client with server's updated files
'''


def get_pull():
    '''
    if were here we assume that the client has already a folder in server
    and therefore its key already in the map.
    '''
    global client_buff, curr_client_id, curr_client_inst
    # Create key for changes map
    changes_key = (curr_client_id, curr_client_inst)
    print('changes map:', changes_map)
    # check if the map is empty
    if len(changes_map[changes_key]) > 0:
        dequeue_all(changes_map[changes_key])
    lib.sendToken(client_socket, 'eoc', [])
    print("server sent eoc")

    # print("this is client buffer:", client_buff)
    # print("client_id:", client_id)

    # client_dir_path = os.path.join(SERVER_DIR, client_id)
    # for root, d_names, f_names in os.walk(client_dir_path):
    #     dirs_then_names = d_names + f_names
    #     print("dir names:" + str(d_names) + "file names: " + str(f_names))
    #     for item in dirs_then_names:
    #         # dir_name = deep_dir
    #         # root server/id/Dirdir
    #         original_path = os.path.join(root, item)
    #         relative_path = os.path.join(root[len(client_dir_path) + 1:], item)
    #         if item in d_names:
    #             lib.sendToken(client_socket, 'mkdir', [relative_path])
    #         else:
    #             lib.send_data(client_socket, original_path, relative_path)


'''
func is responsible to make file in client's file on server.
'''


def rcv_file():
    global client_buff, client_socket, client_address
    client_buff, file_name = lib.getToken(client_socket, client_buff)
    temp_path = os.path.join(SERVER_DIR, curr_client_id)
    file_path = os.path.join(temp_path, file_name)
    lib.create_file(temp_path, file_name)
    # receive data now
    lib.rcv_file(client_socket, client_buff, file_path)
    add_changes((curr_client_id, curr_client_inst), ('mkfile', file_name))


def creat_dir(name):
    os.mkdir(os.path.join(SERVER_DIR, name))


if __name__ == "__main__":
    while True:
        print("ready to accept")
        client_socket, client_address = server.accept()
        print('Connection from: ', client_address)
        while True:
            try:
                time.sleep(1)
            except:
                sys.exit(1)
            client_buff, command_token = lib.getToken(client_socket, client_buff)
            print("command token:", command_token)
            if command_token == 'fin' or command_token is None:
                print("were breaking")
                break
            process_command(command_token)
        client_socket.close()
