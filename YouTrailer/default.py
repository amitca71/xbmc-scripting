import os, os.path, sys
import xbmc

#<onclick>RunScript(special://home/scripts/YouTrailer/default.py,1)</onclick>

# Script constants
__scriptname__ = "YouTrailer"
__author__ = "stanley87"
__url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/YouTrailer/"

__credits__ = "Team XBMC, dbr/Ben(TMDB API Interface), TMDB"
__version__ = "0.5"

xbmc.log( "[SCRIPT] '%s: version %s' initialized!" % ( __scriptname__, __version__, ), xbmc.LOGNOTICE )

BASE_RESOURCE_PATH = os.path.join( os.getcwd(), "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
env = ( os.environ.get( "OS", "win32" ), "win32", )[ os.environ.get( "OS", "win32" ) == "xbox" ]
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "platform_libraries", env ) )

try:
    count = len(sys.argv)
except:
    count = 0

if(count >= 1):
    #Run from Movies
    import main
else:
    pass
    #Run settings
#    import settings
##    ui = gui.GUI( "script-youtrailer-settings.xml", os.getcwd(), "Default" )
##    ui.doModal()
##    del ui    
sys.modules.clear()
