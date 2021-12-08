
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
# Maps account id + instance num to unique list of pending updates
changes_map = {}

def generate_id():
    return str(''.join(random.choices(string.ascii_uppercase + string.ascii_lowercase + string.digits, k=10)))



def identify_new_client():
    global server_rcv_buff, curr_client_id, curr_client_inst, instance_account_map
    # Set client id
    server_rcv_buff, curr_client_id = lib.get_token(client_socket, server_rcv_buff)
    # Set client instance num
    server_rcv_buff, curr_client_inst = lib.get_token(client_socket, server_rcv_buff)
    # New ID and new instance
    if curr_client_id == '-1':
        # Generate and send new ID for client
        new_id = generate_id()
        # Add new ID to instance_count_map
        instance_count_map[new_id] = 0
        # Generate new folder for client
        os.mkdir(os.path.join(SERVER_DIR, new_id))
        # Send client new ID
        lib.send_token(client_socket, [new_id, '0'])
        # Update variable
        curr_client_id = new_id
        curr_client_inst = '0'
        # Add new entry to changes map
        changes_map[(curr_client_id, curr_client_inst)] = []
    # Existing ID but new instance
    elif curr_client_inst == '-1':
        # Increase instance count
        instance_count_map[curr_client_id] += 1
        # Get new instance num
        new_inst_id = str(instance_count_map[curr_client_id])
        # Update variable
        curr_client_inst = new_inst_id
        lib.send_token(client_socket, [new_inst_id])
        # Add new entry to changes map
        changes_map[(curr_client_id, curr_client_inst)] = []
        
    print('New guy:', curr_client_id, curr_client_inst)
    
def add_change(change):
    for (acc_id, inst_num) in changes_map:
        if acc_id == curr_client_id and inst_num != curr_client_inst:
            changes_map[(acc_id, inst_num)].append(change)
    print('Updated changes map: ', change, changes_map)

def process_command(cmd_token):
    global server_rcv_buff
    
    print('Server handing: ', cmd_token)
    
    if cmd_token == 'identify':
        identify_new_client()
    elif cmd_token == 'mkfile':
        # Name of file
        server_rcv_buff, file_name = lib.get_token(client_socket, server_rcv_buff)
        # Creare file
        abs_path = os.path.join(SERVER_DIR, curr_client_id, file_name)
        lib.create_file(abs_path)
        # Receive file data
        lib.rcv_file(client_socket, server_rcv_buff, abs_path)
        # Update changes map
        add_change(('mkfile', abs_path, file_name))

    elif cmd_token == 'mkdir' or cmd_token == 'rmdir' or cmd_token == 'rmfile':
        # Name of directory/file
        server_rcv_buff, dir_name = lib.get_token(client_socket, server_rcv_buff)
        # Creare dir
        abs_path = os.path.join(SERVER_DIR, curr_client_id, dir_name)
        # Delete directory or file accordingly
        if cmd_token == 'mkdir':
            if not os.path.exists(abs_path):
                os.mkdir(abs_path)
        elif cmd_token == 'rmdir':
            lib.deep_delete(abs_path)
#            os.rmdir(abs_path)
        elif cmd_token == 'rmfile':
            # check bugged case remove file but its dir:
            if lib.is_dir(abs_path):
                # need to check if there are recursive files inside this dir,if so we need to delete them aswell.
                lib.deep_delete(abs_path)
            else:
                os.remove(abs_path)

        # Update changes map
        add_change((cmd_token, dir_name))

    elif cmd_token == 'modfile':
        server_rcv_buff, file_name = lib.get_token(client_socket, server_rcv_buff)
        # Convert 'modfile' to remove + create
        server_rcv_buff.insert(0, 'rmfile')
        server_rcv_buff.insert(1, file_name)
        server_rcv_buff.insert(2, 'mkfile')
        server_rcv_buff.insert(3, file_name)
    elif cmd_token == 'mov':
        # Get relative paths of both src and dest
        server_rcv_buff, src_path = lib.get_token(client_socket, server_rcv_buff)
        server_rcv_buff, dest_path = lib.get_token(client_socket, server_rcv_buff)
        # Get absolute paths
        abs_src_path = os.path.join(SERVER_DIR, curr_client_id, src_path)
        abs_dest_path = os.path.join(SERVER_DIR, curr_client_id, dest_path)
        # Move the files
        #os.renames(abs_src_path, abs_dest_path)
        lib.move_folder(abs_src_path, abs_dest_path)
        # Update changes map
        add_change(('mov', src_path, dest_path))

    elif cmd_token.startswith('pull'):
        update_client(cmd_token == 'pull_all')
    

def update_client(send_everything=False):
    print('Updating client')
    # Send all dirs and files (in that order)
    if send_everything:
        client_folder = os.path.join(SERVER_DIR, curr_client_id)
        dirs, files = lib.get_dirs_and_files(client_folder)
        lib.send_all_dirs_and_files(client_socket, dirs, files, client_folder)

    # Only send changes
    else:
        print('Map before: ', changes_map)
        for change in changes_map[(curr_client_id, curr_client_inst)]:
            if change[0] == 'mkfile':
                abs_file_path = change[1]
                rel_file_path = abs_file_path[
                    len(os.path.join(SERVER_DIR, curr_client_id)) + len(os.path.sep):]
#                rel_file_path = abs_file_path[len(SERVER_DIR + curr_client_id) + len(os.path.sep):]
                lib.send_file(client_socket, 'mkfile', abs_file_path, rel_file_path)
            else:
                args = [change[0], change[1]] if len(change) == 2 else [change[0], change[1], change[2]]
                print('Sending: ', change[0], change[1])
                lib.send_token(client_socket, args)

    # Clear changes map
    changes_map[(curr_client_id, curr_client_inst)].clear()
    print('Map after: ', changes_map)
    # Send eoc
    lib.send_token(client_socket, ['eoc'])


if __name__ == "__main__":
    server_port = int(sys.argv[1])
    
    # Open server
    while True:
        try:
            server.bind(('', server_port))
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
            if cmd_token not in ['identify', 'fin']:
                pass
            if cmd_token == 'fin':
                print("were breaking")
                break
            if cmd_token is not None:
                process_command(cmd_token)
        client_socket.close()
        