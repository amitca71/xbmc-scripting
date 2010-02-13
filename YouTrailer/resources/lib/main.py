import os, sys, time, re
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
__version__ = sys.modules[ "__main__" ].__version__

BASE_DATABASE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "script_data", __scriptname__, "YouTrailer.db" )
AVAILABLE_FORMATS = ['37', '22', '35', '18', '5', '17', '13']

VALID_URL = r'^((?:http://)?(?:\w+\.)?youtube\.com/(?:(?:v/)|(?:(?:watch(?:\.php)?)?[\?#](?:.+&)?v=)))?([0-9A-Za-z_-]+)(?(1).+)?$'

SLEEP_TIME = 5 #secs

std_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
	'Accept-Language': 'en-us,en;q=0.5',
}

QUALITY = 0  #0 = 1080p, 1 = 720p, 2 = 1227kbs, 3 = 480p, 4 = flv 295kb/s, 5 = mpeg4 176x144, 6 = h263 176x144


DB_KEYS = {'Title' : 'name', 'Imdb' : 'imdb_id', 'Tmdb' : 'tmdb_id', 'Url' : 'trailer_url', 'Local' : 'local_trailer'}

class Main:
    def __init__(self):
        self.log( "Main Started" )
        starttime = time.time()
        self.setupVariables()
        self.buildDatabase()
        self.movie_info['Title'] = xbmc.getInfoLabel( 'listitem.title' )
        self.movie_info['Director'] = xbmc.getInfoLabel( 'listitem.director' )
        self.movie_info['Year'] = xbmc.getInfoLabel( 'listitem.year' )
        self.movie_info['Genre'] = xbmc.getInfoLabel( 'listitem.genre' )
        self.movie_info['Thumb'] = xbmc.getInfoLabel( 'ListItem.Thumb' )
        self.log( "Movie Name: %s" % self.movie_info['Title'] )
        self.log( "Movie Director: %s" % self.movie_info['Director'] )
        self.log( "Movie Year: %s" % self.movie_info['Year'] )
        self.log( "Movie Genre: %s" % self.movie_info['Genre'] )
        self.main()
        while( time.time() - starttime < 5 ):
            time.sleep( 0.5 )


    def log( self, string ):
        xbmc.log( "[SCRIPT] '%s: version %s' %s" % ( __scriptname__, __version__, string ), xbmc.LOGNOTICE )
        return string


    def main( self ):
        try:
            self.progress_dialog.create( __scriptname__, '' )
            self.fetchXbmcData()
            self.getTrailer()
            self.playTrailer()
            self.progress_dialog.close()
            xbmc.executebuiltin('Dialog.Close(MovieInformation)')
            self.validChecker()
            self.log( "Script Complete Success!" )
        except:
            traceback.print_exc()
            self.progress_dialog.close()
            self.log( "Script Error: %s" % _lang( self.error_id ) )
            self.dialog.ok( "%s - %s" % ( __scriptname__, _lang( 30 ) ), "", "", _lang( self.error_id ) )
            self.log( "Script Complete" )


    def buildDatabase( self ):
        self.log( "Building Trailer Database" )
        if ( not os.path.isdir( os.path.dirname( BASE_DATABASE_PATH ) ) ):
            os.makedirs( os.path.dirname( BASE_DATABASE_PATH ) )
        db = sqlite.connect( BASE_DATABASE_PATH )
        cursor = db.cursor()
        cursor.execute('CREATE TABLE IF NOT EXISTS trailers (id INTEGER PRIMARY KEY, name VARCHAR(100), imdb_id VARACHAR(25), tmdb_id VARACHAR(25), trailer_url VARACHAR(100), local_trailer VARCHAR(200));')
        db.commit()
        db.close()

        
    def setupVariables( self ):
        self.log( "Setting Up Variables" )
        self.tmdb_api = tmdb.MovieDb()
        self.player = xbmc.Player()
        self.progress_dialog = xbmcgui.DialogProgress()
        self.dialog = xbmcgui.Dialog()
        self.movie_info = {'Title': '', 'Director' : '', 'Year' : '', 'Genre' : '', 'Thumb' : '', 'Imdb' : '', 'Tmdb' : '', 'Url' : '', 'Local' : '', 'Full' : '', 'Tid' : ''}
        self.error_id = 35


    def fetchXbmcData( self ):
        self.error_id = 31 #Failed To Retrieve XBMC DB Movie Info
        try:
            self.log( "Fetching XBMC Data" )
            db = sqlite.connect( DBPATH )
            cursor = db.cursor()
            cursor.execute( "SELECT c09, c19 FROM movie WHERE c00 = ? AND c07 = ? AND c15 = ?;", ( self.movie_info['Title'], self.movie_info['Year'], self.movie_info['Director'] ) )
            xbmc_data = cursor.fetchone()
            self.movie_info['Imdb'] = xbmc_data[0].strip()
            self.movie_info['Url'] = xbmc_data[1].strip()
            if( self.movie_info['Imdb'] == '' or self.movie_info['Imdb'] == None ):
                raise
            db.close()
        except:
            self.log( "ERROR Fetching XBMC Data" )
            raise


    def getTrailer( self ):
        self.log( "Checking XBMC DB For Local Trailer or Valid Trailer Url" )
        if( self.checkLocalUrl( self.movie_info['Url'] ) ):
            self.log( "Local Trailer Found: %s" % self.movie_info['Url'] )
            self.movie_info['Local'] = self.movie_info['Full'] = self.movie_info['Url']
            self.movie_info['Url'] = ''
        else:
            self.log( "No Local Trailer" )
            if( self.checkValidUrl( self.movie_info['Url'] ) ):
                self.log( "Valid Trailer URL Found In XBMC DB: %s" % self.movie_info['Url'] )
                self.fetchToken()
            else:
                self.log( "No Vaild Trailer URL Found In XBMC DB" )
                self.checkDb()

    def checkLocalUrl( self, url ):
        if( url == None ):
            return 0
        if( ( not "http" in url ) and ( xbmc.executehttpapi( 'FileExists(%s)' % url ) == '<li>True' ) ):
            return 1
        else:
            return 0

    def checkValidUrl( self, url ):
        if( url == None ):
            return 0
        match = re.match(VALID_URL, url)
        if( match == None ):
            return 0
        else:
            self.movie_info['Tid'] = match.group(2)
            if( self.movie_info['Tid'] == url ):
                return 0
            else:
                return 1
            
    def checkDb( self ):
        self.log( "Checking YouTrailer DB For Valid Trailer URL" )
        db = sqlite.connect( BASE_DATABASE_PATH )
        cursor = db.cursor()
        cursor.execute( "SELECT tmdb_id, trailer_url, local_trailer FROM trailers WHERE imdb_id = ?;" , ( self.movie_info['Imdb'], ) )
        result = cursor.fetchone()
        if( result == None ):
            self.log( "No Entry Found In YouTrailer DB" )
            self.fetchUrl()
        else:
            self.movie_info['Tmdb'] = result[0]
            self.movie_info['Url'] = result[1]
            self.movie_info['Local'] = result[2]
            if( not self.checkLocalUrl( self.movie_info['Local'] ) ):
                if( self.checkValidUrl ( self.movie_info['Url'] ) ):
                    self.log( "Valid Trailer URL Found In YouTrailer DB: %s" % self.movie_info['Url'] )
                    self.fetchToken()
                else:
                    self.log( "No Valid Trailer URL Found In YouTrailer DB" )
                    self.fetchUrl()
                

    def fetchUrl( self ):
        self.error_id = 32
        self.log( "Fetching Trailer URL From TMDB" )
        if( self.movie_info['Tmdb'] == '' or self.movie_info['Tmdb'] == None ):
            self.progress_dialog.update( 0, '%s %s' % ( self.movie_info['Title'], _lang( 2 ) ), "", _lang( 10 ) )
            try:
                api_results = self.tmdb_api.searchimdb( self.movie_info['Imdb'] )
            except:
                self.log( "TMDB API ERROR" )
                raise
            if( ( len( api_results ) < 1 ) or ( not 'id' in api_results[0] ) or ( api_results[0]['id'] == '' ) ):
                self.log( "No TMDB ID Could Be Fetched From TMDB" )
                raise
            self.movie_info['Tmdb'] = api_results[0]['id']
        self.progress_dialog.update( 60, '%s %s' % ( self.movie_info['Title'], _lang( 2 ) ), "", _lang( 11 ) )
        try:
            api_results = self.tmdb_api.getinfo( self.movie_info['Tmdb'] )
        except:
            self.log( "TMDB API ERROR" )
            raise          
        if( ( len( api_results ) < 1 ) or ( not 'trailer' in api_results[0] ) or ( api_results[0]['trailer'] == '' ) ):
            self.log( "No Trailer Could Be Fetched From TMDB" )
            raise
        self.movie_info['Url'] = api_results[0]['trailer']
        self.movie_info['Imdb'] = api_results[0]['imdb_id']
        if( self.checkValidUrl ( self.movie_info['Url'] ) ):
            self.log( "Valid Trailer URL Fetched From TMDB: %s" % self.movie_info['Url'] )
            self.fetchToken()
        else:
            self.log( "No Valid Trailer URL Fetched From TMDB" )
            raise

    def fetchToken( self ):
        self.error_id = 33 # Trailer Not Available
        self.log( "Fetching Trailer Token. Trailer ID: %s" % self.movie_info['Tid'] )
        self.progress_dialog.update( 90, '%s %s' % ( self.movie_info['Title'], _lang( 2 ) ), "", _lang( 13 ) )
        trailer_info_url = 'http://www.youtube.com/get_video_info?&video_id=%s&el=detailpage&ps=default&eurl=&gl=US&hl=en' % self.movie_info['Tid']
        self.log( "Trailer Info Url: %s" % trailer_info_url )
        url_request = urllib2.Request( trailer_info_url, None, std_headers )
        try:
            trailer_info_page = urllib2.urlopen( url_request ).read()
            trailer_info = parse_qs( trailer_info_page )
        except:
            self.log( "Failed opening trailer info page" )
            raise
        if 'token' not in trailer_info:
            if 'reason' not in trailer_info:
                self.log( "Failed Fetching Token: Unknown Reason" )
            else:
                reason = urllib.unquote_plus( trailer_info['reason'][0] )
                self.log( "Failed Fetching Token: %s" % reason.decode( 'utf-8' ) )
            raise
        trailer_token = urllib.unquote_plus( trailer_info['token'][0] )
        if( trailer_token == '' ):
            raise
        self.movie_info['Full'] = 'http://www.youtube.com/get_video?video_id=%s&t=%s&eurl=&el=detailpage&ps=default&gl=US&hl=en' % ( self.movie_info['Tid'], trailer_token )
        self.getFormat()
        if 'conn' in trailer_info and trailer_info['conn'][0].startswith('rtmp'):
            self.movie_info['Full'] = trailer_info['conn'][0]
        self.log( "Trailer Real URL Obtained: %s" % self.movie_info['Full'] )

        
    def playTrailer( self ):
        self.log( "Playing Trailer: %s" % self.movie_info['Full'] )
        self.error_id = 34
        try:
            self.progress_dialog.update( 100, '%s %s' % ( self.movie_info['Title'], _lang( 2 ) ), "", _lang( 14 ) )            
            listitem = xbmcgui.ListItem( self.movie_info['Title'], thumbnailImage = self.movie_info['Thumb'] )
            listitem.setInfo( 'video', {'Title': '%s %s' % ( self.movie_info['Title'], _lang( 2 ) ), 'Studio' : __scriptname__, 'Genre' : self.movie_info['Genre'] } )
            self.player.play( self.movie_info['Full'], listitem )
        except:
            self.log( "ERROR Playing Trailer: %s" % self.movie_info['Full'] )
            raise


    def validChecker( self ):
        self.log( "Valid Trailer Playing Loop Started For %s Seconds" % SLEEP_TIME )
        for i in range(0, ( SLEEP_TIME * 2 ) ):
            if( self.player.isPlayingVideo() ):
                if ( self.player.getPlayingFile() == self.movie_info['Full'] ):
                    self.log( "Playing File = Trailer Url: VALID TRAILER!" )
                    self.addDb()
                    break
            time.sleep( 0.5 )
            
    def getFormat( self ):
        self.log( "Fetching Valid Format" )
        try_quality = QUALITY
        while True:
            try_url = '%s&fmt=%s' % ( self.movie_info['Full'], AVAILABLE_FORMATS[try_quality] )   # to do quality
            self.log( "Trying Quality: %s" % AVAILABLE_FORMATS[try_quality] )
            try:
                    self.movie_info['Full'] = self.verify_url( try_url.encode( 'utf-8' ) ).decode( 'utf-8' )
                    break
            except:
                    try_quality += 1
        self.log( "Quality Found: %s" % AVAILABLE_FORMATS[try_quality] )

    def verify_url( self, url ):
        request = urllib2.Request(url, None, std_headers)
        data = urllib2.urlopen(request)
        data.read(1)
        url = data.geturl()
        data.close()
        return url

    def addDb( self ):
        try:
            db = sqlite.connect( BASE_DATABASE_PATH )
            cursor = db.cursor()
            cursor.execute( "SELECT id FROM trailers WHERE imdb_id = ?;" , ( self.movie_info['Imdb'], ) )
            result = cursor.fetchone()
            if( result != None ):
                self.log( "Updating Entry In YouTrailer DB" )
                params = []
                sql = "UPDATE trailers SET "
                for key in self.movie_info:
                    if( key in DB_KEYS ):
                        dbkey = DB_KEYS[key]
                        value = self.movie_info[key]
                        if( value != '' ):
                            sql += "%s=?, " % dbkey
                            params.append(value)
                sql = sql[:-2] + " WHERE id=%s;" % result[0]
                cursor.execute( sql, params )
            else:
                self.log( "Adding Entry Into YouTrailer DB" )
                cursor.execute('INSERT INTO trailers ( name, imdb_id, tmdb_id, trailer_url, local_trailer ) VALUES ( ?, ?, ?, ?, ? );', ( self.movie_info['Title'], self.movie_info['Imdb'], self.movie_info['Tmdb'], self.movie_info['Url'], self.movie_info['Local'] ) )
            db.commit()
            db.close()
        except:
            traceback.print_exc()
            self.log( "ERROR Playing Trailer: %s" % self.movie_info['Full'] )
            
Main()
