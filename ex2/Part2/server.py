import socket
import string
import random

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', 12345))
server.listen(5)


def generate_id():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=128))


if __name__ == "__main__":
    while True:
        client_socket, client_address = server.accept()
        print('Connection from: ', client_address)
        data = client_socket.recv(100)
        print('Received: ', data)
        client_socket.send(data.upper())
        data = client_socket.recv(100)
        client_socket.close()
        print('Client disconnected')
