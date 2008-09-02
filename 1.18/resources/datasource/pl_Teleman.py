############################################################################################################
# TV Data source: Teleman (Polish)
# Notes:
# Provides Polish tv data, From www.teleman.pl
# ChangeLog:
# 03/03/08 Created
# 02/06/08 Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.baseURL = "http://www.teleman.pl"
		self.channelListURL = self.baseURL + "/arch-%s.html"
		self.channelURL = self.baseURL + "/arch-%s-%s.html"
		self.CHANNELS_FILENAME = os.path.join(cache, "Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		# lookup channels from today list of available channels
		regex = 'href="/arch-\d+-(\d+).*?>(.*?)<'		# 12/08/08
		date = time.strftime("%Y%m%d", time.localtime())
		url = self.channelListURL % date
		return getChannelsLIB(url, self.CHANNELS_FILENAME, regex, '>Archiwum Programu TV<')


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
			url = self.channelURL % (fileDate, chID)
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		doc = doc.decode('ISO 8859-2','replace')			# utf-8 or latin-1 or iso-8859-2 ???
		debug("processing data ...")
		regex = '>(\d+:\d+).*?href="(.*?)">(.*?)<'		# new 02/05/2008 (smuto)
		matches = findAllRegEx(doc, regex)
		if matches:
			for match in matches:
				try:
					startTime, descLink, title = match

					# may have empty link
					if not descLink or not descLink.strip():
						descLink = ''
					else:
						descLink = self.baseURL + descLink
	#				print startTime, descLink

					# convert starttime to secs since epoch
					secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
					lastStartTime = secsEpoch
					progList.append( {
							TVData.PROG_STARTTIME : float(secsEpoch),
							TVData.PROG_ENDTIME : 0,
							TVData.PROG_TITLE : decodeEntities(title),
							TVData.PROG_DESCLINK : descLink
						} )
				except:
					print "invalid match", match
					handleException()

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title=''):
		debug("ListingData.getLink()")
		regex = 'class="content"(.*?)<div'		# 12/08/08
		return getDescriptionLink(link, regex, decodeSet='ISO 8859-2')
