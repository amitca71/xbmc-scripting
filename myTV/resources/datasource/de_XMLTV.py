############################################################################################################
# TV Data source: de_XMLTV
#
# Notes:
# Provides (limited) German tv data from http://xmltv.info
#
# CHANGELOG
# 22-08-08 Created
############################################################################################################

from mytvLib import *
from bbbGUILib import *

import xbmcgui, re, time
from string import split, replace, find, rfind, atoi, zfill
from os import path
import gc	# garbage collection

__language__ = sys.modules["__main__"].__language__

class ListingData:
	def __init__(self, cache):
		debug("> ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FN = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.BASE_URL = 'http://static.xmltv.info/'
		self.ZIP_URL = self.BASE_URL + 'tv.xml.zip'
		self.ZIP_FN = os.path.join(cache, 'tv_%s.zip' % self.getTodayDate())
		self.XML_FN = ""

		debug("< __init__")

	def getName(self):
		return self.name

	def getTodayDate(self):
		return time.strftime("%Y%m%d", time.localtime())	# YYYYMMDD

	def getXMLFilename(self):
		return os.path.join(self.cache, 'tv_%s.xml' % self.getTodayDate())

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("> ListingData.getChannels()")

		channels = []
		if not fileExist(self.CHANNELS_FN):
			# get XML file and extract channels from that
			dialogProgress.create(self.name, __language__(212))
			self.XML_FN = self.getXMLFilename()
			if self.downloadZip():
				doc = readFile(self.XML_FN)
				# use regex, its quicker !
				matches = findAllRegEx(doc, 'channel id="(.*?)".*?name.*?>(.*?)<')	# chID, chName
				if matches:
					for chID, chName in matches:
						channels.append([chID, chName])
					channels = writeChannelsList(self.CHANNELS_FN, channels)
				del doc
			self.XML_FN = ""
			dialogProgress.close()
		else:
			channels = readChannelsList(self.CHANNELS_FN)

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

		# if we have the xml filename then we've prev got latest xml and processed it.
		# no new data will be found from re-processing it, so return empty
		if self.XML_FN:
			debug("XML already processed, return empty")
			return []	# empty

		progList = []
		DATE_TIME_SZ = 12
		DATE_SZ = 8
		logFreeMem("getChannel() start")

		# get last online update date
		self.XML_FN = self.getXMLFilename()
		if not fileExist(self.XML_FN) and not self.downloadZip():
			return None	# error

		dialogProgress.update(0, __language__(312), self.XML_FN )
		xml = readFile(self.XML_FN)
		if not xml:
			debug( "XML file empty!")
			return []
		logFreeMem("getChannel() after read XML")

		# process all channels all dates in XML, so we don't have to do it again
		saveChannels = {}
		CHANNEL_RE = 'programme start="(\d+).*?stop="(\d+).*?channel="(.*?)".*?title.*?>(.*?)</t'
		channelList = readChannelsList(self.CHANNELS_FN)
		matches = findAllRegEx(xml, CHANNEL_RE)
		if matches:
			debug("programme matches=%s" % len(matches) )
			for match in matches:
				try:
#					print match
					startDateTime = match[0]
					stopDateTime = match[1]
					progChID = match[2]
					title = decodeEntities(unicodeToAscii(match[3]))	#.decode('utf8','replace')
					startDate = startDateTime[:DATE_SZ]
					if not startDateTime or not title or not progChID:
						continue

					# convert to secs
					startTimeSecs = time.mktime(time.strptime(startDateTime,"%Y%m%d%H%M%S"))
					stopTimeSecs = time.mktime(time.strptime(stopDateTime,"%Y%m%d%H%M%S"))

					progInfo = {
							TVData.PROG_STARTTIME : float(startTimeSecs),
							TVData.PROG_ENDTIME : float(stopTimeSecs),
							TVData.PROG_TITLE : title
						}

					if progChID == chID and startDate == fileDate:
						progList.append(progInfo)			# requested channel
					else:
						chid_date = "%s_%s" % (progChID, startDate)
						if saveChannels.has_key(chid_date):
							saveChannels[chid_date].append(progInfo)
						else:
							saveChannels[chid_date] = [ progInfo ]
				except:
					print "parse error"
					handleException()

			# save data to flat chID / date file
			dialogProgress.update(0, "Saving files ...")
			for chid_date, progs in saveChannels.items():
				# parse chid_yyymmdd
				progChID = chid_date[:-(DATE_SZ+1)]			# extract chID
				startDate = chid_date[-DATE_SZ:]			# extract yyyymmdd
				fn = os.path.join(self.cache, "%s_%s.dat" % (progChID, startDate))
				saveChannelToFile(progs, fn)

		del channelList
		del saveChannels
		gc.collect()
		# if no progs for chID / date, create empty prog, this will be saved to file
		# which will prevent it from attempting to find/parse for it on next start.
		if not progList:
			debug("no progs, make empty channel")
			startTimeSecs = time.mktime(time.strptime(time.strftime(fileDate+"000000"),"%Y%m%d%H%M%S"))
			stopTimeSecs = startTimeSecs + TVTime.DAY_SECS
			progList = [ createEmptyProg(startTimeSecs, stopTimeSecs, True) ]
#		elif DEBUG:
#			print progList

		logFreeMem("getChannel() end")
		return progList


	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		return ''

	#
	# get current region archive, unpack and rename using todays date
	#
	def downloadZip(self):
		debug("> ListingData.downloadZip()")
		success = False
		zipBasename = os.path.basename(self.ZIP_FN)
		dialogProgress.update(0, __language__(303), self.ZIP_URL, zipBasename )
#		if fileExist(self.ZIP_FN) or fetchURL(self.ZIP_URL, self.ZIP_FN, isBinary=True):
		if fetchURL(self.ZIP_URL, self.ZIP_FN, isBinary=True):
			# unpack archive
			success, installed_path = unzip(self.cache, self.ZIP_FN, False, __language__(315))
			if success:
				try:
					# rename unpacked xml file to one with date
					deleteFile(self.XML_FN)
					debug("XML rename %s to %s" % (installed_path, self.XML_FN))
					os.rename(installed_path, self.XML_FN)
					success = fileExist(self.XML_FN)
				except:
					handleException("downloadZip() rename file")

		if not success:
			messageOK("Download File Failed!", self.ZIP_URL, zipBasename)
			
		debug("< ListingData.downloadZip() success=%s" % success)
		return success


