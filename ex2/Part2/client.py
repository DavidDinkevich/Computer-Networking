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
watch_dog_switch = True


# =======================================
#       General Utility Functions
# =======================================


def file_is_not_hidden(file_name):
    try:
        file_is_hidden = file_name[0] == '.'
        if file_is_hidden:
            return False
        return True
    except:
        return True


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
                open_connection()  # Open connection to server
                if len(wd_queue) > 0:
                    proccess_wd_dequeue(MY_DIR)
                watch_dog_switch = False
                pull_request()  # Send pull request
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
        if watch_dog_switch == True and file_is_not_hidden(file_name):
            open_connection()
            process_dequeue()
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
                pass
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
            proccess_wd_dequeue(event.src_path)
            close_connection()


def proccess_wd_dequeue(abs_path):
    for item in wd_queue:
        cmd = item[0]
        relative_path = item[1]
        if cmd == 'rmdir':
            lib.sendToken(my_socket, cmd, [relative_path])
        elif cmd == 'mkfile':
            handle_create_file_event(abs_path, relative_path)
        elif cmd == 'mkdir':
            handle_create_dir_event(relative_path)
        elif cmd == 'rmfile':
            lib.sendToken(my_socket, cmd, [relative_path])
        elif cmd == 'modified':
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
    file_name = rel_path.split('/')[-1]
    # If file is not hidden
    if file_is_not_hidden(file_name):
        print('Checking if file is open:', abs_path)
        # If file is not closed
        if not is_file_closed(abs_path):
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
        if is_file_closed(relative_path):
            lib.send_data(my_socket, abs_path, relative_path)
            file_upload_queue.pop(0)


# =======================================
#    Non-Watchdog Server Interactions
# =======================================


def on_start_up(s, buff):
    global watch_dog_switch
    watch_dog_switch = False
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


def send_list_request():
    global my_buff, last_file_created

    print('Sending list request:')
    # Request that server provide list of dirs and files
    lib.sendToken(my_socket, 'list', [client_id])
    server_dirs = []
    server_files = []
    while True:
        my_buff, command_token = lib.getToken(my_socket, my_buff)
        if command_token == 'eoc' or command_token is None:
            break
        my_buff, path_token = lib.getToken(my_socket, my_buff)
        if command_token == 'mkdir':
            server_dirs.append(path_token)
        elif command_token == 'mkfile':
            server_files.append(path_token)

    # We now have a full list of server's dirs and files.
    # Let's compare.
    my_dirs, my_files = lib.get_dirs_and_files(MY_DIR)
    to_remove, to_add = lib.diff(my_dirs, my_files, server_dirs, server_files)

    # Return dirs/files that we need to add
    return to_remove, to_add


def pull_request():
    to_remove, to_add = send_list_request()
    print('Must delete: ', to_remove)
    print('Must add: ', to_add)
    lib.remove_all_files_and_dirs(to_remove, MY_DIR)

    # If we have
    if len(to_add) == 0:
        return

    global my_buff, last_file_created

    # Now let's request a pull, and ignore everything that we already have

    lib.sendToken(my_socket, 'pull', [client_id])
    while True:
        my_buff, command_token = lib.getToken(my_socket, my_buff)
        if command_token == 'eoc' or command_token is None:
            break
        my_buff, path_token = lib.getToken(my_socket, my_buff)

        if command_token == 'mkdir' and path_token in to_add:
            lib.create_dir(os.path.join(MY_DIR, path_token))
        elif command_token == 'mkfile' and path_token in to_add:
            abs_path = os.path.join(MY_DIR, path_token)
            lib.create_file(MY_DIR, path_token)
            lib.rcv_file(my_socket, my_buff, abs_path)


if __name__ == "__main__":
    # my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_buff = []
    open_connection()
    on_start_up(my_socket, my_buff)
    print("arrived here")
    watch = OnMyWatch()
    watch.run()
