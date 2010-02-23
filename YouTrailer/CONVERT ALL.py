import Image, os, shutil
from os.path import join, isdir, splitext, exists
from os import listdir

from crcmod import mkCrcFun
import sys
import sqlite3
import shutil
import os, shutil, time, traceback
from os.path import join, isdir, splitext, exists, getsize
import os, shutil, time
from os import stat, mkdir, rmdir, listdir
import os,shutil,string

g=mkCrcFun(0x104C11DB7,rev=False)

def getCrc(filename):
    crc     = hex(g(filename.lower()))
    nicecrc = str(crc[2:-1].lower()).rjust(8,'0') 
    return str(nicecrc)


#Changeable Values Below
vid_db_in = "C:\\Program Files\\XBMC\\userdata\\Database\\MyVideos34.db"
vid_thumbs_in = "C:\\Program Files\\XBMC\\userdata\\Thumbnails\\Video\\"
vid_db_out = "MyVideos34.db"
vid_thumbs_out = "Video\\"

mus_db_in = "C:\\Program Files\\XBMC\\userdata\\Database\\MyMusic7.db"
mus_thumbs_in = "C:\\Program Files\\XBMC\\userdata\\Thumbnails\\Music\\"
mus_db_out = "MyMusic7.db"
mus_thumbs_out = "Music\\"

src_replaces = [["E:\\PUBLIC\\", "smb://NEXSTAR/PUBLIC/"]]

XBOX_IP = '192.168.1.73'
XBOX_USERDATA_PATH = '/E/XBMC/UserData'

fanartdim = 400,400
thumdim = 200,200


try:
    shutil.copy(vid_db_in, vid_db_out)
    if not isdir(vid_thumbs_out):
        mkdir(vid_thumbs_out)
    for item in os.listdir(vid_thumbs_in):
        if isdir(join(vid_thumbs_in, item)):
            if not exists(join(vid_thumbs_out, item)):
                mkdir(join(vid_thumbs_out, item))

    # 1st do movies
    # 3 thumbs for movies
    # Fanart thumb  I:\\PUBLIC\\Movie Test\\Layer Cake (2004)\\Layer Cake (2004).avi
    # Movie DB Thumb  I:\\PUBLIC\\Movie Test\\Layer Cake (2004)\\Layer Cake (2004).avi
    #Movie Folder Thumb  I:\\PUBLIC\\Movie Test\\Layer Cake (2004)\\
    for src_replace in src_replaces:
        old_src = src_replace[0]
        new_src = src_replace[1]

        conn = sqlite3.connect(vid_db_out)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM movie')
        rows = cursor.fetchall()
        for row in rows:
            try:
                idFile = row[22]
                cursor.execute('SELECT * FROM files WHERE idFile =?', (idFile,))
                files = cursor.fetchone()
                idPath = files[1]
                strFilename = files[2]
                cursor.execute('SELECT strPath FROM path WHERE idPath =?', (idPath,))
                old_strPath = cursor.fetchone()[0]
                old_fanart = "%s%s" % (old_strPath, strFilename)
                old_moviedb = "%s%s" % (old_strPath, strFilename)
                old_folder = "%s" % old_strPath
                new_strPath = (old_strPath.replace(old_src, new_src)).replace("\\", "/")
                new_fanart = (old_fanart.replace(old_src, new_src)).replace("\\", "/")
                new_moviedb = (old_moviedb.replace(old_src, new_src)).replace("\\", "/")
                new_folder = (old_folder.replace(old_src, new_src)).replace("\\", "/")
                old_fanart_crc = getCrc(old_fanart)
                old_moviedb_crc = getCrc(old_moviedb)
                old_folder_crc = getCrc(old_folder)
                new_fanart_crc = getCrc(new_fanart)
                new_moviedb_crc = getCrc(new_moviedb)
                new_folder_crc = getCrc(new_folder)
                old_fanart_path = join(vid_thumbs_in, "Fanart", old_fanart_crc + ".tbn")
                old_moviedb_path = join(vid_thumbs_in, old_moviedb_crc[0], old_moviedb_crc + ".tbn")
                old_folder_path = join(vid_thumbs_in, old_folder_crc[0], old_folder_crc + ".tbn")
                new_fanart_path = join(vid_thumbs_out, "Fanart", new_fanart_crc + ".tbn")
                new_moviedb_path = join(vid_thumbs_out, new_moviedb_crc[0], new_moviedb_crc + ".tbn")
                new_folder_path = join(vid_thumbs_out, new_folder_crc[0], new_folder_crc + ".tbn")
                if exists(old_fanart_path):
                    if not exists(new_fanart_path):
                        shutil.copy( old_fanart_path, new_fanart_path )
                        FEEDFILE = new_fanart_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_fanart_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( fanartdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_fanart_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
                if exists(old_moviedb_path):
                    if not exists(new_moviedb_path):
                        shutil.copy( old_moviedb_path, new_moviedb_path )
                        FEEDFILE = new_moviedb_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_moviedb_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( thumdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_moviedb_path )            
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
                if exists(old_folder_path):
                    if not exists(new_folder_path):
                        shutil.copy( old_folder_path, new_folder_path )
                        FEEDFILE = new_folder_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_folder_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( thumdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_folder_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
            except:
                print "error. Row:"
                print row
        conn.commit()
        print "Movies Done. From: %s To: %s" % ( old_src, new_src )
        #MOVIES DONE!!


        #2nd do TV Shows
        #6 thumbs for tv shows
        # Show Folder Thumb  I:\\PUBLIC\\TV Test\\Family Guy\\	- done
        # Episode Thumb  I:\\PUBLIC\\TV Test\\Family Guy\\Season 1\\s01e01 - Death Has A Shadow.avi - done
        # Fanart Thumb  I:\\PUBLIC\\TV Test\\Family Guy\\ - done
        # Season Thumb  seasonI:\\PUBLIC\\TV Test\\Family Guy\\Season 1
        # Season Specials Thumb   seasonI:\\PUBLIC\\TV Test\\Family Guy\\Specials
        # Season All Thumb       seasonI:\\PUBLIC\\TV Test\\Family Guy\\* All seasons

        cursor.execute('SELECT * FROM episode')
        rows = cursor.fetchall()
        for row in rows:
            try:
                idEpisode = row[0]
                idFile = row[22]
                cursor.execute('SELECT idShow FROM tvshowlinkepisode WHERE idEpisode =?', (idEpisode,))
                show_idShow = cursor.fetchone()[0]
                cursor.execute('SELECT idPath FROM tvshowlinkpath WHERE idShow =?', (show_idShow,))
                show_idPath = cursor.fetchone()[0]
                cursor.execute('SELECT strPath FROM path WHERE idPath =?', (show_idPath,))
                show_strPath = cursor.fetchone()[0]
                
                cursor.execute('SELECT * FROM files WHERE idFile =?', (idFile,))
                files = cursor.fetchone()
                idPath = files[1]
                strFilename = files[2]
                season = strFilename[1:3]
                if int(season) < 10:
                    season = strFilename[2]
                else:
                    season = strFilename[1:3]
                cursor.execute('SELECT strPath FROM path WHERE idPath =?', (idPath,))
                
                old_strPath = cursor.fetchone()[0]
                old_episode = "%s%s" % (old_strPath, strFilename)
                old_season = "season%sSeason %s" % (show_strPath, season)
                old_season_special = "season%sSpecials" % (show_strPath)
                old_season_all = "season%s* All seasons" % (show_strPath)

                old_episode_crc = getCrc(old_episode)
                old_season_crc = getCrc(old_season)
                old_season_special_crc = getCrc(old_season_special)
                old_season_all_crc = getCrc(old_season_all)

                old_episode_path = join(vid_thumbs_in, old_episode_crc[0], old_episode_crc + ".tbn")
                old_season_path = join(vid_thumbs_in, old_season_crc[0], old_season_crc + ".tbn")
                old_season_special_path = join(vid_thumbs_in, old_season_special_crc[0], old_season_special_crc + ".tbn")
                old_season_all_path = join(vid_thumbs_in, old_season_all_crc[0], old_season_all_crc + ".tbn")

                new_strPath = (old_strPath.replace(old_src, new_src)).replace("\\", "/")
                new_episode = (old_episode.replace(old_src, new_src)).replace("\\", "/")
                new_season = (old_season.replace(old_src, new_src)).replace("\\", "/")
                new_season_special = (old_season_special.replace(old_src, new_src)).replace("\\", "/")
                new_season_all = (old_season_all.replace(old_src, new_src)).replace("\\", "/")
                
                new_episode_crc = getCrc(new_episode)
                new_season_crc = getCrc(new_season)
                new_season_special_crc = getCrc(new_season_special)
                new_season_all_crc = getCrc(new_season_all)

                new_episode_path = join(vid_thumbs_out, new_episode_crc[0], new_episode_crc + ".tbn")
                new_season_path = join(vid_thumbs_out, new_season_crc[0], new_season_crc + ".tbn")
                new_season_special_path = join(vid_thumbs_out, new_season_special_crc[0], new_season_special_crc + ".tbn")
                new_season_all_path = join(vid_thumbs_out, new_season_all_crc[0], new_season_all_crc + ".tbn")

                if exists(old_episode_path):
                    if not exists(new_episode_path):
                        shutil.copy( old_episode_path, new_episode_path )
                        FEEDFILE = new_episode_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_episode_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( thumdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_episode_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
                if exists(old_season_path):
                    if not exists(new_season_path):
                        shutil.copy( old_season_path, new_season_path )
                        FEEDFILE = new_season_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_season_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( thumdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_season_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
                if exists(old_season_special_path):
                    if not exists(new_season_special_path):
                        shutil.copy( old_season_special_path, new_season_special_path )
                        FEEDFILE = new_season_special_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_season_special_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( thumdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_season_special_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
                if exists(old_season_all_path):
                    if not exists(new_season_all_path):
                        shutil.copy( old_season_all_path, new_season_all_path )
                        FEEDFILE = new_season_all_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_season_all_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( thumdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_season_all_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
            except:
                print "error. Row:"
                print row    

        cursor.execute('SELECT * FROM tvshow')
        rows = cursor.fetchall()
        for row in rows:
            try:
                idShow = row[0]
                showName = row[1]
                cursor.execute('SELECT idPath FROM tvshowlinkpath WHERE idShow =?', (idShow,))
                idPath = cursor.fetchone()[0]
                cursor.execute('SELECT strPath FROM path WHERE idPath =?', (idPath,))
                
                old_strPath = cursor.fetchone()[0]
                old_fanart = "%s" % old_strPath
                old_folder = "%s" % old_strPath

                old_fanart_crc = getCrc(old_fanart)
                old_folder_crc = getCrc(old_folder)

                old_fanart_path = join(vid_thumbs_in, "Fanart", old_fanart_crc + ".tbn")
                old_folder_path = join(vid_thumbs_in, old_folder_crc[0], old_folder_crc + ".tbn")
                
                new_strPath = (old_strPath.replace(old_src, new_src)).replace("\\", "/")
                new_fanart = (old_fanart.replace(old_src, new_src)).replace("\\", "/")
                new_folder = (old_folder.replace(old_src, new_src)).replace("\\", "/")
                
                new_fanart_crc = getCrc(new_fanart)
                new_folder_crc = getCrc(new_folder)

                new_fanart_path = join(vid_thumbs_out, "Fanart", new_fanart_crc + ".tbn")
                new_folder_path = join(vid_thumbs_out, new_folder_crc[0], new_folder_crc + ".tbn")
                
                if exists(old_fanart_path):
                    if not exists(new_fanart_path):
                        shutil.copy( old_fanart_path, new_fanart_path )
                        FEEDFILE = new_fanart_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_fanart_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( fanartdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_fanart_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
                if exists(old_folder_path):
                    if not exists(new_folder_path):
                        shutil.copy( old_folder_path, new_folder_path )
                        FEEDFILE = new_folder_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_folder_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( thumdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_folder_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
            except:
                print "error. Row:"
                print row    
        conn.commit()
        #TV DONE
        print "TV Done. From: %s To: %s" % ( old_src, new_src )

        cursor.execute('SELECT * FROM path')
        rows = cursor.fetchall()
        for row in rows:
            idPath = row[0]
            old_strPath = row[1]
            new_strPath = (old_strPath.replace(old_src, new_src))
            if(new_strPath != old_strPath):
                new_strPath = new_strPath.replace("\\", "/")
            cursor.execute('UPDATE path SET strPath = ? WHERE idPath=?', (new_strPath, idPath))

        cursor.execute('UPDATE version SET idVersion = 33')
        conn.commit()
        conn.close()
        
    #MUSIC TIME
    shutil.copy(mus_db_in, mus_db_out)
    if not isdir(mus_thumbs_out):
        mkdir(mus_thumbs_out)
    for item in os.listdir(mus_thumbs_in):
        if isdir(join(mus_thumbs_in, item)):
            if not exists(join(mus_thumbs_out, item)):
                mkdir(join(mus_thumbs_out, item))
        
    for srcs in src_replaces:
        old_src = srcs[0]
        new_src = srcs[1]

        #copy all artist thumbs and fanart as SAME
        for item in os.listdir(join(mus_thumbs_in, "Artists")):
            destination = join(mus_thumbs_out, "Artists", item)
            if not exists(destination):
                shutil.copy(join(mus_thumbs_in, "Artists", item), destination)
                FEEDFILE = destination.replace( ".tbn", ".jpg" )
                try:
                    os.rename( destination, FEEDFILE )
                    image = Image.open( FEEDFILE )
                    image.thumbnail( thumdim, Image.ANTIALIAS )
                    image.save( FEEDFILE )
                    os.rename( FEEDFILE, destination )
                except:
                    print "Failed to resize: %s" % FEEDFILE
                    pass

        for item in os.listdir(join(mus_thumbs_in, "Fanart")):
            destination = join(mus_thumbs_out, "Fanart", item)
            if not exists(destination):
                shutil.copy(join(mus_thumbs_in, "Fanart", item), destination)
                FEEDFILE = destination.replace( ".tbn", ".jpg" )
                try:
                    os.rename( destination, FEEDFILE )
                    image = Image.open( FEEDFILE )
                    image.thumbnail( fanartdim, Image.ANTIALIAS )
                    image.save( FEEDFILE )
                    os.rename( FEEDFILE, destination )
                except:
                    print "Failed to resize: %s" % FEEDFILE
                    pass

        conn = sqlite3.connect(mus_db_out)
        cursor = conn.cursor()

        #do album thumbs
        cursor.execute('SELECT * FROM album')
        rows = cursor.fetchall()
        for row in rows:
            try:
                strAlbum = row[1]
                idArtist = row[2]
                cursor.execute('SELECT strArtist FROM artist WHERE idArtist =?', (idArtist,))
                strArtist = cursor.fetchone()[0]

                album = "%s%s" % (strAlbum, strArtist)

                album_crc = getCrc(album)

                old_album_path = join(mus_thumbs_in, album_crc[0], album_crc + ".tbn")
                new_album_path = join(mus_thumbs_out, album_crc[0], album_crc + ".tbn")
                
                if exists(old_album_path):
                    if not exists(new_album_path):
                        shutil.copy( old_album_path, new_album_path )
                        FEEDFILE = new_album_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_album_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( thumdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_album_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
            except:
                print "error. Row:"
                print row
            
        cursor.execute('SELECT * FROM song')
        rows = cursor.fetchall()
        for row in rows:
            try:
                idSong = row[0]
                idAlbum = row[1]
                idPath = row[2]
                idArist = row[3]
                strFilename = row[12]
                idThumb = row[21]

                cursor.execute('SELECT strAlbum FROM album WHERE idAlbum =?', (idAlbum,))
                strAlbum = cursor.fetchone()[0]   
                
                cursor.execute('SELECT strArtist FROM artist WHERE idArtist =?', (idArtist,))
                strArtist = cursor.fetchone()[0]

                cursor.execute('SELECT strPath FROM path WHERE idPath =?', (idPath,))

                old_strPath = cursor.fetchone()[0]
                old_strPathstrip = old_strPath[:-1]
                old_strPathstrip_crc = getCrc(old_strPathstrip)
                old_strPathstrip_path = join(mus_thumbs_in, old_strPathstrip_crc[0], old_strPathstrip_crc + ".tbn")

                new_strPath = (old_strPath.replace(old_src, new_src)).replace("\\", "/")
                new_strPathstrip = new_strPath[:-1]
                new_strPathstrip_crc = getCrc(new_strPathstrip)
                new_strPathstrip_path = join(mus_thumbs_out, new_strPathstrip_crc[0], new_strPathstrip_crc + ".tbn")

                if exists(old_strPathstrip_path):
                    if not exists(new_strPathstrip_path):
                        shutil.copy( old_strPathstrip_path, new_strPathstrip_path )
                        FEEDFILE = new_strPathstrip_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_strPathstrip_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( thumdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_strPathstrip_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass

                strThumb = "q:\UserData\Thumbnails\Music\%s\%s.tbn" %( new_strPathstrip_crc[0], new_strPathstrip_crc )
                cursor.execute('UPDATE thumb SET strThumb = ? WHERE idThumb=?', (strThumb, idThumb))
            except:
                print "error. Row:"
                print row                

        cursor.execute('SELECT * FROM path')
        rows = cursor.fetchall()
        for row in rows:
            try:
                idPath = row[0]
                old_strPath = row[1]
                old_strPathstrip = old_strPath[:-1]
                old_strPathstrip_crc = getCrc(old_strPathstrip)
                old_strPathstrip_path = join(mus_thumbs_in, old_strPathstrip_crc[0], old_strPathstrip_crc + ".tbn")

                new_strPath = (old_strPath.replace(old_src, new_src)).replace("\\", "/")
                new_strPathstrip = new_strPath[:-1]
                new_strPathstrip_crc = getCrc(new_strPathstrip)
                new_strPathstrip_path = join(mus_thumbs_out, new_strPathstrip_crc[0], new_strPathstrip_crc + ".tbn")

                if exists(old_strPathstrip_path):
                    if not exists(new_strPathstrip_path):
                        shutil.copy( old_strPathstrip_path, new_strPathstrip_path )
                        FEEDFILE = new_strPathstrip_path.replace( ".tbn", ".jpg" )
                        try:
                            os.rename( new_strPathstrip_path, FEEDFILE )
                            image = Image.open( FEEDFILE )
                            image.thumbnail( thumdim, Image.ANTIALIAS )
                            image.save( FEEDFILE )
                            os.rename( FEEDFILE, new_strPathstrip_path )
                        except:
                            print "Failed to resize: %s" % FEEDFILE
                            pass
            except:
                print "error. Row:"
                print row                
                
        conn.commit()

        cursor.execute('SELECT * FROM path')
        rows = cursor.fetchall()
        for row in rows:
            idPath = row[0]
            old_strPath = row[1]
            new_strPath = (old_strPath.replace(old_src, new_src))
            if(new_strPath != old_strPath):
                new_strPath = new_strPath.replace("\\", "/")
            cursor.execute('UPDATE path SET strPath = ? WHERE idPath=?', (new_strPath, idPath))

        conn.commit()
        conn.close()
        
        print "Music Done. From: %s To: %s" % ( old_src, new_src )

except:
    traceback.print_exc()
    raw_input()
    sys.exit()


try:
    print "starting transfer update!"
    from ftplib import FTP

    ftp = FTP( XBOX_IP, 'xbox', 'xbox' )
    directory = XBOX_USERDATA_PATH + '/Thumbnails'
    ftp.cwd(directory)

    print "transfering movie/tv show icons"
    #transfer MOVIE icons
    for item in os.listdir(vid_thumbs_out):
        if isdir(join(vid_thumbs_out, item)):
            print "Processing Folder %s" % item
            folder = join(vid_thumbs_out, item)
            ftp.cwd('%s/%s' % (directory,folder))
            filelist = ftp.nlst()
            for file in os.listdir(folder):
                if(file not in filelist):
                    print "Transfering %s" % file
                    f = open(join(folder,file),'rb')
                    ftp.storbinary('STOR %s' % file, f)
                    f.close()

    print "transfering music icons"

    #transfer Music icons
    for item in os.listdir(mus_thumbs_out):
        if isdir(join(mus_thumbs_out, item)):
            print "Processing Folder %s" % item
            folder = join(mus_thumbs_out, item)
            ftp.cwd('%s/%s' % (directory,folder))
            filelist = ftp.nlst()
            for file in os.listdir(folder):
                if(file not in filelist):
                    print "Transfering %s" % file
                    f = open(join(folder,file),'rb')
                    ftp.storbinary('STOR %s' % file, f)
                    f.close()

    print "Music transfer done"

    print "Transfering updated Database's"

    directory = XBOX_USERDATA_PATH + '/Database'
    filelist = ftp.nlst()
    
    dbfile = directory + "/" + vid_db_out
    try:
        ftp.delete( dbfile )
    except:
        traceback.print_exc()
        pass
    print "Transfering %s" % vid_db_out
    f = open(vid_db_out,'rb')
    ftp.storbinary('STOR %s' % dbfile, f)
    f.close()


    dbfile = directory + "/" + mus_db_out
    try:
        ftp.delete( dbfile )
    except:
        pass    
    print "Transfering %s" % mus_db_out
    f = open(mus_db_out,'rb')
    ftp.storbinary('STOR %s' % dbfile, f)
    f.close()

    ftp.quit()
except:
    traceback.print_exc()

print "DONE"
raw_input()

