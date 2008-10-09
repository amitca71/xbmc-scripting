############################################################################################################
# TV Data source: nl_omreap
# Notes:
# Provides Dutch tv data.
# Changelog:
# 21-11-07 created as an alternative for nl_TVGids
# 10-03-2008 Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path

# Translate genre to english
GENRE_TRANSLATIONS = {
       "Filmgids" : "Film",
       "Sportgids": "Sport",
       "Soapgids": "Soap"
}

# Add to this list genres (in english) you wish datasource to additionally lookup.
# Each genre added will potentially slow the datasource.
GENRES_TO_FIND = ["Filmgids","Sportgids","Soapgids"]


class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.BASE_URL = "http://gids.omroep.nl"
		self.channelListURL = self.BASE_URL + "/core/content.php?Z=&dag=0"
		self.channelURL = self.BASE_URL + "/core/content.php?Z=&tijd=hele+dag"
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.HEADERS = {'Accept':'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5'}

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		regex = 'zenderlijstnaam">(.*?)<.*?name="(.*?)"'
		channels = getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME, regex, reversed=True, headers=self.HEADERS)
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
		progList = []
		lastStartTime = 0 

		# download data file if file doesnt exists
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, fileDate))
		if not fileExist(dataFilename):
			url = self.channelURL + "&dag=" + str(dayDelta) + "&" + chID + "=on"
			doc = fetchCookieURL(url, dataFilename, headers=self.HEADERS)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		doc = doc.decode('latin-1','replace')

		# fetch listings filtered by genre, each one added here will slow down the whole process
		# extract prog link as key
		regex = '>\d+:\d+ - \d+:\d+<.*?href=\"(.*?)\"'
		genreURL = self.channelURL + '&medium=TV&dag=' + str(dayDelta) + '&guide='
		progsGenreDict = {}
		for genre in GENRES_TO_FIND:
			genreFilename = os.path.join(self.cache, "%s_%s_%s.html" % (self.name,genre,fileDate))
			progs = self._findChannelGenre(genreURL + genre, regex, genreFilename)

			# make prog the key and save genre against it
			for prog in progs:
				progsGenreDict[prog] = self.translateGenre(genre)

		regex = '"pt">(\d+:\d+)<.*?href="(.*?)".*?"title">(.*?)<.*?<br />(.*?)</a'
		matches = parseDocList(doc, regex, "Programmaoverzicht","</form>")
		if matches:
			for match in matches:
				try:
					startTime = match[0]
					link = match[1]
					title = cleanHTML(decodeEntities(match[2]))
					desc = cleanHTML(decodeEntities(match[3]))

					# prog stored with a genre  ?
					try:
						progGenre = progsGenreDict[link]
					except:
						progGenre = ""

					descLink = decodeEntities(link)
					if descLink:
						descLink = self.BASE_URL + descLink

					# convert starttime to secs since epoch
					secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
					lastStartTime = secsEpoch
	#				print title, startTime, progGenre
					progList.append( {
							TVData.PROG_STARTTIME : float(secsEpoch),
							TVData.PROG_ENDTIME : 0,
							TVData.PROG_TITLE : title,
							TVData.PROG_GENRE : progGenre,
							TVData.PROG_DESC : desc,
							TVData.PROG_DESCLINK : descLink
						} )
				except:
					print "bad programme scrape", match

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList

	# load page based on a genre, store prog
	def _findChannelGenre(self, url, regex, genreFilename):
		debug("> ListingData._findChannelGenre() %s" % genreFilename)

		if not fileExist(genreFilename):
			doc = fetchCookieURL(url, genreFilename, headers=self.HEADERS)
		else:
			doc = readFile(genreFilename)

		if doc:
			progsList = findAllRegEx(doc, regex)
		else:
			progsList = []

		debug("< ListingData._findChannelGenre()")
		return progsList

	# Translate language genre into english.
	def translateGenre(self, genre):
		try:
			return GENRE_TRANSLATIONS[genre]
		except:
			return genre

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return getDescriptionLink(link, 'subprogbarbg">(.*?)</table', headers=self.HEADERS)
