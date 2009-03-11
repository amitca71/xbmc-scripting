############################################################################################################
# TV Data source: Ireland
# Notes: Only 'film genere provided.
# Provides Irish & Partial UK TV data (as per common Irish Cable operators), From http://www.entertainment.ie/
# Based on datasource_france.py - modified by collity ... ccox_dublin(!at!)yahoo.co.uk
# Modified again to fetch 7 days by BBB
# Changelog
# 13-11-06 Fix: regex & start_str to get channels
#          Fix: prevent -1 daydelta fetches (caused HTTP 500 error)
# 11-03-09 Fix: base url & params changed. Now based on two html pages per channel.
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.BASE_URL = "http://entertainment.ie/TV/display.asp?cat=tv"
		self.CHANNELS_URL = self.BASE_URL
		self.CHANNEL_URL = self.BASE_URL+ "&prnt=1"
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		regex = "option value=\"(.+?)\">(.*?)<"
		start_str = ">All<"
		end_str = "</select>"
		return getChannelsLIB(self.CHANNELS_URL, self.CHANNELS_FILENAME, regex, start_str, end_str)


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
			return []	# no data as this site doesnt have negative day fetches
		progList = []
		lastStartTime = 0 

		# download data file if file doesnt exists
		formatTime = time.strptime(fileDate,"%Y%m%d")
		urlDate = time.strftime("%d %B %Y", formatTime)
		prog_times = ('time5','time6')
		for prog_time in prog_times:
			dataFilename = os.path.join(self.cache, "%s_%s_%s.html" % (prog_time, chID, fileDate))
			# make POST params
			postData = {
				'programme_day' : urlDate,
				'programme_time' : prog_time,
				'channelid' : chID
				}
			params = urllib.urlencode(postData)
			doc = fetchURL(self.CHANNEL_URL, dataFilename, params=params)

			if not doc:
				continue

			doc = doc.decode('latin-1','replace')

			# HH:MM, data -  which may/not contain href and name
			regex = '>(\d\d:\d\d).*?programme">(.*?)</td.*?<td.*?>(.*?)</td'
			startStr = "<h3>%s<" % chName
			matches = parseDocList(doc, regex, startStr,'</table>')
			for match in matches:
				startTime = match[0]
				title = decodeEntities(cleanHTML(match[1]))
				desc = decodeEntities(cleanHTML(match[2]))
				if not startTime or not title:
					continue

				# convert starttime to secs since epoch
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

	# Download url and regex parse it to extract description.
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return ''
