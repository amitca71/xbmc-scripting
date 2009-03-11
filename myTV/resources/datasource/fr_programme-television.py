############################################################################################################
# TV Data source: France
# Notes:
# Provides FRENCH tv data, From http://www.programme-television.org/
# Changelog:
# 05/11/07 Fixed due to site change.
# 10-03-2008 Updated for myTV v1.18
# 10-03-2009 re fixed.
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.BASE_URL = "http://www.programme-television.org/"
		self.channelListURL = self.BASE_URL
		self.channelURL = self.BASE_URL + "programme-television-$CHID-$DATE-99-000000-CC0000-1.html"
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		regex = "option value=\"(\d+)\">(.*?)<"
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME, regex)


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

		if dayDelta < 0:
			return []	# no data as this site doesnt have negative day fetches

		# download data file if file doesnt exists
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, fileDate))
		if not fileExist(dataFilename):
			formatTime = time.strptime(fileDate,"%Y%m%d")
			urlDate = time.strftime("%d-%m-%y", formatTime)
			url = self.channelURL.replace('$CHID',chID).replace('$DATE',urlDate)
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		# find listing data
		doc = doc.decode('ISO-8859-1','replace')
		section = searchRegEx(doc, 'ProgrammeCol(.*?)INSCRIPTION',re.MULTILINE+re.IGNORECASE+re.DOTALL)

		# split in programmes
		progSplits = section.split("</table>")
		debug("section prog splits=" +str(len(progSplits)))
		if progSplits:
			# for each prog extract info
			reStartTime = '(\d\d:\d\d)'
			reDescLink = 'href="(.*?)"'
			reTitle = '(?:titrepc|lientitregc|titrejournalpc)">(.*?)</'
			reGenre = 'typepc">(.*?)<'
			reDesc = 'TexteResume">(.*?)<'
			reEpisodeName = 'sstitrepc">(.*?)<'
			reEpisodeDate = 'saisonpc">(.*?)<'
			for prog in progSplits:
				startTime = searchRegEx(prog, reStartTime)
				descLink = searchRegEx(prog, reDescLink).replace('description99','description')
				title = cleanHTML(decodeEntities(searchRegEx(prog, reTitle)))
				genre = decodeEntities(searchRegEx(prog, reGenre))
				desc = cleanHTML(decodeEntities(searchRegEx(prog, reDesc)))
				epInfo = ("%s %s" % (cleanHTML(decodeEntities(searchRegEx(prog, reEpisodeName))), 
							cleanHTML(decodeEntities(searchRegEx(prog, reEpisodeDate))))).strip()
				if epInfo:
					desc += ": " + epInfo
				if reDescLink:
					descLink = self.BASE_URL + descLink
				else:
					descLink = ''
				if not startTime or not title:
					print "bad scrape"
					continue
#				print "\n",startTime, title, genre, desc, descLink, epInfo

				# convert starttime to secs since epoch
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = secsEpoch
				progList.append( {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title,
						TVData.PROG_GENRE : genre,
						TVData.PROG_DESC : desc,
						TVData.PROG_DESCLINK : descLink
					} )

			progList = setChannelEndTimes(progList)		# update endtimes

		# return progList
		return progList

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return getDescriptionLink(link, "(\d\d:\d\d.*?)<form")
