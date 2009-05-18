"""
    Plugin for viewing Metacritic website content.

    Written by BigBellyBilly
    Contact me at BigBellyBilly at gmail dot com - Bugs reports and suggestions welcome.
"""

# main imports
import sys
import xbmc

# plugin constants
__plugin__ = "Metacritic"
__author__ = "BigBellyBilly"
__url__ = "http://code.google.com/p/xbmc-addons/"
__svn_url__ = "http://xbmc-addons.googlecode.com/svn/trunk/plugins/programs/metacritic"
__version__ = "1.0"
__date__ = '18-05-2009'
__svn_revision__ = "$Revision: 984 $"
__XBMC_Revision__ = "19001"

def _check_compatible():
    try:
        # spam plugin statistics to log
        xbmc.log( "[PLUGIN] '%s: Version - %s svn-r%s' initialized!" % ( __plugin__, __version__, __svn_revision__.replace( "$", "" ).replace( "Revision:", "" ).strip() ), xbmc.LOGNOTICE )
        # get xbmc revision
        xbmc_version = xbmc.getInfoLabel( "System.BuildVersion" )
        xbmc_rev = int( xbmc_version.split( " " )[ 1 ].replace( "r", "" ) )
        # compatible?
        ok = xbmc_rev >= int( __XBMC_Revision__ )
    except:
        # error, so unknown, allow to run
        xbmc_rev = 0
        ok = 2
    # spam revision info
    xbmc.log( "     ** Required XBMC Revision: r%s **" % ( __XBMC_Revision__, ), xbmc.LOGNOTICE )
    xbmc.log( "     ** Found XBMC Revision: r%d [%s] **" % ( xbmc_rev, ( "Not Compatible", "Compatible", "Unknown", )[ ok ], ), xbmc.LOGNOTICE )
    # if not compatible, inform user
    if ( not ok ):
        import xbmcgui
        xbmcgui.Dialog().ok( "%s - %s: %s" % ( __plugin__, xbmc.getLocalizedString( 30700 ), __version__, ), xbmc.getLocalizedString( 30701 ) % ( __plugin__, ), xbmc.getLocalizedString( 30702 ) % ( __XBMC_Revision__, ), xbmc.getLocalizedString( 30703 ) )
    #return result
    return ok

if ( __name__ == "__main__" ):
#	print "sys.argv=", sys.argv
	if not sys.argv[ 2 ]:
		# check for compatibility, only need to check this once, continue if ok
		if _check_compatible():
			from pluginAPI import xbmcplugin_categories as plugin
	elif "show_item" in sys.argv[ 2 ]:
		from pluginAPI import xbmcplugin_show_item as plugin
	else:
		from pluginAPI import xbmcplugin_categories as plugin

	try:
		plugin.Main()
	except Exception, e:
		print str(e)
