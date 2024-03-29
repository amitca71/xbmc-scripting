"""
Update module

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
"""

import sys
import os
import xbmcgui, xbmc
import urllib
import re
import traceback
from shutil import copytree, rmtree

class Update:
	""" Update Class: used to update scripts from http://code.google.com/p/xbmc-scripting/ """
	def __init__( self, language, script ):
		xbmc.output( "Update().__init__" )
		self._ = language
		self.script = script.replace( ' ', '%20' )
		self.base_url = "http://xbmc-scripting.googlecode.com/svn"
		self.tags_url = "%s/tags/%s/" % ( self.base_url, self.script)
		local_base_dir = os.path.join('Q:' + os.sep,'scripts')
		self.local_dir = os.path.join(local_base_dir, script)
		self.backup_base_dir = os.path.join(local_base_dir,'.backups')
		self.local_backup_dir = os.path.join(self.backup_base_dir, script)

		xbmc.output("script=" + script)
		xbmc.output("base_url=" + self.base_url)
		xbmc.output("tags_url=" + self.tags_url)
		xbmc.output("local_dir=" + self.local_dir)
		xbmc.output("local_backup_dir=" + self.local_backup_dir)

		self.dialog = xbmcgui.DialogProgress()
			
	def downloadVersion( self, version ):
		""" main update function """
		xbmc.output( "> Update().downloadVersion() version=%s" % version)
		success = False
		try:
			self.dialog.create( self._(0), self._( 1004 ), self._( 1005 ) )
			folders = [version]
			script_files = []
			# recusivly look for folders and files
			while folders:
				try:
					htmlsource = self.getHTMLSource( '%s%s' % (self.tags_url, folders[0]) )
					if htmlsource:
						# extract folder/files stored in path
						itemList, url = self.parseHTMLSource( htmlsource )

						# append folders to those we're looping throu and store file
						for item in itemList:
							if item[-1] == "/":
								folders.append( ("%s/%s" % (folders[ 0 ], item)) )
							else:
								script_files.append( ("%s/%s" % (folders[ 0 ], item)).replace('//','/') )
					else:
						xbmc.output("no htmlsource found")
						raise
					folders = folders[1:]
				except:
					folders = None

			if not script_files:
				xbmc.output("empty script_files - raise")
				raise
			else:
				success = self.getFiles( script_files, version )
			self.dialog.close()
		except:
			self.dialog.close()
			traceback.print_exc()
			xbmcgui.Dialog().ok( self._(0), self._( 1031 ) )
		xbmc.output("< Update().downloadVersion() success = %s" % success)
		return success

	def getLatestVersion( self, quiet=True ):
		""" checks for latest tag version """
		version = "-1"
		try:
			if not quiet:
				self.dialog.create( self._(0), self._( 1001 ) )

			# get version tags
			htmlsource = self.getHTMLSource( self.tags_url )
			if htmlsource:
				tagList, url = self.parseHTMLSource( htmlsource )
				if tagList:
					version = tagList[-1].replace("/","")  # remove trailing /

		except:
			traceback.print_exc()
			xbmcgui.Dialog().ok( self._(0), self._( 1031 ) )
		self.dialog.close()

		xbmc.output( "Update().getLatestVersion() new version="+str(version) )
		return version

	def makeBackup( self ):
		xbmc.output("> Update().makeBackup()")
		self.removeBackup()
		# make base backup dir
		try:
			os.makedirs(self.backup_base_dir)
			xbmc.output("created dirs=%s" % self.backup_base_dir )
		except: pass

		copytree(self.local_dir, self.local_backup_dir)
		xbmc.output("< Update().makeBackup() done")

	def issueUpdate( self, version ):
		xbmc.output("> Update().issueUpdate() version=%s" % version)
		path = os.path.join(self.local_backup_dir, 'resources','lib','update.py')
		command = 'XBMC.RunScript(%s,%s,%s)'%(path, self.script.replace('%20',' '), version)
		xbmc.executebuiltin(command)
		xbmc.output("< Update().issueUpdate() done")
	
	def removeBackup( self ):
		xbmc.output("Update().removeBackup()")
		if self.backupExists():
			rmtree(self.local_backup_dir,ignore_errors=True)		
			xbmc.output("Update().removeBackup() done")
	
	def removeOriginal( self ):
		xbmc.output("Update().removeOriginal()")
		rmtree(self.local_dir,ignore_errors=True)		
		
	def backupExists( self ):
		exists = os.path.exists(self.local_backup_dir)
		xbmc.output("Update().backupExists() %s" % exists)
		return exists

	def getFiles( self, script_files, version ):
		""" fetch the files """
		xbmc.output( "Update().getFiles() version=%s" % version )
		success = False
		try:
			totalFiles = len(script_files)
			for cnt, url in enumerate( script_files ):
				items = os.path.split( url )
				path = os.path.join(self.local_dir, items[0]).replace( version+'/', '' ).replace( version, '' ).replace('/','\\').replace( '%20', ' ' )
				file = items[ 1 ].replace( '%20', ' ' )
				pct = int( ( float( cnt ) / totalFiles ) * 100 )
				self.dialog.update( pct, "%s %s" % ( self._( 1007 ), url, ), "%s %s" % ( self._( 1008 ), path, ), "%s %s" % ( self._( 1009 ), file, ) )
				if ( self.dialog.iscanceled() ): raise
				if ( not os.path.isdir( path ) ):
					os.makedirs( path )
				src = "%s%s" % (self.tags_url, url)
				dest = os.path.join(path, file).replace( '%20', ' ' )
				urllib.urlretrieve( src,  dest)

			success = True
		except:
			raise
		return success

	def getHTMLSource( self, url ):
		""" read a doc from a url """
		safe_url = url.replace( " ", "%20" )
		xbmc.output( "Update().getHTMLSource() " + safe_url)
		try:
			sock = urllib.urlopen( safe_url )
			doc = sock.read()
			sock.close()
			return doc
		except:
			traceback.print_exc()
			return None

	def parseHTMLSource( self, htmlsource ):
		""" parse html source for tagged version and url """
		xbmc.output( "Update().parseHTMLSource()" )
		try:
			url = re.search('Revision \d+:(.*?)<', htmlsource, re.IGNORECASE).group(1).strip()
			tagList = re.compile('<li><a href="(.*?)"', re.MULTILINE+re.IGNORECASE+re.DOTALL).findall(htmlsource)
			if tagList[0] == "../":
				del tagList[0]
			return tagList, url
		except:
			return None, None

if __name__ == "__main__":
	xbmc.output("update.py running from __main__")
	if len(sys.argv) != 3:
		xbmcgui.Dialog().ok("Update error",  "Not enough arguments were passed for update")
		sys.exit(1)

	try:
		lang_path = os.path.join('Q:' + os.sep,'scripts', sys.argv[1])
		up = Update(xbmc.Language( lang_path ).getLocalizedString, sys.argv[1])
		up.removeOriginal()
		up.downloadVersion(sys.argv[2])
		xbmc.executebuiltin('XBMC.RunScript(%s)'%(up.local_dir+'\\default.py'))
	except:
		print "failed to start script update from backup copy!"