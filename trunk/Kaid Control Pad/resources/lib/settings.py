import sys, os
import xbmc, xbmcgui
import guibuilder
import utilities

class GUI( xbmcgui.WindowDialog ):
    """ Settings module: used for changing settings """
    def __init__( self, *args, **kwargs ):
        self._ = kwargs[ "language" ]
        self.__scriptname__ = sys.modules[ "__main__" ].__scriptname__
        self.__version__ = sys.modules[ "__main__" ].__version__
        self.setupGUI()
        if ( not self.SUCCEEDED ): self._close_dialog()
        else:
            #self.show()
            self._set_variables()
            self._get_settings()
            self._setup_special()
            self._set_controls_values()
            self._set_page_visible()
            self._set_restart_required()

    def setupGUI( self ):
        """ sets up the gui using guibuilder """
        cwd = os.path.join( os.getcwd().replace( ";", "" ), "resources", "skins" )
        current_skin = xbmc.getSkinDir()
        if ( not os.path.exists( os.path.join( cwd, current_skin ))): current_skin = "default"
        skin_path = os.path.join( cwd, current_skin )
        image_path = os.path.join( skin_path, "gfx" )
        if ( self.getResolution() == 0 or self.getResolution() % 2 ): xml_file = "settings_16x9.xml"
        else: xml_file = "settings.xml"
        if ( not os.path.isfile( os.path.join( skin_path, xml_file ))): xml_file = "settings.xml"
        guibuilder.GUIBuilder( self, os.path.join( skin_path, xml_file ), image_path, useDescAsKey=True, language=self._, fastMethod=True, debug=False )

    def _set_variables( self ):
        """ initializes variables """
        self.current_page = 1
        self.total_pages = 2
        self.controller_action = utilities.setControllerAction()
        self.get_control( "Title Label" ).setLabel( self.__scriptname__ )
        self.get_control( "Version Label" ).setLabel( "%s: %s" % ( self._( 1006 ), self.__version__, ) )
        self.get_control( "Update Button" ).setEnabled( xbmc.getCondVisibility( "System.InternetState" ) )
        self.get_control( "Page Button" ).setVisible( self.total_pages > 1 )
        self.get_control( "Page Button" ).setEnabled( self.total_pages > 1 )
        # setEnabled( False ) if not used
        self.get_control( "Credits Button" ).setVisible( False )
        self.get_control( "Credits Button" ).setEnabled( False )

    def _get_settings( self ):
        """ reads settings """
        self.settings = utilities.Settings().get_settings()

    def _save_settings( self ):
        """ saves settings """
        ok = utilities.Settings().save_settings( self.settings )
        if ( not ok ):
            ok = xbmcgui.Dialog().ok( self.__scriptname__, self._( 230 ) )
        else:
            self._changed_message()

    def _set_page_visible( self ):
        """ shows the current page of settings """
        xbmcgui.lock()
        try: 
            for control in range( 1, 19 ):
                self.get_control( "Setting%s Button" % ( control, ) ).setVisible( self.current_page == int( ( control / 10 ) + 1 ) )
                self.get_control( "Setting%s Button" % ( control, ) ).setEnabled( self.current_page == int( ( control / 10 ) + 1 ) )
                self.get_control( "Setting%s Value" % ( control, ) ).setVisible( self.current_page == int( ( control / 10 ) + 1 ) )
        except: pass
        self.get_control( "Page Button" ).setLabel( "%s: %d/%d" % ( self._( 254 ), self.current_page, self.total_pages, ) )
        xbmcgui.unlock()
    
    def _get_keyboard( self, default="", heading="" ):
        """ shows a keyboard and returns a value """
        keyboard = xbmc.Keyboard( default, heading )
        keyboard.doModal()
        if ( keyboard.isConfirmed() ):
            return keyboard.getText()
        return default

    def _get_numeric( self, default="", heading="", type=3 ):
        """ shows a numeric dialog and returns a value
           - 0 : ShowAndGetNumber
           - 1 : ShowAndGetDate
           - 2 : ShowAndGetTime
           - 3 : ShowAndGetIPAddress
        """
        dialog = xbmcgui.Dialog()
        value = dialog.numeric( type, heading )
        if ( value ): return value
        else: return default

    def _get_browse_dialog( self, default="", heading="", type=1, shares="files" ):
        """ shows a browse dialog and returns a value
            - 0 : ShowAndGetDirectory
            - 1 : ShowAndGetFile
            - 2 : ShowAndGetImage
            - 3 : ShowAndGetWriteableDirectory
        """
        dialog = xbmcgui.Dialog()
        value = dialog.browse( type, heading, shares )
        if ( value ): return value
        else: return default

##### Start of unique defs #####################################################

##### Special defs, script dependent, remember to call them from _setup_special #################
    
    def _set_restart_required( self ):
        """ copies self.settings and add any settings that require a restart on change """
        self.settings_original = self.settings.copy()
        self.settings_restart = ( "firmware", "router_ip", "router_user", "router_pwd", )

    def _setup_special( self ):
        """ calls any special defs """
        self._setup_sniff_devices()
        self._setup_firmware()

    def _setup_sniff_devices( self ):
        """ special def for setting up sniff device choices """
        self.sniff_devices = ( "eth0", "en0", "br0", "vlan0", )
        for cnt, sd in enumerate( self.sniff_devices ):
            if ( sd == self.settings[ "sniff_device" ].lower() ):
                self.current_sniff_device = cnt
                break

    def _setup_firmware( self ):
        """ special def for setting up firmware choices """
        firmware = []
        self.current_firmware = 0
        os.path.walk( os.path.join( os.getcwd().replace( ";", "" ), "resources", "firmware" ), self._add_firmware, firmware )
        self.firmware = firmware
        for cnt, firmware in enumerate( self.firmware ):
            if ( firmware.lower() == self.settings[ "firmware" ].lower() ):
                self.current_firmware = cnt
                break
        
    def _add_firmware( self, firmware, path, files ):
        """ special def for adding firmware to a list variable """
        folder = os.path.split( path )[ 1 ]
        if ( folder.lower() != "firmware" ):
            firmware += [ folder ]

###### End of Special defs #####################################################

    def _set_controls_values( self ):
        """ sets the value labels """
        xbmcgui.lock()
        self.get_control( "Setting1 Value" ).setLabel( "%s" % ( self.settings[ "firmware" ], ) )
        self.get_control( "Setting2 Value" ).setLabel( "%s" % ( self.settings[ "router_ip" ], ) )
        self.get_control( "Setting3 Value" ).setLabel( "%s" % ( self.settings[ "router_user" ], ) )
        self.get_control( "Setting4 Value" ).setLabel( "%s" % ( self.settings[ "router_pwd" ], ) )
        self.get_control( "Setting5 Value" ).setLabel( "%s" % ( self.settings[ "path_to_kaid" ], ) )
        self.get_control( "Setting6 Value" ).setLabel( "%s" % ( self.settings[ "path_to_kaid_conf" ], ) )
        self.get_control( "Setting7 Value" ).setLabel( "%s" % ( ( "http://", "ftp://", )[ self.settings[ "upload_method" ] ], ) )
        self.get_control( "Setting8 Value" ).setLabel( "%s" % ( self.settings[ "xbox_user" ], ) )
        self.get_control( "Setting9 Value" ).setLabel( "%s" % ( self.settings[ "xbox_pwd" ], ) )
        self.get_control( "Setting10 Value" ).setLabel( "%s" % ( self.settings[ "sniff_device" ], ) )
        self.get_control( "Setting11 Value" ).setLabel( "%s" % ( str( self.settings[ "exit_to_kai" ] ), ) )
        xbmcgui.unlock()
    
    def _change_setting1( self ):
        """ changes settings #1 """
        self.current_firmware += 1
        if ( self.current_firmware == len( self.firmware ) ): self.current_firmware = 0
        self.settings[ "firmware" ] = self.firmware[ self.current_firmware ]
    
    def _change_setting2( self ):
        """ changes settings #2 """
        self.settings[ "router_ip" ] = self._get_numeric( self.settings[ "router_ip" ], self._( 202 ) )
        
    def _change_setting3( self ):
        """ changes settings #3 """
        self.settings[ "router_user" ] = self._get_keyboard( self.settings[ "router_user" ], self._( 203 ) )

    def _change_setting4( self ):
        """ changes settings #4 """
        self.settings[ "router_pwd" ] = self._get_keyboard( self.settings[ "router_pwd" ], self._( 204 ) )
        
    def _change_setting5( self ):
        """ changes settings #5 """
        self.settings[ "path_to_kaid" ] = self._get_browse_dialog( self.settings[ "path_to_kaid" ], self._( 205 ) )
    
    def _change_setting6( self ):
        """ changes settings #6 """
        self.settings[ "path_to_kaid_conf" ] = self._get_browse_dialog( self.settings[ "path_to_kaid_conf" ], self._( 206 ) )

    def _change_setting7( self ):
        """ changes settings #7 """
        self.settings[ "upload_method" ] = not self.settings[ "upload_method" ]
        
    def _change_setting8( self ):
        """ changes settings #8 """
        self.settings[ "xbox_user" ] = self._get_keyboard( self.settings[ "xbox_user" ], self._( 208 ) )

    def _change_setting9( self ):
        """ changes settings #9 """
        self.settings[ "xbox_pwd" ] = self._get_keyboard( self.settings[ "xbox_pwd" ], self._( 209 ) )

    def _change_setting10( self ):
        """ changes settings #10 """
        self.current_sniff_device += 1
        if ( self.current_sniff_device == len( self.sniff_devices ) ): self.current_sniff_device = 0
        self.settings[ "sniff_device" ] = self.sniff_devices[ self.current_sniff_device ]
            
    def _change_setting11( self ):
        """ changes settings #11 """
        self.settings[ "exit_to_kai" ] = not self.settings[ "exit_to_kai" ]
        
##### End of unique defs ######################################################
    
    def _update_script( self ):
        """ checks for updates to the script """
        import update
        updt = update.Update( language=self._ )
        del updt
            
    def _show_credits( self ):
        """ shows a credit window """
        import credits
        c = credits.GUI( language=self._ )
        c.doModal()
        del c

    def _change_page( self ):
        """ changes pages """
        self.current_page += 1
        if ( self.current_page > self.total_pages ):
            self.current_page = 1
        self._set_page_visible()
    
    def _changed_message( self ):
        """ checks for any changes that require a restart to take effect """
        restart = False
        for setting in self.settings_restart:
            if ( self.settings_original[ setting ] != self.settings[ setting ] ):
                restart = True
                break
        self._close_dialog( True, restart )

    def _close_dialog( self, changed=False, restart=False ):
        """ closes this dialog window """
        self.changed = changed
        self.restart = restart
        self.close()
        
    def get_control( self, key ):
        """ returns the control that matches the key """
        try: return self.controls[ key ][ "control" ]
        except: return None

    def onControl( self, control ):
        if ( control is self.get_control( "Ok Button" ) ):
            self._save_settings()
        elif ( control is self.get_control( "Cancel Button" ) ):
            self._close_dialog()
        elif ( control is self.get_control( "Update Button" ) ):
            self._update_script()
        elif ( control is self.get_control( "Credits Button" ) ):
            self._show_credits()
        elif ( control is self.get_control( "Page Button" ) ):
            self._change_page()
        else:
            if ( control is self.get_control( "Setting1 Button" ) ):
                self._change_setting1()
            elif ( control is self.get_control( "Setting2 Button" ) ):
                self._change_setting2()
            elif ( control is self.get_control( "Setting3 Button" ) ):
                self._change_setting3()
            elif ( control is self.get_control( "Setting4 Button" ) ):
                self._change_setting4()
            elif ( control is self.get_control( "Setting5 Button" ) ):
                self._change_setting5()
            elif ( control is self.get_control( "Setting6 Button" ) ):
                self._change_setting6()
            elif ( control is self.get_control( "Setting7 Button" ) ):
                self._change_setting7()
            elif ( control is self.get_control( "Setting8 Button" ) ):
                self._change_setting8()
            elif ( control is self.get_control( "Setting9 Button" ) ):
                self._change_setting9()
            elif ( control is self.get_control( "Setting10 Button" ) ):
                self._change_setting10()
            elif ( control is self.get_control( "Setting11 Button" ) ):
                self._change_setting11()
            self._set_controls_values()
            
    def onAction( self, action ):
        button_key = self.controller_action.get( action.getButtonCode(), "n/a" )
        if ( button_key == "Keyboard Backspace Button" or button_key == "B Button" or button_key == "Remote Back Button" ):
            self._close_dialog()
        elif ( button_key == "Keyboard ESC Button" or button_key == "Back Button" or button_key == "Remote Menu Button" ):
            self._save_settings()
