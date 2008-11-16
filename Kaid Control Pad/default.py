"""
    This script allows you to control kai daemon on your linksys wrt54g router.
    
    Nuka1195
"""

import sys
import os
import xbmc
import xbmcgui
import threading

resource_path = os.path.join( os.getcwd(), "resources" )
sys.path.append( os.path.join( resource_path, "lib" ) )

import wrt54g
import utilities
import language
_ = language.Language().localized

__scriptname__ = "Kaid Control Pad"
__author__ = "Nuka1195"
__url__ = "http://code.google.com/p/xbmc-scripting/"
__svn_url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/Kaid%20Control%20Pad"
__credits__ = "XBMC TEAM, freenode/#xbmc-scripting"
__version__ = "pre-2.1"


class GUI( xbmcgui.WindowXMLDialog ):
    def __init__( self, *args, **kwargs ):
        self.timer_msg = None

    def onInit( self ):
        #Start( function=self.setup_all ).start()
        self.setup_all()
        
    def setup_all( self ):
        self.set_labels()
        self.setup_variables()
        self.wrt54g = wrt54g.Commands()
        self.check_status()
        
    def set_labels( self ):
        xbmcgui.lock()
        self.getControl( 2 ).setLabel( __scriptname__ )
        self.getControl( 10 ).setLabel( _( 11 ) )
        self.getControl( 20 ).setLabel( _( 12 ) )
        self.getControl( 30 ).setLabel( _( 13 ) )
        self.getControl( 40 ).setLabel( _( 14 ) )
        self.getControl( 50 ).setLabel( _( 15 ) )
        self.getControl( 101 ).setLabel( _( 100 ) )
        self.getControl( 111 ).setLabel( _( 110 ) )
        self.getControl( 121 ).setLabel( _( 120 ) )
        xbmcgui.unlock()
        
    def setup_variables( self ):
        self.controller_action = utilities.setControllerAction()
        self.KAID_VERSION = ""
        self.command_running = False
        
    def set_status_labels( self ):
        self.getControl( 100 ).setLabel( [ "", _( 101 + self.wrt54g.STATUS_KAID_RUNNING ) ][ self.wrt54g.STATUS_KAID_RUNNING != -1 ] )
        self.getControl( 100 ).setEnabled( self.wrt54g.STATUS_KAID_RUNNING == 1 )
        self.getControl( 110 ).setLabel( self.KAID_VERSION )
        self.getControl( 110 ).setEnabled( self.wrt54g.STATUS_ROUTER == 1 )
        self.getControl( 120 ).setLabel( [ "", _( 121 + self.wrt54g.STATUS_XBOX ) ][ self.wrt54g.STATUS_XBOX != -1 ] )
        self.getControl( 120 ).setEnabled( self.wrt54g.STATUS_XBOX == 1 )
        
    def set_status_buttons( self ):
        self.getControl( 10 ).setLabel( _( 10 + ( self.wrt54g.STATUS_KAID_RUNNING != 1 ) ) )
        self.getControl( 10 ).setEnabled( self.wrt54g.STATUS_ROUTER == True )
        self.getControl( 20 ).setEnabled( self.wrt54g.STATUS_KAID_RUNNING == True )
        self.getControl( 30 ).setEnabled( self.wrt54g.STATUS_XBOX == True and self.wrt54g.STATUS_ROUTER != 2 )
        self.getControl( 40 ).setEnabled( self.wrt54g.STATUS_ROUTER != 2 )
        if ( self.wrt54g.STATUS_ROUTER == True ):
            self.setFocus( self.getControl( 10 ) )
        elif ( self.wrt54g.STATUS_XBOX == True and self.wrt54g.STATUS_ROUTER != 2 ):
            self.setFocus( self.getControl( 30 ) )
        else:
            self.setFocus( self.getControl( 50 ) )

    def set_message( self, msg_id=750, status=0 ):
        xbmcgui.lock()
        self.clear_message_timer()
        self.hide_status_bar()
        key = ( 500, 510, 520, )[ status ]
        self.getControl( key ).reset()
        self.getControl( key ).addLabel( _( msg_id ) )
        self.getControl( key ).setVisible( True )
        if ( status == 2 ):
            self.timer_msg = threading.Timer( 10, self.set_message, () )
            self.timer_msg.start()
        xbmcgui.unlock()

    def hide_status_bar( self ):
        self.getControl( 500 ).setVisible( False )
        self.getControl( 510 ).setVisible( False )
        self.getControl( 520 ).setVisible( False )
        self.getControl( 900 ).setVisible( False )

    def clear_message_timer( self ):
        if ( self.timer_msg is not None ): self.timer_msg.cancel()

    def change_settings( self ):
        import settings
        settings = settings.GUI( "script-KCP-settings.xml", os.getcwd(), "Default", language=_ )
        settings.doModal()
        if ( settings.changed ):
            self.wrt54g._get_settings()
            if ( settings.restart ):
                self.check_status()
        del settings
            
    def check_status( self ):
        self.command_running = True
        self._status_xbox( False )
        self._status_router( False )
        self._status_kaid_running( False )
        self._set_status()
        self.command_running = False
        
    def _set_status( self ):
        self.set_status_labels()
        self.set_status_buttons()

    def _status_xbox( self, update=True ):
        self.set_message( 500, 1 )
        ok = self.wrt54g._status_xbox()
        if ( ok == 2 ): self.set_message( 530, 2 )
        else: self.set_message()
        if ( update ): self._set_status()
            
    def _status_router( self, update=True ):
        self.set_message( 501, 1 )
        ok, version = self.wrt54g._status_router_kaid()
        if ( ok and version ): tmp_version = "Kaid (v.%s)" % ( version[ 0 ], )
        else: tmp_version = _( 112 )
        self.KAID_VERSION = [ _( 111 ), tmp_version, _( 113 ) ][ self.wrt54g.STATUS_ROUTER ]
        if ( ok == 2 ): self.set_message( 531, 2 )
        elif ( self.wrt54g.STATUS_ROUTER ):
            self.set_message( 502, 1 )
            ok = self.wrt54g._status_router_kaid_conf()
            if ( ok == 2 ): self.set_message( 531, 2)
            else: self.set_message()
        if ( update ): self._set_status()

    def _status_kaid_running( self, update=True ):
        if ( self.wrt54g.STATUS_ROUTER != 2 ):
            self.set_message( 503, 1 )
            ok = self.wrt54g._status_kaid_running()
            if ( ok == 2 ): self.set_message( 531, 2 )
            else: self.set_message()
        if ( update ): self._set_status()
        
    def _kaid_restart( self ):
        self.set_message( 600 + ( not self.wrt54g.STATUS_KAID_RUNNING ), 1 )
        ok = self.wrt54g._kaid_restart()
        if ( not ok ): self.set_message( 630, 2 )
        else: 
            self.show_progressbar( 5 )
            self._status_kaid_running()
            
    def _kaid_kill( self ):
        self.set_message( 602, 1 )
        ok = self.wrt54g._kaid_kill()
        if ( not ok ): self.set_message( 630, 2 )
        else: 
            self.set_message()
        self._status_kaid_running()
        
    def _kaid_upload( self ):
        self.set_message( 603, 1 )
        ok = self.wrt54g._kaid_upload()
        if ( not ok ): self.set_message( 633, 2 )
        else: 
            self.set_message( 606, 1 )
            ok = self.wrt54g._finalize_upload()
            if ( not ok ): self.set_message( 636, 2 )
            else: 
                self._status_router( False )
                #self.set_message( 607, 1 )
                #ok = self.wrt54g._config_file_patch()
                #if ( not ok ): self.set_message( 637, 2 )
                #else:
                self._kaid_restart()

    def _router_reboot( self ):
        self.set_message( 604, 1 )
        ok = self.wrt54g._router_reboot()
        if ( not ok ): self.set_message( 630, 2 )
        else: 
            self.show_progressbar( 20 )
            self.set_message()
        self._set_status()

    def show_progressbar( self, seconds ):
        sleep_time = int( float( seconds * 1000 ) / 100 )
        self.hide_status_bar()
        self.getControl( 900 ).setPercent( 0 )
        self.getControl( 900 ).setVisible( True )
        for percent in range( 101 ):
            self.getControl( 900 ).setPercent( percent )
            xbmc.sleep( sleep_time )
        self.getControl( 900 ).setVisible( False )
    
    def exit_script( self, restart=False ):
        self.clear_message_timer()
        self.close()
        if ( restart ): xbmc.executebuiltin( "XBMC.RunScript(%s)" % ( os.path.join( os.getcwd().replace( ";", "" ), "default.py" ), ) )

    def onClick( self, controlId ):
        if ( not self.command_running ):
            self.command_running = True
            if ( controlId == 10 ):
                self._kaid_restart()
            elif ( controlId == 20 ):
                self._kaid_kill()
            elif ( controlId == 30 ):
                self._kaid_upload()
            elif ( controlId == 40 ):
                self._router_reboot()
            elif ( controlId == 50 ):
                self.change_settings()
            self.command_running = False

    def onFocus( self, controlId ):
        pass

    def onAction(self, action):
        if ( not self.command_running ):
            button_key = self.controller_action.get( action.getButtonCode(), "n/a" )
            if ( button_key == "Keyboard ESC Button" or button_key == "Back Button" or button_key == "Remote Menu Button" ):
                self.exit_script()
            elif ( button_key == "Keyboard Menu Button" or button_key == "Y Button" or button_key == "Remote Title Button" or button_key == "White Button" ):
                self.change_settings()
            
class Start( threading.Thread ):
    """ Thread Class used to allow gui to show before all checks are done at start of script """
    def __init__( self, *args, **kwargs ):
        threading.Thread.__init__( self )
        self.function = kwargs[ "function" ]

    def run(self):
        self.function()


if ( __name__ == "__main__" ):
    ui = GUI( "script-KCP-main.xml", os.getcwd(), "Default" )
    ui.doModal()
    del ui
    sys.modules.clear()
