############################################################################################################
# TV Data source: TSReader
# Notes:
# parses an XMLTV file from TSReader
#
# REVISION HISTORY:
# 01/11/05 Created
# 07/11/05 2nd attempt :)
# 12/02/07 Now uses smbLib, several smb funcs removed
#          GUI config added and overhauled to make it faster.
############################################################################################################

import time, os, smb
from mytvLib import *
from smbLib import ConfigSMB, smbConnect, smbFetchFile, isNewSMBFile
import mytvGlobals

__language__ = sys.modules["__main__"].__language__

CHANNELS_REGEX = 'channel id="(.*?)".*?display-name lang="en">(.*?)<'
CHANNEL_REGEX = 'start="(\d\d\d\d\d\d\d\d)(\d\d\d\d\d\d)" stop="(\d+)".*?title>(.*?)<.*?desc>(.*?)<'
XMLTV_FILE = 'xmltv.xml'

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.localSMBFile = os.path.join(cache,XMLTV_FILE)
		self.checkedRemoteFileToday = False
		self.connectionError = False
		self.isConfigured = False

		# smb vars
		self.remote = None
		self.remoteInfo = None
		self.smbIP = None
		self.smbPath = None
		self.smbRemoteFile = None

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("> ListingData.getChannels()")
		channelList = []
		if self.isConfigured:
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

		debug("< ListingData.getChannels()")
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
		if self.isConfigured:
			if not self.checkedRemoteFileToday:
				self.getRemoteFile(False) # fetch only if newer
				self.checkedRemoteFileToday = True

			if fileExist(self.localSMBFile):
				progList = self.createChannelFiles(chID, int(fileDate))
			else:
				debug("file missing " + self.localSMBFile)

		debug("< ListingData.getChannel()")
		return progList

	############################################################################################################
	# determine highest start date for any channel.
	# this will help prevent unnwanted processing when curr. date nearing end of
	# dates contained with XML
	############################################################################################################
#	def findHeighestStartDate(self, data):
#		debug("> ListingData.findHeighestStartDate() current self.highestDate="+str(self.highestDate))
#		regex = 'start=\"(\d\d\d\d\d\d\d\d)'
#		matches = findAllRegEx(data, regex)
#		if matches:
#			matches.sort()
#			lastMatch= int(matches[-1])
#			if lastMatch > self.highestDate:
#				self.highestDate = lastMatch
#		debug("< ListingData.findHeighestStartDate() new self.highestDate="+str(self.highestDate))

		
	############################################################################################################
	# extract data from file using regex - this is specific to TSReader file format
	def createChannelFiles(self, chID, searchDate):
		debug("> ListingData.createChannelFiles() chID=%s  searchDate=%s" % (chID, searchDate))
		progList = []

		dialogProgress.update(0, __language__(312))
		data = readFile(self.localSMBFile)
		if data:
			matches = parseDocList(data, CHANNEL_REGEX, 'channel id="'+chID,'channel id=')
			for prog in matches:
				startDate = prog[0]							# YYYYMMDD
				if int(startDate) < searchDate:
					continue
				elif (int(startDate) > searchDate):
					break
				else:
					startTime = prog[1]						# HHMMSS
					endDateTime = prog[2]					# YYYYMMDDHHMM
					title = decodeEntities(prog[3])
					desc = decodeEntities(prog[4])
		#			print startDate, startTime, endDateTime, title
					# calc programme start time in secs since epoch based on programme date
					startTimeSecs = time.mktime(time.strptime(startDate+startTime,"%Y%m%d%H%M%S"))
					endTimeSecs = time.mktime(time.strptime(endDateTime,"%Y%m%d%H%M%S"))
					progList.append( {
							TVData.PROG_STARTTIME : float(startTimeSecs),
							TVData.PROG_ENDTIME : float(endTimeSecs),
							TVData.PROG_TITLE : title,
							TVData.PROG_DESC : desc
						} )

			if progList:
				progList = setChannelEndTimes(progList)		# update endtimes

		del data
		debug("< ListingData.createChannelFiles() progs count=%s" % len(progList))
		return progList

	############################################################################################################
	# create a SMB connection and fetch remote file
	def getRemoteFile(self, fetchAlways=True):
		debug("> ListingData().getRemoteFile() fetchAlways=%s" % fetchAlways)
		downloaded = False

		if not self.connectionError:
			if not self.remote or not self.remoteInfo:
				self.remote, self.remoteInfo = smbConnect(self.smbIP, self.smbPath)

			if self.remote and self.remoteInfo:
				if fetchAlways or isNewSMBFile(self.remote, self.remoteInfo, self.localSMBFile, self.smbRemoteFile):
					downloaded = smbFetchFile(self.remote, self.remoteInfo, self.localSMBFile, self.smbRemoteFile, silent=False)
					if downloaded == None:
						self.connectionError = True
			else:
				self.connectionError = True

		debug("< ListingData.getRemoteFile() downloaded=%s connectionError=%s" % (downloaded, self.connectionError))
		return downloaded


	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)

		title = "%s - %s" % (self.name, __language__(976))
		configSMB = ConfigSMB(title, fnTitle=__language__(977), fnDefaultValue=XMLTV_FILE)
		if reset:
			configSMB.ask()

		smbDetails = configSMB.checkAll(silent=True)
		if smbDetails:
			self.smbIP, self.smbPath, self.smbRemoteFile = smbDetails
			self.isConfigured = True
		else:
			self.isConfigured = False
		self.connectionError = False	# will allow a retry after a config change

		debug("< ListingData.config() isConfigured=%s" % self.isConfigured)
		return self.isConfigured
