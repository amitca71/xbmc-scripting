"""
Catchall module for shared functions and constants

Nuka1195
"""

import sys
import os
import xbmc
import xbmcgui

DEBUG_MODE = 0

_ = sys.modules[ "__main__" ].__language__
__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__version__ = sys.modules[ "__main__" ].__version__
__svn_revision__ = sys.modules[ "__main__" ].__svn_revision__

# comapatble versions
DATABASE_VERSIONS = ( "pre-0.99.7.1", )
SETTINGS_VERSIONS = DATABASE_VERSIONS
# special categories
GENRES = -1
STUDIOS = -2
ACTORS = -3
FAVORITES = -6
DOWNLOADED = -7
HD_TRAILERS = -8
NO_TRAILER_URLS = -9
WATCHED = -10
RECENTLY_ADDED = -11
MULTIPLE_TRAILERS = -12
CUSTOM_SEARCH = -99
# base paths
BASE_DATA_PATH = os.path.join( xbmc.translatePath( "T:\\script_data" ), __scriptname__ )
BASE_SETTINGS_PATH = os.path.join( xbmc.translatePath( "P:\\script_data" ), os.path.basename( os.getcwd() ), "settings.txt" )
BASE_DATABASE_PATH = os.path.join( xbmc.translatePath( "P:\\script_data" ), os.path.basename( os.getcwd() ), "AMT.db" )
BASE_RESOURCE_PATH = sys.modules[ "__main__" ].BASE_RESOURCE_PATH
# special button codes
SELECT_ITEM = ( 11, 256, 61453, )
EXIT_SCRIPT = ( 247, 275, 61467, )
CANCEL_DIALOG = EXIT_SCRIPT + ( 216, 257, 61448, )
TOGGLE_DISPLAY = ( 216, 257, 61448, )
CONTEXT_MENU = ( 229, 261, 61533, )
MOVEMENT_UP = ( 166, 270, 61478, )
MOVEMENT_DOWN = ( 167, 271, 61480, )
MOVEMENT = ( 166, 167, 168, 169, 270, 271, 272, 273, 61477, 61478, 61479, 61480, )
# special action codes
ACTION_SELECT_ITEM = ( 7, )
ACTION_EXIT_SCRIPT = ( 10, )
ACTION_CANCEL_DIALOG = ACTION_EXIT_SCRIPT + ( 9, )
ACTION_TOGGLE_DISPLAY = ( 9, )
ACTION_CONTEXT_MENU = ( 117, )
ACTION_MOVEMENT_UP = ( 3, )
ACTION_MOVEMENT_DOWN = ( 4, )
ACTION_MOVEMENT = ( 1, 2, 3, 4, )
# Log status codes
LOG_ERROR, LOG_INFO, LOG_NOTICE, LOG_DEBUG = range( 1, 5 )


def _create_base_paths():
    """ creates the base folders """
    new = False
    # create the main cache and database paths
    if ( not os.path.isdir( BASE_DATA_PATH ) ):
        os.makedirs( BASE_DATA_PATH )
        new = True
    if ( not os.path.isdir( os.path.dirname( BASE_SETTINGS_PATH ) ) ):
        os.makedirs( os.path.dirname( BASE_SETTINGS_PATH ) )
    return new
INSTALL_PLUGIN = _create_base_paths()

def install_plugin( plugin_list, message=False ):
    # setup the plugins to install
    plugins = os.listdir( os.path.join( BASE_RESOURCE_PATH, "plugins" ) )
    plugins.sort()
    ok = True
    for plugin in plugin_list:
        # get the correct plugin message block start
        if ( message ):
            ok = xbmcgui.Dialog().yesno( plugins[ plugin ], _( 750 ), "", "", _( 712 ), _( 711 ), )
        if ( ok ):
            try:
                # we use "U:\\" for linux, windows and osx for platform mode
                drive = ( "U:\\", "Q:\\", )[ os.environ.get( "OS", "xbox" ) == "xbox" ]
                # get the thumbnail the user chooses
                thumbnail_copy_path = get_browse_dialog( default=os.path.join( BASE_RESOURCE_PATH, "plugins", plugins[ plugin ], "thumbnails", "thumbs", "default.tbn" ), heading="%s - %s" % ( _( 710 ), plugins[ plugin ], ), dlg_type=2, mask=".tbn", use_thumbs=True )
                # create the progress dialog
                dialog = xbmcgui.DialogProgress()
                dialog.create( plugins[ plugin ] )
                dialog.update(-1, _( 725 ), "", _( 67 ) )
                from shutil import copytree, rmtree, copyfile
                # the main plugin path to install to
                plugin_install_path = os.path.join( xbmc.translatePath( drive + "plugins" ), "video", plugins[ plugin ] )
                # path where plugin is copied from
                plugin_copy_path = os.path.join( BASE_RESOURCE_PATH, "plugins", plugins[ plugin ] )
                # we need pysqlite2 for database access
                pysqlite2_install_path = os.path.join( xbmc.translatePath( drive + "plugins" ), "video", plugins[ plugin ], "pysqlite2" )
                # path where pysqlite2 is copied from
                env = ( os.environ.get( "OS", "win32" ), "win32", )[ os.environ.get( "OS", "win32" ) == "xbox" ]
                pysqlite2_copy_path = os.path.join( BASE_RESOURCE_PATH, "platform_libraries", env, "pysqlite2" )
                # remove an existing install if it exists
                if ( os.path.isdir( plugin_install_path ) ):
                    rmtree( plugin_install_path )
                # copy our main directory
                copytree( plugin_copy_path, plugin_install_path )
                # copy pysqlite2
                copytree( pysqlite2_copy_path, pysqlite2_install_path )
                # default.tbn install path
                thumbnail_install_path = os.path.join( xbmc.translatePath( drive + "plugins" ), "video", plugins[ plugin ], "default.tbn" )
                # folder.jpg install path (probably not needed)
                folderjpg_install_path = os.path.join( xbmc.translatePath( drive + "plugins" ), "video", plugins[ plugin ], "folder.jpg" )
                # get the cached thumb name
                cached_thumbnail = xbmc.getCacheThumbName( os.path.join( drive + "plugins", "video", plugins[ plugin ] + "\\" ) )
                # cached thumb path (we delete the existing, so our plugin re-caches the new thumb)
                cached_thumbnail_path = os.path.join( xbmc.translatePath( "P:\\Thumbnails" ), "Programs", cached_thumbnail )
                # get the root cached thumb name
                root_cached_thumbnail = xbmc.getCacheThumbName( "plugin://video/"+ plugins[ plugin ] + "/" )
                # root cached thumb path (deleting does not work, so we overwrite the existing)
                root_cached_thumbnail_path = os.path.join( xbmc.translatePath( "P:\\Thumbnails" ), "Programs", root_cached_thumbnail )
                # copy default.tbn
                copyfile( thumbnail_copy_path, thumbnail_install_path )
                # copy folder.jpg (probably not needed)
                copyfile( thumbnail_copy_path, folderjpg_install_path )
                # copy default.tbn for our root folder (deleting never refreshes it)
                copyfile( thumbnail_copy_path, root_cached_thumbnail_path )
                # delete our cached thumbnail
                if ( os.path.isfile( cached_thumbnail_path ) ):
                    os.remove( cached_thumbnail_path )
                dialog.close()
                # TODO: enable this once webserver does not need to be running
                """
                # add the bookmark to sources.xml
                addbookmark = xbmcgui.Dialog().yesno( plugins[ plugin ], _( 723 ), _( 724 ), "", _( 712 ), _( 714 ) )
                if ( addbookmark ):
                    xbmc.executehttpapi( "Config(addbookmark,video,%s,plugin://video/%s/)" % ( plugins[ plugin ], plugins[ plugin ], ) )
                else:
                """
            except:
                # oops notify user an error occurred
                dialog.close()
                import traceback
                traceback.print_exc()
                ok = xbmcgui.Dialog().ok( plugins[ plugin ], _( 730 ) )
                return
    if ( ok ):
        # inform user of installation procedure for plugin
        ok = xbmcgui.Dialog().ok( plugins[ plugin ], _( 720 ), _( 721 ), _( 722 ) )

def get_keyboard( default="", heading="", hidden=False ):
    """ shows a keyboard and returns a value """
    keyboard = xbmc.Keyboard( default, heading, hidden )
    keyboard.doModal()
    if ( keyboard.isConfirmed() ):
        return keyboard.getText()
    return default

def get_numeric_dialog( default="", heading="", dlg_type=3 ):
    """ shows a numeric dialog and returns a value
        - 0 : ShowAndGetNumber		(default format: #)
        - 1 : ShowAndGetDate			(default format: DD/MM/YYYY)
        - 2 : ShowAndGetTime			(default format: HH:MM)
        - 3 : ShowAndGetIPAddress	(default format: #.#.#.#)
    """
    dialog = xbmcgui.Dialog()
    value = dialog.numeric( dlg_type, heading, default )
    return value

def get_browse_dialog( default="", heading="", dlg_type=1, shares="files", mask="", use_thumbs=False, treat_as_folder=False ):
    """ shows a browse dialog and returns a value
        - 0 : ShowAndGetDirectory
        - 1 : ShowAndGetFile
        - 2 : ShowAndGetImage
        - 3 : ShowAndGetWriteableDirectory
    """
    dialog = xbmcgui.Dialog()
    value = dialog.browse( dlg_type, heading, shares, mask, use_thumbs, treat_as_folder, default )
    return value

def LOG( status, _class_, format, *args ):
    if ( DEBUG_MODE >= status ):
        _function_ = "(%s) %s::%s" % ( sys._getframe( 1 ).f_code.co_filename, _class_, sys._getframe( 1 ).f_code.co_name, )
        xbmc.output( "%s: %s - %s\n" % ( ( "ERROR", "INFO", "NOTICE", "DEBUG", )[ status - 1 ], _function_, format % args, ) )

def get_custom_sql():
    try:
        query = ""
        file_object = open( os.path.join( BASE_DATA_PATH, "custom.sql" ), "r" )
        query = file_object.read()
        file_object.close()
    except:
        pass
    return query

def save_custom_sql( query ):
    try:
        file_object = open( os.path.join( BASE_DATA_PATH, "custom.sql" ), "w" )
        file_object.write( query )
        file_object.close()
        return True
    except:
        return False

def make_legal_filepath( path, compatible=False, extension=True, conf=True, save_end=False ):
    # xbox, win32 and linux have different filenaming requirements
    environment = os.environ.get( "OS", "xbox" )
    # first we normalize the path (win32 and xbox support / as path separators)
    if ( environment == "win32" or environment == "xbox" ):
        path = path.replace( "\\", "/" )
    # split our drive letter
    drive, tail = os.path.splitdrive( path )
    # split the rest of the path
    parts = tail.split( "/" )
    # if this is a linux path and compatible is true set the drive
    if ( not drive and parts[ 0 ].endswith( ":" ) and len( parts[ 0 ] ) == 2 and compatible ):
        drive = parts[ 0 ]
        parts[ 0 ] = ""
    # here is where we make the filepath valid
    if ( environment == "xbox" or environment == "win32" or compatible ):
        # win32 and xbox invalid characters
        illegal_characters = """,*=|<>?;:"+"""
        # enumerate through and make each part valid
        for count, part in enumerate( parts ):
            tmp_name = ""
            for char in part:
                # if char's ord() value is > 127 or an illegal character remove it
                if ( char in illegal_characters or ord( char ) > 127 ): char = ""
                tmp_name += char
            if ( environment == "xbox" or compatible ):
                # we need to trim the part if it's larger than 42, we need to account for ".conf"
                if ( len( tmp_name ) > 42 - ( conf * 5 ) ):
                    # special handling of the last part with extension
                    if ( count == len( parts ) - 1 and extension == True ):
                        # split the part into filename and extention
                        filename, ext = os.path.splitext( tmp_name )
                        # do we need to save the last two characters of the part for file number (eg _1, _2...)
                        if ( save_end ):
                            tmp_name = filename[ : 35 - len( ext ) ] + filename[ -2 : ]
                        else:
                            tmp_name = filename[ : 37 - len( ext ) ]
                        tmp_name = "%s%s" % ( tmp_name.strip(), ext )
                    # not the last part so just trim the length
                    else:
                        tmp_name = tmp_name[ : 42 ].strip()
            # add our validated part to our list
            parts[ count ] = tmp_name
    # join the parts into a valid path, we use forward slash to remain os neutral
    filepath = drive + "/".join( parts )
    # win32 needs to be encoded to utf-8
    if ( environment == "win32" ):
        return filepath.encode( "utf-8" )
    else:
        return filepath


class Settings:
    def get_settings( self, defaults=False ):
        """ read settings """
        try:
            settings = {}
            if ( defaults ): raise
            settings_file = open( BASE_SETTINGS_PATH, "r" )
            settings = eval( settings_file.read() )
            settings_file.close()
            if ( settings[ "version" ] not in SETTINGS_VERSIONS ):
                raise
        except:
            settings = self._use_defaults( settings, save=( defaults == False ) )
        return settings

    def _use_defaults( self, current_settings=None, save=True ):
        """ setup default values if none obtained """
        LOG( LOG_NOTICE, self.__class__.__name__, "[used default settings]" )
        settings = {}
        defaults = {  
            "skin": "Default",
            "trailer_quality": 2,
            "mode": 0,
            "save_folder": xbmc.translatePath( "U:\\" ),
            "thumbnail_display": 0,
            "fade_thumb": True,
            "startup_category_id": 10,
            "shortcut1": 10,
            "shortcut2": RECENTLY_ADDED,
            "shortcut3": FAVORITES,
            "refresh_newest": False,
            "videoplayer_displayresolution": 10,
            "use_simple_search": True,
            "match_whole_words": False,
            "showtimes_local": "33102",
            "showtimes_scraper": "Google",
            "auto_play_all": False,
            "refresh_trailers": False,
            }
        for key, value in defaults.items():
            # add default values for missing settings
            settings[ key ] = current_settings.get( key, defaults[ key ] )
        settings[ "version" ] = __version__
        if ( save ):
            ok = self.save_settings( settings )
        return settings

    def save_settings( self, settings ):
        """ save settings """
        try:
            settings_file = open( BASE_SETTINGS_PATH, "w" )
            settings_file.write( repr( settings ) )
            settings_file.close()
            return True
        except:
            LOG( LOG_ERROR, "%s (rev: %s) %s::%s (%d) [%s]", __scriptname__, __svn_revision__, self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return False
