import os, os.path, sys
import xbmc, traceback

#<onclick>RunScript(special://home/scripts/YouTrailer/default.py,1)</onclick>

# Script constants
__scriptname__ = "YouTrailer"
__author__ = "stanley87"
__url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/YouTrailer/"

__credits__ = "Chris Tait, Team XBMC, dbr/Ben(TMDB API Interface), TMDB, Nuka1195, Ricardo Garcia Gonzalez, Danny Colligan, Benjamin Johnson"
__version__ = "0.7"

xbmc.log( "[SCRIPT] '%s: version %s By: %s' initialized!" % ( __scriptname__, __version__, __author__, ), xbmc.LOGNOTICE )

BASE_RESOURCE_PATH = os.path.join( os.getcwd(), "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
env = ( os.environ.get( "OS", "win32" ), "win32", )[ os.environ.get( "OS", "win32" ) == "xbox" ]
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "platform_libraries", env ) )

XBMC_SETTINGS = xbmc.Settings( os.getcwd() )


try:
    count = len(sys.argv)
except:
    count = 0

if(count >= 1):
    import main
else:
    XBMC_SETTINGS.openSettings()
