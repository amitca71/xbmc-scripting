"""
Main GUI for Apple Movie Trailers
"""

import sys
import xbmcgui

dialog = xbmcgui.DialogProgress()
def _progress_dialog( count=0, msg="" ):
    if ( count is None ):
        dialog.create( __scriptname__ )
    elif ( count > 0 ):
        percent = int( count * ( float( 100 ) / ( len( modules ) + 1 ) ) )
        dialog.update( percent, _( 50 ), _( 51 ), msg )
    else:
        dialog.close()
    
_ = sys.modules[ "__main__" ].__language__
__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__version__ = sys.modules[ "__main__" ].__version__
__svn_revision__ = sys.modules[ "__main__" ].__svn_revision__

try:
    _progress_dialog( None )
    modules = ( "os", "xbmc", "utilities", "trailers", "database", "context_menu", "cacheurl", "datetime", "urllib", )
    for count, module in enumerate( modules ):
        _progress_dialog( count + 1, "%s %s" % ( _( 52 ), module, ) )
        if ( module == "utilities" ):
            exec "from %s import *" % module
        else:
            exec "import %s" % module
except Exception, e:
    print str( e )
    _progress_dialog( -1 )
    xbmcgui.Dialog().ok( __scriptname__, _( 81 ) )
    raise


class GUI( xbmcgui.WindowXML ):
    # control id's
    CONTROL_TITLE_LABEL = 20
    CONTROL_BUTTON_GROUP_START = 103
    CONTROL_BUTTON_GROUP_END = 109
    CONTROL_TRAILER_LIST_START = 50
    CONTROL_TRAILER_LIST_END = 59
    CONTROL_TRAILER_LIST_PAGE_START = 2050
    CONTROL_TRAILER_LIST_PAGE_END = 2059
    CONTROL_TRAILER_LIST_PAGE_GROUP_START = 2550
    CONTROL_TRAILER_LIST_PAGE_GROUP_END = 2579
    CONTROL_TRAILER_LIST_COUNT = 2150
    CONTROL_CATEGORY_LIST = 60
    CONTROL_CATEGORY_LIST_PAGE = 2060
    CONTROL_CATEGORY_LIST_COUNT = 2160
    CONTROL_CATEGORY_LIST_PAGE_GROUP = ( 2650, 2660, 2661, )
    CONTROL_CAST_LIST = 70
    CONTROL_CAST_LIST_PAGE = 2070
    CONTROL_CAST_BUTTON = 170
    CONTROL_PLOT_TEXTBOX = 75
    CONTROL_PLOT_BUTTON = 175
    CONTROL_TRAILER_POSTER = 201
    CONTROL_OVERLAY_RATING = 202
    CONTROL_OVERLAY_FAVORITE = 203
    CONTROL_OVERLAY_WATCHED = 204
    CONTROL_OVERLAY_SAVED = 205
    CONTROL_TRAILER_TITLE_LABEL = 206
    CONTROL_TRAILER_LIST_GROUP = 3000
    CONTROL_CATEGORY_LIST_GROUP = 4000
    
    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXML.__init__( self, *args, **kwargs )
        self.startup = True
        ##Enable once we figure out why it crashes sometimes#################################
        ##self.videoplayer_resolution = int( xbmc.executehttpapi( "getguisetting(0,videoplayer.displayresolution)" ).replace("<li>","") )
        ######################################################################
        ##self.Timer = None
        self._get_settings()
        self._get_showtimes_scraper()
        self._get_custom_sql()
        self._setup_variables()
        self._set_startup_choices()

    def onInit( self ):
        self._set_shortcut_properties()
        self._set_info_properties()
        if ( self.startup ):
            self.startup = False
            self.getControl( self.CONTROL_TRAILER_LIST_GROUP ).setVisible( False )
            self._set_startup_category()
            if ( INSTALL_PLUGIN ):
                install_plugin( plugin=range( 0, 2 ), message=True)
        else:
            if ( self.trailer >= 0 ):
                self.markAsWatched( self.trailers.movies[ self.trailer ].watched + 1, self.trailer )            
            self.showTrailers( self.sql, self.params, self.trailer_pos, 2 )

    def _get_settings( self ):
        self.settings = Settings().get_settings()

    def _get_showtimes_scraper( self ):
        sys.path.append( os.path.join( BASE_RESOURCE_PATH, "showtimes_scrapers", self.settings[ "showtimes_scraper" ] ) )

    def _get_custom_sql( self ):
        self.search_sql = get_custom_sql()

    def _set_video_resolution( self, default=False ):
        """
        if ( self.settings[ "videoplayer_displayresolution" ] != 10 and not default ):
            # set the videoplayers resolution to AMT setting
            xbmc.executehttpapi( "SetGUISetting(0,videoplayer.displayresolution,%d)" % ( self.settings[ "videoplayer_displayresolution" ], ) )
        else:
            # set the videoplayers resolution back to XBMC setting
            xbmc.executehttpapi( "SetGUISetting(0,videoplayer.displayresolution,%d)" % ( self.videoplayer_resolution, ) )
        """
        pass

    def _setup_variables( self ):
        self.trailers = trailers.Trailers()
        self.query= database.Query()
        self.skin = self.settings[ "skin" ]
        self.flat_cache = ()
        self.sql = ""
        self.params = None
        self.display_info = False
        ##self.dummy()
        ##self.MyPlayer = MyPlayer( xbmc.PLAYER_CORE_MPLAYER, function=self.myPlayerChanged )
        self.update_method = 0
        #self.list_control_pos = [ 0, 0, 0, 0 ]
        self.search_keywords = ""

    # dummy() and self.Timer are currently used for the Player() subclass so when an onPlayback* event occurs, 
    # it calls myPlayerChanged() immediately.
    ##def dummy( self ):
    ##    self.Timer = threading.Timer( 60*60*60, self.dummy,() )
    ##    self.Timer.start()

    ##def myPlayerChanged( self, event ):
    ##    pass
        #if ( event == 0 and self.currently_playing_movie[1] >= 0 ):
        #    self.markAsWatched( self.currently_playing_movie[0] + 1, self.currently_playing_movie[1], self.currently_playing_movie[2] )
        #elif ( event == 2 ):
        #    self.currently_playing_movie = -1
        #    self.currently_playing_genre = -1
        
    def _set_startup_choices( self ):
        self.sql_category = ""
        self.params_category = None
        self.main_category = GENRES
        self.genres = self.trailers.categories
        self.current_display = [ [ GENRES , 0 ], [ 0, 1 ] ]

    def _set_startup_category( self ):
        startup_button = "Shortcut1"
        if ( self.settings[ "startup_category_id" ] == self.settings[ "shortcut2" ] ): startup_button = "Shortcut2"
        elif ( self.settings[ "startup_category_id" ] == self.settings[ "shortcut3" ] ): startup_button = "Shortcut3"
        self.setCategory( self.settings[ "startup_category_id" ], 1 )

    def setCategory( self, category_id=GENRES, list_category=0 ):
        self.category_id = category_id
        self.list_category = list_category
        if ( list_category > 0 ):
            if ( category_id == FAVORITES ):
                sql = self.query[ "favorites" ]
                params = ( 1, )
            elif ( category_id == DOWNLOADED ):
                sql = self.query[ "downloaded" ]
                params = ( "", )
            elif ( category_id == HD_TRAILERS ):
                sql = self.query[ "hd_trailers" ]
                params = ( "%p.mov%", )
            elif ( category_id == NO_TRAILER_URLS ):
                sql = self.query[ "no_trailer_urls" ]
                params = ( "[]", )
            elif ( category_id == WATCHED ):
                sql = self.query[ "watched" ]
                params = ( 0, )
            elif ( category_id == RECENTLY_ADDED ):
                sql = self.query[ "recently_added" ]
                params = None
            elif ( category_id == MULTIPLE_TRAILERS ):
                sql = self.query[ "multiple_trailers" ]
                params = None
            elif ( category_id == CUSTOM_SEARCH ):
                sql = self.search_sql
                params = None
            elif ( list_category == 1 ):
                sql = self.query[ "movies_by_genre_id" ]
                params = ( self.genres[category_id].id, )
            elif ( list_category == 2 ):
                sql = self.query[ "movies_by_studio_name" ]
                params = ( self.trailers.categories[category_id].title, )
            elif ( list_category == 3 ):
                sql = self.query[ "movies_by_actor_name" ]
                names = self.actor.split( " " )[:2]
                if ( len( names ) == 1 ):
                    params = ( "%%%s%%" % ( names[0], ), )
                else:
                    params = ( "%%%s %s%%" % ( names[0], names[1], ), )
            self.current_display = [ self.current_display[ 0 ], [ category_id, list_category ] ]
            self.showTrailers( sql, params )
        else:
            self.main_category = category_id
            if ( category_id == GENRES ):
                sql = self.query[ "genre_category_list" ]
            elif ( category_id == STUDIOS ):
                sql = self.query[ "studio_category_list" ]
            elif ( category_id == ACTORS ):
                sql = self.query[ "actor_category_list" ]
            self.current_display = [ [ category_id, list_category ], self.current_display[ 1 ] ]
            self.showCategories( sql )
        self.showControls( self.category_id <= GENRES and self.category_id > FAVORITES )
    
    def showCategories( self, sql, params=None, choice=0, force_update=False ):
        try:
            self.setCategoryLabel()
            if ( sql != self.sql_category or params != self.params_category or force_update ):
                #self.list_control_pos[ self.list_category ] = choice
                self.trailers.getCategories( sql, params )
                xbmcgui.lock()
                self.sql_category = sql
                self.params_category = params
                self.getControl( self.CONTROL_CATEGORY_LIST ).reset()
                if ( len( self.trailers.categories ) ):
                    for category in self.trailers.categories:
                        if ( self.main_category == GENRES ):
                            title = category.title.replace( "Newest", _( 150 ) ).replace( "Exclusives", _( 151 ) )
                        else:
                            title = category.title
                        thumbnail = "amt-generic-%s%s.png" % ( ( "genre", "studio", "actor", )[ abs( self.category_id ) - 1 ], ( "-i", "", )[ category.completed ], )
                        if ( self.main_category == ACTORS ):
                            actor_path = os.path.join( xbmc.translatePath( "special://profile/" ), "Thumbnails", "Video", xbmc.getCacheThumbName( "actor" + category.title )[ 0 ], xbmc.getCacheThumbName( "actor" + category.title ) )
                            thumbnail = ( thumbnail, actor_path, )[ os.path.isfile( actor_path ) ]
                        count = "(%d)" % ( category.count, )
                        list_item = xbmcgui.ListItem( title, count, thumbnail, thumbnail )
                        ##list_item.setInfo( "video", { "Genre": self.category } )
                        list_item.select( not category.completed )
                        self.getControl( self.CONTROL_CATEGORY_LIST ).addItem( list_item )
                    self._set_selection( self.CONTROL_CATEGORY_LIST, choice )#self.list_control_pos[ self.list_category ] )
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "[%s]", sys.exc_info()[ 1 ] )
        xbmcgui.unlock()

    def showTrailers( self, sql, params=None, choice=0, force_update=False ):
        try:
            self.trailer = -1
            self.setCategoryLabel()
            if ( sql != self.sql or params != self.params or force_update ):
                #self.list_control_pos[ self.list_category ] = choice
                if ( force_update != 2 ):
                    updated = self.trailers.getMovies( sql, params )
                    if ( updated ):
                        self.sql_category = ""
                xbmcgui.lock()
                self.sql = sql
                self.params = params
                self.clearList()
                if ( self.trailers.movies ):
                    for movie in self.trailers.movies: # now fill the list control
                        thumbnail, poster = self._get_thumbnail( movie )
                        total_trailers = ( "", " (x%d)" % len( movie.trailer_urls ), )[ len( movie.trailer_urls ) > 1 ]
                        urls = ( "(%s)", "%%s%s" % total_trailers, )[ len( movie.trailer_urls ) > 0 ]
                        #rating = ( "[%s]" % movie.rating, "", )[ not movie.rating ]
                        list_item = xbmcgui.ListItem( urls % ( movie.title, ), movie.rating, poster, thumbnail )
                        list_item.select( movie.favorite )
                        plot = ( movie.plot, _( 400 ), )[ not movie.plot ]
                        overlay = ( xbmcgui.ICON_OVERLAY_NONE, xbmcgui.ICON_OVERLAY_HD, )[ "720p.mov" in repr( movie.trailer_urls ) or "1080p.mov" in repr( movie.trailer_urls ) ]
                        # release date and year
                        try:
                            year = int( movie.release_date[ -5 ] )
                        except:
                            year = 0
                        date_added = "%s-%s-%s" % ( movie.date_added[ 8 : ], movie.date_added[ 5 : 7 ], movie.date_added[ : 4 ], )
                        list_item.setInfo( "video", { "Title": movie.title, "Date": date_added, "Overlay": overlay, "Plot": plot, "MPAA": movie.rating, "Year": year, "Studio": movie.studio, "Genre": movie.genres, "Count": movie.watched } )
                        format = xbmc.getRegion( "datelong" ).replace( "DDDD, ", "" ).replace( "MMMM", "%B" ).replace( "D", "%d" ).replace( "YYYY", "%Y" )
                        # set date added property
                        date_added = datetime.date( int( movie.date_added[ : 4 ] ), int( movie.date_added[ 5 : 7 ] ), int( movie.date_added[ 8 : ] ) ).strftime( format )
                        list_item.setProperty( "dateadded", date_added )
                        # set release date property
                        list_item.setProperty( "releasedate", movie.release_date )
                        # set watched date property
                        try:
                            watched_date = datetime.date( int( movie.watched_date[ : 4 ] ), int( movie.watched_date[ 5 : 7 ] ), int( movie.watched_date[ 8 : ] ) ).strftime( format )
                        except:
                            watched_date = ""
                        list_item.setProperty( "watcheddate", watched_date )
                        self.addItem( list_item )
                    self._set_selection( self.CONTROL_TRAILER_LIST_START, choice + ( choice == -1 ) )
                else: self.clearTrailerInfo()
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "[%s]", sys.exc_info()[ 1 ] )
        xbmcgui.unlock()

    def _get_thumbnail( self, movie ):
        poster = ( movie.poster, "amt-blank-poster.png", )[ not movie.poster ]
        if ( not movie.poster and self.settings[ "thumbnail_display" ] == 0 ):
            thumbnail = poster
        else:
            thumbnail = ( ( movie.thumbnail, movie.thumbnail_watched )[ movie.watched and self.settings[ "fade_thumb" ] ], "amt-generic-trailer%s.png" % ( ( "", "-w", )[ movie.watched > 0 ], ), "", )[ self.settings[ "thumbnail_display" ] ]
        return thumbnail, poster

    def _set_selection( self, list_control, pos=0 ):
        if ( list_control == self.CONTROL_TRAILER_LIST_START ): 
            self.setCurrentListPosition( pos )
            self.showTrailerInfo()
        elif ( list_control == self.CONTROL_CATEGORY_LIST ):
            self.getControl( self.CONTROL_CATEGORY_LIST ).selectItem( pos )
            choice = self._set_count_label( self.CONTROL_CATEGORY_LIST )

    def showControls( self, category ):
        xbmcgui.lock()
        self.getControl( self.CONTROL_CATEGORY_LIST_GROUP ).setVisible( category )
        self.getControl( self.CONTROL_TRAILER_LIST_GROUP ).setVisible( not category )
        xbmcgui.unlock()
        #self.showPlotCastControls( category )
        self.setFocus( self.getControl( ( self.CONTROL_CATEGORY_LIST_GROUP, self.CONTROL_TRAILER_LIST_GROUP, )[ not category ] ) )

    def _toggle_trailer_info( self ):
        self.display_info = not self.display_info
        self._set_info_properties()
        xbmc.sleep( 20 )
        if ( self.display_info ): self.setFocus( self.getControl( self.CONTROL_PLOT_BUTTON ) )
        else: self.setFocus( self.getControl( self.CONTROL_CAST_BUTTON ) )

    def setCategoryLabel( self ):
        category= u""
        if ( self.category_id == GENRES ):
            category = _( 113 )
        elif ( self.category_id == STUDIOS ):
            category = _( 114 )
        elif ( self.category_id == ACTORS ):
            category = _( 115 )
        elif ( self.category_id == FAVORITES ):
            category = _( 152 )
        elif ( self.category_id == DOWNLOADED ):
            category = _( 153 )
        elif ( self.category_id == HD_TRAILERS ):
            category = _( 160 )
        elif ( self.category_id == NO_TRAILER_URLS ):
            category = _( 161 )
        elif ( self.category_id == CUSTOM_SEARCH ):
            category = _( 162 )
        elif ( self.category_id == WATCHED ):
            category = _( 163 )
        elif ( self.category_id == RECENTLY_ADDED ):
            category = _( 164 )
        elif ( self.category_id == MULTIPLE_TRAILERS ):
            category = _( 165 )
        elif ( self.category_id >= 0 ):
            if ( self.list_category == 3 ):
                category = self.actor
            elif ( self.list_category == 2 ):
                category = self.trailers.categories[ self.category_id ].title
            elif ( self.list_category == 1 ):
                category = self.genres[ self.category_id ].title.replace( "Newest", _( 150 ) ).replace( "Exclusives", _( 151 ) )
        self.category = category
        self.setProperty( "Category", self.category )

    def _set_count_label( self, list_control ):
        separator = ( _( 96 ) )
        if ( list_control == self.CONTROL_TRAILER_LIST_START ):
            pos = self.getCurrentListPosition()
            self.getControl( self.CONTROL_TRAILER_LIST_COUNT ).setLabel( "%d %s %d" % ( pos + 1, separator, len( self.trailers.movies ), ) )
        else:
            pos = self.getControl( self.CONTROL_CATEGORY_LIST ).getSelectedPosition()
            self.getControl( self.CONTROL_CATEGORY_LIST_COUNT ).setLabel( "%d %s %d" % ( pos + 1, separator, len( self.trailers.categories ), ) )#self.getControl( self.CONTROL_CATEGORY_LIST ).size()
        return pos
    
    def clearTrailerInfo( self ):
        self.getControl( self.CONTROL_OVERLAY_RATING ).setImage( "" )
        self.getControl( self.CONTROL_CAST_LIST ).reset()
        self.getControl( self.CONTROL_TRAILER_LIST_COUNT ).setLabel( "" )
        self.showOverlays()
        
    def showTrailerInfo( self ):
        xbmcgui.lock()
        try:
            self.trailer_pos = self._set_count_label( self.CONTROL_TRAILER_LIST_START )
            #hack until panel control is a native python control
            if ( self.trailer_pos == -1 ): 
                self.setCurrentListPosition( len( self.trailers.movies ) - 1 )
                self.trailer_pos = self._set_count_label( self.CONTROL_TRAILER_LIST_START )
            self.getControl( self.CONTROL_TRAILER_TITLE_LABEL ).setEnabled( not self.trailers.movies[ self.trailer_pos ].favorite )
            if ( xbmc.skinHasImage( "%s/%s.png" % ( __scriptname__, self.trailers.movies[ self.trailer_pos ].rating, ) ) ):
                self.getControl( self.CONTROL_OVERLAY_RATING ).setImage( "%s/%s.png" % ( __scriptname__, self.trailers.movies[ self.trailer_pos ].rating, ) )
            else:
                self.getControl( self.CONTROL_OVERLAY_RATING ).setImage( self.trailers.movies[ self.trailer_pos ].rating_url )
            # Cast
            self.getControl( self.CONTROL_CAST_LIST ).reset()
            self.cast_exists = ( len( self.trailers.movies[ self.trailer_pos ].cast ) > 0 )
            thumbnail = "amt-generic-%sactor.png" % ( "no", "" )[ self.trailers.movies[ self.trailer_pos ].cast != [] ]
            if ( self.cast_exists ):
                for actor in self.trailers.movies[ self.trailer_pos ].cast:
                    actor_path = os.path.join( xbmc.translatePath( "special://profile/" ), "Thumbnails", "Video", xbmc.getCacheThumbName( "actor" + actor[ 0 ] )[ 0 ], xbmc.getCacheThumbName( "actor" + actor[ 0 ] ) )
                    actor_thumbnail = ( thumbnail, actor_path, )[ os.path.isfile( actor_path ) ]
                    actual_icon = ( "", actor_thumbnail, )[ actor_thumbnail != thumbnail ]
                    self.getControl( self.CONTROL_CAST_LIST ).addItem( xbmcgui.ListItem( actor[ 0 ], "", actual_icon, actor_thumbnail ) )
            else: 
                self.getControl( self.CONTROL_CAST_LIST ).addItem( xbmcgui.ListItem( _( 401 ), "", "", thumbnail ) )
            #self.showPlotCastControls( False )
            self.showOverlays( self.trailer_pos )
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "[%s]", sys.exc_info()[ 1 ] )
        xbmcgui.unlock()

    def showOverlays( self, trailer=-1 ):
        if ( trailer != -1 ):
            self.getControl( self.CONTROL_OVERLAY_FAVORITE ).setVisible( self.trailers.movies[ trailer ].favorite )
            self.getControl( self.CONTROL_OVERLAY_WATCHED ).setVisible( self.trailers.movies[ trailer ].watched )
            self.getControl( self.CONTROL_OVERLAY_SAVED ).setVisible( self.trailers.movies[ trailer ].saved != [] )
        else:
            self.getControl( self.CONTROL_OVERLAY_FAVORITE ).setVisible( False )
            self.getControl( self.CONTROL_OVERLAY_WATCHED ).setVisible( False )
            self.getControl( self.CONTROL_OVERLAY_SAVED ).setVisible( False )
            
    def getTrailerGenre( self ):
        genre = self.getControl( self.CONTROL_CATEGORY_LIST ).getSelectedPosition()
        if ( self.main_category == STUDIOS ): 
            list_category = 2
        elif ( self.main_category == ACTORS ): 
            list_category = 3
            self.actor = unicode( self.getControl( self.CONTROL_CATEGORY_LIST ).getSelectedItem().getLabel(), "utf-8" )
        else: list_category = 1
        self.setCategory( genre, list_category )

    def getActorChoice( self ):
        choice = self.getControl( self.CONTROL_CAST_LIST ).getSelectedPosition()
        self.actor = unicode( self.getControl( self.CONTROL_CAST_LIST ).getSelectedItem().getLabel(), "utf-8" )
        self.setCategory( choice, 3 )

    def _get_trailer_url( self, trailer ):
        title = self.trailers.movies[ trailer ].title
        trailer_urls = self.trailers.movies[ trailer ].trailer_urls
        saved = self.trailers.movies[ trailer ].saved
        items = ()
        urls = []
        for trailers in trailer_urls:
            # get intial choice
            choice = ( self.settings[ "trailer_quality" ], len( trailers ) - 1, )[ self.settings[ "trailer_quality" ] >= len( trailers ) ]
            # if quality is non progressive
            if ( self.settings[ "trailer_quality" ] <= 2 ):
                # select the correct non progressive trailer
                while ( trailers[ choice ].endswith( "p.mov" ) and choice != -1 ): choice -= 1
            # quality is progressive
            else:
                # select the proper progressive quality
                quality = ( "480p", "720p", "1080p", )[ self.settings[ "trailer_quality" ] - 3 ]
                # select the correct progressive trailer
                while ( quality not in trailers[ choice ] and trailers[ choice ].endswith( "p.mov" ) and choice != -1 ): choice -= 1
            # if we have a valid choice add the url to our list
            if ( choice >= 0 ):
                urls += [ trailers[ choice ] ]
        # if there are selections and there is more than one trailer, let user choose
        if len( urls ):
            trailer = 0
            if ( len( urls ) > 1 ):
                # sort the urls, hopefully they will then be in the order of release
                urls.sort()
                # let the user choose
                trailer = self._get_trailer( title, urls )
            # if the user did not cancel the dialog
            if ( trailer is not None ):
                # if play all was selected, get the filepath for each url
                if ( trailer == len( urls ) ):
                    for c, url in enumerate( urls ):
                        t = self.get_filepath( "%s%s" % ( title, os.path.splitext( url )[ 1 ], ), c + 1, len( urls ) > 1 )
                        items += ( ( t, url, c + 1, ), )
                else:
                    # we only want the trailer selected
                    t = self.get_filepath( "%s%s" % ( title, os.path.splitext( urls[ trailer ] )[ 1 ], ), trailer + 1, len( urls ) > 1 )
                    items = ( ( t, urls[ trailer ], trailer + 1, ), )
        return items

    def get_filepath( self, title, count, multiple ):
        # add our trailer number if there is more than one trailer
        filepath = "%s%s%s" % ( os.path.splitext( title )[ 0 ], ( "", "_%d" % ( count, ), )[ multiple ], os.path.splitext( title )[ 1 ], )
        # now make it legal
        filepath = make_legal_filepath( filepath, save_end=multiple )
        return filepath

    def _get_trailer( self, title, urls ):
        # if Auto play all trailers, return the play all selection
        if ( self.settings[ "auto_play_all" ] ):
            return len( urls )
        import chooser
        force_fallback = self.skin != "Default"
        choices = [ "%s %d%s - (%s)" % ( _( 99 ), c + 1, ( "", " - [HD]", )[ "720p.mov" in url or "1080p.mov" in url ], os.path.splitext( os.path.basename( url ) )[ 0 ] ) for c, url in enumerate( urls ) ]
        choices += [ _( 39 ) ]
        ch = chooser.GUI( "script-%s-chooser.xml" % ( __scriptname__.replace( " ", "_" ), ), os.getcwd(), self.skin, force_fallback, choices=choices, descriptions=[ "" for x in range( len( choices ) ) ], original=-1, selection=0, list_control=1, title=title )
        selection = ch.selection
        del ch
        return selection

    def playTrailer( self ):
        try:
            self.trailer = self.getCurrentListPosition()
            if ( len( self.trailers.movies[ self.trailer ].trailer_urls ) ):
                items = self._get_trailer_url( self.trailer )
                if ( items ):
                    playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
                    playlist.clear()
                    for count, ( title, url, selected ) in enumerate( items ):
                        LOG( LOG_DEBUG, self.__class__.__name__, "[url: %s]", repr( url ) )
                        filename = None
                        for saved in self.trailers.movies[ self.trailer ].saved:
                            #if ( title in saved[ 0 ] ):
                            if ( url == saved[ 1 ] ):
                                filename = saved[ 0 ]
                                self.url = saved[ 1 ]
                                break
                        if ( filename is None or not os.path.isfile( filename ) ):
                            #if ( url.endswith( "p.mov" ) ):
                                #self.core = xbmc.PLAYER_CORE_DVDPLAYER
                            #else:
                            #    self.core = xbmc.PLAYER_CORE_MPLAYER
                            self.url = url
                            if ( self.settings[ "mode" ] == 0 ):
                                filename = url + "?|User-Agent=%s" % ( urllib.quote_plus( cacheurl.__useragent__ ), )
                            else:
                                if ( self.settings[ "mode" ] == 1 ):
                                    if ( not self.check_cache( self.trailers.movies[ self.trailer ].title ) ):
                                        self.flat_cache = ()
                                    fetcher = cacheurl.HTTPProgressSave( save_title=title, clear_cache_folder=not self.flat_cache )
                                    filename = fetcher.urlretrieve( url )
                                    if ( filename and not self.check_cache( filename, 1 ) ):
                                        self.flat_cache += ( ( self.trailers.movies[ self.trailer ].title, filename, ), )
                                elif ( self.settings[ "mode" ] >= 2 ):
                                    fetcher = cacheurl.HTTPProgressSave( self.settings[ "save_folder" ], title )
                                    filename = fetcher.urlretrieve( url )
                                    if ( filename is not None ):
                                        poster = ( self.trailers.movies[ self.trailer ].poster, "amt-blank-poster.png", )[ not self.trailers.movies[ self.trailer ].poster ]
                                        self.saveThumbnail( filename, self.trailer, poster )
                        if ( filename is not None ):
                            listitem = xbmcgui.ListItem( self.trailers.movies[ self.trailer ].title, thumbnailImage=self.trailers.movies[ self.trailer ].poster )
                            if ( len( items ) > 1 ): s = count + 1
                            else: s = selected
                            plot = ( self.trailers.movies[ self.trailer ].plot, _( 400 ), )[ not self.trailers.movies[ self.trailer ].plot ]
                            t = "%s%s" % ( self.trailers.movies[ self.trailer ].title, ( "", " (%s %d)" % ( _( 99 ), s, ), )[ len( self.trailers.movies[ self.trailer ].trailer_urls ) > 1 ] )
                            try:
                                year = int( self.trailers.movies[ self.trailer ].release_date[ -5 : ] )
                            except:
                                year = 0
                            listitem.setInfo( "video", { "Title": t, "Year": year, "PlotOutline": plot, "Plot": plot, "Studio": self.trailers.movies[ self.trailer ].studio, "Genre": self.trailers.movies[ self.trailer ].genres } )
                            LOG( LOG_DEBUG, self.__class__.__name__, "[filename: %s]", repr( filename ) )
                            playlist.add( filename, listitem )
                    if ( len( playlist ) ):
                        self._set_video_resolution()
                        ##xbmc.Player( self.core ).play( playlist )
                        xbmc.Player().play( playlist )
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "[%s]", sys.exc_info()[ 1 ] )

    def check_cache( self, title, pos=0 ):
        exists = False
        for item in self.flat_cache:
            if ( title == item[ pos ] ):
                exists = True
                break
        return exists

    def saveThumbnail( self, filename, trailer, poster ):
        try: 
            new_filename = "%s.tbn" % ( os.path.splitext( filename )[0], )
            if ( not os.path.isfile( new_filename ) ):
                xbmc.executehttpapi("FileCopy(%s,%s)" % ( poster, new_filename, ) )
            if ( not self.check_cache( filename, 1 ) ):# not in repr( self.trailers.movies[ trailer ].saved ) ):
                self.trailers.movies[ trailer ].saved += [ ( filename, self.url, ) ]
                success = self.trailers.updateRecord( "movies", ( "saved", ), ( repr( self.trailers.movies[ trailer ].saved ), self.trailers.movies[ trailer ].idMovie, ), "idMovie" )
                #if ( success ):
                #    self.trailers.movies[ trailer ].saved = filename
                #    ##self.showOverlays( trailer )
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "[%s]", sys.exc_info()[ 1 ] )

    def showContextMenu( self ):
        if ( self.controlId == self.CONTROL_CATEGORY_LIST or self.controlId == self.CONTROL_CAST_LIST ):
            selection = self.getControl( self.controlId ).getSelectedPosition()
            #controlId= self.controlId
        else:
            selection = self.getCurrentListPosition()
        controlId = self.getFocusId()#self.CONTROL_TRAILER_LIST_START
        x, y = self.getControl( controlId ).getPosition()
        w = self.getControl( controlId ).getWidth()
        h = self.getControl( controlId ).getHeight()# - self.getControl( controlId ).getItemHeight()
        labels = ()
        functions = ()
        if ( self.CONTROL_TRAILER_LIST_START <= controlId <= self.CONTROL_TRAILER_LIST_END ):
            if ( len( self.trailers.movies[ selection ].trailer_urls ) ):
                labels += ( _( 501 ), )
                functions += ( self.playTrailer, )
            labels += ( _( 502 + self.trailers.movies[ selection ].favorite ), )
            functions += ( self.toggleAsFavorite, )
            if ( self.trailers.movies[ selection ].watched ): watched_lbl = "  (%d)" % ( self.trailers.movies[ selection ].watched, )
            else: watched_lbl = ""
            labels += ( "%s" % ( _( 504 + ( self.trailers.movies[ selection ].watched > 0 ) ) + watched_lbl, ), )
            functions += ( self.toggleAsWatched, )
            if ( self.category_id != MULTIPLE_TRAILERS ):
                labels += ( _( 506 ), )
                functions += ( self.refreshTrailerInfo, )
            if ( self.category_id == NO_TRAILER_URLS ):
                labels += ( _( 507 ), )
                functions += ( self.refreshAllTrailersInfo, )
            if ( self.category_id >= 0 and self.list_category == 1 ):
                labels += ( _( 512 ), )
                functions += ( self.refreshCurrentGenre, )
            if ( self.trailers.movies[ selection ].saved != [] ):
                labels += ( _( 509 ), )
                functions += ( self.deleteSavedTrailer, )
            elif ( self.check_cache( self.trailers.movies[ selection ].title ) ):
                labels += ( _( 508 ), )
                functions += ( self.saveCachedMovie, )
            if ( self.settings[ "showtimes_local" ] ):
                labels += ( _( 510 ), )
                functions += ( self.get_showtimes, )
        elif ( controlId == self.CONTROL_CATEGORY_LIST ):
            functions += ( self.getTrailerGenre, )
            if ( self.category_id == GENRES ):
                labels += ( _( 511 ), )
                labels += ( _( 512 ), )
                functions += ( self.refreshGenre, )
                labels += ( _( 513 ), )
                functions += ( self.refreshAllGenres, )
            elif ( self.category_id ==  STUDIOS ):
                labels += ( _( 521 ), )
            elif ( self.category_id ==  ACTORS ):
                labels += ( _( 531 ), )
        elif ( controlId == self.CONTROL_CAST_LIST and self.cast_exists ):
                labels += ( _( 531 ), )
                functions += ( self.getActorChoice, )
        if ( not self.trailers.complete ): 
            labels += ( _( 550 ), )
            functions += ( self.force_full_update, )
        force_fallback = self.skin != "Default"
        cm = context_menu.GUI( "script-%s-context.xml" % ( __scriptname__.replace( " ", "_" ), ), os.getcwd(), self.skin, force_fallback, area=( x, y, w, h, ), labels=labels )
        if ( cm.selection is not None ):
            functions[ cm.selection ]()
        del cm

    def force_full_update( self ):
        updated = self.trailers.fullUpdate()
        if ( self.list_category > 0 ):
            self.sql_category = ""
            trailer = self.getCurrentListPosition()
            self.showTrailers( self.sql, self.params, choice=trailer, force_update=2 )
        else:
            self.sql = ""
            if ( self.main_category == GENRES ):
                genre = self.getControl( self.CONTROL_CATEGORY_LIST ).getSelectedPosition()
                self.showCategories( self.sql_category, choice=genre, force_update=True )

    def markAsWatched( self, watched, trailer ):
        date = ( datetime.date.today(), "", )[ not watched ]
        success = self.trailers.updateRecord( "movies", ( "times_watched", "last_watched", ), ( watched, date, self.trailers.movies[ trailer ].idMovie, ), "idMovie" )
        if ( success ):
            self.trailers.movies[ trailer ].watched = watched
            self.trailers.movies[ trailer ].watched_date = str( date )
        else:
            LOG( LOG_ERROR, self.__class__.__name__, "[failed]" )

    def perform_search( self ):
        self.search_sql = ""
        if ( self.settings[ "use_simple_search" ] ):
            keyword = get_keyboard( default=self.search_keywords, heading= _( 95 ) )
            xbmc.sleep(10)
            if ( keyword ):
                keywords = keyword.split()
                self.search_keywords = keyword
                where = ""
                compare = False
                # this may be faster than regex, but not as accurate
                #where += "(LIKE '%% %s %%' OR title LIKE '%% %s.%%' OR title LIKE '%% %s,%%' OR title LIKE '%% %s:%%' OR title LIKE '%% %s!%%' OR title LIKE '%% %s-%%' OR title LIKE '%% %s?%%' OR title LIKE '%s %%' OR title LIKE '%s.%%' OR title LIKE '%s,%%' OR title LIKE '%s:%%' OR title LIKE '%s!%%' OR title LIKE '%s-%%' OR title LIKE '%s?%%' OR title LIKE '%% %s' OR title LIKE '%s' OR title LIKE '%%(%s' OR title LIKE '%% %s)' OR " % ( ( word, ) * 18 )
                pattern = ( "LIKE '%%%s%%'", "regexp('\\b%s\\b')", )[ self.settings[ "match_whole_words" ] ]
                for word in keywords:
                    if ( word.upper() == "AND" or word.upper() == "OR" ):
                        where += " %s " % word.upper()
                        compare = False
                        continue
                    elif ( word.upper() == "NOT" ):
                        where += "NOT "
                        continue
                    elif ( compare ):
                        where += " AND "
                        compare = False
                    where += "(title %s OR " % ( pattern % ( word, ), )
                    where += "plot %s OR " % ( pattern % ( word, ), )
                    where += "actor %s OR " % ( pattern % ( word, ), )
                    where += "studio %s OR " % ( pattern % ( word, ), )
                    where += "genre %s)" % ( pattern % ( word, ), )
                    compare = True
                self.search_sql = self.query[ "simple_search" ] % ( where, )
        else:
            import search
            force_fallback = self.skin != "Default"
            s = search.GUI( "script-%s-search.xml" % ( __scriptname__.replace( " ", "_" ), ), os.getcwd(), self.skin, force_fallback )
            s.doModal()
            if ( s.query ):
                self.search_sql = s.query
            del s
        if ( self.search_sql ):
            self.setCategory( CUSTOM_SEARCH, 1 )

    def changeSettings( self ):
        import settings
        force_fallback = self.skin != "Default"
        settings = settings.GUI( "script-%s-settings.xml" % ( __scriptname__.replace( " ", "_" ), ), os.getcwd(), self.skin, force_fallback, skin=self.skin, genres=self.genres )
        settings.doModal()
        if ( settings.changed ):
            self._get_settings()
            ok = False
            if ( settings.restart ):
                ok = xbmcgui.Dialog().yesno( __scriptname__, _( 240 ), "", _( 241 ), _( 271 ), _( 270 ) )
            if ( not ok ):
                self._set_shortcut_properties()
                self._set_info_properties()
                if ( settings.refresh and self.category_id not in ( GENRES, STUDIOS, ACTORS, ) ):
                    self.sql_category = ""
                    trailer = self.getCurrentListPosition()
                    self.showTrailers( self.sql, self.params, choice=trailer, force_update=2 )
                elif ( settings.refresh ):
                    self.sql = ""
                    genre = self.getControl( self.CONTROL_CATEGORY_LIST ).getSelectedPosition()
                    self.showCategories( self.sql_category, self.params_category, choice=genre, force_update=2 )
                #else: self.sql=""
            else: self.exitScript( True )
        del settings

    def _set_shortcut_properties( self ):
        shortcuts = { FAVORITES: _( 152 ), DOWNLOADED: _( 153 ), HD_TRAILERS: _( 160 ), NO_TRAILER_URLS: _( 161 ),
                            CUSTOM_SEARCH: _( 162 ), WATCHED: _( 163 ), RECENTLY_ADDED: _( 164 ), MULTIPLE_TRAILERS: _( 165 ), }
        self.setProperty( "shortcut1", shortcuts.get( self.settings[ "shortcut1" ], self.genres[ self.settings[ "shortcut1" ] ].title.replace( "Newest", _( 150 ) ).replace( "Exclusives", _( 151 ) ) ) )
        self.setProperty( "shortcut2", shortcuts.get( self.settings[ "shortcut2" ], self.genres[ self.settings[ "shortcut2" ] ].title.replace( "Newest", _( 150 ) ).replace( "Exclusives", _( 151 ) ) ) )
        self.setProperty( "shortcut3", shortcuts.get( self.settings[ "shortcut3" ], self.genres[ self.settings[ "shortcut3" ] ].title.replace( "Newest", _( 150 ) ).replace( "Exclusives", _( 151 ) ) ) )

    def _set_info_properties( self ):
        self.setProperty( "showinfo", ( "", "1", )[ self.display_info ] )

    def showCredits( self ):
        """ shows a credit window """
        import credits
        force_fallback = self.skin != "Default"
        c = credits.GUI( "script-%s-credits.xml" % ( __scriptname__.replace( " ", "_" ), ), os.getcwd(), self.skin, force_fallback )
        del c

    def updateScript( self ):
        import update
        updt = update.Update()
        del updt

    def toggleAsWatched( self ):
        trailer = self._set_count_label( self.CONTROL_TRAILER_LIST_START )
        watched = not ( self.trailers.movies[ trailer ].watched > 0 )
        self.markAsWatched( watched, trailer )

    def toggleAsFavorite( self ):
        trailer = self._set_count_label( self.CONTROL_TRAILER_LIST_START )
        favorite = not self.trailers.movies[ trailer ].favorite
        success = self.trailers.updateRecord( "movies", ( "favorite", ), ( favorite, self.trailers.movies[ trailer ].idMovie, ), "idMovie" )
        if ( success ):
            self.trailers.movies[ trailer ].favorite = favorite
            self.getListItem( trailer ).select( favorite )
            if ( self.category_id == FAVORITES ):
                self.trailers.movies.pop( trailer )
                self.removeItem( trailer )
            if ( not len( self.trailers.movies ) ): self.clearTrailerInfo()
            else: self.showTrailerInfo()

    def refreshAllGenres( self ):
        self.sql = ""
        genres = range( len( self.genres ) )
        self.trailers.refreshGenre( genres, refresh_trailers=self.settings[ "refresh_trailers" ] )
        if ( self.category_id == GENRES ):
            sql = self.query[ "genre_category_list" ]
            genre = self.getControl( self.CONTROL_CATEGORY_LIST ).getSelectedPosition()
            self.sql_category = ""
            self.showCategories( sql, choice=genre, force_update=True )
        
    def refreshGenre( self ):
        genre = self.getControl( self.CONTROL_CATEGORY_LIST ).getSelectedPosition()
        if ( self.current_display[ 1 ][ 0 ] == genre ):
            self.sql = ""
        self.trailers.refreshGenre( ( genre, ), refresh_trailers=self.settings[ "refresh_trailers" ] )
        self.sql_category = ""
        sql = self.query[ "genre_category_list" ]
        self.showCategories( sql, choice=genre, force_update=True )
        #count = "(%d)" % self.trailers.categories[ genre ].count
        #self.getControl( self.CONTROL_CATEGORY_LIST ).getSelectedItem().setLabel2( count )

    def refreshCurrentGenre( self ):
        trailer = self._set_count_label( self.CONTROL_TRAILER_LIST_START )
        self.sql_category = ""
        self.trailers.refreshGenre( ( self.category_id, ), refresh_trailers=self.settings[ "refresh_trailers" ] )
        self.showTrailers( self.sql, params=self.params, choice=trailer, force_update=True )

    def refreshTrailerInfo( self ):
        trailer = self._set_count_label( self.CONTROL_TRAILER_LIST_START )
        #self.getControl( self.CONTROL_TRAILER_POSTER ).setImage( "" )
        self.getControl( self.CONTROL_OVERLAY_RATING ).setImage( "" )
        self.trailers.refreshTrailerInfo( ( trailer, ) )
        self.showTrailers( self.sql, params=self.params, choice=trailer, force_update=True )

    def refreshAllTrailersInfo( self ):
        ##### add a progress dialog
        trailer = self._set_count_label( self.CONTROL_TRAILER_LIST_START )
        self.getControl( self.CONTROL_OVERLAY_RATING ).setImage( "" )
        trailers = range( len( self.trailers.movies ) )
        self.trailers.refreshTrailerInfo( trailers )
        self.showTrailers( self.sql, params=self.params, choice=trailer, force_update=True )

    def saveCachedMovie( self ):
        try:
            dialog = xbmcgui.DialogProgress()
            dialog.create( _( 56 ) )
            trailer = self._set_count_label( self.CONTROL_TRAILER_LIST_START )
            environment = os.environ.get( "OS", "xbox" )
            dirname = self.settings[ "save_folder" ]
            if ( environment == "xbox" or environment == "win32" ):
                dirname = dirname.replace( "\\", "/" )
            for count, filename in enumerate( self.flat_cache ):
                percent = int( ( count + 1 ) * ( float( 100 ) / len( self.flat_cache ) ) )
                new_filename = "%s%s" % ( dirname, os.path.basename( filename[ 1 ] ), )
                dialog.update( percent, "%s %s" % ( _( 1008 ), new_filename, ) )
                if ( not os.path.isfile( new_filename ) ):
                    xbmc.executehttpapi("FileCopy(%s,%s)" % ( filename[ 1 ], new_filename, ) )
                    if ( not new_filename.startswith( "smb://" ) ):
                        xbmc.executehttpapi("FileCopy(%s.conf,%s.conf)" % ( filename[ 1 ], new_filename, ) )
                    poster = ( self.trailers.movies[ trailer ].poster, "amt-blank-poster.png", )[ not self.trailers.movies[ trailer ].poster ]
                    self.saveThumbnail( new_filename, trailer, poster )
            self.showOverlays( trailer )
            dialog.close()
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "[%s]", sys.exc_info()[ 1 ] )
            dialog.close()
            xbmcgui.Dialog().ok( _( 56 ), _( 90 ) )
                
    def deleteSavedTrailer( self ):
        trailer = self._set_count_label( self.CONTROL_TRAILER_LIST_START )
        if ( xbmcgui.Dialog().yesno( "%s?" % ( _( 509 ), ), _( 82 ), self.trailers.movies[ trailer ].title ) ):
            for saved in self.trailers.movies[ trailer ].saved:
                if ( os.path.isfile( saved[ 0 ] ) ):
                    os.remove( saved[ 0 ] )
                if ( os.path.isfile( "%s.conf" % ( saved[ 0 ], ) ) ):
                    os.remove( "%s.conf" % ( saved[ 0 ], ) )
                if ( os.path.isfile( "%s.tbn" % ( os.path.splitext( saved[ 0 ] )[ 0 ], ) ) ):
                    os.remove( "%s.tbn" % ( os.path.splitext( saved[ 0 ] )[ 0 ], ) )
                success = self.trailers.updateRecord( "Movies", ( "saved", ), ( "[]", self.trailers.movies[ trailer ].idMovie, ), "idMovie" )
                if ( success ):
                    self.trailers.movies[ trailer ].saved = []
                    if ( self.category_id == DOWNLOADED ):
                        self.trailers.movies.pop( trailer )
                        self.removeItem( trailer )
                    if ( not len( self.trailers.movies ) ): self.clearTrailerInfo()
                    else: self.showTrailerInfo()

    def get_showtimes( self ):
        trailer = self._set_count_label( self.CONTROL_TRAILER_LIST_START )
        import showtimes
        force_fallback = self.skin != "Default"
        s = showtimes.GUI( "script-%s-showtimes.xml" % ( __scriptname__.replace( " ", "_" ), ), os.getcwd(), self.skin, force_fallback, title=self.trailers.movies[ trailer ].title, location=self.settings[ "showtimes_local" ] )
        del s

    def exitScript( self, restart=False ):
        ##if ( self.Timer is not None ): self.Timer.cancel()
        self._set_video_resolution( True )
        self.close()
        if ( restart ): xbmc.executebuiltin( "XBMC.RunScript(%s)" % ( os.path.join( os.getcwd(), "default.py" ), ) )

    def onClick( self, controlId ):
        try:
            if ( controlId == 100 ):
                self.setCategory( self.settings[ "shortcut1" ], 1 )
            elif ( controlId == 101 ):
                self.setCategory( self.settings[ "shortcut2" ], 1 )
            elif ( controlId == 102 ):
                self.setCategory( self.settings[ "shortcut3" ], 1 )
            elif ( controlId == 103 ):
                self.setCategory( GENRES, 0 )
            elif ( controlId == 104 ):
                self.setCategory( STUDIOS, 0 )
            elif ( controlId == 105 ):
                self.setCategory( ACTORS, 0 )
            elif ( controlId == 106 ):
                self.perform_search()
            elif ( controlId == 107 ):
                self.changeSettings()
            elif ( controlId == 108 ):
                self.showCredits()
            elif ( controlId == 109 ):
                self.updateScript()
            elif ( controlId in ( self.CONTROL_PLOT_BUTTON, self.CONTROL_CAST_BUTTON ) ):
                self._toggle_trailer_info()
            elif ( self.CONTROL_TRAILER_LIST_START <= controlId <= self.CONTROL_TRAILER_LIST_END ):
                self.playTrailer()
            elif ( controlId == self.CONTROL_CATEGORY_LIST ):
                self.getTrailerGenre()
            elif ( controlId == self.CONTROL_CAST_LIST and self.cast_exists ):
                self.getActorChoice()
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "[%s]", sys.exc_info()[ 1 ] )

    def onFocus( self, controlId ):
        #xbmc.sleep( 10 )
        if ( controlId == self.CONTROL_TRAILER_LIST_GROUP ):
            self.controlId = self.CONTROL_TRAILER_LIST_START
        elif ( controlId == self.CONTROL_CATEGORY_LIST_GROUP ):
            self.controlId = self.CONTROL_CATEGORY_LIST
        else:
            self.controlId = controlId

    def onAction( self, action ):
        try:
            if ( action in ACTION_EXIT_SCRIPT ):
                self.exitScript()
            elif ( action in ACTION_TOGGLE_DISPLAY ):
                self.setCategory( self.current_display[ self.list_category == 0 ][ 0 ], self.current_display[ self.list_category == 0 ][ 1 ] )
            else:
                if ( self.CONTROL_TRAILER_LIST_START <= self.controlId <= self.CONTROL_TRAILER_LIST_END ):
                    if ( action in ACTION_CONTEXT_MENU ):
                        self.showContextMenu()
                    ##elif ( action in ACTION_SELECT_ITEM ):
                    ##    self.playTrailer()
                    ###############################################################
                    elif ( action.getButtonCode() in ( 262, 263, ) or action in ACTION_MOVEMENT ):
                        self.showTrailerInfo()
                    ###############################################################
                elif ( self.CONTROL_TRAILER_LIST_PAGE_START <= self.controlId <= self.CONTROL_TRAILER_LIST_PAGE_END ):
                    if ( action in ACTION_MOVEMENT ):
                        self.showTrailerInfo()
                elif ( self.controlId == self.CONTROL_CATEGORY_LIST ):
                    if ( action in ACTION_CONTEXT_MENU ):
                        self.showContextMenu()
                    #elif ( action.getButtonCode() in SELECT_ITEM ):
                    #    self.getTrailerGenre()
                    elif ( action in ACTION_MOVEMENT_UP + ACTION_MOVEMENT_DOWN ):
                        choice = self._set_count_label( self.CONTROL_CATEGORY_LIST )
                elif ( self.controlId == self.CONTROL_CATEGORY_LIST_PAGE ):
                    if ( action in ACTION_MOVEMENT_UP + ACTION_MOVEMENT_DOWN ):
                        self._set_count_label( self.CONTROL_CATEGORY_LIST )
                elif ( self.controlId == self.CONTROL_CAST_LIST ):
                    if ( action in ACTION_CONTEXT_MENU ):
                        self.showContextMenu()
                elif ( ( self.CONTROL_TRAILER_LIST_PAGE_GROUP_START <= self.controlId <= self.CONTROL_TRAILER_LIST_PAGE_GROUP_END ) and action in ACTION_SELECT_ITEM ):
                    self.showTrailerInfo()
                elif ( self.controlId in self.CONTROL_CATEGORY_LIST_PAGE_GROUP and action in ACTION_SELECT_ITEM ):
                    self._set_count_label( self.CONTROL_CATEGORY_LIST )
                    #elif ( action.getButtonCode() in SELECT_ITEM ):
                    #    self.getActorChoice()
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "[%s]", sys.exc_info()[ 1 ] )

def main():
    _progress_dialog( len( modules ) + 1, _( 55 ) )
    settings = Settings().get_settings()
    force_fallback = settings[ "skin" ] != "Default"
    ui = GUI( "script-%s-main.xml" % ( __scriptname__.replace( " ", "_" ), ), os.getcwd(), settings[ "skin" ], force_fallback )
    _progress_dialog( -1 )
    ui.doModal()
    del ui
main()

"""
## Thanks Thor918 for this class ##
class MyPlayer( xbmc.Player ):
    def  __init__( self, *args, **kwargs ):
        xbmc.Player.__init__( self, *args, **kwargs )
        self.function = kwargs["function"]

    def onPlayBackStopped( self ):
        self.function( 0 )
    
    def onPlayBackEnded( self ):
        self.function( 1 )
    
    def onPlayBackStarted( self ):
        self.function( 2 )
"""