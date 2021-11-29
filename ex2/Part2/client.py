
import os
import sys
import lib
import socket
import time

client_id = None
client_instance_id = '-1'
client_socket = None
client_rcv_buff = []

ip = sys.argv[1]
port = int(sys.argv[2])
client_dir = sys.argv[3]
wd_time = int(sys.argv[4])



def open_connection():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 12345))


#
def close_connection():
    lib.send_token(client_socket, ['fin'])
    client_socket.close()
    
def login_procedure():
    global client_id
    global client_instance_id
    global client_rcv_buff

    if len(sys.argv) == 6:
        print('Signing up...')
        # Tell server we are completely new and get new ID and instance num
        lib.send_token(client_socket, ['identify', '-1', '-1'])
        client_rcv_buff, client_id = lib.get_token(client_socket, client_rcv_buff)
        client_rcv_buff, client_instance_id = lib.get_token(client_socket, client_rcv_buff)
        print('Received identity:', client_id, client_instance_id)
    elif len(sys.argv) == 7:
        client_id = sys.argv[6]
        print("Init with client id:", client_id)
#        lib.send_token(client_socket, ['identify', client_id, '-1'])
        lib.send_token(client_socket, ['identify', client_id, '0'])
        #client_rcv_buff, client_instance_id = lib.get_token(client_socket, client_rcv_buff)
        print('Received instance num:', client_instance_id)


def handle_server_directive(cmd):
    global client_rcv_buff
    if cmd == 'mkdir':
        # Name of directory/file
        client_rcv_buff, dir_name = lib.get_token(client_socket, client_rcv_buff)
        # Creare dir
        abs_path = os.path.join(client_dir, dir_name)
        # Add directory or file accordingly
        os.mkdir(abs_path)

def on_start_up():
    global client_rcv_buff

    open_connection()
    login_procedure()
    
    '''
    lib.send_token(client_socket, ['pull'])
    client_rcv_buff, cmd_token = lib.get_token(client_socket, client_rcv_buff)
    while cmd_token is not None:
        handle_server_directive(cmd_token)
    '''
    
    lib.send_file(client_socket, 'mkfile', 'client_dir/img.png', 'img.png')
    lib.send_file(client_socket, 'mkfile', 'client_dir/apple.txt', 'apple.txt')
    lib.send_token(client_socket, ['mkdir', 'tree'])
    
    time.sleep(20)
    lib.send_token(client_socket, ['mov', 'img.png', 'tree/img.png'])
    
    
    #lib.send_token(client_socket, ['mkdir', 'pear'])

    #time.sleep(30)
    
    #open_connection()
    #lib.send_token(client_socket, ['identify', client_id, client_instance_id])
    #lib.send_token(client_socket, ['rmdir', 'tree'])
    #lib.send_file(client_socket, 'modfile', 'client_dir/apple.txt', 'apple.txt')
    
    close_connection()




    print("end pull")
#    lib.sendToken(client_socket, 'fin', [])


if __name__ == "__main__":
    on_start_up()
    print("arrived here")
