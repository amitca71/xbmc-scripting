############################################################################################################
# TV Data source: es_miguiatv (spain)
#
# 05-08-2008 Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from string import split, replace, find, rfind, atoi, zfill
from os import path

# Translate genre to english
GENRE_TRANSLATIONS = {
	"ADULTOS" : "Adult",
	"INFANTILE" : "Children",
	"CARTOONS" : "Childrens",
	"INFANTIL" : "Children",
	"DIBUJOS ANIMADOS" : "Childrens",
	"HUMOR" : "Comedy",
	"DOCUMENTARY" : "Documentary",
	"DOCUMENTAL" : "Documentary",
	"SERIE" : "Drama",
	"DRAMA" : "Drama",
	"MAGAZINE" : "Entertainment",
	"ENTRETENIMIENTO" : "Entertainment",
	"PELICULA" : "Film",
	"CINEMA" : "Film",
	"CINE" : "Film",
	"INTERES" : "Interest",
	"MUSICAL" : "Music",
	"NOTICIAS" : "News",
	"REPORTAJE" : "News",
	"INFORMATIVOS" : "News",
	"NEWS ARTICLE" : "News",
	"INFORMATIVE" : "News",
	"PPV" : "Paid Programming",
	"SERIES DE HUMOR" : "Sitcom",
	"TELENOVELA" : "Soap",
	"DIVULGING" : "Special",
	"DEPORTES" : "Sport",
	"ADOLESCENTES" : "Youth"
}


class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.BASE_URL = 'http://www.miguiatv.com/'
		self.channelListURL = self.BASE_URL + 'rss.html'
		self.channelURL = self.BASE_URL + '$DATE/$CHID.html'
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		regex = 'rsspage\"(?:.*?)rss/(.*?)\.(?:.*?)gif\">(.*?)<'
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME, regex)


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
		progList = []
		lastStartTime = 0 

		# download data file if file doesnt exists
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, fileDate))
		if not fileExist(dataFilename):
			debug("downloading channel ...")
			url = self.channelURL.replace('$CHID',chID).replace('$DATE',fileDate)
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		# check for timout, exception error, or empty page
		if not doc:
			return doc

		doc = doc.decode('latin-1','replace')
		# create Channel from data file
		debug("processing file ...")
		# start, genre, desc
		regex = '>(\d\d:\d\d)<(?:.*?)<strong>(.*?)</strong(?:.*?)<strong>(.*?)</strong(?:.*?)colspan=\"2\">(.*?)<'
		matchList = parseDocList(doc, regex, 'show_even','</div>')
		if matchList:
			for match in matchList:
				try:
					startTime = match[0]
					title = cleanHTML(decodeEntities(match[1]))
					genre = self.translateGenre(match[2]).strip()
					desc = cleanHTML(decodeEntities(match[3]))
				except:
					debug("regex match too short")
					continue

				# convert starttime to secs since epoch
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = secsEpoch
#				print title, desc, secsEpoch, genre
				progList.append( {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title,
						TVData.PROG_GENRE : genre,
						TVData.PROG_DESC : desc
					} )

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList

	# Translate language genre into english.
	def translateGenre(self, genre):
		try:
			translation = GENRE_TRANSLATIONS[genre.upper()]
		except:
			translation = ''
		return translation

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		return ''
