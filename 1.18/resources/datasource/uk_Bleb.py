############################################################################################################
# Bleb.py
# TV Data source: Bleb.org
# Notes:
# Site provides data in XML format files. Use RSS Parser to decode data into required Channel class.
# sample channel fetch for BBC1 - Today : "http://bleb.org/tv/data/rss.php?ch=bbc1&day=0"
# 07/03/08 Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__()")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.channelListURL = "http://www.bleb.org/tv/index.html?all"
		self.channelURL = "http://bleb.org/tv/data/rss.php?"			#ch=bbc1&day=0
		self.rssparser = RSSParser2()
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.rssItems = []
		self.lastFilename = ""

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME ,"ch=(.+?)&all\"(?:><b>|>)(.+?)<")


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
		rssList = []
		lastStartTime = 0 

		# download data file if file doesnt exists
		dataFilename = os.path.join(self.cache, "%s_%s.xml" % (chID, fileDate))
		if not fileExist(dataFilename):
			url = "%sch=%s&day=%s" % (self.channelURL,chID,dayDelta)
			found = self.rssparser.feed(url=url, file=dataFilename)
		elif dataFilename != self.lastFilename:
			found = self.rssparser.feed(file=dataFilename)
		else:
			found = True

		if not found:
			return None

		if dataFilename != self.lastFilename:
			# parse RSS data
			elementDict = { "title" : [],
							"description"  : [] }
			self.rssItems = self.rssparser.parse("item", elementDict)
		else:
			debug("XML already parsed")
		self.lastFilename = dataFilename

		# None == Error , [] = empty
		if not self.rssItems:
			return None

		# create Channel class using data
		for rssItem in self.rssItems:
			timeTitle = rssItem.getElement('title')
			desc = rssItem.getElement('description')
			match = re.search("(\d\d\d\d) : (.+?)$", timeTitle, re.MULTILINE + re.IGNORECASE)
			if match:
				startTime = match.group(1)
				title = decodeEntities(match.group(2))
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = secsEpoch
				progList.append( {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title,
						TVData.PROG_DESC : desc
					} )

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList
