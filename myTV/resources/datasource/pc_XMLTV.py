############################################################################################################
# TV Data source: XMLTV
# Notes:
# On the remote PC use xmltv.exe 'tv_grab_<country_code>.txt' to create an xmltv file (eg xmltv.xml)
#
# REVISION HISTORY:
# 10/09/07 - Created (from pc_tsreader)
# 11/08/08 - Updated for myTV v1.18
# 07/01/09 - Fix. channels regex error
############################################################################################################

from mytvLib import *
from smbLib import ConfigSMB, smbConnect, smbFetchFile, parseSMBPath, isNewSMBFile

import xbmcgui, re, time, os, smb
from string import split

__language__ = sys.modules["__main__"].__language__

CHANNELS_REGEX = 'channel id="(.*?)".*?display-name.*?>(.*?)<'
CHANNEL_REGEX = 'start="($DATE\d\d\d\d\d\d).*?channel="$CHID".*?title.*?>(.*?)<'
XMLTV_FILE = 'xmltv.xml'

class ListingData:
	def __init__(self, cache):
		debug("ListingData().__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.channelListURL = ""
		self.channelURL = ""
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.localSMBFile = os.path.join(cache, XMLTV_FILE)
		self.isConfigured = False
		self.checkedRemoteFileToday = False


	def getName(self):
		return self.name

	############################################################################################################
	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	############################################################################################################
	def getChannels(self):
		debug("ListingData.getChannels()")
		if not self.isConfigured:
			return []

		channelList = []
		# fetch file if not exists
		if not fileExist(self.CHANNELS_FILENAME):
			# if no local XML file, fetch from SMB
			if not fileExist(self.localSMBFile):
				self.getRemoteFile()

			# extract data from file using regex - this is specific to this file format
			data = readFile(self.localSMBFile)
			if data:
				matches = findAllRegEx(data, CHANNELS_REGEX)
				channelList = writeChannelsList(self.CHANNELS_FILENAME, matches)
		else:
			# read in [channel id, channel name]
			channelList = readChannelsList(self.CHANNELS_FILENAME)

		return channelList


	# download channel data, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("> ListingData.getChannel() dayDelta: %s chID=%s fileDate=%s" % (dayDelta,chID,fileDate))
		progList = []

		if not self.checkedRemoteFileToday:
			self.getRemoteFile(False) # fetch only if newer
			self.checkedRemoteFileToday = True

		if fileExist(self.localSMBFile):
			progList = self.createChannelFiles(chID, fileDate)
		else:
			debug("file missing " + self.localSMBFile)

		debug("< getChannel()")
		return progList

	############################################################################################################
	# create a SMB connection and fetch remote file
	############################################################################################################
	def getRemoteFile(self, fetchAlways=True):
		debug("> ListingData().getRemoteFile() fetchAlways=%s" % fetchAlways)
		downloaded = False

		if not self.connectionError:
			if not self.remote:
				self.remote, self.remoteInfo = smbConnect(self.smbIP, self.smbPath)

			if self.remote and self.remoteInfo:
				if fetchAlways or isNewSMBFile(self.remote, self.remoteInfo, self.localSMBFile, self.smbRemoteFile):
					downloaded = smbFetchFile(self.remote, self.remoteInfo, self.localSMBFile, self.smbRemoteFile, silent=False)
					if not downloaded:
						self.connectionError = True
					else:
						self.highestDate = 0	#reset
			else:
				self.connectionError = True

		debug("< ListingData.getRemoteFile() downloaded=%s connectionError=%s" % (downloaded, self.connectionError))
		return downloaded


	# determine highest start date for any channel.
	# this will help prevent unnwanted processing when curr. date nearing end of
	# dates contained with XML
#	def findHeighestStartDate(self, data):
#		debug("> findHeighestStartDate() current self.highestDate="+str(self.highestDate))
#		regex = 'start=\"(\d\d\d\d\d\d\d\d)'
#		matches = findAllRegEx(data, regex)
#		if matches:
#			matches.sort()
#			lastMatch = int(matches[-1])			# get last in list
#			if lastMatch > self.highestDate:
#				self.highestDate = lastMatch
#		debug("< findHeighestStartDate() new self.highestDate="+str(self.highestDate))

		
	############################################################################################################
	# extract data from file using regex - this is specific to TSReader file format
	############################################################################################################
	def createChannelFiles(self, chID, searchDate):
		debug("> ListingData.createChannelFiles() chID=%s  searchDate=%s" % (chID, searchDate))

		progList = []
		dialogProgress.update(0, __language__(312))
		data = readFile(self.localSMBFile)
		regex = CHANNEL_REGEX.replace('$DATE',searchDate).replace('$CHID',chID)
		matches = findAllRegEx(data, regex)
		if matches:
			for prog in matches:
				startDateTime = prog[0]
				title = decodeEntities(prog[1])

				# calc programme start time in secs since epoch based on programme date
				startTimeSecs = time.mktime(time.strptime(startDateTime,"%Y%m%d%H%M%S"))
				progList.append( {
						TVData.PROG_STARTTIME : float(startTimeSecs),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : title
					} )

			if progList:
				progList = setChannelEndTimes(progList)		# update endtimes

		del data
		debug("< ListingData.createChannelFiles() progs count=%s" % len(progList))
		return progList

	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)
		success = False
		CONFIG_SECTION = 'DATASOURCE_' + self.getName()
		self.remote = None
		self.remoteInfo = None
		self.smbIP = None
		self.smbPath = None
		self.smbRemoteFile = None
		self.connectionError = False
		self.highestDate = 0

		configSMB = ConfigSMB(config, CONFIG_SECTION, self.name, fnDefaultValue=XMLTV_FILE)
		if reset:
			configSMB.ask()

		smbDetails = configSMB.checkAll(silent=True)
		if smbDetails:
			self.smbIP, self.smbPath, self.smbRemoteFile = smbDetails
			self.isConfigured = True

		debug("< ListingData.config() self.isConfigured=%s" % self.isConfigured)
		return self.isConfigured

