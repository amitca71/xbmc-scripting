############################################################################################################
# TV Data source: German
#
# Notes:
# From www.tvinfo.de (using their older web pages - http://www.tvinfo.de/exe.php3) 
#
#
# CHANGELOG
# ---------
# 26/08/06 Created.
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from string import split, replace, find, rfind, atoi, zfill
from os import path

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.BASE_URL = "http://www.tvinfo.de/"
		self.CHANNELS_URL= self.BASE_URL + "my.php3?target=abfrage_sender"
		# $DAY and $MONTH tobe zero filled, YEAR YYYY
		self.CHANNEL_URL = self.BASE_URL + "exe.php3?target=senderlist.inc&h=0&min=00&newD=$DAY&newM=$MONTH&newY=$YEAR&showSenderID=$CHID"
		self.CHANNELS_FN = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		startStr = 'Senderauswahl konfigurieren'
		endStr = 'type="submit"'
		regex = 'name="s\[(.*?)\]".*?>(.*?)<'
		return getChannelsLIB(self.CHANNELS_URL, self.CHANNELS_FN , regex, startStr, endStr)


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
			year = fileDate[:4]
			month = fileDate[2:4]
			day = str(int(fileDate[-2:]) +1)	# +1 to day. 31st Aug is 32 08
			url = self.CHANNEL_URL.replace('$CHID',chID).replace('$DAY',day).replace('$MONTH',month).replace('$YEAR',year)
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		# check for timout, exception error, or empty page
		if not doc:
			return doc

		doc = doc.decode('latin-1','replace')
		debug("process data ...")
		# HH:MM, data -  which may/not contain href and name
		#regex = "(\d+:\d+).*?href=(exe.php3.*?)>(.*?)</a>(.*?)</td"
		regex = "(\d+:\d+).*?href=(exe.php3.*?)>(.*?)</a>(.*?)</td.*?spalte.*?>(.*?)</td"	# w/genre
		matches = parseDocList(doc, regex, 'output starts')
		if matches:
			for match in matches:
				startTime = match[0]
				link = match[1]
				title = cleanHTML(decodeEntities(unicodeToAscii(match[2])))
				desc = cleanHTML(unicodeToAscii(decodeEntities(match[3])))
				genre = cleanHTML(decodeEntities(unicodeToAscii(match[4])))
				if not startTime or not title:
					continue

				if link:
					descLink = self.BASE_URL + link
				else:
					descLink = ''
				if genre:
					genre = self.translateGenre(genre)

				# convert starttime to secs since epoch
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = secsEpoch
				progList.append( {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title,
						TVData.PROG_DESC : desc,
						TVData.PROG_SUBTITLE : desc,
						TVData.PROG_DESCLINK : descLink,
						TVData.PROG_GENRE : genre
					} )

				if DEBUG:
					print progList[-1]

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title=""):
		debug("ListingData.getLink()")
		desc = getDescriptionLink(link, 'END PARTNER PROGRAM -->(.*?)</table')		# main desc
		if not desc:
			desc = getDescriptionLink(link, 'HL1">(.*?)</td')						# title short desc
		return desc

	# translate into english genre filenames
	def translateGenre(self, genre):
		# 'find' is to better identify the subgenre eg. 'Show/Musik'
		# startswith identify main genre
		if find(genre, "Musik") != -1:
			genre = 'Music'
		elif find(genre, "Soap") != -1:
			genre = 'Soap'
		elif genre.startswith('Sport'):
			genre = 'Sport'
		elif genre.startswith('Magazin'):
			genre = 'Magazine'
		elif genre.startswith('Serie'):
			genre = 'Series'
		elif genre.startswith('Spielfilm'):
			genre = 'Film'
		elif genre.startswith('Kinder'):
			genre = 'Children'
		elif genre.startswith('Dokumentation'):
			genre = 'Documentary'
		elif genre.startswith('Erotik'):
			genre = 'Adult'
		elif genre.startswith('Show'):
			genre = 'Drama'
		return genre
