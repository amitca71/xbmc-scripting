"""
    Plugin for streaming content from Apple.com
"""

# main imports
import sys
import os
import xbmc

# plugin constants
__plugin__ = "Apple Movie Trailers"
__script__ = "Apple Movie Trailers"
__author__ = "Nuka1195"
__url__ = "http://code.google.com/p/xbmc-scripting/"
__svn_url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/Apple%20Movie%20Trailers"
__credits__ = "XBMC TEAM, freenode/#xbmc-scripting"
__version__ = "1.4"


if ( __name__ == "__main__" ):
    if ( not sys.argv[ 2 ] ):
        from amtAPI import xbmcplugin_categories as plugin
    elif ( "idMovie=" in sys.argv[ 2 ] ):
        from amtAPI import xbmcplugin_player as plugin
    else:
        from amtAPI import xbmcplugin_videos as plugin
    plugin.Main()
