############################################################################################################
# TV Data source: au_OzTivo
#
# Notes:
# Provides Australia tv data from http://xmltv.locost7.info in XMLTV format
#
# CHANGELOG
# 29-07-08 Created
# 22-08-08 unzip moved into bbbLib.py
############################################################################################################

from mytvLib import *
from bbbGUILib import *
import mytvGlobals

import xbmcgui, re, time
from string import split, replace, find, rfind, atoi, zfill
from os import path
import gc	# garbage collection

__language__ = sys.modules["__main__"].__language__

# DO NOT CHANGE THIS CODE - IT IS NOW CONFIGURABLE ONLY THROU MYTV CONFIG MENU !!
REGIONS = [
'ACT', 
'Adelaide',					# SA - Adelaide
'Brisbane',						# Queensland - Brisbane
'CentralCoastNSW',
'Darwin',						# NT - Darwin
'EasternVictoria',
'Geelong',
'GoldCoast',
'Hobart'	,					# Tasmania - Hobart
'Melbourne'	,				# Victoria - Melbourne
'Newcastle',
'Perth'	,					# WA - Perth
'RegionalQLD',
'RegionalWA',
'SouthEastSA',
'SouthernNSW',
'WesternVictoria'
]

class ListingData:
	def __init__(self, cache):
		debug("> ListingData.__init__")

		# EG channels URL
		# http://xmltv.locost7.info/Adelaide

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FN= os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.BASE_URL = 'http://xmltv.locost7.info/'
		self.isConfigured = False
		self.lastUpdate = 0

		debug("< __init__")

	def getName(self):
		return self.name

	def setup(self):
		debug("ListingData.setup()")
		self.CHANNEL_URL = self.BASE_URL + '%s/Oztivo%s.zip' % (self.region,self.region)
		self.ZIP_FN = os.path.join(self.cache, os.path.basename(self.CHANNEL_URL))
		self.xmlFN = ""
		debug("CHANNEL_URL=%s\ZIP_FN=%s" % ( self.CHANNEL_URL, self.ZIP_FN) )

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("> ListingData.getChannels()")

		channels = []
		if not fileExist(self.CHANNELS_FN):
			# get todays data file and extract channels from that
			dialogProgress.create(self.name, __language__(212))
			self.lastUpdate = self.getLastUpdate()
			if self.lastUpdate:
				self.xmlFN = os.path.join(self.cache, "%s_%s.xml" % (self.region, self.lastUpdate))
				if self.downloadZip():
					# use regex, its quicker !
					doc = readFile(self.xmlFN)
					matches = findAllRegEx(doc, 'Channel id="(.*?)".*?name>(.*?)<')	# chID, chName
					if matches:
						for chID, chName in matches:
							channels.append([chID, chName])
						channels = writeChannelsList(self.CHANNELS_FN, channels)

				self.xmlFN = "" # cancel xml filename will cause it to process it
			dialogProgress.close()
		else:
			channels = readChannelsList(self.CHANNELS_FN)

		debug("< ListingData.getChannels() ch count=%s" % len(channels))
		return channels

	# get current region archive, unpack and rename using todays date
	def downloadZip(self):
		debug("> ListingData.downloadZip()")
		success = False
		zipBasename = os.path.basename(self.ZIP_FN)
		dialogProgress.update(0, __language__(303), self.CHANNEL_URL, zipBasename )
#		if fileExist(self.ZIP_FN) or fetchURL(self.CHANNEL_URL, self.ZIP_FN, isBinary=True):
		if fetchURL(self.CHANNEL_URL, self.ZIP_FN, isBinary=True):
			# unpack archive
			success, installed_path = unzip(self.cache, self.ZIP_FN, False, __language__(315))
			if success:
				try:
					fromFN = os.path.join(self.cache, self.region + '.xml')
					deleteFile(self.xmlFN)
					debug("XML rename %s to %s" % (fromFN, self.xmlFN))
					os.rename(fromFN, self.xmlFN)
					success = fileExist(self.xmlFN)
				except:
					handleException("downloadZip() rename file")

		if not success:
			messageOK("Download File Failed!", self.CHANNEL_URL, zipBasename)
			
		debug("< ListingData.downloadZip() success=%s" % success)
		return success

	# download the lastUpdate file which contains a date eg. Mon 29/7/08
	def getLastUpdate(self):
		debug("> ListingData.getLastUpdate()")
		lastUpdate = 0
		url = self.BASE_URL + 'lastupdate.txt'
		dialogProgress.update(0, "Fetching LastUpdate date ...", url, " ")
		doc = fetchURL(url)
#		doc = 'Fri 01/08/2008'
		if doc:
			try:
				tm = time.strptime(strip(doc),"%a %d/%m/%Y")						# string to time_tm
				lastUpdate =  int(time.strftime("%Y%m%d", tm))				# tm to formatted str, to int
			except:
				pass

		if not lastUpdate:
			messageOK("LastUpdate Download Failed!","Failed to get Last Update Date.", url)
		debug("< ListingData.getLastUpdate() lastUpdate=%s" % lastUpdate)
		return lastUpdate

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
		if self.xmlFN and self.lastUpdate and fileExist(self.xmlFN):
			debug("already have xmlFN and lastUpdate and fileexists, dont process again, return empty")
			return []	# empty

		progList = []
		DATE_TIME_SZ = 12
		DATE_SZ = 8
		logFreeMem("getChannel() start")

		# get last online update date
		self.xmlFN = ""
		if not self.lastUpdate:
			self.lastUpdate = self.getLastUpdate()
			if not self.lastUpdate:
				return None	# error

		debug("find a xml file thats newer that LastUpdate date: %s" % self.lastUpdate)
		files = listDir(self.cache, ".xml", "%s_\d+" % self.region)
		files.reverse()
		debug("XML files available=%s" % files)
		for f in files:
			if (int(f[-DATE_SZ:]) >= self.lastUpdate):		# compare YYYYMMDD from end of filename
				self.xmlFN = os.path.join(self.cache, f + '.xml')
				break

		if not self.xmlFN:
			debug("no XML newer than %s, download latest ZIP" % self.lastUpdate)
			self.xmlFN = os.path.join(self.cache, "%s_%s.xml" % (self.region, self.lastUpdate))
			if not self.downloadZip():	# DL , unzip , rename to todays xml
				return None	# error

		dialogProgress.update(0, "Parsing XML file:", self.xmlFN )
		xml = readFile(self.xmlFN)
		if not xml:
			debug( "XML file empty!")
			return []
		logFreeMem("getChannel() after read XML")

		# process all channels all dates in XML, so we don't have to do it again
		saveChannels = {}
		CHANNEL_RE = 'programme start="(\d\d\d\d\d\d\d\d\d\d\d\d).*?stop="(\d\d\d\d\d\d\d\d\d\d\d\d).*?channel="(.*?)".*?title>(.*?)</title>(.*?)</programme'
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
					title = decodeEntities(match[3])
					otherInfo = decodeEntities(match[4])
					startDate = startDateTime[:DATE_SZ]
					if not startDateTime or not title or not progChID:
						continue

					# look for other data
					desc = searchRegEx(otherInfo, 'desc>(.*?)</')
					subTitle = searchRegEx(otherInfo, 'sub-title>(.*?)</')
					genre = searchRegEx(otherInfo, 'category>(.*?)</')

					# convert to secs
					startTimeSecs = time.mktime(time.strptime(startDateTime,"%Y%m%d%H%M"))
					stopTimeSecs = time.mktime(time.strptime(stopDateTime,"%Y%m%d%H%M"))

					progInfo = {
							TVData.PROG_STARTTIME : float(startTimeSecs),
							TVData.PROG_ENDTIME : float(stopTimeSecs),
							TVData.PROG_TITLE : title,
							TVData.PROG_DESC : desc,
							TVData.PROG_GENRE : genre,
							TVData.PROG_SUBTITLE : subTitle
						}
#					print "%s_%s %s" % (progChID, startDate, progInfo)

					if progChID == chID and startDate == fileDate:
						progList.append(progInfo)
					else:
						chid_date = "%s_%s" % (progChID, startDate)
						if saveChannels.has_key(chid_date):
							saveChannels[chid_date].append(progInfo)
						else:
							saveChannels[chid_date] = [ progInfo ]
				except:
					print "parse error %s" % match

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
		# whcih will prevent it from attempting to find/parse for it on next start.
		if not progList:
			startTimeSecs = time.mktime(time.strptime(time.strftime(fileDate+"000000"),"%Y%m%d%H%M%S"))
			stopTimeSecs = startTimeSecs + TVTime.DAY_SECS
			progList = [ createEmptyProg(startTimeSecs, stopTimeSecs, True) ]

		logFreeMem("getChannel() end")
		return progList


	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		return ''

	############################################################################################################
	# load, if not exist ask, then save
	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)

		CONFIG_SECTION = 'DATASOURCE_' + self.name
		CONFIG_KEY_REGION = 'region'
		self.region = mytvGlobals.config.action(CONFIG_SECTION, CONFIG_KEY_REGION)

		if reset or not self.region:
			try:
				selectedPos = REGIONS.index(self.region)
			except:
				selectedPos = 0
			selectDialog = DialogSelect()
			selectDialog.setup("Region:", width=300, rows=len(REGIONS), panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(REGIONS, selectedPos)
			if selectedPos >= 0:
				self.region = REGIONS[selectedPos]
				mytvGlobals.config.action(CONFIG_SECTION, CONFIG_KEY_REGION, self.region, mode=ConfigHelper.MODE_WRITE)
				deleteFile(self.CHANNELS_FN)

		if self.region:
			self.isConfigured = True
			self.setup()
		else:
			self.isConfigured = False
		debug("< ListingData.config() isConfigured=%s" % self.isConfigured)
		return self.isConfigured


