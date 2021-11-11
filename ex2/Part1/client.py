import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('192.168.169.128', 12345))
s.send(b'Roei Gehassi')
data = s.recv(100)
print("Server sent: ", data)
data = s.recv(100)
s.close()
