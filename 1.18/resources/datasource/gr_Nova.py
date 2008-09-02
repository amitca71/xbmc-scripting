############################################################################################################
# TV Data source: Nova 
# Notes:
# Provides GREEK tv data, From http://www.nova.gr/
# CHANGELOG
# 25/10/05 Created
# 10-03-2008 Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path

DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL
__language__ = sys.modules[ "__main__" ].__language__

# chid, chname
CHANNELS = [
	['81','Mega'],
	['82','ANTENNA'],
	['37','Alpha'],
	['225','Star'],
	['241','Alter'],
	['586','Macedonia TV'],
	['83','ET 1'],
	['401','Nwt'],
	['577','ET 3'],
	['549','Antenna Gold'],
	['535','E! Entertainment'],
	['227','MAD'],
	['20','MTV'],
	['19','VH1'],
	['579','Mezzo'],
	['555','BBC World'],
	['550','GBC'],
	['54','CNN'],
	['523','Bloomberg'],
	['101','Jetix'],
	['221','Cartoon Network'],
	['381','Discovery'],
	['25','Animal Planet'],
	['530','National Geographic'],
	['580','History Channel'],
	['17','Travel Channel'],
	['141','SuperSport 1'],
	['501','SuperSport 2'],
	['18','SuperSport 3'],
	['582','SuperSport 4'],
	['583','SuperSport 5'],
	['578','Motors TV'],
	['542','Eurosport'],
	['534','Eurosport 2'],
	['61','FilmNet 1'],
	['24','FilmNet 2'],
	['581','FilmNet 3'],
	['537','MGM'],
	['224','TCM']
]

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.linkURL = ""
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	def setup(self):
		debug("ListingData.setup()")
		self.BASE_URL = "http://www.nova.gr/%s/" % self.lang
		self.CHANNEL_URL = self.BASE_URL + "tvguide.asp?action=search&channel=$CHID&weekday=$DATE"

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		channels = []
		if not fileExist(self.CHANNELS_FILENAME):
			channels = writeChannelsList(self.CHANNELS_FILENAME, CHANNELS)
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
		if not self.isConfigured:
			debug("not configured!")
			return []
		progList = []
		lastStartTime = 0 

		# download data file if file doesnt exists
		dataFilename = os.path.join(self.cache, "%s_%s_%s.html" % (self.lang, chID, fileDate))
		if not fileExist(dataFilename):
			fetchDate = time.strftime("%d/%m/%Y",time.strptime(fileDate,"%Y%m%d"))
			url = self.CHANNEL_URL.replace('$CHID',chID).replace('$DATE', fetchDate)
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		debug("regex data ...")
		doc = doc.decode('latin-1','replace')
		# eg 06:28, link, title
		regex = '>(\d\d:\d\d)<.*?href=\"(.*?)\".*?<b>(.*?)</b'
		matches = parseDocList(doc, regex)
		if matches:
			for match in matches:
				if len(match) < 3:
					print "not enough data, ignore", match
					continue

				startTime = match[0]
				descLink = match[1]
				title = cleanHTML(decodeEntities(match[2]))
	#			print startTime, descLink, title

				# convert starttime to secs since epoch
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = secsEpoch
				progList.append( {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title,
						TVData.PROG_DESCLINK : descLink
					} )

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		re = 'SEARCH MAIN.*?(.*?)(?:END|E N D)'			# 05/08/08
		return getDescriptionLink(self.BASE_URL + link, re)

	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)

		CONFIG_SECTION = 'DATASOURCE_' + self.name
		CONFIG_KEY_LANG = 'lang'
		LANGS = ['Greek','English']

		self.lang = config.action(CONFIG_SECTION, CONFIG_KEY_LANG)
		origLang = self.lang 

		if reset or not self.lang:
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(616), width=350, rows=len(LANGS), panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(LANGS)
			if selectedPos >= 0:
				self.lang = LANGS[selectedPos]
				config.action(CONFIG_SECTION, CONFIG_KEY_LANG, self.lang, mode=ConfigHelper.MODE_WRITE)

		if self.lang:
			self.isConfigured = True
			self.setup()
			if self.lang != origLang:
				clearCache(True)
		else:
			self.isConfigured = False
		debug("< ListingData.config() isConfigured=%s" % self.isConfigured)
		return self.isConfigured
