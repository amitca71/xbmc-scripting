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
__version__ = '0.5'
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '29-01-2009'

import sys, os.path
import xbmc, xbmcgui, xbmcplugin
import os, traceback
from xml.sax.saxutils import unescape
from xml.sax.saxutils import escape

if os.name=='posix':    
    DIR_HOME = os.path.abspath(os.curdir).replace(';','')		# Linux case
else:
    DIR_HOME= os.getcwd().replace(';','')
DIR_USERDATA = os.path.join( "T:"+os.sep, "script_data", __plugin__ )
DIR_SCRIPT_HOME = os.path.join( "Q:"+os.sep, "scripts", __scriptname__ )
DIR_RESOURCES = os.path.join( DIR_SCRIPT_HOME, "resources" )
DIR_RESOURCES_LIB = os.path.join( DIR_RESOURCES, "lib" )
DIR_CACHE = os.path.join(DIR_USERDATA, "cache")
sys.path.insert(0, DIR_RESOURCES_LIB)

# Load Language using xbmc builtin
try:
    # 'resources' now auto appended onto path
    __lang__ = xbmc.Language( DIR_SCRIPT_HOME ).getLocalizedString
except:
	print str( sys.exc_info()[ 1 ] )
	xbmcgui.Dialog().ok("xbmc.Language Error (Old XBMC Build)", "Install a new XBMC build to run this script.")

from bbbLib import *
import reeplayit

#################################################################################################################
class ReeplayitPlugin:
	""" main plugin class """

	def __init__( self, *args, **kwargs ):
		self.debug("> __init__() argv[ 2 ]=%s " % sys.argv[ 2 ])
		self.debug( "argv[ 1 ]=%s" % sys.argv[ 1 ])

		# load settings (as set in script)
		if not self.loadSettings():
			messageOK(__plugin__, __lang__(110))	# setup incomplete
			return

		# create a new lib instance using login details
		self.reeplayitLib = reeplayit.ReeplayitLib(self.user, self.pwd, self.pageSize, self.vq)

		# define param key names
		self.PARAM_TITLE = "title"
		self.PARAM_PLS_ID = 'plsid'
		self.PARAM_PLS_COUNT = 'plscount'
		self.PARAM_PLS_PAGE = 'plspage'
		self.PARAM_URL = 'url'
		self.PARAM_VIDEO_ID = 'videoid'
		self.PARAM_SETTING_KEY = 'setting_key'
		self.PARAM_SETTING_NAME = 'setting_name'

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
					id = paramDict[self.PARAM_PLS_ID]
					count = int(paramDict[self.PARAM_PLS_COUNT])
					page = int(paramDict.get(self.PARAM_PLS_PAGE,1))
					self.getPlaylist(title, id, count, page)
				elif paramDict.has_key(self.PARAM_VIDEO_ID):
					title = unescape(paramDict[self.PARAM_TITLE])
					id = paramDict[self.PARAM_VIDEO_ID]
					source = self.getVideo(title, id)
					if source:
						playMedia(source)
				elif paramDict.has_key(self.PARAM_SETTING_KEY):
					key = paramDict.get(self.PARAM_SETTING_KEY)     # if empty means just show menu as a dir
					name = paramDict.get(self.PARAM_SETTING_NAME,'')     # will be empty on first call	
					self.showMenu(key, name)
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
		self.debug( "loadSettings")
		self.settings = reeplayit.ReeplayitSettings()
		
		self.user = self.settings.get(self.settings.SETTING_USER)
		self.pwd = self.settings.get(self.settings.SETTING_PWD)
		self.pageSize = self.settings.get(self.settings.SETTING_PAGE_SIZE)
		self.vq = self.settings.get(self.settings.SETTING_VQ)
		self.playbackMode = self.settings.get(self.settings.SETTING_PLAY_MODE)
		if not self.user or not self.pwd:
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
		self.debug( "> getPlaylists()")
		ok = False
		try:
			# include menu option
			li_url = "%s?%s=" % ( sys.argv[ 0 ], self.PARAM_SETTING_KEY)
			title = __lang__(204)
			li = xbmcgui.ListItem( title )
			li.setInfo("Files", {"Title" : title} )
			ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
						url=li_url, listitem=li, isFolder=True, totalItems=0)

			if not self.reeplayitLib.getPlaylists():
				raise "Empty"

			for li in self.reeplayitLib.plsListItems:
				plsTitle = li.getLabel()
				plsId = li.getProperty(self.reeplayitLib.PROP_ID)
				plsCount = int(li.getProperty(self.reeplayitLib.PROP_COUNT))
#				plsLink = self.reeplayitLib.URL_PLAYLIST % (self.user, id, 1, self.pageSize)
#				print plsTitle, plsId, plsCount

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

		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )
		self.debug( "< getPlaylists() ok=%s" % ok)

	########################################################################################################################
	def getPlaylist(self, plsTitle, plsId, plsCount, plsPage=1):
		""" Discover a list of Categories within a Directory """
		self.debug( "> getplaylist() %s plsId=%s plsCount=%s plsPage=%s" % (plsTitle, plsId, plsCount, plsPage))

		ok = False
		try:
			maxPages = self.reeplayitLib.getMaxPages( plsCount )
			isNextPage = (plsPage < maxPages)
			self.debug("isNextPage=%s" % isNextPage)

			videoCount = self.reeplayitLib.getPlaylist(-1, plsId, plsTitle, plsPage)
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
													download=self.playbackMode, \
													authReq=True)
			if not source:
				messageOK(__plugin__, __lang__(105), videoTitle)	# no video
		except:
			source = ""
			traceback.print_exc()
			messageOK("ERROR:", str(sys.exc_info()[ 1 ]))

		self.debug( "< getVideo() source=%s" % source)
		return source


	############################################################################################################
	def showMenu(self, key="", name=""):
		""" Alter settings bycreating a directory of menu options """

		self.debug( "> showMenu() key=%s" % (key))
		ok = False
		try:
			# if key; change option
			reset = False
			if key:
				value = self.settings.get(key)
				optionData = (key, value, name, "")
				resetReq, newValue = self.settings.changeOption(optionData)
				if newValue:
					# perform special actions according to option key
					if key == self.settings.SETTING_VQ:
						self.reeplayitLib.setVideoProfile(newValue)
			else:
				# first time into settings, warn of reset
				messageOK(__plugin__, "Any changed setings won't come into","effect until Plugin restarted.")

			# make menu of listItems
			menuData = self.settings.makeMenu()
			print menuData
			itemCount = len(menuData)
			print sys.argv[ 0 ]
			print sys.argv[ 1 ]
			for key, value, lbl1, lbl2 in menuData[3:]:
				li_url = "%s?%s=%s&%s=%s" % ( sys.argv[ 0 ], \
										self.PARAM_SETTING_KEY, key, \
										self.PARAM_SETTING_NAME, lbl1)
				li = xbmcgui.ListItem( lbl1 )
				li.setInfo("Files", {"Title" : lbl1} )

				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
							url=li_url, listitem=li, isFolder=False, totalItems=itemCount)
				if ( not ok ): break
		except:
			traceback.print_exc()
			messageOK("ERROR:", str(sys.exc_info()[ 1 ]))

		if ok:
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
			xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="files" )

		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )
		self.debug( "< showMenu() ok=%s" % ok)


#######################################################################################################################    
# BEGIN !
#######################################################################################################################
makeScriptDataDir() 
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

