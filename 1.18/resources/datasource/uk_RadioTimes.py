############################################################################################################
# TV Data source: RadioTimes
# Notes:
# Mandatory Class name: ListingData
# Mandatory Functions:
#  getChannels()	- Returns a list of all available channels [chID, Ch Name]
#  getChannel()		- Download a requested channel listing, return list of Channel
# NOTES:
# radioTimes provides access to channel raw data, but its 14days in one files, so this needs splitting.
#
# REVISION HISTORY:
# 05-Apr-2005 - Handles Unicode characters
# 20-Nov-2005 - Added. Genre and subTitle support
# 06-08-2008 - Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time, os
from string import split,strip

__language__ = sys.modules["__main__"].__language__

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__()")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.channelListURL = "http://xmltv.radiotimes.com/xmltv/channels.dat"
		self.channelURL = "http://xmltv.radiotimes.com/xmltv/"
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")


	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME ,"(.+?)\|(.+?)$")


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
			return []
		progList = []
		lastDate = ""
		saveFile = None

		# download data file if file doesnt exists
		url = self.channelURL + chID + ".dat"
		todayDate = time.strftime("%Y%m%d",time.localtime())
		todaySecs = time.mktime(time.localtime())

		fn = os.path.join(self.cache, "%s_%s.csv" % (chID, todayDate))
		if not fileExist(fn):
			dialogProgress.update(0, __language__(212))		# downloading channel listing
			doc = fetchURL(url, fn)
		else:
			doc = readFile(fn)

		if not doc:
			debug("empty csv doc")
			return []

		# split data into its own date file
		debug("splitting data to individual date files ...")
		dialogProgress.update(0, __language__(312))		# parsing
		lastStartTime = 0
		saveChannels = {}
		maxFutureSecs = todaySecs + 604800			# forward 7 days
		maxPastSecs = todaySecs - 86400				# back 1 day

		for readLine in doc.split('\n'):
			split = (readLine.decode('latin-1','replace')).split('~')
			try:
				if len(split) < 23:
					debug("rec too short %i %s" % (len(split), split))
					continue
				startDate = split[19]						# position of programme start date in record
				# 29/05/2005 -> 20050529
				reverseDate =  startDate[-4:] + startDate[3:5] + startDate[:2]
				title = decodeEntities(split[0])
				subTitle = decodeEntities(split[2])
				genre = split[16]
				desc = decodeEntities(split[17])
				startTime = split[20]
				endTime = split[21]
				duration = split[22]

				# ignore programme if missing vital information
				if not title or not startTime or not startDate or not endTime:
					print "rec missing data %s" % split
					continue
#				print startDate, startTime, endTime, duration

				# calc programme start time in secs since epoch based on programme date
				startTimeSecs = startTimeToSecs(lastStartTime, startTime, reverseDate)
				lastStartTime = startTimeSecs
				if startTimeSecs > maxFutureSecs:
					debug("break. startTime too far in future, %i > %i" % (startTimeSecs,maxFutureSecs))
					break
				elif startTimeSecs < maxPastSecs:
					debug("ignored. startTime too far in past, %i < %i" % (startTimeSecs, maxPastSecs))
					continue

				if duration and int(duration) != 0:
					duration = int(duration)
					endTimeSecs = startTimeSecs + (duration * 60)	# dur in mins to secs
				else:
					endTimeSecs=0

				progInfo = {
						TVData.PROG_STARTTIME : float(startTimeSecs),
						TVData.PROG_ENDTIME : float(endTimeSecs),
						TVData.PROG_TITLE : title,
						TVData.PROG_SUBTITLE : subTitle,
						TVData.PROG_GENRE : genre,
						TVData.PROG_DESC : desc,
						TVData.PROG_DUR : duration
					}
#				print progInfo

				if reverseDate == fileDate:
					progList.append(progInfo)
				else:
					# store for saving to file
					if saveChannels.has_key(reverseDate):
						saveChannels[reverseDate].append(progInfo)
					else:
						saveChannels[reverseDate] = [ progInfo ]

			except:
				print "parse record idx error ", split
				continue

		# save data to flat chID / date file
		if saveChannels:
			for reverseDate, progs in saveChannels.items():
				fn = os.path.join(self.cache, "%s_%s.dat" % (chID, reverseDate))
				saveChannelToFile(progs, fn)

#		print "progList=", progList
		return progList
