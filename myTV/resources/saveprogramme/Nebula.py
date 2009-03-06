############################################################################################################
#
# Save Programme - Custom script called from myTV 'Save Programme' menu option.
#
# Custom written to send programme information as a url to a Nebula TV card.
# Thanks to jj5768 for help with testing.
#
# NOTES:
# The class must be called 'SaveProgramme' that accepts Channel and Programme classes.
# Must have a run() function that returns success as True or False.
#
# Example of formated URL sent to Nebula HTTP server for a programme to be saved:
#
# http://<your ip>:2880/timers.htm?Name=scrubs;?Timer=004200022070500300
#
# Timer param  down this is:
# 004		= LCN
# 2000 		= start HHMM
# 220705	= start DDMMYY
# 0030		= duration mins
# 0			= record once
# ChangeLog:
# 1/8/05	- Added more LCN codes.
# 22/12/05	- Added manage() - queries digitv server for timers/recording. allows deletion.
#			- Changed order of prompts and details of prog date/time displayed.
#			- Thanks to jj5768 for help with testing.
# 03/05/06	- Amended to allow for RECORDINGS html difference on new Nebula v3.5
#			- Better HTTP checking.
#			- Updated LCN codes.
#			- Now configurable via GUI.
#			- myTV can fetch timers at startup to keep local cache uptodate.
#			- LCN lookup now done using ch name as key not ch id.
# 28/07/06	- Updated: Corrected some LCN codes & removed Repeat Recording option.
# 18/08/06	- Updated Film4
#			- Uses new Config
# 17/11/06	- Updated to cope with recurring dates for timerlist programmes.
# 07/09/07	- Updated to use fetchURL() not its own nebulaFetchURL()
############################################################################################################

import xbmc, urllib, time, datetime
from mytvLib import *
from bbbGUILib import *
import mytvGlobals
from string import zfill, find, upper

__language__ = sys.modules["__main__"].__language__

# NOTE: ALL NEBULA SERVER SETTINGS NOW SET VIA myTV AT FIRST RUN & CONFIG MENU

# channel name : LCN code
# The lookup done using channel name - these names are consistent with RadioTimes names.
# If you want additional matches , or different channel names, add entra lines.
# Codes last updated 3/5/06 from http://en.wikipedia.org/wiki/List_of_UK_Digital_Terrestrial_television_channels
LCN_CODES = {
# TV
'BBC ONE':'001',
'BBC1':'001',
'BBC 1':'001',
'BBC TWO':'002',
'BBC2':'002',
'BBC 2':'002',
'ITV1':'003',
'ITV 1':'003',
'ITV1 YORKSHIRE':'003',
'CHANNEL 4':'004',
'FIVE':'005',
'ITV2':'006',
'ITV 2':'006',
'BBC THREE':'007',
'BBC3':'007',
'BBC 3':'007',
'BBC FOUR':'009',
'BBC4':'009',
'BBC 4':'009',
'ITV3':'010',
'ITV 3':'010',
'SKY THREE':'011',
'Sky3':'011',
'Sky 3':'011',
'UKTV HISTORY':'012',
'MORE4':'013',
'MORE 4':'013',
'E4':'014',
'FILM4':'029',
'FILM 4':'029',
'FILMFOUR':'029',
'ABC1':'015',
'QVC':'016',
'UKTV GOLD':'017',
'THE HITS':'018',
'UKTV BRIGHT IDEAS':'019',
"UKTV BR'TIDEAS":'019',
'FTN':'020',
'F TN':'020',
'TMF':'021',
'TMF: THE MUSIC FACTORY':'021',
'IDEAL WORLD':'022',
'BIDUP TV':'023',
'BID TV':'023',
'PRICE DROP':'024',
'PRICE-DROP TV':'024',
'TMC':'025',
'UKTV STYLE':'026',
'DISCOVERY':'027',
'DISCOVERY REAL TIME':'027',
'DISCOVERYRTIME':'027',
'ITV4':'028',
'ITV 4':'028',
'E4 +1':'030',
'E4+1':'030',
'BRITISH MOTOSPORT':'033',
'SETENTA SPORTS':'034',
'SETENTA SPORTS 1':'034',
'SETENTA SPORTS 2':'034',
'FIVE US':'035',
'FIVE LIFE':'036',
'SMILETV':'037',
'BBC NEWS 24':'080',
'SKY NEWS':'082',
'SKY SPORTS NEWS':'083',
'BBC PARLEMENT':'081',
'CBBC CHANNEL':'070',
'CBEEBIES':'071',
'CARTOON NETWORK':'072',
'CARTOON NWK':'072',
'BOOMBERANG':'073',
'TOONAMI':'074',
'CITV CHANNEL':'075',
'S4C2':'086',
'TELEVISION X':'097',
'RED HOT TV':'098',
# Radio 
'BBC RADIO 1':'700',
'1Xtra BBC':'701',
'BBC RADIO 2':'702',
'BBC RADIO 3':'703',
'BBC RADIO 4':'704',
'BBC R5 Live':'705',
'BBC 5L Sports X':'706',
'BBC 5L SportsX':'706',
'BBC 6 music':'707',
'BBC 7':'708'
}

# this table is used to translate Nebula Channel Names back to a CH ID.
# If this SaveProgramme module cannot translate Nebula Channel Name back into
# a CH ID using your selected DataSource, then its because that Channel Name
# doesnt exist 'as that name' in the DataSource.
# This list is for those names.  Add into it as needed.
CHID_CODES = {
'BBC ONE':'92',
'BBC TWO':'105',
'ITV1 YORKSHIRE':'32',
'ITV1 ANGLIA':'24',
'ITV1 BORDER':'25',
'ITV1 LONDON':'26',
'ITV1 CARLTON CENTRAL':'27',
'ITV1 GRANADA':'29',
'ITV1 MERIDIAN':'30',
'ITV1 TYNE TEES':'31',
'ITV1 CARLTON WEST COUNTRY':'33',
'ITV1 WALES':'35',
'ITV1 WEST':'36',
'MORE 4':'1959'
}

class SaveProgramme:
	def __init__(self, cachePath=""):
		debug("> SaveProgramme().__init__")

		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.channelList = []
		self.configSaveProgramme = ConfigSaveProgramme()

		debug("< SaveProgramme().__init__")

	def getName(self):
		return self.name

	def saveMethod(self):
		return SAVE_METHOD_CUSTOM

	def isConfigured(self):
		return self.configSaveProgramme.checkValues()

	############################################################################################################
	def config(self, reset=True):
		debug("> config() reset=%s" % reset)
		try:
			if reset:
				success = self.configSaveProgramme.reset()
			success = self.isConfigured()
			if success:
				isServerVersionPre35 = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_VERSION)
				serverIP = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_IP)
				serverPort = self.configSaveProgramme.getValue(self.configSaveProgramme.KEY_PORT)
				self.BASE_URL = "http://%s:%s/" % (serverIP,serverPort)

				# Timers
				self.URL_TIMER_SET = self.BASE_URL + "timers.htm?Name=$TITLE;?Timer=$TIMER"
				self.URL_TIMER_LIST = self.BASE_URL + "timerlist.htm"
				self.URL_TIMERS_DEL = self.BASE_URL + "timers.htm?Delete=$ID"

				# Recordings
				self.URL_TVRECS = self.BASE_URL + "tvrecs.htm"
				self.URL_TVRECS_DEL = self.URL_TVRECS + "?DelFile=$ID"
				if isServerVersionPre35:
					self.TVRECS_REGEX = "left['\"]>(.*?)</td(?:.*?)left['\"]>(.*?)</td(?:.*?)left['\"]>(.*?)</td"
				else:
					self.TVRECS_REGEX = "left['\"]>(?:.*?)['\"]>(.*?)\.(?:.*?)left['\"]>(.*?)</td(?:.*?)left['\"]>(.*?)</td"
		except:
			handleException()

		debug("< config() success=%s" % success)
		return success

	def run(self, channelInfo, programme, confirmRequired=True):
		debug("> SaveProgramme.run()")
		success = False

		# get programme information
		chName = channelInfo[TVChannels.CHAN_NAME]
		title = programme[TVData.PROG_TITLE]

		# convert to LCN
		lcn = self.lookupLCN(chName)
		if lcn:
			startTimeSecs = programme[TVData.PROG_STARTTIME]
			endTimeSecs = programme[TVData.PROG_ENDTIME]
			progDate = time.strftime('%d%m%y', time.localtime(startTimeSecs))
			progDateLong = time.strftime('%a %d/%m/%y %H:%M %p', time.localtime(startTimeSecs))
			progTime = time.strftime('%H%M', time.localtime(startTimeSecs))
			progEndTimeLong = time.strftime('%H:%M %p', time.localtime(endTimeSecs))
			durMins = str(int((endTimeSecs - startTimeSecs) /60))
			durMins = zfill(durMins,4)	# pad to required length

			timer = lcn + progTime + progDate + durMins + '0' # 0 == no repeat recording
			url = self.URL_TIMER_SET.replace('$TITLE',title.replace(' ','')).replace('$TIMER',timer)
			result = fetchURL(url)
			if result:
				success = self.checkServerResult(result)
		debug("< SaveProgramme.run() success=%s" % success)
		return success


	############################################################################################################
	# List / Delete timers/recordings
	############################################################################################################
	def manage(self):
		debug("> SaveProgramme().manage()")
		msgTitle = "%s: %s" % (__language__(511), self.name)

		# INITIAL MENU
		OPT_TIMERS = __language__(825)
		OPT_RECS = __language__(826)
		menuList = [__language__(500), OPT_TIMERS, OPT_RECS]

		deleted = False
		selectedPos = 0
		while True:
			# popup dialog to select choice
			selectDialog = DialogSelect()
			selectDialog.setup(title, width=680, rows=len(menuList), panel=mytvGlobals.DIALOG_PANEL)
			selectedPos,action = selectDialog.ask(menuList, selectedPos)
			if selectedPos <= 0:
				break

			itemList = []
			if selectedPos == 1:
				timers = self.getTimers()
				if timers != None:
					# make itemList from timers
					for startTimeSecs, chID, durSecs, chName, progName in timers:
						startDate = time.strftime("%d/%m/%Y %H:%M",time.localtime(startTimeSecs))
						durMins = int(durSecs / 60)
						label1 = "%s, %s" % (progName,chName)
						label2 = "%s, %smins" % (startDate,durMins)
						itemList.append( (label1, label2) )
					title = "%s %s" % (OPT_TIMERS, __language__(586))
					self.menuItems(itemList, self.URL_TIMERS_DEL, title)
			elif selectedPos == 2:
				itemList = self.getRecordings()
				if itemList != None:			# [] = empty, None = error
					title = "%s %s" % (OPT_RECS, __language__(586))
					self.menuItems(itemList, self.URL_TVRECS_DEL, title)

		timers = self.getTimers()
		debug("< SaveProgramme().manage()")
		return timers

	############################################################################################################
	# Timers = True, recording s= False
	############################################################################################################
	def getTimers(self):
		debug("> SaveProgramme().getTimers()")
		success = False
		timersList = None
		dialogProgress.create(self.name, __language__(824))
		result = fetchURL(self.URL_TIMER_LIST)
		dialogProgress.close()
		if result:
			success = self.checkServerResult(result)

		if success:
			timersList = []
			currentTimeSecs = time.mktime(time.localtime())
			# extract timers from list.
			regex = "OnTimer(?:.*?)['\"]>(.*?)<(?:.*?)left['\"]>(.*?)</td(?:.*?)left['\"]>(.*?)</td(?:.*?)left['\"]>(.*?)</td(?:.*?)left['\"]>(.*?)</td"
			matches = parseDocList(result, regex, '<table')
			# found, extract details
			for match in matches:
				progName = decodeEntities(match[0]).strip()
				chName = decodeEntities(match[1]).strip()
				date = self.nextFromRecurring(decodeEntities(match[2]).strip())
				startTime = decodeEntities(match[3]).strip()
				stopTime = decodeEntities(match[4]).strip()
#				print progName, chName, date, startTime, stopTime
				# detect bad channel name that we'll never be able to translate
				if chName == 'Auto-Tuning':
					debug("ignoring 'Auto-Tuning' channel name")
					continue

				chID = self.lookupCHID(chName)	# chname to CHID
				if not chID:
					chID = self.lookupCHIDNebula(chName)	# try to find using extra table
				if not chID:
					continue

				# get start time in secs
				dateTime = date + " " + startTime
				startTimeSecs = time.mktime(time.strptime(dateTime,"%d-%m-%Y %H:%M"))

				# get stop time in secs
				dateTime = date + " " + stopTime
				endTimeSecs = time.mktime(time.strptime(dateTime,"%d-%m-%Y %H:%M"))

				# ensure prog ends after start
				if endTimeSecs < startTimeSecs:
					endTimeSecs += 86400		# 24hrs
				if endTimeSecs > currentTimeSecs:
					durSecs = int(endTimeSecs - startTimeSecs)
					timersList.append([startTimeSecs, chID, durSecs, chName, progName])

		debug("< SaveProgramme().getTimers()")
		return timersList


	############################################################################################################
	# Timers = True, recording s= False
	############################################################################################################
	def getRecordings(self):
		debug("> SaveProgramme().getRecordings()")
		itemList = None
		success = False
		dialogProgress.create(self.name, __language__(827))
		result = fetchURL(self.URL_TVRECS)
		dialogProgress.close()
		if result:
			success = self.checkServerResult(result)

		if success:
			itemList = []
			# extract timers from list.
			matches = parseDocList(result, self.TVRECS_REGEX, 'TV Recordings')
			# found, extract details
			for match in matches:
				try:
					title = decodeEntities(match[0]).strip()
					chName = decodeEntities(match[1]).strip()
					durSecs = decodeEntities(match[2]).strip()
					label1 = "%s, %s" % (title, chName)
					itemList.append( (label1, durSecs) )
				except:
					debug("missing data, not added to recordings list")

			debug("Count of recordings found=%s" % len(itemList))

		debug("< SaveProgramme().getRecordings()")
		return itemList  # None is error, [] is empty,


	############################################################################################################
	# method that can be called from myTV directly to fetch remote Timers files.
	############################################################################################################
	def getRemoteTimers(self):
		debug("> SaveProgramme().getRemoteTimers()")

		timers = self.getTimers()

		debug("< SaveProgramme().getRemoteTimers()")
		return timers

	############################################################################################################
	# show list of item, select row to send delete cmd
	############################################################################################################
	def menuItems(self, itemList, url, title):
		debug("> SaveProgramme().menuItems()")

		# create menu
		menuList = [xbmcgui.ListItem(__language__(500))]
		for item in itemList:
			menuList.append(xbmcgui.ListItem(item[0],label2=item[1]))

		while True:
			# popup dialog to select choice
			selectDialog = DialogSelect()
			selectDialog.setup(title, width=680, rows=len(menuList))
			selectedPos,action = selectDialog.ask(menuList)
			if selectedPos <= 0:
				break

			# get list label1 & label2 to make dialog text
			text = "%s %s" % (itemList[selectedPos][0], itemList[selectedPos][1])
			if xbmcgui.Dialog().yesno(__language__(823),text):		# delete?
				deleteURL = url.replace('$ID', str(selectedPos+1))	# starts at 1
				result = fetchURL(deleteURL)
				if result:
					success = self.checkServerResult(result)
					if success:
						del menuList[selectedPos]

		debug("< SaveProgramme().menuItems()")

	def setChannelList(self, channelList):
		self.channelList = channelList

	# Lookup tv card LCN number based on channel name
	def lookupLCN(self, chName):
		debug("> lookupLCN() chName: " + chName)
		try:
			lcn = LCN_CODES[chName.upper()]
		except:
			lcn = ''
		debug("< lookupLCN() LCN code: " + lcn)
		return lcn

	# find CHID from CHannel Name
	# search in supplied datasource channellist [chID, name, other]
	def lookupCHID(self, chName):
		debug("> lookupCHID() chName: " + chName)
		# search each channel by name
		chID = ''
		searchChName = chName.upper()
		for ch in self.channelList:
			if ch[1].upper() == searchChName:
				chID = ch[0]
				break
		debug("< lookupCHID() chID: " + chID)
		return chID

	# Lookup CHID from extra channel names dict
	def lookupCHIDNebula(self, chName):
		debug("> lookupCHIDNebula() chName: " + chName)
		try:
			chID = CHID_CODES[chName.upper()]
		except:
			chID = ''
		debug("< lookupCHIDNebula() chID: " + chID)
		return chID


	#################################################################################################################
	# Original idea/code by James Rendell, modified by BBB.
	# Function to convert a recurring timer from the Nebula web interface to the date
	# of the next occurrence. Used in Nebula.py getTimers function.
	#################################################################################################################
	def nextFromRecurring(self, date):
		"Returns the next instance of a recurring timer, or returns the date parameter \
		itself if it is not amongst the list of days as used in recurring timer specifications"

		DAYS = ["Mondays", "Tuesdays","Wednesdays","Thursdays","Fridays","Saturdays","Sundays"]

		# discover if its a recurring date
		try:
			dayDelta = DAYS.index(date)		# day will be found
		except:
			return date						# not a recurring date

		# PROCESS RECURRING DATE
		# Get today's date and day number
		today=datetime.date.today()
		weekday=today.weekday()

		# Calculate the difference from the next occurrence and weekday
		if dayDelta > weekday:
			today = today + datetime.timedelta(dayDelta-weekday)
		elif weekday > dayDelta:
			today = today + datetime.timedelta(dayDelta+(7-weekday))

		return today.strftime("%d-%m-%Y")


############################################################################################################
	def checkServerResult(self, result):
		success = False
		# check on returning html for errors
		if result in (None, "", -1):
			messageOK("Web Server Error.","No result returned from server.")
		elif result.find("doesn't exist") > 0:
			messageOK("Web Server Error.","Requested web page doesn't exist on server.")
		elif result.find("oneuser") > 0:
			messageOK("Web Server Error.","Authorisation Failure - Web interface tied to other IP.")
		elif result.find("not authorised to access") > 0:
			messageOK("Web Server Error.","Authorisation Failure - Access denied to DigiTV server.","Check Nebula HTTP server security settings.")
		elif result.find("timer clashes") > 0:
			messageOK("Web Server Error.","Authorisation Failure - Clashes with existing timer.")
		else:
			success = True
		debug("checkServerResult() success=" + str(success))
		return success

############################################################################################################
# load, if not exist ask, then save
############################################################################################################
class ConfigSaveProgramme:
	def __init__(self, reset=False):
		debug("> ConfigSaveProgramme().init() reset=%s" % reset)
		self.CONFIG_SECTION = 'SAVEPROGRAMME_NEBULA'

		# CONFIG KEYS
		self.KEY_VERSION = 'nebula_version_pre35'
		self.KEY_IP = 'nebula_ip'
		self.KEY_PORT = 'nebula_port'

		self.configData = [
			[self.KEY_VERSION,"Pre v3.5?",__language__(350),KBTYPE_YESNO],
			[self.KEY_IP,__language__(812),'192.168.0.1',KBTYPE_IP],
			[self.KEY_PORT, __language__(813), '2880', KBTYPE_NUMERIC]
			]

		debug("< ConfigSaveProgramme().init()")

	def reset(self):
		debug("ConfigSaveProgramme().reset()")
		configOptionsMenu(self.CONFIG_SECTION, self.configData, __language__(534),400)

	# check we have all required config options
	def checkValues(self):
		debug("> ConfigSaveProgramme.checkValues()")

		success = True
		# check mandatory keys have values
		for rec in self.configData:
			key = rec[0]
			value = self.getValue(key)
			if value in (None, "","0"):
				debug("missing value for mandatory key=%s" % key)
				success = False

		debug("< ConfigSaveProgramme.checkValues() success=%s" % success)
		return success

	def getValue(self, key):
		return mytvGlobals.config.action(self.CONFIG_SECTION, key)
