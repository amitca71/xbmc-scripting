"""
    Player module: downloads then plays trailers
"""

# TODO: remove this when dialog issue is resolved
import xbmc
# set our title
g_title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
# set our studio (only works if the user is using the video library)
g_studio = unicode( xbmc.getInfoLabel( "ListItem.Studio" ), "utf-8" )
# set our genre (only works if the user is using the video library)
g_genre = unicode( xbmc.getInfoLabel( "ListItem.Genre" ), "utf-8" )
# set our rating (only works if the user is using the video library)
g_mpaa_rating = xbmc.getInfoLabel( "ListItem.MPAA" )
# set our thumbnail
g_thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
# set our plotoutline
g_plotoutline = unicode( xbmc.getInfoLabel( "ListItem.PlotOutline" ), "utf-8" )
# set our released date
g_releasedate = xbmc.getInfoLabel( "ListItem.Property(releasedate)" )
# set our year
g_year = 0
if ( xbmc.getInfoLabel( "ListItem.Year" ) ):
    g_year = int( xbmc.getInfoLabel( "ListItem.Year" ) )

# create the progress dialog (we do it here so there is minimal delay with nothing displayed)
import xbmcgui
pDialog = xbmcgui.DialogProgress()
pDialog.create( g_title, xbmc.getLocalizedString( 30503 ) )

# main imports
import sys
import os
import xbmcplugin

import urllib


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class Main:
    # base paths
    BASE_CACHE_PATH = os.path.join( xbmc.translatePath( "special://profile" ), "Thumbnails", "Video" )

    def __init__( self ):
        self._get_settings()
        # parse argv for our trailer url and movie id
        self._parse_argv()
        # split trailer_url into separate videos
        urls = self.args.trailer_url.replace( "stack://", "" ).split( " , " ) 
        # do we need to download the videos
        if ( self.settings[ "mode" ] > 0 ):
            # download the video
            urls = self._download_video()
        # play the video
        self._play_video( urls )

    def _parse_argv( self ):
        # call _Info() with our formatted argv to create the self.args object
        exec "self.args = _Info(%s)" % ( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ).replace( "\\u0027", "'" ).replace( "\\u0022", '"' ).replace( "\\u0026", "&" ), )

    def _get_settings( self ):
        self.settings = {}
        self.settings[ "mode" ] = int( xbmcplugin.getSetting( "mode" ) )
        self.settings[ "download_path" ] = xbmcplugin.getSetting( "download_path" )
        self.settings[ "mark_watched" ] = xbmcplugin.getSetting( "mark_watched" ) == "true"
        self.settings[ "amt_db_path" ] = xbmc.translatePath( xbmcplugin.getSetting( "amt_db_path" ) )
        ##self.settings[ "player_core" ] = ( xbmc.PLAYER_CORE_MPLAYER, xbmc.PLAYER_CORE_DVDPLAYER, )[ int( xbmcplugin.getSetting( "player_core" ) ) ]

    def _download_video( self ):
        try:
            urls = self.args.trailer_url.replace( "stack://", "" ).split( " , " ) 
            # TODO: No longer needed as we sort in the videos module **** remove after testing
            #urls.sort()
            filepaths = []
            for count, url in enumerate( urls ):
                title = g_title
                # construct an xbox compatible filepath
                ext = os.path.splitext( url )[ 1 ]
                # we need to keep the end of the title if more than one trailer
                multiple = len( urls ) > 1
                # split and insert the trailer number if more than one
                filepath = "%s%s" % ( title, ( "", "_%d" % ( count + 1, ), )[ multiple ], )
                # folder to save to
                dirname = "Z:/"
                if ( not self.settings[ "download_path" ].startswith( "smb://" ) ):
                    dirname = self.settings[ "download_path" ]
                # get a valid filepath
                filepath = self._make_legal_filepath( os.path.join( dirname, filepath + ext ), save_end=multiple )
                # if the file does not exist, download it
                if ( os.path.isfile( os.path.join( self.settings[ "download_path" ], os.path.basename( filepath ) ) ) ):
                    filepath = os.path.join( self.settings[ "download_path" ], os.path.basename( filepath ) )
                else:
                    if ( self.settings[ "mode" ] == 1 ):
                        filepath = "Z:/AMT_Video_%d%s" % ( count, ext, )
                    # set our display message
                    self.msg = "%s %d of %d" % ( xbmc.getLocalizedString( 30500 ), count + 1, len( urls ), )
                    # fetch the video
                    urllib.urlretrieve( url, filepath, self._report_hook )
                    # make the conf file and copy to smb share if necessary
                    filepath = self._make_conf_file( filepath )
                filepaths += [ filepath ]
        except:
            if ( os.path.isfile( filepath ) ):
                os.remove( filepath )
            filepaths = []
            pDialog.close()
        return filepaths

    def _report_hook( self, count, blocksize, totalsize ):
        percent = int( float( count * blocksize * 100) / totalsize )
        pDialog.update( percent, self.msg )
        if ( pDialog.iscanceled() ): raise

    def _make_legal_filepath( self, path, compatible=False, extension=True, conf=True, save_end=False ):
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

    def _make_conf_file( self, filepath ):
        try:
            new_filepath = filepath
            # create conf file for better MPlayer playback
            if ( not os.path.isfile( filepath + ".conf" ) ):
                f = open( filepath + ".conf" , "w" )
                f.write( "nocache=1" )
                f.close()
            # if save location is a samba share, copy the file
            if ( self.settings[ "download_path" ].startswith( "smb://" ) ):
                new_filepath = os.path.join( self.settings[ "download_path" ], os.path.basename( filepath ) )
                new_thumbpath = os.path.join( self.settings[ "download_path" ], os.path.splitext( os.path.basename( filepath ) )[ 0 ] + ".tbn" )
                xbmc.executehttpapi("FileCopy(%s,%s)" % ( filepath, new_filepath, ) )
                xbmc.executehttpapi("FileCopy(%s,%s)" % ( g_thumbnail, new_thumbpath, ) )
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
        return new_filepath


    def _play_video( self, filepaths ):
        if ( filepaths ):
            # set the thumbnail
            thumbnail = g_thumbnail
            # set the default icon
            icon = "DefaultVideo.png"
            # create our playlist
            playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
            # clear any possible entries
            playlist.clear()
            # enumerate thru and add our item
            for count, filepath in enumerate( filepaths ):
                # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
                listitem = xbmcgui.ListItem( g_title, iconImage=icon, thumbnailImage=thumbnail )
                # set the key information
                listitem.setInfo( "video", { "Title": "%s%s" % ( g_title, ( "", " (%s %d)" % ( xbmc.getLocalizedString( 30504 ), count + 1, ) )[ len( filepaths ) > 1 ], ), "Genre": g_genre, "Studio": g_studio, "Plot": g_plotoutline, "PlotOutline": g_plotoutline, "Year": g_year } )
                # set release date property
                listitem.setProperty( "releasedate", g_releasedate )
                # add our item
                playlist.add( filepath, listitem )
            # mark the video watched
            if ( self.settings[ "mark_watched" ] ):
                self._mark_watched()
            # we're finished
            pDialog.close()
            # play the playlist (TODO: when playlist can set the player core, add this back in)
            xbmc.Player().play( playlist )#self.settings[ "player_core" ]

    def _mark_watched( self ):
        try:
            pDialog.update( -1, xbmc.getLocalizedString( 30502 ), xbmc.getLocalizedString( 30503 ) )
            from pysqlite2 import dbapi2 as sqlite
            import datetime
            fetch_sql = "SELECT times_watched FROM movies WHERE idMovie=?;"
            update_sql = "UPDATE movies SET times_watched=?, last_watched=? WHERE idMovie=?;"
            # connect to the database
            db = sqlite.connect( self.settings[ "amt_db_path" ] )
            # get our cursor object
            cursor = db.cursor()
            # we fetch the times watched so we can increment by one
            cursor.execute( fetch_sql, ( self.args.idMovie, ) )
            # increment the times watched
            times_watched = cursor.fetchone()[ 0 ] + 1
            # get todays date
            last_watched = datetime.date.today()
            # update the record with our new values
            cursor.execute( update_sql, ( times_watched, last_watched, self.args.idMovie, ) )
            # commit the update
            db.commit()
            # close the database
            db.close()
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
