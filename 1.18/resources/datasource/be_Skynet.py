############################################################################################################
# TV Data source: Skynet
# Notes:
# Provides listing data for Belgium & France. www.skynet.be
#
# NOTES
# -----
# Requested by Aert Wezenbeek.
#
# SETUP
# -----
# Select Language when run run myTV - This file doesnt need editing.
#
# CHANGELOG
# ---------
# 17-01-2006 - Created
# 13-11-2006 - Fix: regex for channel name
# 27-05-2007 - Fix: new URLs and scrape regex
# 01-05-2008 - Updated for myTV v1.18
#              Modified so selected language changes BASE_URL
############################################################################################################

from bbbGUILib import *
from mytvLib import *

import xbmcgui, re, time
from string import split, replace, find, rfind, atoi, zfill
from os import path
from urlparse import urljoin

__language__ = sys.modules[ "__main__" ].__language__

# translate genre into english. This will enable the use of genre icons/colours in GUI
GENRE_TRANSLATIONS = {
	# NL
	'NIEUWS' : 'News',
	'JEUGD' : 'Youth',
	'ONTSPANNING' : 'Entertainment',
	'SERIE' : 'Soap',
	'FILM' : 'Film',
	'Films' : 'Film',
	'SPORT' : 'Sports',
	'ONTSPANNING' : 'Comedy',
	'Tv-series' : 'Drama',
	'Reclame' : 'Documentary',

	# FR
	'INFORMATION' : 'News',
	'JEUNESSE' : 'Youth',
	'LOISIR' : 'Comedy',
	'Série Télé' : 'Drama'
}


class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext

	def getName(self):
		return self.name

	def setup(self):
		debug("ListingData.setup()")
		self.name = "%s_%s" % (os.path.splitext(os.path.basename( __file__))[0], self.country_code)
		if self.country_code == 'nl':
			# dutch
			channelsStr = "kanalen"
			self.BASE_URL = "http://www.skynet.be/entertainment-nl/tv/"
		else:
			# french
			channelsStr = "chaines-tv"
			self.BASE_URL = "http://www.skynet.be/entertainment-fr/tele/"

		self.CHANNELS_URL = self.BASE_URL + channelsStr
		self.CHANNEL_URL = self.BASE_URL + channelsStr + "_$HREFID?channelid=$CHID&date=$DATE"
		self.CHANNELS_RE = channelsStr + '_(.*?)\?.*?channelid=(\d+).*?title="(.*?)"'		# href id, chid, ch name

		self.CHANNELS_FILENAME = os.path.join(self.cache,"Channels_"+ self.name + ".dat")
		debug("%s\n%s\n" % (self.CHANNELS_URL,self.CHANNEL_URL))

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("> ListingData.getChannels()")
		channels = []
		self.hrefIDs = {}		# lookup by chID to get href chname_id
		if not fileExist(self.CHANNELS_FILENAME):
			dialogProgress.create(self.name, __language__(212))
			doc = fetchURL(self.CHANNELS_URL)
			if doc:
				startStr = 'id="channelBox"'
				endStr = '</div>'
				matches = parseDocList(doc, self.CHANNELS_RE, startStr, endStr)
				for hrefID, chID, chName in matches:
					channels.append([chID, decodeEntities(chName), hrefID])		# hrefID will be used to for the chid_name in the  url

				if channels:
					channels.sort()
					channels = writeChannelsList(self.CHANNELS_FILENAME, channels)
			dialogProgress.close()
		else:
			channels = readChannelsList(self.CHANNELS_FILENAME)

		# make dict of hrefIDs
		if channels:
			for chID, chName, hrefID in channels:
				self.hrefIDs[chID] = hrefID

		debug("< ListingData.getChannels()")
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
		progList = []
		lastStartTime = 0 
		doc = ''

		# download whole site page if not got data for date
		# FETCH URL
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, fileDate))
		if not fileExist(dataFilename):
			try:
				hrefID = self.hrefIDs[chID]
				formatTime = time.strptime(fileDate,"%Y%m%d")
				urlDate = time.strftime("%Y-%m-%d", formatTime)
				url = self.CHANNEL_URL.replace('$HREFID', hrefID).replace('$CHID',chID).replace('$DATE',urlDate).replace(' ','%20')
				doc = fetchURL(url, dataFilename)
			except:
				debug("unknown hrefID from chID")
				doc = None	# error
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		doc = doc.decode('utf8','replace')
		# HH:MM, link, title, genre
		regex = '>(\d+:\d+).*?href=\"(.*?)\".*?>(.*?)</.*?cat">(.*?)<'
		matches = parseDocList(doc, regex, 'programsByDate','</div')
		if matches:
			isFirstProg = True
			for match in matches:
				try:
					startTime = match[0]
					descLink = urljoin(self.BASE_URL, match[1])
					title = decodeEntities(match[2])
					genre = self.translateGenre(match[3])
				except:
					print "invalid match", match
					continue

				# convert starttime to secs since epoch
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				# first prog might be on prev day . eg 23:40 - so substract 24hours
				if isFirstProg:
					if startTime[:2] == '23':			# hour
						debug("adjusting time back 24hours as first prog is 23:xx hour")
						secsEpoch -= 86400	# 24hours in secs
					isFirstProg = False

				lastStartTime = secsEpoch
				progList.append( {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title,
						TVData.PROG_GENRE : genre,
						TVData.PROG_DESCLINK : descLink
					} )

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList

	# Download url and regex parse it to extract description.
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		startStr = 'programDetails'
		desc = getDescriptionLink(link, 'programDetails">(.*?)</div')	# 31/07/08
		return cleanHTML(decodeEntities(desc, removeNewLines=False))

	# Translate language genre into english.
	def translateGenre(self, genre):
		try:
			translation = GENRE_TRANSLATIONS[genre.upper()]
		except:
			translation = genre
		return translation

	############################################################################################################
	# load, if not exist ask, then save
	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config()")

		CONFIG_OPT = 'country'
		CONFIG_SECTION = 'DATASOURCE_Skynet'

		if reset:
			self.country_code = ''
		else:
			self.country_code = config.action(CONFIG_SECTION, CONFIG_OPT)

		menu = ['Dutch','French']
		langCodes = ['nl','fr']
		while not self.country_code:
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(616), rows=len(menu), width=200, panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(menu)
			if selectedPos >= 0:
				self.country_code = langCodes[selectedPos]
			else:
				break

		if not self.country_code:
			self.country_code = langCodes[0]	# default to 1st lang

		config.action(CONFIG_SECTION, CONFIG_OPT, self.country_code, mode=ConfigHelper.MODE_WRITE)
		self.setup()

		debug("< ListingData.config() country_code=%s" % self.country_code)
		return True
	