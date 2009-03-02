############################################################################################################
# TV Data source: WebScheduler
# Notes:
# Data XML data files served from a  PC running WebScheduler.
#
# Many thanks to ozNick for invaluable assistance in writting this.
# CHANGELOG:
# 11/09/07 - Replaced fetchFancyURL() with fetchCookieURL() (which itself now uses urllib.FancyURLopener())
# 01/05/08 - Accomodate WS Pro XML format
# 01/10/08 - rewritten to not use proper XML parsing as its too memory hungry
#
############################################################################################################

from mytvLib import *
import mytvGlobals

import xbmcgui, xbmc, re, time, datetime
from string import split, replace, find, rfind, atoi, zfill
from os import path

__language__ = sys.modules["__main__"].__language__

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.EPG_FILENAME = os.path.join(cache, 'WS_$DATE.xml')
		self.lastFileDate = ""
		self.isConfigured = False

	def getName(self):
		return self.name

	def getPreferredSaveProgramme(self):
		return "WebScheduler"		# base filename of SaveProgramme

	def setup(self):
		debug("ListingData.setup()")
		self.BASE_URL = 'http://%s:%s/' % (self.IP, self.PORT)
		self.channelURL = self.BASE_URL + 'servlet/KBEpgDataRes?action=01&year=$YEAR&month=$MONTH&day=$DAY&start=0&span=24&xml=1'

	# expects YYYYMMDD
	def makeURL(self, date=''):
		if not date:
			fmtDate = time.localtime()
		else:
			fmtDate = time.strptime(date,"%Y%m%d")

		year = time.strftime("%Y", fmtDate)
		month = time.strftime("%m", fmtDate)
		day = time.strftime("%d", fmtDate)
		url = self.channelURL.replace('$YEAR',year).replace('$MONTH',month).replace('$DAY',day)
		debug("ListingData.makeURL() %s" % url)
		return url

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		if not self.isConfigured:
			return []
		url = self.makeURL()
		regex = '<channel ID="(.*?)".*?display-name>(.*?)<'
		return getChannelsLIB(url, self.CHANNELS_FILENAME , regex, sorted=False)

	# download channel data, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	#
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("> ListingData.getChannel() dayDelta: %s chID=%s fileDate=%s" % (dayDelta,chID,fileDate))
		if not self.isConfigured:
			return []

		# download data file if file doesnt exists
		progList = None
		dataFilename = self.EPG_FILENAME.replace('$DATE',fileDate)
		if not fileExist(dataFilename):
			url = self.makeURL(fileDate)
			data = fetchCookieURL(url, dataFilename)
		else:
			data = readFile(dataFilename)
		if data:
			progList = self.parseData(data, chID, fileDate)

		debug("< ListingData.getChannel()")
		return progList


	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		return ''

	##############################################################################################
	def parseData(self, data, chID, fileDate):
		debug("> ListingData.parseData() chID=%s fileDate=%s" % (chID, fileDate))

		RE_PROG = "(<programme channel=\"%s\".*?</programme>)" % chID
		RE_PROG_TIMES = '<programme channel.*?start="(.*?)".*?stop="(.*?)"'
		RE_PROG_FULL_TIMES = '<full_times.*?start="(.*?)".*?stop="(.*?)"'
		RE_PROG_TITLE = '<title>(.*?)</'
		RE_PROG_SUBTITLE = '<sub-title>(.*?)</'
		RE_PROG_CATEGORY = '<category>(.*?)</'
		RE_PROG_ADD = '<progAdd>(.*?)</'
		RE_PROG_DESC = '<desc>(.*?)</'

		DATE_TIME_SZ = 12
		DATE_SZ = 8
		reFLAGS = re.IGNORECASE + re.MULTILINE + re.DOTALL
		isPROXML = False
		progList = []
		progCount = 0

		progs = findAllRegEx(data, RE_PROG)
		for prog in progs:
			try:
				# prog times
				try:
					if not isPROXML:
						matches = findAllRegEx(prog, RE_PROG_TIMES)
						start = matches[0][0]
						stop = matches[0][1]
						isPROXML = (start[-2:] in ('AM','PM'))

					if isPROXML:
						# is PRO XML, get times from full_times
						matches = findAllRegEx(prog, RE_PROG_FULL_TIMES)
						start = matches[0][0]
						stop = matches[0][1]

					# check if for required date
					if start[:DATE_SZ] != fileDate:
						continue
				except:
					debug("bad prog %s" % prog)
					continue

				progList.append( {
						TVData.PROG_STARTTIME : time.mktime(time.strptime(start[:DATE_TIME_SZ],"%Y%m%d%H%M")),	# 24hr
						TVData.PROG_ENDTIME : time.mktime(time.strptime(stop[:DATE_TIME_SZ],"%Y%m%d%H%M")),
						TVData.PROG_TITLE : cleanHTML(decodeEntities(searchRegEx(prog, RE_PROG_TITLE, reFLAGS))),
						TVData.PROG_SUBTITLE : cleanHTML(decodeEntities(searchRegEx(prog, RE_PROG_SUBTITLE, reFLAGS))),
						TVData.PROG_GENRE : searchRegEx(prog, RE_PROG_CATEGORY, reFLAGS),
						TVData.PROG_DESC : cleanHTML(decodeEntities(searchRegEx(prog, RE_PROG_DESC, reFLAGS)), breaksToNewline=True),
						TVData.PROG_SCHEDLINK : decodeEntities(searchRegEx(prog, RE_PROG_ADD, reFLAGS))
					} )

				progCount += 1
			except:
				handleException("parseData bad prog")

		debug("< ListingData.parseData() progCount=%i" % progCount)
		return progList

	############################################################################################################
	# load, if not exist ask, then save
	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config()")

		CONFIG_SECTION = 'DATASOURCE_' + self.getName()
		CONFIG_OPT_IP = 'PC_IP'
		CONFIG_OPT_PORT = 'PC_PORT'

		self.IP = mytvGlobals.config.action(CONFIG_SECTION, CONFIG_OPT_IP)
		self.PORT = mytvGlobals.config.action(CONFIG_SECTION, CONFIG_OPT_PORT)

		origIP = self.IP
		origPORT = self.PORT
		if reset:
			self.IP = ''
			self.PORT = ''

		# IP
		if not self.IP:
			debug("get IP")
			self.IP = doKeyboard(origIP, __language__(812), KBTYPE_IP)
			if self.IP and self.IP != origIP:
				mytvGlobals.config.action(CONFIG_SECTION, CONFIG_OPT_IP, self.IP, mode=ConfigHelper.MODE_WRITE)

		# PORT
		if not self.PORT:
			debug("get PORT")
			self.PORT = doKeyboard(origPORT, __language__(813), KBTYPE_NUMERIC)
			if self.PORT and self.PORT != origPORT:
				mytvGlobals.config.action(CONFIG_SECTION, CONFIG_OPT_PORT, self.PORT, mode=ConfigHelper.MODE_WRITE)

		if self.IP and self.PORT:
			self.setup()
			self.isConfigured = True
		else:
			self.isConfigured = False
		debug("< ListingData.config() isConfigured=%s" % self.isConfigured)
		return self.isConfigured
		
