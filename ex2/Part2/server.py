import os
import random
import socket
import string
import sys

import lib as lib
import time

SERVER_DIR = "server_dir"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
##this is about to be deleted when we submit
while True:
    try:
        server.bind(('', 12345))
        break
    except:
        print("Couldn't open server, trying again")
        time.sleep(3)
server.listen()
client_buff = []
account_map = {}
make_changes_map={}



def generate_id():
    return str(''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10)))


def create_dir(path_name):
    path = os.path.join(SERVER_DIR, path_name)
    if not os.path.exists(path):
        os.mkdir(os.path.join(SERVER_DIR, path_name))


def update_accounts_map(id, client_address):
    if id in account_map and client_address not in account_map[id]:
        account_map[id].append(client_address)
    else:
        account_map[id] = [client_address]


# need to adjust client to its file when client is making any changes.
def process_command(command):
    global last_file_created
    global client_buff
    if command == 'su':
        get_su()
    elif command == 'list':
        get_list()
    elif command == 'pull':
        get_pull()
    elif command_token == 'mkdir':
        mk_dir()
    elif command_token == 'mkfile':
        rcv_file()
    elif command_token == 'rmdir':
        ##operate remove dir, creat array and send it to the fucntion in utils.
        rm_dir_or_file()
    elif command_token == 'rmfile':
        # removing file
        rm_dir_or_file()


'''
rn_dir_or_file:
function is based on util's func, which removes dir or files from given's path
'''


def rm_dir_or_file():
    global client_buff
    client_id = find_id(client_address)
    client_buff, folder_name = lib.getToken(client_socket, client_buff)
    abs_path = os.path.join(SERVER_DIR, client_id)
    lib.remove_all_files_and_dirs([folder_name], abs_path)


def get_su():
    client_id = generate_id()
    update_accounts_map(client_id, client_address)
    lib.sendToken(client_socket, client_id, [])
    creat_dir(client_id)


def mk_dir():
    global client_buff
    client_id = find_id(client_address)
    client_buff, folder_name = lib.getToken(client_socket, client_buff)
    folder_path = os.path.join(client_id, folder_name)
    lib.create_dir(os.path.join(SERVER_DIR, folder_path))



'''
making list of files from client id's folder 
'''


def get_list():
    global client_buff

    print('Answering list request')
    client_buff, client_id = lib.getToken(client_socket, client_buff)
    update_accounts_map(client_id,client_address)
    client_dir = os.path.join(SERVER_DIR, str(client_id))
    # Get all client's directories and files
    dirs, files = lib.get_dirs_and_files(client_dir)
    # Send each as individual token
    for directory in dirs:
        lib.sendToken(client_socket, 'mkdir', [directory])
    for file in files:
        lib.sendToken(client_socket, 'mkfile', [file])
    # Signal end of data stream
    lib.sendToken(client_socket, 'eoc', [])


'''
operating pull by client request.
updating client with server's updated files
'''


def get_pull():
    global client_buff
    client_buff, client_id = lib.getToken(client_socket, client_buff)
    update_accounts_map(client_id, client_address)
    print("this is client buffer:", client_buff)
    print("client_id:", client_id)
    client_dir_path = os.path.join(SERVER_DIR, client_id)
    for root, d_names, f_names in os.walk(client_dir_path):
        dirs_then_names = d_names + f_names
        print("dir names:" + str(d_names) + "file names: " + str(f_names))
        for item in dirs_then_names:
            # dir_name = deep_dir
            # root server/id/Dirdir
            original_path = os.path.join(root, item)
            relative_path = os.path.join(root[len(client_dir_path) + 1:], item)
            if item in d_names:
                lib.sendToken(client_socket, 'mkdir', [relative_path])
            else:
                lib.send_data(client_socket, original_path, relative_path)
    lib.sendToken(client_socket, 'eoc', [])


'''
func is responsible to make file in client's file on server.
'''


def rcv_file():
    global client_buff, client_socket, client_address
    client_id = find_id(client_address)
    client_buff, file_name = lib.getToken(client_socket, client_buff)
    temp_path = os.path.join(SERVER_DIR, client_id)
    file_path = os.path.join(temp_path, file_name)
    lib.create_file(temp_path, file_name)
    # receive data now
    lib.rcv_file(client_socket, client_buff, file_path)


def find_id(client_adress):
    for client_id in account_map.keys():
        for client_info in account_map[client_id]:
            if client_info[0] == client_adress[0]:
                return str(client_id)
    return None


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
            print("command token:",command_token)
            if command_token == 'fin' or command_token is None:
                print("were breaking")
                break
            process_command(command_token)
        client_socket.close()
