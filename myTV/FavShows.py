"""
 FavShows - Displays channel/time for when a Fav. shows is on in the next 7 days.

 Changelog:
 07-01-06 - Fix: Unicode problems
 04-08-06 - Change: List height increases for HDTV rez.
 09-09-06 - Updated to be inline with myTV v1.14 changes
 15-11-06 - Changes in line with myTV v1.15
 13-02-07 - Changed the way it gets datasource and saves favShows
 24-08-07 - Fixed to work with myTV v1.17a
 18-08-08 - Updated for use with myTV v1.18
 23/02/09 - translatePath()
"""

import sys,os.path,os
import xbmc, xbmcgui
from string import replace,split,upper

# Script doc constants
__title__ = "FavShows"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '23-02-09'
try:
	__scriptname__ = sys.modules[ "__main__" ].__scriptname__
	xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)
	DIR_USERDATA = sys.modules[ "__main__" ].DIR_USERDATA
	__language__ = sys.modules[ "__main__" ].__language__
except:
	__scriptname__ = "myTV"
	xbmc.output("Loading: " + __title__ + " Date: " + __date__)  
	if os.name=='posix':    
		DIR_HOME = os.path.abspath(os.curdir).replace(';','')		# Linux case
	else:
		DIR_HOME = os.getcwd().replace( ";", "" )
	DIR_RESOURCES = os.path.join( DIR_HOME , "resources" )
	DIR_RESOURCES_LIB = os.path.join( DIR_RESOURCES , "lib" )
	DIR_USERDATA = xbmc.translatePath("/".join(["T:", "script_data", __scriptname__] ))
	DIR_CACHE = os.path.join( DIR_USERDATA, "cache" )
	sys.path.insert(0, DIR_RESOURCES_LIB)

	# Load Language using xbmc builtin
	try:
		# 'resources' now auto appended onto path
		__language__ = xbmc.Language( DIR_HOME ).getLocalizedString
		if not __language__( 0 ): raise
	except:
		xbmcgui.Dialog().ok("XBMC Language Error", "Failed to load xbmc.Language.", "Update your XBMC to a newer version.")


from bbbLib import *
from bbbGUILib import *
from mytvLib import *

dialogProgress = xbmcgui.DialogProgress()

class myTVFavShows(xbmcgui.Window):
	def __init__(self):
		debug("> myTVFavShows().init")

		self.favShowsList = []

		try:
			global dataSource
			self.dataSource = dataSource
		except:
			self.dataSource = importDataSource()

		# init start time
		self.currentTime = time.mktime(time.localtime(time.time()))
		self.startupCurrentTime = self.currentTime
		if self.dataSource:
			self.FAVSHOWS_FILENAME = os.path.join(DIR_USERDATA, 'favshows_'+self.dataSource.getName()+'.dat')
			debug("favShowsFilename: " + self.FAVSHOWS_FILENAME)
		else:
			messageOK("No DataSource imported","Use myTV to configure a DataSource.")

		self.tvdata = TVData()
		debug("< myTVFavShows().init")

	def onAction(self, action):
		if not action:
			return
		if action in CANCEL_DIALOG + EXIT_SCRIPT:
			self.close()

	def onControl(self, control):
		if control == self.favShowsCONTROLS[self.CTRL_PREV_BTN]:
			debug("favShowsCONTROL_PREV_BTN")
			if self.currentTime > self.startupCurrentTime:
				self.currentTime -= (86400 * 7)					# sub 7 days
				daysList = self.searchFavShows(self.favShowsList, self.currentTime)
				self.loadLists(daysList)
			else:
				debug("action ignored, going back past startup time")

			# turn off/on prev btn as needed
			visible = self.currentTime > self.startupCurrentTime
			self.favShowsCONTROLS[self.CTRL_PREV_BTN].setVisible(visible)
			if not visible:
				self.setFocus(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])

		elif control == self.favShowsCONTROLS[self.CTRL_NEXT_BTN]:
			debug("favShowsCONTROL_NEXT_BTN")
			self.currentTime += (7 * 86400)					# add 7 days
			daysList = self.searchFavShows(self.favShowsList, self.currentTime)
			self.loadLists(daysList)

			# turn off/on prev btn as needed
			self.favShowsCONTROLS[self.CTRL_PREV_BTN].setVisible(self.currentTime > self.startupCurrentTime)

	def ask(self):
		debug("> myTVFavShows.ask()")

		if not self.favShowsList:
			messageOK(__language__(508), __language__(213))
		else:
			self.setupFavShowDisplay()
			daysList = self.searchFavShows(self.favShowsList, self.currentTime)
			self.loadLists(daysList)
			self.doModal()

		debug("< myTVFavShows.FavSHows().ask()")

	def setupFavShowDisplay(self):
		debug("> myTVFavShows.setupFavShowDisplay")

		setResolution(self)
		xbmcgui.lock()

		# BACKGROUND SKIN
		try:
			self.addControl(xbmcgui.ControlImage(0,0, REZ_W, REZ_H, BACKGROUND_FILENAME))
		except: pass

		# fav show display controls
		self.CTRL_PREV_BTN = 'prevbtn'
		self.CTRL_NEXT_BTN = 'nextbtn'
		self.favShowsCONTROLS = {}
		self.favShowsCONTROLS_LIST = []
		self.favShowsCONTROLS_LBL = []
		self.favShowsCONTROLS_BTN = []

		titleH = 23
		labelH = 20
		xpos = 5
		ypos = titleH

		# listH determined by rez
		numListRows = 3
		listW = 230
		epgH = REZ_H - titleH - (labelH * numListRows)
		debug("epgH = " + str(epgH))
		listH = epgH / numListRows
		debug("listH = " + str(listH))
		btnH = 30
		btnW = listW-10

		# display title
		self.addControl(xbmcgui.ControlLabel(xpos, 0, 0, titleH, __language__(508), FONT13, "0xFFFFFF00"))

		# create each day , incl. prev/next btns as a day each
		for day in range(7):
			# day header label
			ctrl = xbmcgui.ControlLabel(xpos, ypos, listW, labelH, '', FONT11, "0xFFFFFF99")
			self.favShowsCONTROLS_LBL.append(ctrl)
			self.addControl(ctrl)

			# create a control btn as background
			ctrl = xbmcgui.ControlButton(xpos-3, ypos+labelH-3, listW+6, listH+6, '', \
											FRAME_FOCUS_FILENAME, FRAME_NOFOCUS_FILENAME)
			self.favShowsCONTROLS_BTN.append(ctrl)
			self.addControl(ctrl)

			# list - allow for extra unused spinner space at bottom
			ctrl = xbmcgui.ControlList(xpos, ypos + labelH, listW+5, listH+20, FONT10, imageWidth=0, \
									   itemTextXOffset=0, itemHeight=16, alignmentY=XBFONT_CENTER_Y)
			self.favShowsCONTROLS_LIST.append(ctrl)
			self.addControl(ctrl)
			ctrl.setPageControlVisible(False)

			# new row
			if day == 2:
				xpos = 5
				ypos += labelH + listH + 4
			elif day == 5:
				xpos = listW + 10
				ypos += labelH + listH + 4
			else:
				xpos += listW +10

		# PREV btn
		x = 5
		y = int(REZ_H - (listH/2) - (btnH/2))
		ctrl = xbmcgui.ControlButton(x, y, btnW, btnH, '< ' + __language__(588),alignment=XBFONT_CENTER_X)
		self.favShowsCONTROLS[self.CTRL_PREV_BTN]=ctrl
		self.addControl(ctrl)

		# NEXT btn
		x += listW + listW + 15
		ctrl = xbmcgui.ControlButton(x, y, btnW, btnH, __language__(587) + ' >',alignment=XBFONT_CENTER_X)
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN]=ctrl
		self.addControl(ctrl)

		# NAVIGATION - any ctrl to next adjacent ctrl
		day = 0
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS_BTN[day+1])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS[self.CTRL_PREV_BTN])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS_BTN[day+3])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS_BTN[day+1])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS_BTN[day-1])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS_BTN[6])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS_BTN[day+3])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS_BTN[day+1])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS_BTN[day-1])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS_BTN[day+3])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS_BTN[day+1])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS_BTN[day-1])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS_BTN[day-3])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS[self.CTRL_PREV_BTN])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS_BTN[day+1])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS_BTN[day-1])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS_BTN[day-3])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS_BTN[6])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS[self.CTRL_PREV_BTN])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS_BTN[day-1])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS_BTN[day-3])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS[self.CTRL_PREV_BTN])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS_BTN[4])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS_BTN[1])

		# prev btn
		self.favShowsCONTROLS[self.CTRL_PREV_BTN].controlRight(self.favShowsCONTROLS_BTN[6])
		self.favShowsCONTROLS[self.CTRL_PREV_BTN].controlLeft(self.favShowsCONTROLS_BTN[5])
		self.favShowsCONTROLS[self.CTRL_PREV_BTN].controlUp(self.favShowsCONTROLS_BTN[3])
		self.favShowsCONTROLS[self.CTRL_PREV_BTN].controlDown(self.favShowsCONTROLS_BTN[0])
		self.favShowsCONTROLS[self.CTRL_PREV_BTN].setVisible(False)

		# next btn
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN].controlRight(self.favShowsCONTROLS_BTN[0])
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN].controlLeft(self.favShowsCONTROLS_BTN[6])
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN].controlUp(self.favShowsCONTROLS_BTN[5])
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN].controlDown(self.favShowsCONTROLS_BTN[2])
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN].setVisible(True)

		self.setFocus(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])
		xbmcgui.unlock()
		debug("< myTVFavShows.setupFavShowDisplay")

	def addToFavShows(self, showName, chID, chName):
		debug("> myTVFavShows.addToFavShows()")

		if not showName:
			messageOK(__language__(507), __language__(123))
			debug("< myTVFavShows.addToFavShows() bad prog")
			return False

		elif not xbmcgui.Dialog().yesno(__language__(507), chName, showName):	# add ?
			debug("< myTVFavShows.addToFavShows() cancelled")
			return False

		elif not self.favShowsList:
			self.loadFavShows()

		# check for duplicate show selection, unique to channel only
		dup = False
		for show in self.favShowsList:
			loadedShowName = show[0]
			loadedChID = show[1]
			if showName == loadedShowName and chID == loadedChID:
				dup = True
				break

		# save to file
		if not dup:
			self.favShowsList.append([showName, chID, chName])
			self.saveFavShows()
		else:
			messageOK(__language__(507), __language__(124))

		success = not dup
		debug("< myTVFavShows.addToFavShows() success=%s" % success)
		return success

	def loadFavShows(self):
		debug("> myTVFavShows.loadFavShows()")
		self.favShowsList = []
		if fileExist(self.FAVSHOWS_FILENAME):
			for readLine in file(self.FAVSHOWS_FILENAME):
				title, chID, chName = readLine.split('~')
				self.favShowsList.append([title.decode('latin-1', 'replace').strip(), \
								chID, chName.decode('latin-1', 'replace').strip()])
		else:
			debug("file missing: " + self.FAVSHOWS_FILENAME)
		debug("< myTVFavShows.loadFavShows() sz: " + str(len(self.favShowsList)))

	def saveFavShows(self):
		debug("> myTVFavShows.saveFavShows()")
		success = False
		if not self.favShowsList:
			deleteFile(self.FAVSHOWS_FILENAME)
			success = True
		else:
			try:
				fp = open(self.FAVSHOWS_FILENAME, 'w')
				for showName, chID, chName in self.favShowsList:
					showName = showName.encode('latin-1', 'replace').strip()
					chName = chName.encode('latin-1', 'replace').strip()
					fp.write(showName + '~' + chID + '~' + chName+'\n')
				fp.close()
				success = True
			except:
				handleException()
		debug("< myTVFavShows.saveFavShows() success=%s" % success)
		return success

	def getTitles(self):
		debug("> myTVFavShows.getTitles()")
		if not self.favShowsList:
			self.loadFavShows()

		titleList = []
		for title, chID, chName in self.favShowsList:
			titleList.append(title)

		debug("< myTVFavShows.getTitles() sz: %s" % len(titleList))
		return titleList

	def manageFavShows(self):
		debug("> myTVFavShows.manageFavShows()")

		deleted = False
		if not self.favShowsList:
			messageOK(__language__(510), __language__(213))
		else:
			heading = "%s %s" % (__language__(510), __language__(586))
			while True:
				# create menu
				menu = [__language__(500)]
				self.favShowsList.sort()
				for showName, chID, chName in self.favShowsList:
					showName = showName.encode('latin-1', 'replace')
					chName = chName.encode('latin-1', 'replace')
					menu.append(xbmcgui.ListItem(showName, chName))

				selectDialog = DialogSelect()
				selectDialog.setup(heading, rows=len(menu), width=600)
				selectedPos, acton = selectDialog.ask(menu)
				if selectedPos <= 0:
					break		# stop

				showName = menu[selectedPos].getLabel2()
				chName = menu[selectedPos].getLabel()
				if xbmcgui.Dialog().yesno(__language__(510), showName, chName, "", __language__(355), __language__(356)):
					del self.favShowsList[selectedPos-1]
					deleted = True

				del selectDialog

			if deleted:
				self.saveFavShows()	# write whole list
		debug("< myTVFavShows.manageFavShows() deleted="+str(deleted))
		return deleted

	def deleteShow(self, title, chID):
		debug("> myTVFavShows.deleteShow() title=%s chID=%s" % (title, chID))

		if xbmcgui.Dialog().yesno(__language__(510), title, "", "", __language__(355), __language__(356)):
			# find show on channel
			deleted = False
			for i, rec in enumerate(self.favShowsList):
				showName, showChID, chName = rec
				if showName == title and showChID == chID:
					del self.favShowsList[i]
					self.saveFavShows()
					deleted = True
					break

		debug("< myTVFavShows.deleteShow() deleted=%s" % deleted)
		return deleted

	def searchFavShows(self, showList, currentTime):
		debug("> myTVFavShows.searchFavShows() currentTime=" + str(currentTime))
		dialogProgress.create(__language__(508), __language__(300))

		# for each day, examine just the channel stored against show
		commsError = False
		daysList = []
		for day in range(7):
			fileDate = getTodayDate(currentTime)
			debug("day=%s fileDate=%s" % (day, fileDate))

			dayList = []
			# examine all progs on this channel, looking each occurance for show
			for showDetails in showList:
				try:
					show, chID, chName = showDetails
					chName = chName.strip()
				except:
					# unpack error, ignore show
					continue

				# load channel progs
				if not commsError:
					filename =  os.path.join(DIR_CACHE, "%s_%s.dat" % (chID,fileDate))
					filename = xbmc.makeLegalFilename(filename)
					progList = self.dataSource.getChannel(filename, chID, chName, day, fileDate)
					if not progList:
						commsError = True
					else:
						# CHECK CONTINUITY AND SAVE TO FILE
						saveChannelToFile(progList, filename)

				if commsError:
					dayList.append(['HTTP Timeout or Error','',''])
					break
				else:
					# examine all progs on this channel for our fav show name
					showUPPER = show.upper()
					for prog in progList:
						title = self.tvdata.getProgAttr(prog, TVData.PROG_TITLE).upper()
						if title.startswith(showUPPER):
							startTime = self.tvdata.getProgAttr(prog, TVData.PROG_STARTTIME)
							dayList.append([show, chName[:6].strip(), startTime])

			daysList.append(dayList)
			currentTime += 86400					# add 1 day

		dialogProgress.close()
		debug("< myTVFavShows.searchFavShows()")
		return daysList

	# load shows into relevant day list
	def loadLists(self, daysList):
		debug("> myTVFavShows.loadLists()")
		xbmcgui.lock()

		currentTime = self.currentTime
		for dayIDX in range(7):
			dayList = daysList[dayIDX]

			# setup list title to be DATE
			listTitle = time.strftime("%a %d %b",time.localtime(currentTime))
			self.favShowsCONTROLS_LBL[dayIDX].setLabel(listTitle)

			self.favShowsCONTROLS_LIST[dayIDX].reset()
			for title, chName, startTime in dayList:
				if startTime:
					startDate = time.strftime("%H:%M", time.localtime(startTime))
					lbl2= chName + "," + startDate
				else:
					lbl2 = ''
				self.favShowsCONTROLS_LIST[dayIDX].addItem(xbmcgui.ListItem(title, label2=lbl2))

			currentTime += 86400	# add 1 day
		xbmcgui.unlock()
		debug("< myTVFavShows.loadLists()")


########################################################################################################
# Determine if standalone startup or imported
########################################################################################################
if __name__ == '__main__':
	makeScriptDataDir()
	print "myTVFavShows is __main__"
	myTVFavShows().ask()
	del myTVFavShows
