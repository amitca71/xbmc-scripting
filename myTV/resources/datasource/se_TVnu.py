############################################################################################################
# TV Data source: TVnu
# Notes:
# Provides Swedish tv data.
# 01-10-07 Fix: regex due to site HTML change
# 07-03-08 Fix: regex due to site HTML change
# 13-08-08 Updated for myTV v1.18
#          Updated to see date pages other than just todaybeyond today..
#          Downloads channels available instead of being hardcoded.
#          Fix: regex due to site HTML changes
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path
from string import upper

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__()")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		BASE_URL = "http://www.tv.nu"
		self.CHANNELS_URL = BASE_URL
		self.CHANNEL_URL = BASE_URL
		self.DESC_URL = BASE_URL				# 13/08/08
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

		# Idag = today, Imorgon = tomorrow,
		# mandag = monday, tisdag = tuesday, Onsdag = wednesday , torsdag = Thursday
		# Fredag = Friday, lordag = saturday, sondag = sunday	
		self.DAYS = {0: 'mandag', 1:'tisdag', 2: 'onsdag', 3:'torsdag', 4:'fredag', 5:'lordag', 6:'sondag'}

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		regex = 'tabla_kanal".*?href="/kanal/(.*?)">(.*?)<'
		return getChannelsLIB(self.CHANNELS_URL, self.CHANNELS_FILENAME, regex)


	# download channel data, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	#
	# This site provides just one days data for all channels on same page.
	# Save this page and parse out required ch each time when requested.
	#
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("ListingData.getChannel() dayDelta: %s chID=%s fileDate=%s" % (dayDelta,chID,fileDate))
		if dayDelta < 0 or dayDelta > 6:
			return []
		progList = []
		lastStartTime = 0 

		# 1 single file contains all channels for required day.
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (self.name, fileDate))
		if not fileExist(dataFilename):
			# translate dayDelta to dayname
			# find today weekday
			# convert today wday + requested dayDelta to a weekday name
			lookupDayDelta = time.localtime().tm_wday + dayDelta
			if lookupDayDelta >= 7:
				lookupDayDelta -= 7
			debug("lookupDayDelta=%s" % lookupDayDelta)

			try:
				url = urlparse.urljoin(self.CHANNEL_URL,self.DAYS[lookupDayDelta])
			except:
				url = self.CHANNEL_URL

			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		doc = doc.decode('latin-1','replace')
		# no desc from this site at present. its fetched as required from a link
		# time, linkID, title
		regex = '>(\d+:\d+).*?<a href="(.*?)".*?rel=.*?>(.*?)<'		# 07/04/09
		matches = parseDocList(doc, regex, 'href="/kanal/'+chID, '</a></li> </ul> </div>')
		if matches:
			for match in matches:
				desc = ''
				startTime = match[0]
				link = match[1]
				title = decodeEntities(cleanHTML(match[2]))
				if title and startTime:
					descLink = urlparse.urljoin(self.DESC_URL, link)

					# convert starttime to secs since epoch
					secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
					lastStartTime = secsEpoch
					progList.append( {
							TVData.PROG_STARTTIME : float(secsEpoch),
							TVData.PROG_ENDTIME : 0,
							TVData.PROG_TITLE : title,
							TVData.PROG_DESC : desc,
							TVData.PROG_DESCLINK : descLink
						} )
					if DEBUG:
						print progList[-1]

			progList = setChannelEndTimes(progList)		# update endtimes

		if not progList:
			deleteFile(dataFilename)
			deleteFile(filename)
		return progList

	#
	# Download url and regex parse it to extract desc.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return getDescriptionLink(link, '<!-- PLOT -->(.*?)<!')		# 13/08/08
