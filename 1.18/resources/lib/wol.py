# Wake-On-LAN
#
# Copyright (C) 2002 by Micro Systems Marc Balmer
# Written by Marc Balmer, marc@msys.ch, http://www.msys.ch/
# This code is free software under the GPL
 
import struct, socket
 
def WakeOnLan(ethernet_address):
    try:
        if ':' in ethernet_address:
            ch = ':'
        elif '-' in ethernet_address:
            ch = '-'
        elif '.' in ethernet_address:
            ch = '.'
        else:
            ch = ''

        if ch:
            # Construct a six-byte hardware address
            addr_byte = ethernet_address.split(ch)
            hw_addr = struct.pack('BBBBBB',
                int(addr_byte[0], 16),
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

# 139 is SMB port
def CheckHost( path, port ):
    # if a smb path we check to see if host is awake
    if not path.startswith( "smb://" ):
        hostname = False
    else:

        # get the host
        hostname = path.split( "/" )[ 2 ]
        # filter username/password
        if ( "@" in hostname ):
            hostname = hostname.split( "@" )[ 1 ]

        # check if computer is on
        try:
            print "CheckHost() socket using hostname=%s" % hostname
            # try and connect to host on supplied port
            s = socket.socket()
            s.settimeout ( 0.25 )
            s.connect ( ( hostname, port ) )
            s.close()
        except:
            hostname = ""

    print "CheckHost() hostname=%s" % hostname
    return hostname

if ( __name__ == "__main__" ):
#    WakeOnLan( "0:2:B3:33:66:9E" )
#    hostname = CheckHost( "smb://PROXY1/capture/",139 )

    WakeOnLan( "00:19:B9:2E:C3:FC" )
    hostname = CheckHost( "smb://shtest:a@G86PV2J/xbmc/",139 )
