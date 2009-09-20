"""
Url retrieve and cache module

Killarny
"""

import sys
import os
import xbmc
import xbmcgui
import urllib2
import md5
import time
#import socket
#socket.setdefaulttimeout( 20 )

#from keepalive import HTTPHandler
#keepalive_handler = HTTPHandler()
#opener = urllib2.build_opener( keepalive_handler )
#urllib2.install_opener( opener )

from utilities import *


__module_name__ = "cacheurl"
__module_version__ = "0.1"
#__useragent__ = "iTunes/4.7"
__useragent__ = "QuickTime/7.2 (qtver=7.2;os=Windows NT 5.1Service Pack 3)"

_ = sys.modules[ "__main__" ].__language__


def percent_from_ratio( top, bottom ):
    return int( float( top ) / bottom * 100 )

def byte_measurement( bytes, detailed = False ):
    """
        convert integer bytes into a friendly string with B/kB/MB
    """
    B = bytes
    MB = int( float( B ) / 1024 / 1024 )
    B = B - MB * 1024 * 1024
    kB = int( float( B ) / 1024 )
    B = B - kB * 1024
    if detailed:
        if MB:
            result += str( MB )
            if kB or B:
                result += "."
            if kB:
                result += str( percent_from_ratio( kB, 1024 ) )
            if B:
                result += str( percent_from_ratio( B, 1024 ) )
            result += "MB"
        elif kB:
            result += str( kB )
            if B:
                result += ".%i" % percent_from_ratio( B, 1024 )
            result += "kB"
        elif B:
            result += "%ib" % B
    else:
        if MB:
            result = "%iMB" % MB
        elif kB:
            result = "%ikB" % kB
        else:
            result = "%ib" % B
    return result

def rate_remaining( current_time_elapsed, size_read_so_far, filesize ):
    """
        calculates download rate and time remaining
    """
    total_time = int( current_time_elapsed / ( float( size_read_so_far ) / filesize ) - current_time_elapsed )
    minutes = int( float( total_time ) / 60 )
    seconds = total_time - ( minutes * 60 )
    download_rate = "%d %s" % ( int( float( size_read_so_far ) / 1024 / current_time_elapsed ), _( 80 ) )
    download_time_remaining = "%s: %02d:%02d" % ( _( 91 ), minutes, seconds, )
    return download_rate, download_time_remaining

def set_status_symbol( status_symbol ):
    status_symbol_index = [ "-", "\\", "|", "/" ].index( status_symbol ) + 1
    if ( status_symbol_index >= 4 ):
        status_symbol_index = 0
    return [ "-", "\\", "|", "/" ][ status_symbol_index ]

class HTTP:
    def __init__( self, cache = ".cache", title = "", actual_filename = False, flat_cache = False, clear_cache_folder=False ):
        # set the cache directory; default to a .cache directory in BASE_DATA_PATH
        self.cache_dir = cache
        if self.cache_dir.startswith( "." ):
            self.cache_dir = os.path.join( BASE_DATA_PATH, self.cache_dir )

        # title is the real name of the trailer, used for saving
        self.title = title
        
        # flat_cache means that each request will be cached to a special folder; basically a non-persistent cache
        self.flat_cache = flat_cache
        self.clear_cache_folder = clear_cache_folder

        # normally, an md5 hexdigest will be used to determine a unique filename for each request, but with actual_filename set to True, the real filename will be used
        # this can result in overwriting previously cached results if not used carefully
        self.actual_filename = actual_filename

        # set default blocksize (this may require tweaking; cachedhttp1.3 had it set at 8192)
        self.blocksize = 4096#16384#8192

    def clear_cache( self, cache_dir=None ):
        try:
            if cache_dir is None:
                cache_dir = self.cache_dir
            for root, dirs, files in os.walk( cache_dir, topdown = False ):
                for name in files:
                    os.remove( os.path.join( root, name ) )
                os.rmdir( root )
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "%s.%s [%s]", __module_name__, __module_version__, sys.exc_info()[ 1 ] )

    def urlopen( self, url ):
        # retrieve the file so it is cached
        filepath = self.urlretrieve( url )
        # read the data out of the file
        data = ""
        if filepath:
            filehandle = open( filepath, "rb" )
            data = filehandle.read()
        return data

    def make_cache_filename( self, url ):
        # construct the filename
        if self.actual_filename:
            filename = self.title
            if self.flat_cache:
                filename = os.path.join( "flat_cache", filename )
        else:
            filename = md5.new( url ).hexdigest() + os.path.splitext( url )[ 1 ]
            filename = os.path.join( filename[ 0 ], filename )

        # make the filepath legal
        filepath = make_legal_filepath( os.path.join( self.cache_dir, filename ), conf=self.actual_filename )
        return filepath

    def urlretrieve( self, url ):
        self.info = {}
        # get the filename
        filepath = self.make_cache_filename( url )

        # if the file is already in the cache, return that filename
        if os.path.isfile( filepath ):
            # notify handler of being finished
            self.on_finished( url, filepath, os.path.getsize( filepath ), True )
            return filepath
        
        # if self.flat_cache delete existing flat_cache folder since this is a new movie
        if self.flat_cache and self.clear_cache_folder:
            self.clear_cache( os.path.join( self.cache_dir, "flat_cache" ) )

        try:
            request = urllib2.Request( url )
            request.add_header( "User-Agent", __useragent__ )
            # hacky, I know, but the chances that the url will fail twice are slimmer than only trying once
            #try:
            opened = urllib2.urlopen( request )
            #except:
            #    opened = urllib2.urlopen( request )
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "%s.%s [%s]", __module_name__, __module_version__, sys.exc_info()[ 1 ] )
            self.on_finished( url, "", 0, False )
            return None

        # this is the actual url that we got (redirection, etc)
        actual_url = opened.geturl()
        # info dict about the file (headers and such)
        self.info = opened.info()

        # get the filename
        if actual_url != url:
            filepath = self.make_cache_filename( actual_url )
        
        # save the total expected size of the file, based on the Content-Length header
        totalsize = int( self.info[ "Content-Length" ] )
        try:
            is_completed = os.path.getsize( filepath ) == totalsize
        except:
            is_completed = False

        # if the file is already in the cache, return that filename
        if os.path.isfile( filepath ) and is_completed:
            # notify handler of being finished
            self.on_finished( actual_url, filepath, totalsize, is_completed )
            return filepath

        # check if enough disk space exists to store the file
        try:
            drive = os.path.splitdrive( self.cache_dir )[ 0 ].split( ":" )[ 0 ]
            free_space = xbmc.getInfoLabel( "System.Freespace(%s)" % drive )
            if len( free_space.split() ) > 2:
                free_space_mb = int( free_space.split()[ 1 ] )
                free_space_b = free_space_mb * 1024 * 1024
                if totalsize >= free_space_b:
                    header = _( 64 ) # Error
                    line1 = _( 75 ) # Not enough free space in target drive.
                    line2_drive = _( 76 ) # Drive
                    line2_free = _( 77 ) # Free
                    line2_space_required = _( 78 ) # Space Required
                    xbmcgui.Dialog().ok( header, line1, line2_drive + ": %s %iMB " + line2_free % ( drive, free_space_mb ), line2_space_required + ": " + byte_measurement( totalsize ) )
                    # notify handler of being finished
                    self.on_finished( actual_url, filepath, totalsize, is_completed )
                    return None
        except:
            LOG( LOG_ERROR, self.__class__.__name__, "%s.%s [%s]", __module_name__, __module_version__, sys.exc_info()[ 1 ] )
            self.on_finished( url, "", 0, False )
            return None
            
        # create the cache dir if it doesn't exist
        if not os.path.isdir( os.path.split( filepath )[ 0 ] ):#self.cache_dir ):
            os.makedirs( os.path.split( filepath )[ 0 ] )#self.cache_dir )

        # write the data to the cache
        try:
            filehandle = open( filepath, "wb" )
            filedata = "..."
            size_read_so_far = 0
            do_continue = True
            while len( filedata ):
                try:
                    filedata = opened.read( self.blocksize )
                    if len( filedata ):
                        filehandle.write( filedata )
                        size_read_so_far += len( filedata )
                        do_continue = self.on_data( actual_url, filepath, totalsize, size_read_so_far )
                    if len( filedata ) < self.blocksize:
                        break
                    if not do_continue:
                        break
                except ( OSError, IOError ), ( errno, strerror ):
                    # Error
                    xbmcgui.Dialog().ok( _(64), "[%i] %s" % ( errno, strerror ) )
                    break
                except:
                    LOG( LOG_ERROR, self.__class__.__name__, "%s.%s [%s]", __module_name__, __module_version__, sys.exc_info()[ 1 ] )
                    break
            filehandle.close()
        except:
            raise

        try:
            is_completed = os.path.getsize( filepath ) == totalsize
        except:
            is_completed = False

        # notify handler of being finished
        self.on_finished( actual_url, filepath, totalsize, is_completed )

        # if the file transfer was halted before completing, remove the partial file from cache
        if not is_completed:
            os.remove( filepath )
            filepath = None
        return filepath

    def on_data( self, url, filepath, filesize, size_read_so_far ):
        return True

    def on_finished( self, url, filepath, filesize, is_completed ):
        pass


class HTTPProgress( HTTP ):
    def __init__( self, cache = ".cache", title = "", actual_filename = False, flat_cache = False, clear_cache_folder = False ):
        HTTP.__init__( self, cache, title, actual_filename, flat_cache, clear_cache_folder )
        self.dialog = xbmcgui.DialogProgress()
        self.status_symbol = "-"
        self.download_start_time = time.time()

    def urlretrieve( self, url ):
        # Downloading...
        self.dialog.create( _( 79 ), url.split( "/" )[ -1 ] )
        self.dialog.update( 0 )
        return HTTP.urlretrieve( self, url )

    def on_data( self, url, filepath, filesize, size_read_so_far ):
        current_time_elapsed = time.time() - self.download_start_time
        so_far = byte_measurement( size_read_so_far )
        fsize = byte_measurement( filesize )
        percentage = percent_from_ratio( size_read_so_far, filesize )
        self.status_symbol = set_status_symbol( self.status_symbol )
        download_rate, download_time_remaining = rate_remaining( current_time_elapsed, size_read_so_far, filesize )
        self.dialog.update( percentage, url.split( "/" )[ -1 ], "%i%% (%s/%s) %s %s" % ( percentage, so_far, fsize, download_rate, self.status_symbol ), download_time_remaining )
        if self.dialog.iscanceled():
            return False
        return True

    def on_finished( self, url, filepath, filesize, is_completed ):
        self.dialog.close()

class HTTPProgressSave( HTTPProgress ):
    def __init__( self, save_location = ".cache", save_title = "", clear_cache_folder = False ):
        # if filepath is a samba share, save to the flat_cache directory, then copy it to the samba share
        self.save_location = save_location
        if ( save_location.startswith( "smb://" ) or save_location == ".cache" ):
            flat_cache = True
            save_location = ".cache"
        else:
            flat_cache = False
        HTTPProgress.__init__( self, save_location, save_title, True, flat_cache, clear_cache_folder )

    def urlretrieve( self, url ):
        filepath = HTTPProgress.urlretrieve( self, url )
        if filepath is not None:
            filepath = self.filepath
        return filepath

    def on_finished( self, url, filepath, filesize, is_completed ):
        self.filepath = filepath
        if is_completed and os.path.splitext( filepath )[ 1 ] in [ ".mov", ".avi" ]:
            try:
                # create conf file for better MPlayer playback
                if ( not os.path.isfile( filepath + ".conf" ) ):
                    f = open( filepath + ".conf" , "w" )
                    f.write( "nocache=1" )
                    f.close()
                # if save location is a samba share, copy the file
                if ( self.save_location.startswith( "smb://" ) ):
                    self.dialog.update( -1, _( 56 ), _( 67 ), "" )
                    self.filepath = os.path.join( self.save_location, os.path.basename( filepath ) )
                    xbmc.executehttpapi("FileCopy(%s,%s)" % ( filepath, self.filepath, ) )
                    #xbmc.executehttpapi("FileCopy(%s.conf,%s.conf)" % ( filepath, self.filepath, ) )
            except:
                LOG( LOG_ERROR, self.__class__.__name__, "%s.%s [%s]", __module_name__, __module_version__, sys.exc_info()[ 1 ] )
        HTTPProgress.on_finished( self, url, self.filepath, filesize, is_completed )
