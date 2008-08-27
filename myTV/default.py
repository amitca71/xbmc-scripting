"""
	myTV	A tv guide using TV listing data from your own countries DataSource.
			Can setup recordings to some TV cards.

	Written By BigBellyBilly
	bigbellybilly AT gmail DOT com	- bugs, comments, ideas, help ...

	THANKS:
	To everyone who's ever helped in anyway, or if I've used code from your own scripts, MUCH APPRECIATED!

	CHANGELOG: see ..\resources\changelog.txt or view throu Settings Menu
	README: see ..\resources\language\<language>\readme.txt or view throu Settings Menu

    Additional support may be found on xboxmediacenter forum.	
"""

import xbmc, xbmcgui
import sys, re, time, os
from os import path, listdir
from string import replace, split, upper, lower, capwords, join,zfill
from datetime import date
from threading import Thread
import math
import encodings,  encodings.latin_1
from shutil import copy
import gc

# Script doc constants
__scriptname__ = "myTV"
__version__ = '1.18'
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '22-08-2008'
xbmc.output(__scriptname__ + " Version: " + __version__ + " Date: " + __date__)

# Shared resources
DIR_HOME = os.getcwd().replace( ";", "" )
DIR_RESOURCES = os.path.join( DIR_HOME , "resources" )
DIR_RESOURCES_LIB = os.path.join( DIR_RESOURCES , "lib" )
DIR_USERDATA = os.path.join( "T:\\script_data", __scriptname__ )
DIR_GFX = os.path.join(DIR_RESOURCES,'gfx')
sys.path.insert(0, DIR_RESOURCES_LIB)

# Load Language using xbmc builtin
try:
    # 'resources' now auto appended onto path
    __language__ = xbmc.Language( DIR_HOME ).getLocalizedString
    if not __language__( 0 ): raise
except:
	print "failed to get builtin xbmc.Language() or strings not parsed from path - upgrade XBMC"

import update                                       # script update module
from bbbLib import *								# requires __language__ to be defined
from mytvLib import *
from bbbGUILib import *
from wol import WakeOnLan,CheckHost

from smbLib import *
from AlarmClock import AlarmClock
from IMDbWinXML import IMDbWin
 
# GLOBALS
global timerthread, dataSource, saveProgramme, config, mytvFavShows
dataSource = None
saveProgramme = None
timerthread = None
mytvFavShows = None

# override bbbLib globals with those from mytvLib
global DIALOG_PANEL
DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL
setDialogPanel(DIALOG_PANEL)

# external class return states that will cause mytv to perform on return
INIT_NONE = None
INIT_REDRAW = 0
INIT_DISPLAY = 1
INIT_FAV_SHOWS = 2
INIT_TIMERS = 3
INIT_PART = 4
INIT_FULL = 5
INIT_FULL_NOW = 6

#################################################################################################################
# MAIN
#################################################################################################################
class myTV(xbmcgui.WindowXML):
	# control id's
	CGRP_HEADER = 1000
	CI_CHANNEL_LOGO = 1010
	CLBL_PROG_TITLE = 1020
	CLBL_PROG_DESC = 1030
	CLBL_CLOCK = 1040
	CLBL_DATASOURCE = 1050
	CLBL_SAVEPROG = 1060
	CGRP_NAV_LISTS = 1100
	CLST_CHANNEL = 1110
	CLST_DAY = 1120
	CLST_HOUR = 1130
	CBTN_TIME_RESET = 1140
	CGRP_FOOTER_BTNS = 1200
	CLBL_B_BTN = 1201
	CBTN_B_BTN = 1202
	CLBL_A_BTN = 1203
	CLBL_X_BTN = 1204
	CLBL_Y_BTN = 1205
	CLBL_WHITE_BTN = 1206
	CLBL_BACK_BTN = 1207
	CGRP_EPG = 1300
	CLBL_CH_NAME = 1310
	
	def __init__(self, *args, **kwargs):
		debug("> myTV()__init__")

		setResolution(self)

		# used to calc string width based on each char width
		self.fontAttr = FontAttr()
		self.currentTime = TVTime()

		# clock thread
		global timerthread
		timerthread=Timer(self)

		# DATA STORE FOR PROG AS A BUTTON
		self.epgButtons = []				# stores for each channel [btn, prog, progidx, start, end]
		self.epgTimerBars = []				# overlay showing recording period
		self.epgButtonsBtnData_BTN = 0
		self.epgButtonsBtnData_PROG = 1
		self.epgButtonsBtnData_IDX = 2
		self.epgButtonsBtnData_START_TIME = 3
		self.epgButtonsBtnData_END_TIME = 4
		self.epgButtonsBtnData_GENRE_BTN = 5

		self.isEPGEnabled = True
		self.isStartup = True
		self.ready = False
		self.justHDChannels = False
		self.areHDChannels = False
		self.tvChannels = TVChannels()
		self.defaultAnims = [('WindowClose', 'effect=fade end=0 time=200'),
							('WindowOpen', 'effect=fade start=0 time=200'),
							('conditional', 'effect=fade time=200 start=100 end=50 condition=!Control.IsEnabled(%s)' % self.CGRP_HEADER)]

		if not self.initData(True, True):
			self.cleanup()
			self.close()
		else:
			self.ready = True
		debug("< myTV()__init__")

	#################################################################################################################
	def onInit( self ):
		debug("> onInit() isStartup=%s" % self.isStartup)
		if self.isStartup:
			self.ready = False
			self.setBButton(forceOFF=True)

			# if new LOGOS dir created, ask if want to DL logos now?
			if makeDir(DIR_LOGOS) and xbmcgui.Dialog().yesno(__language__(0), __language__(556) + "?"):
				downloadLogos()

			self.isFooterBtns = True
			self.rez = self.getResolution()

			self.epgSetup()		
			self.updateEPG(redrawBtns=True, updateLogo=True, updateChNames=True, forceLoadChannels=True)

			# footer
#			self.setupFooterNavLists()

			# start clock
			if timerthread:
				timerthread.start()

			self.isStartup = False
			self.ready = True

		debug("< onInit()")


	###############################################################################################################
	def setupFooterNavLists(self):
		debug("> setupFooterNavLists()")

		# CHANNELS
		ctrl = self.getControl(self.CLST_CHANNEL)
		if ctrl.getSelectedPosition() == -1:        # empty
			dialogProgress.create(__language__(618), __language__(300))
			ctrl.reset()
			for channel in self.tvChannels.getChannelNames():	# [chID, name, chIDAlt]
				ctrl.addItem( channel[TVChannels.CHAN_NAME] )
			ctrl.selectItem(0)

			# DAY
			dialogProgress.update(33)
			days = WEEKDAYS[:]
			dow = date.today().weekday()
			days[dow] = __language__(327)		# today
			# check for end of week, set tomorrow to week start day
			if dow==6:
				days[0] = __language__(328)		# tomorrow
			else:
				days[dow+1] = __language__(328)
			ctrl = self.getControl(self.CLST_DAY)
			ctrl.reset()
			for day in days:
				ctrl.addItem(day)
			ctrl.selectItem(dow)
			
			# HOURS
			dialogProgress.update(66)
			ctrl = self.getControl(self.CLST_HOUR)
			ctrl.reset()
			for hour in range(0, 24):
				hourStr = zfill(hour,2)
				ctrl.addItem( "%s:00" % hourStr )
				ctrl.addItem( "%s:30" % hourStr )
			dialogProgress.update(100, __language__(304))
			dialogProgress.close()

		# reset time button
		self.getControl(self.CBTN_TIME_RESET).setLabel(__language__(329))

		debug("< setupFooterNavLists()")

	###############################################################################################################
	def setFooterNavLists(self):
		debug("> setFooterNavLists()")

		# CHANNEL - use top of page channel
		self.getControl(self.CLST_CHANNEL).selectItem(self.allChannelIDX)

		# DAY
		currentSecs = self.currentTime.getCurrentTime()
		time_tm = time.localtime(currentSecs)
		self.getControl(self.CLST_DAY).selectItem(time_tm.tm_wday)

		# HOUR
#		timeInterval = self.currentTime.getTimeInterval(1)[0]						# first time interval [hh:mm,secs]
		timeInterval = self.currentTime.timeToHHMM(currentSecs, self.use24HourClock)
		# find matching label in ctrl list
		ctrl = self.getControl(self.CLST_HOUR)
		for idx in range(48):
			if ctrl.getListItem(idx).getLabel() == timeInterval:
				ctrl.selectItem(idx)
				break

		self.setFocus(self.getControl(self.CLST_CHANNEL))
		debug("< setFooterNavLists()")

	###############################################################################################################
	# load genre icons/colours
	def initGenre(self):
		debug("> initGenre()")

		# GENRES ICONS - (not all datasources use this)
		self.genreIcons = ConfigGenreIcons().getEnabledGenres()

		# GENRES COLORS - (not all datasources use this)
		self.genreColours = ConfigGenreColours().load()

		debug("< initGenre()")

	###############################################################################################################
	# SETUP DYNAMIC COMPONENTS OF THE EPG DISPLAY
	def epgSetup(self):
		debug("> epgSetup()")
		xbmcgui.lock()

		self.use24HourClock = config.getSystem(config.KEY_SYSTEM_CLOCK)

		# title
#		self.titleColour = config.getDisplay(config.KEY_DISPLAY_COLOUR_TITLE)
#		self.titleFont = config.getDisplay(config.KEY_DISPLAY_FONT_TITLE)
#		self.getControl(self.CLBL_PROG_TITLE).setLabel(__language__(300), self.titleFont, self.titleColour)	# please wait
		self.getControl(self.CLBL_PROG_TITLE).setLabel(__language__(300))	# please wait

		# title short desc
		self.descW = self.getControl(self.CLBL_PROG_DESC).getWidth()
		self.descColour = config.getDisplay(config.KEY_DISPLAY_COLOUR_SHORT_DESC)
#		self.descFont = config.getDisplay(config.KEY_DISPLAY_FONT_SHORT_DESC)
#		self.getControl(self.CLBL_PROG_DESC).setLabel("", self.descFont, self.descColour)
#		self.descFont = self.getControl(self.CLBL_PROG_DESC).getFont()

		# datasource
		self.getControl(self.CLBL_DATASOURCE).setLabel(config.getSystem(config.KEY_SYSTEM_DATASOURCE))

		# saveprogramme
		text = config.getSystem(config.KEY_SYSTEM_SAVE_PROG)
		if not text:
			text = config.VALUE_SAVE_PROG_NOTV
		self.getControl(self.CLBL_SAVEPROG).setLabel(text)

		# set footer button labels
		self.getControl(self.CLBL_A_BTN).setLabel(__language__(420))
		self.getControl(self.CLBL_X_BTN).setLabel(__language__(423))
		self.getControl(self.CLBL_Y_BTN).setLabel(__language__(424))
		self.getControl(self.CLBL_WHITE_BTN).setLabel(__language__(425))
		self.getControl(self.CLBL_BACK_BTN).setLabel(__language__(500))


		# Channel names visible ?
		useChannelNames = (config.getSystem(config.KEY_SYSTEM_SHOW_CH_ID) != '0')
		debug("useChannelNames=%s" % useChannelNames)

		headerH = self.getControl(self.CGRP_HEADER).getHeight()
		footerH = self.getControl(self.CGRP_FOOTER_BTNS).getHeight()
		debug("headerH=%s footerH=%s" % (headerH, footerH))

		# EPG ROW
		self.epgRowH = int(config.getDisplay(config.KEY_DISPLAY_EPG_ROW_HEIGHT))
		epgRowGapH = int(config.getDisplay(config.KEY_DISPLAY_EPG_ROW_GAP_HEIGHT))
		self.epgRowFullH = self.epgRowH + epgRowGapH
		debug("epgRowH: %s epgRowGapH: %s = epgRowFullH:%s"  % (self.epgRowH,epgRowGapH,self.epgRowFullH))

		epgCtrl = self.getControl(self.CGRP_EPG)
		self.epgW = epgCtrl.getWidth()
		self.epgH = epgCtrl.getHeight()
		self.epgX, self.epgY = epgCtrl.getPosition()
		debug("epgX: %s epgY: %s epgW: %s epgH: %s"  % (self.epgX,self.epgY,self.epgW,self.epgH))

		epgTimeBarH = 25
		self.pageIndicatorH = 15				# the next/prev page available indicators
		sideIndicatorW = 13
		self.epgColGap = 2
		if useChannelNames:
			epgChNameW = self.getControl(self.CLBL_CH_NAME).getWidth()
		else:
			epgChNameW = 0

		self.epgProgsW = self.epgW - epgChNameW - sideIndicatorW - self.epgColGap - sideIndicatorW
		self.epgProgsX = self.epgX + epgChNameW + sideIndicatorW + self.epgColGap
		self.epgProgsY = self.epgY + epgTimeBarH
		self.epgProgsH = self.epgH - epgTimeBarH - self.pageIndicatorH
		debug("epgChNameW=%s epgProgsW=%s epgProgsH=%s epgProgsX=%s epgProgsY=%s"  % \
					(epgChNameW,self.epgProgsW,self.epgProgsH,self.epgProgsX,self.epgProgsY))

		# calc epg space available for just epg rows to fit in (relies on epgProgsH & epgRowFullH)
		self.epgMaxDisplayChannels = self.getMaxDisplayChannels()

		# CLOCK
		try:
			global timerthread
			timerthread.setClock(self.use24HourClock)
		except: pass
		self.clockLbl = self.getControl(self.CLBL_CLOCK)

		# NOW TIME INDICATOR LINE
		try:
			self.removeControl(self.nowTimeCI)
		except: pass
		colour = config.getDisplay(config.KEY_DISPLAY_COLOUR_NOWTIME)
		ypos = self.epgY+1
		self.nowTimeCI = xbmcgui.ControlImage(-5, ypos, 0, self.epgH, ICON_NOW_TIME,colour)	# off screen
		self.nowTimeCI.setVisible(False)
		self.addControl(self.nowTimeCI)
		self.nowTimeCI.setAnimations(self.defaultAnims)
		self.nowTimeCI.setColorDiffuse(colour)

		# TIME INTERVALS
		self.maxTimeBarIntervals = self.currentTime.getMaxTimeBarIntervals()	# incl extra for date
		epgTimeIntervalW = int(self.epgProgsW / (self.currentTime.getMaxTimeBarIntervals()-1))
		self.epgPixelsPerMin = float(epgTimeIntervalW) / float(self.currentTime.getIntervalMins())
		debug("epgTimeIntervalW=%s epgPixelsPerMin=%s" % (epgTimeIntervalW, self.epgPixelsPerMin))

		# remove old timebar ctrls
		try:
			for ctrl in self.epgTimeBar:
				self.removeControl(ctrl)
		except: pass

		# create new timebar ctrls
		self.epgTimeBar = []
		self.epgTimeBar.append(xbmcgui.ControlLabel(self.epgX, self.epgY, epgChNameW, epgTimeBarH, \
													'', FONT12, '0xFFFFFF00'))
		self.addControl(self.epgTimeBar[0])
		tempX = self.epgProgsX
		for i in range(self.maxTimeBarIntervals-1):
			ctrl = xbmcgui.ControlLabel(tempX, self.epgY, 90, epgTimeBarH, '', FONT12, '0xFFFFFF66')
			self.epgTimeBar.append(ctrl)
			self.addControl(ctrl)
			tempX += epgTimeIntervalW

		for ctrl in self.epgTimeBar:
			ctrl.setAnimations(self.defaultAnims)

		# remove date from timebar (above ch names if not showing ch)
		self.epgTimeBar[0].setVisible(useChannelNames)

		# REMOVE TIMERBAR OVERLAYS
		try:
			for ctrl in self.epgTimerBars:
				self.removeControl(ctrl)
		except: pass
		self.epgTimerBars = []

		# CHANNEL NAMES
		try:
			for ctrl in self.epgChNames:
				self.removeControl(ctrl)
		except: pass

		self.epgChNames = []
		# check if were going to use ch names
		if useChannelNames:
			font = config.getDisplay(config.KEY_DISPLAY_FONT_CHNAMES)
			colour = config.getDisplay(config.KEY_DISPLAY_COLOUR_CHNAMES)
			tempY = self.epgProgsY
			for i in range(self.epgMaxDisplayChannels):
				ctrl = xbmcgui.ControlLabel(self.epgX, tempY, epgChNameW, self.epgRowH, '', \
								font, colour, alignment=XBFONT_CENTER_Y)
				self.epgChNames.append(ctrl)
				self.addControl(ctrl)
				ctrl.setAnimations(self.defaultAnims)
				tempY += self.epgRowFullH

		# EPG PROG MORE / PAGE INDICATORS
		try:
			for ctrl in self.epgIndicators:
				self.removeControl(ctrl[0])	# left
				self.removeControl(ctrl[1])	# right
		except: pass
		self.epgIndicators = []

		# create new LEFT AND RIGHT INDICATORS
		colour = config.getDisplay(config.KEY_DISPLAY_COLOUR_ARROWS)
		tempY = self.epgProgsY
		tempX_left = self.epgProgsX - sideIndicatorW
		tempX_right = self.epgProgsX + self.epgProgsW
		for chIDX in range(self.epgMaxDisplayChannels):
			# LEFT
			lblLeft = xbmcgui.ControlLabel(tempX_left, tempY, sideIndicatorW, self.epgRowH, '<', FONT13, \
									colour,alignment=XBFONT_CENTER_X|XBFONT_CENTER_Y)
			# RIGHT
			lblRight = xbmcgui.ControlLabel(tempX_right, tempY, sideIndicatorW, self.epgRowH, '>', FONT13, \
									colour, alignment=XBFONT_CENTER_X|XBFONT_CENTER_Y)
			self.epgIndicators.append([lblLeft, lblRight])
			self.addControl(lblLeft)
			self.addControl(lblRight)
			lblLeft.setVisible(False)
			lblRight.setVisible(False)
			tempY += self.epgRowFullH

		# PAGE UP / DOWN INDICATORS
		# TOP
		ypos = self.epgProgsY - self.pageIndicatorH
		xpos = self.epgProgsX + self.epgProgsW - sideIndicatorW
		lblTop = xbmcgui.ControlLabel(xpos, ypos, 0, 0, '^', FONT13, \
								colour,alignment=XBFONT_CENTER_X|XBFONT_CENTER_Y)
		# BOTTOM
		ypos = self.epgProgsY + self.epgProgsH
		lblBottom = xbmcgui.ControlLabel(xpos, ypos, sideIndicatorW, self.pageIndicatorH, 'V', FONT13, \
								colour,alignment=XBFONT_CENTER_X|XBFONT_CENTER_Y)
		self.epgIndicators.append([lblTop, lblBottom])
		self.addControl(lblTop)
		self.addControl(lblBottom)
		lblTop.setVisible(False)
		lblBottom.setVisible(False)

		for leftCtrl, rightCtrl in self.epgIndicators:
			leftCtrl.setAnimations(self.defaultAnims)
			rightCtrl.setAnimations(self.defaultAnims)

		xbmcgui.unlock()

		debug("< epgSetup()")

	def isReady(self):
		return self.ready


	# divide rows + gap into space available
	def getMaxDisplayChannels(self):
		count = int(self.epgProgsH / self.epgRowFullH)
#		count = 2								# UNCOMMENT DURING DEVELOPMENT ONLY
		debug("getMaxDisplayChannels() (%s / %s) = count=%s" % (self.epgProgsH, self.epgRowFullH, count))
		return count

	############################################################################################################################
	# Clears stored listingdata.
	# (if reqd) import datasource
	# (if reqd) import saveProgramme
	############################################################################################################################
	def initData(self, resetData=True, resetDSSP=False):
		debug("> initData() resetData=%s resetDSSP=%s" %( resetData, resetDSSP) )
		global dataSource, saveProgramme
		success = True

		if resetData or resetDSSP:
			self.clearEPG(clearAll=True)
			self.allChannelIDX = 0
			self.epgChIDX = 0				# currently select channel
			self.epgBtnIDX = 0				# currently select btn
			self.currentTime.reset()
			self.tvChannels.reset()
			self.epgLastProgFocusTime = -1
			self.favShowsList = []
			self.timersDict = {}
			self.timersProgIDList = []
			gc.collect()

		if not dataSource or resetDSSP:
			debug("init dataSource")
			try:
				del dataSource
				gc.collect()
			except: pass
			dataSource = None

			# import data source module
			dataSource = importDataSource()			# import datasource if already saved in config file
			if not dataSource:
				debug("< initData() error init datasource")
				return False
			elif canDataSourceConfig() and not configDataSource(forceReset=False):
				debug("< initData() error config datasource")
				return False

		if not saveProgramme or resetDSSP:
			debug("init saveProgramme")
			if not importSaveProgramme():
				debug("< initData() error init saveprogramme")
				return False

		if not self.tvChannels.channelNames:
			debug("init channelNames")
			chCount = self.tvChannels.loadDatasourceChannelNames(self.justHDChannels)
			if self.justHDChannels:
				self.areHDChannels = (chCount > 0)
			else:
				if not chCount:
					self.areHDChannels = False
#					success = False
				else:
					self.areHDChannels = (self.tvChannels.getHDChannels(countOnly=True) > 0)
			debug("HD channels available=%s" % self.areHDChannels)

			# failed all channels, show config menu
#			if not self.tvChannels.channelNames:
#				ConfigMenu().ask()

			if success and saveProgramme:
				# no need to save timers to local file if fetching from remote server
				saveToFile = not hasattr(saveProgramme,"getRemoteTimers")
				self.manageTimers = ManageTimers(saveToFile)	# True = save to file

				# some saveprogrammes need a full chList
				if hasattr(saveProgramme, "setChannelList"):
					debug("do setChannelList()")
					chList = self.tvChannels.getChannelNames()	# [chID, name, other]
					saveProgramme.setChannelList(chList)


		if success:
			# LOAD TIMERS
			self.initTimers()

			# load favShows
			self.initFavShows()

			# load genres
			self.initGenre()

		debug("< initData() success=%s" % success)
		return success

	##############################################################################################################
	def initTimers(self):
		debug("> initTimers()")

		if saveProgramme:
			if hasattr(saveProgramme,"getRemoteTimers"):
				if sendWOL(True):
					debug("load remote timers")
					timers = saveProgramme.getRemoteTimers()
					if timers == None:		# none is error, [] is empty
						messageOK(saveProgramme.getName(), __language__(830),__language__(829)) # failed
					else:
						self.timersDict,self.timersProgIDList = self.manageTimers.refreshTimerFiles(timers)
			else:
				debug("load local timers")
				self.timersDict,self.timersProgIDList = self.manageTimers.getTimers(forceLoad=True)

		debug("< initTimers()")

	##############################################################################################################
	def initFavShows(self):
		debug("> initFavShows()")
		try:
			global mytvFavShows
			if not mytvFavShows:
				mytvFavShows = myTVFavShows()
			self.favShowsList = mytvFavShows.getTitles()
		except:
			handleException()
		debug("< initFavShows()")


	##############################################################################################################
	def onAction(self, action):
		try:
			actionID = action.getId()
			if not actionID:
				actionID = action.getButtonCode()
		except: return

		if actionID in EXIT_SCRIPT:
			debug("EXIT_SCRIPT")
			self.ready = False
			self.cleanup()
			self.close()
			return
		elif not self.ready:
			return
#		debug( "myTV onAction(): actionID=%i" % actionID )

		self.ready = False
		if actionID in CONTEXT_MENU:
			debug("> CONTEXT_MENU")
			self.getControl(self.CGRP_HEADER).setEnabled(False)
			reInitLevel = MainMenu().ask()
			self.getControl(self.CGRP_HEADER).setEnabled(True)
			redraw = True
			forceLoadChannels = False
			updateChNames = False

			if reInitLevel == INIT_REDRAW:
				redraw = True
			elif reInitLevel == INIT_DISPLAY:
				self.epgSetup()                                     # re-create controls using new attrs
				updateChNames = True
			elif reInitLevel == INIT_PART:
				self.initData(False, False)	                        # part reset
			elif reInitLevel in (INIT_FULL, INIT_FULL_NOW):
				self.initData(True, True)	                        # full reset
				self.epgSetup()
				forceLoadChannels = True
				updateChNames = True
			elif reInitLevel == INIT_FAV_SHOWS:
				self.initFavShows()
			elif reInitLevel == INIT_TIMERS:
				self.initTimers()
			else:								# init_none
				redraw = False

			if reInitLevel != INIT_NONE:
				self.updateEPG(redrawBtns=redraw, updateLogo=False, updateChNames=updateChNames, forceLoadChannels=forceLoadChannels)
			debug("< CONTEXT_MENU")
		elif self.isFooterBtns:										# currently NAVIGATING USING EPG
			if actionID in CLICK_X:									# toggle footer display
				debug("CLICK_X")
				self.setupFooterNavLists()
				self.toogleFooter()
			elif actionID in CLICK_Y:								# IMDb
				debug("CLICK_Y")
				title = self.getCurrentProgrammeTitle()
				if validProgramme(title):
					self.getControl(self.CGRP_HEADER).setEnabled(False)
					callIMDB(title)
					self.getControl(self.CGRP_HEADER).setEnabled(True)
			elif actionID in CLICK_B or actionID == ACTION_REMOTE_RECORD:
				# action according to function of B (red) btn.
				# no TV card == toggle SD/HD
				# TV card == SaveProgramme
				if not saveProgramme:
					debug("CLICK_B - no saveProgramme")
					if self.areHDChannels:
						self.justHDChannels = not self.justHDChannels			# toogle state
						self.initData(True, False)                              # reset Data, not DS,SP
						self.updateEPG(redrawBtns=True, updateLogo=True, updateChNames=True, forceLoadChannels=True)
				else:
					debug("CLICK_B - have saveProgramme")
					if validProgramme(self.getCurrentProgrammeTitle()):
						# record button
						if not self.isTimer():
							success = callSaveProgramme()
							if success:
								self.initTimers()
						else:
							success = callManageSaveProgramme()
						if success:
							self.updateEPG(redrawBtns=True, updateLogo=False, updateChNames=False, forceLoadChannels=False)
			elif actionID in MOVEMENT and actionID not in MOVEMENT_STICKS:	# move to another prog on epg
				self.moveEPG(actionID)
		elif not self.isFooterBtns:									# currently NAVIGATING USING LISTS
			if actionID in CLICK_X:
				self.toogleFooter()

		self.ready = True

	###############################################################################################################
	def onClick(self, controlID):
		if not self.ready:
			return

		self.ready = False
		if not self.isFooterBtns:										# using navlists
			if controlID == self.CBTN_TIME_RESET:
				debug("> TIME RESET BUTTON")
				# reset epg to system actual time
				self.currentTime.reset()
				self.setFooterNavLists()		# update navlist to reflect new epg date/time
				self.updateEPG(redrawBtns=True, updateLogo=True, updateChNames=True, forceLoadChannels=True, forceUseNavLists=True)
				debug("< TIME RESET BUTTON")
			else:
				debug("> ON NAVLISTS CONTROL")
				self.updateEPG(redrawBtns=True, updateLogo=True, updateChNames=True, forceLoadChannels=True, forceUseNavLists=True)
				debug("< ON NAVLISTS CONTROL")
			self.setFocus(self.getControl(controlID))
		else:
			self.showDescription()

		self.ready = True

	###################################################################################################################
	def setBButton(self, forceOFF=False):
		debug("setBButton() forceOFF=%s" % forceOFF)
		try:
			if not forceOFF:
				isVisible = True
				if not saveProgramme:
					if self.areHDChannels:
						if self.justHDChannels:
							self.getControl(self.CLBL_B_BTN).setLabel(__language__(427))		# view SD channels
						else:
							self.getControl(self.CLBL_B_BTN).setLabel(__language__(421))		# view HD channels
					else:
						isVisible = False
				elif validProgramme(self.getCurrentProgrammeTitle()):
					if not self.isTimer():
						self.getControl(self.CLBL_B_BTN).setLabel(__language__(422))			# record
					else:
						self.getControl(self.CLBL_B_BTN).setLabel(__language__(426))			# cancel rec
				else:
					isVisible = False
			else:
				isVisible = False

			# skin may not show button image
			self.getControl(self.CBTN_B_BTN).setVisible(isVisible)
		except: pass

	###################################################################################################################
	def onFocus(self, controlID):
#		debug("onFocus(): controlID=%i" % controlID)
#		self.controlID = controlID
		pass

	###################################################################################################################
	def toogleFooter(self, forceState=None):
		debug("> toogleFooter() forceState=%s" % forceState)
		try:
			origState = self.isFooterBtns
			if forceState == None:
				self.isFooterBtns = not self.isFooterBtns		# toggle
			else:
				self.isFooterBtns = forceState
		except:
			self.isFooterBtns = True
			origState = True

		# change visible state of FOOTER BTNS GRP
		if self.isFooterBtns:
			self.getControl(self.CGRP_FOOTER_BTNS).setVisible(True)

		# if footer state changed, change epg height available, then redraw
		if origState != self.isFooterBtns:
			diffH = self.getControl(self.CGRP_NAV_LISTS).getHeight() - self.getControl(self.CGRP_FOOTER_BTNS).getHeight()
			debug( "diffH=%s" % diffH )
			if self.isFooterBtns:
				debug(" has become navlists OFF")
				self.epgH += diffH					# btn footer, more height available
				self.epgProgsH += diffH
				forceUseNavLists = True				# force to read date/time from navlists
			else:
				debug(" has become navlists ON")
				self.epgH -= diffH					# nav list footer, less height available
				self.epgProgsH -= diffH
				forceUseNavLists = False

			self.epgMaxDisplayChannels = self.getMaxDisplayChannels()
			self.updateEPG(redrawBtns=True, updateLogo=True, updateChNames=True, forceLoadChannels=False, forceUseNavLists=forceUseNavLists)
			if not self.isFooterBtns:
				self.setFooterNavLists()

		if not self.isFooterBtns:
			self.getControl(self.CGRP_FOOTER_BTNS).setVisible(False)

		debug("< toogleFooter(): isFooterBtns=%s" % self.isFooterBtns)

	###################################################################################################################
	def showDescription(self):
		debug("> showDescription()")
		# setup description panel
		prog = self.getCurrentProgramme()
		title = prog[TVData.PROG_TITLE]
		if validProgramme(title):
			self.getControl(self.CGRP_HEADER).setEnabled(False)
			pdd = ProgDescDialog("script-mytv-progdesc.xml", DIR_HOME, "Default")
			link = self.tvChannels.getProgAttr(prog, TVData.PROG_DESCLINK)
			genre = self.tvChannels.getProgAttr(prog, TVData.PROG_GENRE)
			subTitle = self.tvChannels.getProgAttr(prog, TVData.PROG_SUBTITLE)
			chID, chName, chIDAlt = self.tvChannels.getChannelInfo(self.allChannelIDX + self.epgChIDX)

			startTimeSecs = self.tvChannels.getProgAttr(prog, TVData.PROG_STARTTIME)
			startTime = time.strftime("%A %x %H:%M %p" ,time.localtime(startTimeSecs))
			endTimeSecs = self.tvChannels.getProgAttr(prog, TVData.PROG_ENDTIME)
			if not endTimeSecs:
				endTime = "??:??"
				displayDate = "%s - %s.  %s" % (startTime,endTime,chName)
			else:
				endTime = time.strftime("%H:%M %p" ,time.localtime(endTimeSecs))
				durMins = int((endTimeSecs - startTimeSecs) /60)
				displayDate = "%s - %s,  %smins.  %s" % (startTime,endTime,durMins, chName)

			# if a link is provided, dl it according to datasource
			if link:
				dialogProgress.create(__language__(206), __language__(300))
				desc = dataSource.getLink(link, title)
				prog[TVData.PROG_DESC] = desc
				dialogProgress.close()
			else:
				desc = self.tvChannels.getProgAttr(prog, TVData.PROG_DESC)

			if not desc:
				desc = __language__(205)    # no info

			# remove Record option if already a timer
			if not saveProgramme:
				isTimer = None
			else:
				isTimer = self.isTimer(prog,chID)
			isFav = self.isFavShow(title)

			reInitLevel = pdd.ask(title,subTitle,genre,displayDate,desc,isTimer,isFav)
			if reInitLevel != INIT_NONE:
				if reInitLevel == INIT_TIMERS:
					self.initTimers()
				elif reInitLevel == INIT_FAV_SHOWS:
					self.initFavShows()
				self.updateEPG(redrawBtns=True, updateLogo=False, updateChNames=False, forceLoadChannels=False)
			del pdd

			self.getControl(self.CGRP_HEADER).setEnabled(True)
		debug("< showDescription()")


	#######################################################################################################################
	# If time has moved on passed 3rd timebar interval (in secs) then return epg update required
	#######################################################################################################################
	def isEPGBehindTime(self):
		nowSecs = self.currentTime.getSystemTime()				# get now time
		intervalSecs = self.currentTime.getTimeInterval(2)[1]	# 3rd interval, [HH:MM, secs]
		doUpdate = (nowSecs > intervalSecs)
		debug("isEPGBehindTime() doUpdate=%s" % doUpdate)
		return doUpdate

	def getCurrentChannel(self):
		return self.tvChannels.getChannel(self.epgChIDX)
	def getCurrentChannelInfo(self):
		return self.tvChannels.getChannelInfo(self.allChannelIDX + self.epgChIDX)
	def getCurrentProgramme(self):
		return self.epgButtons[self.epgChIDX][self.epgBtnIDX][self.epgButtonsBtnData_PROG]
	def getCurrentProgrammeTitle(self):
		try:
			return (self.getCurrentProgramme()[TVData.PROG_TITLE])
		except:
			return ""

	# tidy up before exit
	def cleanup(self):
		debug("myTV().cleanup()")
		self.tvChannels.cleanup()
		try:
			global timerthread
			timerthread.stop()
		except: pass

	# direct navigation to ch / day / hour using lists
	def loadChannels(self, forceUseNavLists=False):
		debug("> loadChannels() forceUseNavLists=%s" % forceUseNavLists)

		if not self.isFooterBtns or forceUseNavLists:
			debug("load channels from navlists")
			self.allChannelIDX = self.getControl(self.CLST_CHANNEL).getSelectedPosition()
			self.epgChIDX = 0
			selectedDOW = self.getControl(self.CLST_DAY).getSelectedPosition()
			hourItem = self.getControl(self.CLST_HOUR).getSelectedItem().getLabel()
			debug( "navLists: CLST_CHANNEL %s CLST_DAY %s CLST_HOUR %s" % (self.allChannelIDX,selectedDOW,hourItem))

			# convert dow to dayDelta
			dow = date.today().weekday()
			if selectedDOW == dow:
				dayDelta = 0
			elif selectedDOW > dow:
				dayDelta = (selectedDOW - dow)
			else:
				dayDelta = (7 - dow) + selectedDOW
			debug("dayDelta=%i" % dayDelta)
			# set to time on today
			self.currentTime.resetToMidnight()
			self.currentTime.setCurrentTimeFromHHMM(hourItem)
			self.currentTime.setDayDelta(dayDelta)
			# move currentTime according to day delta
			if dayDelta > 0:
				self.currentTime.updateCurrentTime(TVTime.DAY_SECS * dayDelta)
		else:
			debug("load channels from current day/time")
			self.currentTime.reset()
			dayDelta = 0

		# determine file date from currentTime and daydelta 
		saveDate = self.currentTime.timeToFileDate()
		self.tvChannels.setFileSaveDate(saveDate)
		fetchCount = self.tvChannels.loadChannels(self.allChannelIDX, 0, self.epgMaxDisplayChannels, \
												dayDelta, saveDate, self.tvChannels.LOAD_DATA_CLEAR)
		debug("< loadChannels() fetchCount=%s" % fetchCount)
		return fetchCount


	##############################################################################################
	# find btn middle time
	##############################################################################################
	def getButtonMiddleTime(self, epgChIDX, epgBtnIDX):
		btnData = self.epgButtons[self.epgChIDX][self.epgBtnIDX]
		# get btn actual shown start/end times (as opposed to prog start/end times)
		btnStartTime = btnData[self.epgButtonsBtnData_START_TIME]
		btnEndTime = btnData[self.epgButtonsBtnData_END_TIME]
		btnMiddleTime = btnStartTime + ((btnEndTime - btnStartTime) /2)
		debug("getButtonMiddleTime() epgChIDX=%s epgBtnIDX=%s btnMiddleTime=%s" % (epgChIDX, epgBtnIDX, btnMiddleTime))
		return btnMiddleTime

	##############################################################################################
	# MOVE EPG LEFT/RIGHT/UP or DOWN
	##############################################################################################
	def moveEPG(self, actionID):
		debug("> moveEPG() actionID=%s " % actionID)
		channelsSZ = self.tvChannels.getChannelsSZ()
		debug("allChannelIDX=%s epgChIDX=%s epgBtnIDX=%s channelsSZ=%s" % (self.allChannelIDX,self.epgChIDX,self.epgBtnIDX,channelsSZ))

		loadData = False
		redraw = False
		updateChNames = False
		ignoreAction = False
		loadDataAction = 0		# -1 prefix new data, 0 clear data store, 1 append new data
		saveDate = self.currentTime.timeToFileDate()

		# set last button focus time, if not already set, to middle of prog time.
		if self.epgLastProgFocusTime == -1:
			self.epgLastProgFocusTime = self.getButtonMiddleTime(self.epgChIDX, self.epgBtnIDX)

		if actionID in MOVEMENT_LEFT:
			debug("MOVEMENT_LEFT")
			# check if moving left 1 prog or need to move epg right 1 interval
			if self.epgBtnIDX > 0:
				self.epgBtnIDX -= 1
				self.epgLastProgFocusTime = self.getButtonMiddleTime(self.epgChIDX, self.epgBtnIDX)
			else:
				intervalTime, intervalSecs = self.currentTime.getTimeInterval(1)	# [HH:MM, secs]
				# prevent backtracking beyond script initial start start time
				if intervalSecs <= self.currentTime.getStartupTime():
					debug("< moveEPG() attempt to move BACK past startup time, action ignored")
					return 

				# determine time that btn focus routine is to compare against
				self.epgLastProgFocusTime = self.getButtonMiddleTime(self.epgChIDX, self.epgBtnIDX)

				# move currentTime Back one interval
				currentTime = self.currentTime.updateInterval(-1)
				saveDate = self.currentTime.timeToFileDate(currentTime)
				if saveDate != self.tvChannels.getFileSaveDate():
					debug("need PREV day data file")
					self.currentTime.updateDayDelta(-1)
					self.tvChannels.setFileSaveDate(saveDate)
					loadData = True
					loadDataAction = self.tvChannels.LOAD_DATA_PREFIX
				else:
					redraw = True

		elif actionID in MOVEMENT_RIGHT:
			debug("MOVEMENT_RIGHT")
			# check if moving right 1 prog or need to move epg left 1 interval
			if self.epgBtnIDX < len(self.epgButtons[self.epgChIDX])-1:
				# right with epg shown
				self.epgBtnIDX += 1
				self.epgLastProgFocusTime = self.getButtonMiddleTime(self.epgChIDX, self.epgBtnIDX)
			else:
				# get last interval time
				intervalTime, intervalSecs = self.currentTime.getTimeInterval(self.maxTimeBarIntervals)	# [HH:MM, secs]

				# determine time that btn focus routine is to compare against
				self.epgLastProgFocusTime = self.getButtonMiddleTime(self.epgChIDX, self.epgBtnIDX)

				# move currentTime forward one interval
				self.currentTime.updateInterval(1)

				saveDate = self.currentTime.timeToFileDate(intervalSecs)
				if saveDate != self.tvChannels.getFileSaveDate():
					debug("need NEXT day data file reqd")
					self.tvChannels.setFileSaveDate(saveDate)
					self.currentTime.updateDayDelta(1)
					loadData = True
					loadDataAction = self.tvChannels.LOAD_DATA_APPEND
				else:
					redraw = True

		elif actionID in MOVEMENT_UP:
			debug("MOVEMENT_UP")
			if self.allChannelIDX > 0 or self.epgChIDX > 0:
				# check if need new page of channels
				if self.epgChIDX == 0:
					debug("UP page")
					self.tvChannels.resetChannelFirstProgIDX()
					loadData = True
					updateChNames = True
					self.allChannelIDX -= self.epgMaxDisplayChannels
					if self.allChannelIDX < 0:		# reached the top of all channels, reset indexes
						self.allChannelIDX = 0
					else:
						self.epgChIDX = self.epgMaxDisplayChannels-1		# last ch on prev page
				else:
					# move within epg
					self.epgChIDX -= 1
					self.epgBtnIDX = self.findButtonFocusByTime(self.epgChIDX, self.epgLastProgFocusTime)
			else:
				ignoreAction = True

		elif actionID in MOVEMENT_DOWN:
			debug("MOVEMENT_DOWN")
			if self.allChannelIDX < self.tvChannels.getChannelNamesSZ()-1:
				# check if need new page of channels
				if self.epgChIDX < channelsSZ-1:
					# move within epg
					self.epgChIDX += 1										# next onscreen channel
					self.epgBtnIDX = self.findButtonFocusByTime(self.epgChIDX, self.epgLastProgFocusTime)
				elif self.allChannelIDX + self.epgMaxDisplayChannels >= self.tvChannels.getChannelNamesSZ():
					ignoreAction = True										# page down would go past all channels
				else: 
					debug("DOWN page")
					self.tvChannels.resetChannelFirstProgIDX()
					loadData = True
					updateChNames = True
					self.epgChIDX = 0
					self.allChannelIDX += self.epgMaxDisplayChannels				# set to top of next page
			else:
				ignoreAction = True

		elif actionID in MOVEMENT_SCROLL_DOWN:
			debug("MOVEMENT_SCROLL_DOWN")
			if self.allChannelIDX < self.tvChannels.getChannelNamesSZ()-1:
				self.tvChannels.resetChannelFirstProgIDX()
				# check if we can move down a page
				if self.allChannelIDX + self.epgMaxDisplayChannels >= self.tvChannels.getChannelNamesSZ():
					self.epgChIDX = channelsSZ-1							# set to last epg channel
					self.epgBtnIDX = self.findButtonFocusByTime(self.epgChIDX, self.epgLastProgFocusTime)
				else:
					debug("DOWN page")
					loadData = True
					updateChNames = True
					self.epgChIDX = 0
					self.allChannelIDX += self.epgMaxDisplayChannels				# set to top of next page
			else:
				ignoreAction = True

		elif actionID in MOVEMENT_SCROLL_UP:
			debug("MOVEMENT_SCROLL_UP")
			self.epgChIDX = 0
			if self.allChannelIDX > 0:
				self.tvChannels.resetChannelFirstProgIDX()
				loadData = True
				updateChNames = True
				self.allChannelIDX -= self.epgMaxDisplayChannels		# move idx page up

				# check if idx moved passed first channel
				if self.allChannelIDX < 0:
					self.allChannelIDX = 0						# set to first
			else:
				self.epgBtnIDX = self.findButtonFocusByTime(self.epgChIDX, self.epgLastProgFocusTime)

		if not ignoreAction:
			debug("loadData: %s " % loadData)
			if loadData:
				dow = self.currentTime.getDayDelta()
				# load channel data if needed
				if self.tvChannels.loadChannels(self.allChannelIDX, 0, self.epgMaxDisplayChannels, \
												dow, saveDate, loadDataAction):
					redraw = True
				else:
					# cancel left / right time interval move
					if actionID in MOVEMENT_LEFT:
						debug("loadChannels failed, MOVEMENT_LEFT, reverting currentTime by +1 interval")
						self.currentTime.updateInterval(1)
					elif actionID in MOVEMENT_RIGHT:
						debug("loadChannels failed, MOVEMENT_RIGHT, reverting currentTime by -1 interval")
						self.currentTime.updateInterval(-1)

			updateLogo = (actionID in MOVEMENT_UP + MOVEMENT_DOWN + MOVEMENT_SCROLL_UP + MOVEMENT_SCROLL_DOWN)
			if redraw:
				if actionID in MOVEMENT_LEFT:
					self.epgBtnIDX = 0
				elif actionID in MOVEMENT_RIGHT:
					self.epgBtnIDX = len(self.epgButtons[self.epgChIDX])-1
#				else:
#					# up/down
#					self.epgBtnIDX = self.findButtonFocusByTime(self.epgChIDX, self.epgLastProgFocusTime)

			self.updateEPG(redrawBtns=redraw, updateLogo=updateLogo, updateChNames=updateChNames, forceLoadChannels=False)
		debug("< moveEPG() allChannelIDX=%s epgChIDX=%s epgBtnIDX=%s" % (self.allChannelIDX,self.epgChIDX,self.epgBtnIDX))

	###############################################################################################
	# clearLogo - is a way to clear all epg items, not just epg buttons
	#############################################################################################
	def clearEPG(self,clearAll=False):
		debug("> clearEPG() clearAll=%s" % clearAll)

		xbmcgui.lock()
		if clearAll:
			try:
				self.setLogo(reset=True)
				self.getControl(self.CLBL_PROG_TITLE).setLabel(__language__(300))
				self.getControl(self.CLBL_PROG_DESC).setLabel('')
			except: pass

			# channel names
			try:
				for ctrl in self.epgChNames:
					ctrl.setLabel('')
			except: pass

		# if no epgButtons, there wont be any other controls drawn
		if self.epgButtons:
			# remove all buttons on channels
			for channel in self.epgButtons:
				for btnData in channel:
					try:
						self.removeControl(btnData[self.epgButtonsBtnData_BTN])
						self.removeControl(btnData[self.epgButtonsBtnData_GENRE_BTN])
					except: pass
			self.epgButtons = []

			# remove timerbar overlays
			for ctrl in self.epgTimerBars:
				self.removeControl(ctrl)
			self.epgTimerBars = []

			# indicator arrows
			for ctrl in self.epgIndicators:
				ctrl[0].setVisible(False)
				ctrl[1].setVisible(False)

			self.nowTimeCI.setVisible(False)
		xbmcgui.unlock()
		debug("< clearEPG()")

	###############################################################################################
	def updateEPG(self, redrawBtns=True, updateLogo=False, updateChNames=False, forceLoadChannels=False, forceUseNavLists=False):
		debug("> updateEPG() redrawBtns=%s updateLogo=%s forceLoadChannels=%s forceUseNavLists=%s" % \
			  (redrawBtns, updateLogo,forceLoadChannels,forceUseNavLists))

		# Force load if more space than ch shown, only if more chs available
		# getChannelsSZ is no. chs stored
		# getChannelNamesSZ is total no. channel names available
		# epgMaxDisplayChannels is max channels that can be displayed in space available
		# force only if less than max that can be drawn, but not beyond ch available.
		if (self.tvChannels.getChannelsSZ() < self.epgMaxDisplayChannels) and \
			(self.allChannelIDX + self.epgMaxDisplayChannels < self.tvChannels.getChannelNamesSZ()):
			debug("more channel space, force load")
			forceLoadChannels = True
			updateChNames = True

		# ensure epg is showing upto date time frame
		if (forceLoadChannels or self.isEPGBehindTime()) and self.loadChannels(forceUseNavLists):
			redrawBtns = True

		if redrawBtns:
			self.clearEPG(clearAll=updateChNames)
			self.createEPGBtns(updateChNames)

		self.updateNowTimeLine()	# update line position
		self.buttonFocus()			# set focus to curr ch & btn
		self.setBButton()			# set btns on footer according to prog
		if updateLogo:
			self.setLogo(self.allChannelIDX + self.epgChIDX)
		self.updateTitle()			# set title & desc to curr prog

		debug("< updateEPG() tvChannels.getChannelsSZ=%i epgMaxChannels=%i epgButtons=%i" % \
			  (self.tvChannels.getChannelsSZ(),self.epgMaxDisplayChannels, len(self.epgButtons)))

	##############################################################################################
	def createEPGBtns(self, redrawChannelNames=True):
		debug("> createEPGBtns() redrawChannelNames=%s" % redrawChannelNames)

		xbmcgui.lock()
		self.updateTimeBarIntervals()

		# epg colours/fonts
		font = config.getDisplay(config.KEY_DISPLAY_FONT_EPG)
		nofocusFile_odd = config.getDisplay(config.KEY_DISPLAY_NOFOCUS_ODD)
		nofocusFile_even = config.getDisplay(config.KEY_DISPLAY_NOFOCUS_EVEN)
		nofocusFile_fav = config.getDisplay(config.KEY_DISPLAY_NOFOCUS_FAV)
		focusFile = config.getDisplay(config.KEY_DISPLAY_FOCUS)
		textColor_odd = config.getDisplay(config.KEY_DISPLAY_COLOUR_TEXT_ODD)
		textColor_even = config.getDisplay(config.KEY_DISPLAY_COLOUR_TEXT_EVEN)
		textColor_fav = config.getDisplay(config.KEY_DISPLAY_COLOUR_TEXT_FAV)
		showCHIDType = config.getSystem(config.KEY_SYSTEM_SHOW_CH_ID)
		dayDelta = self.currentTime.getDayDelta()
		tempY = self.epgProgsY
		isOddLine = True

		debug("tvChannels.getChannelsSZ=%i epgMaxChannels=%i" % (self.tvChannels.getChannelsSZ(),self.epgMaxDisplayChannels))
		for epgChIDX in range(self.tvChannels.getChannelsSZ()):
			if epgChIDX >= self.epgMaxDisplayChannels:
				break

			# set channel name if been cleared
			if redrawChannelNames and self.epgChNames:
				# display channel name (with CH ID if turned on)
				chID, chName, chIDAlt = self.tvChannels.getChannelInfo(self.allChannelIDX + epgChIDX)
				if showCHIDType == '0':					# no name or id
					channelLabel = ''
				elif showCHIDType == '2':				# show ch ID
					channelLabel = "%s:%s" % (chID, chName)
				elif showCHIDType == '3':				# show ch alt ID
					channelLabel = "%s:%s" % (chIDAlt, chName)
				else:
					channelLabel = chName				# show name, no ch id
				self.epgChNames[epgChIDX].setLabel(channelLabel.strip())

			self.drawChannel(epgChIDX, self.epgProgsX, tempY, dayDelta, isOddLine, \
										font, nofocusFile_odd, nofocusFile_even, nofocusFile_fav, \
										focusFile, textColor_odd, textColor_even, textColor_fav)

			# draw overlaying timerbar (if any)
			self.drawTimers(epgChIDX, tempY)

			tempY += self.epgRowFullH
			isOddLine = not isOddLine

		self.setIndicators()	# make visible those needed
		xbmcgui.unlock()
		debug("< createEPGBtns()")

	##############################################################################################
	# draw a channel row
	##############################################################################################
	def drawChannel(self, epgChIDX,  xpos, ypos, dayDelta, isOddTimeline, font, \
					nofocusFile_odd, nofocusFile_even, nofocusFile_fav, focusFile, \
					textColor_odd, textColor_even, textColor_fav):

		actualChIDX = self.allChannelIDX + epgChIDX
		debug("> +++++++++ drawChannel() actualChIDX=%i epgChIDX=%i self.epgBtnIDX=%i dayDelta=%s"  % \
			  (actualChIDX, epgChIDX, self.epgBtnIDX, dayDelta))
#		startSecs = time.clock()
#		print "startSecs=%s" % startSecs
#		logFreeMem("drawChannel start")

		channelData = []
		btnStart = 0
		btnEnd = 0
		ICON_W_LARGE = 23
		ICON_W_SMALL = 10
		prog = None
		chID = self.tvChannels.getChannelID(self.allChannelIDX + epgChIDX)

		# first time interval holds epg date & mins, skip that
		firstTimeBarIntervalSecs = self.currentTime.getTimeInterval(1)[1]			# [hh:mm,secs]
		lastTimeBarIntervalSecs = self.currentTime.getTimeInterval(self.currentTime.getTimeIntervalSZ()-1)[1]# [hh:mm,secs]
		debug("firstTimeBarIntervalSecs=%s lastTimeBarIntervalSecs=%s" % (firstTimeBarIntervalSecs,lastTimeBarIntervalSecs))

		# find which first prog onto epg that ends after first timebar interval
		# check in current dayDelta file
		progIDX = self.tvChannels.getProgAtTime(epgChIDX, firstTimeBarIntervalSecs)
		if progIDX == -1:
			# load prev day file
			if dayDelta > -1:
				# back 24hrs, get new saveDate as YYYYMMDD
				saveDate = self.currentTime.timeToFileDate(firstTimeBarIntervalSecs - self.currentTime.DAY_SECS)
				debug("load PREV day files")
				# load all on channels epg (not just current), as they probs all reqd anyway
				xbmcgui.unlock()
				if self.tvChannels.loadChannels(actualChIDX, epgChIDX, self.epgMaxDisplayChannels, dayDelta-1, saveDate, self.tvChannels.LOAD_DATA_PREFIX):
					progIDX = self.tvChannels.getProgAtTime(epgChIDX, firstTimeBarIntervalSecs)
				xbmcgui.lock()
			else:
				debug("prev day not loaded. stopped by dayDelta already at -1")

		elif progIDX == -2:
			# load NEXT day file
			# fwd 24hrs, get new saveDate as YMD
			saveDate = self.currentTime.timeToFileDate(firstTimeBarIntervalSecs + self.currentTime.DAY_SECS)
			debug( "load NEXT day files")
			xbmcgui.unlock()
			if self.tvChannels.loadChannels(actualChIDX, epgChIDX, self.epgMaxDisplayChannels, dayDelta+1, saveDate, self.tvChannels.LOAD_DATA_APPEND):
				progIDX = self.tvChannels.getProgAtTime(epgChIDX, firstTimeBarIntervalSecs)
			xbmcgui.lock()

		if progIDX == -1: 				# unable to load PREV day, set prog to first of what we have
			progIDX = 0
		elif progIDX == -2:				# unable to loaded NEXT day file, set prog to last of what we have
			progIDX = self.tvChannels.getChannelSZ(actualChIDX)

		if progIDX >= 0:
			prog = self.tvChannels.getProgramme(epgChIDX, progIDX)

		# main BTN per PROG creation loop
		# loop until a prog on/during last time interval
		while btnStart < lastTimeBarIntervalSecs:
			if prog:
				btnStart = self.tvChannels.getProgAttr(prog, TVData.PROG_STARTTIME)
				btnEnd = self.tvChannels.getProgAttr(prog, TVData.PROG_ENDTIME)

			debug("0) progIDX=%s btnStart=%s btnEnd=%s" % (progIDX,btnStart,btnEnd))
#			if DEBUG and prog:
#				print self.tvChannels.getProgAttr(prog, TVData.PROG_TITLE)

			# TRIM BTN LEN TO THAT OF EPG START/END
			if btnStart < firstTimeBarIntervalSecs:
				btnStart = firstTimeBarIntervalSecs

			# truncate btn end time if past epg end time
			if btnEnd > lastTimeBarIntervalSecs or btnEnd <= firstTimeBarIntervalSecs or btnStart >= btnEnd:
				btnEnd = lastTimeBarIntervalSecs

			# check for a prog gap, create empty prog
			if not prog:
				debug("prog gap, create empty prog %s to %s" % (btnStart, btnEnd))
				prog = createEmptyProg(btnStart, btnEnd, True)

			# PLACE BUTTON
			btnLenSecs = (btnEnd - btnStart)
			nofocusFile = ""
			textColor = ""
			iconCI = None
			iconFilename = ""
			genre = ""
			btnTxt = self.tvChannels.getProgAttr(prog, TVData.PROG_TITLE)

			# only check for prog icons if valid prog
			if validProgramme(btnTxt):
				# TIMER icon
				if self.isTimer(prog, chID):
					iconFilename = ICON_TIMER					# no except so it was found

				# FAV SHOW icon - if no icon set
				if not iconFilename and self.isFavShow(btnTxt):
					iconFilename = ICON_FAV_SHOWS
					nofocusFile = nofocusFile_fav
					textColor = textColor_fav

				# GENRE icon and/or COLOUR - only if icon not assigned
				if not iconFilename:
					genre = self.tvChannels.getProgAttr(prog, TVData.PROG_GENRE)
					if genre:
						# GENRE ICON
						try:
							iconFilename = self.genreIcons[genre]
						except: pass # not found

						# GENRE COLOUR
						try:
							nofocusFile = self.genreColours[genre]
						except: pass # not found

			# calc avail space for text on btn
			btnW = int((btnLenSecs / 60) * self.epgPixelsPerMin) - self.epgColGap

			# set btn text and iconW according to space available
			if btnW < 5:												# no space for txt or icon
				btnTxt = ""
				iconFilename = ""
			elif btnW < ICON_W_SMALL:									# 'i' only, no icon
				btnTxt = "i"
				iconFilename = ""
			elif btnW >= ICON_W_SMALL and btnW < ICON_W_LARGE+5:		# 'i' only, small icon
				btnTxt = "i"
				iconW = ICON_W_SMALL
			elif btnW >= ICON_W_LARGE+5 and btnW < ICON_W_LARGE + 15:	# 'i' only, large icon
				btnTxt = "i"
				iconW = ICON_W_LARGE
			else:														# nornal txt, large icon
				iconW = ICON_W_LARGE
				if iconFilename:
					btnTxt = self.fontAttr.truncate(btnW - iconW, btnTxt, font, self.rez)
				else:
					btnTxt = self.fontAttr.truncate(btnW, btnTxt, font, self.rez)

			# fallback to configured epg colours if nothing set by now
			if not nofocusFile:
				if isOddTimeline:
					nofocusFile = nofocusFile_odd
					textColor = textColor_odd
				else:
					nofocusFile = nofocusFile_even
					textColor = textColor_even

			textXOffset = 2
			# if icon, move text further right
			if iconFilename:
				# shrink icon if on small button
				try:
					if iconW == ICON_W_SMALL:
						iconH = iconW
					else:
						iconH = self.epgRowH
						textXOffset = iconW + 1
						# create icon controlimage
					iconCI = xbmcgui.ControlImage(int(xpos), int(ypos), iconW, iconH, iconFilename)
				except: pass

			# create prog button
#			if DEBUG:
#				print btnW, textXOffset, btnTxt, iconFilename
#				print xpos, ypos, int(btnW-self.epgColGap), self.epgRowH
#				print btnTxt, focusFile, nofocusFile
#				print font, textXOffset, textColor
			progCB = xbmcgui.ControlButton(int(xpos), int(ypos), int(btnW), self.epgRowH, \
								btnTxt, focusFile, nofocusFile, font=font, \
								textXOffset=textXOffset, textColor=textColor, \
								alignment=XBFONT_CENTER_Y|XBFONT_TRUNCATED)
			self.addControl(progCB)
			progCB.setAnimations(self.defaultAnims)

			# add icon if used
			if iconFilename:
				self.addControl(iconCI)
				iconCI.setAnimations(self.defaultAnims)

			# store button onto channel btn list
			channelData.append([progCB, prog, progIDX, btnStart, btnEnd, iconCI])

			# stop processing if last btn end was beyond final interval time
			if btnEnd >= lastTimeBarIntervalSecs:
				debug("STOP, last btn >= final interval time")
				break

			# GET NEXT PROGs
			xpos += btnW + self.epgColGap
			progIDX += 1
			prog = self.tvChannels.getProgramme(epgChIDX, progIDX)
			if not prog:
				# load NEXT day's file
				debug("no next prog for this channel, load NEXT day data")
				xbmcgui.unlock()
				saveDate = self.currentTime.timeToFileDate(firstTimeBarIntervalSecs + self.currentTime.DAY_SECS)
				if self.tvChannels.loadChannels(actualChIDX, epgChIDX, 1, dayDelta+1, saveDate, self.tvChannels.LOAD_DATA_APPEND) > 0:
					prog = self.tvChannels.getProgramme(epgChIDX, progIDX)
				xbmcgui.lock()

			# still no prog, fill to end of epg
			if not prog:
				debug("no more progs loaded")
				btnStart = btnEnd							# set to end of last prog
				btnEnd = lastTimeBarIntervalSecs

		if channelData:
			self.epgButtons.append(channelData)

#		endSecs = time.clock()
#		print "endSecs=%s" % endSecs
#		print "process secs=%s" % (endSecs - startSecs)
		debug("< drawChannel() No. btns on channel=%i" % len(channelData))

	###############################################################################################
	def drawTimers(self, epgChIDX, ypos):
		debug("> drawTimers() epgChIDX=%s" % epgChIDX)
		chID = self.tvChannels.getChannelID(self.allChannelIDX + epgChIDX)
		if self.timersDict.has_key(chID):
			colour = config.getDisplay(config.KEY_DISPLAY_COLOUR_TIMERBAR)
			firstTimeBarIntervalSecs = self.currentTime.getTimeInterval(1)[1]			# [hh:mm,secs]
			lastTimeBarIntervalSecs = self.currentTime.getTimeInterval(self.currentTime.getTimeIntervalSZ()-1)[1]# [hh:mm,secs]

			# iter throu timers placing onto epg if within epg timeframe
			channelTimers = self.timersDict[chID]
			for startTime, endTime in channelTimers:
				# ensure timer overlays epg timeframe
				if endTime <= firstTimeBarIntervalSecs or startTime >= lastTimeBarIntervalSecs:
					continue

				if startTime < firstTimeBarIntervalSecs:
					startTime = firstTimeBarIntervalSecs
				if endTime > lastTimeBarIntervalSecs:
					endTime = lastTimeBarIntervalSecs

				# calc timebar w
				mins = int((endTime - startTime) / 60)
				w = int(mins * self.epgPixelsPerMin)

				# get startime mins as offset from first interval
				minsFromFirstInterval = int((startTime - firstTimeBarIntervalSecs) /60)

				# calc x pos
				xpos = int(self.epgProgsX + (minsFromFirstInterval * self.epgPixelsPerMin))

				y = (ypos + self.epgRowH -3)
				ctrl = xbmcgui.ControlImage(xpos, y, w, 0, ICON_TIMERBAR, colour)
				self.addControl(ctrl)
				ctrl.setAnimations(self.defaultAnims)
				ctrl.setColorDiffuse(colour)
				self.epgTimerBars.append(ctrl)

		debug("< drawTimers()")


	###############################################################################################
	def isFavShow(self, title):
		if self.favShowsList:
			try:
				self.favShowsList.index(title)
				return True
			except:
				return False
		else:
			return False

	###############################################################################################
	def isTimer(self, prog=None, chID=''):
		isProgTimer = False
		if saveProgramme:
			if not prog:
				prog = self.getCurrentProgramme()
			progID = self.tvChannels.getProgAttr(prog, TVData.PROG_ID)
			startTime = self.tvChannels.getProgAttr(prog, TVData.PROG_STARTTIME)
			endTime = self.tvChannels.getProgAttr(prog, TVData.PROG_ENDTIME)
			if not chID:
				chID = self.tvChannels.getChannelID(self.allChannelIDX+self.epgChIDX)
			if self.timersProgIDList:
				try:
					self.timersProgIDList.index(progID)
					isProgTimer = True
				except: pass

			if not isProgTimer and self.timersDict and self.timersDict.has_key(chID):
				# we have timers on this channel
				channelTimers = self.timersDict[chID]
				try:
					# try match by starttime & endtime
					channelTimers.index((startTime, endTime))
					isProgTimer = True
				except:
					# match by if prog in timer timeframe
					for timerStartTime, timerEndTime in channelTimers:
						if startTime >= timerStartTime and endTime <= timerEndTime:
							isProgTimer = True
							break

		debug("isTimer() isProgTimer=%s" % isProgTimer)
		return isProgTimer

	###############################################################################################
	# find first prog whos END time >= given time
	###############################################################################################
	def findButtonFocusByTime(self, chIDX, focusTime):
		debug("> findButtonFocusByTime() chIDX=%i focusTime=%s" % (chIDX, focusTime))

		btnIDX = 0
		try:
			for btnIDX, btnData in enumerate(self.epgButtons[chIDX]):
				if btnData[self.epgButtonsBtnData_END_TIME] >= focusTime:
					break
		except: pass

		debug("< findButtonFocusByTime() new btnIDX=%s" % btnIDX)
		return btnIDX

	###############################################################################################
	def buttonFocus(self):
		debug("> buttonFocus()")
		if self.epgButtons:
			try:
				self.setFocus(self.epgButtons[self.epgChIDX][self.epgBtnIDX][self.epgButtonsBtnData_BTN])
			except:
				debug("btn idx out of range")
				if self.epgChIDX >= len(self.epgButtons):
					self.epgChIDX = len(self.epgButtons)-1

				chanBtnLen = len(self.epgButtons[self.epgChIDX])
				if self.epgBtnIDX >= chanBtnLen:
					self.epgBtnIDX = chanBtnLen-1
				self.setFocus(self.epgButtons[self.epgChIDX][self.epgBtnIDX][self.epgButtonsBtnData_BTN])
		debug("< buttonFocus() epgChIDX=%i  epgBtnIDX=%i" % (self.epgChIDX, self.epgBtnIDX))

	###############################################################################################
	def setLogo(self, chIDX=0, reset=False):
		debug("setLogo() chIDX=%s" % chIDX)
		if not reset:
			filename = self.tvChannels.getLogo(chIDX)
		else:
			filename = LOGO_FILENAME
		self.getControl(self.CI_CHANNEL_LOGO).setImage(filename)

	###########################################################################################################
	def setIndicators(self):
		debug("> setIndicators()")

		firstTimeIntervalSecs = self.currentTime.getTimeInterval(1)[1]							# [HH:MM, secs]
		lastTimeIntervalSecs = self.currentTime.getTimeInterval(self.maxTimeBarIntervals-1)[1]	# [HH:MM, secs]
		# for each channel, set indicators left/right
		for chIDX, chButtons in enumerate(self.epgButtons):
			# LEFT
			prog = chButtons[0][self.epgButtonsBtnData_PROG]								# first btn on chan
			progTime = self.tvChannels.getProgAttr(prog, TVData.PROG_STARTTIME)				# prog start time
			if progTime < firstTimeIntervalSecs:
				self.epgIndicators[chIDX][0].setVisible(True)
			# RIGHT
			prog = chButtons[-1][self.epgButtonsBtnData_PROG]								# last btn on chan
			progTime = self.tvChannels.getProgAttr(prog, TVData.PROG_ENDTIME)				# prog end time
			if progTime==0 or progTime > lastTimeIntervalSecs:
				self.epgIndicators[chIDX][1].setVisible(True)

		# TOP INDICATOR
		topBottomIndicatorIdx = len(self.epgIndicators)-1		# last row in list [top, bottom]
		if self.allChannelIDX > 0:
			self.epgIndicators[topBottomIndicatorIdx][0].setVisible(True)

		# BOTTOM INDICATOR - change its position to bottom of current progs area heights
		if (self.allChannelIDX + self.epgMaxDisplayChannels) < self.tvChannels.getChannelNamesSZ():
			ctrl = self.epgIndicators[topBottomIndicatorIdx][1]
			xpos, ypos = ctrl.getPosition()
			ypos = self.epgProgsY + self.epgProgsH
			ctrl.setPosition(xpos, ypos)
			ctrl.setVisible(True)

		debug("< setIndicators()")

	##############################################################################################
	def updateTitle(self):
		debug("> updateTitle() epgChIDX=%i epgBtnIDX=%i" % (self.epgChIDX, self.epgBtnIDX))

		try:
			prog = self.getCurrentProgramme()
			title = self.tvChannels.getProgAttr(prog, TVData.PROG_TITLE)
#			self.getControl(self.CLBL_PROG_TITLE).setLabel(title, self.titleFont, self.titleColour)
			self.getControl(self.CLBL_PROG_TITLE).setLabel(title)

			# make desc "start time-end time: description"
			startTime = self.tvChannels.getProgAttr(prog, TVData.PROG_STARTTIME)
			descText = self.currentTime.timeToHHMM(startTime, self.use24HourClock) + "-"
			endTime = self.tvChannels.getProgAttr(prog, TVData.PROG_ENDTIME)
			if not endTime:
				descText += "??:??"
			else:
				descText += self.currentTime.timeToHHMM(endTime, self.use24HourClock)

			desc = self.tvChannels.getProgAttr(prog, TVData.PROG_DESC)
			if desc:
				descText += ": " + desc[:70].replace('\n',' ')
			self.getControl(self.CLBL_PROG_DESC).setLabel(descText)
		except:
			self.getControl(self.CLBL_PROG_TITLE).setLabel("Error")
		debug("< updateTitle()")

	##############################################################################################
	def updateNowTimeLine(self):
		debug("> updateNowTimeLine()")
		maxTimeBarIntervals = self.currentTime.getTimeIntervalSZ()
		currentTime = self.currentTime.getSystemTime()
		firstInterval = self.currentTime.getTimeInterval(1)[1]		                # [HH:MM, secs]
		lastInterval = self.currentTime.getTimeInterval(maxTimeBarIntervals-1)[1]	# [HH:MM, secs]

		self.nowTimeCI.setVisible(False)
		if currentTime >= firstInterval and currentTime <= lastInterval:
			offsetsecs = currentTime - firstInterval
			xpos = self.epgProgsX + int((offsetsecs/60) * self.epgPixelsPerMin)		# add time offset
			self.nowTimeCI.setPosition(xpos, self.epgY)
			self.nowTimeCI.setHeight(self.epgH)
			self.nowTimeCI.setVisible(True)

		debug("< updateNowTimeLine()")

	# put times into epg intervals, using requested clock format.
	# now also draws current time indicator line.
	def updateTimeBarIntervals(self):
		debug("> updateTimeBarIntervals()")
		# setup times on timebar above epg
		maxTimeBarIntervals = self.currentTime.setupTimeBar(self.maxTimeBarIntervals, self.use24HourClock)

		# Draw time intervals. last timebar time not displayed
		for idx, ctrl in enumerate(self.epgTimeBar):
			txt = self.currentTime.getTimeInterval(idx)[0]		                    # [HH:MM, secs]
			ctrl.setLabel(txt)
		debug("< updateTimeBarIntervals()")



###########################################################################################################
class ProgDescDialog(xbmcgui.WindowXMLDialog):

	# control id's
	CGRP_DIALOG = 2000
	CLBL_PROG_TITLE = 1
	CLBL_SUBTITLE = 2
	CLBL_GENRE = 4
	CLBL_DATETIME = 5
	CTB_DESC = 6
	CLBL_B = 7
	CLBL_X = 8
	CLBL_Y = 9
	CLBL_BACK = 10

	def __init__( self, *args, **kwargs ):
		debug("ProgDescDialog() init")
		self.isStartup = True
		self.optReInit = None

	#################################################################################################################
	def onInit( self ):
		debug("> ProgDescDialog().onInit() isStartup=%s" % self.isStartup)
		if self.isStartup:
			self.getControl(self.CLBL_PROG_TITLE).setLabel(self.title)
			self.getControl(self.CLBL_SUBTITLE).setLabel(self.subTitle)
			self.getControl(self.CLBL_GENRE).setLabel(self.genre)
			self.getControl(self.CLBL_DATETIME).setLabel(self.datetime)
			self.getControl(self.CTB_DESC).setText(self.desc)

			# B BTN - REC btn if tvcard enabled
			if self.isTimer == None:										# no tv card
				self.getControl(self.CLBL_B).setVisible(False)
			else:
				self.getControl(self.CLBL_B).setVisible(True)				# show rec btn
				if not self.isTimer:
					self.getControl(self.CLBL_B).setLabel(__language__(422))	# RECORD
				else:
					self.getControl(self.CLBL_B).setLabel(__language__(426))	# cancel rec

			if self.isFav:
				self.getControl(self.CLBL_X).setLabel(__language__(520))		# CANCEL FAV
			else:
				self.getControl(self.CLBL_X).setLabel(__language__(507))		# FAV
			self.getControl(self.CLBL_Y).setLabel(__language__(514))		# IMDb
			self.getControl(self.CLBL_BACK).setLabel(__language__(500))		# BACK

			self.isStartup = False

		debug("< ProgDescDialog().onInit()")


	#################################################################################################################
	def onAction(self, action):
		try:
			actionID = action.getId()
			if not actionID:
				actionID = action.getButtonCode()
		except: return
		debug( "onAction(): actionID=%i" % actionID )

		if actionID in EXIT_SCRIPT:
			debug("ProgDescDialog() EXIT_SCRIPT")
			self.close()
		elif actionID in CLICK_B or actionID == ACTION_REMOTE_RECORD:		# RECORD / cancel record
			debug("ProgDescDialog() CLICK_B")
			if self.isTimer != None:										# disabled
				if not self.isTimer:
					if callSaveProgramme():									# record
						self.optReInit = INIT_TIMERS
						self.close()
				elif callManageSaveProgramme():								# cancel record
					self.optReInit = INIT_TIMERS
					self.close()
		elif actionID in CLICK_X:											# FAV
			debug("ProgDescDialog() CLICK_X")
			global mytvFavShows
			chID, chName, chIDAlt = mytv.tvChannels.getChannelInfo(mytv.allChannelIDX+mytv.epgChIDX)
			if not self.isFav:
				# ADD fav
				if mytvFavShows.addToFavShows(self.title, chID, chName):
					self.optReInit = INIT_FAV_SHOWS
					self.close()
			else:
				# CANCEL fav
				if mytvFavShows.deleteShow(self.title, chID):
					self.optReInit = INIT_FAV_SHOWS
					self.close()
		elif actionID in CLICK_Y:											# IMDB
			debug("ProgDescDialog() CLICK_Y")
			self.getControl(self.CGRP_DIALOG).setVisible(False)
			callIMDB()
			self.getControl(self.CGRP_DIALOG).setVisible(True)

	#################################################################################################################
	def onClick(self, controlID):
		pass

	###################################################################################################################
	def onFocus(self, controlID):
		pass

	###################################################################################################################
	def ask(self,title,subTitle,genre,datetime,desc,isTimer=None,isFav=False):
		debug("> ProgDescDialog().ask()")
		self.title = title
		self.subTitle = subTitle
		self.genre = genre
		self.datetime = datetime
		self.desc = desc
		self.isTimer = isTimer
		self.isFav = isFav
		self.doModal()
		debug("< ProgDescDialog() optReInit=%s" % self.optReInit)
		return self.optReInit



#######################################################################################################################    
# Realtime clock
#######################################################################################################################    
class Timer(Thread): 
	def __init__(self, motherclass, use24HourClock=True):
		debug("> **** Timer() init")
		Thread.__init__(self)
		self.mother = motherclass #self.mother will be the same as 'self' in the main class
		self.running=0
		self.use24HourClock = use24HourClock
		debug("< **** Timer() init")

	def run(self):
		if self.running:
			return
		debug("Timer().run() running: %s use24HourClock: %s" % (self.running, self.use24HourClock))

		self.running=1
		while self.running:
			time.sleep(1)
			if self.use24HourClock:
				format = "%H:%M:%S"
			else:
				format = "%I:%M:%S %p"
			text = time.strftime(format, time.localtime())
			# strip leading 0 in 12hr mode
			if not self.use24HourClock:
				if text[0] == '0': text = text[1:]

			self.mother.clockLbl.setLabel(text)

	def setClock(self, use24HourClock):
		debug("setClock() use24HourClock: " + str(use24HourClock))
		self.use24HourClock = use24HourClock

	def stop(self):
		debug( "Timer().stop() self.running: " +str(self.running))
		if self.running:
			self.running = 0
			self.join()


#################################################################################################################
class ButtonColorPicker(xbmcgui.WindowDialog):
	def __init__(self):
		debug("> ButtonColorPicker().init")

		setResolution(self)

		width = 620
		height = 430
		originX = int((REZ_W /2) - (width /2))
		originY = int((REZ_H /2) - (height /2)) +10
		try:
			self.addControl(xbmcgui.ControlImage(originX, originY, width, height, DIALOG_PANEL))
		except: pass

		# TITLE
		xpos = originX + 70
		ypos = originY + 30
		self.titleCL = xbmcgui.ControlLabel(xpos, ypos, width, 40, '', FONT13, "0xFFFFFF66")
		self.addControl(self.titleCL)

		# PICKER BUTTON
		self.pickerW = 350
		self.pickerH = 60
		self.pickerX = originX + 225
		self.pickerY = originY + 150
		self.pickerCB = None
		self.pickerFileIDX = 0

		# CHANGER buttons
		changerBtnW = 145
		changerBtnH = 35

		# background changer NEXT
		xpos = originX + 70
		ypos = originY + 90
		self.backgNextCB = xbmcgui.ControlButton(xpos, ypos, changerBtnW, changerBtnH, __language__(602))
		self.addControl(self.backgNextCB)
		self.backgNextCB.setVisible(False)
		self.backgNextCB.setEnabled(False)

		# background changer PREV
		ypos += changerBtnH + 10
		self.backgPrevCB = xbmcgui.ControlButton(xpos, ypos, changerBtnW, changerBtnH, __language__(603))
		self.addControl(self.backgPrevCB)
		self.backgPrevCB.setVisible(False)
		self.backgPrevCB.setEnabled(False)

		# TEXT changer NEXT
		ypos += changerBtnH + 20
		self.textNextCB = xbmcgui.ControlButton(xpos, ypos, changerBtnW, changerBtnH, __language__(604))
		self.addControl(self.textNextCB)
		self.textNextCB.setVisible(False)
		self.textNextCB.setEnabled(False)

		# TEXT changer PREV
		ypos += changerBtnH + 10
		self.textPrevCB = xbmcgui.ControlButton(xpos, ypos, changerBtnW, changerBtnH, __language__(605))
		self.addControl(self.textPrevCB)
		self.textPrevCB.setVisible(False)
		self.textPrevCB.setEnabled(False)

		# accept button
		ypos += changerBtnH + 30
		self.acceptCB = xbmcgui.ControlButton(xpos, ypos, 70, 25, __language__(360))	# OK
		self.addControl(self.acceptCB)

		# cancel button
		xpos += 90
		self.cancelCB = xbmcgui.ControlButton(xpos, ypos, 70, 25, __language__(355))	# cancel
		self.addControl(self.cancelCB)

		# DISABLE button
		xpos += 90
		self.disableCB = xbmcgui.ControlButton(xpos, ypos, 80, 25, __language__(606))	# turn off
		self.addControl(self.disableCB)
		self.disableCB.setEnabled(False)
		self.disableCB.setVisible(False)

		self.textColor = ""
		self.backgFile = ""
		debug("< ButtonColorPicker().init")

	def setNav(self):
		debug("ButtonColorPicker().setNav()")
		self.backgNextCB.controlUp(self.acceptCB)
		self.backgNextCB.controlDown(self.backgPrevCB)

		self.backgPrevCB.controlUp(self.backgNextCB)
		self.backgPrevCB.controlDown(self.textNextCB)

		self.textNextCB.controlUp(self.backgPrevCB)
		self.textNextCB.controlDown(self.textPrevCB)

		self.textPrevCB.controlUp(self.textNextCB)
		self.textPrevCB.controlDown(self.acceptCB)

		self.acceptCB.setNavigation(self.textPrevCB,self.backgNextCB,self.disableCB,self.cancelCB)
		self.cancelCB.setNavigation(self.textPrevCB,self.backgNextCB,self.acceptCB,self.disableCB)
		self.disableCB.setNavigation(self.textPrevCB,self.backgNextCB,self.cancelCB,self.acceptCB)

	def drawPicker(self):
		debug("> drawPicker()")
		try:
			self.removeControl(self.pickerCB)
		except: pass

		text = ""
		if self.backgFile:
			text += " File: " + os.path.basename(self.backgFile)
		if self.textColor:
			text += " Text: " + self.textColor

		texture = prefixDirPath(self.backgFile, DIR_EPG)
		debug("texture=%s  textColor=%s" % (texture, self.textColor))
		self.pickerCB = xbmcgui.ControlButton(self.pickerX, self.pickerY, self.pickerW, self.pickerH, \
								text, texture, texture, font=FONT13, textColor=self.textColor, \
								alignment=XBFONT_CENTER_X|XBFONT_CENTER_Y)
		self.addControl(self.pickerCB)
		debug("< drawPicker()")

	# show this dialog and wait until it's closed
	def ask(self, backgFile="", textColor="", title=""):
		debug("> ask()")
		debug("backgFile=%s  textColor=%s" % (backgFile, textColor))

		self.backgFile = backgFile
		self.textColor = textColor
		if title:
			selectText = title
		elif backgFile and textColor:
			selectText = __language__(599)	# back + text
		elif backgFile:
			selectText = __language__(600)	# backg
		elif textColor:
			selectText = __language__(601)	# text
		else:
			selectText = ""
		self.titleCL.setLabel(selectText)

		if textColor:
			self.textNextCB.setVisible(True)
			self.textNextCB.setEnabled(True)
			self.textPrevCB.setVisible(True)
			self.textPrevCB.setEnabled(True)

		if backgFile:
			# show disable button
			self.disableCB.setVisible(True)
			self.disableCB.setEnabled(True)
			self.fileList = listDir(DIR_EPG, '.png', getFullFilename=True)
			if not self.fileList:
				messageOK("Alert","No background colour files found in folder:", DIR_EPG)
				self.backgFile = ""
				self.textColor = ""
			else:
				self.backgNextCB.setVisible(True)
				self.backgNextCB.setEnabled(True)
				self.backgPrevCB.setVisible(True)
				self.backgPrevCB.setEnabled(True)

		if self.backgFile or self.textColor:
			self.drawPicker()
			self.setNav()

		if self.backgFile:
			self.setFocus(self.backgNextCB)
		elif self.textColor:
			self.setFocus(self.textNextCB)
		else:
			self.setFocus(self.cancelCB)

		self.doModal()
		debug("< ask() backgFile=%s textColor=%s" % (self.backgFile, self.textColor))
		return self.backgFile, self.textColor

	def onAction(self, action):
		try:
			actionID = action.getId()
			if not actionID:
				actionID = action.getButtonCode()
		except: return
		debug( "onAction(): actionID=%i" % actionID )
		if actionID in EXIT_SCRIPT + CANCEL_DIALOG:
			self.backgFile = ""
			self.textColor = ""
			self.close()

	def onControl(self, control):
		if control == self.cancelCB:
			# unset values
			self.backgFile = ""
			self.textColor = ""
			self.close()
		elif control == self.acceptCB:
			self.close()
		elif control == self.backgNextCB:
			self.pickerFileIDX += 1
			if self.pickerFileIDX >= len(self.fileList):
				self.pickerFileIDX = 0
			self.backgFile = self.fileList[self.pickerFileIDX]
			self.drawPicker()
			self.setFocus(control)
		elif control == self.backgPrevCB:
			self.pickerFileIDX -= 1
			if self.pickerFileIDX < 0 :
				self.pickerFileIDX = len(self.fileList)-1
			self.backgFile = self.fileList[self.pickerFileIDX]
			self.drawPicker()
			self.setFocus(control)
		elif control == self.textNextCB:
			# move fwd in 0x33 increments
			hex_num = int(self.textColor.replace('0xFF',''),16)
			if self.textColor[-4:] == "FFFF":
				hex_num +=  0x320001
			elif self.textColor[-2:] == "FF":
				hex_num += 0x003201
			else:
				hex_num += 0x33
			if hex_num >= 0xFFFFFF:
				self.textColor = "0xFF000066"		# dark blue
			else:
				self.textColor = "0xFF" + upper(hex(hex_num).replace('0x','').rjust(6, '0'))

			self.drawPicker()
			self.setFocus(control)
		elif control == self.textPrevCB:
			# move back in 0x33 increments
			hex_num = int(self.textColor.replace('0xFF',''),16)
			if self.textColor[-4:] == "0000":
				hex_num -=  0x320001
			elif self.textColor[-2:] == "00":
				hex_num -= 0x003201
			else:
				hex_num -= 0x33
			if hex_num < 0:
				self.textColor = "0xFFFFFFFF"
			else:
				self.textColor = "0xFF" + upper(hex(hex_num).replace('0x','').rjust(6, '0'))
			self.drawPicker()
			self.setFocus(control)
		elif control == self.disableCB:
			self.backgFile = None
			self.textColor = None
			self.close()

#################################################################################################################
def viewReadme():
	debug("> viewReadme()")
	fn = getReadmeFilename()
	doc = readFile(fn)
	if not doc:
		doc = "Readme not found: " + fn
	tbd = TextBoxDialogXML("script-bbb-textbox.xml", DIR_HOME, "Default")
	tbd.ask(__language__(550), doc)
	del tbd
	debug("< viewReadme()")

#################################################################################################################
def viewChangelog():
	debug("> viewChangelog()")
	fn = os.path.join(DIR_HOME, "Changelog.txt")
	doc = readFile(fn)
	if not doc:
		doc = "Changelog not found: " + fn

	tbd = TextBoxDialogXML("script-bbb-textbox.xml", DIR_HOME, "Default")
	tbd.ask(__language__(551), doc)
	del tbd
	debug("< viewChangelog()")


#################################################################################################################
# Re-configure datasource. Not all datasource require configuring.
#################################################################################################################
def configDataSource(forceReset=True):
	debug("> configDataSource() forceReset=%s" % forceReset)
	success = False

	global dataSource
	while not success:
		try:
			success = dataSource.config(forceReset)	# force reset
			if not success:
				if not xbmcgui.Dialog().yesno(__language__(532), __language__(216)):	# setup now?
					break
				else:
					forceReset = True
		except:
			handleException("configDataSource()")

	debug("< configDataSource() success=%s" % success)
	return success

#################################################################################################################
# Re-configure saveprogramme. Not all saveprogramme require configuring.
#################################################################################################################
def configSaveProgramme(reset=True):
	debug("> configSaveProgramme() reset=%s" % reset)
	success = False

	global saveProgramme
	if saveProgramme:
		try:
			while not success:
				success = saveProgramme.config(reset)
				if not success:
					# setup now ?
					if xbmcgui.Dialog().yesno(__language__(534),__language__(216)):
						reset = True
					else:
						break		# quit anyway
		except AttributeError:
			success = True
		except:
			handleException("configSaveProgramme()")

	debug("< configSaveProgramme() success=%s" % success)
	return success


#################################################################################################################
# Choose a SaveProgramme module from a list of files named SaveProgramme_<somename>.py in subfolder
#################################################################################################################
def selectSaveProgramme():
	debug("> selectSaveProgramme()")
	spName = None

	# create menu
	menuList = []
	# get all the files
	menuList = listDir(DIR_SAVEPROGRAMME, '.py')
	menuList.insert(0, config.VALUE_SAVE_PROG_NOTV)             # no tv card
	menuList.insert(0, __language__(500))                       # exit

	# popup dialog to select choice
	selectDialog = DialogSelect()
	selectDialog.setup(__language__(533), rows=len(menuList), width=270, panel=DIALOG_PANEL)
	selectedPos, action = selectDialog.ask(menuList)
	if selectedPos > 0:
		if selectedPos == 1:
#			spName = config.VALUE_SAVE_PROG_NOTV
			spName = ""		# no tv card
		else:
			spName = menuList[selectedPos]
		config.setSystem(config.KEY_SYSTEM_SAVE_PROG, spName)

	debug("< selectSaveProgramme() %s" % spName)
	return spName

#######################################################################################################################    
# Import SaveProgramme_<somename>.py as determined by configuration file.
# None (no config setting) is no SP set - force selection.
# "" is No TV Card to be used.
#######################################################################################################################    
def importSaveProgramme():
	debug("> importSaveProgramme()")
	success = False
	global saveProgramme
	try:
		del saveProgramme
		gc.collect()
	except: pass
	saveProgramme = None

	# read config file
	spName = config.getSystem(config.KEY_SYSTEM_SAVE_PROG)
	if spName == None:      # setting not exist
		spName = selectSaveProgramme()

	if spName in ("",config.VALUE_SAVE_PROG_NOTV):		# no tv card
		success = True
	elif spName:
		# import module
		try:
			debug("importing SaveProgramme: %s" % spName)
			sys.path.insert(0, DIR_SAVEPROGRAMME)
			module = __import__(spName, globals(), locals(), [])
			saveProgramme = module.SaveProgramme(cachePath=DIR_CACHE)
			sys.path.remove(DIR_SAVEPROGRAMME)
			success = configSaveProgramme(False)
		except:
			messageOK(__language__(99), __language__(116))
			handleException()

	if not success:
		debug("no saveProgramme selected/imported/configured, removed tvcard setting")
		config.action(config.SECTION_SYSTEM, config.KEY_SYSTEM_SAVE_PROG, mode=ConfigHelper.MODE_REMOVE_OPTION)
		saveProgramme = None
		success = True              # pretend it all ok now
	sys.path
	debug("< importSaveProgramme() success=%s" % success)
	return success


#################################################################################################################
def configChannelName():
	debug("> configChannelName()")
	changed = False
	# exit, No Channel name, No IDs, ID, alt.ID
	menuList = [__language__(500), __language__(577), __language__(560), __language__(561), __language__(562)]

	# popup dialog to select choice
	selectDialog = DialogSelect()
	selectDialog.setup(__language__(539), rows=len(menuList), width=270, panel=DIALOG_PANEL)
	selectedPos, action = selectDialog.ask(menuList)
	if selectedPos > 0:	
		# 0 no ch names or id
		# 1 no ch id shown
		# 2 ch id
		# 3 alt ch id
		changed = config.setSystem(config.KEY_SYSTEM_SHOW_CH_ID, selectedPos-1)

	debug("< configChannelName() changed=%s" % changed)
	return changed


#################################################################################################################
def configFetchTimersStartup():
	return configYesNo(__language__(400),__language__(535), \
					   config.KEY_SYSTEM_FETCH_TIMERS_STARTUP, config.SECTION_SYSTEM)

#################################################################################################################
def configScriptUpdateCheck():
    return configYesNo(__language__(400), __language__(553), config.KEY_SYSTEM_CHECK_UPDATE, config.SECTION_SYSTEM)

#################################################################################################################
def configTimerClash():
	return configYesNo(__language__(400), __language__(538), \
					   config.KEY_SYSTEM_TIMER_CLASH_CHECK, config.SECTION_SYSTEM)

#################################################################################################################
# MENU ITEM - Is LiveSportOnTV MainMenu option visible in main menu
#################################################################################################################
def configLSOTV():
	return configYesNo(__language__(400),__language__(549), \
					   config.KEY_SYSTEM_USE_LSOTV, config.SECTION_SYSTEM)

#################################################################################################################
# MENU ITEM - Use 12 or 24hr clock and epg intervals
#################################################################################################################
def configClock():
	return configYesNo(__language__(400), __language__(536), \
					   config.KEY_SYSTEM_CLOCK, config.SECTION_SYSTEM, yesButton="24Hr", noButton="12Hr")


############################################################################################################
def configSMB(reset=True):
    debug("> myTV.configSMB() reset=%s" % reset)
    success = False
    cSMB = ConfigSMB(config, config.SECTION_SMB, __language__(546), \
                          fnTitle=__language__(565), \
                          fnDefaultValue=config.VALUE_SMB_FILE,\
                          pathDefaultValue=config.VALUE_SMB_PATH)
    while not success:
        if not reset:
            smbDetails = cSMB.checkAll(silent=True)
            if smbDetails:
                success = True
            elif not xbmcgui.Dialog().yesno(__language__(959), __language__(309)):
                break

        if not success or reset:
            cSMB.ask()
            reset = False	# allows changes to be checked

    debug("< myTV.configSMB() success= %s" % success)
    return success


#######################################################################################################################    
# List all files SMB share
#######################################################################################################################    
def smbGetVideoFiles(remote, share, dirPath=''):
	debug("> smbGetVideoFiles() dirPath=" + dirPath)
	if dirPath.endswith('/'):
		dirPath = dirPath[:-1]
	success = False
	allPathList = []
	files = []
	extList = ['.ts','.mov','.qt','.divx','.xvid','.vob','.wmv','.asf','.asx','.m2v','.avi','.mpg','.mpeg','.mp4','.mkv','.avc','.flv']
	paths = []

	dialogProgress.create(__language__(202), __language__(300))
	# files only = True, folders only = False
	def listpath(path='/*'):
		debug("> listpath() path="+path)
		files = []
		list_path = []
		try:
			if path[-1] == '/':
				path += '*'
			elif not path.endswith('/*'):
				path += '/*'
			list_path=remote.list_path(share, path=path, timeout=15)
		except: pass

		# save folder name
		sz = len(list_path)-2
		if sz > 0:		# ignore folders with just . and ..
			files = [path.replace('/*',''), list_path]
		debug("< listpath() file count=" + str(sz))
		return files

	dialogProgress.update(0, __language__(300), '/*')
	pathList = listpath(dirPath)
	if pathList:
		allPathList.append(pathList)

	# process files, remove folders and none video files
	MAX = len(allPathList)
	count = 0
	debug("recurse folder discover")
	for count, pathData in enumerate(allPathList):
		pathName, fileList = pathData
		percent = int( float( count * 100) / MAX )
		dialogProgress.update(percent, __language__(300), pathName)

		# for each data list [path, [SharedFiles]]
		for sharedfile in fileList:
			longname = sharedfile.get_longname()
			# reject . & .. directory names
			if longname in ['.','..']: continue

			if sharedfile.is_directory():			# recurse into directory
				allPathList.append(listpath(pathName + '/' +longname))
				continue							# always reject directory as a filename

			# ignore system/hidden/0 len files
			fsize = sharedfile.get_filesize()
			if (not fsize) or sharedfile.is_hidden() or sharedfile.is_system():
				continue

			# its a normal file, check its a valid extension
			fn, ext = os.path.splitext(longname)
			try:
				idx =  extList.index(lower(ext))
				# valid file & ext, get create time
				ctime = sharedfile.get_ctime_epoch()
				# remove smb dirPath from pathname
				files.append([ctime, pathName.replace(dirPath,''), longname, fsize])
			except: pass

	dialogProgress.close()

	files.sort()
	sz = len(files)
	if not sz:
		messageOK(__language__(202),"No suitable video files found.")
	debug("< smbGetVideoFiles() file list sz=%s" % sz)
	return files

#######################################################################################################################    
# show menu of strm packs, then menu of contents which can be selected & played
#################################################################################################################
def playStreamPack():
	debug("> playStreamPack()")

	extList = ( '.strm', '.pls','.m3u' )
	fileList = []
	for ext in extList:
		extFileList = listDir(DIR_CACHE, ext, getFullFilename=True)
		if extFileList:
			fileList += extFileList

	if not fileList:
		messageOK(__language__(512),__language__(105))
	else:
		fileList.sort()
		fileList.insert(0, __language__(500))	# exit
		selectDialog = DialogSelect()
		selectDialog.setup(__language__(567), rows=len(fileList), width=350, panel=DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(fileList)
		if selectedPos > 0:
			success = True
			streamFN = os.path.join(DIR_CACHE, fileList[selectedPos])
			debug("streamFN= %s" % streamFN)
			try:
				xbmc.Player().play(streamFN)
			except:
				debug('xbmc.Player().play() failed trying xbmc.PlayMedia() ')
				try:
					cmd = 'xbmc.PlayMedia(%s)' % streamFN
					xbmc.executebuiltin(cmd)
				except:
					handleException('xbmc.PlayMedia()')
					success = False

			if success:
				xbmc.executebuiltin('XBMC.ReplaceWindow(2005)')

	debug("< playStreamPack()")


#######################################################################################################################    
# show all files on SMB as a menu, 
#################################################################################################################
def smbMenuFiles():
	debug("> smbMenuFiles()")
	url = ''
	remote = None
	GB = float(1024*1024*1024)
	MB = float(1024*1024)

	ip = config.getSMB(config.KEY_SMB_IP)
	smbPath = config.getSMB(config.KEY_SMB_PATH)
	remote, remoteInfo = smbConnect(ip, smbPath)
	if remote:
		domain,user,password,pcname,share,dirPath = remoteInfo

		# loop until exit
		selectedPos = 0
		while not url:
			# fetch all video files
			menu = [__language__(500), __language__(308)]
			files = smbGetVideoFiles(remote, share, dirPath)
			if not files:
				break

			# make menu
			for ctime, pathName, longname, fsize in files:
				longDate = time.strftime("%d-%m-%Y %H:%M", time.localtime(ctime))
				if fsize > GB:
					lbl2 = longDate + ' (%0.2f Gb)' % (float(fsize/GB))
				else:
					lbl2 = longDate + ' (%0.2f Mb)' % (float(fsize/MB))
				menu.append(xbmcgui.ListItem(longname, label2=lbl2))

			# popup dialog to select choice
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(568), rows=len(menu), width=620, panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menu, selectedPos)
			if selectedPos <= 0:
				break
			elif selectedPos == 1:	# refresh
				continue

			selectedPos -= 2 # allow for refresh & exit options
			# remove any leading '/' from pathname
			path = files[selectedPos][1]
			if path and path[0] == '/':
				path = path[1:]

			# add fname
			url = smbPath + path + files[selectedPos][2]
			if not playMedia(url):
				url = ''		# failed to play

	debug("< smbMenuFiles()")
	return url

#################################################################################################################
# MENU ITEM - select save programme method, SMB or external custom module (SaveProgramme.py)
#################################################################################################################
def callSaveProgramme(prog=None, channelInfo=None, confirmRequired=True):
	debug("> callSaveProgramme()")
	success = False
	global saveProgramme
	# if MAC, send WOL nd check is awake before continuing
	if saveProgramme and sendWOL(True):

		# get highlighted programme
		if not prog:
			prog = mytv.getCurrentProgramme()
		if not channelInfo:
			channelInfo = mytv.getCurrentChannelInfo()

		# check for valid prog
		title = mytv.tvChannels.getProgAttr(prog, TVData.PROG_TITLE).encode('latin-1', 'replace')
		if not validProgramme(title):
			debug("no programme/no channel, ignoring")

		# check if already finished
		elif mytv.tvChannels.getProgAttr(prog, TVData.PROG_ENDTIME) <= time.mktime(time.localtime()):
			messageOK(__language__(801), __language__(802))				# already finished

		# do timer clash if reqd.
		elif config.getSystem(config.KEY_SYSTEM_TIMER_CLASH_CHECK) and mytv.manageTimers.checkTimerClash(prog):
			success = False
		else:
			try:
				saveProgMethod = saveProgramme.saveMethod()
			except:														# no save method
				saveProgMethod = SAVE_METHOD_CUSTOM
			debug("SaveProgramme saveProgMethod=%s" % saveProgMethod)

			if saveProgMethod == SAVE_METHOD_SMB:
				# save using internal SMB method
				success = saveProgrammeSMB(channelInfo, prog, False)
			else:
				# check it is setup
				if configSaveProgramme(False):
					try:
						chName = mytv.tvChannels.getChannelName(mytv.allChannelIDX+mytv.epgChIDX)
						startTime = mytv.tvChannels.getProgAttr(prog, TVData.PROG_STARTTIME)
						displayDate = time.strftime("%a %d %b, %H:%M",time.localtime(startTime))
						# Confirm record ?
						if xbmcgui.Dialog().yesno(saveProgramme.getName(), title, displayDate, chName, __language__(355), __language__(800)):
							doRec = True
							# allow for any custom saveprogramme record prompts. None indicates failure
							if hasattr(saveProgramme, "customPrompts") and saveProgramme.customPrompts() == None:
								doRec = False

							if doRec:
								# call external Save Programme module
								dialogProgress.create(config.getSystem(config.KEY_SYSTEM_SAVE_PROG))    # module name
								returnValue = saveProgramme.run(channelInfo, prog, confirmRequired)
								if returnValue:
									success = True
								dialogProgress.close()

								# if save method requires SMB send, send it now
								if success and saveProgMethod == SAVE_METHOD_CUSTOM_SMB:
									# we can only send via SMB if we have data to write to a file
									if not isinstance(returnValue, bool):
										success = saveProgrammeSMB(channelInfo, prog, data=returnValue, showSuccess=False)
					except:
						handleException("callSaveProgramme()")

			# save to local timer file if we dont rely on saveProgramme to fetch them
			if success and not hasattr(saveProgramme, "getRemoteTimers"):
				debug("save timer")
				mytv.timersDict, mytv.timersProgIDList = mytv.manageTimers.saveTimer(prog, channelInfo)

	debug("< callSaveProgramme() success=%s" % success)
	return success


#######################################################################################################################    
# show list of timers to be selected, then passed onto saveProgramme to delete
# or deleted with manageTimers
#######################################################################################################################    
def callManageSaveProgramme():
	debug("> callManageSaveProgramme()")
	deleted = False
	# get highlighted programme
	programme = mytv.getCurrentProgramme()
	channel = mytv.getCurrentChannel()

	global saveProgramme
	if saveProgramme:
		if hasattr(saveProgramme, "manage"):     # manage with it own menu eg. Nebula
			debug("do saveProgramme manage")
			timers = saveProgramme.manage()
			mytv.timersDict, mytv.timersProgIDList = mytv.manageTimers.refreshTimerFiles(timers)
			deleted = True
		else:
			debug("do local ManageTimers menu")
			# check if saveprogramme has a remote delete func
			doRemoteDelete = hasattr(saveProgramme, "deleteTimer")
			debug("doRemoteDelete=%s" % doRemoteDelete)

			# show menu and delete each timer as selected
			while True:
				timer = mytv.manageTimers.ask()
				if not timer: break

				startTime = timer[ManageTimers.REC_STARTTIME]
				if doRemoteDelete:
					if saveProgramme.deleteTimer(timer) and mytv.manageTimers.deleteTimer(startTime):
						deleted = True
				else:
					if mytv.manageTimers.deleteTimer(startTime):
						deleted = True

			# reload timers keys
			if deleted:
				mytv.timersDict, mytv.timersProgIDList = mytv.manageTimers.getTimers()

	debug("< callManageSaveProgramme() deleted=%s" % deleted)
	return deleted


#######################################################################################################################    
def callIMDB(title=''):
	debug("> callIMDB()")
	if not title:
		title = mytv.getCurrentProgrammeTitle()
		if not validProgramme(title):
			title = None

	if title:
		imdbwin = IMDbWin("script-bbb-imdb.xml", DIR_HOME, "Default")
		imdbwin.ask(title)
		del imdbwin
	debug("< callIMDB()")

#######################################################################################################################    
def callTVCom():
	debug("> callTVCom()")
	success = False

	# import module
	try:
		pathHome = "Q:\\Scripts\\tv.com\\"
		pathSystem = os.path.join(pathHome, "System")
		moduleName = "default"
		pathFull = os.path.join( pathHome, moduleName + ".py" )
		if not fileExist(pathFull):
			messageOK(__language__(513), __language__(106))
		else:
			prog = mytv.getCurrentProgramme()
			progTitle = mytv.tvChannels.getProgAttr(prog, TVData.PROG_TITLE)
			debug("importing tvcom")	
			sys.path.insert(0, pathSystem)
			sys.path.insert(0, pathHome)
			module = __import__(moduleName, globals(), locals(), [])
			tvcom = module.TVdotCom()
			tvcom.ask(progTitle, searchType=True)
			del tvcom
			sys.path.remove(pathHome)
			sys.path.remove(pathSystem)
			success = True
	except:
		handleException("callTVCom()")

	debug("< callTVCom() success: " +str(success))
	return success

#######################################################################################################################    
# Save highlighted programme info 
#######################################################################################################################    
def saveProgrammeSMB(channelInfo, programme, data='', showSuccess=False):
	debug("> saveProgrammeSMB()")
	success = False

	configFilename = config.getSMB(config.KEY_SMB_FILE)
	ip = config.getSMB(config.KEY_SMB_IP)
	smbPath = config.getSMB(config.KEY_SMB_PATH)
	if not configFilename or not ip or not smbPath:
		doSave = configSMB(False)
	else:
		doSave = True

	if doSave:
		pst = ProgrammeSaveTemplate()
		localFile = os.path.join(DIR_CACHE, "temp.dat")
		title = mytv.tvChannels.getProgAttr(programme, TVData.PROG_TITLE).encode('latin-1','replace')

		# if DATA not supplied, load SAVE STRING from config file then expand
		if not data:
			template = config.getSystem(config.KEY_SYSTEM_SAVE_TEMPLATE)
			data = pst.format(channelInfo, programme, template)

		if not data:
			messageOK(__language__(422), __language__(108), template)
		else:
			try:
				# save data into a local file for sending
				debug("save data into a local file for sending: " + localFile)
				file(localFile,'w').write(data)
			except:
				messageOK(__language__(422),__language__(109), localFile)
			else:
				# expand $ substitutions
				remoteFile = pst.format(channelInfo, programme, configFilename)
				# send to smb
				remote, remoteInfo = smbConnect(ip, smbPath)
				if remote:
					domain,user,password,pcname,share,dirPath = remoteInfo
					remoteFile = dirPath + remoteFile
					success = smbSendFile(remote, share, localFile, remoteFile, not showSuccess)
					if success and showSuccess:
						messageOK(__language__(422), __language__(301))

			deleteFile(localFile)

	debug("< saveProgrammeSMB() success=%s" % success)
	return success

#######################################################################################################################    
# Edit the save programme template
#######################################################################################################################    
def configEditTemplate():
	debug("> configEditTemplate()")

	pst = ProgrammeSaveTemplate()
	value = config.getSystem(config.KEY_SYSTEM_SAVE_TEMPLATE)
	if value == None:
		value = ''

	while True:
		value = doKeyboard(value, __language__(547))
		if pst.validTemplate(value):
			config.setSystem(config.KEY_SYSTEM_SAVE_TEMPLATE, value)
			break
		else:
			messageOK(__language__(547), __language__(110))

	debug("< configEditTemplate()")

#######################################################################################################################    
# Config Wake On LAN MAC
#######################################################################################################################    
def configWOL():
    debug("> configWOL()")

    macOK = False
    mac = config.getSystem(config.KEY_SYSTEM_WOL)
    while True:
        mac = doKeyboard(mac, __language__(555) + " eg. 0:e:7f:ac:d6:4d")
        # check valid MAC
        if mac and not validMAC(mac):
            messageOK(__language__(555), __language__(134))
        else:
            config.setSystem(config.KEY_SYSTEM_WOL, mac)
            sendWOL(True)
            break

    debug("< configWOL()")

#######################################################################################################################    
# View the save programme template options
#######################################################################################################################    
class ProgrammeSaveTemplate:
	def __init__(self):
		debug("> ProgrammeSaveTemplate.init()")

		self.TEMPLATES = [['C','Channel ID', self.getChannelID],
						['c','Channel Name', self.getChannelName],
						['T','Title', self.getTitle],
						['N','Description', self.getDesc],
						['S','Start Date/Time DD//MM//YYYY HH:MM', self.getDateFullS],
						['s','Start Date/Time MM//DD//YYYY HH:MM', self.getDateFulls],
						['E','End Date/Time DD//MM//YYYY HH:MM', self.getDateFullE],
						['e','End Date/Time MM//DD//YYYY HH:MM', self.getDateFulle],
						['D','Start Date (DD)', self.getStartDate],
						['d','End Date (DD)', self.getEndDate],
						['M','Start Month (MM)', self.getStartMonth],
						['m','End Month (MM)', self.getEndMonth],
						['Y','Start Year (YYYY)', self.getStartYear],
						['y','End Year (YYYY)', self.getEndYear],
						['H','Start Hour (HH 24hr)', self.getStartHour],
						['h','End Hour (HH 24hr)', self.getEndHour],
						['I','Start Minutes (MM)', self.getStartMins],
						['i','End Minutes (MM)', self.getEndMins],
						['T','Start Seconds since epoch', self.getStartSecs],
						['t','End Seconds since epoch', self.getEndSecs],
						['L','Duration (HH:MM)', self.getDuration],
						['l','Duration (Mins)', self.getDurationMins]]
		self.PREFIX = '$'
		self.KEY = 0
		self.VALUE = 1
		self.FUNC = 2
		self.prog = None
		debug("< ProgrammeSaveTemplate.init()")

	def viewTemplates(self):
		debug("> ProgrammeSaveTemplate.viewTemplates()")
		menu = [__language__(500)]
		for key,value,func in self.TEMPLATES:
			menu.append(xbmcgui.ListItem(self.PREFIX+key, label2=value))

		selectDialog = DialogSelect()
		selectDialog.setup(__language__(548), rows=len(menu), panel=DIALOG_PANEL)
		selectDialog.ask(menu)
		del selectDialog
		debug("< ProgrammeSaveTemplate.viewTemplates()")

	def getTemplates(self):
		return self.TEMPLATES

	def validTemplate(self, text):
		debug("> validTemplate: template: %s " % text)
		success = False

		if text:
			matches = self.parseTemplate(text)
			for key in matches:
				success = False
				for template in self.TEMPLATES:
					if template[self.KEY] == key:
						success = True	# found
						break

				if not success:
					break	# abort search

		debug("< validTemplate() success=%s" % success)
		return success

	def getFunc(self,key):
		for template in self.TEMPLATES:
			if template[self.KEY] == key:
				return template[self.FUNC]
		return None

	def parseTemplate(self, template):
		matches = re.findall('\\'+self.PREFIX + '(.)', template)
		return matches

	def format(self, channelInfo, prog, template):
		debug("> format()")
		self.channelInfo = channelInfo
		self.prog = prog
		try:
			matches = self.parseTemplate(template)
			for match in matches:
				func = self.getFunc(match)
				if func:
					template = replace(template, self.PREFIX+match, func())
		except:
			handleException("ProgrammeSaveTemplate().format()")
			template = ''

		debug("< format()")
		return template

	def getChannelID(self):
		self.channelInfo[TVChannels.CHAN_ID]

	def getChannelIDAlt(self):
		self.channelInfo[TVChannels.CHAN_IDALT]

	def getChannelName(self):
		self.channelInfo[TVChannels.CHAN_NAME]

	def getTitle(self):
		return mytv.tvChannels.getProgAttr(self.prog, TVData.PROG_TITLE)

	def getDesc(self):
		return mytv.tvChannels.getProgAttr(self.prog, TVData.PROG_DESC)

	def getDateFullS(self):
		return time.strftime("%d/%m/%Y %H:%M",time.localtime(self.getStartSecsEpoch()))
	def getDateFullE(self):
		return time.strftime("%d/%m/%Y %H:%M",time.localtime(self.getEndSecsEpoch()))

	def getDateFulls(self):
		return time.strftime("%m/%d/%Y %H:%M",time.localtime(self.getStartSecsEpoch()))
	def getDateFulle(self):
		return time.strftime("%m/%d/%Y %H:%M",time.localtime(self.getEndSecsEpoch()))

	def getStartDate(self):
		return time.strftime("%d",time.localtime(self.getStartSecsEpoch()))
	def getEndDate(self):
		return time.strftime("%d",time.localtime(self.getEndSecsEpoch()))

	def getStartMonth(self):
		return time.strftime("%m",time.localtime(self.getStartSecsEpoch()))
	def getEndMonth(self):
		return time.strftime("%m",time.localtime(self.getEndSecsEpoch()))

	def getStartYear(self):
		return time.strftime("%Y",time.localtime(self.getStartSecsEpoch()))
	def getEndYear(self):
		return time.strftime("%Y",time.localtime(self.getEndSecsEpoch()))

	def getStartHour(self):
		return time.strftime("%H",time.localtime(self.getStartSecsEpoch()))
	def getEndHour(self):
		return time.strftime("%H",time.localtime(self.getEndSecsEpoch()))

	def getStartMins(self):
		return time.strftime("%M",time.localtime(self.getStartSecsEpoch()))
	def getEndMins(self):
		return time.strftime("%M",time.localtime(self.getEndSecsEpoch()))

	def getDuration(self):
		durSecs = self.getEndSecsEpoch() - self.getStartSecsEpoch()
		return time.strftime("%H:%M",time.localtime(durSecs))

	def getDurationMins(self):
		durMins = int((self.getEndSecsEpoch() - self.getStartSecsEpoch()) / 60)
		return str(durMins)

	def getStartSecs(self):
		return str(self.getStartSecsEpoch())
	def getStartSecsEpoch(self):
		return mytv.tvChannels.getProgAttr(self.prog, TVData.PROG_STARTTIME)
	def getEndSecs(self):
		return str(self.getEndSecsEpoch())
	def getEndSecsEpoch(self):
		return mytv.tvChannels.getProgAttr(self.prog, TVData.PROG_ENDTIME)

#################################################################################################################
# CONFIG EPG BUTTON COLOURS
#################################################################################################################
class ConfigEPGColours:
	def __init__(self):
		debug("> ConfigEPGColours() init()")

		self.EXT = '.png'
		self.MENU_OPT_CHNAME = "Channel Name Colour"
		self.MENU_OPT_TITLE = "Title Colour"
		self.MENU_OPT_TITLE_DESC = "Title Description Colour"
		self.MENU_OPT_ODD = "ODD Rows"
		self.MENU_OPT_EVEN = "EVEN Rows"
		self.MENU_OPT_FAV = "FAV Programme"
		self.MENU_OPT_FOCUS = "HIGHLIGHTED Programme"
		self.MENU_OPT_COLOUR_ARROWS = "Programme Arrows Colour"
		self.MENU_OPT_COLOUR_NOWTIME = "Current Time Line Colour"
		self.MENU_OPT_COLOUR_TIMERBAR = "Timerbar Colour"
		self.MENU_OPT_BLUE_THEME = "Blue Theme"
		self.MENU_OPT_LIGHTBLUE_THEME = "Light Blue Theme"
		self.MENU_OPT_BLUESTRIPE_THEME = "Blue (stripe) Theme"
		self.MENU_OPT_OLIVE_THEME = "Olive Theme"
		self.MENU_OPT_PMIII_THEME = "PMIII Theme"
		self.MENU_OPT_PMIII_STRIPE_THEME = "PMIII (Stripe) Theme"
		self.MENU_OPT_MC360_THEME = "MC360 Theme"
		self.MENU_OPT_RESET = "Skin Theme For: %s" % getSkinName()

		self.menu = [
			__language__(500),		# exit
			self.MENU_OPT_CHNAME,
			self.MENU_OPT_TITLE,
			self.MENU_OPT_TITLE_DESC,
			self.MENU_OPT_ODD,
			self.MENU_OPT_EVEN,
			self.MENU_OPT_FAV,
			self.MENU_OPT_FOCUS,
			self.MENU_OPT_COLOUR_ARROWS,
			self.MENU_OPT_COLOUR_NOWTIME,
			self.MENU_OPT_COLOUR_TIMERBAR,
			self.MENU_OPT_RESET,
			self.MENU_OPT_BLUE_THEME,
			self.MENU_OPT_LIGHTBLUE_THEME,
			self.MENU_OPT_BLUESTRIPE_THEME,
			self.MENU_OPT_OLIVE_THEME,
			self.MENU_OPT_PMIII_THEME,
			self.MENU_OPT_PMIII_STRIPE_THEME,
			self.MENU_OPT_MC360_THEME
			]

		self.WHITE = '0xFFFFFFFF'
		self.YELLOW = '0xFFFFFF00'
		self.YELLOW_LIGHT = '0xFFFFFFCC'
		self.BLACK = '0xFF000000'

		self.themeDefault = {
			config.KEY_DISPLAY_COLOUR_CHNAMES : self.WHITE,
			config.KEY_DISPLAY_COLOUR_TITLE : self.WHITE,
			config.KEY_DISPLAY_COLOUR_SHORT_DESC : self.WHITE,
			config.KEY_DISPLAY_NOFOCUS_ODD : "DarkBlue.png",
			config.KEY_DISPLAY_NOFOCUS_EVEN : "DarkBlue.png",
			config.KEY_DISPLAY_NOFOCUS_FAV : "DarkYellow.png",
			config.KEY_DISPLAY_FOCUS : "LightBlue.png",
			config.KEY_DISPLAY_COLOUR_TEXT_ODD : self.WHITE,
			config.KEY_DISPLAY_COLOUR_TEXT_EVEN : self.WHITE,
			config.KEY_DISPLAY_COLOUR_TEXT_FAV : self.YELLOW,
			config.KEY_DISPLAY_COLOUR_ARROWS : self.YELLOW_LIGHT,
			config.KEY_DISPLAY_COLOUR_NOWTIME : self.YELLOW_LIGHT,
			config.KEY_DISPLAY_COLOUR_TIMERBAR : '0xFF99FFFF'
			}

		# pre-defined colour scheme
		self.themeLightBlue = {
			config.KEY_DISPLAY_NOFOCUS_ODD : "Blue.png",
			config.KEY_DISPLAY_NOFOCUS_EVEN : "Blue.png"
			}

		self.themeBlueStripe = {
			config.KEY_DISPLAY_NOFOCUS_EVEN : "Blue.png"
			}

		self.themeOlive = {
			config.KEY_DISPLAY_NOFOCUS_ODD : "DarkGreen.png",
			config.KEY_DISPLAY_NOFOCUS_EVEN : "DarkGreen.png",
			config.KEY_DISPLAY_FOCUS : "LightGreen.png"
			}

		self.themePMIII = {
			config.KEY_DISPLAY_NOFOCUS_ODD : "DarkGrey.png",
			config.KEY_DISPLAY_NOFOCUS_EVEN : "DarkGrey.png",
			config.KEY_DISPLAY_NOFOCUS_FAV : "LightGrey.png",
			config.KEY_DISPLAY_FOCUS : "LightGrey.png"
			}

		self.themePMIIIStripe = {
			config.KEY_DISPLAY_NOFOCUS_ODD : "DarkGrey.png",
			config.KEY_DISPLAY_NOFOCUS_EVEN : "Grey.png",
			config.KEY_DISPLAY_FOCUS : "LightGrey.png"
			}

		self.themeMC360 = {
			config.KEY_DISPLAY_COLOUR_CHNAMES : self.BLACK,
			config.KEY_DISPLAY_COLOUR_TITLE : self.BLACK,
			config.KEY_DISPLAY_COLOUR_SHORT_DESC : self.BLACK
			}

		# set the default theme
		self.initDefault()
		debug("< ConfigEPGColours() init()")

	def initDefault(self):
		debug("initDefault()")
		self.scheme = self.themeDefault.copy()

	# RESET EPG COLOUR SCHEME TO DEFAULT
	def reset(self):
		debug("> reset()")
		self.initDefault()
		self.write()
		debug("< reset()")
		return self.scheme

	# load values from config
	def load(self):
		debug("> load()")
		for key in self.scheme.keys():
			value = config.getDisplay(key)
			if value:
				self.scheme[key] = value

		debug("< load()")
		return self.scheme

	# write values to config
	def write(self):
		debug("> write()")
		for key,value in self.scheme.items():
			config.setDisplay(key, os.path.basename(value))
		debug("< write()")

	def updateScheme(self, newScheme):
		debug("> updateScheme()")
		self.initDefault()
		# apply differences
		for key,value in newScheme.items():
			self.scheme[key] = value
		self.write()
		debug("< updateScheme()")

	def ask(self):
		debug("> ConfigEPGColours.ask()")
		reInit = False
		self.load()

		# show this dialog and wait until it's closed
		selectedPos = 0
		while True:
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(541), width=330, rows=len(self.menu), panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(self.menu, selectedPos)
			if selectedPos <= 0:
				break

			selectedOpt = self.menu[selectedPos]
			if selectedOpt == self.MENU_OPT_CHNAME:
				textColor = self.scheme[config.KEY_DISPLAY_COLOUR_CHNAMES]
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					self.scheme[config.KEY_DISPLAY_COLOUR_CHNAMES] = textColor
					self.write()
			elif selectedOpt == self.MENU_OPT_TITLE:
				textColor = self.scheme[config.KEY_DISPLAY_COLOUR_TITLE]
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					self.scheme[config.KEY_DISPLAY_COLOUR_TITLE] = textColor
					self.write()
			elif selectedOpt == self.MENU_OPT_TITLE_DESC:
				textColor = self.scheme[config.KEY_DISPLAY_COLOUR_SHORT_DESC]
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					self.scheme[config.KEY_DISPLAY_COLOUR_SHORT_DESC] = textColor
					self.write()
			elif selectedOpt == self.MENU_OPT_ODD:			# ODD line
				backgFile = self.scheme[config.KEY_DISPLAY_NOFOCUS_ODD]
				textColor = self.scheme[config.KEY_DISPLAY_COLOUR_TEXT_ODD]
				backgFile, textColor = ButtonColorPicker().ask(backgFile, textColor, selectedOpt)
				if backgFile and textColor:
					self.scheme[config.KEY_DISPLAY_NOFOCUS_ODD] = backgFile
					self.scheme[config.KEY_DISPLAY_COLOUR_TEXT_ODD] = textColor
					self.write()
			elif selectedOpt == self.MENU_OPT_EVEN:			# EVEN line
				backgFile = self.scheme[config.KEY_DISPLAY_NOFOCUS_EVEN]
				textColor = self.scheme[config.KEY_DISPLAY_COLOUR_TEXT_EVEN]
				backgFile, textColor = ButtonColorPicker().ask(backgFile, textColor, selectedOpt)
				if backgFile and textColor:
					self.scheme[config.KEY_DISPLAY_NOFOCUS_EVEN] = backgFile
					self.scheme[config.KEY_DISPLAY_COLOUR_TEXT_EVEN] = textColor
					self.write()
			elif selectedOpt == self.MENU_OPT_FAV:			# FAV SHOWS
				backgFile = self.scheme[config.KEY_DISPLAY_NOFOCUS_FAV]
				textColor = self.scheme[config.KEY_DISPLAY_COLOUR_TEXT_FAV]
				backgFile, textColor = ButtonColorPicker().ask(backgFile, textColor, selectedOpt)
				if backgFile and textColor:
					self.scheme[config.KEY_DISPLAY_NOFOCUS_FAV] = backgFile
					self.scheme[config.KEY_DISPLAY_COLOUR_TEXT_FAV] = textColor
					self.write()
			elif selectedOpt == self.MENU_OPT_FOCUS:		# FOCUS
				backgFile = self.scheme[config.KEY_DISPLAY_FOCUS]
				textColor = self.scheme[config.KEY_DISPLAY_COLOUR_TEXT_ODD]
				backgFile, textColor = ButtonColorPicker().ask(backgFile, textColor, selectedOpt)
				if backgFile and textColor:
					self.scheme[config.KEY_DISPLAY_FOCUS] = backgFile
					self.scheme[config.KEY_DISPLAY_COLOUR_TEXT_ODD] = textColor
					self.write()
			elif selectedOpt == self.MENU_OPT_COLOUR_ARROWS:
				textColor = self.scheme[config.KEY_DISPLAY_COLOUR_ARROWS]
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					self.scheme[config.KEY_DISPLAY_COLOUR_ARROWS] = textColor
					self.write()
			elif selectedOpt == self.MENU_OPT_COLOUR_NOWTIME:
				textColor = self.scheme[config.KEY_DISPLAY_COLOUR_NOWTIME]
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					self.scheme[config.KEY_DISPLAY_COLOUR_NOWTIME] = textColor
					self.write()
			elif selectedOpt == self.MENU_OPT_COLOUR_TIMERBAR:
				textColor = self.scheme[config.KEY_DISPLAY_COLOUR_TIMERBAR]
				backgFile, textColor = ButtonColorPicker().ask("", textColor, selectedOpt)
				if textColor:
					self.scheme[config.KEY_DISPLAY_COLOUR_TIMERBAR] = textColor
					self.write()
			else:
				debug("change to a theme")
				if selectedOpt == self.MENU_OPT_BLUE_THEME:					# Blue
					self.initDefault()
					self.write()
				elif selectedOpt == self.MENU_OPT_LIGHTBLUE_THEME:			# Light Blue
					self.updateScheme(self.themeLightBlue)
				elif selectedOpt == self.MENU_OPT_BLUESTRIPE_THEME:			# Blue (stripe)
					self.updateScheme(self.themeBlueStripe)
				elif selectedOpt == self.MENU_OPT_OLIVE_THEME:				# Olive
					self.updateScheme(self.themeOlive)
				elif selectedOpt == self.MENU_OPT_PMIII_THEME:				# PMIII
					self.updateScheme(self.themePMIII)
				elif selectedOpt == self.MENU_OPT_PMIII_STRIPE_THEME:		# PMIII (stripe)
					self.updateScheme(self.themePMIIIStripe)
				elif selectedOpt == self.MENU_OPT_MC360_THEME:				# MC360 (mostly blue)
					self.updateScheme(self.themeMC360)
				elif selectedOpt == self.MENU_OPT_RESET:					# reset to curr skin.dat
					config.setDisplay(config.KEY_DISPLAY_SKIN,"")
					config.initSectionDisplay()								# this also writes to file
				messageOK(__language__(541), __language__(215) % selectedOpt)

			reInit = True

		debug("< ConfigEPGColours.ask() reInit=%s" % reInit)
		return reInit


#######################################################################################################################    
# CONFIG GENRE ICONS
#######################################################################################################################    
class ConfigGenreIcons:
	def __init__(self):
		debug("ConfigGenreIcons() init()")

		self.genres = {}
		self.EXT = '.png'
		self.DISABLED_STR = '_disabled' + self.EXT
		self.ENABLED_STR = self.EXT

	# find all icon files , create a dict of {fname, fullpath + fname}
	def load(self):
		debug("> ConfigGenreIcons().load()")
		try:
			self.genres = {}
			fileList = listDir(DIR_GENRE, self.EXT, getFullFilename=True)
			for fname in fileList:
				name = fname.replace(self.DISABLED_STR, '').replace(self.ENABLED_STR,'').replace('_',' ')
				self.genres[name] = prefixDirPath(fname, DIR_GENRE)
		except:
			handleException("ConfigGenreIcons.load()")
		debug("< ConfigGenreIcons().load()")
		return self.genres

	# return a dict containing only enabled genres (those without _disabled on end of fname)
	def getEnabledGenres(self):
		debug("> ConfigGenreIcons().getEnabledGenres()")
		self.load()

		enabledGenres = {}
		for key,value in self.genres.items():
			if not value.endswith(self.DISABLED_STR):
				enabledGenres[key] = value

		debug("< ConfigGenreIcons().getEnabledGenres()")
		return enabledGenres

	def setState(self, key, state):
		changed = False
		try:
			src = self.genres[key]										# current state
			dest = src.replace(self.DISABLED_STR,self.ENABLED_STR)		# make enabled
			if not state:
				dest = dest.replace(self.ENABLED_STR,self.DISABLED_STR)	# make not enabled
			if src != dest:
				try:
					# os rename file
					self.genres[key] = dest
					os.rename(src, dest)
					changed = True
				except: pass
		except: pass
		return changed
	
	def ask(self):
		debug("> ConfigGenreIcons().ask()")
		reInit = False
		self.load()

		# make menu
		imageList = [None]
		menu = [(__language__(500), '')]	# exit
		keyList = self.genres.keys()
		keyList.sort()
		for key in keyList:
			fname = self.genres[key]
			yesno = config.configHelper.boolToYesNo(not fname.endswith(self.DISABLED_STR))
			menu.append([key, yesno])
			imageList.append(fname)

		useXOptions = [ __language__(350), __language__(351) ]			# YES , NO
		selectDialog = DialogSelect()
		selectDialog.setup(__language__(542), rows=len(menu), width=330, imageWidth=30, \
						   title2=__language__(617),useXOptions=useXOptions, panel=DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(menu, 0, imageList)

		# rename genre files if changed
		changed=False
		for key, value in menu:
			if value:
				if self.setState(key, config.configHelper.yesNoToBool(value)):
					changed = True 
		del selectDialog

		debug("< ConfigGenreIcons().ask() changed=%s" % changed)
		return changed

#################################################################################################################
# CONFIG GENRE BUTTON COLOURS
#################################################################################################################
class ConfigGenreColours:
	def __init__(self):
		debug("ConfigGenreColours() init()")

		self.SECTION_GENRE_COLOURS = "GENRE_COLORS"
		self.EXT = '.png'
		self.DISABLED_STR = '_disabled' + self.EXT
		self.genres = {}

	# RESET ALL OFF
	def reset(self):
		debug("> ConfigGenreColours().reset()")
		config.action(self.SECTION_GENRE_COLOURS, mode=ConfigHelper.MODE_REMOVE_SECTION)
		for genreName in self.genres.keys():
			self.genres[genreName] = None
		debug("< ConfigGenreColours().reset()")

	# load values from file
	def load(self):
		debug("> ConfigGenreColours().load()")
		try:
			# find all genres
			self.genres = {}
			fileList = listDir(DIR_GENRE, self.EXT, getFullFilename=True)
			for fname in fileList:
				genreName = os.path.basename(fname).replace(self.DISABLED_STR, '').replace(self.EXT, '').replace('_',' ')

				# get saved genre colour file, if exists in config
				colourName = config.action(self.SECTION_GENRE_COLOURS, genreName)
				if colourName:
					self.genres[genreName] = prefixDirPath(colourName, DIR_EPG)
				else:
					self.genres[genreName] = None
		except:
			handleException()
		debug("< ConfigGenreColours().load() loaded=%s" % len(self.genres))
		return self.genres

	# menu consists of icon image, genre name, filename
	def createMenu(self):
		debug("> ConfigGenreColours().createMenu()")
		menu = [ (__language__(500),""), ("All OFF", "") ]	# exit
		colourImgList = [None,None]

		genres = self.genres.items()
		genres.sort()
		for genreName, colourName in genres:
			if colourName:
				menu.append( (genreName, os.path.basename(colourName)) )
				colourImgFN = prefixDirPath(colourName, DIR_EPG)
			else:
				menu.append( (genreName, __language__(357)) )		# OFF
				colourImgFN = None
			colourImgList.append(colourImgFN)

		debug("< ConfigGenreColours().createMenu()")
		return menu, colourImgList

	def ask(self):
		debug("> ConfigGenreColours().ask()")
		reInit = INIT_NONE
		if not self.genres:
			self.load()

		# show this dialog and wait until it's closed
		selectedPos = 0
		while True:
			menu, colourImgList = self.createMenu()
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(543), rows=len(menu), width=450, imageWidth=30, panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menu, selectedPos, colourImgList)
			if selectedPos <= 0:			# exit
				break
			elif selectedPos == 1:			# ALL OFF
				self.reset()
				reInit = INIT_DISPLAY
			else:
				genreName = menu[selectedPos][0]
				backgFile = self.genres[genreName]
				if not backgFile:					# set a default backg colour
					backgFile = "DarkBlue.png"
				backgFile, textColor = ButtonColorPicker().ask(backgFile)
				if backgFile == None:				# DISABLED
					self.genres[genreName] = None
					config.action(self.SECTION_GENRE_COLOURS, genreName, mode=ConfigHelper.MODE_REMOVE_OPTION)
					reInit = INIT_DISPLAY
				elif backgFile:						# SELECTED
					self.genres[genreName] = backgFile
					config.action(self.SECTION_GENRE_COLOURS, genreName, os.path.basename(backgFile), \
								  mode=ConfigHelper.MODE_WRITE)
					reInit = INIT_DISPLAY

		debug("< ConfigGenreColours().ask() reInit=%s" % reInit)
		return reInit


#######################################################################################################################    
# CONFIG OVESCAN & FONTS
#######################################################################################################################    
class configFonts:
	def __init__(self):
		debug("> configFonts() init()")

		self.menu = [
			[__language__(500),None],
#			[__language__(593), config.KEY_DISPLAY_FONT_TITLE],
#			[__language__(594), config.KEY_DISPLAY_FONT_SHORT_DESC],
			[__language__(595), config.KEY_DISPLAY_FONT_CHNAMES],
			[__language__(596), config.KEY_DISPLAY_FONT_EPG]
			]

		self.TITLE = 0
		self.CONFIG_KEY = 1

		# init config file
		self.selectedPos = 0
		debug("< configFonts() init()")

	def enterFont(self, currentValue):
		debug("> enterFont()")
		value = currentValue
		menu = [__language__(500)]
		for font in ALL_FONTS:
			menu.append(font)
		try:
			currentIdx = menu.index(currentValue)
		except:
			currentIdx = 0
		selectDialog = DialogSelect()
		selectDialog.setup(__language__(572), rows=len(menu), width=360, panel=DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(menu, currentIdx)
		if selectedPos > 0:
			value = menu[selectedPos]
		debug("< enterFont() value=%s" % value)
		return value

	def createMenuList(self):
		debug("> createMenuList()")

		list = []
		for label, key in self.menu:
			if key:
				label2 = config.getDisplay(key)
				if not label2:
					label2 = "?"
			else:
				label2 = ''
			list.append(xbmcgui.ListItem(label, label2=label2))

		debug("< createMenuList() list sz: " + str(len(list)))
		return list

	def ask(self):
		debug("> ask()")
		# show this dialog and wait until it's closed

		changed = False
		selectedPos = 0
		while True:
			menuList = self.createMenuList()
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(544), rows=len(menuList), width=300, panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menuList, selectedPos)
			if selectedPos <= 0:
			 	break # exit selected

			else:												# FONTS
				selectedValue = menuList[selectedPos].getLabel2()
				key = self.menu[selectedPos][self.CONFIG_KEY]

				value = self.enterFont(selectedValue)
				if (value != selectedValue) and config.setDisplay(key, value):
					changed = True

		debug("< ask() changed=%s " % changed)
		return changed

#######################################################################################################################    
# CONFIG EPG ROW / GAP HEIGHTS
#######################################################################################################################    
class configEPGRows:
	def __init__(self):
		debug("> configEPGRows() init")

		# menu choices
		self.menu = [
			[__language__(500),None],
			[__language__(573), config.KEY_DISPLAY_EPG_ROW_HEIGHT],
			[__language__(574), config.KEY_DISPLAY_EPG_ROW_GAP_HEIGHT]
			]

		self.TITLE = 0
		self.CONFIG_KEY = 1
		debug("< configEPGRows() init")

	def selectValue(self, currentValue, minValue, maxValue, title):
		debug("> configEPGRows.selectValue() currentValue=%s minValue=%s maxValue=%s" % (currentValue,minValue,maxValue))
		menu = [None,] * ((maxValue - minValue) +1)
		menu[0] = __language__(500)	# exit
		i = 1
		for v in range(minValue, maxValue):
			menu[i] = str(v)
			i += 1
		# find current value
		try:
			currentIdx = menu.index(str(currentValue))
		except:
			currentIdx = 0
		selectDialog = DialogSelect()
		selectDialog.setup(title, rows=len(menu), width=250, panel=DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(menu, currentIdx)
		if selectedPos > 0:
			currentValue = menu[selectedPos]

		debug("< selectValue() currentValue=%s" % currentValue)
		return int(currentValue)

	def createMenuList(self):
		debug("> configEPGRows.createMenuList()")

		list = []
		for label, key in self.menu:
			if key:
				label2 = config.getDisplay(key)
				if not label2:
					label2 = "?"
			else:
				label2 = ''
			list.append(xbmcgui.ListItem(label, label2=label2))

		debug("< createMenuList()")
		return list

	def ask(self):
		debug("> configEPGRows.ask()")
		# show this dialog and wait until it's closed

		changed = False
		selectedPos = 0
		while True:
			menuList = self.createMenuList()
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(545), rows=len(menuList), width=270, panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menuList, selectedPos)
			if selectedPos <= 0:
				break # exit selected

			selectedItem, key = self.menu[selectedPos]
			selectedValue = menuList[selectedPos].getLabel2()

			if selectedPos == 1: # row height
				value = self.selectValue(selectedValue, 20, 61, selectedItem)
			else:				# row gap height
				value = self.selectValue(selectedValue, 1, 21, selectedItem)

			if (value != selectedValue) and config.setDisplay(key, value):
				changed = True

		debug("< ask() changed=%s " % changed)
		return changed


#################################################################################################################
# Manual recording - create a Programme /Channel object with required data
#################################################################################################################
class ManualTimer:
	def __init__(self):
		debug("> ManualTimer() init()")
		self.NOT_SET = '?'
		self.DISPLAY_DATE_FMT = '%A, %d %b %Y'
		self.FREQ_ONCE = 'Once'
		self.FREQ_DAILY = 'Daily'
		self.FREQ_WEEKLY = 'Weekly'
		self.FREQ_DUR_OPTS = [__language__(500),self.FREQ_ONCE, self.FREQ_DAILY, self.FREQ_WEEKLY]

		self.MENU_OPT_TITLE = 'Title:'
		self.MENU_OPT_DATE = 'Date:'
		self.MENU_OPT_START = 'Start Time (HHMM):'
		self.MENU_OPT_END = 'End Time (HHMM):'
		self.MENU_OPT_CHANNEL = 'Channel:'
		self.MENU_OPT_FREQ = 'Frequency:'
		self.MENU_OPT_FREQ_DUR = 'Frequency Count:'
		self.MENU_OPT_SAVE = 'Save Programme'
		self.menu = [
			__language__(500),
			self.MENU_OPT_TITLE,
			self.MENU_OPT_CHANNEL,
			self.MENU_OPT_DATE,
			self.MENU_OPT_START,
			self.MENU_OPT_END,
			self.MENU_OPT_FREQ,
			self.MENU_OPT_FREQ_DUR,
			self.MENU_OPT_SAVE
			]

		self.initData()

		debug("< ManualTimer() init()")

	# init default values
	def initData(self):
		self.data = {self.MENU_OPT_FREQ : self.FREQ_ONCE,
					 self.MENU_OPT_FREQ_DUR : '0'}

	def selectDate(self):
		debug("> ManualTimer().selectDate()")
		value = ''
		secs = time.time()

		MAX_DAYS = 14
		menuList = [None,] * MAX_DAYS	# pre-allocate list sz
		for i in range(MAX_DAYS):
			menuList[i] = time.strftime(self.DISPLAY_DATE_FMT, time.localtime(secs))
			secs += 86400
		menuList.insert(0, __language__(500))	# exit

		# menu
		selectDialog = DialogSelect()
		selectDialog.setup("SELECT RECORDING DATE:", rows=len(menuList), width=270, panel=DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(menuList)
		if selectedPos > 0:
			value = menuList[selectedPos]

		debug("< ManualTimer().selectDate() value = " + str(value))
		return value

	def selectChannel(self, currentChannel = ''):
		debug("> selectChannel()")
		value = ''

		chList = mytv.tvChannels.getChannelNames()	# [chID, name, other]
		sz = len(chList)
		menuList = [None, ] * sz
		for i in range(sz):
			menuList[i] = chList[i][1]		# name
		menuList.insert(0, __language__(500))	# exit

		try:
			selectIDX = menuList.index(currentChannel)
		except:
			selectIDX = 0

		# menu
		selectDialog = DialogSelect()
		selectDialog.setup(__language__(575), rows=len(menuList), width=270, panel=DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(menuList, selectIDX)
		if selectedPos > 0:
			value = chList[selectedPos]

		debug("< selectChannel() value = " + str(value))
		return value

	def selectTime(self, setStart=True):
		debug("> setTime().setDate() selectTime=" + str(setStart))
		value = ''

		if setStart:
			header = 'Enter START Time HHMM'
		else:
			header = 'Enter END Time HHMM'
		while not value:
			value = doKeyboard(value, header, KBTYPE_NUMERIC)	# numeric
			if not value:
				break

			if (len(value) != 4 or int(value[:2]) > 23 or int(value[2:]) > 59):
				messageOK("Invalid Time","Use 24hr time format HHMM")
				value = ''
		debug("< ManualTimer().selectTime()")
		return value

	def selectFreq(self):
		debug("> selectFreq()")
		value = ''

		# menu
		selectDialog = DialogSelect()
		selectDialog.setup(__language__(576), rows=len(self.FREQ_DUR_OPTS), width=250, panel=DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(self.FREQ_DUR_OPTS)
		if selectedPos > 0:
			value = self.FREQ_DUR_OPTS[selectedPos]

		debug("< selectFreq() value = " + str(value))
		return value

	def selectFreqDur(self):
		debug("> selectFreqDur()")
		value = ''

		while not value:
			value = doKeyboard(value, 'Enter Frequency (1 to 365):', KBTYPE_NUMERIC)
			if not value:
				break
			if (int(value) > 365 or int(value) < 1):
				messageOK("Invalid Frequency Count","Please enter number between 1 and 365")
				value = ''

		debug("< selectFreqDur() value = " + str(value))
		return value


	def createMenuList(self):
		debug("> ManualTimer().createMenuList()")
		list = []
		for menuTitle in self.menu:
			try:
				if menuTitle == self.MENU_OPT_CHANNEL:
					data = self.data[menuTitle]			# [id, name]
					value = data[1]
				else:
					value = self.data[menuTitle]
			except:
				value = ''
			list.append(xbmcgui.ListItem(menuTitle, label2=value))
		debug("< ManualTimer().createMenuList()")
		return list


	def ask(self):
		debug("> ManualTimer().ask()")
		# show this dialog and wait until it's closed

		saved = False
		selectedPos = -1
		while True:
			value = ''
			menuList = self.createMenuList()
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(509), width=620, rows=len(menuList), panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menuList, selectedPos)
			if selectedPos < 0:
				break # exit selected

			elif self.menu[selectedPos] == self.MENU_OPT_TITLE:
				try:
					title = self.data[self.MENU_OPT_TITLE]
				except:
					title = ''
				value = doKeyboard(title, __language__(592))
				if value:
					self.data[self.MENU_OPT_TITLE] = value.strip()
			elif self.menu[selectedPos] == self.MENU_OPT_DATE:
				value = self.selectDate()
				if value:
					self.data[self.MENU_OPT_DATE] = value
			elif self.menu[selectedPos] == self.MENU_OPT_START:
				value = self.selectTime()
				if value:
					self.data[self.MENU_OPT_START] = value
			elif self.menu[selectedPos] == self.MENU_OPT_END:
				value = self.selectTime(False)
				if value:
					self.data[self.MENU_OPT_END] = value
			elif self.menu[selectedPos] == self.MENU_OPT_CHANNEL:
				try:
					currentChannel = self.data[self.MENU_OPT_CHANNEL]
				except:
					currentChannel = ''
				value = self.selectChannel(currentChannel)
				if value:
					self.data[self.MENU_OPT_CHANNEL] = value
			elif self.menu[selectedPos] == self.MENU_OPT_FREQ:
				value = self.selectFreq()
				if value:
					self.data[self.MENU_OPT_FREQ] = value
			elif self.menu[selectedPos] == self.MENU_OPT_FREQ_DUR:
				value = self.selectFreqDur()
				if value:
					self.data[self.MENU_OPT_FREQ_DUR] = value
			elif self.menu[selectedPos] == self.MENU_OPT_SAVE:
				# required data
				save = False
				try:
					title = self.data[self.MENU_OPT_TITLE].strip()
					date = self.data[self.MENU_OPT_DATE]
					startTime = self.data[self.MENU_OPT_START]
					endTime = self.data[self.MENU_OPT_END]
					chData = self.data[self.MENU_OPT_CHANNEL]
					chID = chData[0]
					chName = chData[1]
					freq = self.data[self.MENU_OPT_FREQ]
					freqDur = int(self.data[self.MENU_OPT_FREQ_DUR])

					secsFormat = self.DISPLAY_DATE_FMT + ' %H%M'
					startTimeSecs = time.mktime(time.strptime(date+' '+startTime,secsFormat))
					endTimeSecs = time.mktime(time.strptime(date+' '+endTime,secsFormat))
					if startTimeSecs >= endTimeSecs:
						messageOK(__language__(509), __language__(107), __language__(132))	# start/end
					elif freq != self.FREQ_ONCE and freqDur <= 0:
						messageOK(__language__(509), __language__(107), __language__(133))	# freq
					elif freq != self.FREQ_ONCE:
						save = xbmcgui.Dialog().yesno(__language__(509),__language__(590), \
													  chName + ": " + title, \
													__language__(590) + str(freqDur))
					else:
						save = True
				except:
					messageOK(__language__(509), __language__(107))	# incomplete

				if save:
					if freq == self.FREQ_ONCE:
						secsOffset = 0
						freqDur = 1
					elif freq == self.FREQ_DAILY:
						secsOffset = 86400
					elif freq == self.FREQ_WEEKLY:
						secsOffset = 86400 * 7

					confirmRequired = (freq == self.FREQ_ONCE)

					# create programme for each repeat required
					success = False
					for count in range(freqDur):
						# make fake prog & channelInfo
						programme = { TVData.PROG_TITLE:title, TVData.PROG_STARTTIME:startTimeSecs, TVData.PROG_ENDTIME:endTimeSecs }
						channelInfo = [chID, chName, '']
						success = callSaveProgramme(programme, channelInfo, confirmRequired=confirmRequired)
						if success:
							saved = True	# any timers saved
						else:
							break
						startTimeSecs += secsOffset
						endTimeSecs += secsOffset

					# show finished for repeating progs, as they dont give confirmation
					if success:
						messageOK(__language__(509), __language__(301))		# success
						self.initData()	# reset
					else:
						messageOK(__language__(509), __language__(302))		# failed

		if saved:
			reInit = INIT_REDRAW
		else:
			reInit = INIT_NONE
		debug("< ManualTimer().ask() reInit: " + str(reInit))
		return reInit

#################################################################################################################
# List/Cancel XBMC AlarmClocks that exist
#################################################################################################################
def manageAlarms():
	debug("> manageAlarms()")
	deleted = False

	# load alarmclock file
	alarmClock = AlarmClock()
	if not alarmClock.loadAlarms():
		messageOK(__language__(517), __language__(127))
	else:
		while alarmClock.alarms:
			menu = alarmClock.alarms.values()
			menu.insert(0, __language__(500))
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(517) + ' ' + __language__(586), rows=len(menu), width=620, panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menu)
			if selectedPos <= 0:
				break
			
			elif xbmcgui.Dialog().yesno(__language__(517), __language__(305), menu[selectedPos], '', \
										__language__(355), __language__(356)):
				if alarmClock.cancelAlarm(selectedPos-1):	# allow for exit opt
					deleted = True

			del selectDialog
	debug("< manageAlarms() deleted=%s" % deleted)
	return deleted


#################################################################################################################
# Set an XBMC AlarmClock - uses prog starttime secs as alarm name
#################################################################################################################
def setAlarmClock():
	debug("> setAlarmClock()")
	prog = mytv.getCurrentProgramme()
	title = mytv.tvChannels.getProgAttr(prog, TVData.PROG_TITLE)
	startTime = int(mytv.tvChannels.getProgAttr(prog, TVData.PROG_STARTTIME))
	chName = mytv.tvChannels.getChannelName(mytv.allChannelIDX + mytv.epgChIDX)

	alarmClock = AlarmClock()
	success = alarmClock.saveAlarm(startTime, title, chName)
	debug("< setAlarmClock() success=%s" % success)
	return success

#################################################################################################################
def changeDataSource():
	debug("> changeDataSource()")

	changed = selectDataSource()
	if changed:
		global mytvFavShows
		mytvFavShows.deleteSaved()
		mytvFavShows = None
	
	debug("< changeDataSource()")
	return changed

#######################################################################################################################    
# CONFIG MENU
#######################################################################################################################    
class ConfigMenu:
	def __init__(self):
		debug("> ConfigMenu() init()")

		self.TITLE = 0
		self.FUNC = 1
		self.REINIT_REQUIRED = 2
		self.CONFIG_KEY = 3

		# init config file
		self.selectedPos = 0
		debug("< ConfigMenu() init()")

	def createMenuList(self):
		debug("> ConfigMenu().createMenuList()")

		# menu choices [title, func, reInit epg, config file setting name, config value]
		MENU_REC_CONFIG_DS = [__language__(532), configDataSource,INIT_FULL]
		MENU_REC_CONFIG_SP = [__language__(534), configSaveProgramme,INIT_FULL]
		MENU_REC_TIMER_CLASH = [__language__(538), configTimerClash, INIT_NONE, config.KEY_SYSTEM_TIMER_CLASH_CHECK]
		self.menu = [
			[__language__(500)],
			[__language__(530), clearCache, INIT_FULL],
			[__language__(531), changeDataSource,INIT_FULL_NOW, config.KEY_SYSTEM_DATASOURCE],
			MENU_REC_CONFIG_DS,
			[__language__(533), selectSaveProgramme,INIT_FULL_NOW, config.KEY_SYSTEM_SAVE_PROG],
			MENU_REC_CONFIG_SP,
			MENU_REC_TIMER_CLASH,
			[__language__(536), configClock, INIT_DISPLAY, config.KEY_SYSTEM_CLOCK],
			[__language__(539), configChannelName, INIT_DISPLAY, config.KEY_SYSTEM_SHOW_CH_ID],
			[__language__(540), configReorderChannels, INIT_FULL],
			[__language__(541), ConfigEPGColours().ask, INIT_DISPLAY],
			[__language__(544), configFonts().ask, INIT_DISPLAY],
			[__language__(542), ConfigGenreIcons().ask, INIT_PART],
			[__language__(543), ConfigGenreColours().ask, INIT_PART],
			[__language__(545), configEPGRows().ask, INIT_DISPLAY],
			[__language__(546), configSMB, INIT_NONE],
			[__language__(547), configEditTemplate, INIT_NONE, config.KEY_SYSTEM_SAVE_TEMPLATE],
			[__language__(548), ProgrammeSaveTemplate().viewTemplates,INIT_NONE],
			[__language__(549), configLSOTV, INIT_NONE, config.KEY_SYSTEM_USE_LSOTV],
			[__language__(555), configWOL, INIT_NONE, config.KEY_SYSTEM_WOL],
			[__language__(556), downloadLogos, INIT_DISPLAY],
			[__language__(553), configScriptUpdateCheck, INIT_NONE, config.KEY_SYSTEM_CHECK_UPDATE],
			[__language__(554), updateScript, INIT_NONE],
			[__language__(550), viewReadme, INIT_NONE],
			[__language__(551), viewChangelog, INIT_NONE],
			[__language__(552), config.reset, INIT_FULL]
			]

		# remove unwanted options
		# option config DS only if needed
		if not canDataSourceConfig():
			self.menu.remove(MENU_REC_CONFIG_DS)

		# tv card SAVEPROG related options
		if not config.getSystem(config.KEY_SYSTEM_SAVE_PROG):
			self.menu.remove(MENU_REC_CONFIG_SP)
			self.menu.remove(MENU_REC_TIMER_CLASH)

		list = []
		for menuItem in self.menu:
			label2=''
			label = menuItem[self.TITLE]
			# read in config setting if this menu item is a config setting
			try:
				key = menuItem[self.CONFIG_KEY]
				value = config.getSystem(key)
				if key == config.KEY_SYSTEM_SAVE_PROG:
					if not value:
						label2 = config.VALUE_SAVE_PROG_NOTV
				elif key == config.KEY_SYSTEM_SHOW_CH_ID:
					if value == '0':
						label2 = __language__(577)		# no ch name or id
					elif value == '2':
						label2 = __language__(561)		# show ch id
					elif value == '3':
						label2 = __language__(562)		# show alt ch id
					else:
						label2 = __language__(560)		# ch name only
				else:
					label2 = ''

				if not label2:
					label2 = config.configHelper.boolToYesNo(value)
			except:
				label2 = ''
			list.append(xbmcgui.ListItem(label, label2=label2))

		
		debug("< ConfigMenu().createMenuList() list sz: " + str(len(list)))
		return list

	def ask(self):
		debug("> ConfigMenu().ask()")
		# show this dialog and wait until it's closed

		reInit = INIT_NONE
		selectedPos = 0
		while True:
			menuList = self.createMenuList()
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(502), width=550, rows=len(menuList), banner=LOGO_FILENAME, panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menuList, selectedPos)
			if selectedPos <= 0:
				break # exit selected

			# exec func associated with menu option (if has one)
			if self.menu[selectedPos][self.FUNC]:
				done = self.menu[selectedPos][self.FUNC]()

				# force exit if updating script
				if done and self.menu[selectedPos][0] == __language__(554):         # update script
					# restart script after update
					deleteCacheFiles(0)
					xbmc.executebuiltin('XBMC.RunScript(%s)'%(os.path.join(DIR_HOME, 'default.py')))
					sys.exit(0)	                                                    # end current instance
			else:
				done = True

			# set reInit status if still false.
			# this allows setting to persist
			if done:
				optInitLevel = self.menu[selectedPos][self.REINIT_REQUIRED]
				debug("func complete, optInitLevel=" + str(optInitLevel))
				if optInitLevel > reInit:
					reInit = optInitLevel	# save highest reinit level

				# exit back to epg for reInint now for some options
				if optInitLevel == INIT_FULL_NOW:
					debug("options requires exit menu to epg now")
					break

		debug("< ConfigMenu().ask() reInit=%s" % reInit)
		return reInit


#######################################################################################################################    
# MAIN MENU
#######################################################################################################################    
class MainMenu:
	def __init__(self):
		debug("> MainMenu() init()")

		# menu choices
		if not mytv.justHDChannels:
			self.OPT_CH_VIEW = __language__(504)
		else:
			self.OPT_CH_VIEW = __language__(505)
		self.OPT_PLAY_SMB = __language__(506)
		self.OPT_ADD_FAV = __language__(507)
		self.OPT_VIEW_FAV = __language__(508)
		self.OPT_MANUAL_TIMER = __language__(509)
		self.OPT_MANAGE_FAV = __language__(510)
		self.OPT_VIEW_TIMERS = __language__(511)
		self.OPT_STREAMURL = __language__(512)
		self.OPT_VIEW_TVCOM = __language__(513)
		self.OPT_IMDB_MANUAL = __language__(515)
		self.OPT_ALARMCLOCK = __language__(516)
		self.OPT_MANAGE_ALARMCLOCK = __language__(517)
		self.OPT_TVRAGE = __language__(518)
		self.OPT_LIVESPORT = __language__(519)
		self.OPT_CONFIG_MENU = __language__(502)
		self.OPT_CANCEL_FAV = __language__(520)
		self.OPT_SAVEPROG_PLAYBACK = __language__(503)

		self.alarmClock = AlarmClock()
		self.alarmClock.loadAlarms()
		self.countryCode = upper(config.getSystem(config.KEY_SYSTEM_DATASOURCE)[:2])

		debug("< MainMenu() init()")

	def setupMenuOptions(self):
		debug("> setupMenuOptions()")

		self.menu = [
			__language__(500),	# exit
			self.OPT_IMDB_MANUAL,
			self.OPT_ADD_FAV,
			self.OPT_CANCEL_FAV,
			self.OPT_VIEW_FAV,
			self.OPT_MANAGE_FAV,
			self.OPT_CH_VIEW,
#			self.OPT_VIEW_TVCOM,
			self.OPT_TVRAGE,
			self.OPT_LIVESPORT,
			self.OPT_MANUAL_TIMER,
			self.OPT_VIEW_TIMERS,
			self.OPT_ALARMCLOCK,
			self.OPT_MANAGE_ALARMCLOCK,
			self.OPT_SAVEPROG_PLAYBACK,
			self.OPT_PLAY_SMB,
			self.OPT_STREAMURL,
			self.OPT_CONFIG_MENU
			]

		if not saveProgramme or not hasattr(saveProgramme, "playbackFromFile"):
			self.menu.remove(self.OPT_SAVEPROG_PLAYBACK)

		# check if a non programme
		isValidProg = validProgramme(self.title)
		if not isValidProg:
			self.menu.remove(self.OPT_ADD_FAV)
			self.menu.remove(self.OPT_CANCEL_FAV)
			self.menu.remove(self.OPT_TVRAGE)
			self.menu.remove(self.OPT_ALARMCLOCK)

		# not using tv card, remove timer options
		if not config.getSystem(config.KEY_SYSTEM_SAVE_PROG):
			self.menu.remove(self.OPT_VIEW_TIMERS)
			self.menu.remove(self.OPT_MANUAL_TIMER)

		# remove ADD FAV if already a FAV, swap with CANCEL FAV
		if isValidProg:
			if not mytv.isFavShow(self.title):
				try:
					self.menu.remove(self.OPT_CANCEL_FAV)
				except: pass # may have already been removed
			else:
				try:
					self.menu.remove(self.OPT_ADD_FAV)
				except: pass # may have already been removed

		# remove OPT_LIVESPORT if not UK or not config enabled
		useLiveSportOnTv = (config.getSystem(config.KEY_SYSTEM_USE_LSOTV) or self.countryCode == 'UK')
		if not useLiveSportOnTv:
			self.menu.remove(self.OPT_LIVESPORT)

		# remove view/manage fav shows if non saved
		if not mytvFavShows or not mytvFavShows.getTitles():
			self.menu.remove(self.OPT_MANAGE_FAV)
			self.menu.remove(self.OPT_VIEW_FAV)

		# remove HD/Normal option if no HD Channels if non avail.
		if not mytv.areHDChannels:
			self.menu.remove(self.OPT_CH_VIEW)

		# alarm clock
		if not self.alarmClock.alarms:
			self.menu.remove(self.OPT_MANAGE_ALARMCLOCK)

		# remove manage timers if non exist
		if not mytv.timersDict:
			try:
				self.menu.remove(self.OPT_VIEW_TIMERS)
			except: pass # may have already been removed
		debug("< setupMenuOptions()")


	# show this dialog and wait until it's closed
	def ask(self):
		debug("> MainMenu().ask()")

		chID, chName, chIDAlt = mytv.tvChannels.getChannelInfo(mytv.allChannelIDX+mytv.epgChIDX)
		self.title = mytv.getCurrentProgrammeTitle()

		reInit = INIT_NONE
		selectedPos = 0
		exit = False
		while not exit:
			optReInit = INIT_NONE
			self.setupMenuOptions()
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(501), rows=len(self.menu), width=330, banner=LOGO_FILENAME, panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(self.menu, selectedPos)
			if selectedPos <= 0:				# exit selected
				break

			elif self.menu[selectedPos] == self.OPT_SAVEPROG_PLAYBACK:			# playback via
				saveProgramme.playbackFromFile()
			
			elif self.menu[selectedPos] == self.OPT_ADD_FAV:			# Add to fav
				if mytvFavShows.addToFavShows(self.title, chID, chName):
					optReInit = INIT_FAV_SHOWS
					exit = True
			elif self.menu[selectedPos] == self.OPT_CANCEL_FAV:			# Cancel fav
				if mytvFavShows.deleteShow(self.title, chID):
					optReInit = INIT_FAV_SHOWS
					exit = True
			elif self.menu[selectedPos] == self.OPT_MANAGE_FAV:			# delete/list fav shows
				if mytvFavShows.manageFavShows():
					optReInit = INIT_FAV_SHOWS
			elif self.menu[selectedPos] == self.OPT_VIEW_FAV:			# display 7-day fav show list
				mytvFavShows.ask()
#			elif self.menu[selectedPos] == self.OPT_VIEW_TVCOM:			# TV.com
#				callTVCom()
			elif self.menu[selectedPos] == self.OPT_VIEW_TIMERS:		# view timers
				if callManageSaveProgramme():							# call custom or gui SaveProgramme manager
					optReInit = INIT_REDRAW
			elif self.menu[selectedPos] == self.OPT_STREAMURL:			# list/select/stream url 
				playStreamPack()
			elif self.menu[selectedPos] == self.OPT_PLAY_SMB:			# list/select/play smb videp file
				if smbMenuFiles():
					break # quit menu now
			elif self.menu[selectedPos] == self.OPT_CONFIG_MENU:		# config menu
				optReInit = ConfigMenu().ask()
				if optReInit != INIT_NONE:
					self.setupMenuOptions()								# may need to remove menu options
			elif self.menu[selectedPos] == self.OPT_MANUAL_TIMER:
				if ManualTimer().ask():
					optReInit = INIT_TIMERS
					exit = True
			elif self.menu[selectedPos] == self.OPT_CH_VIEW:
				mytv.justHDChannels = not mytv.justHDChannels
				optReInit = INIT_FULL
				exit = True
			elif self.menu[selectedPos] == self.OPT_IMDB_MANUAL:
				callIMDB()
			elif self.menu[selectedPos] == self.OPT_ALARMCLOCK:
				if setAlarmClock():
					exit = True
			elif self.menu[selectedPos] == self.OPT_MANAGE_ALARMCLOCK:
				manageAlarms()
			elif self.menu[selectedPos] == self.OPT_TVRAGE:
				tvrage = TVRage()
				tvrage.ask(self.title, self.countryCode)
				del tvrage
			elif self.menu[selectedPos] == self.OPT_LIVESPORT:
				lsontv = LiveSportOnTV().ask()
			else:
				debug("unknown option %s" % self.menu[selectedPos])

			debug("optReInit=%s" % optReInit)
			if optReInit > reInit:
				reInit = optReInit	# save highest reinit level

			del selectDialog

			# quit menu if some option requested
			if optReInit == INIT_FULL_NOW:
				exit = True

#		del favShows
		debug("< MainMenu().ask() reInit: %s" % reInit)
		return reInit


#################################################################################################################
def configReorderChannels():
	debug("> configReorderChannels()")

	def isHiddenText(text):
		if text[0] == '*':					# * indicates HIDDEN
			text = __language__(350)		# YES
			isHidden = True
		else:
			text = __language__(351)		# NO
			isHidden = False
		return text, isHidden

	def setHidden(text, isHidden):
		if isHidden and text[0] != '*':						# make hidden
			return '*' + text
		elif not isHidden and text[0] == '*':				# unhide
			return text[1:]
		return text

	def makeMenu():
		debug("> ReorderChannels.makeMenu()")
		# add channel name to list from [chid, ch name, alt ch id]
		menu = [ [__language__(500), ''] ]
		for channel in channels:
			label2,isHidden = isHiddenText(channel[1])
			if isHidden:
				label = channel[1][1:]			# removes the * at beginnning
			else:
				label = channel[1]
			menu.append( [label, label2] )
		debug("< ReorderChannels.makeMenu()")
		return menu

	# load channel names
	channelsFilename = getChannelListFilename()
	channels = readChannelsList(channelsFilename, loadHidden=True)	# chid, chname, alt.chid

	# loop until finished then break
	useXOptions = [ __language__(350), __language__(351) ]			# YES , NO
	newChannels = []
	menu = makeMenu()
	allowReorder = (len(menu) > 2)

	selectDialog = DialogSelect()
	selectDialog.setup(__language__(597), width=450, rows=len(menu), useXOptions=useXOptions, \
					   reorder=allowReorder,title2=__language__(609),movingTitle=__language__(598))
	selectedPos,action = selectDialog.ask(menu)

	if selectedPos <= 0:
		for menuIdx in range(len(menu)):
			label,label2 = menu[menuIdx]
			if label == __language__(500):		# ignore exit
				continue

			for channel in channels:
				# compare menu's chName against channel chName, whcih may/not have * prefix
				if label == channel[1] or label == channel[1][1:]:
					isHidden = (label2 == __language__(350))
					channel[1] = setHidden(channel[1], isHidden)
					newChannels.append(channel)
					break

	del selectDialog

	writeChannelsList(channelsFilename, newChannels)
	changed = True

	debug("< configReorderChannels changed=%s" % changed)
	return changed


###################################################################################################################
class LiveSportOnTV:
	def __init__(self):
		debug("> LiveSportOnTV() init()")

		self.URL_BASE = 'http://www.livesportontv.com/'
		self.URL_FULLLISTING = self.URL_BASE + 'search3.php?id='
		self.URL_RSS = self.URL_BASE + 'rss.php?p=/search3.php&id='
		self.ICON_FN = os.path.join(DIR_GFX, "lsotv_$ID.gif")

		self.MAIN_MENU_DATA = {
			'All Sports' : 'index.php?show=all', 
			'HDTV' : 'hdfull.php',
			'Olympics' : 'olympics.php',
			'Football' : 1,
			'Darts' : 2,
			'Snooker' : 3,
			'Cricket' : 4,
			'Motor Sports' : 5,
			'Golf' : 6,
			'Rugby Union' : 7,
			'Rugby League' : 8,
			'Tennis' : 9,
			'Basketball' : 10,
			'American Football' : 11,
			'Boxing' : 12,
			'Baseball' : 13,
			'Hockey' : 14,
			'Winter Sports' : 20,
			'Athletics' : 21,
			'Cycling' : 22,
			'Martial Arts' : 23,
			'Bowls' : 27,
			'Wrestling' : 28,
			'Gymnastics' : 29,
			'Water Sports' : 30,
			'Vollyball' : 32,
			'Pool' : 33
			}
		debug("< LiveSportOnTV() init()")

	###################################################################################################################
	def onAction(self, action):
		try:
			actionID = action.getId()
			if not actionID:
				actionID = action.getButtonCode()
		except: return
		if actionID in CANCEL_DIALOG + EXIT_SCRIPT:
			self.close()

	###################################################################################################################
	def onControl(self, control):
		pass

	###################################################################################################################
	def getSportDataRSS(self, html, ID):
		debug("> LiveSportOnTV.getSportDataRSS() ID=%s" % ID)

		menu = []
		menuIcons = []

		# split into rss items
		items = html.split("</item>")
		for item in items:
			matches = findAllRegEx(item, "<title>(.*?)</title")
			for match in matches:
				title = cleanHTML(decodeEntities(match))
				if title:
					menu.append(xbmcgui.ListItem(title))
					iconFN = self.ICON_FN.replace('$ID', str(ID))
					menuIcons.append(iconFN)

		debug("< LiveSportOnTV.getSportDataRSS()")
		return menu, menuIcons

	###################################################################################################################
	def getSportData(self, html, ID):
		debug("> LiveSportOnTV.getSportData() ID=%s" % ID)

		menu = []
		menuIcons = []

#		regex = '(?:tm\d*|dt)">(.*?)<.*?fx\d*">(.*?)<.*?tt\d*">(.*?)<.*?ch\d*">(.*?)</td' # w/o icon
		regex = '_images/(\d+).*?(?:tm\d*|dt)">(.*?)<.*?fx\d*">(.*?)<.*?tt\d*">(.*?)<.*?ch\d*">(.*?)</td' # w/icon
		matches = parseDocList(html, regex, 'class="theader"','id="footer"' )
		for match in matches:
			iconID = match[0]
			if iconID:
				iconFN = self.ICON_FN.replace('$ID', str(iconID))
			else:
				iconFN = self.ICON_FN.replace('$ID', str(ID))
			date = cleanHTML(decodeEntities(match[1]))
			fixture = cleanHTML(decodeEntities(match[2]))
			tourn = cleanHTML(decodeEntities(match[3]))
			channel = cleanHTML(decodeEntities(match[4]))
			channel = re.sub(r'(document.write.*?;)', ' ', channel)
			label = "%s, %s, %s" % (date,fixture,tourn)
			menu.append(xbmcgui.ListItem(label, channel))
			menuIcons.append(iconFN)

		debug("< LiveSportOnTV.getSportData()")
		return menu, menuIcons

	###################################################################################################################
	# ID is either a number (eg 1 = football) or partURL (eg hdindex.php)
	# get specific sport from the RSS version of web page (quicker)
	# or uses the web page, from which it can also get sport image icon.
	###################################################################################################################
	def displaySport(self, title, ID):
		debug("> LiveSportOnTV.displaySport ID=%s" % ID)

		# ID string is a url otherwise a number
		if isinstance(ID, int):
			urlList = [self.URL_FULLLISTING + str(ID), self.URL_RSS + str(ID)]
		else:
			urlList = [self.URL_BASE + ID]		# eg BASE + hdfull.php

		listTitle = __language__(519)
		menu = []
		menuIcons = []
		for url in urlList:
			dialogProgress.create(__language__(519), __language__(300), title)
			html = fetchURL(url)
			dialogProgress.close()
			if html:
				if find(url, 'rss') != -1:
					menu, menuIcons = self.getSportDataRSS(html, ID)
				else:
					menu, menuIcons = self.getSportData(html, ID)
				if menu:
					break

		menu.insert(0, xbmcgui.ListItem(__language__(500), ''))	# exit
		menuIcons.insert(0,'')									# exit icon
		selectDialog = DialogSelect()
		selectDialog.setup(listTitle, imageWidth=25,width=720, rows=len(menu), itemHeight=24, font=FONT10, panel=DIALOG_PANEL)
		selectedPos,action = selectDialog.ask(menu, icons=menuIcons)
		debug("< LiveSportOnTV.displaySport")

	###################################################################################################################
	def ask(self):
		debug("> LiveSportOnTV.ask()")

		# make menu
		menu = self.MAIN_MENU_DATA.keys()
		menu.sort()
		menuIcons = []
		for title in menu:
			if title[:3] == 'All':
				ID = 'all'
			else:
				ID = str(self.MAIN_MENU_DATA[title])
			iconFN = self.ICON_FN.replace('$ID', ID)
			menuIcons.append(iconFN)

		menu.insert(0, __language__(500))	# exit
		menuIcons.insert(0, '')				# exit has no icon
		selectedPos = 0
		while menu:
			selectDialog = DialogSelect()
			selectDialog.setup(imageWidth=25, width=300, rows=len(menu), itemHeight=25,
							   banner=os.path.join(DIR_GFX, 'livesportontv_logo.gif'), panel=DIALOG_PANEL)
			selectedPos,action = selectDialog.ask(menu, selectedPos,icons=menuIcons)
			if selectedPos <= 0:				# exit selected
				break

			title = menu[selectedPos]
			id = self.MAIN_MENU_DATA[title]
			self.displaySport(title, id)

		debug("< LiveSportOnTV.ask()")


############################################################################################################################
# send WOL if MAC in settings
# checkAwake - if have SMB path, checks HOST & port 139
############################################################################################################################
def sendWOL(checkAwake=True):
	debug("> sendWOL() checkAwake=%s" % checkAwake)
	isAwake = True
	mac = config.getSystem(config.KEY_SYSTEM_WOL)
	if mac:
		WakeOnLan(mac)

		# if reqd, loop to check host is awake
		if checkAwake:
			isAwake = False
			# some saveprogrammes store detail in own config section
			if hasattr(saveProgramme, "getSMB"):
				smbPath = saveProgramme.getSMB()
			else:
				smbPath = config.getSMB(config.KEY_SMB_PATH)
			if not smbPath:
				messageOK(__language__(607),__language__(136))
			else:
				quit = False
				RETRIES = 25
				macMsg = "MAC: %s" % mac
				while not isAwake and not quit:
					for count in range(RETRIES):
						isAwake = CheckHost(smbPath, 139)		# using a SMB port
						if isAwake:
							break
						elif count == 0:
							dialogProgress.create(__language__(607), macMsg, __language__(300))
						else:
							dialogProgress.update(int( float( count * 100) / RETRIES ))

						if ( dialogProgress.iscanceled() ):
							quit = True
						else:
							time.sleep(3)

					try:
						dialogProgress.close()
					except: pass
					if not quit and not isAwake:
						if not xbmcgui.Dialog().yesno(__language__(607), __language__(135)):	# retry ?
							break

	debug("< sendWOL() isAwake=%s" % isAwake)
	return isAwake

######################################################################################
def updateScript(silent=False):
	xbmc.output( "> updateScript() silent=%s" % silent)

	updated = False
	up = update.Update(__language__, __scriptname__)
	version = up.getLatestVersion(silent)
	xbmc.output("Current Version: " + __version__ + " Tag Version: " + version)
	if version != "-1":
		if __version__ < version:
			if xbmcgui.Dialog().yesno( __language__(0), \
								"%s %s %s." % ( __language__(1006), version, __language__(1002) ), \
								__language__(1003 )):
				updated = True
				up.makeBackup()
				up.issueUpdate(version)
		elif not silent:
			dialogOK(__language__(0), __language__(1000))
#	elif not silent:
#		dialogOK(__language__(0), __language__(1030))				# no tagged ver found

	del up
	xbmc.output( "< updateScript() updated=%s" % updated)
	return updated

#################################################################################################################
def validProgramme(title):
    return (title and title not in (__language__(204), __language__(203)))

#################################################################################################################
class TextBoxDialogXML( xbmcgui.WindowXML ):
	""" Create a skinned textbox window """
	def __init__( self, *args, **kwargs):
		pass
		
	def onInit( self ):
		xbmc.output( "TextBoxDialogXML.onInit()" )
		self.getControl( 3 ).setLabel( self.title )
		self.getControl( 5 ).setText( self.text )

	def onClick( self, controlId ):
		pass

	def onFocus( self, controlId ):
		pass

	def onAction( self, action ):
		try:
			actionID = action.getId()
			if not actionID:
				actionID = action.getButtonCode()
		except: return

		if actionID in CANCEL_DIALOG + EXIT_SCRIPT:
			self.close()

	def ask(self, title, text ):
		xbmc.output("TextBoxDialogXML().ask()")
		self.title = title
		self.text = text
		self.doModal()		# causes window to be drawn


#################################################################################################################
def downloadLogos():
	debug("> downloadLogos()")
	BASE_URL = "http://www.lyngsat-logo.com/tvcountry/"
	COUNTRIES_URL = BASE_URL + "tvcountry.html"
	COUNTRIES_FILE = os.path.join(DIR_CACHE, "tvcountry.html")
	COUNTRY_URL = BASE_URL + "$CCODE.html"

	dialogTitle = __language__(556)
	if not fileExist(COUNTRIES_FILE):
		dialogProgress.create(dialogTitle,__language__(610))		# fetch country codes
		doc = fetchURL(COUNTRIES_URL, COUNTRIES_FILE)
		dialogProgress.close()
	else:
		doc = readFile(COUNTRIES_FILE)

	if not doc:
		messageOK(dialogTitle, "Missing countries webpage", COUNTRIES_FILE)
		deleteFile(COUNTRIES_FILE)
		debug("< downloadLogos() no country page")
		return

	# get datasource inuse country code
	dsName = config.getSystem(MYTVConfig.KEY_SYSTEM_DATASOURCE)[:2]			# eg uk_RadioTimes -> uk

	# extract country code
	menu = [xbmcgui.ListItem(__language__(500),'')]
	matches = parseDocList(doc, 'icon/flags/.*?gif.*?tvcountry/(.*?).html">(.*?)</a')
	selectedPos = 0
	for i, match in enumerate(matches):
		ccode = match[0]
		if ccode == dsName:
			selectedPos = i+1		# allow for exit
		menu.append(xbmcgui.ListItem(cleanHTML(match[1]),match[0].upper()))

	selectDialog = DialogSelect()
	selectDialog.setup(__language__(611), rows=len(menu), width=300, panel=DIALOG_PANEL)
	selectedPos, action = selectDialog.ask(menu,selectedPos)
	if selectedPos <= 0:
		debug("< downloadLogos() no country picked")
		return

	# get country page
	ccode = matches[selectedPos-1][0]
	cname = matches[selectedPos-1][1]
	country_url = COUNTRY_URL.replace('$CCODE', ccode)
	country_fn = os.path.join(DIR_CACHE, os.path.basename(country_url))
	dialogTitle = "%s: %s" % (__language__(556), ccode.upper())
	if fileExist(country_fn):
		doc = readFile(country_fn)
	else:
		dialogProgress.create(dialogTitle, __language__(612))	# fetch filenames
		doc = fetchURL(country_url, country_fn)
		dialogProgress.close()

	if not doc:
		messageOK(dialogTitle, "Failed to fetch logo page", country_url)
		deleteFile(country_fn)
		debug("< downloadLogos()")
		return

	# extract logo filename & name
	logonames = []
	matches = parseDocList(doc, 'img src="(../icon/tv/.*?.gif)".*?html">(.*?)<')
	for match in matches:
		logonames.append(match[1])		# name

	if not logonames:
		messageOK(dialogTitle, "No logos found on webpage")
		deleteFile(country_fn)
		debug("< downloadLogos()")
		return

	debug("for each missing logo - try to match by channel ID or name...")
	missing = []
	dialogProgress.create(dialogTitle, __language__(613) )		# missing logos
	channelNames = mytv.tvChannels.getChannelNames()
	maxFetch = len(channelNames)
	for i, chData in enumerate(channelNames):
		chID = logoSafeName(chData[0])
		chName = logoSafeName(chData[1])
		chIDFn = xbmc.makeLegalFilename(os.path.join(DIR_LOGOS, chID+'.gif'))
		chNameFn = xbmc.makeLegalFilename(os.path.join(DIR_LOGOS, chName+'.gif'))
		
		if not fileExist(chIDFn) and not fileExist(chNameFn):
			missing.append(i)                                   # save the idx into channelNames
	dialogProgress.close()

	if not missing:
		messageOK(dialogTitle,"No missing logos.")
		debug("< downloadLogos()")
		return

	# make menu of available logo filenames
	menu = [__language__(500), __language__(614)]
	for logoURL, logoName in matches:
		menu.append(logoName)

	# ask to pick missing logos
	for i in missing:
		chData = channelNames[i]
		chName = chData[1]

		# attempt to goto nearest logo name
		chNameSZ = len(chName)
		if chNameSZ < 14:
			startPos = chNameSZ
		else:
			startPos = 14
		selectedPos = -1
		for chName_w in range(startPos, 0, -1):
			partChName = chName[:chName_w]
			for i, logoname in enumerate(logonames):
				if logoname.startswith(partChName):
					selectedPos = i+2		# allow for exit, skip options
					break
			if selectedPos != -1:
				break

		# dialog to pick logo
		selectDialog = DialogSelect()
		selectDialog.setup(__language__(615) + chName, rows=len(menu), width=320, panel=DIALOG_PANEL, useY=True)
		selectedPos, action = selectDialog.ask(menu, selectedPos)
		if selectedPos <= 0:		# exit
			break
		elif selectedPos == 1 or action in CLICK_X + CLICK_Y:		# skip
			continue
		else:
			url = BASE_URL + matches[selectedPos-2][0]						# url from previous country logo regex
			fn = os.path.join(DIR_LOGOS, logoSafeName(chName)+'.gif')		# save logo using ch name
			fn = xbmc.makeLegalFilename(fn)
			dialogProgress.create(dialogTitle, matches[selectedPos-2][1], os.path.basename(fn))
			fetchURL(url, fn, isBinary=True)
			dialogProgress.close()

	# cause mytv to reload logo filenames
	mytv.tvChannels.loadLogoFilenames()
	deleteFile(country_fn)
	debug("< downloadLogos()")

def messageXBMCOld():
	messageOK("WindowXML path error","XBMC Build probably too old.", "Upgrade to a post 'Atlantis' (2008-08-12)")
	
######################################################################################    
# BEGIN !
######################################################################################

# check for script update
updated = False
if config.getSystem(config.KEY_SYSTEM_CHECK_UPDATE):
    updated = updateScript(True)

if not updated:
	try:
		# start script main
		mytv = myTV("script-mytv-main.xml", DIR_HOME, "Default")
		if mytv.ready:
			mytv.doModal()
		del mytv
	except TypeError:
		messageXBMCOld()
	except:
		handleException()

debug("exiting script ...")
moduleList = ['mytvLib', 'bbbLib', 'bbbGUILib','smbLib', 'IMDbWin', 'IMDbLib','AlarmClock','FavShows','saveProgramme','datasource','tv.com','mytvFavShows','wol']
if not updated:
    moduleList += ['update', 'language']
for m in moduleList:
	try:
		del sys.modules[m]
		xbmc.output("del sys.module=%s" % m)
	except: pass

# remove other globals
try:
	del dialogProgress
except: pass
try:
	del config
except: pass
try:
	del dataSource
except: pass
try:
	del saveProgramme
except: pass
try:
	del mytvFavShows
except: pass

# goto xbmc home window
#try:
#	xbmc.executebuiltin('XBMC.ReplaceWindow(0)')
#except: pass
