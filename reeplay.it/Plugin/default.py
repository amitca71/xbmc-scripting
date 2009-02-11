"""
 A Plugin to play videos shared at http://reeplay.it

 Written By BigBellyBilly
 bigbellybilly AT gmail DOT com	- bugs, comments, ideas ...

 Please don't alter or re-publish this script without authors persmission.
 Additional support may be found on xboxmediacenter forum.	

 - url = sys.argv[ 0 ]
 - handle = sys.argv[ 1 ]
 - params =  sys.argv[ 2 ]

"""

import xbmc, xbmcgui, xbmcplugin
import sys, os, traceback
from xml.sax.saxutils import unescape
from xml.sax.saxutils import escape
from pprint import pprint

__plugin__ = "reeplay.it"
__scriptname__  = "reeplay.it"
__version__ = '0.9'
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__svn_url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/reeplay.it"
__date__ = '10-02-2009'
xbmc.output(__plugin__ + " Version: " + __version__ + " Date: " + __date__)

# Shared resources
DIR_HOME= os.getcwd().replace(';','')
DIR_SCRIPT_HOME = '/'.join( [ "Q:", "scripts", __scriptname__] )
DIR_RESOURCES_LIB = '/'.join( [DIR_SCRIPT_HOME, "resources", "lib"] ) # shares modules with script version
DIR_USERDATA = '/'.join( ["T:", "script_data", __plugin__] )
DIR_CACHE = '/'.join( [ DIR_USERDATA, "cache"] )
sys.path.insert(0, xbmc.translatePath(DIR_RESOURCES_LIB) )

# Load Language using xbmc builtin
try:
    # 'resources' now auto appended onto path
    __lang__ = xbmc.Language( xbmc.translatePath(DIR_SCRIPT_HOME) ).getLocalizedString
except:
	print str( sys.exc_info()[ 1 ] )
	xbmcgui.Dialog().ok("XBMC Language Error", "Install a new XBMC build to run this script.")

from bbbLib import *
import reeplayit

debug("DIR_HOME=" + DIR_HOME)
debug("DIR_SCRIPT_HOME=" + DIR_SCRIPT_HOME)
debug("DIR_RESOURCES_LIB=" + DIR_RESOURCES_LIB)
debug("DIR_USERDATA=" + DIR_USERDATA)
debug("DIR_CACHE=" + DIR_CACHE)

#################################################################################################################
class ReeplayitPlugin:
	""" main plugin class """

	def __init__( self, *args, **kwargs ):
		self.debug("> __init__()")
		if DEBUG:
			pprint (sys.argv)

		# load settings (as set in script)
		if not self.loadSettings():
			self.debug("incomplete settings - quit")
			return

		# create a new lib instance using login details
		self.reeplayitLib = reeplayit.ReeplayitLib(self.settings.get(self.settings.SETTING_USER), \
												self.settings.get(self.settings.SETTING_PWD), \
												self.settings.get(self.settings.SETTING_PAGE_SIZE), \
												self.settings.get(self.settings.SETTING_VQ), True)

		# define param key names
		self.PARAM_TITLE = "title"
		self.PARAM_PLS_ID = 'plsid'
		self.PARAM_PLS_COUNT = 'plscount'
		self.PARAM_PLS_PAGE = 'plspage'
		self.PARAM_URL = 'url'
		self.PARAM_VIDEO_ID = 'videoid'
		self.PARAM_SETTINGS = 'setting'
		self.PARAM_PLS_PLAYALL = 'plsplayall'

		if ( not sys.argv[ 2 ] ):
			# new session clear cache
			reeplayit.deleteScriptCache(False)	# just clear old XML/JSON and videos
#			xbmcplugin.ClearProperties()
			self.getPlaylists()
		else:
			# extract URL params and act accordingly
			try:
				paramDict = self._getParams()
				url = paramDict.get(self.PARAM_URL,'')
				if paramDict.has_key(self.PARAM_PLS_ID):
					title = unescape(paramDict[self.PARAM_TITLE])
					count = int(paramDict[self.PARAM_PLS_COUNT])
					page = int(paramDict.get(self.PARAM_PLS_PAGE,1))
					id = paramDict[self.PARAM_PLS_ID]
					self.getPlaylist(title, id, count, page)
				elif paramDict.has_key(self.PARAM_VIDEO_ID):
					title = unescape(paramDict[self.PARAM_TITLE])
					id = paramDict[self.PARAM_VIDEO_ID]
					self.getVideo(title, id)
				elif paramDict.has_key(self.PARAM_SETTINGS):
					if self.showMenu():
						self.debug("reset plugin")
						xbmc.executebuiltin("xbmc.ActivateWindow(videofiles,%s)" % sys.argv[0])
				elif paramDict.has_key(self.PARAM_PLS_PLAYALL):
					id = paramDict[self.PARAM_PLS_PLAYALL]
					title = unescape(paramDict[self.PARAM_TITLE])
					count = int(paramDict[self.PARAM_PLS_COUNT])
					self.playPlaylist(title, id, count) 
				else:
					raise
			except:
				traceback.print_exc()
				messageOK("ERROR", str(sys.exc_info()[ 1 ]))

		self.debug("< __init__()")

	def debug(self, msg=""):
		debug("%s.%s" % (self.__class__.__name__, msg))

	########################################################################################################################
	def loadSettings(self):
		""" Settings are set in the script, this is just to check all settings exist """
		self.debug( "> loadSettings")
		success = False

		while not success:
			self.settings = reeplayit.ReeplayitSettings()
			success = (self.settings.get(self.settings.SETTING_USER) and \
						self.settings.get(self.settings.SETTING_PWD))
			if not success:
				if xbmcgui.Dialog().yesno(__lang__(0),__lang__(107)):	# edit now?
					self.showMenu()
				else:
					break

		self.debug( "< loadSettings")
		return success


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
		self.debug( "> getPlaylists()")
		ok = False
		try:
			# include menu option
			li_url = "%s?%s=" % ( sys.argv[ 0 ], self.PARAM_SETTINGS)
			title = __lang__(204)	# menu
			li = xbmcgui.ListItem( title )
			li.setInfo("Files", {"Title" : title} )

			ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
						url=li_url, listitem=li, isFolder=False, totalItems=1)

			if not self.reeplayitLib.getPlaylists():
				raise "Empty"

			for li in self.reeplayitLib.plsListItems:
				plsTitle = li.getLabel()
				plsId = li.getProperty(self.reeplayitLib.PROP_ID)
				plsCount = int(li.getProperty(self.reeplayitLib.PROP_COUNT))

				# context menu option - Play Playlist
#				menuCmd = "xbmc.ActivateWindow(videofiles,%s?%s=%s&%s=%s&%s=%s)" % (sys.argv[0], \
#																self.PARAM_PLS_PLAYALL, plsId,
#																self.PARAM_TITLE, plsTitle, \
#																self.PARAM_PLS_COUNT, plsCount)

				# use RunPlugin as its not creating a new dir - just doing an action
				menuCmd = "xbmc.RunPlugin(%s?%s=%s&%s=%s&%s=%s)" % (sys.argv[0], \
																self.PARAM_PLS_PLAYALL, plsId,
																self.PARAM_TITLE, plsTitle, \
																self.PARAM_PLS_COUNT, plsCount)
				li.addContextMenuItems([(__lang__(233), menuCmd)])		# play pls
	
				li_url = "%s?%s=%s&%s=%s&%s=%s" % ( sys.argv[ 0 ], \
												self.PARAM_TITLE, plsTitle, \
												self.PARAM_PLS_ID, plsId, \
												self.PARAM_PLS_COUNT, plsCount )

				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
							url=li_url, listitem=li, isFolder=True, totalItems=plsCount)
				if ( not ok ): break
		except "Empty":
			self.debug("Empty raised")
			messageOK(__plugin__, __lang__(104))	# no pls found
		except:
			traceback.print_exc()
			messageOK("ERROR:", str(sys.exc_info()[ 1 ]))

		if ok:
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_SIZE )
			xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="files" )

		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok)
		self.debug( "< getPlaylists() ok=%s" % ok)

	########################################################################################################################
	def getPlaylist(self, plsTitle, plsId, plsCount, plsPage=1):
		""" Discover a list of Categories within a Directory """
		self.debug( "> getplaylist() plsId=%s plsCount=%s plsPage=%s" % (plsId,plsCount,plsPage))

		ok = False
		try:
			maxPages = self.reeplayitLib.getMaxPages( plsCount )
			isNextPage = (plsPage < maxPages)
			self.debug("isNextPage=%s" % isNextPage)

			msg = "%s - %s %s" % (plsTitle, __lang__(219), plsPage)
			dialogProgress.create(__lang__(0), __lang__(217), msg) # DL playlist content
			self.reeplayitLib.set_report_hook(self.reeplayitLib.progressHandler, dialogProgress)

			videoCount = self.reeplayitLib.getPlaylist(plsId, page=plsPage)

			dialogProgress.close()
			if not videoCount: raise "Empty"

			if isNextPage:
				videoCount += 1
			if isNextPage:
				nextPage = plsPage+1
				title = "%s (%s/%s)" % (__lang__(221), plsPage+1, maxPages)
				
				li_url = "%s?%s=%s&%s=%s&%s=%s&%s=%s" % ( sys.argv[ 0 ], \
												self.PARAM_TITLE, escape(title), \
												self.PARAM_PLS_ID, plsId, \
												self.PARAM_PLS_COUNT, plsCount, \
												self.PARAM_PLS_PAGE, nextPage )

				li = xbmcgui.ListItem(title)
				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
							url=li_url, listitem=li, isFolder=True, totalItems=0)

			# for each video , extract info and store to a ListItem
			for li in self.reeplayitLib.videoListItems:
				videoTitle = li.getLabel()
				videoId = li.getProperty(self.reeplayitLib.PROP_ID)
#				videoLink = li.getProperty(self.reeplayitLib.PROP_URL)
#				print videoTitle, videoId#, videoLink

				li_url = "%s?%s=%s&%s=%s" % ( sys.argv[ 0 ], \
												self.PARAM_VIDEO_ID, videoId, \
												self.PARAM_TITLE, escape(videoTitle) )

				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
							url=li_url, listitem=li, isFolder=False, totalItems=videoCount)
				if ( not ok ): break
		except "Empty":
			self.debug("Empty raised")
		except:
			traceback.print_exc()
			messageOK("ERROR:", str(sys.exc_info()[ 1 ]))

#		dialogProgress.close()
		if not ok:
			messageOK(__plugin__, __lang__(105), plsTitle)	# no video
		else:
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_VIDEO_RUNTIME )
			xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="movies" )

		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )
		self.debug( "< getPlaylist() ok=%s" % ok)

	############################################################################################################
	def getVideo(self, videoTitle, videoId):
		""" Discover media link from video content """

		self.debug( "> getVideo() videoId=%s" % (videoId))
		source = ''
		try:
			source, li = self.reeplayitLib.getVideo(id=videoId, \
										title=videoTitle, \
										download=self.settings.get(self.settings.SETTING_PLAY_MODE))
			if not source:
				messageOK(__plugin__, __lang__(105), videoTitle)	# no video
			else:
#				xbmcPlaylist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
#				xbmcPlaylist.clear()
#				xbmcPlaylist.add(source, li)
#				playMedia(xbmcPlaylist)
				playMedia(source, li)
		except:
			source = ""
			traceback.print_exc()
			messageOK("ERROR:", str(sys.exc_info()[ 1 ]))

		self.debug( "< getVideo()")

	########################################################################################################################
	def playPlaylist(self, plsTitle, plsId, plsCount):
		""" Discover a list of Categories within a Directory """ 
		self.debug( "> playPlaylist() plsId=%s plsCount=%s" % (plsId,plsCount))
		ok = False

		try:
			# delete existing data docs as were now getting every video in pls, not by pagesize
			reeplayit.deleteScriptCache(False)

			dialogProgress.create(__lang__(0), __lang__(217), plsTitle) # DL playlist content
			self.reeplayitLib.set_report_hook(self.reeplayitLib.progressHandler, dialogProgress)

			# get all videos in playlist
			videoCount = self.reeplayitLib.getPlaylist(plsId, pageSize=plsCount)
			dialogProgress.close()

			if not videoCount: raise "Empty"

			# create a playlist and add items to it
			xbmcPlaylist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
			xbmcPlaylist.clear()

			playMode = self.settings.get(self.settings.SETTING_PLAY_MODE)
			for idx in range(videoCount):
				source, li = self.reeplayitLib.getVideo(idx, download=playMode)
				if source and li:
#						url = li.getProperty(self.reeplayitLib.PROP_URL)
					xbmcPlaylist.add(source, li)
				else:
					break	# http error, so stop processing more videos

			# play all in xbmc pls
			debug("Playlist size=%d" % xbmcPlaylist.size())
			if xbmcPlaylist.size() <= 0: raise "Empty"

			if xbmcgui.Dialog().yesno(__lang__(0), __lang__(234), "","", __lang__(236), __lang__(235)):
				xbmcPlaylist.shuffle()
			playMedia(xbmcPlaylist)
#			xbmc.executebuiltin("Container.Refresh")
		except "Empty":
			self.debug("Empty raised")
			messageOK(__lang__(0), __lang__(105))		# no videos
		except:
			handleException()

		self.debug( "< playPlaylist()")

	############################################################################################################
	def showMenu(self):
		self.debug( "> showMenu()")

		reset = False
		try:
			while True:
				# make menu of listItems
				options = []
				menuData = self.settings.makeMenu()
				for key, value, lbl1, lbl2 in menuData:
					options.append( lbl1 )

				# SHOW MENU
				selectedPos = xbmcgui.Dialog().select( __lang__(204), options )
				debug( "selectedPos=%s" % selectedPos)
				if selectedPos <= 0:
					break

				resetReq, newValue = self.settings.changeOption(menuData[selectedPos])
				if resetReq:
					reset = True
				elif newValue:
					# perform special actions according to option key
					key, value, optName, optValue = menuData[selectedPos]
					if key == self.settings.SETTING_VQ:
						self.reeplayitLib.setVideoProfile(newValue)
		except:
			traceback.print_exc()
			messageOK("ERROR:", str(sys.exc_info()[ 1 ]))

		self.debug( "< showMenu() reset=%s" % reset)
		return reset


#######################################################################################################################    
# BEGIN !
#######################################################################################################################
makeDir(DIR_USERDATA) 
makeDir(DIR_CACHE)

try:
	# check language loaded
	xbmc.output( "__lang__ = %s" % __lang__ )
	myplugin = ReeplayitPlugin()
	del myplugin
except:
	handleException()

# clean up on exit
debug(__plugin__ + ": exit housekeeping ...")
moduleList = ['bbbLib', 'reeplayit']
for m in moduleList:
	try:
		del sys.modules[m]
		xbmc.output(__plugin__ + " del sys.module=%s" % m)
	except: pass

# remove other globals
try:
	del dialogProgress
except: pass
sys.modules.clear()

