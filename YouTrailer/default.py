import os, os.path, sys
import xbmc

#<onclick>RunScript(special://home/scripts/YouTrailer/default.py,"$INFO[listitem.filename]","$INFO[listitem.path]")</onclick>

# Script constants
__scriptname__ = "YouTrailer"
__author__ = "stanley87"
__url__ = "http://code.google.com/p/xbmc-addons/"

__credits__ = "Team XBMC"
__version__ = "0.0.1"

xbmc.log( "[SCRIPT] '%s: version %s' initialized!" % ( __scriptname__, __version__, ), xbmc.LOGNOTICE )

BASE_RESOURCE_PATH = os.path.join( os.getcwd(), "resources" )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
env = ( os.environ.get( "OS", "win32" ), "win32", )[ os.environ.get( "OS", "win32" ) == "xbox" ]
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "platform_libraries", env ) )

try:
    count = len(sys.argv)
except:
    count = 0

if(count > 2):
    #Run from Movies
    import main
else:
    pass
    #Run from Scripts
#    import settings
##    ui = gui.GUI( "script-youtrailer-settings.xml", os.getcwd(), "Default" )
##    ui.doModal()
##    del ui    
sys.modules.clear()
