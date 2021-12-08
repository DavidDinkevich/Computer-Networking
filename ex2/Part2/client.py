
import os
import sys
import lib
import socket
import time

import watchdog.events
import watchdog.observers
import watchdog
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


client_id = None
client_instance_id = '-1'
client_socket = None
client_rcv_buff = []

server_ip = sys.argv[1]
server_port = int(sys.argv[2])
client_dir = sys.argv[3]
wd_time = int(sys.argv[4])


# =======================================
#               Watchdog
# =======================================

# Queue of events to push to server at next contact period
event_push_queue = []
blacklist = []

class OnMyWatch:
    # Set the directory on watch
    watchDirectory = client_dir

    def __init__(self):
        print("observer started")
        self.observer = Observer()

    def run(self):
        global watch_dog_switch, blacklist
        event_handler = Handler()
        self.observer.schedule(event_handler, self.watchDirectory, recursive=True)
        self.observer.start()
        try:
            while True:
                print("opening connection")
                open_connection()  # Open connection to server
                # Identify ourselves to the server
                lib.send_token(client_socket, ['identify', client_id, client_instance_id])
                print("Requesting updates")
                blacklist.extend(request_updates('pull_changes'))
                flush_push_event_queue()
                close_connection()  # Close connection
                print("closing connection")
                time.sleep(wd_time)
        except:
            self.observer.stop()
            print("Observer Stopped")

        self.observer.join()


class Handler(FileSystemEventHandler):
    @staticmethod
    def on_any_event(event):
        global event_push_queue

        file_name = event.src_path.split(os.path.sep)[-1]
        print('Event in general:', event.src_path)
        
        # Get relative path of file/dir
        relative_path = event.src_path[len(client_dir) + 1:]

        #print('Filtered out: (' + file_name + ')')
        # Ignore hidden files
        if relative_path.startswith('.') or relative_path.find(os.path.sep + '.') >= 0:
            return
        

        #print("event had occured", event.event_type)
        #print('SUBJECT FILE: ' + relative_path)
        if event.event_type == 'created':
            print("Watchdog received created event - (% s)." % relative_path)
            
            if os.path.isdir(event.src_path):
                event_push_queue.append(('mkdir', relative_path))
            else:
                event_push_queue.append(('mkfile', event.src_path, relative_path))
            
        elif event.event_type == 'moved':
            print("Watchdog received moved event - (% s)." % relative_path)
            relative_dest_path = event.dest_path[len(client_dir) + len(os.path.sep):]
            #lib.send_token(client_socket, ['mov', relative_path, relative_dest_path])
            
            # Update all old references to the old location to the new one
            new_event_push_queue = []
            for ev in event_push_queue:
                if ev[1].find(relative_path) >= 0:
                    new_event_push_queue.append(ev)
                elif ev[0] == 'mkfile' and ev[1].find(relative_path) >= 0:
                    old_ev = ev
                    ev[1] = os.path.join(client_dir, relative_dest_path)
                    ev[1] = relative_dest_path
                    new_event_push_queue.append(ev)
                    print('Turned ', old_ev, ' into ', ev)
                else:    
                    print('In mov: removing: ', ev, ' bc its outdated')
            event_push_queue = new_event_push_queue
            
            event_push_queue.append(('mov', relative_path, relative_dest_path))

        elif event.event_type == 'deleted':
            print("Watchdog received deleted event - (% s)." % relative_path)
            if event.is_directory:
                event_push_queue.append(('rmdir', relative_path))
                #lib.send_token(client_socket, ['rmdir', relative_path])
            else:
                event_push_queue.append(('rmfile', relative_path))
                #lib.send_token(client_socket, ['rmfile', relative_path])
            
        # For modified events, ignore directories
        elif event.event_type == 'modified' and not event.is_directory:
            print("Watchdog received modified event - (% s)." % relative_path)
            # Convert 'modfile' to remove + create
            mkfile_cmd = ('mkfile', event.src_path, relative_path)
            if mkfile_cmd not in event_push_queue and mkfile_cmd not in blacklist:
                event_push_queue.append(('rmfile', relative_path))
                event_push_queue.append(('mkfile', event.src_path, relative_path))


def flush_push_event_queue():
    #print('Beginning to empty event push queue', event_push_queue)
    for item in event_push_queue:
        if item in blacklist:
            print('Not doing: ', item, ' bc its in the blacklist')
            blacklist.remove(item)
        else:
            print(client_instance_id + ' telling server to ' + str(item))
            if item[0] == 'mkfile':
                lib.send_file(client_socket, 'mkfile', item[1], item[2])
            elif item[0] == 'mov':
                lib.send_token(client_socket, [item[0], item[1], item[2]])
            else:
                lib.send_token(client_socket, [item[0], item[1]])
    event_push_queue.clear()


# ==========  END WATCHDOG  ==========

def open_connection():
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))



#
def close_connection():
    print(client_instance_id + ' Trying to send fin')
    lib.send_token(client_socket, ['fin'])
    client_socket.close()
    
def login_procedure():
    global client_id
    global client_instance_id
    global client_rcv_buff

    if len(sys.argv) == 5:
        print('Signing up...')
        # Tell server we are completely new and get new ID and instance num
        lib.send_token(client_socket, ['identify', '-1', '-1'])
        client_rcv_buff, client_id = lib.get_token(client_socket, client_rcv_buff)
        client_rcv_buff, client_instance_id = lib.get_token(client_socket, client_rcv_buff)
        # get all files and dirs from current file(if there are such files)
        # send all the files to the server.
        dir_arr, file_arr = lib.get_dirs_and_files(client_dir)
        # send all files and dirs (if they exists):
        lib.send_all_dirs_and_files(client_socket, dir_arr, file_arr, client_dir)

        print('Received identity:', client_id, client_instance_id)
    elif len(sys.argv) == 6:
        client_id = sys.argv[5]
        print("Init with client id:", client_id)
        lib.send_token(client_socket, ['identify', client_id, '-1'])
        client_rcv_buff, client_instance_id = lib.get_token(client_socket, client_rcv_buff)
        print('Received instance num:', client_instance_id)
        # Download entire directory from the cloud
        request_updates('pull_all')

def request_updates(pull_type):
    global client_rcv_buff
    
    server_directives = []
    
    lib.send_token(client_socket, [pull_type])
    while True:
        client_rcv_buff, cmd_token = lib.get_token(client_socket, client_rcv_buff)
        if cmd_token == 'eoc':
            break
        server_directive = handle_server_directive(cmd_token)
        server_directives.extend(server_directive)
    print('Read eoc and exiting. ServerDirectives: ')

    return server_directives


def handle_server_directive(cmd_token):
    global client_rcv_buff
    print('cmd is ' + cmd_token)

    if cmd_token == 'mkfile':
        # Name of directory/file
        client_rcv_buff, file_name = lib.get_token(client_socket, client_rcv_buff)
        # Creare file
        abs_path = os.path.join(client_dir, file_name)
        lib.create_file(abs_path)
        # Receive file data
        lib.rcv_file(client_socket, client_rcv_buff, abs_path)
        # Return partial blacklist
        return [(cmd_token, abs_path, file_name)]

    elif cmd_token == 'mkdir' or cmd_token == 'rmdir' or cmd_token == 'rmfile':
        # Name of directory/file
        client_rcv_buff, dir_name = lib.get_token(client_socket, client_rcv_buff)
        # Creare dir
        abs_path = os.path.join(client_dir, dir_name)
        # Delete directory or file accordingly
        if cmd_token == 'mkdir':
            if not os.path.exists(abs_path):
                os.mkdir(abs_path)
                print('made dir: ', abs_path)
            else:
                print("Didn't make " + abs_path + " bc already exists")
        elif cmd_token == 'rmdir':
            lib.deep_delete(abs_path)
#            os.rmdir(abs_path)
        elif cmd_token == 'rmfile':
            os.remove(abs_path)
        # Return partial blacklist
        return [(cmd_token, dir_name)]

    elif cmd_token == 'modfile':
        client_rcv_buff, file_name = lib.get_token(client_socket, client_rcv_buff)
        # Convert 'modfile' to remove + create
        client_rcv_buff.insert(0, 'rmfile')
        client_rcv_buff.insert(1, file_name)
        client_rcv_buff.insert(2, 'mkfile')
        client_rcv_buff.insert(3, file_name)
    elif cmd_token == 'mov':
        # Get relative paths of both src and dest
        client_rcv_buff, src_path = lib.get_token(client_socket, client_rcv_buff)
        client_rcv_buff, dest_path = lib.get_token(client_socket, client_rcv_buff)
        # Get absolute paths
        abs_src_path = os.path.join(client_dir, src_path)
        abs_dest_path = os.path.join(client_dir, dest_path)
        abs_abs_path = lib.get_abs_path(abs_dest_path)
        # Check if move file is needed
        if not os.path.exists(abs_abs_path):
            # Move the files
            # os.renames(abs_src_path, abs_dest_path)
            lib.move_folder(abs_src_path, abs_dest_path)
        # Return blacklist
        return [(cmd_token, src_path, dest_path), ('mkfile', dest_path), ('rmfile', src_path)]


def on_start_up():
    open_connection()
    login_procedure()
    close_connection()


    print("end pull")
#    lib.sendToken(client_socket, 'fin', [])


if __name__ == "__main__":
    on_start_up()
    print('Begin watchdog...')
    watch = OnMyWatch()
    watch.run()

    print("arrived here")
