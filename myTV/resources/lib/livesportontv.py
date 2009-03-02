"""
  Show live sport on tv  powered by www.livesportontv.com
"""  

import xbmc, xbmcgui
import sys, os.path
from bbbLib import *
from bbbGUILib import DialogSelect

__language__ = sys.modules[ "__main__" ].__language__
DIR_GFX = sys.modules[ "__main__" ].DIR_GFX     			# should be in default.py
DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL

class LiveSportOnTV:

	URL_BASE = 'http://www.livesportontv.com/'

	def __init__(self):
		debug("LiveSportOnTV() init()")

		self.URL_RSS = self.URL_BASE + 'rss.php?p=sportfull&id='
		self.URL_RSS_NOID = self.URL_BASE + 'rss.php?p='
		self.ICON_FN = os.path.join(DIR_GFX, "lsotv_%s.gif")
		self.ICON_URL = self.URL_BASE + "_images/%s.gif"

		self.MAIN_MENU_DATA = {
			'All Sports' : 'index', 
			'HDTV' : 'hdfull',
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
			'Mixed Martial Arts' : 23,
			'Bowls' : 27,
			'Wrestling' : 28,
			'Gymnastics' : 29,
			'Water Sports' : 30,
			'Weight Lifting' : 31,
			'Vollyball' : 32,
			'Pool' : 33,
			'Squash' : 38
			}

	###################################################################################################################
	def onAction(self, action):
		try:
			actionID = action.getId()
			buttonID = action.getButtonCode()
		except: return
		if actionID in CANCEL_DIALOG + EXIT_SCRIPT or buttonID in CANCEL_DIALOG + EXIT_SCRIPT:
			self.close()

	###################################################################################################################
	def onControl(self, control):
		pass

	###################################################################################################################
	def downloadIcons(self):
		debug("> downloadIcons()")

		isDialogShowing = False
		MAX_COUNT = len(self.MAIN_MENU_DATA.values())
		for count, value in enumerate(self.MAIN_MENU_DATA.values()):
			fn = "lsotv_%s.gif" % value
			if value == "hdfull":
				value = "hdready"
			elif value == "index":
				value = "home"

			filePath = os.path.join(DIR_GFX, fn)
			if not os.path.isfile(filePath):
				if not isDialogShowing:
					dialogProgress.create(__language__(519))
					isDialogShowing = True
					
				percent = int( (count * 100.0) / MAX_COUNT )
				dialogProgress.update(percent, __language__(209), fn)
				if fetchURL(self.ICON_URL % value, filePath, isBinary=True) == None:
					break

		if isDialogShowing:
			dialogProgress.close()
		debug("< downloadIcons()")

	###################################################################################################################
	def parseRSS(self, html, ID):
		debug("> LiveSportOnTV.parseRSS() ID=%s" % ID)

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
					iconFN = self.ICON_FN % ID
					menuIcons.append(iconFN)

		debug("< LiveSportOnTV.parseRSS()")
		return menu, menuIcons

	###################################################################################################################
	def getSportData(self, html, ID):
		debug("> LiveSportOnTV.getSportData() ID=%s" % ID)

		menu = []
		menuIcons = []

		iconFN = self.ICON_FN % ID
		regex = '(?:tm\d*|dt)">(.*?)<.*?fx\d*">(.*?)<.*?tt\d*">(.*?)<.*?ch\d*">(.*?)</td' # w/o icon
#		regex = '_images/(\d+).*?(?:tm\d*|dt)">(.*?)<.*?fx\d*">(.*?)<.*?tt\d*">(.*?)<.*?ch\d*">(.*?)</td' # w/icon
		matches = parseDocList(html, regex, 'class="theader"','id="footer"' )
		for match in matches:
			date = cleanHTML(decodeEntities(match[0]))
			fixture = cleanHTML(decodeEntities(match[1]))
			tourn = cleanHTML(decodeEntities(match[2]))
			channel = cleanHTML(decodeEntities(match[3]))
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
			url = self.URL_RSS + str(ID)	# 
		else:
			url = self.URL_RSS_NOID + ID

		listTitle = __language__(519)
		menu = []
		menuIcons = []
		dialogProgress.create(__language__(519), __language__(303), title)
		html = fetchURL(url)
		dialogProgress.close()
		if html:
			menu, menuIcons = self.parseRSS(html, ID)
			if menu:
				menu.insert(0, xbmcgui.ListItem(__language__(500), ''))	# exit
				menuIcons.insert(0,'')									# exit icon
				selectDialog = DialogSelect()
				selectDialog.setup(listTitle, imageWidth=25,width=720, rows=len(menu), itemHeight=24, font=FONT10, panel=DIALOG_PANEL)
				selectedPos,action = selectDialog.ask(menu, icons=menuIcons)
		debug("< LiveSportOnTV.displaySport")

	###################################################################################################################
	def ask(self):
		debug("> LiveSportOnTV.ask()")

		self.downloadIcons()

		# make menu
		menu = self.MAIN_MENU_DATA.keys()
		menu.sort()
		menuIcons = []
		for value in self.MAIN_MENU_DATA.values():
			menuIcons.append(self.ICON_FN % value)

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

