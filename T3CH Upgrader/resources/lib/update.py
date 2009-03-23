"""
Update module SCRIPT VERSION

Changes:
18-11-2007 
 Use language self._(0) in dialogs instead of __scriptname__
 Used regex to parse svn.
 Added a 'silent' mode.
 Changed to use YES/NO string ids.
02-01-2008 Fixed error in downloadVersion()
06-02-2008 Changed to update into same folder
28-02-2008 removed a syntax error when not isSilent
20-02-2008 Altered to save script backup into Q:\\scripts\\backups subfolder. Makes the scripts folder cleaner.
20-04-2008 Fix makedir of backup folder.
02-05-2008 \backups renamed to \.backups in anticipation of xbmc adopting hidden folder prefixed with '.'
12-09-2008 use os.path.join instead of string +
10-10-2008 Fix: to use xbmc.language from __main__
           Fix: Created folders replaced %20 with a space
23/02/09 - translatePath()
20/03/09 - special:// path check to fallback to old style
"""

import sys
import os
import xbmcgui, xbmc
import urllib
import re
import traceback
from shutil import copytree, rmtree

def log(msg):
	try:
		xbmc.output("[%s]: %s" % (__name__, msg))
	except: pass

# check if build is special:// aware - set roots paths accordingly
XBMC_HOME = 'special://home'
if not os.path.isdir(xbmc.translatePath(XBMC_HOME)):	# if fails to convert to Q:, old builds
	XBMC_HOME = 'Q:'
log("XBMC_HOME=%s" % XBMC_HOME)

class Update:
	""" Update Class: used to update from xbmc google svn repo """

	URL_BASE = "http://xbmc-scripting.googlecode.com/svn"
#	URL_BASE = "http://xbmc-addons.googlecode.com/svn"
	
	def __init__( self, language, script, svnUrl="" ):
		log( "Update().__init__" )

		self._ = language
		self.script = script.replace( ' ', '%20' )
		if not svnUrl:
			svnUrl = self.URL_BASE

		self.URL_TAGS = "%s/tags/%s/" % ( svnUrl, self.script)
		local_base_dir = xbmc.translatePath("/".join( [XBMC_HOME,'scripts'] ))
		self.local_dir = os.path.join(local_base_dir, script)
		self.backup_base_dir = os.path.join(local_base_dir,'.backups')
		self.local_backup_dir = os.path.join(self.backup_base_dir, script)

		log("script=" + script)
		log("URL_BASE=" + svnUrl)
		log("URL_TAGS=" + self.URL_TAGS)
		log("local_dir=" + self.local_dir)
		log("local_backup_dir=" + self.local_backup_dir)

		self.dialog = xbmcgui.DialogProgress()
			
	def downloadVersion( self, version ):
		""" main update function """
		log( "> Update().downloadVersion() version=%s" % version)
		success = False
		try:
			self.dialog.create( self._(0), self._( 1004 ), self._( 1005 ) )
			folders = [version]
			script_files = []
			# recusivly look for folders and files
			while folders:
				try:
					htmlsource = self.getHTMLSource( '%s%s' % (self.URL_TAGS, folders[0]) )
					if htmlsource:
						# extract folder/files stored in path
						itemList, url = self.parseHTMLSource( htmlsource )

						# append folders to those we're looping throu and store file
						for item in itemList:
							if item[-1] == "/":
								folders.append( ("%s/%s" % (folders[ 0 ], item)).replace('//','/') )
							else:
								script_files.append( ("%s/%s" % (folders[ 0 ], item)).replace('//','/') )
					else:
						log("no htmlsource found")
						raise
					folders = folders[1:]
				except:
					folders = None

			if not script_files:
				log("empty script_files - raise")
				raise
			else:
				success = self.getFiles( script_files, version )
			self.dialog.close()
		except:
			self.dialog.close()
			traceback.print_exc()
			xbmcgui.Dialog().ok( self._(0), self._( 1031 ) )
		log("< Update().downloadVersion() success = %s" % success)
		return success

	def getLatestVersion( self, quiet=True ):
		""" checks for latest tag version """
		version = "-1"
		try:
			if not quiet:
				self.dialog.create( self._(0), self._( 1001 ) )

			# get version tags
			htmlsource = self.getHTMLSource( self.URL_TAGS )
			if htmlsource:
				tagList, url = self.parseHTMLSource( htmlsource )
				if tagList:
					version = tagList[-1].replace("/","")  # remove trailing /

		except:
			traceback.print_exc()
			xbmcgui.Dialog().ok( self._(0), self._( 1031 ) )
		self.dialog.close()

		log( "Update().getLatestVersion() new version="+str(version) )
		return version

	def makeBackup( self ):
		log("> Update().makeBackup()")
		self.removeBackup()
		# make base backup dir
		try:
			os.makedirs(self.backup_base_dir)
			log("created dirs=%s" % self.backup_base_dir )
		except: pass

		try:
			copytree(self.local_dir, self.local_backup_dir)
		except:
			traceback.print_exc()
			xbmcgui.Dialog().ok( "Error Making Script Backup!", str( sys.exc_info()[ 1 ] ) )
		log("< Update().makeBackup() done")

	def issueUpdate( self, version ):
		log("> Update().issueUpdate() version=%s" % version)
		path = os.path.join(self.local_backup_dir, 'resources','lib','update.py')
		command = 'XBMC.RunScript(%s,%s,%s)'%(path, self.script.replace('%20',' '), version)
		log(command)
		xbmc.executebuiltin(command)
		log("< Update().issueUpdate() done")
	
	def removeBackup( self ):
		try:
			rmtree(self.local_backup_dir,ignore_errors=True)		
			log("Update().removeBackup() removed OK")
		except: pass
	
	def removeOriginal( self ):
		try:
			rmtree(self.local_dir,ignore_errors=True)
			log("Update().removeOriginal() removed OK")
		except:
			traceback.print_exc()
		
	def backupExists( self ):
		exists = os.path.exists(self.local_backup_dir)
		log("Update().backupExists() %s" % exists)
		return exists

	def getFiles( self, script_files, version ):
		""" fetch the files """
		log( "Update().getFiles() version=%s" % version )
		success = False
		try:
			totalFiles = len(script_files)
			log("Update().getFiles() totalFiles=%d" % totalFiles)
			for cnt, url in enumerate( script_files ):
				items = os.path.split( url )
				path = os.path.join(self.local_dir, items[0]).replace( version+'/', '' ).replace( version, '' ).replace('/','\\').replace( '%20', ' ' )
				file = items[ 1 ].replace( '%20', ' ' )
				pct = int( ( float( cnt ) / totalFiles ) * 100 )
				self.dialog.update( pct, "%s %s" % ( self._( 1007 ), url, ), "%s %s" % ( self._( 1008 ), path, ), "%s %s" % ( self._( 1009 ), file, ) )
				if ( self.dialog.iscanceled() ): raise
				if ( not os.path.isdir( path ) ):
					os.makedirs( path )
				src = "%s%s" % (self.URL_TAGS, url)
				dest = os.path.join(path, file).replace( '%20', ' ' )
				src = src.replace(' ','%20')
				log("urlretrieve src=%s dest=%s" % (src, dest))
				urllib.urlretrieve( src,  dest)

			success = True
		except:
			raise
		return success

	def getHTMLSource( self, url ):
		""" read a doc from a url """
		safe_url = url.replace( " ", "%20" )
		log( "Update().getHTMLSource() " + safe_url)
		try:
			sock = urllib.urlopen( safe_url )
			doc = sock.read()
			sock.close()
			return doc
		except:
			traceback.print_exc()
			xbmcgui.Dialog().ok( self._(0),  str( sys.exc_info()[ 1 ] ))
			return None

	def parseHTMLSource( self, htmlsource ):
		""" parse html source for tagged version and url """
		log( "Update().parseHTMLSource()" )
		try:
			url = re.search('Revision \d+:(.*?)<', htmlsource, re.IGNORECASE).group(1).strip()
			tagList = re.compile('<li><a href="(.*?)"', re.MULTILINE+re.IGNORECASE+re.DOTALL).findall(htmlsource)
			if tagList[0] == "../":
				del tagList[0]
			return tagList, url
		except:
			return None, None

if __name__ == "__main__":
	log("update.py running from __main__")
	if len(sys.argv) != 3:
		xbmcgui.Dialog().ok("Update error",  "Not enough arguments were passed for update")
		sys.exit(1)

	try:
		lang_path = xbmc.translatePath("/".join( [XBMC_HOME,'scripts', sys.argv[1]] ))
		up = Update(xbmc.Language( lang_path ).getLocalizedString, sys.argv[1])
		up.removeOriginal()
		up.downloadVersion(sys.argv[2])
		xbmc.executebuiltin('XBMC.RunScript(%s)' % os.path.join(up.local_dir, 'default.py'))
	except:
		traceback.print_exc()
		print "failed to start script update from backup copy!"