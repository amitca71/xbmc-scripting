"""
 TVRage - tv show episode guide powered from www.TVRage.com
"""  

import xbmc, xbmcgui
import sys, os.path
from bbbLib import *
from bbbGUILib import DialogSelect
import mytvGlobals

__language__ = sys.modules[ "__main__" ].__language__
DIR_GFX = sys.modules[ "__main__" ].DIR_GFX     			# should be in default.py
DIR_CACHE = sys.modules["__main__"].DIR_CACHE
DIR_DATASOURCE_GFX = sys.modules["mytvLib"].DIR_DATASOURCE_GFX
#global DIALOG_PANEL
#DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL

class TVRage:

	URL_BASE = 'http://www.tvrage.com/'
	DEFAULT_COUNTRY = "US"

	def __init__(self):
		debug("> TVRage() init()")

		self.schedule = {}
		self.FILE_SHOW_IMAGE = os.path.join(DIR_CACHE, 'tvrage_image_%s')
		self.FILE_LOGO = os.path.join(DIR_GFX, 'tvrage.jpg')
		self.FILE_SCHEDULE = os.path.join(DIR_CACHE, 'tvrage_schedule_%s.dat' % getTodayDate())

		self.URL_SCHEDULE = self.URL_BASE + 'quickschedule.php?show_yesterday=1&country=%s'
		self.URL_QUICK_INFO = self.URL_BASE + 'quickinfo.php?show=%s'
		self.URL_SEARCH = self.URL_BASE + 'search.php?search=%s&show_ids=1&sonly=1'

		self.MENU_OPT_YESTERDAY = __language__(330)
		self.MENU_OPT_TODAY = __language__(327)
		self.MENU_OPT_TOMORROW = __language__(328)
		self.MENU_OPT_WEEK = __language__(581)
		self.MENU_OPT_DAY = __language__(582)
		self.MENU_OPT_CURR_PROG = __language__(583)
		self.MENU_OPT_SEARCH = __language__(584)
		self.MENU_OPT_COUNTRY = __language__(585)

		# showInfo dict keys
		self.KEY_SHOW_URL = 'Show URL'
		self.COUNTRIES = (__language__(500), "AU","CA","JP","SE","UK","US")

		# dayDelta 0, 1, 2
		self.DAYS = [__language__(330),__language__(327),__language__(328)]    #'Yesterday','Today','Tomorrow'

		debug("< TVRage() init()")

	def getScheduleFN(self):
		return self.FILE_SCHEDULE

	###################################################################################################################
	def onAction(self, action):
		try:
			actionID = action.getId()
			buttonCode = action.getButtonCode()
		except: return

		if actionID in CANCEL_DIALOG + EXIT_SCRIPT or buttonCode in CANCEL_DIALOG + EXIT_SCRIPT:
#			self.deleteCache()
			self.close()

	###################################################################################################################
	def onControl(self, control):
		pass

	###################################################################################################################
	def createMainMenu(self):
		self.mainMenu = [xbmcgui.ListItem(__language__(500)), 
						xbmcgui.ListItem(self.MENU_OPT_YESTERDAY),
						xbmcgui.ListItem(self.MENU_OPT_TODAY),
						xbmcgui.ListItem(self.MENU_OPT_TOMORROW),
						xbmcgui.ListItem(self.MENU_OPT_WEEK),
						xbmcgui.ListItem(self.MENU_OPT_DAY),
						xbmcgui.ListItem(self.MENU_OPT_CURR_PROG),
						xbmcgui.ListItem(self.MENU_OPT_SEARCH),
						xbmcgui.ListItem(self.MENU_OPT_COUNTRY, self.countryCode)
						]

	#################################################################################################################
	def deleteCache(self):
		debug("> TVRage.deleteCache()")

		try:
			if os.path.exists(DIR_CACHE):
				files = os.listdir(DIR_CACHE)
				for filename in files:
					if not filename.startwith('tvrage_schedule') and filename.startswith('tvrage'):
						deleteFile(os.path.join(DIR_CACHE, filename))
		except:
			handleException("deleteCache()")

		debug("< TVRage.deleteCache()")

	###################################################################################################################
	def selectCountry(self):
		debug("> TVRage.selectCountry()")

		origCode = self.countryCode
		flags = []
		for code in self.COUNTRIES:
			flags.append(os.path.join(DIR_DATASOURCE_GFX, code + '.gif'))

		selectDialog = DialogSelect()
		selectDialog.setup(imageWidth=25, width=200, rows=len(self.COUNTRIES), banner=self.FILE_LOGO, panel=mytvGlobals.DIALOG_PANEL)
		selectedPos,action = selectDialog.ask(self.COUNTRIES, icons=flags)
		if selectedPos > 0:
			self.countryCode = self.COUNTRIES[selectedPos]

		changed = (origCode != self.countryCode)
		debug("< TVRage.selectCountry() changed=%s countryCode=%s" % (changed, self.countryCode))
		return changed

	###################################################################################################################
	def makeShowListItem(self, show):
		try:
			lbl = '[%s] %s' % (show[0], show[1])		# ch, title
			lbl2 = show[2]								# ep
			li = xbmcgui.ListItem(lbl, lbl2)
		except:
			li = None
		return li

	###################################################################################################################
	def menuAddDate(self, menu, date, addFirstTitle=False):
		debug("> TVRage.menuAddDate() date="+date + " addFirstTitle="+str(addFirstTitle))
		if addFirstTitle:
			menu.append(xbmcgui.ListItem(date))

		for time, shows in self.schedule[date]:
			menu.append(xbmcgui.ListItem(time))
			for show in shows:
				menu.append(self.makeShowListItem(show))
		debug("< TVRage.menuAddDate()")

	###################################################################################################################
	def searchShow(self, showName=''):
		debug("> TVRage.searchShow()")

		firstSearch = True
		found = False
		while not found:
			if not firstSearch or not showName:
				showName = doKeyboard(showName, __language__(569))
				if not showName:
					break
			firstSearch = False

			# download search page
			url = self.URL_SEARCH % showName
			dialogProgress.create(__language__(518), __language__(311), showName)
			doc = fetchURL(url)
			dialogProgress.close()

			if doc:
				flags = []
#				regex = "src=['\"](.*?)['\"].+?href=.*?>(.*?)<.+?align='center'>(.*?)<"     # 25/01/08
				regex = "src=['\"](.*?)['\"].+?href=.*?>(.*?)<.+?(<table.*?</table>)"       # 30/04/08
				matches = parseDocList(doc, regex, '<b>Found ','</div')
				if matches:
					menu = [xbmcgui.ListItem(__language__(500),'')]
					flags = ['']
					found = True
					for match in matches:
						imgFN = os.path.join(DIR_DATASOURCE_GFX, os.path.basename(match[0]))
						flags.append(imgFN)
						title = cleanHTML(decodeEntities(match[1]))
						year = cleanHTML(decodeEntities(match[2]))
						menu.append(xbmcgui.ListItem(title, year))

					showSelectPos = 0
					while menu:
						selectDialog = DialogSelect()
						selectDialog.setup(width=475, rows=len(menu), imageWidth=25, banner=self.FILE_LOGO, panel=mytvGlobals.DIALOG_PANEL)
						showSelectPos,action = selectDialog.ask(menu, showSelectPos, icons=flags)
						if showSelectPos <= 0:				# exit selected
							break
						showName = menu[showSelectPos].getLabel()
						self.getShowInfo(showName)
				else:
					messageOK(__language__(518), __language__(117), showName)

		debug("< TVRage.searchShow()")

	###################################################################################################################
	def getShowInfo(self, showName):
		debug("> TVRage.getShowInfo()")
		showInfo = {}
		imgFN = ''
		summary = ''

		debug("download QuickInfo. contains show url, next ep etc")
		dialogProgress.create(__language__(518), __language__(207), showName)
		doc = fetchURL(self.URL_QUICK_INFO % showName)
		if doc and doc != -1:
			reALL = re.compile(r'(.*?)@(.*)')
			for line in doc.split('\n'):
				match = reALL.match(line)
				if match:
					showInfo[match.group(1)] = match.group(2).replace('^',',')

		try:
			showURL = showInfo[self.KEY_SHOW_URL]
		except:
			messageOK(__language__(518), __language__(118))
		else:
			dialogProgress.update(33, __language__(208))
			doc = fetchURL(showURL)
			if doc:
				debug("scrape Summary & banner url")
				regex = "Summary<.+?<img src=.(http://images.tvrage.net/shows.*?)['\"].+?</table>(.*?)</td"
				matches = re.search(regex, doc, re.IGNORECASE + re.MULTILINE + re.DOTALL)
				if matches:
					imgURL = matches.group(1)	# could be jpg or gif
					imgFN = self.FILE_SHOW_IMAGE % os.path.basename(imgURL)
					summary = cleanHTML(decodeEntities(matches.group(2)).replace('<br>','\n'))
					dialogProgress.update(66, __language__(209))
					fetchURL(imgURL, imgFN, isBinary=True)

		dialogProgress.close()
		if showInfo:
			debug("showInfo= %s" % showInfo)
			tvrageDialog = TVRageShowInfoXML(TVRageShowInfoXML.XML_FN, DIR_HOME, "Default")
			tvrageDialog.ask(showName, showInfo, imgFN, summary)
			del tvrageDialog

		debug("< TVRage.getShowInfo()")

	###################################################################################################################
	# parse the schedule into a dict of dates
	# { date : [
	#			[time, [show, show,...]],
	#			[time, [show, show,...]]
	#			]
	# }
	###################################################################################################################
	def parseSchedule(self, doc):
		debug("> TVRage.parseSchedule()")

		self.schedule = {}			# holds all data
		self.scheduleDates = []		# list maintains dates order
		times = []
		shows = []
		reDAY       = re.compile(r'\[DAY\](.*?)\[/DAY\]')
		reTIME		= re.compile(r'\[TIME\](.*)\[/TIME\]')
		reSHOW		= re.compile(r'\[SHOW\](.*)\^(.*)\^(.*)\^(.*)\[/SHOW\]')

		for line in doc.split('\n'):
			match = reDAY.match(line)
			if match:
				date = match.group(1)
				shows = []
				times = []
				self.schedule[date] = times
				self.scheduleDates.append(date)
				continue

			match = reTIME.match(line)
			if match:
				time = match.group(1)
				shows = []
				times.append([time, shows])
				continue

			match = reSHOW.match(line)
			if match:
				shows.append(match.groups())
				continue

#		if DEBUG:
#			for i in self.schedule.items():
#				print '\n', i

#			print "\n\self.scheduleDates=", self.scheduleDates

		success = (self.schedule != {})
		if not success:
			messageOK(__language__(518), __language__(119))

		debug("< TVRage.parseSchedule() success="+str(success))
		return success


	###################################################################################################################
	def getSchedule(self):
		debug("> TVRage.getSchedule()")
		success = False
		
		dialogProgress.create(__language__(518) )
		if not fileExist(self.FILE_SCHEDULE):
			dialogProgress.update(0, __language__(303), os.path.basename(self.FILE_SCHEDULE))
			doc = fetchURL(self.URL_SCHEDULE % self.countryCode, self.FILE_SCHEDULE)
		else:
			doc = readFile(self.FILE_SCHEDULE)

		if doc:	# no error
			dialogProgress.update(50, __language__(312))
			success = self.parseSchedule(doc)
			dialogProgress.update(100, __language__(304))
			dialogProgress.close()
		else:
			messageOK(__language__(518), __language__(120))
			dialogProgress.close()

		debug("< TVRage.getSchedule() success=%s" % success)
		return success

	###################################################################################################################
	def scheduledWeek(self):
		debug("> TVRage.scheduledWeek()")
		menu = [__language__(500)]

		# exclude first date which is 'yesterday'
		for date in self.scheduleDates[1:]:
			self.menuAddDate(menu, date, True)

		title = __language__(210) % (self.scheduleDates[1], self.scheduleDates[-1])
		self.displayShowMenu(menu, title)

		debug("< TVRage.scheduledWeek()")

	###################################################################################################################
	# dayDelta: 0, Yesterday, 1 Today, 2 Tomorrow ...
	# dayDelta None - show date menu
	###################################################################################################################
	def scheduledDay(self, dayDelta=None):
		debug("> TVRage.scheduledDay() dayDelta="+str(dayDelta))

		if dayDelta == None:
			menu = self.DAYS + self.scheduleDates[3:]	# join [Yes, Tod, Tom] onto rest of week dates
			menu.insert(0, __language__(500))	# exit
			selectDialog = DialogSelect()
			selectDialog.setup(width=300, rows=len(menu), banner=self.FILE_LOGO, panel=mytvGlobals.DIALOG_PANEL)
			dayDelta,action = selectDialog.ask(menu)
			dayDelta -= 1	# allow for exit

		if dayDelta >= 0:
			menu = [ __language__(500)]
			date = self.scheduleDates[dayDelta]
			self.menuAddDate(menu, date)
			title = __language__(211) % date
			self.displayShowMenu(menu, title)

		debug("< TVRage.scheduledDay()")


	###################################################################################################################
	def displayShowMenu(self, menu, title):
		debug("> TVRage.displayShowMenu()")

		selectedPos = 0
		while menu:
			selectDialog = DialogSelect()
			selectDialog.setup(title, width=650, rows=len(menu), banner=self.FILE_LOGO, panel=mytvGlobals.DIALOG_PANEL)
			selectedPos,action = selectDialog.ask(menu, selectedPos)
			if selectedPos <= 0:
				break

			# if selected a Show, download extra info and display
			showName, epName = self.parseShowEpisodeName(menu[selectedPos])
			# at least a showName reqd. 
			if showName:
				self.getShowInfo(showName)

		debug("< TVRage.displayShowMenu()")

	###################################################################################################################
	def parseShowEpisodeName(self, listItem):
		debug("> TVRage.parseShowEpisodeName()")
		lbl1 = listItem.getLabel()
		lbl2 = listItem.getLabel2()

		showName = searchRegEx(lbl1, '^\[.*\] (.*?)$')
		epName = searchRegEx(lbl2, '(\d+x\d+)')
		if epName and len(epName) < 2:
			epName = '0'+epName
		debug("< TVRage.parseShowEpisodeName()")
		return showName, epName

	###################################################################################################################
	def ask(self, progTitle='', countryCode=''):
		debug("> TVRage.ask() countryCode="+countryCode)

		# setup country code
		countryCode = countryCode.upper()
		if not countryCode or countryCode not in self.COUNTRIES:
			self.countryCode = self.DEFAULT_COUNTRY
		else:
			self.countryCode = countryCode

		# create menu according to countryCode & get country schedule
		self.createMainMenu()
		if self.getSchedule():
			selectedPos = 1		# start on Today
			# show this dialog and wait until it's closed
			while self.mainMenu:
				selectDialog = DialogSelect()
				selectDialog.setup(width=300, rows=len(self.mainMenu), banner=self.FILE_LOGO, panel=mytvGlobals.DIALOG_PANEL)
				selectedPos,action = selectDialog.ask(self.mainMenu, selectedPos)
				if selectedPos <= 0:				# exit selected
					break

				selectedItem = self.mainMenu[selectedPos].getLabel()
				if selectedItem == self.MENU_OPT_YESTERDAY:
					self.scheduledDay(dayDelta=0)
				elif selectedItem == self.MENU_OPT_TODAY:
					self.scheduledDay(dayDelta=1)
				elif selectedItem == self.MENU_OPT_TOMORROW:
					self.scheduledDay(dayDelta=2)
				elif selectedItem == self.MENU_OPT_WEEK:
					self.scheduledWeek()
				elif selectedItem == self.MENU_OPT_DAY:
					self.scheduledDay()
				elif selectedItem == self.MENU_OPT_CURR_PROG:
					self.searchShow(progTitle)
				elif selectedItem == self.MENU_OPT_SEARCH:
					self.searchShow()
				elif selectedItem == self.MENU_OPT_COUNTRY:
					if self.selectCountry():			# changed
						deleteFile(self.FILE_SCHEDULE)	# delete old country schedule
						self.createMainMenu()			# rebuild menu
						if not self.getSchedule():		# fetch & parse new schedule
							self.close()

				del selectDialog

			self.deleteCache()
		debug("< TVRage.ask()")

###########################################################################################################
class TVRageShowInfoXML(xbmcgui.WindowXMLDialog):

	# control id's
	CLBL_TITLE = 100
	CIMG_PHOTO = 101
	CTB_DESC = 102
	CLBL_KEY = 110
	CLBL_VALUE = 210
	CLBL_LAST = 126
	XML_FN = "script-mytv-tvrage.xml"

	def __init__( self, *args, **kwargs ):
		debug("TVRageShowInfoXML() init")
		self.isStartup = True

	#################################################################################################################
	def onInit( self ):
		debug("> TVRageShowInfoXML().onInit() isStartup=%s" % self.isStartup)
		if self.isStartup:
			self.getControl(self.CLBL_TITLE).setLabel(self.showName)
			self.getControl(self.CTB_DESC).setText(self.summary)
			if self.imgFN:
				self.getControl(self.CIMG_PHOTO).setImage(self.imgFN)

			self.setInfoLabels()

			self.isStartup = False

		debug("< TVRageShowInfoXML().onInit()")


	def setInfoLabels(self):
		debug("> TVRageShowInfoXML().setInfoLabels()")

		ctrlKey = self.CLBL_KEY
		ctrlValue = self.CLBL_VALUE
		for key, value in self.showInfo.items():
			self.getControl(ctrlKey).setLabel(key+':')
			self.getControl(ctrlValue).setLabel(value)
			ctrlKey += 1
			ctrlValue += 1
			if ctrlKey > self.CLBL_LAST:
				break

		while ctrlKey <= self.CLBL_LAST:
			self.getControl(ctrlKey).setVisible(False)
			self.getControl(ctrlValue).setVisible(False)
			ctrlKey += 1
			ctrlValue += 1

		debug("< TVRageShowInfoXML().setInfoLabels()")

	#################################################################################################################
	def onAction(self, action):
		try:
			actionID = action.getId()
			buttonCode = action.getButtonCode()
		except: return

		if actionID in EXIT_SCRIPT or buttonCode in EXIT_SCRIPT:
			debug("TVRageShowInfoXML() EXIT_SCRIPT")
			self.close()

	#################################################################################################################
	def onClick(self, controlID):
		pass

	###################################################################################################################
	def onFocus(self, controlID):
		pass

	###################################################################################################################
	def ask(self, showName, showInfo, imgFN='', summary=''):
		debug("> TVRageShowInfoXML.ask()")
		self.showName = showName
		self.showInfo = showInfo
		self.imgFN = imgFN
		self.summary = summary
		self.doModal()
		debug("< TVRageShowInfoXML.ask()")

