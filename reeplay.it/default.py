"""
    Python XBMC script to view videos at reeplay.it

	Written By BigBellyBilly
	bigbellybilly AT gmail DOT com	- bugs, comments, ideas, help ...

	THANKS:
	To everyone who's ever helped in anyway, or if I've used code from your own scripts, MUCH APPRECIATED!

    Please don't alter or re-publish this script without authors persmission.

	CHANGELOG: see changelog.txt or view throu Settings Menu
	README: see ..\resources\language\<language>\readme.txt or view throu Settings Menu

    Additional support may be found on xboxmediacenter forum.	
"""

import xbmc, xbmcgui
import sys, os.path
from os import path
from string import find, strip, replace

# Script doc constants
__scriptname__ = "reeplay.it"
__version__ = '0.4'
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__svn_url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/reeplay.it"
__date__ = '28-01-2009'
xbmc.output(__scriptname__ + " Version: " + __version__ + " Date: " + __date__)

# Shared resources
DIR_HOME = os.getcwd().replace( ";", "" )
DIR_RESOURCES = os.path.join( DIR_HOME , "resources" )
DIR_RESOURCES_LIB = os.path.join( DIR_RESOURCES , "lib" )
DIR_USERDATA = os.path.join( "T:"+os.sep,"script_data", __scriptname__ )
DIR_CACHE = os.path.join(DIR_USERDATA, "cache")
sys.path.insert(0, DIR_RESOURCES_LIB)

# Load Language using xbmc builtin
try:
    # 'resources' now auto appended onto path
    __lang__ = xbmc.Language( DIR_HOME ).getLocalizedString
except:
	print str( sys.exc_info()[ 1 ] )
	xbmcgui.Dialog().ok("xbmc.Language Error (Old XBMC Build)", "Script needs at least XBMC 'Atlantis' build to run.")

import update
from bbbLib import *
from bbbSkinGUILib import TextBoxDialogXML
import reeplayit

#################################################################################################################
# MAIN
#################################################################################################################
class ReeplayitGUI(xbmcgui.WindowXML):
	# control id's
	CGRP_HEADER = 1000
	CLBL_VERSION = 1001
	CLBL_TITLE = 1002
	CGRP_FOOTER = 3000
	CLBL_BACK_BTN = 3001
	CLBL_WHITE_BTN = 3002
	CLBL_A_BTN = 3003
	CLBL_B_BTN = 3004
	CLST_CONTENT = 50
	CBTN_PREV_PAGE = 20
	CBTN_NEXT_PAGE = 21
	CLST_WINDOW_LISTS = (50, 51, 52, 53, 54, 55, 56, 57, 58, 59)

	#################################################################################################################
	def __init__(self, *args, **kwargs):
		debug("> __init__")

		self.ready = False
		self.startup = True
		self.contentListControlID = self.CLST_CONTENT

		# settings keys
		self.SETTINGS_FILENAME = os.path.join( DIR_USERDATA, "settings.txt" )
		self.SETTING_USER = "user"
		self.SETTING_PWD = "pwd"
		self.SETTING_CHECK_UPDATE = "check_script_update_startup"
		self.SETTING_PAGE_SIZE = "page_size"
		self.SETTING_VQ = "video_quality"
		self.SETTING_CACHE_ACTION = "cache_action"
		self.SETTING_PLAY_MODE = "play_mode"

		self.SETTINGS_DEFAULTS = {
			self.SETTING_USER : "",
			self.SETTING_PWD : "",
			self.SETTING_CHECK_UPDATE : False,
			self.SETTING_PAGE_SIZE : 200,
			self.SETTING_VQ : False,					# False = high, True = med
			self.SETTING_CACHE_ACTION : False,			# False == All, True == Videos Only
			self.SETTING_PLAY_MODE : False				# False == Stream, True == Download
			}

		self.settings = {}
		self._initSettings()
		# check for script update
		if self.settings[self.SETTING_CHECK_UPDATE]:	# check for update ?
			scriptUpdated = updateScript(False, False)
		else:
			scriptUpdated = False
		if not scriptUpdated:
			self.ready = True

		debug("< __init__")

	######################################################################################
	def exit(self):
		debug("exit()")
		reeplayit.deleteScriptCache(self.settings[self.SETTING_CACHE_ACTION])
		self.close()

	######################################################################################
	def _initSettings( self, forceReset=False ):
		debug("> _initSettings() forceReset=%s" % forceReset)
		changed = False

		if forceReset:
			self.settings = {}
		elif not self.settings:
			self.settings = loadFileObj( self.SETTINGS_FILENAME, {} )

		# put default values into any settings that are missing
		for key, defaultValue in self.SETTINGS_DEFAULTS.items():
			if forceReset or not self.settings.has_key( key ) or self.settings[key] in [None,""]:
				self.settings[key] = defaultValue
				changed = True
				debug("using default value for key=%s" % key)

		if changed or not fileExist(self.SETTINGS_FILENAME):
			saveFileObj(self.SETTINGS_FILENAME, self.settings)

		debug( "< _initSettings() changed=%s" % changed)
		return changed


	#################################################################################################################
	def reset(self):
		debug("reset()")
		self.ready = self.login()
		if not self.ready:
			self.exit()
			return False

		self.isContentPlaylists = True
		self.lastPlaylistIdx = 0
		self.current_position = 0
		self.currPage = 1
		self.maxPages = 1
		return True

	#################################################################################################################
	def onInit( self ):
		debug("> onInit() startup=%s" % self.startup)
		if self.startup:
			self.startup = False
			self.getControl( self.CLBL_VERSION ).setLabel( "v" + __version__ )
			self.getControl( self.CBTN_PREV_PAGE ).setVisible(False)
			self.getControl( self.CBTN_NEXT_PAGE ).setVisible(False)
			self.getControl( self.CLBL_BACK_BTN ).setLabel( __lang__(203) )
			self.getControl( self.CLBL_WHITE_BTN ).setLabel( __lang__(204) )
			self.getControl( self.CLBL_A_BTN ).setLabel( __lang__(229) )
			self.getControl( self.CLBL_B_BTN ).setLabel( __lang__(230) )

			if self.reset():
				self.initPlaylists()
#					self.setCurrentListPosition(self.current_position)
#					self.setFocus(self.getControl(self.CLST_CONTENT))
		elif not self.isContentPlaylists:
			debug("refresh default window list with videoList")
			self.initList(self.reeplayitLib.videoListItems)
		else:
			debug("refresh default window list with plsList")
			self.initList(self.reeplayitLib.plsListItems, self.lastPlaylistIdx)

		self.ready = True
		debug("< onInit()")

	#################################################################################################################
	def onAction(self, action):
		try:
			actionID = action.getId()
			if not actionID:
				actionID = action.getButtonCode()
		except: return

		# allow exit regardless of ready state
		if (actionID in EXIT_SCRIPT):
			self.exit()
		if not self.ready: return

		self.ready = False
		if actionID in CONTEXT_MENU:
			debug("> CONTEXT_MENU")
			if self.mainMenu():
				self.startup = True
				self.onInit()
			debug("< CONTEXT_MENU")
		elif actionID in CLICK_B:
			debug("> CLICK_B isContentPlaylists=%s" %  self.isContentPlaylists)
			if not self.isContentPlaylists:
				self.initPlaylists()
			debug("< CLICK_B")

		self.ready = True

	#################################################################################################################
	def onClick(self, controlID):
		debug("onClick() controlID=%s" % controlID)
		if not controlID or not self.ready:
			return
		self.ready = False

		if (controlID in self.CLST_WINDOW_LISTS):
			debug("> CLST_CONTENT")
			if self.isContentPlaylists:
				self.playlistSelected()
			else:
				self.videoSelected()
			debug("< CLST_CONTENT")
		elif (controlID == self.CBTN_PREV_PAGE):
			self.getNextPrevPage(False)
		elif (controlID == self.CBTN_NEXT_PAGE):
			self.getNextPrevPage(True)

		self.ready = True

	##############################################################################################
	def onFocus(self, controlID):
		debug("onFocus() controlID %i" % controlID)
		self.controlID = controlID
		if controlID in self.CLST_WINDOW_LISTS:
			self.contentListControlID = controlID

	##############################################################################################
	def isReady(self):
		return self.ready

	##############################################################################################
	def setHeader(self, title=""):
		self.getControl( self.CLBL_TITLE ).setLabel(title)

	##############################################################################################
	def setPageNav(self):
		debug("setPageNav() currPage=%s maxPages=%s " % (self.currPage, self.maxPages))
		# PREV btn
		ctrl = self.getControl( self.CBTN_PREV_PAGE )
		ctrl.setLabel("%s   (%s/%s)" % (__lang__(220), self.currPage-1, self.maxPages))
		ctrl.setVisible((self.currPage > 1))
		# NEXT btn
		ctrl = self.getControl( self.CBTN_NEXT_PAGE )
		ctrl.setLabel("%s   (%s/%s)" % (__lang__(221), self.currPage+1, self.maxPages))
		ctrl.setVisible((self.currPage < self.maxPages))

	##############################################################################################################
	def getNextPrevPage(self, isNextPage):
		debug("> getNextPrevPage() isNextPage=%s" % isNextPage)

		origPage = self.currPage
		if isNextPage:
			self.currPage += 1
		else:
			self.currPage -= 1

		success = self.initVideos(self.lastPlaylistIdx)
		if success:
			self.setPageNav()
		else:
			self.currPage = origPage

		debug("< getNextPrevPage() success=%s" % success)

	##############################################################################################
	def mainMenu(self):
		debug("> mainMenu()")

		reset = False
		self.getControl(self.CGRP_HEADER).setEnabled(False)
		while True:
			# BUILD MENU OPTIONS
			user = "%s %s" % (__lang__(303), self.settings[self.SETTING_USER])
			# get pwd - show as * for the length of pwd
			pwd = "%s " % __lang__(304)
			for i in range(len(self.settings[self.SETTING_PWD])):
				pwd += "*"

			pageSZ = "%s %s" % (__lang__(305), self.settings[self.SETTING_PAGE_SIZE])
			if self.settings[self.SETTING_CHECK_UPDATE]:
				yesno = __lang__(200)
			else:
				yesno = __lang__(201)
			check_startup = "%s %s" % (__lang__(302), yesno)

			# video quality (high, med, low)
			vqValue = (__lang__(225), __lang__(226))[self.settings[self.SETTING_VQ]]
			vq = "%s %s" % (__lang__(306), vqValue)

			# cache action on exit
			cacheValue = (__lang__(227), __lang__(228))[self.settings[self.SETTING_CACHE_ACTION]]
			cache = "%s %s" % (__lang__(307), cacheValue)

			# Playback mode
			playbackValue = (__lang__(231), __lang__(232))[self.settings[self.SETTING_PLAY_MODE]]
			playback = "%s %s" % (__lang__(308), playbackValue)

			# make menu
			options = [__lang__(203), __lang__(300), __lang__(301), check_startup, user, pwd, pageSZ, vq, cache,playback]
			selectedPos = xbmcgui.Dialog().select( __lang__(204), options )
			debug( "selectedPos=%s" % selectedPos)
			if selectedPos <= 0:
				break
			elif selectedPos == 1:
				fn = getReadmeFilename()
				tbd = TextBoxDialogXML("DialogScriptInfo.xml", DIR_HOME, "Default")
				tbd.ask(options[selectedPos], fn=fn)
				del tbd
			elif selectedPos == 2:
				fn = os.path.join( DIR_HOME, "changelog.txt" )
				tbd = TextBoxDialogXML("DialogScriptInfo.xml", DIR_HOME, "Default")
				tbd.ask(options[selectedPos], fn=fn)
				del tbd
			elif selectedPos == 3:
				self.settings[self.SETTING_CHECK_UPDATE] = not self.settings[self.SETTING_CHECK_UPDATE]
				saveFileObj(self.SETTINGS_FILENAME, self.settings)
			elif selectedPos == 4:
				result = doKeyboard(self.settings[self.SETTING_USER], options[selectedPos])
				if result:
					self.settings[self.SETTING_USER] = result
					saveFileObj(self.SETTINGS_FILENAME, self.settings)
					reset = True
			elif selectedPos == 5:
				result = doKeyboard(self.settings[self.SETTING_PWD], options[selectedPos], KBTYPE_ALPHA, True)
				if result:
					self.settings[self.SETTING_PWD] = result
					saveFileObj(self.SETTINGS_FILENAME, self.settings)
					reset = True
			elif selectedPos == 6:
				result = doKeyboard(str(self.settings[self.SETTING_PAGE_SIZE]), options[selectedPos], KBTYPE_NUMERIC)
				if result:
					# ensure range limits
					result = int(result)
					if result < 5:
						result = 5
					elif result > 1000: # limited by available ram - much less on xbox
						result = 1000
					self.settings[self.SETTING_PAGE_SIZE] = result
					saveFileObj(self.SETTINGS_FILENAME, self.settings)
					self.reeplayitLib.setPageSize(result)
					# delete existing cached XML as its probs for wrong page size now
					reeplayit.deleteScriptCache(False)
					reset = True
			elif selectedPos == 7:
				# video quality
				self.settings[self.SETTING_VQ] = not self.settings[self.SETTING_VQ]	# toggle
				saveFileObj(self.SETTINGS_FILENAME, self.settings)
				self.reeplayitLib.setVideoProfile(self.settings[self.SETTING_VQ])
			elif selectedPos == 8:
				# cache action on exit
				self.settings[self.SETTING_CACHE_ACTION] = not self.settings[self.SETTING_CACHE_ACTION]	# toggle
				saveFileObj(self.SETTINGS_FILENAME, self.settings)
			elif selectedPos == 9:
				# playback mode
				print self.settings[self.SETTING_PLAY_MODE]
				self.settings[self.SETTING_PLAY_MODE] = not self.settings[self.SETTING_PLAY_MODE]	# toggle
				print self.settings[self.SETTING_PLAY_MODE]
				saveFileObj(self.SETTINGS_FILENAME, self.settings)
				print "saved"

		self.getControl(self.CGRP_HEADER).setEnabled(True)
		debug ("< mainMenu() reset=%s" % reset)
		return reset

	##############################################################################################################
	def initList(self, items=[], itemIdx=0):
		debug("> initList() itemIdx=%s" % itemIdx)

		self.clearList()
		if items:
			xbmcgui.lock()
			for item in items:
				self.addItem(item)

			self.setCurrentListPosition(self.current_position)
			debug("contentListControlID=%s" % self.contentListControlID)
			self.getControl(self.contentListControlID).selectItem(itemIdx)
			self.setFocus(self.getControl(self.contentListControlID))
			xbmcgui.unlock()
		debug("< initList()")

	#################################################################################################################
	def initPlaylists(self):
		debug("> initPlaylists() lastPlaylistIdx=%s" % self.lastPlaylistIdx)
		success = False
		if self.reeplayitLib.getPlaylists():
			self.setHeader(__lang__(216))		# choose a pls
			success = True
		else:
			self.setHeader(__lang__(104))		# no pls found

		# send [] to clear
		self.initList(self.reeplayitLib.plsListItems, self.lastPlaylistIdx)
		self.isContentPlaylists = True
		self.currPage = 1
		self.maxPages = 1
		self.setPageNav()

		debug("< initPlaylists() success=%s" % success)
		return success

	##############################################################################################################
	def playlistSelected(self):
		debug("> playlistSelected()")
		success = False

		idx = self.getCurrentListPosition()
		li = self.reeplayitLib.getPlsLI(idx)
		videoCount = int(li.getProperty(self.reeplayitLib.PROP_COUNT))
		# set cur & max videos pages as determined by max page setting
		self.maxPages = int( videoCount / self.settings[self.SETTING_PAGE_SIZE])
		mod = videoCount % self.settings[self.SETTING_PAGE_SIZE]
		if mod:
			self.maxPages += 1
		debug("videoCount=%s maxPages=%s" % (videoCount, self.maxPages))

		self.currPage = 1
		success = self.initVideos(idx)
		self.lastPlaylistIdx = idx
		if success:
			self.setPageNav()

		debug("< playlistSelected() success=%s" % success)
		return success

	######################################################################################
	def initVideos(self, plsIdx=0):
		debug("> initVideos() plsIdx=%s" % plsIdx)
		success = False

		if self.reeplayitLib.getPlaylist(plsIdx, self.currPage):
			self.initList(self.reeplayitLib.videoListItems)
			self.isContentPlaylists = False
			self.setHeader(__lang__(218))		# choose a video
			success = True
		else:
			messageOK(__lang__(0), __lang__(105))

		debug("< initVideos() success=%s" % success)
		return success

	##############################################################################################################
	def videoSelected(self):
		debug("> videoSelected()")

		idx = self.getCurrentListPosition()
		source, li = self.reeplayitLib.getVideo(idx, self.settings[self.SETTING_PLAY_MODE])
		if source:
			playMedia(source, li)
#					messageOK(__lang__(0), __lang__(109), source)	# playback failed
#		elif fn == None:
#			messageOK(__lang__(0), __lang__(106))		# DL failed

		debug("< videoSelected()")

	##############################################################################################################
	def login(self):
		debug("> login()")
		success = False

		# loop to ensure use/pwd entered
		while not success:
			user = self.settings[self.SETTING_USER]
			pwd =  self.settings[self.SETTING_PWD]
			if not user or not pwd:
				if not xbmcgui.Dialog().yesno(__lang__(0),__lang__(107)):
					break
				else:
					self.mainMenu()
					continue
			else:
				# create a new lib instance using login details
				self.reeplayitLib = reeplayit.ReeplayitLib(user, pwd, \
												self.settings[self.SETTING_PAGE_SIZE], \
												self.settings[self.SETTING_VQ])
				success = True

		debug("< login() success=%s" % success)
		return success

######################################################################################
def updateScript(silent=False, notifyNotFound=False):
	debug( "> updateScript() silent=%s" % silent)

	updated = False
	up = update.Update(__lang__, __scriptname__)
	version = up.getLatestVersion(silent)
	debug("Current Version: %s Tag Version: %s" % (__version__,version))
	if version and version != "-1":
		if __version__ < version:
			if xbmcgui.Dialog().yesno( __lang__(0), \
								"%s %s %s." % ( __lang__(1006), version, __lang__(1002) ), \
								__lang__(1003 )):
				updated = True
				up.makeBackup()
				up.issueUpdate(version)
		elif notifyNotFound:
			dialogOK(__lang__(0), __lang__(1000))
#	elif not silent:
#		dialogOK(__lang__(0), __lang__(1030))				# no tagged ver found

	del up
	debug( "< updateScript() updated=%s" % updated)
	return updated


#############################################################################################
# BEGIN !
#############################################################################################
makeScriptDataDir() 
makeDir(DIR_CACHE)

try:
	# check language loaded
	xbmc.output( "__lang__ = %s" % __lang__ )
	installPlugin('video', __scriptname__, __lang__(1015), )
	myscript = ReeplayitGUI("script-reeplay-main.xml", DIR_HOME, "Default")
	if myscript.ready:
		myscript.doModal()
	del myscript
except:
	handleException()

# clean up on exit
debug("exiting script, housekeeping ...")
moduleList = ['bbbLib', 'bbbSkinGUILib', 'reeplayit', 'net']
for m in moduleList:
	try:
		del sys.modules[m]
		xbmc.output(__scriptname__ + " del sys.module=%s" % m)
	except: pass

# remove other globals
try:
	del dialogProgress
except: pass

sys.modules.clear()

# goto xbmc home window
#try:
#	xbmc.executebuiltin('XBMC.ReplaceWindow(0)')
#except: pass
