import os, sys, time, re, math
import xbmc
import xbmcgui
from pysqlite2 import dbapi2 as sqlite
import tmdb, traceback
import urllib, urllib2
from cgi import parse_qs


_lang = xbmc.Language(os.getcwd()).getLocalizedString

DBPATH = xbmc.translatePath( "special://database/MyVideos34.db" )
__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__version__ = sys.modules[ "__main__" ].__version__
__credits__ = sys.modules[ "__main__" ].__credits__

BASE_DATABASE_PATH = os.path.join( xbmc.translatePath( "special://profile/" ), "script_data", __scriptname__, "YouTrailer.db" )
AVAILABLE_FORMATS = ['13','17','5','18','35','22','37']

DB_KEYS = {
    'Title' : 'name',
    'Imdb' : 'imdb_id',
    'Tmdb' : 'tmdb_id',
    'Url' : 'trailer_url',
    'Local' : 'local_trailer'
    }

VALID_URL = r'^((?:http://)?(?:\w+\.)?youtube\.com/(?:(?:v/)|(?:(?:watch(?:\.php)?)?[\?#](?:.+&)?v=)))?([0-9A-Za-z_-]+)(?(1).+)?$'

std_headers = {
	'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
	'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
	'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
	'Accept-Language': 'en-us,en;q=0.5',
}



SETTINGS = sys.modules[ "__main__" ].XBMC_SETTINGS


#User Settings

SLEEP_TIME = 5 #in seconds to check if trailer playing after play command sent
DOWNLOAD_TRAILER = 0  #0 to stream trailers, 1 to download trailers - maybe have pop up when complete to watch, option to add to xbmc db
#Download Trailer not implemented YET

class Main:
    def __init__(self):
        self.log( "Main Started" )
        starttime = time.time()
        self.setupVariables()
        self.buildDatabase()
        self.fetchInfoLabels()
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
           # self.playTrailer()
            self.progress_dialog.close()
            self.downloadTrailer()
##            if( not self.settings['Window'] ):
##                xbmc.executebuiltin('Dialog.Close(MovieInformation)')
##            self.validChecker()
        except:
            traceback.print_exc()
            self.progress_dialog.close()
            self.log( "Script Error: %s" % _lang( self.error_id ) )
            self.dialog.ok( "%s - %s" % ( __scriptname__, _lang( 30 ) ), "", "", _lang( self.error_id ) )
        self.log( "Credits: %s" % __credits__)
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
        self.error_id = 35
        if(SETTINGS.getSetting( "latest" ) == 'true'):
            LatTrailer = 1
        else:
            LatTrailer = 0
        if(SETTINGS.getSetting( "local" ) == 'true'):
            LocTrailer = 1
        else:
            LocTrailer = 0
        if(SETTINGS.getSetting( "xbmct" ) == 'true'):
            XbmcTrailer = 1
        else:
            XbmcTrailer = 0
        if(SETTINGS.getSetting( "window" ) == 'true'):
            window = 1
        else:
            window = 0            
        self.settings = {
                        'STime' : SLEEP_TIME,
                        'MaxQuality': int(SETTINGS.getSetting( "quality" )),
                        'LatTrailer' : LatTrailer,
                        'LocTrailer' : LocTrailer,
                        'XbmcTrailer' :  XbmcTrailer,
                        'Window' :  window,
                        'DTrailer' :  DOWNLOAD_TRAILER
                        }
        self.movie_info = {
                           'Title': '',
                           'Director' : '',
                           'Year' : '',
                           'Genre' : '',
                           'Thumb' : '',
                           'Imdb' : '',
                           'Tmdb' : '',
                           'Url' : '',
                           'Local' : '',
                           'Full' : '',
                           'Tid' : ''
                            }
        print self.settings['LatTrailer']


    def fetchInfoLabels( self ):
        self.movie_info['Title'] = xbmc.getInfoLabel( 'listitem.title' )
        self.movie_info['Director'] = xbmc.getInfoLabel( 'listitem.director' )
        self.movie_info['Year'] = xbmc.getInfoLabel( 'listitem.year' )
        self.movie_info['Genre'] = xbmc.getInfoLabel( 'listitem.genre' )
        self.movie_info['Thumb'] = xbmc.getInfoLabel( 'ListItem.Thumb' )        


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
        if( ( self.fetchLocalUrl() ) and ( self.settings['LocTrailer'] ) ):
            self.log( "Local Trailer Found In XBMC DB: %s" % self.movie_info['Url'] )
        else:
            self.log( "No Local Trailer" )
            if( ( self.fetchTrailerId() ) and ( self.settings['XbmcTrailer'] ) ):
                self.log( "Valid Trailer URL Found In XBMC DB: %s" % self.movie_info['Url'] )
                self.fetchToken()
            else:
                self.log( "No Vaild Trailer URL Found In XBMC DB" )
                self.checkDb()


    def fetchLocalUrl( self ):
        url = self.movie_info['Url']
        if( url == None ):
            self.movie_info['Local'] = ''
            return 0
        if( ( not "http" in url ) and ( xbmc.executehttpapi( 'FileExists(%s)' % url ) == '<li>True' ) ):
            self.movie_info['Local'] = self.movie_info['Full'] = self.movie_info['Url']
            self.movie_info['Url'] = ''
            return 1
        else:
            self.movie_info['Local'] = ''
            return 0


    def fetchTrailerId( self ):
        url = self.movie_info['Url']
        if( url == None ):
            self.movie_info['Tid'] = ''
            return 0
        match = re.match(VALID_URL, url)
        if( match == None ):
            self.movie_info['Tid'] = ''
            return 0
        else:
            result = match.group(2)
            if( result == url ):
                self.movie_info['Tid'] = ''
                return 0
            else:
                self.movie_info['Tid'] = result
                return 1

            
    def checkDb( self ):
        self.log( "Checking YouTrailer DB For Valid Trailer URL" )
        db = sqlite.connect( BASE_DATABASE_PATH )
        cursor = db.cursor()
        cursor.execute( "SELECT tmdb_id, trailer_url, local_trailer FROM trailers WHERE imdb_id = ?;" , ( self.movie_info['Imdb'], ) )
        result = cursor.fetchone()
        db.close()
        if( result == None ):
            self.log( "No Entry Found In YouTrailer DB" )
            self.fetchUrl()
        else:
            self.movie_info['Tmdb'] = result[0]
            self.movie_info['Url'] = result[1]
            self.movie_info['Local'] = result[2]
            if( ( self.fetchLocalUrl() ) and ( self.settings['LocTrailer'] ) ):
                self.log( "Local Trailer Found In YouTrailer DB: %s" % self.movie_info['Url'] )
            else:
                if( ( self.fetchTrailerId () ) and ( not self.settings['LatTrailer'] ) ):
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
        if( self.fetchTrailerId () ):
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

    def downloadTrailer( self ):
        try:
            self.log( "Downloading Trailer: %s" % self.movie_info['Full'] )
            self.progress_dialog.create( __scriptname__, '' )
            print "downloading %s" % self.movie_info['Full']
            stream = None
            open_mode = 'wb'
            basic_request = urllib2.Request( self.movie_info['Full'], None, std_headers)
            request = urllib2.Request( self.movie_info['Full'], None, std_headers)
            filename = os.path.join( os.getcwd(), "trailer.flv" )
            print filename
    ##	if os.path.isfile(filename):
    ##            resume_len = os.path.getsize(filename)
    ##	else:
    ##	    resume_len = 0	
            data = urllib2.urlopen(request)
            data_len = data.info().get('Content-length', None)
            data_len_str = self.format_bytes(data_len)
            byte_counter = 0
            block_size = 1024
            start = time.time()
            while True:
                    # Download and write
                    before = time.time()
                    data_block = data.read(block_size)
                    after = time.time()
                    data_block_len = len(data_block)
                    if data_block_len == 0:
                            break
                    byte_counter += data_block_len

                    # Open file just in time
                    if stream is None:
                            try:
                                    stream = open(filename, open_mode)
                                #    self.report_destination(filename)
                            except (OSError, IOError), err:
                                 #   self.trouble('ERROR: unable to open for writing: %s' % str(err))
                                    return False
                    stream.write(data_block)
                    block_size = self.best_block_size(after - before, data_block_len)

                    # Progress message
                 #   percent_str = self.calc_percent(byte_counter, data_len)
                    eta_str = self.calc_eta(start, time.time(), data_len, byte_counter)
                    speed_str = self.calc_speed(start, time.time(), byte_counter)
                    self.progress_dialog.update( (float(byte_counter) / float(data_len) * 100.0), '%s %s' % ( self.movie_info['Title'], _lang( 2 ) ), "Speed:%s Eta:%s" % (speed_str, eta_str), _lang( 16 ) )
    
    ##                self.report_progress(percent_str, data_len_str, speed_str, eta_str)

                    # Apply rate limit
                #    self.slow_down(start, byte_counter)
        except:
            traceback.print_exc()


    def calc_eta( self, start, now, total, current):
            if total is None:
                    return '--:--'
            dif = now - start
            if current == 0 or dif < 0.001: # One millisecond
                    return '--:--'
            rate = float(current) / dif
            eta = long((float(total) - float(current)) / rate)
            (eta_mins, eta_secs) = divmod(eta, 60)
            if eta_mins > 99:
                    return '--:--'
            return '%02d:%02d' % (eta_mins, eta_secs)

    def calc_speed(self, start, now, bytes):
            dif = now - start
            if bytes == 0 or dif < 0.001: # One millisecond
                    return '%10s' % '---b/s'
            return '%10s' % ('%s/s' % self.format_bytes(float(bytes) / dif))


##    def calc_percent(self, byte_counter, data_len):
##            if data_len is None:
##                    return 0
##            return '%6s' % ('%3.1f' % (float(byte_counter) / float(data_len) * 100.0))

    def slow_down(self, start_time, byte_counter):
            """Sleep if the download speed is over the rate limit."""
            rate_limit = self.params.get('ratelimit', None)
            if rate_limit is None or byte_counter == 0:
                    return
            now = time.time()
            elapsed = now - start_time
            if elapsed <= 0.0:
                    return
            speed = float(byte_counter) / elapsed
            if speed > rate_limit:
                    time.sleep((byte_counter - rate_limit * (now - start_time)) / rate_limit)


    def format_bytes(self, bytes):
            if bytes is None:
                    return 'N/A'
            if type(bytes) is str:
                    bytes = float(bytes)
            if bytes == 0.0:
                    exponent = 0
            else:
                    exponent = long(math.log(bytes, 1024.0))
            suffix = 'bkMGTPEZY'[exponent]
            converted = float(bytes) / float(1024**exponent)
            return '%.2f%s' % (converted, suffix)

    def best_block_size(self, elapsed_time, bytes):
            new_min = max(bytes / 2.0, 1.0)
            new_max = min(max(bytes * 2.0, 1.0), 4194304) # Do not surpass 4 MB
            if elapsed_time < 0.001:
                    return long(new_max)
            rate = bytes / elapsed_time
            if rate > new_max:
                    return long(new_max)
            if rate < new_min:
                    return long(new_min)
            return long(rate)

        
    def playTrailer( self ):
        self.log( "Playing Trailer: %s" % self.movie_info['Full'] )
        self.error_id = 34
        try:
            self.progress_dialog.update( 100, '%s %s' % ( self.movie_info['Title'], _lang( 2 ) ), "", _lang( 14 ) )            
            listitem = xbmcgui.ListItem( self.movie_info['Title'], thumbnailImage = self.movie_info['Thumb'] )
            listitem.setInfo( 'video', {'Title': '%s %s' % ( self.movie_info['Title'], _lang( 2 ) ), 'Studio' : __scriptname__, 'Genre' : self.movie_info['Genre'] } )
            self.player.play( self.movie_info['Full'], listitem, self.settings['Window'] )
        except:
            self.log( "ERROR Playing Trailer: %s" % self.movie_info['Full'] )
            raise


    def validChecker( self ):
        self.log( "Valid Trailer Playing Loop Started For %s Seconds" % SLEEP_TIME )
        for i in range(0, (  self.settings['STime'] * 2 ) ):
            if( self.player.isPlayingVideo() ):
                if ( self.player.getPlayingFile() == self.movie_info['Full'] ):
                    self.log( "Playing File is same as Trailer Url AKA VALID TRAILER!" )
                    self.addDb()
                    break
            time.sleep( 0.5 )
            
    def getFormat( self ):
        self.log( "Fetching Valid Trailer Quality" )
        try_quality = self.settings['MaxQuality']
        while True:
            try_url = '%s&fmt=%s' % ( self.movie_info['Full'], AVAILABLE_FORMATS[try_quality] )
            self.log( "Trying Quality: %s" % AVAILABLE_FORMATS[try_quality] )
            try:
                    self.movie_info['Full'] = self.verify_url( try_url.encode( 'utf-8' ) ).decode( 'utf-8' )
                    break
            except:
                    try_quality -= 1
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
