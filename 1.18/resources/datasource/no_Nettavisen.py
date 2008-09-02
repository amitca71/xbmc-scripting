############################################################################################################
# TV Data source: Nettavisen 
# Notes:
# Provides Norwegian tv data, From http://pub.tv2.no/nettavisen/
# 24-10-2005 - Fix, Due to HTML change. Also increased number of channels available.
# 07-01-2006 - Fix: Rewrote how channel data collected as it was missing progs w/o links
# 12-08-2008 - Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.channelListURL = "http://pub.tv2.no/nettavisen/tv/long/"
		self.channelURL = "http://pub.tv2.no/nettavisen/do/tvguide/search?category=alle&timeslot=0&sort=channel&textquery=&day=$DAYDELTA&channel=$CHID"
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		regex = "<input type=checkbox(?:.*?)value=(.*?)[>| ](?:.*?)\)>(.*?)<"	# 12/08/08
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
		if dayDelta < 0:
			return []	# no data as this site doesnt have negative day fetches

		progList = []
		lastStartTime = 0 

		# download data file if file doesnt exists
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, fileDate))
		if not fileExist(dataFilename):
			url = self.channelURL.replace('$DAYDELTA', str(dayDelta)).replace('$CHID',chID)
			html = fetchURL(url, dataFilename)
		else:
			html = readFile(dataFilename)

		# check for timout, exception error, or empty page
		if not html:
			return html

		debug("regex data to extract title & description etc ...")
		html = html.decode('latin-1','replace')
		# get table
		section = searchRegEx(html, '<TABLE BGCOLOR="#ffffff"(.*?)</table>', re.DOTALL + re.MULTILINE + re.IGNORECASE)
		splits = section.split('<TR bgcolor=')
		if splits:
			reList = ('>(\d\d:\d\d)<(?:.*?)false\">(.*?)<(?:.*?)display:none\">(.*?)Slutt',
					  '>(\d\d:\d\d)<(?:.*?)verdana>(.*?)<()')
			for split in splits:
				try:
					startTime = ''
					title = ''
					description = ''
					for regex in reList:
						matches = re.search(regex, split, re.DOTALL+re.IGNORECASE)
						if matches:
							startTime= matches.group(1).strip()
							title = cleanHTML(decodeEntities(matches.group(2)))
							desc = cleanHTML(decodeEntities(matches.group(3))).replace('null','')
							break # found, stop doing regex loop

					# convert starttime to secs since epoch
					if startTime and title:
	#					print startTime, title
						secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
						lastStartTime = secsEpoch
						progList.append( {
								TVData.PROG_STARTTIME : float(secsEpoch),
								TVData.PROG_ENDTIME : 0,
								TVData.PROG_TITLE : title,
								TVData.PROG_DESC : desc
							} )
				except: pass

			progList = setChannelEndTimes(progList)		# update endtimes
		return progList

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return ""
