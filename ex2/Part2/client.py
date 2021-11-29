
import os
import sys
import lib
import socket

client_dir = 'client_dir'
client_id = None
client_instance_id = '-1'
client_socket = None
client_rcv_buff = []

def open_connection():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('127.0.0.1', 12345))


#
def close_connection():
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
        lib.send_token(client_socket, ['identify', client_id, '-1'])
        client_rcv_buff, client_instance_id = lib.get_token(client_socket, client_rcv_buff)
        print('Received instance num:', client_instance_id)


def on_start_up():
    open_connection()
    login_procedure()
    
    #lib.send_file(client_socket, 'client_dir/img.png', 'img.png')
    lib.send_file(client_socket, 'client_dir/apple.txt', 'apple.txt')
    close_connection()




    print("end pull")
#    lib.sendToken(client_socket, 'fin', [])


if __name__ == "__main__":
    on_start_up()
    print("arrived here")
