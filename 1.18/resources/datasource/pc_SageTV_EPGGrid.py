############################################################################################################
# TV Data source: pc_SageTV_EPGGrid
#
# Notes
# -----
# This version uses the EpgGrid url to get listing data.
# The returning page contains 1 days worth of data for 1 channel, starting from 00:00 AM
# It has short descriptions, no genre.
# It can be called for a specific date.
#
# 25/07/2007 - First attempt
# 07/09/2007 - Second attempt
# 10/03/2008 - Updated for myTV v1.18
############################################################################################################

from mytvLib import *
import xbmc,xbmcgui, re, time, os.path

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
		self.channelURL = self.BASE_URL + "EpgGrid"
		self.DESC_URL = self.BASE_URL + "DetailedInfo?AiringId="

		
	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		if not self.isConfigured:
			return []
		regex = 'value="(\d+)".*?>\d+ - (.*?)<'
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME , \
							regex, startStr='startchan',endStr='</select>')


	# download channel data, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("ListingData.getChannel() dayDelta: %s chID=%s fileDate=%s" % (dayDelta,chID,fileDate))
		if not self.isConfigured or dayDelta < 0 or dayDelta > 5:
			return []
		progList = []

		# download data file if file doesnt exists
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, fileDate))
		if not fileExist(dataFilename):
			urlDate = "%s/%s/%s" % (fileDate[:4], fileDate[4:6], fileDate[-2:])
			url = self.channelURL.replace('$CHID',chID).replace('$DATE',urlDate)

			# fetch file using cookies
			txData = "&startchan=%s&startdate=%s&starthr=0" % (chID,urlDate)
			txHeaders =  {'Cookie' : 'grid_num_hours=24; grid_num_chans=1; UseChannelLogos=false; grid_show_desc=true'}
			doc = fetchURL(url, dataFilename, txData, txHeaders)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		doc = doc.decode('utf8','replace')
		# title, desc, start, end, id
		regex = 'title="(.*?)$(.*?)(\d+:\d+ .M).*?-.*?(\d+:\d+ .M).*?AiringId=(\d+)'
		matches = parseDocList(doc, regex, 'epgcell','[Show Options]')
		if matches:
			fileDateMidnightSecs = time.mktime(time.strptime(fileDate+'0000',"%Y%m%d%H%M"))
			afterMidnight = False
			for match in matches:
				title = cleanHTML(decodeEntities(match[0]))
				desc = cleanHTML(decodeEntities(match[1]))
				startTime = match[2]
				endTime = match[3]
				id = match[4]

				# format startTime 
				startDateTime = "%s %s" % (fileDate, startTime)
				fmtStartDateTime = time.strptime(startDateTime,"%Y%m%d %I:%M %p")

				# format endTime
				startDateTime = "%s %s" % (fileDate, endTime)
				fmtEndDateTime = time.strptime(startDateTime,"%Y%m%d %I:%M %p")

				startTimeSecs = time.mktime(fmtStartDateTime)
				# check if start is on prev day
				if not afterMidnight:
					if startTime[-2:] == 'PM':
						startTimeSecs -= 86400	# prog started on prev day subtract 24 hours
					
					if startTimeSecs >= fileDateMidnightSecs:
						afterMidnight = True
					
				endTimeSecs = time.mktime(fmtEndDateTime)
				# ensure prog ends after start. eg 11:50 PM to 12:10 AM
				if endTimeSecs <= startTimeSecs:
					endTimeSecs += 86400		# add 24 hours

				# check minimum data requirments
				if not id or not startTimeSecs or not endTimeSecs or not title:
					debug("rec missing mandatory fields")
					continue

				if DEBUG:
					print title, startTime, endTime, desc, startTimeSecs, endTimeSecs, id
				progList.append( {
						TVData.PROG_STARTTIME : float(startTimeSecs),
						TVData.PROG_ENDTIME : float(endTimeSecs),
						TVData.PROG_TITLE : title,
						TVData.PROG_ID : id,
						TVData.PROG_GENRE : genre,
						TVData.PROG_DESC : desc,
						TVData.PROG_DESCLINK : id
					} )

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
			debug("getLink() exception")
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

		self.IP = config.action(self.CONFIG_SECTION, KEY_IP)
		self.PORT = config.action(self.CONFIG_SECTION, KEY_PORT)
		self.USER = config.action(self.CONFIG_SECTION, KEY_USER)
		self.PASS = config.action(self.CONFIG_SECTION, KEY_PASS)

		if self.IP and self.PORT and self.USER and self.PASS:
			self.setup()
			self.isConfigured = True
		else:
			self.isConfigured = False
		debug("< ListingData.config() self.isConfigured=%s" % self.isConfigured)
		return self.isConfigured
