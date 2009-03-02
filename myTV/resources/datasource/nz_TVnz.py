############################################################################################################
# TV Data source: TVNZ
# Notes:
# Provides NewZealand from www.tvnz.co.nz
#
# CHANGELOG
# =========
# 29/11/05 Created.
# 10/03/08 Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from string import split, replace, find, rfind, atoi, zfill
from os import path

# CHANNELS
channelsListingsSkin = {
'tvone' : ('TV ONE', 'http://tvnz.co.nz/content/tvone_listings_data/tvone_listings_skin?date=$DATE#00:00'),
'tv2' : ('TV2', 'http://tvnz.co.nz/content/tv2_listings_data/tv2_listings_skin?date=$DATE#00:00'),
'tvnz_6' : ('TVNZ 6', 'http://tvnz.co.nz/content/tvnz6_listings_data/tvnz6_listings_skin?date=$DATE#00:00'),
'tvnz_7' : ('TVNZ 7', 'http://tvnz.co.nz/content/tvnz7_listings_data/tvnz7_listings_skin?date=$DATE#00:00')
}

# dict chData is [chName, url, "webpage ch idx as shown on page"]
channelsEpgSkinURL = 'http://tvnz.co.nz/content/listings_data/tvnz_listings_all_skin?date=$DATE#00:00'
channelsEpgSkin = {
	'tv3' : ('TV3', channelsEpgSkinURL, 4),
	'c4tv' : ('C4TV', channelsEpgSkinURL, 5),
	'prime' : ('Prime', channelsEpgSkinURL, 6)
	}

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("> ListingData.getChannels()")
		channels = []
		# channelsListingsSkin
		for item in channelsListingsSkin.items():
			chID, chData = item
			channels.append([chID, chData[0]])		# [chName, url]

		# channelsEpgSkin
		for item in channelsEpgSkin.items():
			chID, chData = item
			channels.append([chID, chData[0]])		# [chName, url, ch page idx]

		debug("< ListingData.getChannels() ch count=%s" % len(channels))
		return channels


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

		# download whole site page if not got data for date
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, fileDate))
		if not fileExist(dataFilename):
			allChannels = {}			# store progs for each channel
			formatTime = time.strptime(fileDate,"%Y%m%d")
			urlDate = time.strftime("%d%m%Y", formatTime)
			if channelsListingsSkin.has_key(chID):
				chURL = channelsListingsSkin[chID][1]
				url = chURL.replace('$DATE', urlDate)
				progList = self.parseListingsSkin(url, fileDate)
			elif channelsEpgSkin.has_key(chID):
				chURL = channelsEpgSkin[chID][1]
				url = chURL.replace('$DATE', urlDate)
				chDisplayIdx = channelsEpgSkin[chID][2]
				progList = self.parseEpgSkin(url, chDisplayIdx, fileDate)
			else:
				debug("unknown chID")
				return None

		return progList


	# get channel data for TVNZ channels
	def parseListingsSkin(self, url, fileDate):
		debug("> parseListingsSkin()")
		progList = []
		lastStartTime = 0

		# FETCH URL
		doc = fetchCookieURL(url)
		if doc and doc != -1:
			# split into progs on channel
			regex = 'id=\"epg_programmes_content_container"(.*?)id=\"footer_spacer'
			doc = searchRegEx(doc, regex, re.DOTALL+re.MULTILINE+re.IGNORECASE)
			progs = split(doc,'class="epg_cell')
			debug("progs count=%s" % len(progs))
			if progs:
				# extract each prog details, some with link some without
				reList = ('href=\"(.*?)\".*?>(.*?)</a>.*?(\d\d:\d\d)<.*?content\">(.*?)</div',			# link
						  '()epg_section_heading\">(.*?)</.*?(\d\d:\d\d)<.*?content\">(.*?)</div',	# no link
						  '()epg_section_heading\">(.*?)</.*?(\d\d:\d\d)<()')						# no content
				for prog in progs:
					# try to match a regex
					for regex in reList:
						matches = re.search(regex, prog, re.DOTALL+re.MULTILINE+re.IGNORECASE)
						if matches:
							descLink = cleanHTML(matches.group(1))
							title = decodeEntities(cleanHTML(matches.group(2)))
							startTime = matches.group(3)
							desc = decodeEntities(cleanHTML(matches.group(4)))
	#						print "FOUND=", startTime, title, descLink, desc
							if startTime and title: 
								# calc programme start time in secs since epoch based on programme date
								startTimeSecs = startTimeToSecs(lastStartTime, startTime, fileDate)
								lastStartTime = startTimeSecs

								progList.append( {
										TVData.PROG_STARTTIME : float(startTimeSecs),
										TVData.PROG_ENDTIME : 0,
										TVData.PROG_TITLE : title,
										TVData.PROG_DESC : desc,
										TVData.PROG_DESCLINK : descLink
									} )
								break		# stop matching regex, goto next prog

				progList = setChannelEndTimes(progList)		# update endtimes

		debug("< parseListingsSkin() prog count: %s" % len(progList))
		return progList


	#
	# Looks at a page that has all channels on it.
	#
	def parseEpgSkin(self, url, chDisplayIdx, fileDate):
		debug("> parseEpgSkin()")
		progList = []
		lastStartTime = 0

		# FETCH URL
		doc = fetchCookieURL(url)
		if doc and doc != -1:
			# extract each prog details, some with link some without
			reList = ('title="(.*?)".*?href="(.*?)".*?(\d+:\d+)',					# link
					  'title="(.*?)".*?()(\d+:\d+)')								# no link

			# split into channels
			regex = 'id=\"epg_index_programmes_container.*?epg_logo_spacer(.*?)id=\"footer_spacer'
			doc = searchRegEx(doc, regex, re.DOTALL+re.MULTILINE+re.IGNORECASE)
			channels = split(doc,'</table>')
			debug("channels count=%s" % len(channels))
			try:
				# split into progs on channel
				progs = split(channels[chDisplayIdx],'class="epg_cell')
				debug("channel progs count=%s" % len(progs))

				# for each prog on channel ...
				for prog in progs:
					# try to match a regex
					for regex in reList:
						matches = re.search(regex, prog, re.DOTALL+re.MULTILINE+re.IGNORECASE)
						if matches:
							title = decodeEntities(cleanHTML(matches.group(1)))
							descLink = matches.group(2)
							startTime = matches.group(3)
#							print "FOUND= ", startTime, title, link
							if startTime and title: 
								# calc programme start time in secs since epoch based on programme date
								startTimeSecs = startTimeToSecs(lastStartTime, startTime, fileDate)
								lastStartTime = startTimeSecs
								progList.append( {
										TVData.PROG_STARTTIME : float(startTimeSecs),
										TVData.PROG_ENDTIME : 0,
										TVData.PROG_TITLE : title,
										TVData.PROG_DESCLINK : descLink
									} )
								break						# dont match on next regex

				# add channels progs
				if progList:
					progList = setChannelEndTimes(progList)	# update endtimes
			except:
				debug("displayed channel missing")

		debug("< parseEpgSkin() prog count: %s" % len(progList))
		return progList

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return ""
