# Wake-On-LAN
#
# Copyright (C) 2002 by Micro Systems Marc Balmer
# Written by Marc Balmer, marc@msys.ch, http://www.msys.ch/
# This code is free software under the GPL
#
# Modified 2008 for use in XBMC Plugins - ozNick


import struct
import socket


def WakeOnLan(ethernet_address):
    try:
        # Construct a six-byte hardware address
        addr_byte = ethernet_address.split(':')
        hw_addr = struct.pack('BBBBBB', int(addr_byte[0], 16),
            int(addr_byte[1], 16),
            int(addr_byte[2], 16),
            int(addr_byte[3], 16),
            int(addr_byte[4], 16),
            int(addr_byte[5], 16))

        # Build the Wake-On-LAN "Magic Packet"...
        msg = '\xff' * 6 + hw_addr * 16

        # ...and send it to the broadcast address using UDP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(msg, ('<broadcast>', 9))
        s.close()
    except:
        import traceback
        traceback.print_exc()
        return

def CheckHost( path ):
    # if a smb path we check to see if host is awake
    if ( not path.startswith( "smb://" ) ): return True
    # get the host
    hostname = path.split( "/" )[ 2 ]
    # filter username/password
    if ( "@" in hostname ):
        hostname = hostname.split( "@" )[ 1 ]
    # check if computer is on
    try:
        ip = socket.gethostbyname( hostname )
        return ip
    except:
        return ""

if ( __name__ == "__main__" ):
    WakeOnLan( "##:##:##:##:##:##" )
    print "sent"
    ip = CheckHost( "smb://SERVER/Movies/" )
    print "IP:", ip


