
import socket
import time
import lib
import sys
import random
import string

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
        lib.send_token(client_socket, [new_id, '0'])
        # Add new ID to instance_count_map
        instance_count_map[new_id] = 0
    elif curr_client_inst == '-1':
        instance_count_map[curr_client_id] += 1
        new_inst_id = str(instance_count_map[curr_client_id])
        lib.send_token(client_socket, [new_inst_id])


def process_command(cmd_token):
    if cmd_token == 'identify':
        identify_new_client()


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
            server_rcv_buff, cmd_token = lib.get_token(client_socket, server_rcv_buff)
            print("Received command from client: ", cmd_token)
            if cmd_token == 'fin' or cmd_token is None:
                print("were breaking")
                break
            process_command(cmd_token)
        client_socket.close()
