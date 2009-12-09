# official python modules
import sys
# script modules
import base, dialog

# script variables
common = sys.modules['common']

class BaseScriptWindow:
    def __init__( self, xmlFile = '', resourcePath = '', defaultName = 'Default', forceFallback = False ):
        if not len( xmlFile ):
            xmlFile = 'script-%s-window.xml' % common.scriptname.replace( ' ', '_' )
        if not len( resourcePath ):
            resourcePath = common.resource_path
        if not hasattr( self, 'controls_map' ):
            self.controls_map = {
                # id: {
                #   'onClick': callback,
                #   'onFocus': callback,
                #   'label': str(),
                # },
            }
        self.window = base.__internal_base_classWindow__( xmlFile, resourcePath, defaultName, forceFallback, parentClass = self )

    def close( self ):
        self.window.close()

    def display( self ):
        self.window.doModal()

class BaseScriptDialog:
    def __init__( self, xmlFile = '', resourcePath = '', defaultName = 'Default', forceFallback = False ):
        if not len( xmlFile ):
            xmlFile = 'script-%s-dialog.xml' % common.scriptname.replace( ' ', '_' )
        if not len( resourcePath ):
            resourcePath = common.resource_path
        if not hasattr( self, 'controls_map' ):
            self.controls_map = {
                # id: {
                #   'onClick': callback,
                #   'onFocus': callback,
                #   'label': str(),
                # },
            }
        self.window = base.__internal_base_classDialog__( xmlFile, resourcePath, defaultName, forceFallback, parentClass = self )

    def close( self ):
        self.window.close()

    def display( self ):
        self.window.doModal()
