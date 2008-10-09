############################################################################################################
# TV Data source: nl_TVGids
# Notes:
# Provides Dutch tv data.
# Changelog:
# 15-11-06 Fix: get description regex
# 07-03-08 Updated & Fix for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path

# Translate genre to english
GENRE_TRANSLATIONS = {
       "Serie" : "Series",
       "Amusement":"Entertainment",
       "Animatie":"Animation",
       "Documentaire":"Documentary",
       "Erotiek":"Adult",
       "Informatief":"Interests",
       "Jeugd":"Children",
       "Kunst/Cultuur":"Music and Arts",
       "Misdaad":"Drama",
       "Muziek":"Music",
       "Natuur":"Documentary",
       "Nieuws/Actualiteiten":"Interests",
       "Theater":"Drama",
       "Wetenschap":"Special"
}

# Add to this list genres (in english) you wish datasource to additionally lookup.
# Each genre added will potentially slow the datasource.
GENRES_TO_FIND = ["Film","Sport","Serie"]

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.BASE_URL = "http://www.tvgids.nl"
		self.channelListURL = self.BASE_URL + "/index.php"
		self.channelURL = self.BASE_URL + "/zoeken/?trefwoord="
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.GENRE_URL = self.BASE_URL + "?trefwoord=&station=$STATION&dagdeel=0.0&genre=$GENRE"
		self.HEADERS = {'Accept':'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
						'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.9) Gecko/20071025'}

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		debug("getChannels()")
		regex = 'option value="(\d+)" >(.+?)<'
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME, regex, \
								  startStr="Hoofdzenders", headers=self.HEADERS)


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
		url = self.channelURL + "&station=" + chID+"&dagdeel="+str(dayDelta)+'.0'
		if not fileExist(dataFilename):
			doc = fetchCookieURL(url, dataFilename, headers=self.HEADERS)
		else:
			doc = readFile(dataFilename)

		# check for timout, exception error, or empty page
		if not doc:
			return doc

		doc = doc.decode('latin-1')

		# fetch listings filtered by genre, each one added here will slow down the whole process
		# extract prog link as key
		regex = '>\d+:\d+ - \d+:\d+<.*?href=\"(.*?)\"'
		genreURL = self.channelURL + "&station=&dagdeel="+str(dayDelta)+'.0'
		progsGenreDict = {}
		for genre in GENRES_TO_FIND:
			genreFilename = os.path.join(self.cache, "%s_%s_%s.dat" % (self.name,genre,fileDate))	# all channels
			progsList = self._findChannelGenre(genreURL + "&genre="+genre, regex, genreFilename)

			# make prog the key and save genre against it
			for prog in progsList:
				progsGenreDict[prog] = self.translateGenre(genre)

#		print "progsGenreDict=", progsGenreDict

		# get days listing page (no genre)
		regex = ">(\d+:\d+) - (\d+:\d+)</th>.*?href=\"(.*?)\">(.*?)<"
		matches = findAllRegEx(doc, regex) 
		for match in matches:
			try:
				startTime = match[0]
				endTime = match[1]
				link = match[2]
				title = cleanHTML(decodeEntities(match[3]))

				# prog stored with a genre  ?
				try:
					progGenre = progsGenreDict[link]
				except:
					progGenre = ""

				descLink = decodeEntities(link)
				if descLink:
					descLink = self.BASE_URL + descLink

				# convert starttime to secs since epoch
				startSecsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = startSecsEpoch
				endSecsEpoch = startTimeToSecs(lastStartTime, endTime, fileDate)
#				print title, startTime, progGenre
				progList.append( {
						TVData.PROG_STARTTIME : float(startSecsEpoch),
						TVData.PROG_ENDTIME : float(endSecsEpoch),
						TVData.PROG_TITLE : title,
						TVData.PROG_GENRE : progGenre,
						TVData.PROG_DESCLINK : descLink
					} )
			except:
				print "bad programme scrape", match

		# return progList
		return progList


	# Translate language genre into english.
	def translateGenre(self, genre):
		try:
			return GENRE_TRANSLATIONS[genre]
		except:
			return genre

	# load page based on a genre, store prog
	def _findChannelGenre(self, url, regex, genreFilename):
		debug("> _findChannelGenre()")
		progsList = []
		doc = ""

		if not fileExist(genreFilename):
			doc = fetchCookieURL(url, genreFilename, headers=self.HEADERS)
		else:
			doc = readFile(genreFilename)

		if doc:
			progsList = findAllRegEx(doc, regex) 

		debug("< _findChannelGenre() found=" + str(len(progsList)))
		return progsList


	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return getDescriptionLink(link, "<span>"+title+"</span>(?:.+?)<p>(.+?)</", headers=self.HEADERS)
