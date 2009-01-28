"""
 A Plugin to play videos shared at http://reeplay.it

 Written By BigBellyBilly
 bigbellybilly AT gmail DOT com	- bugs, comments, ideas ...

 - url = sys.argv[ 0 ]
 - handle = sys.argv[ 1 ]
 - params =  sys.argv[ 2 ]

"""

__plugin__ = "reeplay.it"
__scriptname__  = "reeplay.it"
__version__ = '0.3'
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '28-01-2009'

import sys, os.path
import xbmc, xbmcgui, xbmcplugin
import re, os, traceback, urllib, urllib2, cookielib
from xml.sax.saxutils import unescape
from xml.sax.saxutils import escape

if os.name=='posix':    
    DIR_HOME = os.path.abspath(os.curdir).replace(';','')		# Linux case
else:
    DIR_HOME= os.getcwd().replace(';','')
DIR_USERDATA = os.path.join( "T:"+os.sep,"script_data", __plugin__ )
DIR_RESOURCES = os.path.join( "Q:"+os.sep,"scripts", __scriptname__, "resources" )
DIR_RESOURCES_LIB = os.path.join( DIR_RESOURCES , "lib" )
DIR_CACHE = os.path.join(DIR_USERDATA, "cache")
sys.path.insert(0, DIR_RESOURCES_LIB)

import xbmcutils.net as net
from bbbLib import *
from reeplayit import *

print "plugin URL_BASE=" , URL_BASE

#################################################################################################################
class ReeplayitPlugin:
	""" main plugin class """

	def __init__( self, *args, **kwargs ):
		debug("> __init__() argv[ 2 ]=%s " % sys.argv[ 2 ])
		debug( "argv[ 1 ]=%s" % sys.argv[ 1 ])

		URL_BASE = "http://staging.reeplay.it/"        # LIVE is "http://reeplay.it/"

		# load settings (as set in script)
		if not self.loadSettings():
			messageOK(__plugin__, "Settings Incomplete", "Please run Script version to setup settings.")
			return

		# CREATE HTTP HANDLERS
		try:
			debug("setup HTTP handlers")
			# password manager handler
			passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
			passman.add_password(None, URL_BASE, self.user, self.pwd)
			# Basic Auth. handler
			authhandler = urllib2.HTTPBasicAuthHandler(passman)

			# Cookie handler
			self.cookiejar = cookielib.LWPCookieJar()
			self.cookie_file = os.path.join(DIR_CACHE, 'cookie.lwp')
			if fileExist(self.cookie_file):
				self.cookiejar.load(self.cookie_file)
			cookiehandler = urllib2.HTTPCookieProcessor(self.cookiejar)

			# add our handlers
			urlopener = urllib2.build_opener(authhandler, cookiehandler)
			# install urlopener so all urllib2 calls use our handlers
			urllib2.install_opener(urlopener)
			debug("install_opener done")
			self.http_installed = True
		except:
			handleException("HTTP handlers")
			return

		self.PROP_ID = "ID"					# pls id
		self.PROP_COUNT = "COUNT"			# pls video count
		self.PROP_URL = "URL"				# video url
		self.URL_PLAYLISTS = URL_BASE + "users/%s/playlists.xml"
		self.URL_PLAYLIST = URL_BASE + "users/%s/playlists/%s.xml?page=%s^page_size=%s"
		self.lastSaveMediaPath = DIR_USERDATA

		# define param key names
		self.PARAM_TITLE = "title"
		self.PARAM_PLS_ID = 'plsid'
		self.PARAM_PLS_COUNT = 'plscount'
		self.PARAM_URL = 'url'
		self.PARAM_VIDEO_ID = 'videoid'
		self.report_hook = None
		self.report_udata = None

		if ( not sys.argv[ 2 ] ):
			# new session clear cache
			deleteScriptCache(False)	# just clear old XML and videos
#			xbmcplugin.ClearProperties()
			self.getPlaylists()
		else:
			# extract URL params and act accordingly
			try:
				paramDict = self._getParams()
				url = paramDict[self.PARAM_URL]
				if paramDict.has_key(self.PARAM_PLS_ID):
					title = unescape(paramDict[self.PARAM_TITLE])
					id = paramDict[self.PARAM_PLS_ID]
					count = int(paramDict[self.PARAM_PLS_COUNT])
					page = int(searchRegEx(url, 'page=(\d+)'))
					self.getPlaylist(title, id, url, count, page)
				elif paramDict.has_key(self.PARAM_VIDEO_ID):
					title = unescape(paramDict[self.PARAM_TITLE])
					id = paramDict[self.PARAM_VIDEO_ID]
					fn = self.getVideo(title, id, url)
					if fn:
						playMedia(fn)
				else:
					raise
			except:
				print sys.exc_info()[ 1 ]
				messageOK("ERROR", str(sys.exc_info()[ 1 ]))

		debug("< __init__()")

	########################################################################################################################
	def loadSettings(self):
		""" Settings are set in the script, this is just to check all settings exist """
		debug( "loadSettings")
		self.settings = loadFileObj( os.path.join( DIR_USERDATA, "settings.txt" ), {} )
		self.user = self.settings.get('user','')
		self.pwd = self.settings.get('pwd','')
		self.pageSize = self.settings.get('page_size','')
#		self.pageSize = 10000	# fixed so we dont have to bother with paging
		vq = self.settings.get('video_quality',False)
		self.vqProfile = ( 'xbmc_high', 'xbmc_standard' )[vq]
		if not self.user or not self.pwd or not self.pageSize or not self.vqProfile:
			return False
		else:
			return True

	########################################################################################################################
	def _getParams(self):
		""" extract params from argv[2] to make a dict (key=value) """
		paramDict = {}
		paramPairs=sys.argv[2][1:].split( "&" )
		for paramsPair in paramPairs:
			param = paramsPair.split('=')
			if len(param) == 2:
				paramDict[param[0]] = param[1]
			elif len(param) > 2:
				value = "=".join(param[1:]).replace('^','&')	# frig to avoid being split prematurely
				paramDict[param[0]] = value

		if DEBUG:
			print "paramDict=%s" % paramDict
		return paramDict

	########################################################################################################################
	def getPlaylists(self):
		""" Return a list of Playlists """
		debug( "> getPlaylists()")
		ok = False
		try:
			# if exist, load from cache
			xmlFN = os.path.join(DIR_CACHE, "playlists.xml")
			debug("xmlFN=" + xmlFN)
			data = readFile(xmlFN)
			if not data:
				# not in cache, download
				dialogProgress.create(__plugin__, "Downloading Playlists ...", self.user)
				self.set_report_hook(self.progressHandler, dialogProgress)
				data = self.retrieve(self.URL_PLAYLISTS % self.user)
				dialogProgress.close()

			if not data: raise "Empty"

			# extarct data and store into ListItems
			items = parsePlaylists(data)
			itemCount = len(items)
			if not itemCount: raise "Empty"

			for item in items:
				title, id, desc, count, updatedDate, imgURL = item
				# get thumb image
				imgName = os.path.basename(imgURL)
				imgFN = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, imgName))
				if not fileExist(imgFN):
					data = self.retrieve(imgURL, fn=imgFN)
					if data == "": # aborted
						break
					elif not data:
						imgFN = ""

				longTitle = "%s (%s)" % (title, count)			
				link = self.URL_PLAYLIST % (self.user, id, 1, self.pageSize)
				li_url = "%s?%s=%s&%s=%s&%s=%s&%s=%s" % ( sys.argv[ 0 ], \
												self.PARAM_TITLE, escape(title), \
												self.PARAM_PLS_ID, id, \
												self.PARAM_PLS_COUNT, count, \
												self.PARAM_URL, link )

				li = xbmcgui.ListItem(longTitle, desc, imgFN, imgFN)
				li.setInfo(type="video", infoLabels={ "Title" : longTitle, "Size": int(count), \
													  "Album" : desc, "Date" : updatedDate })

				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
							url=li_url, listitem=li, isFolder=True, totalItems=itemCount)
				if ( not ok ): break
		except "Empty":
			debug("Empty raised")
		except:
			traceback.print_exc()
			messageOK("ERROR:", str(sys.exc_info()[ 1 ]))

		if not ok:
			messageOK(__plugin__, "No Playlists Found")
		else:
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_SIZE )
			xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="files" )

		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )
		debug( "< getPlaylists() ok=%s" % ok)

	########################################################################################################################
	def getPlaylist(self, plsTitle, plsId, plsUrl, plsCount, page):
		""" Discover a list of Categories within a Directory """
		debug( "> getplaylist() %s id=%s %s count=%s page=%s" % (plsTitle, plsId, plsUrl, plsCount, page))

		ok = False
		try:
			maxPages = int( plsCount / self.pageSize)
			mod = plsCount % self.pageSize
			if mod:
				maxPages += 1
			debug("videoCount=%s maxPages=%s" % (plsCount, maxPages))
			isNextPage = (page < maxPages)

			dialogProgress.create(__plugin__, "Downloading Playlist ...", plsTitle, "Page: %d / %d" % (page,maxPages))
			self.set_report_hook(self.progressHandler, dialogProgress)

			# if exist, load from cache
			xmlFN = os.path.join(DIR_CACHE, "pls_%s_page_%d.xml" % (plsId, page))
			debug("xmlFN=" + xmlFN)
			data = readFile(xmlFN)
			if not data:
				# not in cache, download
				data = self.retrieve(plsUrl)
				saveData(data, xmlFN)

			if not data: raise "Empty"

			items = parsePlaylist(data)
			itemCount = len(items)
			if not itemCount: raise "Empty"

			if isNextPage:
				itemCount += 1

			if isNextPage:
				newPage = "page=%s^" % (page+1)
				oldPage = "page=%s&" % page
				title = "Next Page (%s/%s)" % (page+1, maxPages)
				link = plsUrl.replace(oldPage, newPage)
				li_url = "%s?%s=%s&%s=%s&%s=%s&%s=%s" % ( sys.argv[ 0 ], \
												self.PARAM_TITLE, escape(title), \
												self.PARAM_PLS_ID, plsId, \
												self.PARAM_PLS_COUNT, plsCount, \
												self.PARAM_URL, link )

				li = xbmcgui.ListItem(title)
				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
							url=li_url, listitem=li, isFolder=True, totalItems=itemCount)

			defaultThumbImg = xbmc.makeLegalFilename(os.path.join(DIR_HOME, "default.tbn"))

			# for each video , extract info and store to a ListItem
			for item in items:
				videoTitle, videoid, videoDate, link, imgURL, duration = item
				link += "?profile=%s" % self.vqProfile

				# get thumb image
				imgName = videoid+".jpg"
				imgFN = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, imgName))
				if not fileExist(imgFN):
					debug("download imgFN=" + imgFN)
					# download thumb image
					if not self.retrieve(imgURL, fn=imgFN):
						imgFN = defaultThumbImg

				li_url = "%s?%s=%s&%s=%s&%s=%s" % ( sys.argv[ 0 ], \
												self.PARAM_VIDEO_ID, videoid, \
												self.PARAM_TITLE, escape(videoTitle), \
												self.PARAM_URL, link )

				li = xbmcgui.ListItem(videoTitle, videoDate, imgFN, imgFN)
				li.setInfo(type="video", infoLabels={ "Title" : videoTitle, "Date" : videoDate, "Duration" : duration })

				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
							url=li_url, listitem=li, isFolder=False, totalItems=itemCount)
				if ( not ok ): break
		except "Empty":
			debug("Empty raised")
		except:
			traceback.print_exc()
			messageOK("ERROR:", str(sys.exc_info()[ 1 ]))

#		dialogProgress.close()
		if not ok:
			messageOK(__plugin__, "No videos found", plsTitle)
		else:
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
			xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="movies" )

		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )
		debug( "< getPlaylist() ok=%s" % ok)

	############################################################################################################
	def getVideo(self, title, id, url):
		""" Discover media link from video content """

		debug( "> getVideo() %s %s" % (id, url))
		fn = ''
		try:
			dialogProgress.create(__plugin__, title, "User Authentication ...")
			self.set_report_hook(self.progressHandler, dialogProgress)
			data = self.retrieve(self.URL_PLAYLISTS % self.user)
			dialogProgress.update(0, title, "Video Information ...")

			# if exist, load from cache
			xmlFN = os.path.join(DIR_CACHE, "%s_%s.xml" % (id, self.vqProfile))
			debug("xmlFN=" + xmlFN)
			data = readFile(xmlFN)
			if not data:
				# not in cache, download
				data = self.retrieve(url)
				saveData(data, xmlFN)

			if not data: raise "Empty"

			videoURL = parseVideo(data)
			debug("videoURL=" + videoURL)

			# download and save video from its unique media-url
			if not videoURL: raise "Empty"

			basename = os.path.basename(videoURL)
			videoName = "%s_%s%s" % (id, self.vqProfile, os.path.splitext(basename)[1])		# eg ".mp4"
			fn = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, videoName))
			if not fileExist(fn):
				dialogProgress.update(0,  "Downloading Video ...", title, videoName)
				if not self.retrieve(videoURL, fn=fn):
					deleteFile(fn)	# delete incase of partial DL
					raise "Empty"
					
		except "Empty":
			debug("Empty raised")
			fn = ""
		except:
			fn = ""
			traceback.print_exc()
			messageOK("ERROR:", str(sys.exc_info()[ 1 ]))

		dialogProgress.close()
		if not fn:
			messageOK(__plugin__, "Video not found!", title)

		debug( "< getVideo() fn=%s" % fn)
		return fn


	##############################################################################################################
	def retrieve(self, url, post=None, headers={}, fn=None):
		""" Downloads an url. Returns: None = error , '' = cancelled """
		debug("retrieve() " + url)
		if fn:
			debug("retrieve() fn=" + fn)
		try:
			result = net.retrieve (url, post, headers, self.report_hook, self.report_udata, fn)
			if result:
				self.cookiejar.save(self.cookie_file)
			return result
		except net.AuthError, e:
			messageOK(__plugin__, "Authorization Failed!")
		except net.DownloadAbort, e:
			messageOK(__plugin__ + ": Download Aborted!", e.value)
			return "" # means aborted
		except net.DownloadError, e:
			messageOK(__plugin__ + ": Download Error!", e.value)
		except:
			handleException()
		return None


	##############################################################################################################
	def set_report_hook(self, func, udata=None):
		"""Set the download progress report handler."""
		debug("set_report_hook()")
		self.report_hook = func
		self.report_udata = udata

	##############################################################################################################
	def progressHandler(self, count, totalsize, dlg):
		"""Update progress dialog percent and return abort status."""
		if count and totalsize:
			percent = int((count * 100) / totalsize )
			if (percent % 5) == 0:
				dlg.update( percent )

		return not dlg.iscanceled()


#######################################################################################################################    
# BEGIN !
#######################################################################################################################
try:
	os.makedirs(DIR_USERDATA)
except: pass

if ( __name__ == "__main__" ):
	app = ReeplayitPlugin()
	del app

# remove other globals
try:
	del dialogProgress
except: pass

