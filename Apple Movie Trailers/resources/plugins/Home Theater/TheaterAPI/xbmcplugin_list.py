"""
    List module: creates a directory listing of videos and folders.
"""

# main imports
import os
import sys
import xbmc
import xbmcgui
import xbmcplugin

import datetime
from urllib import quote_plus, unquote_plus


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class Main:
    # base paths
    BASE_CACHE_PATH = os.path.join( xbmc.translatePath( "special://" ), "Thumbnails", "Video" )
    # add all video extensions wanted in lowercase
    VIDEO_EXT = xbmc.getSupportedMedia( "video" )

    def __init__( self ):
        self._get_settings()
        # if no database was found we need to run the script to create it.
        if ( not os.path.isfile( self.settings[ "amt_db_path" ] ) ):
            self._launch_script()
        else:
            if ( sys.argv[ 2 ] ):
                self._parse_argv()
            self._get_items( self.args.path )

    def _launch_script( self ):
        # we need to get the localized strings before the call to endOfDirectory()
        msg1 = xbmc.getLocalizedString( 30600 )
        msg2 = xbmc.getLocalizedString( 30601 )
        msg3 = xbmc.getLocalizedString( 30602 )
        # no database was found so notify XBMC we're finished, false so no blank list is shown
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=False )
        # we use "U:\\" for linux, windows and osx for platform mode
        drive = xbmc.translatePath( "special://home/" )
        # ask to run script to create the database
        if ( os.path.isfile( os.path.join( drive, "scripts", sys.modules[ "__main__" ].__script__, "default.py" ) ) ):
            if ( xbmcgui.Dialog().yesno( sys.modules[ "__main__" ].__plugin__, msg1, msg3 ) ):
                xbmc.executebuiltin( "XBMC.RunScript(%s)" % ( os.path.join( drive, "scripts", sys.modules[ "__main__" ].__script__, "default.py" ) ), )
        else:
            ok = xbmcgui.Dialog().ok( sys.modules[ "__main__" ].__plugin__, msg1, msg2, sys.modules[ "__main__" ].__svn_url__ )

    def _get_settings( self ):
        self.settings = {}
        self.settings[ "path" ] = self._get_path_list( xbmcplugin.getSetting( "path" ) )
        self.settings[ "use_db" ] = xbmcplugin.getSetting( "use_db" ) == "true"
        self.settings[ "limit_query" ] = xbmcplugin.getSetting( "limit_query" ) == "true"
        self.settings[ "rating" ] = int( xbmcplugin.getSetting( "rating" ) )
        self.settings[ "transparent_archives" ] = xbmc.executehttpapi( "getguisetting(1,filelists.unrollarchives)" ).replace("<li>","").lower() == "true"
        self.PluginCategory = ( "", xbmc.getLocalizedString( 30700 ), )[ self.settings[ "use_db" ] ]
        self.settings[ "fanart_image" ] = xbmcplugin.getSetting( "fanart_image" )
        self.settings[ "fanart_color1" ] = xbmcplugin.getSetting( "fanart_color1" )
        self.settings[ "fanart_color2" ] = xbmcplugin.getSetting( "fanart_color2" )
        self.settings[ "fanart_color3" ] = xbmcplugin.getSetting( "fanart_color3" )
        self.settings[ "amt_db_path" ] = xbmc.translatePath( xbmcplugin.getSetting( "amt_db_path" ) )
        # we need to set self.args.path
        self.args = _Info( path=self.settings[ "path" ] )

    def _get_path_list( self, paths ):
        # we do not want the slash at end
        if ( paths.endswith( "\\" ) or paths.endswith( "/" ) ):
            paths = paths[ : -1 ]
        # if this is not a multipath return it as a list
        if ( not paths.startswith( "multipath://" ) ): return [ paths ]
        # we need to parse out the separate paths in a multipath share
        fpaths = []
        # multipaths are separated by a forward slash(why not a pipe)
        path_list = paths[ 12 : ].split( "/" )
        # enumerate thru our path list and unquote the url
        for path in path_list:
        # we do not want the slash at end
            if ( path.endswith( "\\" ) or path.endswith( "/" ) ):
                path = path[ : -1 ]
            # add our path
            fpaths += [ path ]
        return fpaths

    def _parse_argv( self ):
        # call _Info() with our formatted argv to create the self.args object
        exec "self.args = _Info(%s)" % ( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ), )
        # we want this to be a list
        self.args.path = [ self.args.path ]

    def _get_items( self, path ):
        try:
            # smb share and local retrieve the lists differently than database
            if ( self.settings[ "use_db" ] ):
                ok = self._get_videodb_list()
            else:
                ok = self._get_list()
            # if successful and user did not cancel, set our sort orders, content, plugin category and fanart
            if ( ok ):
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_SIZE )
                xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
                if ( self.settings[ "use_db" ] ):
                    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
                    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_YEAR )
                    #xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
                    #xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_MPAA_RATING )
                    xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_STUDIO )
                # set content
                xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="movies" )
            try:
                # set our plugin category
                xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=self.PluginCategory )
                # set our fanart from user setting
                if ( self.settings[ "fanart_image" ] ):
                    xbmcplugin.setPluginFanart( handle=int( sys.argv[ 1 ] ), image=self.settings[ "fanart_image" ], color1=self.settings[ "fanart_color1" ], color2=self.settings[ "fanart_color2" ], color3=self.settings[ "fanart_color3" ] )
            except:
                pass
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            ok = False
        # send notification we're finished, successfully or unsuccessfully
        xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )

    def _get_videodb_list( self ):
        try:
            ok = True
            # TODO: change GLOB -> LIKE when and if sqLite get's updated with a fix
            rating_sql = ""
            mpaa_ratings = [ "G", "PG", "PG-13", "R", "NC-17" ]
            # if the user set a valid rating and limit query add all up to the selection
            if ( self.settings[ "limit_query" ] and self.settings[ "rating" ] < len( mpaa_ratings ) ):
                user_rating = mpaa_ratings[ self.settings[ "rating" ] ]
                rating_sql = "WHERE ("
                # enumerate through mpaa ratings and add the selected ones to our sql statement
                for rating in mpaa_ratings:
                    rating_sql += "movie.c12 GLOB '* %s *' OR " % ( rating, )
                    # if we found the users choice, we're finished
                    if ( rating == user_rating ): break
                # fix the sql statement
                rating_sql = rating_sql[ : -4 ] + ") "
            # TODO: add pagination (ORDER BY movie.c00 LIMIT %d OFFSET %d)
            # our sql statement movie.c00, movie.c01, movie.c09, movie.c12, movie.c14, movie.c18 
            sql = "SELECT path.strPath, files.strFileName, movie.* FROM movie JOIN files ON files.idFile=movie.idFile JOIN path ON files.idPath=path.idPath %sLIMIT 50 OFFSET %d;"
            cast_sql = "SELECT actors.strActor, actorlinkmovie.strRole FROM actorlinkmovie JOIN actors ON actors.idActor=actorlinkmovie.idActor WHERE actorlinkmovie.idMovie=%s;"
            # TODO: determine why 'u[[TRIPLE_QUOTE]]' as an OpenField response does not work as a unicode qualifier
            # format our response, so it returns a valid python list of records
            xbmc.executehttpapi( "SetResponseFormat(OpenRecordSet,%s)" % ( quote_plus( '[' ), ) )
            xbmc.executehttpapi( "SetResponseFormat(CloseRecordSet,%s)" % ( quote_plus( ']' ), ) )
            xbmc.executehttpapi( "SetResponseFormat(OpenRecord,%s)" % ( quote_plus( '(' ), ) )
            xbmc.executehttpapi( "SetResponseFormat(CloseRecord,%s)" % ( quote_plus( '), ' ), ) )
            # we use [[TRIPLE_QUOTE]] for fields so as not to interfere with quoted strings
            xbmc.executehttpapi( "SetResponseFormat(OpenField,%s)" % ( quote_plus( '[[TRIPLE_QUOTE]]' ), ) )
            xbmc.executehttpapi( "SetResponseFormat(CloseField,%s)" % ( quote_plus( '[[TRIPLE_QUOTE]], ' ), ) )
            # query the database
            items = []
            offset = 0
            records = ""
            while records != "[]":
                # create new sql based on our offset. (we limit the number of records returned each time to 100 for memory)
                new_sql = sql % ( rating_sql, offset, )
                # fetch the records
                records = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % quote_plus( new_sql ), )
                # eval response to a python list, replace \ with \\ or else eval will fail, same with handling quotes
                items += eval( records.replace( "\\", "\\\\" ).replace( '"', "[[QUOTE]]" ).replace( "[[TRIPLE_QUOTE]]", '"""' ) )
                # increment our record offset
                offset += 50
            # enumerate through our items list and add the info to our media list
            for item in items:
                # fetch the cast
                records = xbmc.executehttpapi( "QueryVideoDatabase(%s)" % quote_plus( cast_sql % ( item[ 2 ], ) ), )
                # our final actor/role list
                actors = []
                # eval response to a python list, replace \ with \\ or else eval will fail, same with handling quotes
                try:
                    cast = eval( records.replace( "\\", "\\\\" ).replace( '"', "[[QUOTE]]" ).replace( "[[TRIPLE_QUOTE]]", '"""' ) )
                    # we enumerate through and convert actors/roles to a unicode object
                    # we have to do this because adding a 'u' to OpenField response does not work
                    for actor in cast:
                        actors += [ ( unicode( actor[ 0 ], "utf-8" ), unicode( actor[ 1 ], "utf-8" ), ) ]
                except:
                    pass
                # concatenate the file and path if not a rar:// file, if a rar:// just use file
                if ( item[ 1 ].startswith( "rar://" ) ):
                    fpath = item[ 1 ]
                else:
                    fpath = item[ 0 ] + item[ 1 ]
                # add video to our list
                ok = self._add_item( ( unicode( fpath, "utf-8" ), unicode( item[ 3 ].replace( "[[QUOTE]]", '"' ), "utf-8" ), False, unicode( item[ 4 ].replace( "[[QUOTE]]", '"' ), "utf-8" ), unicode( item[ 5 ].replace( "[[QUOTE]]", '"' ), "utf-8" ), unicode( item[ 6 ].replace( "[[QUOTE]]", '"' ), "utf-8" ), item[ 7 ], item[ 8 ], unicode( item[ 9 ], "utf-8" ), item[ 10 ], item[ 11 ], item[ 12 ], item[ 13 ], item[ 14 ], item[ 15 ], item[ 16 ], item[ 17 ], unicode( item[ 18 ], "utf-8" ), item[ 19 ], item[ 20 ], unicode( item[ 21 ], "utf-8" ), actors ), len( items ) )
                if ( not ok ): raise
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            ok = False
        return ok

    def _get_list( self ):
        items = []
        for path in self.args.path:
            items += self._get_file_list( path )
        return self._fill_media_list( items )

    def _get_file_list( self, path ):
        #    if ( os.path.supports_unicode_filenames or os.environ.get( "OS", "n/a" ) == "win32"  or os.environ.get( "OS", "n/a" ) == "xbox" ):
        try:
            items = []
            # get the directory listing
            entries = xbmc.executehttpapi( "GetDirectory(%s)" % ( unquote_plus( path ), ) ).split( "\n" )
            # enumerate through our items list and add the full name to our entries list
            for entry in entries:
                if ( entry ):
                    # fix path
                    file_path = self._clean_file_path( entry )
                    # get the item info
                    title, isVideo, isFolder = self._get_file_info( file_path )
                    # add our entry to our items list
                    if ( isVideo or isFolder ):
                        items += [ ( file_path, title, isFolder, "", "", "", "", "0", "", "0", "", "", "", "", "", "", "", "", "", "", "", [], ) ]
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
        return items

    def _clean_file_path( self, path ):
        # replace <li>
        path = path.replace( "<li>", "" )
        # remove slash at end
        if ( path.endswith( "/" ) or path.endswith( "\\" ) ):
            path = path[ : -1 ]
        """
        # if it is a rar we check for a single video
        if ( path and path.endswith( ".rar" ) and self.settings[ "transparent_archives" ] ):
            # fetch the archives listing
            entries = xbmc.executehttpapi( "GetDirectory(%s)" % ( path, ) ).split( "\n" )
            # if there is only one entry set the new path
            if ( len( entries ) == 2 ):
                path = entries[ 1 ]
                # replace <li>
                path = path.replace( "<li>", "" )
                # remove slash at end
                if ( path.endswith( "/" ) or path.endswith( "\\" ) ):
                    path = path[ : -1 ]
        """
        # make it a unicode object
        path = unicode( path, "utf-8" )
        # return final rsult
        return path

    def _get_file_info( self, file_path ):
        try:
            # parse item for title
            title, ext = os.path.splitext( os.path.basename( file_path ) )
            # TODO: verify .zip can be a folder also
            # is this a folder?
            isFolder = ( ext == ".rar" or os.path.isdir( self._fix_stacked_path( file_path ) ) )
            # if it's a folder keep extension in title
            title += ( "", ext, )[ isFolder ]
            # default isVideo to false
            isVideo = False
            # if this is a file, check to see if it's a valid video file
            if ( not isFolder ):
                # if it is a video file add it to our items list
                isVideo = ( ext and ext.lower() in self.VIDEO_EXT )
            return title, isVideo, isFolder
        except:
            # oops print error message
            print repr( file_path )
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return "", False, False

    def _fill_media_list( self, items ):
        try:
            ok = True
            # enumerate through the list and add the item to our media list
            for item in items:
                # add the item
                ok = self._add_item( item, len( items ) )
                # if there was an error or the user cancelled, raise an exception
                if ( not ok ): raise
        except:
            # listing failed for some reason
            ok = False
        return ok

    def _add_item( self, item, total ):
        ok = True
        add = True
        # create our url
        url = '%s?path=%s&isFolder=%d' % ( sys.argv[ 0 ], repr( quote_plus( item[ 0 ] ) ), item[ 2 ], )
        # handle folders differently
        if ( item[ 2 ] ):
            # if a folder.jpg exists use that for our thumbnail
            #thumbnail = os.path.join( item[ 0 ], "%s.jpg" % ( title, ) )
            #if ( not os.path.isfile( thumbnail ) ): thumbnail = ""
            icon = "DefaultFolder.png"
            # only need to add label and icon, setInfo() and addSortMethod() takes care of label2
            listitem=xbmcgui.ListItem( label=item[ 1 ], iconImage=icon )
            # add the different infolabels we want to sort by
            listitem.setInfo( type="Video", infoLabels={ "Title": item[ 1 ] + " (%s)" % ( xbmc.getLocalizedString( 20334 ), ) } )
        else:
            # we only want the first path in a stack:// file item
            fpath = self._fix_stacked_path( item[ 0 ] )
            # call _get_thumbnail() for the path to the cached thumbnail
            thumbnail = self._get_thumbnail( fpath )
            # set the default icon
            icon = "DefaultVideo.png"
            try:
                # get the date of the file
                date = datetime.datetime.fromtimestamp( os.path.getmtime( fpath.encode( "utf-8" ) ) ).strftime( "%d-%m-%Y" )
                # get the size of the file
                size = long( os.path.getsize( fpath.encode( "utf-8" ) ) )
                # only need to add label and thumbnail, setInfo() and addSortMethod() takes care of label2
                listitem = xbmcgui.ListItem( label=item[ 1 ], iconImage=icon, thumbnailImage=thumbnail.encode( "utf-8" ) )
                # set watched status
                watched = item[ 12 ] == "true"
                # set an overlay if one is practical
                overlay = ( xbmcgui.ICON_OVERLAY_NONE, xbmcgui.ICON_OVERLAY_RAR, xbmcgui.ICON_OVERLAY_ZIP, )[ item[ 0 ].endswith( ".rar" ) + ( 2 * item[ 0 ].endswith( ".zip" ) ) ]
                overlay = ( overlay, xbmcgui.ICON_OVERLAY_WATCHED, )[ watched ]
                # add the different infolabels we want to sort by
                listitem.setInfo( type="Video", infoLabels={ "Title": item[ 1 ], "Date": date, "Size": size, "Overlay": overlay, "Plot": item[ 3 ], "Plotoutline": item[ 4 ], "TagLine": item[ 5 ], "Votes": item[ 6 ], "Rating": float( item[ 7 ] ), "Writer": item[ 8 ], "Year": int( item[ 9 ] ), "Watched": watched, "Duration": item[ 13 ], "MPAA": item[ 14 ], "Genre": item[ 16 ], "Director": item[ 17 ], "Studio": item[ 20 ], "Cast": item[ 21 ] } )
            except:
                # oops print error message
                add = False
                print repr( item[ 1 ] )
                print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
        if ( add ):
            # add the item to the media list
            ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=url, listitem=listitem, isFolder=item[ 2 ], totalItems=total )
        return ok

    def _fix_stacked_path( self, path ):
        # we need to strip stack:// and return only the first path
        if ( path.startswith( "stack://" ) ):
            path = path[ 8 : ].split( " , " )[ 0 ]
        return path

    def _get_thumbnail( self, path ):
        fpath = path
        # if this is a smb path, we need to eliminate username/password
        if ( path.startswith( "smb://" ) and "@" in path ):
            # split the path into useable parts
            share_string_list = path.split( "/" )
            # strip username/password
            share_string_list[ 2 ] = share_string_list[ 2 ].split( "@" )[ 1 ]
            # concatenate the list back together
            fpath = "/".join( share_string_list )
        # make the proper cache filename and path so duplicate caching is unnecessary
        filename = xbmc.getCacheThumbName( fpath )
        thumbnail = os.path.join( self.BASE_CACHE_PATH, filename[ 0 ], filename )
        # if the cached thumbnail does not exist check for a tbn file
        if ( not os.path.isfile( thumbnail ) ):
            # create filepath to a local tbn file
            thumbnail = os.path.splitext( path )[ 0 ] + ".tbn"
            # if there is no local tbn file leave blank
            if ( not os.path.isfile( thumbnail.encode( "utf-8" ) ) ):
                thumbnail = ""
        return thumbnail
