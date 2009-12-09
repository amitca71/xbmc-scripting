# official python modules
import sys
# official xbmc modules
import xbmc, xbmcgui
# script modules
import base, dialog

# script variables
common = sys.modules['common']

def _keyboard( default = '', heading = '', hidden = False ):
    '''Shows a keyboard and returns a value'''
    keyboard = xbmc.Keyboard( default, heading, hidden )
    keyboard.doModal()
    if ( keyboard.isConfirmed() ):
        return keyboard.getText()
    return default
    
def getText( heading = '', default = '', masked = False ):
    '''Returns a text string from the user. Set masked for password entries.'''
    return _keyboard( default, heading, hidden = masked )

def _numeric( default = '', heading = '', type = 3 ):
    '''
    Shows a numeric dialog and returns a value
        - 0 : ShowAndGetNumber        (default format: #)
        - 1 : ShowAndGetDate          (default format: DD/MM/YYYY)
        - 2 : ShowAndGetTime          (default format: HH:MM)
        - 3 : ShowAndGetIPAddress     (default format: #.#.#.#)
    '''
    dialog = xbmcgui.Dialog()
    value = dialog.numeric( type, heading, default )
    return value

def getDate( heading = '', default = '' ):
    '''Displays a dialog to obtain a date from the user.'''
    if not len( heading ): heading = 'Enter date [DD/MM/YYYY]:'
    return _numeric( default, heading, type = 1 )

def getIPAddress( heading = '', default = '' ):
    '''Displays a dialog to obtain an ip address from the user.'''
    if not len( heading ): heading = 'Enter an IP address:'
    return _numeric( default, heading, type = 3 )

def getNumber( heading = '', default = '' ):
    '''Displays a dialog to obtain a number from the user.'''
    if not len( heading ): heading = 'Enter a number:'
    return _numeric( default, heading, type = 0 )

def getTime( heading = '', default = '' ):
    '''Displays a dialog to obtain a time from the user.'''
    if not len( heading ): heading = 'Enter time [HH:MM]:'
    return _numeric( default, heading, type = 2 )

def browse( default = '', heading = '', dlg_type = 1, shares = 'files', mask = '', use_thumbs = False, treat_as_folder = False ):
    '''
    Shows a browse dialog and returns a value
        - 0 : ShowAndGetDirectory
        - 1 : ShowAndGetFile
        - 2 : ShowAndGetImage
        - 3 : ShowAndGetWriteableDirectory
    '''
    dialog = xbmcgui.Dialog()
    value = dialog.browse( dlg_type, heading, shares, mask, use_thumbs, treat_as_folder, default )
    return value

class popupmenu:
    '''
        Shows a popup dialog with the specified list items automatically added.
    '''
    def __init__( self, menuItems, xmlFile = '', resourcePath = '', defaultName = 'Default', forceFallback = False ):
        if not len( xmlFile ):
            xmlFile = 'script-%s-popupmenu.xml' % common.scriptname.replace( ' ', '_' )
        if not len( resourcePath ):
            resourcePath = common.resource_path
        self.controls_map = menuItems
        self.window = base.__internal_base_classPopupMenu__( xmlFile, resourcePath, defaultName, forceFallback, parentClass = self )
        self.window.doModal()
