"""
    Home Theater Plugin for viewing random trailers from Apple.com before viewing the main movie
"""
# main imports
import os
import sys
import xbmc

# plugin constants
__plugin__ = "Home Theater"
__script__ = "Apple Movie Trailers"
__author__ = "Nuka1195"
__url__ = "http://code.google.com/p/xbmc-scripting/"
__svn_url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/Apple%20Movie%20Trailers"
__credits__ = "XBMC TEAM, freenode/#xbmc-scripting"
__version__ = "1.5"


if ( __name__ == "__main__" ):
    if ( "isFolder=0" in sys.argv[ 2 ] ):
        from TheaterAPI import xbmcplugin_player as plugin
    else:
        from TheaterAPI import xbmcplugin_list as plugin
    plugin.Main()
