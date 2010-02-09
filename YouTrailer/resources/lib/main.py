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

_VALID_URL = r'^((?:http://)?(?:\w+\.)?youtube\.com/(?:(?:v/)|(?:(?:watch(?:\.php)?)?[\?#](?:.+&)?v=)))?([0-9A-Za-z_-]+)(?(1).+)?$'
_available_formats = ['37', '22', '35', '18', '5', '17', '13', None] # listed in order of priority for -b flag
_LANG_URL = r'http://uk.youtube.com/?hl=en&persist_hl=1&gl=US&persist_gl=1&opt_out_ackd=1'
_AGE_URL = 'http://www.youtube.com/verify_age?next_url=/&gl=US&hl=en'


std_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
	'Accept-Language': 'en-us,en;q=0.5',
}



class Main:
    def __init__(self):
        starttime = time.time()
        self.setupVariables()
        self.buildDatabase()
        self.movie_name = xbmc.getInfoLabel( 'listitem.title' )
        self.movie_director = xbmc.getInfoLabel( 'listitem.director' )
        self.movie_year = xbmc.getInfoLabel( 'listitem.year' )
        self.movie_genre = xbmc.getInfoLabel( 'listitem.genre' )
        self.main()
        while time.time() - starttime < 5:
            pass

    def buildDatabase( self ):
        if ( not os.path.isdir( os.path.dirname( BASE_DATABASE_PATH ) ) ):
            os.makedirs( os.path.dirname( BASE_DATABASE_PATH ) )
        db = sqlite.connect( BASE_DATABASE_PATH )
        cursor = db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS trailers (id INTEGER PRIMARY KEY, name VARCHAR(100), imdb_id VARACHAR(25), tmdb_id VARACHAR(25), trailer_url VARACHAR(100), format INTEGER(5));')
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
        self.error_message = ''

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
            self.dialog.ok( "%s - %s" % ( __scriptname__, _lang( 30 ) ), "", self.error_message, _lang( self.error_id ) )


    def fetchXbmcData( self ):
        try:
            db = sqlite.connect( DBPATH )
            cursor = db.cursor()
            cursor.execute( "SELECT c09,c19 FROM movie WHERE c00 = ? AND c07 = ? AND c15 = ?;", ( self.movie_name, self.movie_year, self.movie_director ) )
            xbmc_data = cursor.fetchone()
            self.imdb_id = xbmc_data[0].strip()
            self.trailer_url = xbmc_data[1].strip()
            db.close()
        except:
            traceback.print_exc()
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
            cursor.execute( "SELECT tmdb_id, trailer_url FROM trailers WHERE imdb_id = ?;" , ( self.imdb_id, ) )
            data = cursor.fetchone()[0]
            self.tmdb_id = data[0]
            self.trailer_url = data[1]
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
            self.progress_dialog.update( 90, '%s %s' % ( self.movie_name, _lang( 2 ) ), "", _lang( 13 ) )
            quality_index = 0
            self.format_param = _available_formats[quality_index]
            trailer_id = self.trailer_url.split("watch?v=")[1]

            request = urllib2.Request(_LANG_URL, None, std_headers)
            urllib2.urlopen(request).read()
            
            age_form = {
                            'next_url':		'/',
                            'action_confirm':	'Confirm',
                            }
            request = urllib2.Request(_AGE_URL, urllib.urlencode(age_form), std_headers)
            urllib2.urlopen(request).read()
            trailer_token_url = 'http://www.youtube.com/get_video_info?&video_id=%s&el=detailpage&ps=default&eurl=&gl=US&hl=en' % trailer_id
            url_request = urllib2.Request( trailer_token_url, None, std_headers )
            trailer_token_page = urllib2.urlopen( url_request ).read()
            trailer_token_info = parse_qs( trailer_token_page )
            if 'token' not in trailer_token_info:
                if 'reason' not in trailer_token_info:
                    raise
                else:
                    self.error_message = urllib.unquote_plus(trailer_token_info['reason'][0])
                    raise
            trailer_token = urllib.unquote_plus( trailer_token_info['token'][0] )
            if( trailer_token == '' ):
                raise            
            while True:
                self.full_url = 'http://www.youtube.com/get_video?video_id=%s&t=%s&eurl=&el=detailpage&ps=default&gl=US&hl=en' % ( trailer_id, trailer_token )
                if self.format_param is not None:
                    self.full_url = '%s&fmt=%s' % (self.full_url, self.format_param)
                if 'conn' in trailer_token_info and trailer_token_info['conn'][0].startswith('rtmp'):
                    self.full_url = video_info['conn'][0]
                try:
                    print "trying %s" % self.full_url.encode('utf-8')
                    self.full_url = self.verify_url( self.full_url.encode('utf-8') ).decode('utf-8')
                    #record quality setting and insert into db for fast getting next time :D
                    break
                except:
                    print "invalid format %s" % self.format_param
                    quality_index += 1
                    self.format_param = _available_formats[quality_index]
        except:
            traceback.print_exc()
            self.error_id = 33
            raise

    def verify_url( self, url):
            """Verify a URL is valid and data could be downloaded. Return real data URL."""
            request = urllib2.Request(url, None, std_headers)
            data = urllib2.urlopen(request)
            data.read(1)
            url = data.geturl()
            data.close()
            return url
        
    def playTrailer( self ):
        try:
            self.progress_dialog.update( 100, '%s %s' % ( self.movie_name, _lang( 2 ) ), "", _lang( 14 ) )            
            thumb_image = xbmc.getInfoLabel( 'ListItem.Thumb' )
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
                cursor.execute( "UPDATE trailers SET name=?, tmdb_id=?, trailer_url=?, format=? WHERE id='%s'" % result[0], ( self.movie_name, self.tmdb_id, self.trailer_url, self.format_param ) )
            else:
                cursor.execute('INSERT INTO trailers ( name, imdb_id, tmdb_id, trailer_url , format ) VALUES ( ?, ?, ?, ?, ? );', ( self.movie_name, self.imdb_id, self.tmdb_id, self.trailer_url, self.format_param ) )
            db.commit()
            db.close()
        except:
            print "Failed to add trailer to script Database"
            
Main()
