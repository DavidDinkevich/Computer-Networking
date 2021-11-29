
import socket
import os


SEP_CHAR = '|'

def send_token(socket, args, encode=True):
    assert len(args) > 0, "send_token: length of args in send_token must be > 0"
    if encode:
        msg = (SEP_CHAR.join(args) + SEP_CHAR).encode()
        print("Sending message: ", msg)
        socket.send(msg)
    # in case its pure data and not files or dirs
    else:
        assert len(args) == 1, "send_token: encode=False but len(args) != 1"
        socket.send(args[0])

def get_token(socket, buff, decode=True, num_bytes_to_read=2048):
    # If buffer is empty, must read from socket
    if len(buff) == 0:
        # need to check buffer limit, if there is still data left to pull.
        data = socket.recv(num_bytes_to_read)
        if decode:
            str_data = data.decode('utf8')
            temp = str_data.split(SEP_CHAR)[:-1]
            buff = buff + temp
        else:
            assert len(data) == num_bytes_to_read, "get_token: decode=False but given num bytes to read not accurate"
            buff.append(data)
    # whether its empty or not, we want to return one command_token from the buff list we have 😀'
    if len(buff) > 0:
        return buff, buff.pop(0)
    return buff, None
