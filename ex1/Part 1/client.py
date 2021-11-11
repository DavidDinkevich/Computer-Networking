#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Oct 21 17:05:43 2021

@author: david
"""

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(b'David Dinkevich (ID: 584698174), Roei Gehasi (ID: 208853754)',
         ('127.0.0.1', 12345))
    
data, addr = s.recvfrom(1024)
print(str(data), addr)

s.close()

