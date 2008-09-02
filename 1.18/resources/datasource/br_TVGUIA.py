############################################################################################################
# TV Data source: TVGUIA
#
# Notes:
# From http://www.tvguia.com.br
#
#
# CHANGELOG
# ---------
# 28/04/06 Created.
# 10-03-2008 Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from string import replace, find
from os import path

# Translate genre to english
genreTranslation = {
#	"" : "Adult",
	"Infantil" : "Children",
#	"" : "Comedy",
	"Documentários" : "Documentary",
#	"" : "Drama",
	"Variedades" : "Entertainment",
	"Filmes" : "Film",
	"Infomercial" : "Interest",
#	"" : "Music",
	"Jornalismo" : "News",
#	"" : "Paid Programming",
	"Séries" : "Sitcom",
#	"" : "Soap",
#	"" : "Special"
	"Esportes" : "Sport"
#	"" : "Youth"
	}

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__()")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.BASE_URL = "http://www.tvguia.com.br/site/"
		self.channelListURL = self.BASE_URL + "grade.asp"
		self.channelURL = self.BASE_URL + "canal.asp?id=$CHID&data=$DATE"
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.LINK_URL = self.BASE_URL + "programa.asp?id=$PROGID"

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME , \
							"link_cannal\('(.*?)'\)(?:.*?)alt=\"(.*?)\"")


	# download channel data, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	#
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("ListingData.getChannel() dayDelta: %s chID=%s fileDate=%s" % (dayDelta,chID,fileDate))
		if dayDelta < 0:
			return []
		progList = []
		lastStartTime = 0 

		# download data file if file doesnt exists
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, fileDate))
		if not fileExist(dataFilename):
			formatTime = time.strptime(fileDate,"%Y%m%d")
			urlDate = time.strftime("%Y-%m-%d", formatTime)
			url = self.channelURL.replace('$CHID',chID).replace('$DATE',urlDate)
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		doc = doc.decode('latin-1','replace')
		progsDict = {}
		# PROGS WITH LINKS
		regex = ">(\d\d:\d\d)<(?:.*?)id=(\d+)\">(.*?)<(?:.*?)th>(.*?)$"
		matches = findAllRegEx(doc, regex)
		if matches:
			for match in matches:
				try:
					startTime = match[0]
					progID = match[1]
					title = decodeEntities(match[2]).strip()
					genre = decodeEntities(match[3]).strip()
					if not startTime or not title:
						print "bad scrape"
						continue
				except:
					print "bad scrape"

				# convert genre to english
				try:
					genreEN = genreTranslation[genre.encode('latin-1','replace')]
				except:
					genreEN = ''
				descLink = self.LINK_URL.replace('$PROGID',progID)
#				print startTime, progID, link, genreEN

				# convert starttime to secs since epoch
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = secsEpoch
				progList.append( {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title,
						TVData.PROG_GENRE : genreEN,
						TVData.PROG_DESCLINK : descLink,
						TVData.PROG_ID : progID
					} )

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList


	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return getDescriptionLink(link, "table summary=(?:.*?)top\">(.*?)<")
