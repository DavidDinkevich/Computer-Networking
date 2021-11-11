#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import socket

SEP_CHAR = str(3)

lang = {
    "su":       (0, 1),
    "pull":     (1, 0),
    "mkfile":   (2, 0),
    "movfl":    (2, 0),
    "movdir":   (2, 0),
    "rmf":      (1, 0),
    "rmdir":    (1, 0) # Recursive    
}

def sendToken(socket, cmd, args):
    
    if cmd == "su":
        msg = cmd + SEP_CHAR + args[0]
        socket.send(msg.encode())
    elif cmd == "pull":
        pass