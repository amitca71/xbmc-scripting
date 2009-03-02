############################################################################################################
# TV Data source: Telkku
# Notes:
# Provides Finnish tv data.
# ChangeLog:
# 20/09/05 Fix. Change to web site urls
# 29/09/05 Fix. Change to web site html for channel regex.
# 10-03-2008 Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.channelListURL = "http://www.telkku.com/telkku?tila=knvt&kan=0&p=0"
		self.channelURL = "http://www.telkku.com/telkku?tila=knvt&kan="
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		# use the lib func to get channel list. Uses regex to extract data from url.
		# if this isn't suitable for your hosting site, write code to produce a channels list [chid, ch name]
		regex = ('kan=(\d+).*?>(.*?)<', '(0).*?<span>(.*?)<')
		start = '<h3>A-Z</h3>'
		stop = '</ul>'
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME, regex, start, stop)

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
			url = self.channelURL + chID + "&p=" + fileDate
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		doc = doc.decode('ISO-8859-1','replace')
		debug("parse data ...")
		matches = parseDocList(doc, ">(\d\d[.:]\d\d)(.*?)<.*?/>(.*?)<")
		if matches:
			for match in matches:
				if len(match) < 2:
					print "match too short, ignore. %s" % match
					continue

				try:
					startTime, title, desc = match
				except:
					startTime, title = match
					desc = ''

	#			print startTime, title, desc

				# convert starttime to secs since epoch
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = secsEpoch
				progList.append( {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : decodeEntities(title),
						TVData.PROG_DESC : decodeEntities(desc)
					} )

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return ''

