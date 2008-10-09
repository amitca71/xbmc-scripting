############################################################################################################
# TV Data source: WirtualnaPolska (formally wppl)
# Notes:
# Initially written by XBMC forum member 'smuto'.
# Provides Polish tv data, From http://tv.wp.pl
# ChangeLog:
# 14/10/06 Fix: renamed, regex & getDescription() decode change - thanks to smuto
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from os import path

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__()")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		baseURL = "http://tv.wp.pl/"
		self.channelListURL = baseURL + "katn,Lista kana%B3%F3w,programy.html"
		self.channelURL = baseURL + "program.html?T[date]=$DATE&T[station]=$CHID&T[category]=ALL&T[time]=$DAYDELTA&ticaid=12aea"
		self.linkURL = baseURL + "opis.html?pr_tele_id="
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		regex = "option.*?value=\"(\d+)\">(.*?)<"		# 12/08/08
		startStr='Najpopularniejsze'
		endStr='</select>'
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME,regex,startStr,endStr)


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
			formatTime = time.strptime(fileDate,"%Y%m%d")
			fetchDate = time.strftime("%Y-%m-%d", formatTime)
			url = self.channelURL.replace("$DATE",fetchDate).replace("$CHID",chID).replace("$DAYDELTA",str(dayDelta))
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		debug("regex data  ...")
		doc = doc.decode('ISO 8859-2','replace')
		# finds time, then href OR just <b>, get text, find SGinfo, get text
		# (TIME)(TITLE)(<DESC LINK>)(<DESC>)
		regex = "nowrap><b>(.+?)</b>.*?(?:<b><a href.*?id=(\d+)\'.*?\">|<b><span.*?>)(.+?)</.*?SGinfo\">(.*?)<"
		matches = findAllRegEx(doc, regex)
		if matches:
			for match in matches:
				if len(match) != 4:
					# not enough data, ignore
					continue

				# time, link (optional), title, description (optional)
				startTime, descLink, title, desc = match

				# may have empty link and desc
				if descLink == None or not descLink.strip():
					descLink = ''
				else:
					descLink = self.linkURL + descLink

				if desc == None or not desc.strip():
					desc = ''

				# convert starttime to secs since epoch
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = secsEpoch
				progList.append( {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : decodeEntities(title),
						TVData.PROG_DESCLINK : descLink
					} )

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return getDescriptionLink(link, 'id="opis">(.*?)</table', decodeSet='ISO 8859-2')
