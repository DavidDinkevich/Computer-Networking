import watchdog.events
import watchdog.observers
import time
import socket
import lib
import sys
import os

global my_buff
global my_socket
global client_id
MY_DIR = 'client_dir'


class Handler(watchdog.events.PatternMatchingEventHandler):
    def __init__(self):
        # Set the patterns for PatternMatchingEventHandler
        watchdog.events.PatternMatchingEventHandler.__init__(self, patterns=['*.csv'],
                                                             ignore_directories=True, case_sensitive=False)

    def on_created(self, event):
        print("Watchdog received created event - % s." % event.src_path)
        # Event is created, you can process it now

    def on_modified(self, event):
        print("Watchdog received modified event - % s." % event.src_path)
        # Event is modified, you can process it now


def on_start_up(s, buff):
    '''
    to check: if we have id argument.
    '''
    global client_id
    global my_buff
    if len(sys.argv) == 5:
        lib.sendToken(s, 'su', [])
        my_buff, client_id = lib.getToken(s, buff)
    elif len(sys.argv) == 6:
        client_id = sys.argv[5]
    pull_request()


def pull_request():
    lib.sendToken(my_socket, 'pull', [client_id])
    tokens = ['mkdir', 'mkfile']
    while True:
        global my_buff
        my_buff, command_token = lib.getToken(my_socket, my_buff)
        print('Received command token:', command_token)
        if command_token not in tokens:
            break
        print(my_buff)
        my_buff, path_token = lib.getToken(my_socket, my_buff)
        creat_dir(path_token)


def creat_dir(name):
    print("this is the iceberg", os.path.join(MY_DIR, name))
    os.mkdir(os.path.join(MY_DIR, name))


if __name__ == "__main__":
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.connect(('127.0.0.1', 12345))
    my_buff = []
    on_start_up(my_socket, my_buff)
    src_path = r"/home/roei/Documents/Computer Networking/ex2/Part2"
    event_handler = Handler()
    observer = watchdog.observers.Observer()
    observer.schedule(event_handler, path=src_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
