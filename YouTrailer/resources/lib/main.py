import os, sys, time
import xbmc
import xbmcgui
from pysqlite2 import dbapi2 as sqlite
import tmdb, traceback
import urllib, urllib2
from cgi import parse_qs

#enable language localization
_lang = xbmc.Language(os.getcwd()).getLocalizedString

DBPATH = xbmc.translatePath( "special://database/MyVideos34.db" )
__scriptname__ = sys.modules[ "__main__" ].__scriptname__

BASE_DATABASE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "script_data", __scriptname__, "YouTrailer.db" )

SLEEP_TIME = 5

class Main:
    def __init__(self):
        starttime = time.time()
        self.setupVariables()
        self.buildDatabase()
        self.file_name = sys.argv[1].strip()
        self.file_path = sys.argv[2].strip()
        self.main()
        while time.time() - starttime < 5:
            pass

    def buildDatabase( self ):
        if ( not os.path.isdir( os.path.dirname( BASE_DATABASE_PATH ) ) ):
            os.makedirs( os.path.dirname( BASE_DATABASE_PATH ) )
        db = sqlite.connect( BASE_DATABASE_PATH )
        cursor = db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS trailers (id INTEGER PRIMARY KEY, name VARCHAR(100), imdb_id VARACHAR(25), tmdb_id VARACHAR(25), trailer_url VARACHAR(100) );')
        db.commit()
        db.close()
        
    def setupVariables( self ):
        self.tmdb_api = tmdb.MovieDb()
        self.player = xbmc.Player()
        self.progress_dialog = xbmcgui.DialogProgress()
        self.dialog = xbmcgui.Dialog()
        self.full_url = ''
        self.imdb_id = ''
        self.tmdb_id = ''
        self.trailer_url = ''
        self.error_id = 35

    def main( self ):
        try:
            self.progress_dialog.create( __scriptname__, '' )
            self.fetchXbmcData()
            self.checkLocalTrailer()
            self.playTrailer()
            self.progress_dialog.close()
            self.validChecker()
        except:
            self.progress_dialog.close()
            self.dialog.ok( "%s - %s" % ( __scriptname__, _lang( 30 ) ), "", "", _lang( self.error_id ) )


    def fetchXbmcData( self ):
        try:
            db = sqlite.connect( DBPATH )
            cursor = db.cursor()
            cursor.execute( "SELECT idPath FROM path WHERE strPath = ?;" , ( self.file_path, ) )
            idPath = cursor.fetchone()[0]
            cursor.execute( "SELECT idFile FROM files WHERE idPath = ? AND strFilename = ?;", ( idPath, self.file_name ) )
            idFile = cursor.fetchone()[0]
            cursor.execute( "SELECT c00,c09,c14,c19 FROM movie WHERE idFile = ?;", ( idFile, ) )
            xbmc_data = cursor.fetchone()
            self.movie_name = xbmc_data[0].strip()
            self.imdb_id = xbmc_data[1].strip()
            self.movie_genre = xbmc_data[2].strip()
            self.trailer_url = xbmc_data[3].strip()
            db.close()
        except:
            self.error_id = 31
            raise


    def checkLocalTrailer( self ):
        if( ( not "http" in self.trailer_url ) and ( xbmc.executehttpapi( 'FileExists(%s)' % self.trailer_url ) == '<li>True' ) ):
            self.full_url = self.trailer_url
        else:
            self.checkTrailerUrl()

    def checkTrailerUrl( self ):
        try:
            self.fetchToken()
        except:
            self.checkDb()
             
    def checkDb( self ):
        try:
            db = sqlite.connect( BASE_DATABASE_PATH )
            cursor = db.cursor()
            cursor.execute( "SELECT trailer_url FROM trailers WHERE imdb_id = ?;" , ( self.imdb_id, ) )
            self.trailer_url = cursor.fetchone()[0]
            if( self.trailer_url == '' ):
                raise
            self.fetchToken()
        except:
            self.fetchUrl()
            self.fetchToken()

    def fetchUrl( self ):
        try:
            self.progress_dialog.update( 0, '%s %s' % ( self.movie_name, _lang( 2 ) ), "", _lang( 10 ) )
            api_results = self.tmdb_api.searchimdb( self.imdb_id )
            self.tmdb_id = api_results[0]['id']
            self.progress_dialog.update( 60, '%s %s' % ( self.movie_name, _lang( 2 ) ), "", _lang( 11 ) )
            api_results = self.tmdb_api.getinfo( self.tmdb_id )
            self.trailer_url = api_results[0]['trailer']
            if( self.trailer_url == '' ):
                raise
        except:
            self.error_id = 32
            raise

    def fetchToken( self ):
        try:
            trailer_id = self.trailer_url.split("watch?v=")[1]
            trailer_token_url = 'http://www.youtube.com/get_video_info?&video_id=%s&el=detailpage&ps=default&eurl=&gl=US&hl=en' % trailer_id
            self.progress_dialog.update( 90, '%s %s' % ( self.movie_name, _lang( 2 ) ), "", _lang( 13 ) )
            url_request = urllib2.Request( trailer_token_url )
            trailer_token_page = urllib2.urlopen( url_request ).read()
            trailer_token_info = parse_qs( trailer_token_page )
            trailer_token = urllib.unquote_plus( trailer_token_info['token'][0] )
            if( trailer_token == '' ):
                raise
            self.full_url = 'http://www.youtube.com/get_video?video_id=%s&t=%s%%3D' % ( trailer_id, trailer_token )
        except:
            self.error_id = 33
            raise
        
    def playTrailer( self ):
        try:
            self.progress_dialog.update( 100, '%s %s' % ( self.movie_name, _lang( 2 ) ), "", _lang( 14 ) )
            cache_name = xbmc.getCacheThumbName( os.path.join( self.file_path, self.file_name ) )
            thumb_image = os.path.join(  xbmc.translatePath( "special://thumbnails/Video/" ), cache_name[0],  cache_name )
            listitem = xbmcgui.ListItem( self.movie_name, thumbnailImage = thumb_image )
            listitem.setInfo( 'video', {'Title': '%s %s' % ( self.movie_name, _lang( 2 ) ), 'Studio' : __scriptname__, 'Genre' : self.movie_genre } )
            self.player.play( self.full_url, listitem )
        except:
            self.error_id = 34
            raise

    def validChecker( self ):
        for i in range(0, SLEEP_TIME):
            if( self.player.isPlayingVideo() ):
                if ( self.player.getPlayingFile() == self.full_url ):
                    self.addDb()
                    break
            time.sleep( 1 )

    def addDb( self ):
        try:
            db = sqlite.connect( BASE_DATABASE_PATH )
            cursor = db.cursor()
            cursor.execute( "SELECT id FROM trailers WHERE imdb_id = ?;" , ( self.imdb_id, ) )
            result = cursor.fetchone()
            if( result != None ):
                cursor.execute( "UPDATE trailers SET name=?, tmdb_id=?, trailer_url=? WHERE id='%s'" % result[0], ( self.movie_name, self.tmdb_id, self.trailer_url ) )
            else:
                cursor.execute('INSERT INTO trailers ( name, imdb_id, tmdb_id, trailer_url ) VALUES ( ?, ?, ?, ? );', ( self.movie_name, self.imdb_id, self.tmdb_id, self.trailer_url ) )
            db.commit()
            db.close()
        except:
            print "Failed to add to script Database"
            
Main()
