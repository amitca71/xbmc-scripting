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
__version__ = '1.18.2'
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '03-03-2009'
xbmc.output(__scriptname__ + " Version: " + __version__ + " Date: " + __date__)

# Shared resources
DIR_HOME = os.getcwd().replace( ";", "" )
DIR_RESOURCES = os.path.join( DIR_HOME , "resources" )
DIR_RESOURCES_LIB = os.path.join( DIR_RESOURCES , "lib" )
DIR_USERDATA = xbmc.translatePath("/".join( ["T:", "script_data", __scriptname__] ))
DIR_CACHE = os.path.join( DIR_USERDATA, "cache" )
DIR_GFX = os.path.join( DIR_RESOURCES, "gfx" )
sys.path.insert(0, DIR_RESOURCES_LIB)

# Load Language using xbmc builtin
try:
    # 'resources' now auto appended onto path
    __language__ = xbmc.Language( DIR_HOME ).getLocalizedString
except:
	e = str( sys.exc_info()[ 1 ] )
	print e
	xbmcgui.Dialog().ok("XBMC Builtin Error", "Update XBMC to run this script", e)

import mytvGlobals
from bbbLib import *
from mytvLib import *
from bbbGUILib import *

from AlarmClock import AlarmClock
from smbLib import smbConnect

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

#		setResolution(self)

		# used to calc string width based on each char width
		self.fontAttr = FontAttr()
		self.currentTime = TVTime()

		# clock thread
		self.timerthread=Timer(self)

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
				if downloadLogos(self.tvChannels.getChannelNames()):
					self.tvChannels.loadLogoFilenames()	# reload logo filenames

			self.isFooterBtns = True
			self.rez = self.getResolution()
			debug("onInit() resolution=%s" % self.rez)

			self.epgSetup()		
			self.updateEPG(redrawBtns=True, updateLogo=True, updateChNames=True, forceLoadChannels=True)

			# footer
#			self.setupFooterNavLists()

			# start clock
			if self.timerthread:
				self.timerthread.start()

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
		from configmenu import ConfigGenreIcons, ConfigGenreColours
		self.genreIcons = ConfigGenreIcons().getEnabledGenres()

		# GENRES COLORS - (not all datasources use this)
		self.genreColours = ConfigGenreColours().load()
		del sys.modules['configmenu']

		debug("< initGenre()")

	###############################################################################################################
	# SETUP DYNAMIC COMPONENTS OF THE EPG DISPLAY
	def epgSetup(self):
		debug("> epgSetup()")
		xbmcgui.lock()

		self.use24HourClock = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_CLOCK)

		# title
		self.getControl(self.CLBL_PROG_TITLE).setLabel(__language__(300))	# please wait

		# title short desc
		self.descW = self.getControl(self.CLBL_PROG_DESC).getWidth()
		self.descColour = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_SHORT_DESC)

		# set SP DS label visible
		showDSSP = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SHOW_DSSP)
		text = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SAVE_PROG)
		if not text:
			text = MYTVConfig.VALUE_SAVE_PROG_NOTV
		self.getControl(self.CLBL_SAVEPROG).setLabel(text)
		self.getControl(self.CLBL_DATASOURCE).setLabel(mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_DATASOURCE))
		self.getControl(self.CLBL_DATASOURCE).setVisible(showDSSP)
		self.getControl(self.CLBL_SAVEPROG).setVisible(showDSSP)

		# set footer button labels
		self.getControl(self.CLBL_A_BTN).setLabel(__language__(420))
		self.getControl(self.CLBL_X_BTN).setLabel(__language__(423))
		self.getControl(self.CLBL_Y_BTN).setLabel(__language__(424))
		self.getControl(self.CLBL_WHITE_BTN).setLabel(__language__(425))
		self.getControl(self.CLBL_BACK_BTN).setLabel(__language__(500))

		# Channel names visible ?
		useChannelNames = (mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SHOW_CH_ID) != '0')
		debug("useChannelNames=%s" % useChannelNames)

		headerH = self.getControl(self.CGRP_HEADER).getHeight()
		footerH = self.getControl(self.CGRP_FOOTER_BTNS).getHeight()
		debug("headerH=%s footerH=%s" % (headerH, footerH))

		# EPG ROW
		self.epgRowH = int(mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_EPG_ROW_HEIGHT))
		epgRowGapH = int(mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_EPG_ROW_GAP_HEIGHT))
		self.epgRowFullH = self.epgRowH + epgRowGapH
		debug("epgRowH: %s epgRowGapH: %s = epgRowFullH:%s"  % (self.epgRowH,epgRowGapH,self.epgRowFullH))

		epgCtrl = self.getControl(self.CGRP_EPG)
		self.epgW = epgCtrl.getWidth()
		self.epgH = epgCtrl.getHeight()
		self.epgX, self.epgY = epgCtrl.getPosition()
		debug("epgX: %s epgY: %s epgW: %s epgH: %s"  % (self.epgX,self.epgY,self.epgW,self.epgH))

		epgTimeBarH = 25
		self.pageIndicatorH = 10				# the next/prev page available indicators
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
		if self.timerthread:
			self.timerthread.setClock(self.use24HourClock)
		self.clockLbl = self.getControl(self.CLBL_CLOCK)

		# NOW TIME INDICATOR LINE
		try:
			self.removeControl(self.nowTimeCI)
		except: pass
		colour = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_NOWTIME)
		ypos = self.epgY+1
		try:
			self.nowTimeCI = xbmcgui.ControlImage(-5, ypos, 0, self.epgH, ICON_NOW_TIME, colour)	# off screen
		except:
			self.nowTimeCI = xbmcgui.ControlImage(-5, ypos, 0, self.epgH, ICON_NOW_TIME)	# off screen
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
			font = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_FONT_CHNAMES)
			colour = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_CHNAMES)
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
		colour = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_ARROWS)
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
		ypos = (self.epgProgsY + self.epgProgsH) - self.pageIndicatorH
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
#		global dataSource, saveProgramme
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

		if not mytvGlobals.dataSource or resetDSSP:
			debug("init dataSource")
			try:
				del mytvGlobals.dataSource
				gc.collect()
			except: pass
			mytvGlobals.dataSource = None

			# import data source module
			mytvGlobals.dataSource = importDataSource()			# import datasource if already saved in config file
			if not mytvGlobals.dataSource:
				debug("< initData() error init datasource")
				return False
			elif canDataSourceConfig() and not configDataSource(forceReset=False):
				debug("< initData() error config datasource")
				return False

		if not mytvGlobals.saveProgramme or resetDSSP:
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

			if success and mytvGlobals.saveProgramme:
				# no need to save timers to local file if fetching from remote server
				saveToFile = not hasattr(mytvGlobals.saveProgramme,"getRemoteTimers")
				self.manageTimers = ManageTimers(saveToFile)	# True = save to file

				# some saveprogrammes need a full chList
				if hasattr(mytvGlobals.saveProgramme, "setChannelList"):
					debug("do setChannelList()")
					chList = self.tvChannels.getChannelNames()	# [chID, name, other]
					mytvGlobals.saveProgramme.setChannelList(chList)


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

		if mytvGlobals.saveProgramme:
			if hasattr(mytvGlobals.saveProgramme,"getRemoteTimers"):
				if sendWOL(True):
					debug("load remote timers")
					timers = mytvGlobals.saveProgramme.getRemoteTimers()
					if timers == None:		# none is error, [] is empty
						messageOK(mytvGlobals.saveProgramme.getName(), __language__(830),__language__(829)) # failed
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
			if not mytvGlobals.mytvFavShows:
				mytvGlobals.mytvFavShows = myTVFavShows()
			self.favShowsList = mytvGlobals.mytvFavShows.getTitles()
		except:
			handleException()
		debug("< initFavShows()")


	##############################################################################################################
	def onAction(self, action):
		try:
			actionID = action.getId()
			buttonID = action.getButtonCode()
		except: return

		if actionID in CANCEL_DIALOG + EXIT_SCRIPT or buttonID in CANCEL_DIALOG + EXIT_SCRIPT:
			debug("EXIT_SCRIPT")
			self.ready = False
			self.cleanup()
			self.close()
			return
		elif not self.ready:
			return

		self.ready = False
		if actionID in CONTEXT_MENU or buttonID in CONTEXT_MENU:
			debug("> CONTEXT_MENU")
			self.getControl(self.CGRP_HEADER).setEnabled(False)
			reInitLevel = MainMenu().ask()
			self.getControl(self.CGRP_HEADER).setEnabled(True)
			redraw = True
			forceLoadChannels = False
			updateChNames = False

			if reInitLevel == mytvGlobals.INIT_REDRAW:
				redraw = True
			elif reInitLevel == mytvGlobals.INIT_DISPLAY:
				self.epgSetup()                                     # re-create controls using new attrs
				updateChNames = True
			elif reInitLevel == mytvGlobals.INIT_PART:
				self.initData(False, False)	                        # part reset
			elif reInitLevel in (mytvGlobals.INIT_FULL, mytvGlobals.INIT_FULL_NOW):
				self.initData(True, True)	                        # full reset
				self.epgSetup()
				forceLoadChannels = True
				updateChNames = True
			elif reInitLevel == mytvGlobals.INIT_FAV_SHOWS:
				self.initFavShows()
			elif reInitLevel == mytvGlobals.INIT_TIMERS:
				self.initTimers()
			else:								# init_none
				redraw = False

			if reInitLevel != mytvGlobals.INIT_NONE:
				self.updateEPG(redrawBtns=redraw, updateLogo=True, updateChNames=updateChNames, forceLoadChannels=forceLoadChannels)
			debug("< CONTEXT_MENU")
		elif self.isFooterBtns:										# currently NAVIGATING USING EPG
			if actionID in CLICK_X or buttonID in CLICK_X:			# toggle footer display
				debug("CLICK_X")
				self.setupFooterNavLists()
				self.toogleFooter()
			elif actionID in CLICK_Y or buttonID in CLICK_Y:		# IMDb
				debug("CLICK_Y")
				title = self.getCurrentProgrammeTitle()
				if validProgramme(title):
					self.getControl(self.CGRP_HEADER).setEnabled(False)
					callIMDB(title)
					self.getControl(self.CGRP_HEADER).setEnabled(True)
			elif actionID in CLICK_B or actionID == ACTION_REMOTE_RECORD or buttonID in CLICK_B:
				# action according to function of B (red) btn.
				# no TV card == toggle SD/HD
				# TV card == SaveProgramme
				if not mytvGlobals.saveProgramme:
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
			if actionID in CLICK_X or buttonID in CLICK_X:
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
				if not mytvGlobals.saveProgramme:
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

		debug("< toogleFooter() isFooterBtns=%s" % self.isFooterBtns)

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
				desc = mytvGlobals.dataSource.getLink(link, title)
				# update desc if we don't already have something saved
				if not self.tvChannels.getProgAttr(prog, TVData.PROG_DESC):
					prog[TVData.PROG_DESC] = desc
				dialogProgress.close()
			else:
				desc = self.tvChannels.getProgAttr(prog, TVData.PROG_DESC)

			if not desc:
				desc = __language__(205)    # no info

			# remove Record option if already a timer
			if not mytvGlobals.saveProgramme:
				isTimer = None
			else:
				isTimer = self.isTimer(prog,chID)
			isFav = self.isFavShow(title)

			reInitLevel = pdd.ask(title,subTitle,genre,displayDate,desc,isTimer,isFav)
			if reInitLevel != mytvGlobals.INIT_NONE:
				if reInitLevel == mytvGlobals.INIT_TIMERS:
					self.initTimers()
				elif reInitLevel == mytvGlobals.INIT_FAV_SHOWS:
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
		if self.timerthread:
			self.timerthread.stop()

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
					ctrl.setLabel('')		# for label
					ctrl.setVisible(False)
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
		font = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_FONT_EPG)
		nofocusFile_odd = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_NOFOCUS_ODD)
		nofocusFile_even = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_NOFOCUS_EVEN)
		nofocusFile_fav = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_NOFOCUS_FAV)
		focusFile = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_FOCUS)
		textColor_odd = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_ODD)
		textColor_even = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_EVEN)
		textColor_fav = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_FAV)
		showCHIDType = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SHOW_CH_ID)
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
				self.epgChNames[epgChIDX].setVisible(channelLabel != '')

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
		debug("< drawChannel() No. btns on channel=%i" % len(channelData))

	###############################################################################################
	def drawTimers(self, epgChIDX, ypos):
		debug("> drawTimers() epgChIDX=%s" % epgChIDX)
		chID = self.tvChannels.getChannelID(self.allChannelIDX + epgChIDX)
		if self.timersDict.has_key(chID):
			colour = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_COLOUR_TIMERBAR)
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
				try:
					ctrl = xbmcgui.ControlImage(xpos, y, w, 0, ICON_TIMERBAR, colour)
				except:
					ctrl = xbmcgui.ControlImage(xpos, y, w, 0, ICON_TIMERBAR)
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
		if mytvGlobals.saveProgramme:
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
				descText += ": " + desc[:150].replace('\n',' ')
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
			buttonID = action.getButtonCode()
		except: return

		if actionID in CANCEL_DIALOG + EXIT_SCRIPT or buttonID in CANCEL_DIALOG + EXIT_SCRIPT:
			debug("ProgDescDialog() EXIT_SCRIPT")
			self._close_dialog()
		elif actionID in CLICK_B or actionID == ACTION_REMOTE_RECORD:		# RECORD / cancel record
			debug("ProgDescDialog() CLICK_B")
			self.actionB()
		elif actionID in CLICK_X:											# FAV
			debug("ProgDescDialog() CLICK_X")
			self.actionX()
		elif actionID in CLICK_Y:											# IMDB
			debug("ProgDescDialog() CLICK_Y")
			self.actionY()

	#################################################################################################################
	def onClick(self, controlID):
		debug("onClick() controlID=%s" % controlID)

		if controlID == self.CLBL_B:
			debug("onClick() CLICK_B")
			self.actionB()		# rec
		elif controlID == self.CLBL_X:
			debug("onClick() CLICK_X")
			self.actionX()		# fav
		elif controlID == self.CLBL_Y:
			debug("onClick() CLICK_Y")
			self.actionY()		# imdb
		elif controlID == self.CLBL_BACK:
			debug("onClick() CLICK_BACK")
			self._close_dialog()

	#################################################################################################################
	def _close_dialog( self ):
		debug("_close_dialog()")
		self.close()

	#################################################################################################################
	def actionB(self):
		debug("actionB()")
		if self.isTimer != None:										# disabled
			if not self.isTimer:
				if callSaveProgramme():									# record
					self.optReInit = mytvGlobals.INIT_TIMERS
					self.close()
			elif callManageSaveProgramme():								# cancel record
				self.optReInit = mytvGlobals.INIT_TIMERS
				self.close()

	#################################################################################################################
	def actionX(self):
		debug("actionX()")
#		global mytvFavShows
		chID, chName, chIDAlt = mytv.tvChannels.getChannelInfo(mytv.allChannelIDX+mytv.epgChIDX)
		if not self.isFav:
			# ADD fav
			if mytvGlobals.mytvFavShows.addToFavShows(self.title, chID, chName):
				self.optReInit = mytvGlobals.INIT_FAV_SHOWS
				self.close()
		else:
			# CANCEL fav
			if mytvGlobals.mytvFavShows.deleteShow(self.title, chID):
				self.optReInit = mytvGlobals.INIT_FAV_SHOWS
				self.close()

	#################################################################################################################
	def actionY(self):
		debug("actionY()")
		self.getControl(self.CGRP_DIALOG).setVisible(False)
		callIMDB()
		self.getControl(self.CGRP_DIALOG).setVisible(True)


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


#######################################################################################################################    
# show menu of strm packs, then menu of contents which can be selected & played
#################################################################################################################
def playStreamPack():
	debug("> playStreamPack()")
	mask = "|".join( [ '.strm', '.pls','.m3u' ] )
	
	if DIR_CACHE[-1] != os.sep:
		defaultFolder = DIR_CACHE + os.sep
	else:
		defaultFolder = DIR_CACHE
	fn = xbmcgui.Dialog().browse(1, __language__(512), "files", mask, False, False, defaultFolder)
	debug("browse fn=%s" % fn)
	if fn and fn != DIR_CACHE:
		xbmc.Player().play(fn)
	debug("< playStreamPack()")


#######################################################################################################################    
# show all files on SMB as a menu, 
#################################################################################################################
def playSMBVideo():
	debug("> playSMBVideo()")
	smbPath = mytvGlobals.config.getSMB(MYTVConfig.KEY_SMB_PATH)
	mask = xbmc.getSupportedMedia('video')
	fn = xbmcgui.Dialog().browse(1, __language__(506), "files", mask, False, False, smbPath)
	debug("browse fn=%s" % fn)
	if fn and fn != smbPath:
		xbmc.Player().play(fn)
		xbmc.executebuiltin("xbmc.ActivateWindow('video')")
		isPlaying = True
	else:
		isPlaying = False
	debug("< playSMBVideo() playing=%s" % isPlaying)
	return isPlaying


#################################################################################################################
# MENU ITEM - select save programme method, SMB or external custom module (SaveProgramme.py)
#################################################################################################################
def callSaveProgramme(prog=None, channelInfo=None, confirmRequired=True):
	debug("> callSaveProgramme()")
	success = False
	# if MAC, send WOL nd check is awake before continuing
	if mytvGlobals.saveProgramme and sendWOL(True):

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
		elif mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_TIMER_CLASH_CHECK) and mytv.manageTimers.checkTimerClash(prog):
			success = False
		else:
			try:
				saveProgMethod = mytvGlobals.saveProgramme.saveMethod()
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
						if xbmcgui.Dialog().yesno(mytvGlobals.saveProgramme.getName(), title, displayDate, chName, __language__(355), __language__(800)):
							doRec = True
							# allow for any custom saveprogramme record prompts. None indicates failure
							if hasattr(mytvGlobals.saveProgramme, "customPrompts") and mytvGlobals.saveProgramme.customPrompts() == None:
								doRec = False

							if doRec:
								# call external Save Programme module
								dialogProgress.create(mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SAVE_PROG))    # module name
								returnValue = mytvGlobals.saveProgramme.run(channelInfo, prog, confirmRequired)
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
			if success and not hasattr(mytvGlobals.saveProgramme, "getRemoteTimers"):
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

#	global saveProgramme
	if mytvGlobals.saveProgramme:
		if hasattr(mytvGlobals.saveProgramme, "manage"):     # manage with it own menu eg. Nebula
			debug("do saveProgramme manage")
			timers = mytvGlobals.saveProgramme.manage()
			mytv.timersDict, mytv.timersProgIDList = mytv.manageTimers.refreshTimerFiles(timers)
			deleted = True
		else:
			debug("do local ManageTimers menu")
			# check if saveprogramme has a remote delete func
			doRemoteDelete = hasattr(mytvGlobals.saveProgramme, "deleteTimer")
			debug("doRemoteDelete=%s" % doRemoteDelete)

			# show menu and delete each timer as selected
			while True:
				timer = mytv.manageTimers.ask()
				if not timer: break

				startTime = timer[ManageTimers.REC_STARTTIME]
				if doRemoteDelete:
					if mytvGlobals.saveProgramme.deleteTimer(timer) and mytv.manageTimers.deleteTimer(startTime):
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
		from IMDbWinXML import IMDbWin
		IMDbWin("script-bbb-imdb.xml", DIR_HOME, "Default").ask(title)
		del sys.modules['IMDbWinXML']
	debug("< callIMDB()")

#######################################################################################################################    
def callTVCom():
	debug("> callTVCom()")
	success = False

	# import module
	try:
		pathHome = "/".join(["Q:", "Scripts", "tv.com"])
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

	configFilename = mytvGlobals.config.getSMB(MYTVConfig.KEY_SMB_FILE)
	ip = mytvGlobals.config.getSMB(MYTVConfig.KEY_SMB_IP)
	smbPath = mytvGlobals.config.getSMB(MYTVConfig.KEY_SMB_PATH)
	if not configFilename or not ip or not smbPath:
		from smbLib import ConfigSMB
		cSMB = ConfigSMB()
		cSMB.ask()
		doSave = cSMB.checkAll()
	else:
		doSave = True

	if doSave:
		pst = ProgrammeSaveTemplate()
		localFile = os.path.join(DIR_CACHE, "temp.dat")
		title = mytv.tvChannels.getProgAttr(programme, TVData.PROG_TITLE).encode('latin-1','replace')

		# if DATA not supplied, load SAVE STRING from config file then expand
		if not data:
			template = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SAVE_TEMPLATE)
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
		selectDialog.setup("SELECT RECORDING DATE:", rows=len(menuList), width=270, panel=mytvGlobals.DIALOG_PANEL)
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
		selectDialog.setup(__language__(575), rows=len(menuList), width=270, panel=mytvGlobals.DIALOG_PANEL)
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
		selectDialog.setup(__language__(576), rows=len(self.FREQ_DUR_OPTS), width=250, panel=mytvGlobals.DIALOG_PANEL)
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
			selectDialog.setup(__language__(509), width=620, rows=len(menuList), panel=mytvGlobals.DIALOG_PANEL)
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
			reInit = mytvGlobals.INIT_REDRAW
		else:
			reInit = mytvGlobals.INIT_NONE
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
			selectDialog.setup(__language__(517) + ' ' + __language__(586), rows=len(menu), width=620, panel=mytvGlobals.DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menu)
			if selectedPos <= 0:
				break

			msgs = menu[selectedPos].split(',')
			if xbmcgui.Dialog().yesno(__language__(517), msgs[0].strip(), msgs[1].strip(), msgs[2].strip(), \
										__language__(355), __language__(356)):

				alarmTime = alarmClock.alarms.keys()[selectedPos-1]		# allow for exit opt
				deleted = alarmClock.cancelAlarm(alarmTime)
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
		self.OPT_LSOTV = __language__(519)
		self.OPT_CONFIG_MENU = __language__(502)
		self.OPT_CANCEL_FAV = __language__(520)
		self.OPT_SAVEPROG_PLAYBACK = __language__(503)

		self.alarmClock = AlarmClock()
		self.countryCode = upper(mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_DATASOURCE)[:2])

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
			self.OPT_LSOTV,
			self.OPT_MANUAL_TIMER,
			self.OPT_VIEW_TIMERS,
			self.OPT_ALARMCLOCK,
			self.OPT_MANAGE_ALARMCLOCK,
			self.OPT_SAVEPROG_PLAYBACK,
			self.OPT_PLAY_SMB,
			self.OPT_STREAMURL,
			self.OPT_CONFIG_MENU
			]

		if not mytvGlobals.saveProgramme or not hasattr(mytvGlobals.saveProgramme, "playbackFromFile"):
			self.menu.remove(self.OPT_SAVEPROG_PLAYBACK)

		# check if a non programme
		isValidProg = validProgramme(self.title)
		if not isValidProg:
			self.menu.remove(self.OPT_ADD_FAV)
			self.menu.remove(self.OPT_CANCEL_FAV)
			self.menu.remove(self.OPT_TVRAGE)
			self.menu.remove(self.OPT_ALARMCLOCK)

		# not using tv card, remove timer options
		if not mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SAVE_PROG):
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

		# remove OPT_LSOTV if not UK or not config enabled
		useLiveSportOnTv = (mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_USE_LSOTV) or self.countryCode == 'UK')
		if not useLiveSportOnTv:
			self.menu.remove(self.OPT_LSOTV)

		# remove view/manage fav shows if non saved
		if not mytvGlobals.mytvFavShows or not mytvGlobals.mytvFavShows.getTitles():
			self.menu.remove(self.OPT_MANAGE_FAV)
			self.menu.remove(self.OPT_VIEW_FAV)

		# remove HD/Normal option if no HD Channels if non avail.
		if not mytv.areHDChannels:
			self.menu.remove(self.OPT_CH_VIEW)

		# alarm clock
		self.alarmClock.loadAlarms()
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

		reInit = mytvGlobals.INIT_NONE
		selectedPos = 0
		exit = False
		while not exit:
			optReInit = mytvGlobals.INIT_NONE
			self.setupMenuOptions()
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(501), rows=len(self.menu), width=330, banner=LOGO_FILENAME, panel=mytvGlobals.DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(self.menu, selectedPos)
			if selectedPos <= 0:				# exit selected
				break

			elif self.menu[selectedPos] == self.OPT_SAVEPROG_PLAYBACK:			# playback via
				mytvGlobals.saveProgramme.playbackFromFile()
			
			elif self.menu[selectedPos] == self.OPT_ADD_FAV:			# Add to fav
				if mytvGlobals.mytvFavShows.addToFavShows(self.title, chID, chName):
					optReInit = mytvGlobals.INIT_FAV_SHOWS
					exit = True
			elif self.menu[selectedPos] == self.OPT_CANCEL_FAV:			# Cancel fav
				if mytvGlobals.mytvFavShows.deleteShow(self.title, chID):
					optReInit = mytvGlobals.INIT_FAV_SHOWS
					exit = True
			elif self.menu[selectedPos] == self.OPT_MANAGE_FAV:			# delete/list fav shows
				if mytvGlobals.mytvFavShows.manageFavShows():
					optReInit = mytvGlobals.INIT_FAV_SHOWS
			elif self.menu[selectedPos] == self.OPT_VIEW_FAV:			# display 7-day fav show list
				mytvGlobals.mytvFavShows.ask()
#			elif self.menu[selectedPos] == self.OPT_VIEW_TVCOM:			# TV.com
#				callTVCom()
			elif self.menu[selectedPos] == self.OPT_VIEW_TIMERS:		# view timers
				if callManageSaveProgramme():							# call custom or gui SaveProgramme manager
					optReInit = mytvGlobals.INIT_REDRAW
			elif self.menu[selectedPos] == self.OPT_STREAMURL:			# list/select/stream url 
				playStreamPack()
			elif self.menu[selectedPos] == self.OPT_PLAY_SMB:			# list/select/play smb videp file
				if playSMBVideo():
					break # quit menu now
			elif self.menu[selectedPos] == self.OPT_CONFIG_MENU:		# config menu
				import configmenu
				optReInit = configmenu.ConfigMenu().ask()
				if optReInit != mytvGlobals.INIT_NONE:
					self.setupMenuOptions()								# may need to remove menu options
				del sys.modules['configmenu']
			elif self.menu[selectedPos] == self.OPT_MANUAL_TIMER:
				if ManualTimer().ask():
					optReInit = mytvGlobals.INIT_TIMERS
					exit = True
			elif self.menu[selectedPos] == self.OPT_CH_VIEW:
				mytv.justHDChannels = not mytv.justHDChannels
				optReInit = mytvGlobals.INIT_FULL
				exit = True
			elif self.menu[selectedPos] == self.OPT_IMDB_MANUAL:
				callIMDB()
			elif self.menu[selectedPos] == self.OPT_ALARMCLOCK:
				if setAlarmClock():
					exit = True
			elif self.menu[selectedPos] == self.OPT_MANAGE_ALARMCLOCK:
				manageAlarms()
			elif self.menu[selectedPos] == self.OPT_TVRAGE:
				import tvrage
				tvrage.TVRage().ask(self.title, self.countryCode)
				del sys.modules['tvrage']
			elif self.menu[selectedPos] == self.OPT_LSOTV:
				import livesportontv
				livesportontv.LiveSportOnTV().ask()
				del sys.modules['livesportontv']
			else:
				debug("unknown option %s" % self.menu[selectedPos])

			debug("optReInit=%s" % optReInit)
			if optReInit > reInit:
				reInit = optReInit	# save highest reinit level

			del selectDialog

			# quit menu if some option requested
			if optReInit == mytvGlobals.INIT_FULL_NOW:
				exit = True

#		del favShows
		debug("< MainMenu().ask() reInit: %s" % reInit)
		return reInit




#################################################################################################################
def validProgramme(title):
    return (title and title not in (__language__(204), __language__(203)))


######################################################################################    
# BEGIN !
######################################################################################

# check for script update
updated = False
if mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_CHECK_UPDATE):
    updated = updateScript(False)

if not updated:
	try:
		# check language loaded
		xbmc.output( "__language__ = %s" % __language__ )
		# start script main
		mytv = myTV("script-mytv-main.xml", DIR_HOME, "Default")
		if mytv.ready:
			mytv.doModal()
		del mytv
	except:
		handleException()

debug("exiting script: " + __scriptname__)
moduleList = ['mytvLib', 'bbbLib', 'bbbGUILib','smbLib', 'IMDbWin', 'IMDbLib','AlarmClock','FavShows','mytvGlobals.saveProgramme','mytvGlobals.datasource','tv.com','mytvGlobals.mytvFavShows','wol']
for m in moduleList:
	try:
		del sys.modules[m]
		xbmc.output(__scriptname__ + " del module=%s" % m)
	except: pass

# remove other globals
try:
	del dialogProgress
except: pass
try:
	del mytvGlobals.config
except: pass
try:
	del mytvGlobals.dataSource
except: pass
try:
	del mytvGlobals.saveProgramme
except: pass
try:
	del mytvGlobals.mytvFavShows
except: pass

# goto xbmc home window
#try:
#	xbmc.executebuiltin('XBMC.ReplaceWindow(0)')
#except: pass
