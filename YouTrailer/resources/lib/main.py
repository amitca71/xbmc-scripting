import os, sys, time
import xbmc
import xbmcgui
from pysqlite2 import dbapi2 as sqlite
import tmdb, traceback
import urllib, urllib2
from cgi import parse_qs

#enable language localization
_lang = xbmc.Language(os.getcwd()).getLocalizedString

dbpath = xbmc.translatePath( "special://database/MyVideos34.db" )
__scriptname__ = sys.modules[ "__main__" ].__scriptname__


class Main:
    def __init__(self):
        starttime = time.time()
        self.setupVariables()
        self.startScript()
        while time.time() - starttime < 5:
            pass

    def startScript( self ):
        file_name = sys.argv[1]
        file_path = sys.argv[2]
        fail_code = self.fetchXbmcData( file_name, file_path)
        if( fail_code ):
            self.error( fail_code )
            return
        self.progress_dialog.create( "%s - %s" % ( __scriptname__, self.movie_name ), "" )
        if( self.trailer_url == '' or self.trailer_url == None ):
            fail_code = self.fetchTmdbId()
            if( fail_code ):
                self.error( fail_code )
                return
            fail_code = self.fetchUrl()
            if( fail_code ):
                self.error( fail_code )
                return
        fail_code = self.fetchTrailerId()
        if( fail_code ):
            self.error( fail_code )
            return
        fail_code = self.fetchToken()
        if( fail_code ):
            self.error( fail_code )
            return
        fail_code = self.playTrailer( self.fetchFullUrl() )
        
            
    def error( self, fail_code ):
        self.progress_dialog.close()
        return self.dialog.ok( __scriptname__, _lang( 30 ), "", _lang( fail_code ) )

    def setupVariables( self ):
        self.tmdb_api = tmdb.MovieDb()
        self.player = xbmc.Player()
        self.progress_dialog = xbmcgui.DialogProgress()
        self.dialog = xbmcgui.Dialog()

    def fetchXbmcData( self, file_name, file_path ):
        try:
            db = sqlite.connect( dbpath )
            cursor = db.cursor()
            cursor.execute( "SELECT idPath FROM path WHERE strPath = ?;" , ( file_path, ) )
            idPath = cursor.fetchone()[0]
            cursor.execute( "SELECT idFile FROM files WHERE idPath = ? AND strFilename = ?;", ( idPath, file_name ) )
            idFile = cursor.fetchone()[0]
            cursor.execute( "SELECT c00,c09,c19 FROM movie WHERE idFile = ?;", ( idFile, ) )
            xbmc_data = cursor.fetchone()
            self.movie_name = xbmc_data[0].strip()
            self.imdb_id = xbmc_data[1].strip()
            self.trailer_url = xbmc_data[2].strip()
            db.close()
            if( self.imdb_id == '' ):
                return 31
            else:
                return 0
        except:
            traceback.print_exc()
            return 32
        
    def fetchTmdbId( self ):
        try:
            self.progress_dialog.update( 0, "" , "", _lang( 11 ) )
            api_results = self.tmdb_api.searchimdb( self.imdb_id )
            if( len( api_results ) < 1 ):
                return 33
            if not( 'id' in api_results[0] ):
                return 33
            self.tmdb_id = api_results[0]['id']
            if( self.tmdb_id == '' ):
                return 33
            else:
                return 0
        except:
            traceback.print_exc()
            return 34

    def fetchUrl( self ):
        try:
            self.progress_dialog.update( 30, "" , "", _lang( 12 ) )
            api_results = self.tmdb_api.getinfo( self.tmdb_id )
            if( len( api_results ) < 1 ):
                return 35
            if not( 'trailer' in api_results[0] ):
                return 35
            self.trailer_url = api_results[0]['trailer']
            if( self.trailer_url == '' ):
                return 35
            else:
                return 0
        except:
            traceback.print_exc()
            return 36

    def fetchTrailerId( self ):
        try:
            self.trailer_id = self.trailer_url.split("watch?v=")[1]
            return 0
        except:
            traceback.print_exc()
            return 37

    def fetchToken( self ):
        try:
            self.progress_dialog.update( 60, "" , "", _lang( 13 ) )
            trailer_token_url = self.fetchTokenUrl()
            url_request = urllib2.Request( trailer_token_url )
            try:
                trailer_token_page = urllib2.urlopen( url_request ).read()
            except:
                return 38
            trailer_token_info = parse_qs( trailer_token_page )
            if not( 'token' in trailer_token_info ):
                return 38
            self.trailer_token = urllib.unquote_plus( trailer_token_info['token'][0] )
            if( self.trailer_token == '' ):
                return 38
            return 0
        except:
            traceback.print_exc()
            return 39

    def fetchTokenUrl( self ):
        return 'http://www.youtube.com/get_video_info?&video_id=%s&el=detailpage&ps=default&eurl=&gl=US&hl=en' % self.trailer_id

    def fetchFullUrl( self ):
        return 'http://www.youtube.com/get_video?video_id=%s&t=%s%%3D' % ( self.trailer_id, self.trailer_token )

    def playTrailer( self, url ):
        self.player.play( url )
        return 0
Main()
