############################################################################################################
# TV Data source: DR.DK (danish)
#
# Notes:
# From http://www.dr.dk/tjenester/programoversigten
#
#
# CHANGELOG
# ---------
# 02/02/06 Created.
# 15/03/06 Fix: replace + with %20 for filename and channel ids
# 10-03-2008 Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from string import split, replace, find, rfind, atoi, zfill
from os import path

class ListingData:
	def __init__(self, cache):

# detalheCanal.aspx?IDcanal=131&amp;data=13/1/2006

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.BASE_URL = "http://www.dr.dk/tjenester/programoversigten/w3c/"
		self.channelListURL = self.BASE_URL + "epg.asp"
		self.channelURL = self.BASE_URL + "inc/channel.aframe?channel=$CHID&seldate=$DAYDELTA&seltime=0"
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME , \
							"NormalLink(?:.*?)channel=(.*?)['\"](?:.*?)>(.*?)<", \
							startStr='KANALER</div', endStr='</form')


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

#		chID = chID.replace('+','%20')
#		filename = filename.replace('+','%20')
		# download data file if file doesnt exists
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, fileDate))
		if not fileExist(dataFilename):
			formatTime = time.strptime(fileDate,"%Y%m%d")
			url = self.channelURL.replace('$CHID',chID).replace('$DAYDELTA',str(dayDelta))
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc
		
		doc = doc.decode('latin-1','replace')
		progsDict = {}
		# PROGS WITH DESC
		regex = "EPG_Toggle(?:.*?)>(\d\d.\d\d)(.*?)<(?:.*?)p_text_border>(.*?)<"
		matches = findAllRegEx(doc, regex)
		for match in matches:
			startTime = decodeEntities(match[0])
			title = decodeEntities(match[1])
			desc = cleanHTML(decodeEntities(match[2])).strip()
#			print startTime, title, desc
			if not startTime or not title:
				continue

			# convert starttime to secs since epoch
			secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
			lastStartTime = secsEpoch
			try:
				progsDict[secsEpoch] = {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title,
						TVData.PROG_DESC : desc
					}
			except:
				pass

		# PROGS WITHOUT DESC - gets all progs, but just keep those not yet seen before,
		# which will be the progs without a desc
		lastStartTime = 0
		regex = ">(\d\d.\d\d)(.*?)<"
		matches = findAllRegEx(doc, regex)
		if matches:
			for match in matches:
				startTime = decodeEntities(match[0])
				title = decodeEntities(match[1])
	#			print startTime, title
				if not startTime or not title:
					continue

				# convert starttime to secs since epoch
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = secsEpoch
				try:
					prog = progsDict[secsEpoch]
				except:
					# not found, add to dict
					progsDict[secsEpoch] = {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title
					}

		# COMBINE ALL PROGS SORTING BY START TIME
		if progsDict:
			debug("combining progDict to make progList, progs=%s" % len(progsDict))
			# sort into startTime order
			keys = progsDict.keys()
			keys.sort()
			# load into progList
			for key in keys:
				progList.append(progsDict[key])

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList


	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return ''
