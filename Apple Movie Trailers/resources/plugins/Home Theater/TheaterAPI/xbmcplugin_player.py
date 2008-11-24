"""
    Player Module:
    - plays # of optional coming attraction videos
    - plays # of random trailers
    - plays # of optional feature presentation videos
    - plays selected video
    - plays # of optional end of presentation videos
"""

import xbmc
# set our title
g_title = unicode( xbmc.getInfoLabel( "ListItem.Title" ), "utf-8" )
# set our studio (only works if the user is using the video library)
g_studio = unicode( xbmc.getInfoLabel( "ListItem.Studio" ), "utf-8" )
# set our director (only works if the user is using the video library)
g_director = unicode( xbmc.getInfoLabel( "ListItem.Director" ), "utf-8" )
# set our genre (only works if the user is using the video library)
g_genre = unicode( xbmc.getInfoLabel( "ListItem.Genre" ), "utf-8" )
# set our rating (only works if the user is using the video library)
g_mpaa_rating = xbmc.getInfoLabel( "ListItem.MPAA" )
# set our thumbnail
g_thumbnail = xbmc.getInfoImage( "ListItem.Thumb" )
# set our plotoutline
g_plotoutline = unicode( xbmc.getInfoLabel( "ListItem.PlotOutline" ), "utf-8" )
# set our year
g_year = 0
if ( xbmc.getInfoLabel( "ListItem.Year" ) ):
    g_year = int( xbmc.getInfoLabel( "ListItem.Year" ) )
# set our rating
g_rating = 0.0
if ( xbmc.getInfoLabel( "ListItem.Rating" ) ):
    g_rating = float( xbmc.getInfoLabel( "ListItem.Rating" ) )

# create the progress dialog (we do it here so there is minimal delay with nothing displayed)
import xbmcgui
import sys
pDialog = xbmcgui.DialogProgress()
pDialog.create( sys.modules[ "__main__" ].__plugin__, xbmc.getLocalizedString( 30500 )  )

# main imports
import os
import xbmcplugin

from random import randrange
from urllib import unquote_plus
import datetime

from pysqlite2 import dbapi2 as sqlite


class _Info:
    def __init__( self, *args, **kwargs ):
        self.__dict__.update( kwargs )


class Trivia( xbmcgui.WindowXML ):
    import threading
    # special action codes
    ACTION_NEXT_SLIDE = ( 7, )
    ACTION_EXIT_SCRIPT = ( 9, 10, )

    def __init__( self, *args, **kwargs ):
        xbmcgui.WindowXML.__init__( self, *args, **kwargs )
        pDialog.update( -1, xbmc.getLocalizedString( 30510 ) )
        self.global_timer = None
        self.slide_timer = None
        self.exiting = False
        self.playlist = kwargs[ "playlist" ]
        self.trivia_music = kwargs[ "trivia_music" ]
        self.volume_percent = kwargs[ "trivia_music_volume" ]
        self.slide_time = kwargs[ "trivia_slide_time" ]
        self.trivia_end_image = kwargs[ "trivia_end_image" ]
        self.trivia_end_music = kwargs[ "trivia_end_music" ]
        self._get_slides( kwargs[ "trivia_path" ] )
        self._get_global_timer( kwargs[ "trivia_total_time" ] )

    def onInit( self ):
        pDialog.close()
        self._next_slide()
        self._start_music()

    def _start_music( self ):
        # get the current volume
        self.current_volume = int( xbmc.executehttpapi( "GetVolume" ).replace( "<li>", "" ) )
        # calculate the volume
        volume = self.current_volume * ( float( self.volume_percent ) / 100 )
        # set the volume percent from settings
        xbmc.executebuiltin( "XBMC.SetVolume(%d)" % ( volume, ) )
        if ( self.trivia_music ):
            xbmc.Player().play( self.trivia_music )

    def _get_slides( self, slide_path ):
        from random import randrange
        try:
            # our main slide list
            self.slides = []
            # get the directory listing
            entries = xbmc.executehttpapi( "GetDirectory(%s)" % ( slide_path, ) ).split( "\n" )
            # initialize type variables
            questions = []
            clues = []
            answers = []
            # enumerate through our entries list and separate question, clue, answer
            for entry in entries:
                if ( entry.lower().endswith( ".jpg" ) ):
                    # fix path
                    file_path = self._clean_file_path( entry )
                    # clue
                    if ( file_path.lower().endswith( "c.jpg" ) ):
                        clues += [ file_path ]
                    # answer
                    elif ( file_path.lower().endswith( "a.jpg" ) ):
                        answers += [ file_path ]
                    # question
                    else:
                        questions += [ file_path ]
            # group the appropriate slides into their own list and order them question, clue, answer
            slides = []
            for count, question in enumerate( questions ):
                slide = []
                # if there is a b slide, we need to reverse answer and question since the order is a,b
                if ( question.endswith( "b.jpg" ) ):
                    slide += [ answers[ count ] ]
                else:
                    slide += [ question ]
                # only add clue if it's not blank
                if ( len( clues ) > count ):
                    slide += [ clues[ count ] ]
                # again if there is a b slide, we need to reverse answer and question since the order is a,b
                if ( question.endswith( "b.jpg" ) ):
                    slide += [ question ]
                elif ( len( answers ) > count ):
                    slide += [ answers[ count ] ]
                # add our group
                slides += [ slide ]
            # randomize the groups and create our play list
            for count in range( len( slides ) ):
                rnd = randrange( len( slides ) )
                self.slides += slides[ rnd ]
                del slides[ rnd ]
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
        self.image_count = 0

    def _clean_file_path( self, path ):
        try:
            # replace <li>
            path = path.replace( "<li>", "" )
            # make it a unicode object
            path = unicode( path, "utf-8" )
        except:
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
        # return final rsult
        return path

    def _get_global_timer( self, trivia_time ):
        self.global_timer = self.threading.Timer( trivia_time * 60, self.exit_script,() )
        self.global_timer.start()

    def _get_slide_timer( self ):
        self.slide_timer = self.threading.Timer( self.slide_time, self._next_slide,() )
        self.slide_timer.start()

    def _next_slide( self ):
        if ( self.image_count == len( self.slides ) ):
            self.exit_script()
        else:
            if ( self.slide_timer is not None ):
                self.slide_timer.cancel()
            self.getControl( 100 ).setImage( self.slides[ self.image_count ] )
            self.image_count += 1
            self._get_slide_timer()

    def exit_script( self ):
        self.exiting = True
        if ( self.global_timer is not None ):
            self.global_timer.cancel()
        if ( self.slide_timer is not None ):
            self.slide_timer.cancel()
        # set the volume back to original
        xbmc.executebuiltin( "XBMC.SetVolume(%d)" % ( self.current_volume, ) )
        if ( self.trivia_end_image ):
            self.getControl( 100 ).setImage( self.trivia_end_image )
            if ( self.trivia_end_music ):
                xbmc.Player().play( self.trivia_end_music )
            xbmc.sleep( self.slide_time * 1000 )
        # TODO: enable player core when XBMC supports it for playlists
        xbmc.Player().play( self.playlist )# self.settings[ "player_core" ]
        # TODO: verify this does NOT cause problems
        #xbmc.sleep( 200 )
        self.close()

    def onClick( self, controlId ):
        pass

    def onFocus( self, controlId ):
        pass

    def onAction( self, action ):
        if ( action in self.ACTION_EXIT_SCRIPT and not self.exiting ):
            self.exit_script()
        elif ( action in self.ACTION_NEXT_SLIDE and not self.exiting ):
            self._next_slide()


class Main:
    # base paths
    BASE_CACHE_PATH = os.path.join( xbmc.translatePath( "P:\\Thumbnails" ), "Video" )
    BASE_DATA_PATH = os.path.join( xbmc.translatePath( "T:\\script_data" ), sys.modules[ "__main__" ].__script__ )

    def __init__( self ):
        self._get_settings()
        self._parse_argv()
        # create the playlist
        playlist = self._create_playlist()
        # play the videos
        self._play_videos( playlist )

    def _get_settings( self ):
        self.settings = {}
        self.settings[ "limit_query" ] = xbmcplugin.getSetting( "limit_query" ) == "true"
        self.settings[ "newest_only" ] = xbmcplugin.getSetting( "newest_only" ) == "true"
        self.settings[ "rating" ] = int( xbmcplugin.getSetting( "rating" ) )
        self.settings[ "number_trailers" ] = int( xbmcplugin.getSetting( "number_trailers" ) )
        self.settings[ "quality" ] = int( xbmcplugin.getSetting( "quality" ) )
        self.settings[ "only_hd" ] = xbmcplugin.getSetting( "only_hd" ) == "true"
        self.settings[ "only_unwatched" ] = xbmcplugin.getSetting( "only_unwatched" ) == "true"
        #self.settings[ "player_core" ] = ( xbmc.PLAYER_CORE_MPLAYER, xbmc.PLAYER_CORE_DVDPLAYER, )[ int( xbmcplugin.getSetting( "player_core" ) ) ]
        self.settings[ "trivia_path" ] = xbmcplugin.getSetting( "trivia_path" )
        self.settings[ "trivia_total_time" ] = ( 0, 5, 10, 15, 20, 25, 30, )[ int( xbmcplugin.getSetting( "trivia_total_time" ) ) ]
        self.settings[ "trivia_slide_time" ] = ( 10, 15, 20, 25, 30, 45, 60 )[ int( xbmcplugin.getSetting( "trivia_slide_time" ) ) ]
        self.settings[ "trivia_music" ] = xbmcplugin.getSetting( "trivia_music" )
        self.settings[ "trivia_music_volume" ] = int( xbmcplugin.getSetting( "trivia_music_volume" ).replace( "%", "" ) )
        self.settings[ "trivia_end_image" ] = xbmcplugin.getSetting( "trivia_end_image" )
        self.settings[ "trivia_end_music" ] = xbmcplugin.getSetting( "trivia_end_music" )
        self.settings[ "rating_videos_path" ] = xbmcplugin.getSetting( "rating_videos_path" )
        self.settings[ "coming_attraction_videos" ] = xbmcplugin.getSetting( "coming_attraction_videos" )
        self.settings[ "feature_presentation_videos" ] = xbmcplugin.getSetting( "feature_presentation_videos" )
        self.settings[ "end_presentation_videos" ] = xbmcplugin.getSetting( "end_presentation_videos" )
        self.settings[ "amt_db_path" ] = xbmcplugin.getSetting( "amt_db_path" )

    def _parse_argv( self ):
        # call _Info() with our formatted argv to create the self.args object
        exec "self.args = _Info(%s)" % ( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ), )
        # unquote path
        self.args.path = unquote_plus( self.args.path )

    def _create_playlist( self ):
        # create a video playlist
        playlist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
        # clear any possible items
        playlist.clear()
        # if there is a trailer intro video add it
        if ( self.settings[ "coming_attraction_videos" ] ):
            # create our trailer record
            trailer = ( self.settings[ "coming_attraction_videos" ], os.path.splitext( os.path.basename( unicode( self.settings[ "coming_attraction_videos" ], "utf-8" ) ) )[ 0 ], "", self.settings[ "coming_attraction_videos" ], "", "", "", "", "", "0 0 0", "", "", "", "", "", "", "Coming Attractions Intro", 0.0, "", )
            # create the listitem and fill the infolabels
            listitem = self._get_listitem( trailer )
            # add our item to the playlist
            playlist.add( unicode( self.settings[ "coming_attraction_videos" ], "utf-8" ), listitem )
        # fetch our random trailers
        trailers = self._fetch_records()
        # enumerate through our list of trailers and add them to our playlist
        for trailer in trailers:
            # we need to select the proper trailer url
            url = self._get_trailer_url( eval( trailer[ 3 ] ) )
            # add a false rating
            trailer += ( 0.0, )
            # create the listitem and fill the infolabels
            listitem = self._get_listitem( trailer + ( "", ) )
            # add our item to the playlist
            if ( url ):
                playlist.add( url, listitem )
                # mark trailer watched
                self._mark_watched( trailer[ 0 ] )
        # if there is a movie intro video add it
        if ( self.settings[ "feature_presentation_videos" ] ):
            # create our trailer record
            trailer = ( self.settings[ "feature_presentation_videos" ], os.path.splitext( os.path.basename( unicode( self.settings[ "feature_presentation_videos" ], "utf-8" ) ) )[ 0 ], "", self.settings[ "feature_presentation_videos" ], "", "", "", "", "", "0 0 0", "", "", "", "", "", "", "Feature Presentation Intro", 0.0, "", )
            # create the listitem and fill the infolabels
            listitem = self._get_listitem( trailer )
            # add our item to the playlist
            playlist.add( unicode( self.settings[ "feature_presentation_videos" ], "utf-8" ), listitem )
        # if there is a rating and intro video add it
        if ( self.settings[ "rating_videos_path" ] and g_mpaa_rating ):
            rating = g_mpaa_rating.split( " " )[ 1 ] + ".avi"
            rating_path = os.path.join( self.settings[ "rating_videos_path" ], rating )
            # if a rating exists add it
            if ( os.path.isfile( rating_path ) ):
                # create our trailer record
                trailer = ( rating_path, os.path.splitext( os.path.basename( rating_path ) )[ 0 ], "", rating_path, "", "", "", "", "", "0 0 0", "", "", "", "", "", "", "MPAA Rating", 0.0, "", )
                # create the listitem and fill the infolabels
                listitem = self._get_listitem( trailer )
                # add our item to the playlist
                playlist.add( rating_path, listitem )
        # set the genre if missing
        genre = g_genre
        if ( not g_genre ):
            genre = "Feature Presentation"
        # add the selected video to our playlist
        trailer = ( sys.argv[ 0 ] + sys.argv[ 2 ], g_title, "", self.args.path, g_thumbnail, g_plotoutline, "", "", "", "0 0 %d" % g_year, "", "", "", "", "", g_studio, genre, g_rating, g_director, )
        # create the listitem and fill the infolabels
        listitem = self._get_listitem( trailer )
        # add our item to the playlist
        playlist.add( self.args.path, listitem )
        # if there is a end of movie video add it
        if ( self.settings[ "end_presentation_videos" ] ):
            # create our trailer record
            trailer = ( self.settings[ "end_presentation_videos" ], os.path.splitext( os.path.basename( unicode( self.settings[ "end_presentation_videos" ], "utf-8" ) ) )[ 0 ], "", self.settings[ "end_presentation_videos" ], "", "", "", "", "", "0 0 0", "", "", "", "", "", "", "End of Feature Presentation", 0.0, "", )
            # create the listitem and fill the infolabels
            listitem = self._get_listitem( trailer )
            # add our item to the playlist
            playlist.add( unicode( self.settings[ "end_presentation_videos" ], "utf-8" ), listitem )
        return playlist

    def _play_videos( self, playlist ):
        if ( playlist and not pDialog.iscanceled() ):
            # if trive path an time play the trivia slides
            if ( self.settings[ "trivia_path" ] and self.settings[ "trivia_total_time" ] ):
                ui = Trivia( "plugin-%s-trivia.xml" % ( sys.modules[ "__main__" ].__plugin__.replace( " ", "_" ), ), os.getcwd(), "default", False, trivia_path=self.settings[ "trivia_path" ], trivia_total_time=self.settings[ "trivia_total_time" ], trivia_slide_time=self.settings[ "trivia_slide_time" ], trivia_music=self.settings[ "trivia_music" ], trivia_end_image=self.settings[ "trivia_end_image" ], trivia_end_music=self.settings[ "trivia_end_music" ], trivia_music_volume=self.settings[ "trivia_music_volume" ], playlist=playlist )
                ui.doModal()
                del ui
                xbmc.executebuiltin( "XBMC.ActivateWindow(2005)" )
            else:
                pDialog.close()
                # TODO: enable player core when XBMC supports it for playlists
                xbmc.Player().play( playlist )# self.settings[ "player_core" ]
        else:
            pDialog.close()

    def _fetch_records( self ):
        try:
            records = Records( amt_db_path=self.settings[ "amt_db_path" ] )
            # select only trailers with valid trailer urls
            sql = """
                        SELECT movies.*, studios.studio, genres.genre  
                        FROM movies, genres, genre_link_movie, studios, studio_link_movie 
                        WHERE movies.trailer_urls IS NOT NULL 
                        AND movies.trailer_urls!='[]' 
                        %s
                        %s
                        %s
                        AND genre_link_movie.idMovie=movies.idMovie 
                        AND genre_link_movie.idGenre=genres.idGenre 
                        AND studio_link_movie.idMovie=movies.idMovie 
                        AND studio_link_movie.idStudio=studios.idStudio 
                        %s
                        ORDER BY RANDOM() 
                        LIMIT %d;
                    """
            # mpaa ratings
            mpaa_ratings = [ "G", "PG", "PG-13", "R", "NC-17" ]
            rating_sql = ""
            # if the user set a valid rating add all up to the selection
            if ( self.settings[ "rating" ] < len( mpaa_ratings ) ):
                user_rating = mpaa_ratings[ self.settings[ "rating" ] ]
                rating_sql = "AND ("
                # enumerate through mpaa ratings and add the selected ones to our sql statement
                for rating in mpaa_ratings:
                    rating_sql += "rating='%s' OR " % ( rating, )
                    # if we found the users choice, we're finished
                    if ( rating == user_rating ): break
                # fix the sql statement
                rating_sql = rating_sql[ : -4 ] + ") "
            hd_sql = ( "", "AND (movies.trailer_urls LIKE '%720p.mov%' OR movies.trailer_urls LIKE '%1080p.mov%')", )[ self.settings[ "only_hd" ] and ( self.settings[ "quality" ] > 3 ) ]
            genre_sql = ""
            if ( self.settings[ "newest_only" ] ):
                genre_sql = "AND genres.genre='Newest'\n"
            watched_sql = ""
            if ( self.settings[ "only_unwatched" ] ):
                watched_sql = "AND movies.times_watched=0\n"
            # if the use sets limit query limit our search to the genre and rating of the movie
            if ( self.settings[ "limit_query" ] ):
                # genre limit
                ##movie_genres = unicode( xbmc.getInfoLabel( "ListItem.Genre" ), "utf-8" ).split( "/" )
                if ( not genre_sql ):
                    movie_genres = g_genre.split( "/" )
                    if ( movie_genres[ 0 ] != "" ):
                        genre_sql = "AND ("
                        for genre in movie_genres:
                            genre = genre.strip().replace( "Sci-Fi", "Science Fiction" )
                            if ( genre == "Action" or genre == "Adventure" ):
                                genre = "Action and Adventure"
                            # fix certain genres
                            genre_sql += "genres.genre='%s' OR " % ( genre, )
                        # fix the sql statement
                        genre_sql = genre_sql[ : -4 ] + ") "
                # rating limit TODO: decide if this should override the set rating limit
                ##movie_rating = xbmc.getInfoLabel( "ListItem.MPAA" ).split( " " )
                movie_rating = g_mpaa_rating.split( " " )
                if ( len( movie_rating ) > 1 ):
                    if ( movie_rating[ 1 ] in mpaa_ratings ):
                        rating_sql = "AND ("
                        for rating in mpaa_ratings:
                            rating_sql += "rating='%s' OR " % ( rating, )
                            # if we found the users choice, we're finished
                            if ( rating == movie_rating[ 1 ] ): break
                        # fix the sql statement
                        rating_sql = rating_sql[ : -4 ] + ") "
            # fetch our trailers
            result = records.fetch( sql % ( hd_sql, rating_sql, genre_sql, watched_sql, self.settings[ "number_trailers" ], ) )
            records.close()
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            result = []
        return result

    def _get_listitem( self, trailer ):
        # check for a valid thumbnail
        thumbnail = ""
        if ( trailer[ 4 ] and trailer[ 4 ] is not None ):
            thumbnail = os.path.join( self.BASE_DATA_PATH, ".cache", trailer[ 4 ][ 0 ], trailer[ 4 ] )
        else:
            thumbnail = self._get_thumbnail( trailer[ 3 ], trailer[ 0 ] )
        # set the default icon
        icon = "DefaultVideo.png"
        # only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
        listitem = xbmcgui.ListItem( trailer[ 1 ], iconImage=icon, thumbnailImage=thumbnail )
        # release date and year
        try:
            parts = trailer[ 9 ].split( " " )
            year = int( parts[ 2 ] )
        except:
            year = 0
        # add the different infolabels we want to sort by
        listitem.setInfo( type="Video", infoLabels={ "Title": trailer[ 1 ], "Year": year, "Studio": trailer[ 15 ], "Genre": trailer[ 16 ], "Plot": trailer[ 5 ], "PlotOutline": trailer[ 5 ], "Rating": trailer[ 17 ], "Director": trailer[ 18 ] } )
        # set release date property
        listitem.setProperty( "releasedate", trailer[ 9 ] )
        return listitem

    def _get_thumbnail( self, item, url ):
        # All these steps are necessary for the differnt caching methods of XBMC
        # make the proper cache filename and path so duplicate caching is unnecessary
        filename = xbmc.getCacheThumbName( item )
        thumbnail = os.path.join( self.BASE_CACHE_PATH, filename[ 0 ], filename )
        # if the cached thumbnail does not exist create the thumbnail based on url
        if ( not os.path.isfile( thumbnail ) ):
            filename = xbmc.getCacheThumbName( url )
            thumbnail = os.path.join( self.BASE_CACHE_PATH, filename[ 0 ], filename )
            # if the cached thumbnail does not exist create the thumbnail based on filepath.tbn
            if ( not os.path.isfile( thumbnail ) ):
                # create filepath to a local tbn file
                thumbnail = os.path.splitext( item )[ 0 ] + ".tbn"
                # if there is no local tbn file use a default
                if ( not os.path.isfile( thumbnail ) or thumbnail.startswith( "smb://" ) ):
                    thumbnail = ""
        return thumbnail

    def _get_trailer_url( self, trailer_urls ):
        # pick a random url (only applies to multiple urls)
        r = randrange( len( trailer_urls ) )
        # get the preferred quality
        qualities = [ "Low", "Medium", "High", "480p", "720p", "1080p" ]
        url = ""
        # get intial choice
        choice = ( self.settings[ "quality" ], len( trailer_urls[ r ] ) - 1, )[ self.settings[ "quality" ] >= len( trailer_urls[ r ] ) ]
        # if quality is non progressive
        if ( self.settings[ "quality" ] <= 2 ):
            # select the correct non progressive trailer
            while ( trailer_urls[ r ][ choice ].endswith( "p.mov" ) and choice != -1 ): choice -= 1
        # quality is progressive
        else:
            # select the proper progressive quality
            quality = ( "480p", "720p", "1080p", )[ self.settings[ "quality" ] - 3 ]
            # select the correct progressive trailer
            while ( quality not in trailer_urls[ r ][ choice ] and trailer_urls[ r ][ choice ].endswith( "p.mov" ) and choice != -1 ): choice -= 1
        # if there was a valid trailer set it
        if ( choice >= 0 ):
            url = trailer_urls[ r ][ choice ]
        return url

    def _mark_watched( self, idMovie ):
        try:
            # our database object
            records = Records( amt_db_path=self.settings[ "amt_db_path" ] )
            # needed sql commands
            fetch_sql = "SELECT times_watched FROM movies WHERE idMovie=?;"
            update_sql = "UPDATE movies SET times_watched=?, last_watched=? WHERE idMovie=?;"
            # we fetch the times watched so we can increment by one
            result = records.fetch( fetch_sql, ( idMovie, ) )
            if ( result ):
                # increment the times watched
                times_watched = result[ 0 ][ 0 ] + 1
                # get todays date
                last_watched = datetime.date.today()
                # update the record with our new values
                ok = records.update( update_sql, ( times_watched, last_watched, idMovie, ) )
            # close the database
            records.close()
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )


class Records:
    def __init__( self, *args, **kwargs ):
        self.connect( kwargs[ "amt_db_path" ] )

    def connect( self, db ):
        self.db = sqlite.connect( db )
        self.cursor = self.db.cursor()

    def commit( self ):
        try:
            self.db.commit()
            return True
        except: return False

    def close( self ):
        self.db.close()
    
    def fetch( self, sql, params=None ):
        try:
            if ( params is not None ): self.cursor.execute( sql, params )
            else: self.cursor.execute( sql )
            retval = self.cursor.fetchall()
        except:
            retval = None
        return retval

    def update( self, sql, params ):
        try:
            self.cursor.execute( sql, params )
            ok = self.commit()
            return True
        except:
            # oops print error message
            print "ERROR: %s::%s (%d) - %s" % ( self.__class__.__name__, sys.exc_info()[ 2 ].tb_frame.f_code.co_name, sys.exc_info()[ 2 ].tb_lineno, sys.exc_info()[ 1 ], )
            return False
