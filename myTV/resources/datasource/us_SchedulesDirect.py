############################################################################################################
# TV Data source: schedulesdirect
#
# SETUP
# -----
# 1) Create an account at wwww.schedulesdirect.org
# 2) Run myTV and enter User/Pass when prompted. (can be re-configured via ConfigMenu)
#
# REVISION HISTORY:
# 20-11-2005 - Added. Genre and subTitle support
# 17-01-2006 - Added. user/password now configurable from GUI and stored into config file.
# 22-08-2006 - CHanged: Uses new Config class
# 02-10-2006 - Fix: incorrectly check DST from config
# 03-03-2008 - Now uses Schedules Direct - requires a paid a/c wwww.schedulesdirect.org ~ $20pa
############################################################################################################

from mytvLib import *
import mytvGlobals
import xbmc,xbmcgui, re, time, os.path
from string import zfill

__language__ = sys.modules["__main__"].__language__

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__()")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.XML_FILENAME = os.path.join(self.cache, "XMLTV_$DATE.xml")
		self.isConfigured = False

	def getName(self):
		return self.name

	def setup(self):
		debug("ListingData.setup()")
		# calc GMT offset, taking into account DST setting
		self.GMT_OFFSET = ((time.timezone * -1)/3600)
		if self.DST:
			self.GMT_OFFSET += 1
		#self.GMT_OFFSET = -4						# use this if the calc isnt working well for you
		debug("useDST=%s  time.timezone=%s  GMT_OFFSET=%s" % (self.DST, time.timezone, self.GMT_OFFSET))


	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		if not self.isConfigured:
			return []

		channels = []
		if not fileExist(self.CHANNELS_FILENAME):
			# get todays XMLTV data file and extract channels from that
			fileDate = time.strftime( '%Y%m%d', time.localtime())
			fn = self.XML_FILENAME.replace('$DATE', fileDate)
			if self.getXMLTV(fileDate, fn):
				channels = getChannelListXMLTV(fn)
				if channels:
					channels = writeChannelsList(self.CHANNELS_FILENAME, channels)
		else:
			channels = readChannelsList(self.CHANNELS_FILENAME)

		return channels

	# download channel data, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("ListingData.getChannel() dayDelta: %s chID=%s fileDate=%s" % (dayDelta,chID,fileDate))
		if dayDelta < 0:
			return []

		# one XML contains all channel data
		dataFilename = self.XML_FILENAME.replace('$DATE', fileDate)
		if not self.getXMLTV(fileDate, dataFilename):
			return None

		# parse data
		progList = []
		listing = readFile(dataFilename)
		if listing:
			channelProgs = []
			GMToffsetSecs = (self.GMT_OFFSET * 60) * 60
			regex = "<schedule program=\'(.*?)'\ station=\'"+chID+"\' time=\'(.*?)\' duration=\'(.*?)\'"
			matches = re.findall(regex, listing)
			for match in matches:
				try:
					progID = match[0]
					startTime = match[1]
					duration = match[2]
					channelProgs.append([progID, startTime, duration])
				except:
					print "not enough channel data", match

			for progID, progDateTime, progDur in channelProgs:
				try:
					# create date in reverse. ie 2008-08-15T06:37:00Z -> 20050630
					reverseDate = progDateTime[:4] + progDateTime[5:7] + progDateTime[8:10]
					if reverseDate != fileDate:
						continue

					# calc programme start/end time in secs since epoch based on programme date
					startTimeSecs = time.mktime(time.strptime(progDateTime,"%Y-%m-%dT%H:%M:%SZ"))
					progDurSecs = ((int(progDur[2:4]) * 60) + int(progDur[5:7])) * 60
					endTimeSecs = startTimeSecs + progDurSecs
					startTimeSecs += GMToffsetSecs
					endTimeSecs += GMToffsetSecs

					# get programme info
					tags = ['title','subTitle','Description','showType']
					tagData = getProgrammeXMLTV(listing, progID, tags)
					if tagData:
						progList.append( {
								TVData.PROG_STARTTIME : float(startTimeSecs),
								TVData.PROG_ENDTIME : float(endTimeSecs),
								TVData.PROG_DUR : progDurSecs,
								TVData.PROG_TITLE : tagData["title"],
								TVData.PROG_SUBTITLE : tagData["subTitle"],
								TVData.PROG_GENRE : tagData["showType"],
								TVData.PROG_DESC : tagData["Description"]
							} )

#						if DEBUG:
#							print progList[-1]
				except:
					print "error parsing channel data", progID, progDateTime, progDur
					handleException("getChannel()")

			del channelProgs

		return progList

	############################################################################################################
	# DOWNLOAD/PARSE XMLTV DATA
	############################################################################################################
	def getXMLTV(self, fileDate, filename):
		debug("> ListingData.getXMLTV() fileDate=%s fn=%s" % (fileDate,filename))

		if not fileExist(filename):
			success = False
			while not success:
				result = fetchXMLTV(self.USER, self.PWD, fileDate, filename)
				if result < 0:	# logon failed
					if xbmcgui.Dialog().yesno("Schedules Direct","Login Failed","Amend Username/Password and try again ?"):
						self.config(True)	# force reset
					else:
						break
				elif result == 0:				# any other error
					deleteFile(filename)		# might be corrupt
					break
				else:
					success = True
		else:
			debug("file exists")
			success = True

		debug("< ListingData.getXMLTV() success=%s" % success)
		return success

	############################################################################################################
	# load, if not exist ask, then save
	############################################################################################################
	def config(self, reset=False):
		debug("> config() reset=%s" % reset)

		CONFIG_SECTION = 'DATASOURCE_' + self.name
		# CONFIG KEYS
		KEY_USER = 'user'
		KEY_PASS = 'pass'
		KEY_DST = 'dst'

		# config key, title, defaultValue, kbtype
		configData = [
			[KEY_USER, __language__(805), 'SchedulesDirect Username', KBTYPE_ALPHA],
			[KEY_PASS, __language__(806), 'SchedulesDirect Password', KBTYPE_ALPHA],
			[KEY_DST, "Enable Daylight Saving Time?", False, KBTYPE_YESNO]
			]

		if reset:
			configOptionsMenu(CONFIG_SECTION, configData, self.name, 350)

		self.USER = mytvGlobals.config.action(CONFIG_SECTION, KEY_USER)
		self.PWD = mytvGlobals.config.action(CONFIG_SECTION, KEY_PASS)
		dst = mytvGlobals.config.action(CONFIG_SECTION, KEY_DST)
		if dst not in (True, False):
			dst = False
		self.DST = mytvGlobals.config.configHelper.boolToYesNo(dst)

		if self.USER and self.PWD:
			self.setup()
			self.isConfigured = True
		else:
			self.isConfigured = False

		debug("< config() self.isConfigured=%s" % self.isConfigured)
		return self.isConfigured



############################################################################################################
def getChannelListXMLTV(filename):
	debug("> getChannelListXMLTV() filename=" + filename)

	channelList = []
	listing = readFile(filename)
	if listing:
		# station IDs
		chIDList = re.findall("<station id=\'(.*?)\'",listing)
		chIDSZ = len(chIDList)
		debug("chIDList sz: %s" % chIDSZ)
		if not chIDList:
			debug("failed to find any chID's")
		else:
			# station NAME
			chNAMEList = re.findall("<name>(.*?)</name>",listing)
			debug("chNAMEList sz: %s" % len(chNAMEList))

			# callSign
			chCallSignList = re.findall("<callSign>(.*?)</callSign>",listing)
			debug("chCallSignList sz: %s" % len(chCallSignList))

			# make a list [chID, chName, callSign]
			for i in range(chIDSZ):
				try:
		#			print chIDList[i], chCallSignList[i], chNAMEList[i]
					channelList.append([chIDList[i], chNAMEList[i], chCallSignList[i]])
				except:
					handleException("getChannelListXMLTV() bad chID data")
					break

	debug("< getChannelListXMLTV() channels count=%s" % len(channelList))
	return channelList


############################################################################################################
def getProgrammeXMLTV(listing, progID, tags):
	debug("getProgrammeXMLTV() progID=%s" % progID)

	title = ""
	desc = ""
	showType = ""
	tagData = {}
	if listing:
		regex = "<program id=\'"+progID+"\'>(.*?)</program"
		matches = re.search(regex,listing, re.DOTALL + re.MULTILINE)
		if matches:
			for tag in tags:
				regex = tag+'>(.*?)</'+tag
				tagMatches = re.search(regex, matches.group(1), re.DOTALL + re.MULTILINE + re.IGNORECASE)
				if tagMatches:
					tagData[tag] = decodeEntities(tagMatches.group(1)).decode('latin-1')
				else:
					tagData[tag] = ''


#	print "tagData=", tagData
	return tagData
