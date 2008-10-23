"""
 Python XBMC script to view your DVDProfiler collection or somebody elses online collection.

	Written By BigBellyBilly
	bigbellybilly AT gmail DOT com	- bugs, comments, ideas, help ...

	THANKS:
	To everyone who's ever helped in anyway, or if I've used code from your own scripts, MUCH APPRECIATED!

	CHANGELOG: see ..\resources\changelog.txt or view throu Settings Menu
	README: see ..\resources\language\<language>\readme.txt or view throu Settings Menu

    Additional support may be found on xboxmediacenter forum.	
    Please don't alter or re-publish this script without authors persmission.

"""

import xbmc, xbmcgui
import sys,os.path,re,urlparse,fileinput,time
from os import path
from string import find, strip, split, lower, replace
from shutil import rmtree

# Script doc constants
__scriptname__ = "DVDProfiler"
__version__ = '1.6.3'
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '23-10-2008'
xbmc.output(__scriptname__ + " Version: " + __version__ + " Date: " + __date__)

# Shared resources
DIR_HOME = os.getcwd().replace( ";", "" )
DIR_RESOURCES = os.path.join( DIR_HOME , "resources" )
DIR_RESOURCES_LIB = os.path.join( DIR_RESOURCES , "lib" )
DIR_USERDATA = os.path.join( "T:"+os.sep, "script_data", __scriptname__ )
DIR_GFX = os.path.join(DIR_RESOURCES , "gfx")
DIR_IMG_CACHE = os.path.join(DIR_USERDATA, "images")
DIR_CACHE = os.path.join(DIR_USERDATA, "cache")
sys.path.insert(0, DIR_RESOURCES_LIB)

# Load Language using xbmc builtin
try:
    # 'resources' now auto appended onto path
    __language__ = xbmc.Language( DIR_HOME ).getLocalizedString
except:
	print str( sys.exc_info()[ 1 ] )
	xbmcgui.Dialog().ok("xbmc.Language Error (Old XBMC Build)", "Script needs at least XBMC 'Atlantis' build to run.","Use script v1.7.2 instead.")

import update                                       # script update module
from bbbLib import *								# requires __language__ to be defined
#from bbbGUILib import *
from bbbSkinGUILib import TextBoxDialogXML,DialogSelectXML
from IMDbWinXML import IMDbWin
from smbLib import *

# GLOBALS
KEYS_FILE = os.path.join( DIR_CACHE , 'keys.dat' )
COLLECTION_FLAT_FILE = os.path.join( DIR_CACHE, 'collection.dat' )
COLLECTION_XML_FILE = os.path.join( DIR_CACHE, 'collection.xml' )
BASE_URL_INTER = "http://www.intervocative.com"
BASE_URL_INVOS = "http://www.invelos.com"

# GFX
NOIMAGE_FILENAME = os.path.join( DIR_GFX , 'noimage.png' )
TICK_FILENAME = os.path.join( DIR_GFX , 'tick.png' )
FILM_FILENAME = os.path.join( DIR_GFX , 'film.png' )

QUIT_SCRIPT = -1

#################################################################################################################
class DVDProfiler(xbmcgui.WindowXML):
	# control id's
	CGRP_HEADER = 1000
	CI_COVER = 1301
	CLBL_TITLE = 1011
	CLBL_DESC = 1012
	CLBL_SCRIPT_VER = 1013
	CLBL_DATASOURCE = 1014
	CBTN_SORT_BY = 1111
	CBTN_SORT_ORDER = 1112
	CBTN_FILTER = 1113
	CLBL_MENU_BTN = 1121
	CLBL_Y_BTN = 1122
	CLBL_A_BTN = 1123
	CLBL_X_BTN = 1124
	CLBL_B_BTN = 1125
	CLBL_BACK_BTN = 1126
	CLST_TITLES_LIST = 1321
	CLST_CAST_LIST = 1331
	CTB_DETAILS = 1311

	def __init__(self, *args, **kwargs):
		debug("> DVDProfiler().init")

		self.ready = False
		self.isStartup = True

		# settings keys
		self.SETTING_SMB_USE = "smb_enabled"
		self.SETTING_SMB_PATH = "smb_path"
		self.SETTING_SMB_PC_IP = "smb_pc_ip"
		self.SETTING_SMB_FILENAME = "smb_filename"
		self.SETTING_SMB_COLLECTION_DIR = "smb_collection_dir"
		self.SETTING_SMB_IMAGES_DIR = "smb_images_dir"
		self.SETTING_SMB_DVDPRO_SHARE = "smb_dvdpro_share"
		self.SETTING_SMB_MOVIES_SHARE = "smb_movies_share"
		self.SETTING_START_MODE = "start_mode"
		self.SETTING_CHECK_UPDATE = "check_script_update_startup"
		self.SETTING_LOCAL_MODE_MEDIA_LOC = "local_mode_media"

		# default values
		self.SETTINGS_FILENAME = os.path.join( DIR_USERDATA, "settings.txt" )
		self.START_MODE_SMB = __language__(550)
		self.START_MODE_LOCAL = __language__(551)
		self.START_MODE_ONLINE = __language__(552)
		self.START_MODE_MENU = __language__(553)

		# order if important as a lookup index is used
		self.startModeNames = [self.START_MODE_MENU, self.START_MODE_SMB, self.START_MODE_LOCAL, self.START_MODE_ONLINE]

		self.SETTINGS_DEFAULTS = {
			self.SETTING_SMB_USE : True,
			self.SETTING_SMB_PATH : "smb://user:pass@OFFICE",
			self.SETTING_SMB_PC_IP : "",						# empty so smb details incomplete by default
			self.SETTING_SMB_FILENAME :  "collection.xml",
			self.SETTING_START_MODE : 0,						# menu
			self.SETTING_SMB_COLLECTION_DIR : "EXPORT",
			self.SETTING_SMB_IMAGES_DIR : "IMAGES",
			self.SETTING_SMB_DVDPRO_SHARE : "DVD Profiler",
			self.SETTING_SMB_MOVIES_SHARE : "My Videos",
			self.SETTING_CHECK_UPDATE : False,					# No
			self.SETTING_LOCAL_MODE_MEDIA_LOC : "F:\Videos"
			}

		self.settings = {}
		self._initSettings(forceReset=False)
		# check for script update
		if self.settings[self.SETTING_CHECK_UPDATE]:	# check for update ?
			scriptUpdated = updateScript(False, False)
		else:
			scriptUpdated = False
		if not scriptUpdated:
			self.reset()

		debug("< DVDProfiler().init ready=%s" % self.ready)

	#################################################################################################################
	def onInit( self ):
		debug("> onInit() isStartup=%s" % self.isStartup)
		if self.isStartup:
			dialogProgress.create(__scriptname__, __language__(249))
			self.setupDisplay()
			self.setupTitles()
			dialogProgress.close()

			self.isStartup = False
			self.ready = True

		debug("< onInit()")


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
				debug( "setting reset: " + key + " = " + str(defaultValue))

		if changed or not fileExist(self.SETTINGS_FILENAME):
			saveFileObj(self.SETTINGS_FILENAME, self.settings)

		debug( "< _initSettings() changed="+str(changed))
		return changed

	##############################################################################################
	def isReady(self):
		return self.ready

	###################################################################################################
	def onAction(self, action):
		try:
			buttonCode =  action.getButtonCode()
			actionID   =  action.getId()
		except: return

		if actionID in EXIT_SCRIPT or buttonCode in EXIT_SCRIPT:
			self.close()

		if not self.ready:
			return
		self.ready = False
		if actionID in CONTEXT_MENU or buttonCode in CONTEXT_MENU:
			debug("> CONTEXT_MENU")
			self.fadeBackground(True)
			success = self.mainMenu()             # restart ?
			self.fadeBackground(False)
			if success == QUIT_SCRIPT:
				self.close()
			elif success:
				if not self.startup():
					if self.onlineAliasData:		# gforce back from online alias
						self.ready = True
						self.onAction(ACTION_B)
					else:
						self.reset()
						self.setupDisplay()
						self.setupTitles()
				else:
					self.setupDisplay()
					self.setupTitles()
			debug("< CONTEXT_MENU")
		elif actionID in CLICK_X or buttonCode in CLICK_X:
			debug("> CLICK_X")
			if self.isOnlineOnly or self.onlineAliasData:
				aliasData = ManageOnlineCollection().ask()
				if aliasData:							# only action/save if alias selected
					self.onlineAliasData = aliasData
					if not self.startup():
						self.reset()
					self.setupDisplay()
					self.setupTitles()

			elif not self.onlineAliasData:
				self.doFilters()
			debug("< CLICK_X")
		elif actionID in CLICK_Y or buttonCode in CLICK_Y:
			debug("> CLICK_Y")
			if not self.onlineAliasData:
				colNo = self.lastCollNo
			else:
				colNo = self.lastOnlineCollNo

			self.fadeBackground(True)
			title = self.dvdCollection.getDVDKey(colNo)[self.dvdCollection.KEYS_DATA_SORTTITLE]
			imdbwin = IMDbWin("script-bbb-imdb.xml", DIR_HOME, "Default")
			imdbwin.ask(title)
			self.fadeBackground(False)
			debug("< CLICK_Y")
		elif actionID in CLICK_B or buttonCode in CLICK_B:			        # B btn
			debug("> CLICK_B")
			if not self.isOnlineOnly:
				if self.selectedGenres or self.selectedTags:
					self.selectedGenres = []
					self.selectedTags = []
					self.setupTitles()				# setup lists
				elif self.onlineAliasData:
					# online - back to own collection
					self.onlineAliasData = []
					if not self.startup():
						self.reset()
					self.setupDisplay()
					self.setupTitles()				# setup lists
			debug("< CLICK_B")

		self.ready = True

	##############################################################################################
	def onClick(self, controlID):
		self.ready = False

		if controlID == self.getControl(self.CLST_TITLES_LIST).getId():				# select title
			debug("titlesCL")
			# if selecting same title, attempt playback
			colNo = self.getControl(self.CLST_TITLES_LIST).getSelectedItem().getLabel2()
			if not self.onlineAliasData and colNo == self.lastCollNo:
				self.playback()
			elif not self.showDVD():
				self.reset()
		elif controlID == self.getControl(self.CBTN_SORT_BY).getId():				# sort by column btn
			debug("sortColCB")
			self.sortByTitle = not self.sortByTitle
			if not self.setupTitles():
				self.reset()
		elif controlID == self.getControl(self.CBTN_SORT_ORDER).getId():				# sort asc/desc btn
			debug("sortDirCB")
			self.sortAsc = not self.sortAsc
			if not self.setupTitles():
				self.reset()
		elif controlID == self.getControl(self.CBTN_FILTER).getId():				# filters btn
			debug("filtersCB")
			self.doFilters()

		self.ready = True

	###################################################################################################################
	def onFocus(self, controlID):
		debug("onFocus(): controlID=%i" % controlID)

	###################################################################################################
	def playback(self):
		debug("> playback()")
		playbackPath = ''

		try:
			location = self.dvdCollection.getDVDData(self.dvdCollection.LOCATION)[0]
			debug("location=%s" % location);
			if not location: raise
		except:
			dialogOK(__language__(210),__language__(211))
		else:
			if self.settings[self.SETTING_SMB_USE]:		# SMB enabled, playback from SMB
				debug("use SMB for playback")
				playbackPath = "%s/%s/%s" % (self.settings[self.SETTING_SMB_PATH], \
										self.settings[self.SETTING_SMB_MOVIES_SHARE],
										location)
			else:
				# local only mode, assume location is a local path
				debug("local playback")
				playbackPath = os.path.join(self.settings[self.SETTING_LOCAL_MODE_MEDIA_LOC], location)
				if not fileExist(playbackPath):
					dialogOK(__language__(210),__language__(240), playbackPath)
					playbackPath = ''

		if playbackPath:
			debug("playbackPath= " + playbackPath)
			result = xbmc.Player().play(playbackPath)
			if not xbmc.Player().isPlaying():
				dialogOK(__language__(210),__language__(212), playbackPath)

		debug("< playback()")
	
	###################################################################################################
	def reset(self):
		debug("> reset()")
		self.dvdCollection = None
		self.sortByTitle = True
		self.sortAsc = True
		self.lastCollNo = 0
		self.lastOnlineCollNo = 0
		self.remote = None
		self.onlineAliasData = []
		self.selectedGenres = {}
		self.selectedTags = {}
		self.localCollectionFilename = COLLECTION_XML_FILE

		if not self.startupMenu():
			self.ready = False
			self.close()
		else:
			self.ready = True
		debug("< reset()")


	##############################################################################################
	def startupMenu(self):
		debug("> startupMenu()")
		success = False
		menu = [__language__(500)] + self.startModeNames[1:]      # excl Use Menu as we need to pick a mode

		startMode = self.settings[self.SETTING_START_MODE]
		while not success:
			self.isOnlineOnly = False
			self.onlineAliasData = []

			if startMode == 0:                            		# self.START_MODE_MENU:
				startMode = xbmcgui.Dialog().select("%s: %s" % (__scriptname__,__language__(553)), menu)
			
			# start according to startupMode
			if startMode <= 0:
				break
			if startMode == 1:								    # SMB
				self.settings[self.SETTING_SMB_USE] = True
				success = self.startup()
			elif startMode == 2:							    # LOCAL
				self.settings[self.SETTING_SMB_USE] = False
				success = self.startup()
			elif startMode == 3:							    # ONLINE
				self.settings[self.SETTING_SMB_USE] = False
				self.isOnlineOnly = True
				self.onlineAliasData = ManageOnlineCollection().ask()
				if self.onlineAliasData:
					success = self.startup()

			if not success:
				startMode = 0									# self.START_MODE_MENU

		debug("< startupMenu() success=%s" % success)
		return success

	##############################################################################################
	def startup(self):
		debug("> startup()")
		success = False
		self.dvdCollection = None
		self.sortByTitle = True
		self.sortAsc = True

		if self.onlineAliasData:
			debug("ONLINE collection")
			self.dvdCollection = DVDCollectionOnline(self.onlineAliasData)
			if self.dvdCollection and self.dvdCollection.getCollectionSize() > 0:
				success = True
		elif self.settings[self.SETTING_SMB_USE]:
			debug("SMB collection")
			if self.startupSMB() and self.settings[self.SETTING_SMB_USE]:	# continue if not been disabled
				self.dvdCollection = DVDCollectionXML(self.localCollectionFilename)
				if self.dvdCollection and self.dvdCollection.getCollectionSize() > 0:
					success = True
				else:
					dialogOK(__language__(101),__language__(102))
		else:
			debug("LOCAL collection")
			if fileExist(self.localCollectionFilename):
				self.dvdCollection = DVDCollectionXML(self.localCollectionFilename)
				if self.dvdCollection and self.dvdCollection.getCollectionSize() > 0:
					success = True
			if not success:
				dialogOK(__language__(101),__language__(103), self.localCollectionFilename)

		debug("< startup() success=%s" % success)
		return success

	##############################################################################################
	def _checkSMBSettings(self):
		success = False
		try:
			if self.settings[self.SETTING_SMB_PATH] and \
					self.settings[self.SETTING_SMB_PC_IP] and \
					self.settings[self.SETTING_SMB_FILENAME] and \
					self.settings[self.SETTING_SMB_COLLECTION_DIR] and \
					self.settings[self.SETTING_SMB_IMAGES_DIR] and \
					self.settings[self.SETTING_SMB_DVDPRO_SHARE] :
				success = True
		except: pass
		debug("_checkSMBSettings() success="+str(success))
		return success

	##############################################################################################
	def startupSMB(self, forceConfig=False):
		debug("> startupSMB() forceConfig="+str(forceConfig))
		success = False

		while not success:
			if forceConfig or not self._checkSMBSettings():
				if not forceConfig:
					dialogOK(__language__(959),__language__(105))
				self.configSMB()
				forceConfig = False
				continue									# loop to re-check SMB setup

			if not self.settings[self.SETTING_SMB_USE]:		# SMB disabled
				break

			# check SMB
			smbPath = "%s/%s" % (self.settings[self.SETTING_SMB_PATH], self.settings[self.SETTING_SMB_DVDPRO_SHARE])
			self.remote, remoteInfo = smbConnect(self.settings[self.SETTING_SMB_PC_IP], smbPath)
			if self.remote and remoteInfo:
				smbPath = self.makeDVDProSMBPath()
				# if no collecttin file, or newer exists, fetch from SMB
				if not fileExist(self.localCollectionFilename) or \
						isNewSMBFile(smbPath, self.localCollectionFilename, \
							self.remote, self.settings[self.SETTING_SMB_PC_IP]):
					success = self.fetchCollectionSMB(True)
					if not success:
						title = __language__(953)
				else:
					success = True

			# report failure reason
			if not success:
				if xbmcgui.Dialog().yesno(title, __language__(214)):
					forceConfig = True
				else:
					self.settings[self.SETTING_SMB_USE] = False
					break

		debug("< startupSMB() success=%s" % success)
		return success

	##############################################################################################
	def setupDisplay(self):
		debug("> setupDisplay()")

		# version
		self.getControl(self.CLBL_SCRIPT_VER).setLabel("v"+__version__)

		# datasource
		if self.onlineAliasData:
			user, host = self.onlineAliasData
			text = "%s (%s)" % (user, host)
		elif self.settings[self.SETTING_SMB_USE]:
			text = self.settings[self.SETTING_SMB_PC_IP]
		else:
			text = self.START_MODE_LOCAL
		self.getControl(self.CLBL_DATASOURCE).setLabel(text)

		# TITLE
		self.getControl(self.CLBL_TITLE).setLabel("")
#		self.getControl(self.CLBL_DESC).setLabel("")
		self.getControl(self.CLBL_MENU_BTN).setLabel(__language__(431))			# menu
		self.getControl(self.CLBL_Y_BTN).setLabel(__language__(432))			# imdb
		self.getControl(self.CLBL_BACK_BTN).setLabel(__language__(500))			# exit

		if self.isOnlineOnly or self.onlineAliasData:
			text = __language__(427)    # select
		else:
			text = __language__(428)    # play
		self.getControl(self.CLBL_A_BTN).setLabel(text)

		# " X - ONLINE or FILTERS - depends on startup mode"
		if self.isOnlineOnly or self.onlineAliasData:
			text = __language__(433)    # alias
		else:
			text = __language__(434)    # filters
		self.getControl(self.CLBL_X_BTN).setLabel(text)
		self.getControl(self.CLBL_B_BTN).setVisible(False)

		debug("< setupDisplay()")

	###################################################################################################
	def fadeBackground(self, fade):
		self.getControl(self.CGRP_HEADER).setEnabled(not fade)

	###################################################################################################
	def doFilters(self):
		debug("> doFilters()")

		self.fadeBackground(True)

		# make dict - set enabled items from last time filters was shown
		genresDict = {}
		for genre in self.dvdCollection.filterGenres:
			genresDict[genre] = (genre in self.selectedGenres)

		tagsDict = {}
		for tag in self.dvdCollection.filterTags:
			tagsDict[tag] = (tag in self.selectedTags)

		filters = Filters("script-dvdpro-filters.xml", DIR_HOME, "Default")
		self.selectedGenres, self.selectedTags = filters.ask(genresDict, tagsDict)
		# ALL is same as no filter selecting for genres.
		if len(self.selectedGenres) == len(self.dvdCollection.filterGenres):
			self.selectedGenres = []
		del filters

		self.setupTitles()		# setup lists
		self.fadeBackground(False)
		debug("< doFilters()")

	###################################################################################################
	def updateFilterBtn(self, filterCount):
		debug("> updateFilterBtn() filterCount=%s" % filterCount)
		isEnabled = ( not self.onlineAliasData and self.dvdCollection.keys != {} )
		ctrl = self.getControl(self.CBTN_FILTER)
		ctrl.setVisible(isEnabled)
		ctrl.setEnabled(isEnabled)
		if isEnabled:
			text = "%s: %s\\%s" % (__language__(434), filterCount, len(self.dvdCollection.keys))
			ctrl.setLabel(text)
		debug("< updateFilterBtn()")

	##############################################################################################
	def setupTitles(self):
		debug("> setupTitles()")
#		xbmcgui.lock()

		if self.sortByTitle:
			text = __language__(423)    # sort by #
		else:
			text = __language__(424)    # sort by title
		self.getControl(self.CBTN_SORT_BY).setLabel(text)

		if self.sortAsc:
			text = __language__(425)    # desc
		else:
			text = __language__(426)    # asc
		self.getControl(self.CBTN_SORT_ORDER).setLabel(text)

		filterCount = self.loadTitlesCL(self.sortByTitle, self.sortAsc)
		self.updateFilterBtn(filterCount)
		if filterCount:
			success = self.showDVD()
		else:
			self.clearControls()
			success = True

		# update A btn according to online status
		if self.isOnlineOnly or self.onlineAliasData:
			text = __language__(427)    # select
		else:
			text = "%s/%s" % (__language__(427),__language__(428))    # select/play
		self.getControl(self.CLBL_A_BTN).setLabel(text)

		# update B btn label
		if self.selectedGenres or self.selectedTags:
			text = __language__(429)    # clear filters
		elif not self.isOnlineOnly and self.onlineAliasData:
			text = __language__(430)    # My profile
		else:
			text = ''
		self.getControl(self.CLBL_B_BTN).setLabel(text)
		self.getControl(self.CLBL_B_BTN).setVisible((text != ''))
#		xbmcgui.unlock()

		debug("< setupTitles()")
		return success

	###################################################################################################
	def loadTitlesCL(self, sortByTitles=True, sortAsc=True):
		debug ("> loadTitlesCL() sortByTitles=%s sortAsc=%s" % (sortByTitles, sortAsc))

		def sortItemsAsc(x, y):
			return cmp(x[1],y[1])

		def sortItemsDesc(x, y):
			return cmp(y[1],x[1])

		self.getControl(self.CLST_TITLES_LIST).reset()

		# FILTERS -  make a dict just containing those matching filter
		filterDict = {}
		if self.onlineAliasData or not self.selectedGenres and not self.selectedTags:
			# no filters selected  - match ALL
			debug("match ALL")
			filterDict = self.dvdCollection.keys
		else:
			# examine filters - for each dvd
			debug("using filters")
			for key, data in self.dvdCollection.keys.items():
				add = False
				# match genre or incl. ALL if no genres selected
				genres = data[self.dvdCollection.KEYS_DATA_GENRES]
				if not self.selectedGenres:		# no selected genres also == ALL selected
					add = True
				elif not genres:
					# dvd has no genres, incl only when 'no genres' selected
					if self.dvdCollection.GENRE_NONE in self.selectedGenres:
						add = True
				else:
					# examine all genres for this dvd
					for genre in genres:
						if genre in self.selectedGenres:
							add = True
							break		# matched, stop processing dvd genres

				# if added, and dvd has tags, sub filter against tags
				if add and self.selectedTags:
					tags = data[self.dvdCollection.KEYS_DATA_TAGS]
					# dvd has tags, check for match
					add = False			# reset, as it must now also have one of the selected tags
					# examine all tags for this dvd
					for tag in tags:
						if tag in self.selectedTags:
							add = True
							break		# matched, stop processing dvd tags

				if add:
					filterDict[int(key)] = data

		if filterDict:
			self.getControl(self.CLBL_TITLE).setLabel(__language__(249))
			selectedPos = 0
			if not sortByTitles:
				sortList = filterDict.keys()
				sortList.sort()
				if not sortAsc:
					sortList.reverse()

				# [collnum]
				ctrl = self.getControl(self.CLST_TITLES_LIST)
				for i in range(len(sortList)):
					collnum = sortList[i]
					title = self.dvdCollection.getDVDKey(collnum)[self.dvdCollection.KEYS_DATA_SORTTITLE]
					# check for Location in tags, then show icon
					try:
						tags = self.dvdCollection.getDVDKey(collnum)[self.dvdCollection.KEYS_DATA_TAGS]
						idx = tags.index(self.dvdCollection.LOCATION)
						img = FILM_FILENAME
					except:
						img = ''

					ctrl.addItem(xbmcgui.ListItem(title, str(collnum), img, img))
					if not self.onlineAliasData and collnum == self.lastCollNo:
						selectedPos = i
			else:
				sortList = filterDict.items()
				if sortAsc:
					sortList.sort(sortItemsAsc)
				else:
					sortList.sort(sortItemsDesc)

				# [(collnum, ['sorttitle','id',title,genres,tags)]
				ctrl = self.getControl(self.CLST_TITLES_LIST)
				for i in range(len(sortList)):
					collnum = sortList[i][0]
					title = sortList[i][1][self.dvdCollection.KEYS_DATA_SORTTITLE]
					# check for Location in tags, then show icon
					try:
						tags = sortList[i][1][self.dvdCollection.KEYS_DATA_TAGS]
						idx = tags.index(self.dvdCollection.LOCATION)
						img = FILM_FILENAME
					except:
						img = ''
					ctrl.addItem(xbmcgui.ListItem(title, str(collnum), img, img))
					if not self.onlineAliasData and collnum == self.lastCollNo:
						selectedPos = i

			self.getControl(self.CLST_TITLES_LIST).selectItem(0)

		filterCount = len(filterDict)
		debug ("< loadTitlesCL() filerCount=%s" % filterCount)
		return filterCount

	##############################################################################################
	def makeDVDProSMBPath(self):
		return "%s/%s/%s/%s" % (self.settings[self.SETTING_SMB_PATH], \
								self.settings[self.SETTING_SMB_DVDPRO_SHARE],
								self.settings[self.SETTING_SMB_COLLECTION_DIR], \
								self.settings[self.SETTING_SMB_FILENAME])

	##############################################################################################
	def clearControls(self, clearTitles=False):
		debug("> clearControls() clearTitles=%s" % clearTitles)
		self.getControl(self.CLBL_TITLE).setLabel('')
#		self.getControl(self.CLBL_DESC).setLabel('')
		self.getControl(self.CI_COVER).setImage(NOIMAGE_FILENAME)
#		self.getControl(self.CI_COVER).setImage('')
		self.getControl(self.CTB_DETAILS).reset()
		self.getControl(self.CLST_CAST_LIST).reset()
		if clearTitles:
			self.getControl(self.CLST_TITLES_LIST).reset()
			self.getControl(self.CLBL_DATASOURCE).setLabel('')
		debug("< clearControls()")

	###################################################################################################
	def fetchCollectionSMB(self, forceNew=False):
		debug ("> fetchCollectionSMB() forceNew="+str(forceNew))

		if forceNew:
			self.deleteLocalCollection()
			success = False
		else:
			success = fileExist(self.localCollectionFilename)

		if not success:
			dialogProgress.create(__language__(215), __language__(200))
			# remove any old parsed files
			deleteFile(KEYS_FILE)
			deleteFile(COLLECTION_FLAT_FILE)

			# fetch from SMB
			smbPath = self.makeDVDProSMBPath()
			success = smbFetchFile(smbPath, self.localCollectionFilename, \
							self.remote, self.settings[self.SETTING_SMB_PC_IP])
			dialogProgress.close()
		else:
			debug("local xml already exists")
		debug ("< fetchCollectionSMB() success="+str(success))
		return success

	###################################################################################################
	def deleteLocalCollection(self):
		debug("deleteLocalCollection()")
		# remove any old parsed files
		deleteFile(self.localCollectionFilename)
		deleteFile(KEYS_FILE)
		deleteFile(COLLECTION_FLAT_FILE)

	###################################################################################################
	def showDVD(self):
		debug ("> showDVD()")

		ctrl = self.getControl(self.CLST_TITLES_LIST)
		selectedPos = ctrl.getSelectedPosition()
		collNum = ctrl.getSelectedItem().getLabel2()
		if not self.onlineAliasData:
			self.lastCollNo = collNum
		else:
			self.lastOnlineCollNo = collNum
		debug("selectedPos=%s collNum=%s lastCollNo=%s lastOnlineCollNo=%s" % \
			  (selectedPos, collNum, self.lastCollNo, self.lastOnlineCollNo))

		self.clearControls()

		# load data into controls
		self.getControl(self.CLBL_TITLE).setLabel(__language__(200))
		success = self.dvdCollection.parseDVD(collNum)
		if not success:
			self.getControl(self.CLBL_TITLE).setLabel("Failed to parse DVD")
			debug ("< showDVD() failed to parseDVD")
			return False

		#######################################################
		# extract text from object which could be a list of lists of strings etc
		def _getItemsText(key, joinCh=","):
#			print "key=%s" % key
			try:
				data = self.dvdCollection.getDVDData(key)
				if not data:
					return notAvail

#				print "type=%s data=%s" % (type(data), data)
				if isinstance(data,list):
					if isinstance(data[0], list):			# a list of lists
						text = ''
						for item in data:
							text += joinCh.join(item)		# join elements of sublist
							text += ';'
						text = text[:-1]					# remove end ch
					else:
						text = joinCh.join(data)
				else:
					if data.lower() == 'true':
						text = __language__(350)			# yes
					elif data.lower() == 'false':
						text = __language__(351)			# no
					else:
						text = data
			except:
				debug("_getItemsText() except doing key %s" % key)
				text = notAvail
			return text

		#######################################################

		xbmcgui.lock()
		self.getControl(self.CLBL_TITLE).setLabel(self.dvdCollection.getDVDKey(collNum)[self.dvdCollection.KEYS_DATA_SORTTITLE])

		# cast list
		debug("build cast list")
		ctrl = self.getControl(self.CLST_CAST_LIST)
		ctrl.addItem(xbmcgui.ListItem(__language__(417)))
		ctrl.addItem(xbmcgui.ListItem(__language__(418),__language__(419)))
		try:
			for items in self.dvdCollection.getDVDData(self.dvdCollection.ACTORS):
				if items:
					if not isinstance(items,str):
						itemCount = len(items)
						if itemCount == 1:
							name = items[0]
							role = ''
						else:
							name = ' '.join(items[0:itemCount-1])
							role = items[-1]
					else:
						name = items
						role = ''
					ctrl.addItem(xbmcgui.ListItem(name, role))
		except:
			ctrl.addItem(xbmcgui.ListItem('-'))
		else:
			debug("cast done OK")

		# append credits
		debug("build credits")
		ctrl.addItem(xbmcgui.ListItem(__language__(420)))
		ctrl.addItem(xbmcgui.ListItem(__language__(421),__language__(422)))
		try:
			for items in self.dvdCollection.getDVDData(self.dvdCollection.CREDITS):
				if items:
					if not isinstance(items,str):
						itemCount = len(items)
						if itemCount == 1:
							name = items[0]
							role = ''
						else:
							name = ' '.join(items[0:itemCount-1])
							role = items[-1]
					else:
						name = items
						role = ''
					ctrl.addItem(xbmcgui.ListItem(name, role))
		except:
			ctrl.addItem(xbmcgui.ListItem('-'))
		else:
			debug("credits done OK")

		# overview (also incorp additional information)
		debug("build OVERVIEW")
		details = self.getControl(self.CTB_DETAILS)
		details.reset()
		text = ''
		notAvail = '-'

		try:
			text += _getItemsText(self.dvdCollection.OVERVIEW)
		except: text += notAvail

		text += '\n\n%s:  ' % __language__(401)    # additional information

		# only show 'slot' if used
		try:
			text += '\n%s:  %s' % (__language__(436), _getItemsText(self.dvdCollection.SLOT))
		except: pass

		try:
			text += '\n%s:  ' % __language__(402)
			text += _getItemsText(self.dvdCollection.RATING)
		except: text += notAvail

		try:
			text += '\n%s:  ' % __language__(403)
			mins = _getItemsText(self.dvdCollection.RUNNINGTIME)
			if mins and mins != '-' and find(mins,'min') == -1:
				mins += ' mins'
			text += mins
		except: text += notAvail

		try:
			text += '\n%s:  ' % __language__(404)
			text += _getItemsText(self.dvdCollection.REGION)
		except: text += notAvail

		try:
			text += '\n%s:  '  % __language__(405)
			text += _getItemsText(self.dvdCollection.PRODYEAR)
		except: text += notAvail

		try:
			text += '\n%s:  ' % __language__(406)
			text += _getItemsText(self.dvdCollection.RELEASED)
		except: text += notAvail

		try:
			text += '\n%s:  ' % __language__(407)
			text += _getItemsText(self.dvdCollection.GENRE)
		except: text += notAvail

		text += '\n%s: ' % __language__(435)		# video
		if not self.onlineAliasData:
			try:
				text += ' %s: ' % __language__(408)
				text += _getItemsText(self.dvdCollection.VIDEOFORMAT_ASPECT)
			except: text += notAvail

			try:
				text += ' %s: ' % __language__(409)
				text += _getItemsText(self.dvdCollection.VIDEOFORMAT_STD)
			except: text += notAvail

			try:
				text += ' %s: ' % __language__(410)
				value = _getItemsText(self.dvdCollection.VIDEOFORMAT_IS16x9)
				if value.lower() == 'true':
					value = 'Yes'
				else:
					value = 'No'
				text += value
			except: text += notAvail
		else:
			try:
				text += _getItemsText(self.dvdCollection.VIDEOFORMAT)
			except: text += notAvail

		try:
			text += '\n%s:  ' % __language__(411)
			text += _getItemsText(self.dvdCollection.AUDIOFORMAT)
		except: text += notAvail

		try:
			text += '\n%s:  ' % __language__(412)
			text += _getItemsText(self.dvdCollection.STUDIO)
		except: text += notAvail

		try:
			text += '\n%s:  ' % __language__(413)
			text += _getItemsText(self.dvdCollection.REVIEW)
		except: text += notAvail

		try:
			text += '\n%s:  ' % __language__(414)
			text += _getItemsText(self.dvdCollection.FEATURES)
		except: text += notAvail

		try:
			text += '\n%s:  ' % __language__(415)
			text += _getItemsText(self.dvdCollection.EASTEREGGS)
		except: text += notAvail

		try:
			text += '\n%s:  ' % __language__(416)
			text += _getItemsText(self.dvdCollection.LOCATION)
		except: text += notAvail

		details.setText(text)

		# cover image
		id = self.dvdCollection.getDVDKey(int(collNum))[self.dvdCollection.KEYS_DATA_ID]
		fn = self.fetchCover(id)
		self.getControl(self.CI_COVER).setImage(fn)
		self.getControl(self.CI_COVER).setVisible(True)
		self.setFocus(self.getControl(self.CLST_TITLES_LIST))
		xbmcgui.unlock()
		debug ("< showDVD() collNum: %s" % collNum)
		return True

	###################################################################################################
	# fetch cover from same site collection held on
	###################################################################################################
	def fetchCover(self, coverID):
		debug ("> fetchCover() coverID=" + coverID)

		coverFilename = coverID + 'f.jpg'
		localFile = os.path.join(DIR_IMG_CACHE, coverFilename)
		debug("localFile="+ localFile)
		success = fileExist(localFile)
		if success:
			debug("cover file exists ")
		else:
			debug("cover file NOT exist ")
			if self.onlineAliasData:
				alias, aliasURL = self.onlineAliasData
				if aliasURL == BASE_URL_INTER:
					url = "%s/cgi-bin/data/myprofiler/images/%s" % (aliasURL, coverFilename)
				else:
					url = "%s/mpimages/%s/%s" % (aliasURL, coverFilename[:2],coverFilename)
#				dialogProgress.create(__language__(216), coverFilename)
				success = fetchCookieURL(url, localFile, isBinary=True)
#				dialogProgress.close()
			elif self.settings[self.SETTING_SMB_USE]:
				smbPath = "%s/%s/%s/%s" % (self.settings[self.SETTING_SMB_PATH],
										   self.settings[self.SETTING_SMB_DVDPRO_SHARE],
										   self.settings[self.SETTING_SMB_IMAGES_DIR],
										   coverFilename)
				success = smbFetchFile(smbPath, localFile, self.remote, self.settings[self.SETTING_SMB_PC_IP])
			else:
				success = False

			if not success:
				localFile = NOIMAGE_FILENAME

		debug("< fetchCover() success=%s" % success)
		return localFile

	###################################################################################################
	def fetchAllImages(self):
		debug("> fetchAllImages()")

		dialogProgress.create(__language__(303))
		MAX = self.dvdCollection.getCollectionSize()
		count = 0
		for collNum, data in self.dvdCollection.keys.items():
			dvdKeys = self.dvdCollection.getDVDKey(int(collNum))
			id = dvdKeys[self.dvdCollection.KEYS_DATA_ID]
			title = dvdKeys[self.dvdCollection.KEYS_DATA_SORTTITLE]
			dialogProgress.update(int(count*100.0/MAX), title)
			self.fetchCover(id)
			count += 1
			if dialogProgress.iscanceled(): break

		dialogProgress.close()
		debug("< fetchAllImages(")

	###################################################################################################
	def mainMenu(self):
		debug("> mainMenu()")

		# menu choices
		MENU_VIEW_IMDB = __language__(503)
		MENU_VIEW_ONLINE = __language__(504)
		MENU_VIEW_OWN = __language__(505)
		MENU_FILTERS = __language__(506)
		MENU_FETCH_COLL = __language__(507)
		MENU_FETCH_ALL_IMAGES = __language__(508)
		MENU_CONFIG_MENU = __language__(502)

		menuOptions = [
			__language__(500),	# exit
			MENU_VIEW_IMDB,
			MENU_VIEW_ONLINE,
			MENU_VIEW_OWN,
			MENU_FILTERS,
			MENU_FETCH_COLL,
			MENU_FETCH_ALL_IMAGES,
			MENU_CONFIG_MENU
			]

		if self.isOnlineOnly or not self.onlineAliasData:
			menuOptions.remove(MENU_VIEW_OWN)
		if self.isOnlineOnly or not self.remote:
			menuOptions.remove(MENU_FETCH_COLL)
			menuOptions.remove(MENU_FETCH_ALL_IMAGES)
		if self.isOnlineOnly or self.onlineAliasData:
			menuOptions.remove(MENU_FILTERS)

		# show this dialog and wait until it's closed
		restart = False
		selectedPos = 0	# start on exit
		while not restart:
			selectedPos = xbmcgui.Dialog().select(__language__(501), menuOptions)
			if selectedPos <= 0:				# exit selected
				break

			elif menuOptions[selectedPos] == MENU_VIEW_IMDB:
				if not self.onlineAliasData:
					colNo = self.lastCollNo
				else:
					colNo = self.lastOnlineCollNo
				title = self.dvdCollection.getDVDKey(colNo)[self.dvdCollection.KEYS_DATA_SORTTITLE]
				imdbwin = IMDbWin("script-bbb-imdb.xml", DIR_HOME, "Default")
				imdbwin.ask(title)
			elif menuOptions[selectedPos] == MENU_VIEW_ONLINE:
				aliasData = ManageOnlineCollection().ask()
				if aliasData:							# if text entered
					self.onlineAliasData = aliasData
					restart = True
			elif menuOptions[selectedPos] == MENU_VIEW_OWN:
				self.onlineAliasData = []
				restart = True
			elif menuOptions[selectedPos] == MENU_FETCH_COLL:
				restart = self.fetchCollectionSMB(True)		# force new fetch
			elif menuOptions[selectedPos] == MENU_FILTERS:
				self.doFilters()
				break
			elif menuOptions[selectedPos] == MENU_CONFIG_MENU:
				restart = self.settingsMenu()
			elif menuOptions[selectedPos] == MENU_FETCH_ALL_IMAGES:
				self.fetchAllImages()

		debug ("< mainMenu() restart: " + str(restart))
		return restart


	###################################################################################################
	def settingsMenu(self):
		debug("> settingsMenu() init()")

		# menu choices
		OPT_VIEW_README = __language__(521)
		OPT_VIEW_CHANGELOG = __language__(522)
		OPT_UPDATE_SCRIPT = __language__(523)
		OPT_CHECK_SCRIPT_UPDATE = __language__(524)
		OPT_CLEAR_CACHE = __language__(525)
		OPT_START_MODE = __language__(526)
		OPT_CONFIG_SMB = __language__(527)
		OPT_LOCAL_MODE_MEDIA_LOC = __language__(528)

		def _makeMenu():
			menu = [xbmcgui.ListItem(__language__(500))]	# exit
			menu.append(xbmcgui.ListItem(OPT_CONFIG_SMB))
			if self.settings[self.SETTING_CHECK_UPDATE]:
				value = __language__(350)
			else:
				value = __language__(351)
			menu.append(xbmcgui.ListItem(OPT_CHECK_SCRIPT_UPDATE, value))
			menu.append(xbmcgui.ListItem(OPT_UPDATE_SCRIPT))
			menu.append(xbmcgui.ListItem(OPT_CLEAR_CACHE))
			# translate SETTING_START_MODE into a language name
			name = self.startModeNames[self.settings[self.SETTING_START_MODE]]
			menu.append(xbmcgui.ListItem(OPT_START_MODE, name))
			menu.append(xbmcgui.ListItem(OPT_LOCAL_MODE_MEDIA_LOC, self.settings[self.SETTING_LOCAL_MODE_MEDIA_LOC]))
			menu.append(xbmcgui.ListItem(OPT_VIEW_README))
			menu.append(xbmcgui.ListItem(OPT_VIEW_CHANGELOG))
			return menu

		# show this dialog and wait until it's closed
		selectedPos = 0
		restart = False
		title = "%s: %s" % (__language__(0), __language__(502))
		while restart == False:
			menu = _makeMenu()
			selectDialog = DialogSelectXML("script-bbb-dialogselect.xml", DIR_HOME, "Default")
			selectedPos, action = selectDialog.ask(title, menu, selectedPos)
			del selectDialog
			if action in EXIT_SCRIPT or selectedPos <= 0:				# exit selected
				break

			selectedOpt = menu[selectedPos].getLabel()
			if selectedOpt == OPT_CONFIG_SMB:
				self.configSMB()
			elif selectedOpt == OPT_CHECK_SCRIPT_UPDATE:
				self.settings[self.SETTING_CHECK_UPDATE] = xbmcgui.Dialog().yesno( __language__(502), OPT_CHECK_SCRIPT_UPDATE )
				saveFileObj(self.SETTINGS_FILENAME, self.settings)
			elif selectedOpt == OPT_UPDATE_SCRIPT:
				if updateScript(False, True):							# never silent from config menu
					xbmc.output("update issued - exit script")
					restart = QUIT_SCRIPT
			elif selectedOpt == OPT_CLEAR_CACHE:
				restart = self.clearCache()
			elif selectedOpt == OPT_START_MODE:
				menuStartMode = [ __language__(500) ] + self.startModeNames
				selectedPosStartMode = xbmcgui.Dialog().select(__language__(527), menuStartMode)
				if selectedPosStartMode > 0:
					# translate selectedPos into startMode
					selectedPosStartMode -=1 # allow for exit opt
					self.settings[self.SETTING_START_MODE] = selectedPosStartMode
					saveFileObj(self.SETTINGS_FILENAME, self.settings)
			elif selectedOpt == OPT_VIEW_README:
				fn = getReadmeFilename()
				doc = readFile(fn)
				if not doc:
					doc = "Readme not found: " + fn
				tbd = TextBoxDialogXML("DialogScriptInfo.xml", DIR_HOME, "Default")
				tbd.ask(OPT_VIEW_README, doc)
				del tbd
			elif selectedOpt == OPT_VIEW_CHANGELOG:
				fn = os.path.join(DIR_HOME, "Changelog.txt")
				doc = readFile(fn)
				if not doc:
					doc = "Changelog not found: " + fn
				tbd = TextBoxDialogXML("DialogScriptInfo.xml", DIR_HOME, "Default")
				tbd.ask(OPT_VIEW_CHANGELOG, doc)
				del tbd
			elif selectedOpt == OPT_LOCAL_MODE_MEDIA_LOC:
				value = self.settings[self.SETTING_LOCAL_MODE_MEDIA_LOC]
				value = doKeyboard(value, OPT_LOCAL_MODE_MEDIA_LOC)
				if value:
					self.settings[self.SETTING_LOCAL_MODE_MEDIA_LOC] = value
					saveFileObj(self.SETTINGS_FILENAME, self.settings)

		debug ("< settingsMenu().ask() restart=%s" % restart)
		return restart

	#################################################################################################################
	# MENU ITEM - config SMB PC connection
	#################################################################################################################
	def configSMB(self):
		debug("> configSMB()")

		MENU_OPT_SMB_USE = __language__(540)
		MENU_OPT_SMB_PATH = __language__(541)
		MENU_OPT_SMB_PC_IP = __language__(542)
		MENU_OPT_SMB_DVDPRO_SHARE = __language__(543)
		MENU_OPT_SMB_MOVIES_SHARE = __language__(544)
		MENU_OPT_SMB_FILENAME = __language__(545)
		MENU_OPT_SMB_COLLECTION_DIR = __language__(546)
		MENU_OPT_SMB_IMAGES_DIR = __language__(547)
		MENU_OPT_SMB_CONN_CHECK = __language__(548)

		def _makeMenu():
			debug("_makeMenu()")
			menu = [xbmcgui.ListItem(__language__(500))]
			if self.settings[self.SETTING_SMB_USE]:
				menu.append(xbmcgui.ListItem(MENU_OPT_SMB_USE, __language__(350)))	# yes
			else:
				menu.append(xbmcgui.ListItem(MENU_OPT_SMB_USE, __language__(351)))	# no
			menu.append(xbmcgui.ListItem(MENU_OPT_SMB_PATH, self.settings[self.SETTING_SMB_PATH]))
			menu.append(xbmcgui.ListItem(MENU_OPT_SMB_PC_IP, self.settings[self.SETTING_SMB_PC_IP]))
			menu.append(xbmcgui.ListItem(MENU_OPT_SMB_DVDPRO_SHARE, self.settings[self.SETTING_SMB_DVDPRO_SHARE]))
			menu.append(xbmcgui.ListItem(MENU_OPT_SMB_COLLECTION_DIR, self.settings[self.SETTING_SMB_COLLECTION_DIR]))
			menu.append(xbmcgui.ListItem(MENU_OPT_SMB_IMAGES_DIR, self.settings[self.SETTING_SMB_IMAGES_DIR]))
			menu.append(xbmcgui.ListItem(MENU_OPT_SMB_FILENAME, self.settings[self.SETTING_SMB_FILENAME]))
			menu.append(xbmcgui.ListItem(MENU_OPT_SMB_MOVIES_SHARE, self.settings[self.SETTING_SMB_MOVIES_SHARE]))
			menu.append(xbmcgui.ListItem(MENU_OPT_SMB_CONN_CHECK))
			return menu

		changed = False
		selectedPos = 0	# start on exit
		title = "%s: %s" % (__language__(0), __language__(527))
		while True:
			menu = _makeMenu()
			selectDialog = DialogSelectXML("script-bbb-dialogselect.xml", DIR_HOME, "Default")
			selectedPos, action = selectDialog.ask(title, menu, selectedPos)
			if selectedPos <= 0:
				break # exit selected

			# get menu selected value
			key = menu[selectedPos].getLabel()
			value = menu[selectedPos].getLabel2()
			if value == None:
				value = ''

			if key == MENU_OPT_SMB_PATH:
				# this is now just the SMB base path, no sharename on end
				smbPath = doKeyboard(value, MENU_OPT_SMB_PATH, KBTYPE_ALPHA)
				smbPath, ip = getSMBPathIP(smbPath, isSMBBasePathOnly=True)
				if smbPath:
					self.settings[self.SETTING_SMB_PATH] = smbPath
				if ip:
					self.settings[self.SETTING_SMB_PC_IP] = ip
				if smbPath or ip:
					changed = True

			elif key == MENU_OPT_SMB_PC_IP:
				ip = doKeyboard(value, __language__(218), KBTYPE_IP)	# IP dialog)
				if not isIP(ip):
					messageOK(MENU_OPT_SMB_PC_IP,__language__(975))
				else:
					self.settings[self.SETTING_SMB_PC_IP] = ip
					changed = True

			elif key == MENU_OPT_SMB_FILENAME:
				filename = doKeyboard(value,__language__(220),KBTYPE_ALPHA)
				if filename:
					self.settings[self.SETTING_SMB_FILENAME] = filename
					changed = True

			elif key == MENU_OPT_SMB_COLLECTION_DIR:
				value = doKeyboard(value,__language__(221),KBTYPE_ALPHA)
				if value.endswith('/'): value = value[:-1]
				value = value.replace('\\','/')
				self.settings[self.SETTING_SMB_COLLECTION_DIR] = value
				changed = True

			elif key == MENU_OPT_SMB_IMAGES_DIR:
				value = doKeyboard(value,__language__(222),KBTYPE_ALPHA)
				if value.endswith('/'): value = value[:-1]
				value = value.replace('\\','/')
				self.settings[self.SETTING_SMB_IMAGES_DIR] = value
				changed = True

			elif key == MENU_OPT_SMB_USE:
				self.settings[self.SETTING_SMB_USE] = xbmcgui.Dialog().yesno(__language__(527), MENU_OPT_SMB_USE)
				changed = True

			elif key == MENU_OPT_SMB_DVDPRO_SHARE:
				value = doKeyboard(value, MENU_OPT_SMB_DVDPRO_SHARE, KBTYPE_ALPHA)
				if value:
					if value.endswith('/'): value = value[:-1]
					value = value.replace('\\','/')
					self.settings[self.SETTING_SMB_DVDPRO_SHARE] = value
					changed = True

			elif key == MENU_OPT_SMB_MOVIES_SHARE:
				value = doKeyboard(value, MENU_OPT_SMB_MOVIES_SHARE, KBTYPE_ALPHA)
				if value:
					if value.endswith('/'): value = value[:-1]
					value = value.replace('\\','/')
					self.settings[self.SETTING_SMB_MOVIES_SHARE] = value
					changed = True

			elif key == MENU_OPT_SMB_CONN_CHECK:
				smbPath = "%s/%s" % (self.settings[self.SETTING_SMB_PATH], self.settings[self.SETTING_SMB_DVDPRO_SHARE])
				remote, remoteInfo = smbConnect(self.settings[self.SETTING_SMB_PC_IP],smbPath)
				if remote and remoteInfo:
					messageOK(MENU_OPT_SMB_CONN_CHECK,__language__(201), smbPath)

			if changed:
				saveFileObj(self.SETTINGS_FILENAME, self.settings)

			del selectDialog

		debug ("< configSMB changed="+str(changed))
		return changed

	#################################################################################################################
	def clearCache(self):
		debug("> clearCache()")
		success = False
		try:
			title = __language__(526)
			if xbmcgui.Dialog().yesno(title, __language__(223)):
				rmtree( DIR_IMG_CACHE )
				time.sleep(1)
				makeDir( DIR_IMG_CACHE )

			if xbmcgui.Dialog().yesno(title, __language__(224)):
				rmtree( DIR_CACHE )
				time.sleep(1)
				makeDir( DIR_CACHE )
		except:
			handleException()
		else:
			success = True

		debug("< clearCache() success="+str(success))
		return success


###################################################################################################
class DVDCollectionXML:
	def __init__(self, filename):
		debug("DVDCollectionXML().__init__")
		self.localCollectionFilename = filename

		# keys dict - [collNum] = [title, id, ...]
		DVDCollectionXML.KEYS_DATA_SORTTITLE = 0
		DVDCollectionXML.KEYS_DATA_ID = 1
		DVDCollectionXML.KEYS_DATA_GENRES = 2
		DVDCollectionXML.KEYS_DATA_TAGS = 3

		# DICT KEYS
		DVDCollectionXML.COLLNUM = 'collnum'
		DVDCollectionXML.ID = 'id'
		DVDCollectionXML.TITLE = 'title'
		DVDCollectionXML.SORTTITLE = 'sorttitle'
		DVDCollectionXML.GENRE = 'Genre'
		DVDCollectionXML.TAG = 'Tag'
		DVDCollectionXML.OVERVIEW = 'Overview'
		DVDCollectionXML.EASTEREGGS = 'EasterEggs'
		DVDCollectionXML.RATING = 'Rating'
		DVDCollectionXML.PRODYEAR = 'ProductionYear'
		DVDCollectionXML.RELEASED = 'Released'
		DVDCollectionXML.RUNNINGTIME = 'RunningTime'
		DVDCollectionXML.VIDEOFORMAT_ASPECT = 'VideoFormatAspect'
		DVDCollectionXML.VIDEOFORMAT_STD = 'VideoFormatStd'
		DVDCollectionXML.VIDEOFORMAT_IS16x9 = 'VideoFormatIs16x9'
		DVDCollectionXML.AUDIOFORMAT = 'AudioFormat'
		DVDCollectionXML.STUDIO = 'Studio'
		DVDCollectionXML.ACTORS = 'Actors'
		DVDCollectionXML.CREDITS = 'Credits'
		DVDCollectionXML.REGION = 'Region'
		DVDCollectionXML.REVIEW = 'Review'
		DVDCollectionXML.LOCATION = 'Location'
		DVDCollectionXML.SLOT = 'Slot'

		DVDCollectionXML.GENRE_NONE = 'Unspecified genre'
		self.dvdDict = {}
		self.keys = {}
		self.filterGenres = []
		self.filterTags = []

		if fileExist(COLLECTION_FLAT_FILE) and fileExist(KEYS_FILE):
			self.loadKeys()
		elif fileExist(self.localCollectionFilename):
			dialogProgress.create(__language__(225),__language__(227))
			self.saveFlatFile()
			dialogProgress.update(0,__language__(228))
			self.saveKeys()
			dialogProgress.close()

		if not self.keys:
			messageOK(__language__(225), __language__(202))	# failed

		if DEBUG:
			print "filterGenres=", self.filterGenres
			print "filterTags=", self.filterTags

		debug("< DVDCollectionXML().__init__")


	##############################################################################################
	def saveFlatFile(self):
		debug("> saveFlatFile()")

		try:
			self.regexDict = {
						self.ID : '<ID>(.*?)</',
						self.TITLE : '<Title>(.*?)</',
						self.SORTTITLE : '<SortTitle>(.*?)</',
						self.GENRE : '<Genres>(.*?)</Genres>',
						self.OVERVIEW : '<Overview>(.*?)</Overview>',
						self.EASTEREGGS : '<EasterEggs>(.*?)</EasterEggs>',
						self.RATING : '<Rating>(.*?)</Rating>',
						self.PRODYEAR : '<ProductionYear>(.*?)</ProductionYear>',
						self.RELEASED : '<Released>(.*?)</Released>',
						self.RUNNINGTIME : '<RunningTime>(.*?)</RunningTime>',
						self.VIDEOFORMAT_ASPECT : '<FormatAspectRatio>(.*?)<',
						self.VIDEOFORMAT_STD : '<FormatVideoStandard>(.*?)<',
						self.VIDEOFORMAT_IS16x9 : '<Format16X9>(.*?)<',
						self.AUDIOFORMAT : '<AudioContent>(.*?)</.*?<AudioFormat>(.*?)</',
						self.STUDIO : '<Studios>(.*?)</Studios>',
						self.REGION : '<Region>(.*?)</Region>',
						self.LOCATION : '<Location>(.*?)</Location>',
						self.SLOT : '<Slot>(.*?)</Slot>'
						}

			# different re for each version
			self.isV2 = self.isV2XML()
			if self.isV2:
				self.regexDict[self.ACTORS] = '<Actor>.*?<FirstName>(.*?)</.*?<LastName>(.*?)</.*?(?:<Role>(.*?)|)</'
				self.regexDict[self.CREDITS] =  '<Credit>.*?<FirstName>(.*?)<.*?<LastName>(.*?)<.*?<CreditSubtype>(.*?)<'
				self.regexDict[self.TAG] =  '<FullyQualifiedName>(.*?)<'
				self.regexDict[self.REVIEW] =  '<Review>(.*?)</Review>'
			else:
				self.regexDict[self.ACTORS] = '<Actor FirstName="(.*?)".*?LastName="(.*?)".*?Role="(.*?)"'
				self.regexDict[self.CREDITS] =  '<Credit FirstName="(.*?)".*?LastName="(.*?)".*?CreditSubtype="(.*?)"'
				self.regexDict[self.TAG] =  '<Tag Name.*?FullName="(.*?)"'
				self.regexDict[self.REVIEW] =  '<Review (Film=.*?) (Video=.*?) (Audio=.*?) (Extras=.*?)/>'

			fpDict = {}
			f = open(COLLECTION_FLAT_FILE,'w')

			self.keys = {}
			self.filterTags = []
			self.filterGenres = []
			section = []
			found = False
			replaceRE = re.compile('(<Locks>.*?</Locks>)', re.DOTALL + re.IGNORECASE + re.MULTILINE)
			collnumRE = re.compile('<CollectionNumber>(.*?)</', re.DOTALL + re.IGNORECASE + re.MULTILINE)

			for line in open(self.localCollectionFilename,'r'):
				if not found:
					if line.strip() == '<DVD>':
						found = True
						section = []
					continue
				elif line.strip() != '</DVD>':
					section.append(line)				# store line
					continue

				# process DVD XML section
				if found and section:
					data = '\n'.join(section)
					found = False
					dvdDict = {}

					# make sure this is owned
					matches = collnumRE.findall(data)
					if not matches:
						continue
					else:
						collnum = matches[0]

					dvdDict[self.COLLNUM] = [collnum]

					# remove LOCKS section
					data = replaceRE.sub('', data)

					# load dict with a list for each key
					for key, regex in self.regexDict.items():
						findRe = re.compile(regex, re.DOTALL + re.IGNORECASE + re.MULTILINE)
						matches = findRe.findall(data)
						matchList = []
						for match in matches:
							if not isinstance(match,str):
								matchList.append(match)		# saved as a list
							else:
								# split on newline, may give several <name>data</name>, then clean
								items = match.split('\n')
								cleanItemsList = []
								for item in items:
									cleanItem = cleanHTML(item)
									if cleanItem:
										cleanItemsList.append(cleanItem)

								matchList.extend(cleanItemsList)

						if matchList:
							dvdDict[key] = matchList

					if dvdDict:
						# save to file
#						print "save dvd to flat file"
						rec = self.COLLNUM+'|'+collnum
						for key,value in dvdDict.items():
							if not isinstance(value,str):					# is a list
								if isinstance(value[0],str):				# list of strs
									rec += '~'+key+'|'+'^'.join(value)
								else:										# list of lists
									for subValue in value:					# save each sublist with key name
										rec += '~'+key+'|'+'^'.join(subValue)
							else:
								rec += '~'+key+'|'+value

						f.write(decodeEntities(rec) + '\n')

						# save genre, further split to individual unique genre list
						if dvdDict.has_key(self.GENRE):
							keyData = dvdDict[self.GENRE]
							for value in keyData:
								genreList = value.split('~')
								for split in genreList:
									try:
										self.filterGenres.index(split)
									except:
										self.filterGenres.append(split)

						# save the tag as 'Location' if location contains data
						if dvdDict.has_key(self.LOCATION):
							debug("save LOCATION")
							if dvdDict[self.LOCATION]:
								try:
									self.filterTags.index(self.LOCATION)
								except:
									self.filterTags.append(self.LOCATION)
								# add Location to this dvd's tags
								try:
									dvdDict[self.TAG].append(self.LOCATION)	# add to existing tags list
								except:
									dvdDict[self.TAG] = [self.LOCATION]		# start a tags list


						# save tags
						if dvdDict.has_key(self.TAG):
							debug("save tags")
							keyData = dvdDict[self.TAG]
							for value in keyData:
								try:
									self.filterTags.index(value)
								except:
									self.filterTags.append(value)

						# save keys
						rec = [dvdDict[self.SORTTITLE][0],dvdDict[self.ID][0]]
						try:
							rec.append(dvdDict[self.GENRE])
						except:
							rec.append([])

						try:
							rec.append(dvdDict[self.TAG])
						except:
							rec.append([])
						self.keys[int(collnum)] = rec

			f.close()
		except:
			handleException("saveFlatFile()")

		debug("< saveFlatFile()")

	##############################################################################################
	def saveKeys(self):
		debug("> saveKeys()")
		try:
			f = open(KEYS_FILE,'w')
			if self.filterGenres:
				f.write(('genres|'+('~'.join(self.filterGenres))+'\n'))
			if self.filterTags:
				f.write(('tags|'+('~'.join(self.filterTags))+'\n'))
			if self.keys:
				for key,value in self.keys.items():
					if isinstance(value, str):
						f.write(('keys|%s~%s\n' % (key,decodeEntities(value))))
					else:
						rec = 'keys|%s' % key
						for item in value:
							if isinstance(item, str):
								rec += '~'+item
							else:
								rec += '~'+('^'.join(item))

						f.write(decodeEntities(rec)+'\n')
			f.close()
		except:
			handleException("saveKeys()")
		debug("< saveKeys()")

	##############################################################################################
	def loadKeys(self):
		debug("> loadKeys()")

		try:
			for line in open(KEYS_FILE,'r'):
				rec = line.strip().split('|')
				if rec[0] == 'genres':
					self.filterGenres = rec[1].split('~')
				elif rec[0] == 'tags':
					self.filterTags = rec[1].split('~')
				elif rec[0] == 'keys':
					# dict key is collnum. each rec pos +1 as prefixed by collnum
					splits = rec[1].split('~')
					collnum = int(splits[0])
					keysList = [splits[self.KEYS_DATA_SORTTITLE+1],
								splits[self.KEYS_DATA_ID+1]]
					if splits[self.KEYS_DATA_GENRES+1]:
						keysList.append(splits[self.KEYS_DATA_GENRES+1].split('^'))
					else:
						keysList.append([])
					
					if splits[self.KEYS_DATA_TAGS+1]:
						keysList.append(splits[self.KEYS_DATA_TAGS+1].split('^'))
					else:
						keysList.append([])

					self.keys[collnum] = keysList
		except:
			handleException("loadKeys()")

		debug("< loadKeys()")


	##############################################################################################
	def getFileSize(self):
		try:
			return (os.stat(self.localCollectionFilename).st_size / 1024) / 1024	# into kb
		except:
			return 0


	##############################################################################################
	# sets a dict of selected DVD from stored collection
	##############################################################################################
	def parseDVD(self, collNum):
		debug("> parseDVD() collNum=%s" % collNum)

		success = False
		self.dvdDict = {}
		regex = re.compile('(.*?)\|(.*?)(?:~|$)')
		for line in open(COLLECTION_FLAT_FILE,'r'):
			if line.startswith(self.COLLNUM+'|'+ collNum + '~'):
				matches = regex.findall(line)
				for key,value in matches:
					keyCount = line.count(key+'|')		# how many of this key stored ?
					subSplits = value.decode('latin-1','replace').split('^')
					if not self.dvdDict.has_key(key):
						self.dvdDict[key] = [subSplits]
					else:
						try:
							self.dvdDict[key].append(subSplits)
						except: pass
#							print "ignored 2nd subSplits=", subSplits

				break

		if self.dvdDict:
			self.dvdDict[self.COLLNUM] = [collNum]
			success = True

		debug("< parseDVD() success="+str(success))
		return success


	##############################################################################################
	def getCollectionSize(self):
		sz = len(self.keys)
		debug("getCollectionSize() sz=" + str(sz))
		return sz

	##############################################################################################
	def getDVDData(self, dataKey):
		try:
			return self.dvdDict[dataKey]
		except:
			debug("getDVDData() unknown key: %s" % dataKey)
			return ''

	##############################################################################################
	def getDVDKey(self, collnum):
		try:
			return self.keys[int(collnum)]
		except:
			return None

	##############################################################################################
	# True = v2
	# False = v3+
	##############################################################################################
	def isV2XML(self):
		isV2 = False
		if fileExist(self.localCollectionFilename):
			lineCount = 0
			for line in open(self.localCollectionFilename,'r'):
				if find(line,'Version 2') >= 0:
					isV2 = True
					break
				elif lineCount >= 3:
					break
				else:
					lineCount += 1

		debug("isV2XML() "+str(isV2))
		return isV2

###################################################################################################
class DVDCollectionOnline:
	def __init__(self, aliasData):
		debug("DVDCollectionOnline().__init__")
		self.alias,aliasURL = aliasData

		# keys dict - [collNum] = [title, id]
		DVDCollectionOnline.KEYS_DATA_SORTTITLE = 0
		DVDCollectionOnline.KEYS_DATA_ID = 1

		# DICT KEYS
		DVDCollectionOnline.ID = 'id'
		DVDCollectionOnline.TITLE = 'title'
		DVDCollectionOnline.GENRE = 'Genre'
		DVDCollectionOnline.OVERVIEW = 'Overview'
		DVDCollectionOnline.RATING = 'Rating'
		DVDCollectionOnline.PRODYEAR = 'ProductionYear'
		DVDCollectionOnline.RELEASED = 'Released'
		DVDCollectionOnline.RUNNINGTIME = 'RunningTime'
		DVDCollectionOnline.VIDEOFORMAT = 'VideoFormat'
		DVDCollectionOnline.AUDIOFORMAT = 'AudioFormat'
		DVDCollectionOnline.STUDIO = 'Studio'
		DVDCollectionOnline.ACTORS = 'Actors'
		DVDCollectionOnline.CREDITS = 'Credits'
		DVDCollectionOnline.FEATURES = 'Features'
		DVDCollectionOnline.REGION = 'Region'

		self.regexDict = {
					self.GENRE : '>Genres<.+?f2">(.*?)</SPAN',
					self.OVERVIEW : '>SRP:<.+?<TD class="stylearea" colSpan="2">.+?f2">(.*?)<',
					self.RATING : 'Rating:<.+?f2">(.*?)</SPAN',
					self.PRODYEAR : 'Year:<.+?f2">(.*?)</SPAN',
					self.RELEASED : 'Release:<.+?f2">(.*?)</SPAN',
					self.RUNNINGTIME : 'Time:<.+?f2">(.*?)</SPAN',
					self.REGION : 'Coding:<.+?f2">(.*?)</SPAN',
					self.VIDEOFORMAT : 'Video.*?Formats:<.+?f2">(.*?)</SPAN',
					self.AUDIOFORMAT : 'Audio.*?Tracks<.+?f2">(.*?)</SPAN',
					self.STUDIO : '>Studios<.+?f2">(.*?)</SPAN',
					self.ACTORS : 'Actors<.+?f2">(.*?)</SPAN',
					self.CREDITS : 'Credits:<.+?f2">(.*?)</SPAN',
					self.FEATURES : '>Features<.+?f2">(.*?)</SPAN'
					}

		self.URL = aliasURL + "/DVDCollection.aspx/"
		self.URL_TITLES = aliasURL + "/onlinecollections/dvd/PlumPeachy/List.aspx?type=a&Sort=ta"
		self.URL_DVD = aliasURL + "/onlinecollections/dvd/PlumPeachy/DVD.aspx?U="
		self.FILENAME_ONLINE_COLLECTION = os.path.join(DIR_CACHE, 'online_titles.html')
		self.FILENAME_DVD = os.path.join(DIR_CACHE , 'online_dvd.html')

		self.dvdDict = {}
		self.keys = {}
		self.filterGenres = []
		self.filterTags = []

		self.fetchCollection()
		self.extractKeys()

	###################################################################################################
	def fetchCollection(self):
		debug ("> fetchCollectionOnline()")
		success = False
		html = ''

		deleteFile(self.FILENAME_ONLINE_COLLECTION)
		deleteFile(self.FILENAME_DVD)
		dialogProgress.create(__language__(229),__language__(230) + self.alias)

		html = fetchCookieURL(self.URL + self.alias)
		if html:
			# check if known alias
			if find(html,'Unknown Alias') >= 0:
				dialogOK(__language__(229), __language__(109) + self.alias)
			elif find(html,'Empty Online') >= 0:
				dialogOK(__language__(229), __language__(110) +  self.alias)
			else:
				debug("fetching data page")
				dialogProgress.update(50, __language__(231) + self.alias)

				if fetchCookieURL(self.URL_TITLES, self.FILENAME_ONLINE_COLLECTION,newRequest=False):
					success = True

				dialogProgress.update(100, __language__(203))
		dialogProgress.close()

		debug ("< fetchCollectionOnline() success="+str(success))
		return success

	###################################################################################################
	def fetchDVD(self, collNum):
		debug ("> fetchDVD() collNum=%s" % collNum)

		deleteFile(self.FILENAME_DVD)
		title = self.getDVDKey(int(collNum))[self.KEYS_DATA_SORTTITLE]
		id = self.getDVDKey(int(collNum))[self.KEYS_DATA_ID]

		url = self.URL_DVD + id
		dialogProgress.create(__language__(229), self.alias, title)
		if fetchCookieURL(url, self.FILENAME_DVD):
			success = True
		else:
			success = False
		dialogProgress.close()

		debug ("< fetchDVD() success=%s" % success)
		return success

	##############################################################################################
	# parse DVD info
	def parseDVD(self, collNum):
		debug("> parseDVD() collNum="+str(collNum))

		self.dvdDict = {}
		if not self.fetchDVD(collNum):
			debug ("< parseDVD() failed")
			return None

		# using regex create a dict of lists
		try:
			title = self.keys[int(collNum)][self.KEYS_DATA_SORTTITLE]
			id = self.keys[int(collNum)][self.KEYS_DATA_ID]
			self.dvdDict[self.TITLE] = [title]
			self.dvdDict[self.ID] = [id]
			html = file(self.FILENAME_DVD).read()
			if html:
				# load dict with a list for each key
				for key, regex in self.regexDict.items():
					findRe = re.compile(regex, re.DOTALL + re.IGNORECASE + re.MULTILINE)
					findList = findRe.findall(html)
					matchList = []
					for matches in findList:
						matches = matches.replace('<br>','<BR>')
						replaceRE = re.compile('(<b>.*?</b>)', re.DOTALL + re.IGNORECASE + re.MULTILINE)
						groups = replaceRE.sub('', matches).split('<BR>')

						for group in groups:
							# DVD Profiler does not use HTML entities in its pages, we have to use translate manually
							cleanItem = cleanHTML(unicodeToAscii(group))
							if cleanItem:
								matchList.append([cleanItem])

					if matchList:
						self.dvdDict[key] = matchList
		except:
			handleException()
			self.dvdDict = {}

		debug("< parseDVD()")
		return self.dvdDict

	##############################################################################################
	def extractKeys(self):
		debug("> extractKeys()")
		self.keys = {}
		doc = readFile(self.FILENAME_ONLINE_COLLECTION)
		if doc:
			regex = "<A HREF=\"DVD.aspx\?U=(.*?)\" .+?entry\">(.*?)<.+?NOBR>(.*?)<.+?right\">(\d+)<"
			findRe = re.compile(regex, re.DOTALL + re.MULTILINE + re.IGNORECASE)
			matches = findRe.findall(doc)
			for match in matches:
				id = match[0]
#				DVD Profiler does not use HTML entities in its pages, we have to translate manually
				title = unicodeToAscii(match[1])
				date = match[2]
				collNum = int(match[3])
				self.keys[collNum] = [title, id, title]

		sz = len(self.keys)
		debug("< extractKeys() num keys="+str(sz))
		return sz

	##############################################################################################
	def getCollectionSize(self):
		sz = len(self.keys)
		debug("getCollectionSize() sz=" + str(sz))
		return sz

	##############################################################################################
	def getDVDData(self, dataKey):
		return self.dvdDict[dataKey]

	##############################################################################################
	def getDVDKey(self, collnum):
		try:
			return self.keys[int(collnum)]
		except:
			return None

#######################################################################################################################    
# Select/Add/Delete from list of online collections
#######################################################################################################################    
class ManageOnlineCollection:
	def __init__(self):
		debug("ManageOnlineCollection() init()")

		self.ONLINE_FILENAME = os.path.join( DIR_USERDATA, 'online_users.dat' )
		self.TITLE = __language__(504)

	def load(self):
		debug("> ManageOnlineCollection.load()")
		users = []
		if fileExist(self.ONLINE_FILENAME):
			for line in file(self.ONLINE_FILENAME).readlines():
				rec = line.strip().split('~')
				if len(rec) == 1:
					rec = [rec[0],BASE_URL_INTER]
				users.append(rec)
		else:
			debug("file missing: " + self.ONLINE_FILENAME)

		debug("< ManageOnlineCollection.load() sz=%s" % len(users))
		return users

	def save(self, users):
		debug("> ManageOnlineCollection.save()")
		if not users:
			deleteFile(self.ONLINE_FILENAME)
		else:
			f = file(self.ONLINE_FILENAME,'w')
			for user, host in users:
				f.write(user + '~' + host+'\n')
			f.close()
		debug("< save()")

	def ask(self):
		debug("> ManageOnlineCollection().ask()")

		selectedPos = 0	# start on exit
		users = self.load()
		users.sort()
		users.insert(0, [__language__(500),""])
		while True:
			aliasData = []
			title = "%s - (A=%s, Y=%s, X=%s)" % \
						(self.TITLE,__language__(565),__language__(560),__language__(563))

			selectDialog = DialogSelectXML("script-bbb-dialogselect.xml", DIR_HOME, "Default")
			selectedPos, action = selectDialog.ask(title, users, selectedPos, "User","Host", useX=True, useY=True)
			if action in EXIT_SCRIPT or selectedPos <= 0:
				break
			elif action in CLICK_Y: 	# add new
				debug("add user")
				# ALIAS
				user = doKeyboard("",__language__(241))

				# HOST URL
				if user:
					if xbmcgui.Dialog().yesno(__language__(242), "","", "", \
									__language__(356), __language__(355)):
						host = BASE_URL_INTER
					else:
						host = BASE_URL_INVOS

					# HOST URL
					try:
						aliasData = [user, host]
						users.index(aliasData)
						messageOK(__language__(240), __language__(111), user, host)
					except:
						users.append(aliasData)
						self.save(users)

			elif action in CLICK_X: 			# delete
				user, host = users[selectedPos]
				if xbmcgui.Dialog().yesno(__language__(304), user, host):
					del users[selectedPos]
					self.save(users)
			elif selectedPos >= 1:				# select
				user, host = users[selectedPos]
				aliasData = [user, host]
				break
			elif selectedPos < 0:				# exit
				break

			del selectDialog

		debug("< ManageOnlineCollection().ask()")
		return aliasData

#######################################################################################################################    
#
#######################################################################################################################    
class Filters(xbmcgui.WindowXMLDialog):
	# control id's
	CLBL_TITLE = 1401
	CLBL_GENRES = 1411
	CLST_GENRES = 1412
	CLBL_TAGS = 1421
	CLST_TAGS = 1422

	def __init__(self, *args, **kwargs):
		debug("Filters().__ init__")
		self.isStartup = True

	#################################################################################################################
	def onInit( self ):
		debug("> Filters.onInit() isStartup=%s" % self.isStartup)
		if self.isStartup:
			xbmcgui.lock()

			self.getControl(self.CLBL_TITLE).setLabel(__language__(243))
			self.setupList(self.CLST_GENRES, self.genresDict)
			self.setupList(self.CLST_TAGS, self.tagsDict)

			xbmcgui.unlock()
			self.isStartup = False

		debug("< Filters.onInit()")

	##############################################################################################
	def onAction(self, action):
		try:
			buttonCode =  action.getButtonCode()
			actionID   =  action.getId()
		except: return
		if actionID in EXIT_SCRIPT or buttonCode in EXIT_SCRIPT:
			self.close()

	##############################################################################################
	def onClick(self, controlID):
		control = self.getControl(controlID)
		if controlID in (self.CLST_GENRES, self.CLST_TAGS):
			lbl1 = control.getSelectedItem().getLabel()
			selectedItem = control.getSelectedItem()
			pos = control.getSelectedPosition()

			exit = False
			if controlID == self.CLST_GENRES:
				if pos == 0:								# exit
					exit = True
				elif pos == 1:								# select ALL
					self.setListAllStates(self.genresDict, True)
					pos = -1
					isSelected = True
				elif pos == 2:								# select NONE
					self.setListAllStates(self.genresDict, False)
					pos = -1
					isSelected = False
				elif pos == 3:								# select NONE for both filters
					self.setListAllStates(self.tagsDict, False)
					self.setListAllStates(self.genresDict, False)
					pos = -1
					isSelected = False
					self.setListItemIcon(self.getControl(self.CLST_TAGS), pos, isSelected)
				else:										# indivudual
					isSelected = self.genresDict[lbl1]
					isSelected = not isSelected				# toggle state
					self.genresDict[lbl1] = isSelected		# re-save
			elif controlID == self.CLST_TAGS:				# tags CL
				if pos == 0:								# exit
					exit = True
				elif pos == 1:								# select ALL
					self.setListAllStates(self.tagsDict, True)
					pos = -1
					isSelected = True
				elif pos == 2:								# select NONE
					self.setListAllStates(self.tagsDict, False)
					pos = -1
					isSelected = False
				elif pos == 3:								# select NONE for both filters
					self.setListAllStates(self.genresDict, False)
					self.setListAllStates(self.tagsDict, False)
					pos = -1
					isSelected = False
					self.setListItemIcon(self.getControl(self.CLST_GENRES), pos, isSelected)
				else:										# indivudual
					isSelected = self.tagsDict[lbl1]
					isSelected = not isSelected
					self.tagsDict[lbl1] = isSelected

			if exit:
				self.close()
			else:
				self.setListItemIcon(control, pos, isSelected)
				self.updateTagsHeading()
				self.updateGenresHeading()

	##############################################################################################
	def setListAllStates(self, dataDict, newState):
		debug("setListAllStates() newState=%s" % newState)
		for key in dataDict.keys():
			dataDict[key] = newState

	##############################################################################################
	def setListItemIcon(self, control, pos, newState):
		debug("Filters.setListItemIcon() pos=%s newState=%s" % (pos, newState))
		xbmcgui.lock()
		if pos != -1:
			fromPos = pos
			toPos = pos+1
		else:
			fromPos = 4		# first real option after a hardcoded options
			toPos = control.size()

		if newState:
			fn = TICK_FILENAME
		else:
			fn = ''
		for pos in range(fromPos,toPos):
			li = control.getListItem(pos)
			li.setIconImage(fn)
			li.setThumbnailImage(fn)
		xbmcgui.unlock()

	##############################################################################################
	def updateTagsHeading(self):
		debug("Filters.updateTagsHeading()")
		enabledCount = self.tagsDict.values().count(True)			# count enabled
		text = "%s %s\\%s" % (__language__(244), enabledCount, len(self.tagsDict))
		self.getControl(self.CLBL_TAGS).setLabel(text)

	##############################################################################################
	def updateGenresHeading(self):
		debug("Filters.updateGenresHeading()")
		enabledCount = self.genresDict.values().count(True)			# count enabled
		text = "%s %s\\%s" % (__language__(245), enabledCount, len(self.genresDict))
		self.getControl(self.CLBL_GENRES).setLabel(text)

	##############################################################################################
	def setupList(self, controlListID, dataDict):
		debug("> Filters.setupList() controlListID=%s" % controlListID)

		controlList = self.getControl(controlListID)
		controlList.reset()

		sortList = dataDict.keys()
		sortList.sort()
		controlList.addItem(xbmcgui.ListItem(__language__(500)))	# exit
		controlList.addItem(xbmcgui.ListItem(__language__(246)))	# select all
		controlList.addItem(xbmcgui.ListItem(__language__(247)))	# select none
		controlList.addItem(xbmcgui.ListItem(__language__(248)))	# turn off all filters

		for key in sortList:
			if dataDict[key]:
				controlList.addItem(xbmcgui.ListItem(key, iconImage=TICK_FILENAME,thumbnailImage=TICK_FILENAME))
			else:
				controlList.addItem(xbmcgui.ListItem(key))

		self.updateTagsHeading()
		self.updateGenresHeading()
		debug("< Filters.setupList()")

	##############################################################################################
	def ask(self, genres, tags):
		debug ("> Filters.ask()")
		self.genresDict = genres
		self.tagsDict = tags

		self.doModal()

		# just return selected list from each filter dict
		selectedGenres = []
		for genre, state in self.genresDict.items():
			if state:
				selectedGenres.append(genre)

		selectedTags = []
		for tag, state in self.tagsDict.items():
			if state:
				selectedTags.append(tag)

		debug ("< Filters.ask()")
		return selectedGenres, selectedTags



######################################################################################
def updateScript(silent=False, notifyNotFound=False):
	debug( "> updateScript() silent=%s" %silent)

	updated = False
	up = update.Update(__language__, __scriptname__)
	version = up.getLatestVersion(silent)
	debug("Current Version: %s Tag Version: %s" % (__version__,version))
	if version and version != "-1":
		if __version__ < version:
			if xbmcgui.Dialog().yesno( __language__(0), \
								"%s %s %s." % ( __language__(1006), version, __language__(1002) ), \
								__language__(1003 )):
				updated = True
				up.makeBackup()
				up.issueUpdate(version)
		elif notifyNotFound:
			dialogOK(__language__(0), __language__(1000))
#	elif not silent:
#		dialogOK(__language__(0), __language__(1030))				# no tagged ver found

	del up
	debug( "< updateScript() updated=%s" % updated)
	return updated


#############################################################################################
# BEGIN !
#############################################################################################
makeScriptDataDir() 
makeDir(DIR_IMG_CACHE)
makeDir(DIR_CACHE)

# check for script update
if DEBUG:
    updated = False
else:
    updated = updateScript(True)
if not updated:
	try:
		# check language loaded
		xbmc.output( "__language__ = %s" % __language__ )

		myscript = DVDProfiler("script-dvdpro-main.xml", DIR_HOME, "Default")
		if myscript.ready:
			myscript.doModal()
		del myscript
	except:
		handleException()

# clean up on exit
deleteFile(os.path.join(DIR_HOME, "temp.xml"))
deleteFile(os.path.join(DIR_HOME, "temp.html"))
moduleList = ['bbbLib', 'bbbGUILib', 'smbLib', 'IMDbWin', 'IMDbLib']
if not updated:
    moduleList += ['update']
for m in moduleList:
	try:
		del sys.modules[m]
		xbmc.output(__scriptname__ + " del sys.module=%s" % m)
	except: pass

# remove other globals
try:
	del dialogProgress
except: pass

# goto xbmc home window
#try:
#	xbmc.executebuiltin('XBMC.ReplaceWindow(0)')
#except: pass
