"""
Database module

Nuka1195
"""

import sys
import os
import xbmc
import xbmcgui
from pysqlite2 import dbapi2 as sqlite
#import traceback

from utilities import *

_ = sys.modules[ "__main__" ].__language__
__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__version__ = sys.modules[ "__main__" ].__version__


class Database:
    """ Main database class """
    def __init__( self, *args, **kwargs ):
        self.query = Query()
        self.db_version, self.complete = self._get_version()
        if ( not self.db_version ):
            LOG( LOG_ERROR, "%s (ver: %s) Incompatible database!", __scriptname__, __version__, )
            raise

    def _get_version( self ):
        records = Records()
        record = records.fetch( self.query[ "version" ] )
        records.close()
        if ( record is not None ):
            idVersion, version, complete = record
            if ( version not in DATABASE_VERSIONS ): 
                version, complete = self._convert_database( version, complete )
        else: version, complete = self._create_database()
        return version, complete
    
    def _create_database( self ):
        def _create_tables():
            dialog = xbmcgui.DialogProgress()
            def _progress_dialog( count=0 ):
                if ( not count ):
                    dialog.create( _( 44 ) )
                elif ( count > 0 ):
                    percent = int( count * ( float( 100 ) / len( records.tables.keys() ) ) )
                    __line1__ = "%s: %s" % ( _( 47 ), table, )
                    dialog.update( percent, __line1__ )
                    if ( dialog.iscanceled() ): return False
                    else: return True
                else:
                    dialog.close()

            def _write_version():
                return records.add( "version", ( __version__, False, ), True )

            def _create_table( table ):
                try:
                    sql = "CREATE TABLE %s (" % table
                    for item in records.tables[ table ]:
                        sql += "%s %s %s, " % ( item[ 0 ], item[ 1 ], item[ 2 ])
                    sql = sql[ : -2 ].strip() + ");"
                    records.db.execute( sql )
                    for item in records.tables[ table ]:
                        if ( item[ 3 ] != "" ):
                            sql = "CREATE %s %s_%s_idx ON %s %s;" % ( item[ 3 ], table, item[0], table, item[4], )
                            records.db.execute( sql )
                    return True
                except: 
                    return False
            
            try:
                _progress_dialog()
                records = Records()
                for count, table in enumerate( records.tables.keys() ):
                    ok = _progress_dialog( count + 1 )
                    ok = _create_table( table )
                    if ( not ok ): raise
                ok = records.commit()
                ok = _write_version()
                records.close()
                _progress_dialog( -1 )
                if ( ok ): return __version__
                else: raise
            except:
                records.close()
                _progress_dialog( -1 )
                xbmcgui.Dialog().ok( _( 44 ), _( 89 ) )
                return False
        
        version = _create_tables()
        return version, False

    def _convert_database( self, version, complete ):
        dialog = xbmcgui.DialogProgress()
        def _progress_dialog( count=0, total_count=None, movie=None ):
            __line1__ = _( 63 )
            if ( not count ):
                dialog.create( _( 59 ), __line1__ )
            elif ( count > 0 ):
                percent = int( count * ( float( 100 ) / total_count ) )
                __line2__ = "%s: (%d of %d)" % ( _( 88 ), count, total_count, )
                __line3__ = movie[ 1 ]
                dialog.update( percent, __line1__, __line2__, __line3__ )
                if ( dialog.iscanceled() ): return False
                else: return True
            else:
                dialog.close()

        def _update_table():
            try:
                sql = "ALTER TABLE genres ADD updated text"
                records = Records()
                records.cursor.execute( sql )
                records.close()
                return True
            except: return False

        def _update_records_poster():
            try:
                sql = "SELECT idMovie, title, poster, rating_url FROM movies ORDER BY title;"
                records = Records()
                movies = records.fetch( sql, all=True )
                total_count = len( movies )
                for count, movie in enumerate( movies ):
                    ok = _progress_dialog( count + 1, total_count, movie )
                    if ( movie[ 2 ] ): poster = os.path.basename( movie[ 2 ] )
                    else: poster = ""
                    if ( movie[ 3 ] ): rating_url = os.path.basename( movie[ 3 ] )
                    else: rating_url = ""
                    ok = records.update( "movies", ( "poster", "rating_url", ), ( poster, rating_url, movie[ 0 ], ), "idMovie" )
                    if ( not ok ): raise
                    if ( ( float( count + 1) / 100 == int( ( count + 1 ) / 100) ) or ( ( count + 1 ) == total_count ) ):
                        ok = records.commit()
                records.close()
                return True
            except:
                records.close()
                return False

        def _update_completed():
            sql = "SELECT idMovie, trailer_urls FROM movies WHERE trailer_urls IS NULL ORDER BY title;"
            records = Records()
            movies = records.fetch( sql, all=True )
            ok = True
            updated = False
            if ( movies is not None ):
                ok = records.update( "version", ( "complete", ), ( 0, 1, ), "idVersion", True )
                if ( ok ): updated = True
            records.close()
            return ok, updated

        def _update_records():
            try:
                sql = "SELECT idMovie, title, trailer_urls FROM movies WHERE trailer_urls='[]' ORDER BY title;"
                records = Records()
                movies = records.fetch( sql, all=True )
                total_count = len( movies )
                for count, movie in enumerate( movies ):
                    ok = _progress_dialog( count + 1, total_count, movie )
                    ok = records.update( "movies", ( "trailer_urls", ), ( None, movie[ 0 ], ), "idMovie" )
                    if ( not ok ): raise
                    if ( ( float( count + 1) / 100 == int( ( count + 1 ) / 100) ) or ( ( count + 1 ) == total_count ) ):
                        ok = records.commit()
                records.close()
                return True
            except: 
                records.close()
                return False

        def _update_table_movies():
            try:
                sql = "ALTER TABLE movies ADD saved_core integer"
                records = Records()
                records.cursor.execute( sql )
                records.close()
                return True
            except: return False

        def _update_version():
            records = Records()
            ok = records.update( "version", ( "version", ), ( __version__, 1, ), "idVersion", True )
            records.close()
            return ok

        msg = ( _( 53 ), _( 54 ), )
        if ( version in ( "pre-0.97.1", "pre-0.97.2", "pre-0.97.3", "pre-0.97.4", "pre-0.97.5", "0.97.5", "pre-0.98", "pre-0.98.1", "pre-0.98.2", ) ):
            try:
                _progress_dialog()
                ok = True
                if ( version == "pre-0.97.1" ):
                    ok = _update_table()
                if ( not ok ): raise
                if ( version == "pre-0.97.1" or version == "pre-0.97.2" ):
                    ok = _update_records()
                if ( not ok ): raise
                if ( version == "pre-0.97.3" ):
                    ok, updated = _update_completed()
                    if ( updated ): complete = False
                if ( version in ( "pre-0.97.1", "pre-0.97.2", "pre-0.97.3", "pre-0.97.4", "pre-0.97.5", "0.97.5", "pre-0.98", "pre-0.98.1", ) ):
                    ok = _update_table_movies()
                if ( not ok ): raise
                ok = _update_records_poster()
                if ( not ok ): raise
                ok = _update_version()
                if ( not ok ): raise
            except:
                msg = ( _( 59 ), _( 46 ), )
            _progress_dialog( -1 )
            if ( ok ): return ( __version__, complete )
        xbmcgui.Dialog().ok( __scriptname__, msg[ 1 ] )
        raise


class Tables( dict ):
    """ Database tables dictionary class """
    def __init__( self ):
        #{ column name, type, auto increment, index , index columns }
        self[ "version" ] = (
            ( "idVersion", "integer PRIMARY KEY", "AUTOINCREMENT", "", "" ),
            ( "version", "text", "", "", "" ),
            ( "complete", "integer", "", "", "" ),
        )
        self[ "genres" ] = (
            ( "idGenre", "integer PRIMARY KEY", "AUTOINCREMENT", "", "" ),
            ( "genre", "text", "", "", "" ),
            ( "urls", "blob", "", "", "" ),
            ( "trailer_urls", "blob", "", "", "" ),
            ( "updated", "text", "", "", "" ),
        )
        self[ "actors" ] = (
            ( "idActor", "integer PRIMARY KEY", "AUTOINCREMENT", "", "" ),
            ( "actor", "text", "", "", "" ),
        )
        self[ "studios" ] = ( 
            ( "idStudio", "integer PRIMARY KEY", "AUTOINCREMENT", "", "" ),
            ( "studio", "text", "", "", "" ),
        )
        self[ "movies" ] = (
            ( "idMovie", "integer PRIMARY KEY", "AUTOINCREMENT", "", "" ), 
            ( "title", "text", "", "", "" ),
            ( "url", "text",  "", "", "" ),
            ( "trailer_urls", "text", "", "", "" ),
            ( "poster", "text", "", "", "" ),
            ( "plot", "text", "", "", "" ),
            ( "rating", "text", "", "", "" ),
            ( "rating_url", "text", "", "", "" ),
            ( "year", "integer", "", "", "" ),
            ( "times_watched", "integer", "", "", "" ),
            ( "last_watched", "text", "", "", "" ),
            ( "favorite", "integer", "", "", "" ),
            ( "saved_location", "text", "", "", "" ),
            ( "saved_core", "integer", "", "", "" ),
        )
        self[ "genre_link_movie" ] = ( 
            ( "idGenre", "integer", "", "UNIQUE INDEX", "(idGenre, idMovie)" ),
            ( "idMovie", "integer", "", "UNIQUE INDEX", "(idMovie, idGenre)" ),
        )
        self[ "actor_link_movie" ] = ( 
            ( "idActor", "integer", "", "UNIQUE INDEX", "(idActor, idMovie)" ),
            ( "idMovie", "integer", "", "UNIQUE INDEX", "(idMovie, idActor)" ),
        )
        self[ "studio_link_movie" ] = ( 
            ( "idStudio", "integer", "", "UNIQUE INDEX", "(idStudio, idMovie)" ),
            ( "idMovie", "integer", "", "UNIQUE INDEX", "(idMovie, idStudio)" ),
        )


class Records:
    "add, delete, update and fetch records"
    def __init__( self, *args, **kwargs ):
        self.tables = Tables()
        self.connect()

    def connect( self ):
        self.db = sqlite.connect( os.path.join( BASE_DATA_PATH, "AMT.db" ) )#, detect_types=sqlite.PARSE_DECLTYPES|sqlite.PARSE_COLNAMES)
        self.cursor = self.db.cursor()
    
    def commit( self ):
        try:
            self.db.commit()
            return True
        except: return False
    
    def close( self ):
        self.db.close()
    
    def add( self, table, params, commit=False ):
        try:
            sql = "INSERT INTO %s (" % ( table, )
            count = 0
            for column in self.tables[ table ]:
                if ( column[ 2 ] != "AUTOINCREMENT" ):
                    sql += "%s, " % column[ 0 ]
                    count += 1
                if ( count == len( params ) ): break
            sql = sql[ : -2 ] + ") VALUES (" + ( "?, " * len( params ) )
            sql = sql[ : -2 ] + ");"
            self.cursor.execute( sql, params )
            if ( commit ): ok = self.commit()
            return self.cursor.lastrowid
        except:
            LOG( LOG_ERROR, "%s (ver: %s) Records::add [sql=%s %s]", __scriptname__, __version__, sql, sys.exc_info()[ 1 ], )
            return False

    def delete( self, table, columns, params, commit=False ):
        try:
            sql = "DELETE FROM %s WHERE " % table
            for col in columns:
                sql += "%s=? AND " % col
            sql = sql[ : -5 ]
            self.cursor.execute( sql, params )
            if ( commit ): ok = self.commit()
            return True
        except:
            LOG( LOG_ERROR, "%s (ver: %s) Records::delete [sql=%s %s]", __scriptname__, __version__, sql, sys.exc_info()[ 1 ], )
            return False

    def update( self, table, columns, params, key, commit=False ):
        try:
            if ( isinstance( columns[ 0 ], int ) ):
                start_column = columns[ 0 ]
                if ( len( columns ) == 2 ):
                    end_column = columns[ 1 ]
                else:
                    end_column = len( self.tables[table] )
                columns = ()
                for item in self.tables[table][ start_column : end_column ]:
                    columns += ( item[0], )
            sql = "UPDATE %s SET " % ( table, )
            for col in columns:
                sql += "%s=?, " % col
            sql = sql[:-2] + " WHERE %s=?;" % ( key, )
            self.cursor.execute( sql, params )
            if ( commit ): ok = self.commit()
            return True
        except:
            LOG( LOG_ERROR, "%s (ver: %s) Records::update [sql=%s %s]", __scriptname__, __version__, sql, sys.exc_info()[ 1 ], )
            return False

    def fetch( self, sql, params=None, all=False ):
        try:
            if ( params is not None ): self.cursor.execute( sql , params )
            else: self.cursor.execute( sql )
            if ( all ): retval = self.cursor.fetchall()
            else: retval = self.cursor.fetchone()
        except:
            retval = None
        return retval


class Query( dict ):
    "all sql statments. add as needed"
    def __init__( self ):
        #good sql statements
        self[ "movie_by_movie_id" ]		= "SELECT movies.* FROM movies WHERE movies.idMovie=?;"
        self[ "studio_by_movie_id" ]		= "SELECT studios.studio FROM studio_link_movie, studios WHERE studio_link_movie.idStudio = studios.idStudio AND studio_link_movie.idMovie=?;"
        self[ "actors_by_movie_id" ]		= "SELECT actors.actor FROM actor_link_movie, actors WHERE actor_link_movie.idActor = actors.idActor AND actor_link_movie.idMovie=? ORDER BY actors.actor;"

        self[ "movies_by_genre_id" ]		= "SELECT movies.* FROM movies, genre_link_movie WHERE genre_link_movie.idMovie=movies.idMovie AND genre_link_movie.idGenre=? ORDER BY movies.title;"
        self[ "movies_by_studio_id" ]		= "SELECT movies.* FROM movies, studio_link_movie WHERE studio_link_movie.idMovie=movies.idMovie AND studio_link_movie.idStudio=? ORDER BY movies.title;"
        self[ "movies_by_actor_id" ]		= "SELECT movies.* FROM movies, actor_link_movie WHERE actor_link_movie.idMovie=movies.idMovie AND actor_link_movie.idActor=? ORDER BY movies.title;"

        self[ "movies_by_genre_name" ]	= "SELECT movies.* FROM movies, genres, genre_link_movie WHERE genre_link_movie.idGenre=genres.idGenre AND genre_link_movie.idMovie=movies.idMovie AND genres.genre=? ORDER BY movies.title;"
        self[ "movies_by_studio_name" ]= "SELECT movies.* FROM movies, studios, studio_link_movie WHERE studio_link_movie.idStudio=studios.idStudio AND studio_link_movie.idMovie=movies.idMovie AND upper(studios.studio)=? ORDER BY movies.title;"
        self[ "movies_by_actor_name" ]	= "SELECT movies.* FROM movies, actors, actor_link_movie WHERE actor_link_movie.idActor=actors.idActor AND actor_link_movie.idMovie=movies.idMovie AND upper(actors.actor) LIKE ? ORDER BY movies.title;"

        self[ "incomplete_movies" ]		= "SELECT * FROM movies WHERE trailer_urls IS NULL ORDER BY title;"
        self[ "version" ]						= "SELECT * FROM version;"

        self[ "genre_category_list" ]		= "SELECT genres.idGenre, genres.genre, count(genre_link_movie.idGenre) FROM genre_link_movie, genres WHERE genre_link_movie.idGenre=genres.idGenre GROUP BY genres.genre;"
        self[ "studio_category_list" ]		= "SELECT studios.idStudio, studios.studio, count(studio_link_movie.idStudio) FROM studio_link_movie, studios WHERE studio_link_movie.idStudio=studios.idStudio GROUP BY upper(studios.studio);"
        self[ "actor_category_list" ]		= "SELECT actors.idActor, actors.actor, count(actor_link_movie.idActor) FROM actor_link_movie, actors WHERE actor_link_movie.idActor=actors.idActor GROUP BY upper(actors.actor);"

        self[ "genre_table_list" ]			= "SELECT idGenre, genre, updated FROM genres ORDER BY genre;"
        self[ "genre_urls_by_genre_id" ]	= "SELECT urls FROM genres WHERE idGenre=?;"
        self[ "idMovie_by_genre_id" ]		= "SELECT idMovie FROM genre_link_movie WHERE idGenre=?;"
        self[ "idMovie_in_genre" ]			= "SELECT * FROM genre_link_movie WHERE idGenre=? AND idMovie=?;"

        self[ "movie_exists" ]				= "SELECT idMovie FROM movies WHERE upper(title)=?;"
        self[ "actor_exists" ]				= "SELECT idActor FROM actors WHERE upper(actor)=?;"
        self[ "studio_exists" ]				= "SELECT idStudio FROM studios WHERE upper(studio)=?;"

        self[ "favorites" ]						= "SELECT * FROM movies WHERE favorite=? ORDER BY title;"
        self[ "downloaded" ]					= "SELECT * FROM movies WHERE saved_location!=? ORDER BY title;"

        self[ "hd_trailers" ]					= "SELECT * FROM movies WHERE trailer_urls LIKE ? ORDER BY title;"
        self[ "no_trailer_urls" ]				= "SELECT * FROM movies WHERE (trailer_urls=? OR trailer_urls IS NULL) AND poster IS NOT NULL ORDER BY title;"
