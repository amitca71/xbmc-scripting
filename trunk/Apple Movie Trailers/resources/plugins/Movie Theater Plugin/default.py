"""
    Movie Theater: Plugin for viewing random trailers from Apple.com before viewing the main movie
"""
# main imports
import os
import sys
import xbmc

# plugin constants
__plugin__ = "Movie Theater Plugin"
__script__ = "Apple Movie Trailers"
__author__ = "Nuka1195"
__url__ = "http://code.google.com/p/xbmc-scripting/"
__svn_url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/Apple%20Movie%20Trailers"
__credits__ = "XBMC TEAM, freenode/#xbmc-scripting"
__version__ = "1.1"

# base paths
BASE_PATH = os.getcwd().replace( ";", "" )
BASE_DATABASE_PATH = xbmc.translatePath( os.path.join( "P:\\script_data", __script__ ) )


if ( __name__ == "__main__" ):
    if ( "isFolder=0" in sys.argv[ 2 ] ):
        from TheaterAPI import xbmcplugin_player as plugin
    else:
        from TheaterAPI import xbmcplugin_list as plugin
    plugin.Main()
