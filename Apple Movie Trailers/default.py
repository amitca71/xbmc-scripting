# main import's
import sys
import os

# Script constants
__scriptname__ = "Apple Movie Trailers"
__author__ = "Apple Movie Trailers (AMT) Team"
__url__ = "http://code.google.com/p/xbmc-scripting/"
__svn_url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/Apple%20Movie%20Trailers"
__credits__ = "XBMC TEAM, freenode/#xbmc-scripting"
__version__ = "pre-0.99.7.1"
__svn_revision__ = 0

# Shared resources
BASE_RESOURCE_PATH = xbmc.translatePath( os.path.join( os.getcwd(), "resources" ) )
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "lib" ) )
# append the proper platforms folder to our path, xbox is the same as win32
env = ( os.environ.get( "OS", "win32" ), "win32", )[ os.environ.get( "OS", "win32" ) == "xbox" ]
sys.path.append( os.path.join( BASE_RESOURCE_PATH, "platform_libraries", env ) )
# create our language object
__language__ = xbmc.Language( os.getcwd() ).getLocalizedString

# Main team credits
__credits_l1__ = __language__( 910 )#"Head Developer & Coder"
__credits_r1__ = "Killarny"
__credits_l2__ = __language__( 911 )#"Coder & Skinning"
__credits_r2__ = "Nuka1195"
__credits_l3__ = __language__( 912 )#"Graphics & Skinning"
__credits_r3__ = "Pike"

# additional credits
__add_credits_l1__ = __language__( 1 )#"Xbox Media Center"
__add_credits_r1__ = "Team XBMC"
__add_credits_l2__ = __language__( 913 )#"Usability"
__add_credits_r2__ = "Spiff & JMarshall"
__add_credits_l3__ = __language__( 914 )#"Language File"
__add_credits_r3__ = __language__( 2 )#"Translators name"


# Start the main gui
if __name__ == "__main__":
    # main window
    import gui
    # clear all modules
    sys.modules.clear()
