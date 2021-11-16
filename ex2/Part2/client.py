import watchdog.events
import watchdog.observers
import watchdog
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import time
import socket
import lib
import sys
import os

global my_buff
global my_socket
global client_id
MY_DIR = 'client_dir'


class OnMyWatch:
    # Set the directory on watch
    watchDirectory = MY_DIR

    def __init__(self):
        print("observer started")
        self.observer = Observer()

    def run(self):
        event_handler = Handler()
        self.observer.schedule(event_handler, self.watchDirectory, recursive=True)
        self.observer.start()
        try:
            while True:
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()


file_upload_queue = []


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        open_connection()
        process_upload_queue()
        relative_path = event.src_path[len(MY_DIR) + 1:]
        print('SUBJECT FILE: ' + relative_path)
        # in case client modified something in its files
        if event.event_type == 'modified':
            # in case client modified dir:
            if event.is_directory and len(relative_path) > 0:
                # sending server to handle the modifying
                lib.sendToken(my_socket, 'movdir', [relative_path])
            # Event is modified, you can process it now
            file_name = relative_path.split(os.pathsep)[-1]
            if file_is_not_hidden(file_name):
                print("Watchdog received modified event - % s." % relative_path)
        if event.event_type == 'created':
            if event.is_directory:
                lib.sendToken(my_socket, 'mkdir', [relative_path])
            else:
                file_name = relative_path.split('/')[-1]
                if file_is_not_hidden(file_name):
                    print('Checking if file is open:', event.src_path)
                    if not is_file_closed(event.src_path):
                        print('File is open, adding to queue')
                        file_upload_queue.append((event.src_path, relative_path))
                    else:
                        lib.sendToken(my_socket, 'mkfile', [relative_path])
                        lib.send_data(my_socket, relative_path)
            # Event is created, you can process it now
            print("Watchdog received created event - % s." % relative_path)
        elif event.event_type == 'moved':
            pass
        close_connection()


def file_is_not_hidden(file_name):
    try:
        file_is_hidden = file_name[0] == '.'
        if file_is_hidden:
            return False
        return True
    except:
        return True


'''
@function open connection with the server.
'''


def process_upload_queue():
    while len(file_upload_queue) > 0:
        (abs_path, rel_path) = file_upload_queue[0]
        print('Checking if file is open:', abs_path)
        if is_file_closed(rel_path):
            lib.sendToken(my_socket, 'mkfile', [rel_path])
            lib.send_data(my_socket, abs_path)
            file_upload_queue.pop(0)


def is_file_closed(file_path):
    try:
        f = open(file_path, 'r')
        f.close()
        return False
    except:
        return True


def open_connection():
    global my_socket
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.connect(('127.0.0.1', 12345))

#   
def close_connection():
    global my_socket
    pass


def on_start_up(s, buff):
    '''
    to check: if we have id argument.
    '''
    # open_connection()
    global client_id
    global my_buff
    if len(sys.argv) == 6:
        lib.sendToken(s, 'su', [])
        my_buff, client_id = lib.getToken(s, buff)
    elif len(sys.argv) == 7:
        client_id = sys.argv[6]
        print("this is client id:", client_id)
    pull_request()
    print("end pull")
    lib.sendToken(my_socket, 'fin', [])
    my_socket.close()


def pull_request():
    global my_buff, last_file_created
    lib.sendToken(my_socket, 'pull', [client_id])
    while True:
        my_buff, command_token = lib.getToken(my_socket, my_buff)
        if command_token == 'eoc' or command_token is None:
            break
        my_buff, path_token = lib.getToken(my_socket, my_buff)
        if command_token == 'mkdir':
            create_dir(path_token)
        elif command_token == 'mkfile':
            last_file_created = os.path.join(MY_DIR, path_token)
            lib.creat_file(MY_DIR, path_token)
        elif command_token == 'data':
            lib.write_data(last_file_created, path_token.encode('utf8'))


##need to move into lib library
def create_dir(path_name):
    path = os.path.join(MY_DIR, path_name)
    if not os.path.exists(path):
        os.mkdir(os.path.join(MY_DIR, path_name))


if __name__ == "__main__":
    # my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_buff = []
    open_connection()
    on_start_up(my_socket, my_buff)
    print("arrived here")
    watch = OnMyWatch()
    watch.run()
    my_socket.close()
