import os
import random
import socket
import string
import lib as lib

SERVER_DIR = "server_dir"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
server.listen()
client_buff = []
account_map = {}


def generate_id():
    return str(''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10)))


def update_accounts_map(id, client_socket, client_address):
    if id in account_map:
        account_map[id].append((client_socket, client_address))
    else:
        account_map[id] = []
        account_map[id] = [(client_socket, client_address)]


def process_command(command, client_socket, client_address):
    global client_buff
    if command == 'su':
        client_id = generate_id()
        update_accounts_map(client_id, client_socket, client_address)
        lib.sendToken(client_socket, client_id, [])
        creat_dir(client_id)
    elif command == 'pull':
        client_buff, client_id = lib.getToken(client_socket, client_buff)
        print("this is client buffer:", client_buff)
        for root, d_names, f_names in os.walk(client_id):
            if len(d_names) == 0:
                continue
            for dir_f in d_names:
                print('-' + dir_f + '-')
                dir_name = dir_f
                if root != SERVER_DIR:
                    dir_name += root
                if dir_f == '':
                    continue
                lib.sendToken(client_socket, 'mkdir', [dir_name])


def creat_dir(name):
    os.mkdir(os.path.join(SERVER_DIR, name))


if __name__ == "__main__":
    while True:
        client_socket, client_address = server.accept()
        print('Connection from: ', client_address)
        client_buff, command_token = lib.getToken(client_socket, client_buff)
        process_command(command_token, client_socket, client_address)
        client_buff, pull_token = lib.getToken(client_socket, client_buff)
        print('this is pull token:', pull_token)
        process_command(pull_token, client_socket, client_address)
        client_socket.close()
