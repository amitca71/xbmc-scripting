############################################################################################################
# TV Data source: pc_SageTV_Search
#
# Notes
# -----
# This version uses the EPG Search facility inorder to get listing data.
# The returning page contains 5 days worth of data for 1 channel.
# It doesnt have any descriptions or genre.
# It cant be called for a specific date.
# Data is cached and code works out if it needs to get a new file.
#
# 25/07/2007 First attempt.
# 10/03/2008 - Updated for myTV v1.18
############################################################################################################

from mytvLib import *
import mytvGlobals
import xbmc,xbmcgui, re, time, os.path
from string import split

DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL
__language__ = sys.modules["__main__"].__language__

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__()")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.isConfigured = False

	def getName(self):
		return self.name

	def getPreferredSaveProgramme(self):
		return "SageTV"		# base filename of SaveProgramme

	def setup(self):
		debug("ListingData.setup()")
		self.BASE_URL = "http://" + self.USER + ":" + self.PASS + "@" + self.IP + ":" + self.PORT + "/sage/"
		self.channelListURL = self.BASE_URL + "EpgGrid"
		self.channelURL = self.BASE_URL + "Search?SearchString=&searchType=Airings&Video=on&DVD=on&search_fields=title&TimeRange=120&Categories=**Any**&Channels=$CHID&watched=any&dontlike=any&favorite=any&autodelete=any&partials=none&sort1=airdate_asc&sort2=none&pagelen=inf"
		self.DESC_URL = self.BASE_URL + "DetailedInfo?AiringId="

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		if not self.isConfigured:
			return []
		regex = 'value="(\d+)".*?>\d+ - (.*?)<'
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME , \
							regex, startStr='startchan',endStr='</select')


	# download channel data, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("getChannel() dayDelta: " + str(dayDelta) + " chID: " + chID + " fileDate: " + fileDate)
		if not self.isConfigured or dayDelta < 0 or dayDelta > 5:
			return []
		progList = []
		dataFilename = ''

		# check to see if date exists in any previous files that might have been cached in last 5 days
		# loop, subtracting 1 day from filedate for 5 days, until found
		fileDateSecs = time.mktime(time.strptime(fileDate,"%Y%m%d"))
		for cachedDay in range(0, 6):
			lt = time.localtime(fileDateSecs - (cachedDay * 86400))
			cachedFileDate = time.strftime("%Y%m%d", lt)
			cacheFilename = os.path.join(self.cache, "%s_%s.html" % (chID, cachedFileDate))
			if fileExist(cacheFilename):
				dataFilename = cacheFilename
				debug("cachedDay=%s file=%s" % (cachedDay, cacheFilename))
				break

		# if not found a cached file, use today date for filename
		if not dataFilename:
			today = time.strftime("%Y%m%d", time.localtime())
			dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, today))
			debug("no cached file, using todays date: " + dataFilename)

		# download data file if file doesnt exists
		if not fileExist(dataFilename):
			url = self.channelURL.replace('$CHID',chID)
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		# check for timout, exception error, or empty page
		if not doc:
			return doc

		debug("Proces listing data ...")
		doc = doc.decode('utf8','replace')
		# time, id, title, desc
		regex = 'AiringId=(\d+)">(.*?)<.*?(Markerblank|Manual|Favorite).*?datecell">.*?>(.*?)<.*?>(.*?(?:AM|PM)).*?(\d+:\d+ (?:AM|PM))'
		matches = parseDocList(doc, regex, '[Unselect all]','[Select all]')
		if matches:
			# breakdown requested date, fileDate
			fileDateYear = int(fileDate[:4])
			fileDateMon = int(fileDate[4:6])
			fileDateMDay = int(fileDate[-2:])

			foundDate = False
			for match in matches:
				dataStartDateTime = "%s %s %s" % (match[3],str(fileDateYear),match[4])
				fmtDataDate = time.strptime(dataStartDateTime,"%a, %b %d %Y %I:%M %p")
	#			print "fmtDataDate=", fmtDataDate

				# ensure were looking at same year, month date
				if fmtDataDate.tm_year != fileDateYear or fmtDataDate.tm_mon != fileDateMon or fmtDataDate.tm_mday != fileDateMDay:
					if foundDate:
						break				# quit processing loop
					else:
						continue			# loop to next prog

				# get prog start as secs from epoch
				startTimeSecs = time.mktime(fmtDataDate)

				# get prog end times as secs
				endTime = match[5]
				endTimeSecs = startTimeToSecs(startTimeSecs, endTime, fileDate)		# ensures correct secs for AM/PM times
		
				id = match[0]
				title = cleanHTML(decodeEntities(match[1]))
				desc = ''
				genre = match[2]								# manual or favorite recording attribute and puts it in genre

				# check minimum data requirments
				if not id or not startTimeSecs or not endTimeSecs or not title:
					continue

				if DEBUG:
					print title, desc, startTimeSecs, endTimeSecs, id, genre
				progList.append( {
						TVData.PROG_STARTTIME : float(startTimeSecs),
						TVData.PROG_ENDTIME : float(endTimeSecs),
						TVData.PROG_TITLE : title,
						TVData.PROG_ID : id,
						TVData.PROG_GENRE : genre,
						TVData.PROG_DESC : desc,
						TVData.PROG_DESCLINK : id
					} )
				foundDate = True

		return progList


	############################################################################################################
	# Download url and regex parse it to extract description.
	############################################################################################################
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		desc = ''
		try:
			url = self.DESC_URL + link
			doc = fetchURL(url)
			if doc:
				doc = doc.decode('utf8','replace')
				regexList = ['p>(Airing:.*?)<',
							 'p>(Duration:.*?)<',
							 'p>(Channel:.*?)<',
							 'p>(Category:.*?)<',
							 'p>(Show ID:.*?)<',
#							 'p>(Internal details:.*?)<',
							 'p>(Description:.*?)<']
				for regex in regexList:
					value = searchRegEx(doc, regex, flags=re.MULTILINE+re.IGNORECASE+re.DOTALL)
					if value:
						desc += cleanHTML(decodeEntities(value)) + '\n'
		except:
			desc = ''
		return desc


	############################################################################################################
	# load, if not exist ask, then save
	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)

		CONFIG_SECTION = 'DATASOURCE_' + self.name
		# CONFIG KEYS
		KEY_IP = 'ip'
		KEY_PORT = 'port'
		KEY_USER = 'user'
		KEY_PASS = 'pass'

		# config key, title, defaultValue, kbtype
		configData = [
			[KEY_IP,__language__(812), '192.168.0.2', KBTYPE_IP],
			[KEY_PORT,__language__(813), '', KBTYPE_NUMERIC],
			[KEY_USER,__language__(805), 'SageUsername', KBTYPE_ALPHA],
			[KEY_PASS, __language__(806), 'SagePassword', KBTYPE_ALPHA]
			]

		if reset:
			configOptionsMenu(CONFIG_SECTION, self.configData, self.name)

		self.IP = mytvGlobals.config.action(self.CONFIG_SECTION, KEY_IP)
		self.PORT = mytvGlobals.config.action(self.CONFIG_SECTION, KEY_PORT)
		self.USER = mytvGlobals.config.action(self.CONFIG_SECTION, KEY_USER)
		self.PASS = mytvGlobals.config.action(self.CONFIG_SECTION, KEY_PASS)

		if self.IP and self.PORT and self.USER and self.PASS:
			self.setup()
			self.isConfigured = True
		else:
			self.isConfigured = False
		debug("< config() self.isConfigured=%s" % self.isConfigured)
		return self.isConfigured

