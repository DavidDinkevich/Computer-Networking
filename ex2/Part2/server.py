
import socket
import time
import lib
import sys
import random
import string
import os

SERVER_DIR = "server_dir"
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_rcv_buff = []


curr_client_id = None
curr_client_inst = None
global client_socket
global client_addr

# Maps account id to number of instances logged in to that id
instance_count_map = {}

def generate_id():
    return str(''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10)))



def identify_new_client():
    global server_rcv_buff, curr_client_id, curr_client_inst, instance_account_map
    # Get client id
    server_rcv_buff, curr_client_id = lib.get_token(client_socket, server_rcv_buff)
    # Get client instance num
    server_rcv_buff, curr_client_inst = lib.get_token(client_socket, server_rcv_buff)
    if curr_client_id == '-1':
        # Generate and send new ID for client
        new_id = generate_id()
        # Update variable
        curr_client_id = new_id
        # Add new ID to instance_count_map
        instance_count_map[new_id] = 0
        # Generate new folder for client
        os.mkdir(os.path.join(SERVER_DIR, new_id))
        print('Made dir')
        # Send client new ID
        lib.send_token(client_socket, [new_id, '0'])

    elif curr_client_inst == '-1':
        instance_count_map[curr_client_id] += 1
        new_inst_id = str(instance_count_map[curr_client_id])
        lib.send_token(client_socket, [new_inst_id])


def process_command(cmd_token):
    global server_rcv_buff
    
    if cmd_token == 'identify':
        identify_new_client()
    elif cmd_token == 'mkfile':
        server_rcv_buff, file_name = lib.get_token(client_socket, server_rcv_buff)
        # Creare file
        abs_path = os.path.join(SERVER_DIR, curr_client_id, file_name)
        lib.create_file(abs_path)
        # Receive file data
        lib.rcv_file(client_socket, server_rcv_buff, abs_path)


if __name__ == "__main__":
    # Open server
    while True:
        try:
            server.bind(('', 12345))
            break
        except:
            print("Couldn't open server, trying again")
            time.sleep(3)
    server.listen()

    # Begin receiving clients
    while True:
        global client_socket
        global client_addr

        print("ready to accept next client")
        client_socket, client_address = server.accept()
        print('Connection from: ', client_address)
        while True:
            try:
                time.sleep(1)
            except:
                sys.exit(1)
            print('Server main loop calling gettoken')
            server_rcv_buff, cmd_token = lib.get_token(client_socket, server_rcv_buff)
            print("Received command from client: ", cmd_token)
            if cmd_token == 'fin':
                print("were breaking")
                break
            process_command(cmd_token)
        client_socket.close()
