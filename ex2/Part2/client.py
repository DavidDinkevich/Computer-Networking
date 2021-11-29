
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

def on_start_up(s, buff):
    global client_id
    global client_instance_id
    global client_rcv_buff

    open_connection()
    if len(sys.argv) == 6:
        print('Signing up...')
        lib.send_token(client_socket, ['identify', '-1', '-1'])
        client_rcv_buff, client_id = lib.get_token(client_socket, client_rcv_buff)
        client_rcv_buff, client_instance_id = lib.get_token(client_socket, client_rcv_buff)
        print('Received identity:', client_id, client_instance_id)
#        lib.sendToken(s, 'su', [])
#        my_buff, client_id = lib.get_token(s, buff)
    elif len(sys.argv) == 7:
        client_id = sys.argv[6]
        print("Init with client id:", client_id)
#    pull_request()
    print("end pull")
#    lib.sendToken(client_socket, 'fin', [])
    close_connection()


if __name__ == "__main__":
    on_start_up(client_socket, client_rcv_buff)
    print("arrived here")
