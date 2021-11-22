import time

import watchdog.events
import watchdog.observers
import watchdog
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import socket
import lib
import sys
import os

global first_time
global my_buff
global my_socket
MY_DIR = 'client_dir'
watch_dog_switch = True

client_id = None
client_instance_id = '-1'
# arguments define
ip = sys.argv[1]
port = int(sys.argv[2])
client_dir = sys.argv[3]
wd_time = int(sys.argv[4])


# =======================================
#       General Utility Functions
# =======================================

def open_connection():
    global my_socket
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.connect((ip, port))


#
def close_connection():
    global my_socket
    my_socket.close()


# =======================================
#               Watchdog
# =======================================

class OnMyWatch:
    # Set the directory on watch
    watchDirectory = MY_DIR

    def __init__(self):
        print("observer started")
        self.observer = Observer()

    def run(self):
        global watch_dog_switch
        event_handler = Handler()
        self.observer.schedule(event_handler, self.watchDirectory, recursive=True)
        self.observer.start()
        try:
            while True:
                print("open connection")
                open_connection()  # Open connection to server
                print("queue to dequeue", wd_queue)
                # why here?
                watch_dog_switch = False
                process_dequeue()
                if len(wd_queue) > 0:
                    proccess_wd_dequeue(MY_DIR)
                pull_request()  # Send pull request
                print("proccessing dequeue")
                process_dequeue()
                if len(wd_queue) > 0:
                    proccess_wd_dequeue(MY_DIR)
                print("queue before closing")
                print("were closing")
                close_connection()  # Close connection
                watch_dog_switch = True
                time.sleep(5)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()


# wd_queue --> logic is- when event had detected, it wont stop main thread
# but it will add the event to a queue, when back on while running (in run func)
# we will dequeue by order.
wd_queue = []
file_upload_queue = []


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        # in case we opened a new thread, we want to check if there is already
        # connection between the server and client.
        file_name = event.src_path.split(os.path.sep)[-1]
        if watch_dog_switch:
            print('open connection')
            open_connection()
        if lib.file_is_not_hidden(file_name):
            print("event had occured", event.event_type)

            # Get relative path of file/dir
            relative_path = event.src_path[len(MY_DIR) + 1:]
            print('SUBJECT FILE: ' + relative_path)
            # in case client modified something in its files
            #        if event.event_type == 'modified':
            #            # in case client modified dir:
            #            if event.is_directory and len(relative_path) > 0:
            #                # sending server to handle the modifying
            #                lib.sendToken(my_socket, 'movdir', [relative_path])
            #            # Event is modified, you can process it now
            #            file_name = relative_path.split(os.pathsep)[-1]
            #            if file_is_not_hidden(file_name):
            #                print("Watchdog received modified event - % s." % relative_path)
            if event.event_type == 'created':
                if event.is_directory:
                    wd_queue.append(('mkdir', relative_path))
                    # handle_create_dir_event(relative_path)
                else:
                    # handle_create_file_event(event.src_path, relative_path)
                    wd_queue.append(('mkfile', relative_path))
                    # Event is created, you can process it now
                print("Watchdog received created event - % s." % relative_path)
            elif event.event_type == 'moved':
                wd_queue.append(('movdir',))
            elif event.event_type == 'deleted':
                if event.is_directory:
                    # lib.sendToken(my_socket, 'rmdir', [relative_path])
                    wd_queue.append(('rmdir', relative_path))
                else:
                    # if event's directory is actually file's directory.
                    # lib.sendToken(my_socket, 'rmfile', [relative_path])
                    wd_queue.append(('rmfile', relative_path))
            elif event.event_type == 'modified':
                pass
                # if event.is_directory:
                #     wd_queue.append(('movdir', relative_path))
                # else:
                #     wd_queue.append(('movfile', relative_path))
            if watch_dog_switch:
                print("were closing")
                proccess_wd_dequeue(MY_DIR)
                process_dequeue()
                close_connection()


def proccess_wd_dequeue(abs_path):
    for item in wd_queue:
        print("deque item:", item)
        cmd = item[0]
        relative_path = item[1]
        lib.sendToken(my_socket, 'identify', [client_id, client_instance_id])

        if cmd == 'mkfile':
            abs_path = os.path.join(abs_path, relative_path)
            handle_create_file_event(abs_path, relative_path)
        elif cmd == 'mkdir':
            handle_create_dir_event(relative_path)
        elif cmd == 'rmfile' or cmd == 'rmdir' or cmd == 'modified':
            lib.sendToken(my_socket, cmd, [relative_path])
        elif cmd == 'movdir':
            lib.sendToken(my_socket, cmd, [relative_path])
        # means its movfile
        elif cmd == 'movfile':
            lib.sendToken(my_socket, cmd, [relative_path])
        print("queue is:", wd_queue)
        wd_queue.remove(item)


# Update server about watchdog-detected directory creation
def handle_create_dir_event(relative_path):
    # Send mkdir token with directory name
    lib.sendToken(my_socket, 'mkdir', [relative_path])


def handle_create_file_event(abs_path, rel_path):
    # Get file name (to check if file is hidden)
    file_name = rel_path.split(os.path.sep)[-1]
    # If file is not hidden
    if lib.file_is_not_hidden(file_name):
        print('Checking if file is open:', abs_path)
        # If file is not closed
        if not lib.is_file_closed(abs_path):
            print('File is open, adding to queue')
            # Add file to upload queue--we'll upload it later
            file_upload_queue.append((abs_path, rel_path))
        else:  # If file is closed
            # Send file to server
            lib.send_data(my_socket, abs_path, rel_path)


'''
@function open connection with the server.
'''


def process_dequeue():
    while len(file_upload_queue) > 0:
        (abs_path, relative_path) = file_upload_queue[0]
        print('Checking if file is open:', abs_path)
        if lib.is_file_closed(relative_path):
            lib.send_data(my_socket, abs_path, relative_path)
            file_upload_queue.pop(0)


# =======================================
#    Non-Watchdog Server Interactions
# =======================================


def on_start_up(s, buff):
    global watch_dog_switch, client_instance_id
    watch_dog_switch = False
    '''
    to check: if we have id argument.
    '''
    # open_connection()
    global client_id, my_buff
    if len(sys.argv) == 6:
        lib.sendToken(s, 'su', [])
        my_buff, client_id = lib.getToken(s, buff)
        client_instance_id = '0'

    elif len(sys.argv) == 7:
        client_id = sys.argv[6]
        lib.sendToken(my_socket, 'identify', [client_id, '-1'])
        my_buff, client_instance_id = lib.getToken(my_socket, my_buff)
        lib.sendToken(my_socket, 'de', [])
        print("this is client id:", client_id)
    pull_request()
    print("end pull")
    lib.sendToken(my_socket, 'fin', [])
    my_socket.close()


def pull_request():
    global my_buff, last_file_created
    lib.sendToken(my_socket, 'identify', [client_id, client_instance_id])
    lib.sendToken(my_socket, 'pull', [])
    process_server_instructions()


def process_server_instructions():
    global my_buff
    while True:
        my_buff, command_token = lib.getToken(my_socket, my_buff)
        if command_token == 'eoc' or command_token is None:
            break
        my_buff, path_token = lib.getToken(my_socket, my_buff)
        if command_token == 'mkdir':
            lib.create_dir(os.path.join(MY_DIR, path_token))
        elif command_token == 'mkfile':
            abs_path = os.path.join(MY_DIR, path_token)
            lib.create_file(MY_DIR, path_token)
            lib.rcv_file(my_socket, my_buff, abs_path)
        elif command_token == 'rmdir' or command_token == 'rmfile':
            abs_path = os.path.join(MY_DIR, path_token)
            lib.remove_all_files_and_dirs([path_token], abs_path)
        elif command_token == 'movdir' or command_token == 'movfile':
            pass


if __name__ == "__main__":
    global first_time
    my_buff = []
    open_connection()
    on_start_up(my_socket, my_buff)
    print("arrived here")
    watch = OnMyWatch()
    watch.run()
