############################################################################################################
# TV Data source: 
# Notes:
# Pulls DM cretaed day files from Dreambox Enigma2.
#
# REVISION HISTORY:
# 20/02/09 - Created
############################################################################################################

from mytvLib import *
from smbLib import ConfigSMB, smbConnect, smbFetchFile, listDirSMB

import xbmcgui, re, time, os, smb
from string import split

__language__ = sys.modules["__main__"].__language__

CHANNELS_REGEX = '^(\d+)=[1|2|3],(.*?)[,\n]'
CHANNEL_REGEX = '^(\d+)###(.*?)###(.*?)###(.*?)$'
DM_FILENAME_REGEX = 'australiasat###(\w+)_(\d+)-(\d+)###(\d+)$'
DAY_FILENAME = 'australiasat###$CHNAME_$CHID_DM-$CHID###$DATE'
DM_CONF_FILENAME = "australiasat-channel_list.conf"

class ListingData:
	def __init__(self, cache):
		debug("ListingData().__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.channelListURL = ""
		self.channelURL = ""
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
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
			# fetch from SMB
			localFN = os.path.join(self.cache, DM_CONF_FILENAME)
			self.getRemoteFile(DM_CONF_FILENAME, localFN)

			# extract data from file using regex - this is specific to this file format
			data = readFile(localFN)
			if data:
				matches = parseDocList(data, CHANNELS_REGEX, "[channel_list]")
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

		if not self.checkedRemoteFileToday and not self.connectionError:
			if not self.remote or not self.remoteInfo:
				self.remote, self.remoteInfo = smbConnect(self.smbIP, self.smbPath)

			# fetch all DM day files, after today
			remoteFileList = listDirSMB(self.remote, self.remoteInfo)
			if remoteFileList:
				# filter out unwanted files, keeping DM day files >= today
				dayFilesList = []
				for sharedFile in remoteFileList:
					fn = sharedFile.get_longname()
					if not fn.startswith("australiasat###"): continue
					dayFilesList.append(fn)
					# store the full fn of the day file if it matches what were after


				# fetch all files we dont have
				for fn in dayFilesList:
					try:
						match = re.search(DM_FILENAME_REGEX, fn)
						fnChID = match.group(3)
						fnDate = match.group(4)
					except:
						continue
					channelFN = os.path.join(DIR_CACHE, "%s_%s.dat" % (fnChID,fnDate))
					if not fileExist(channelFN):
						dataFN = os.path.join(self.cache, fn)
						if self.getRemoteFile(fn, dataFN):
							self.createChannelFiles(dataFN, channelFN)
							deleteFile(dataFN)

			self.checkedRemoteFileToday = True

		if fileExist(filename):
			progList = loadChannelFromFile(filename)

		debug("< getChannel()")
		return progList


	############################################################################################################
	# extract data from file using regex - this is specific to TSReader file format
	############################################################################################################
	def createChannelFiles(self, dataFN, channelFN):
		debug("> ListingData.createChannelFiles() dataFN=%s channelFN=%s" % (dataFN,channelFN))

		progList = []
		dialogProgress.update(0, __language__(312))
		data = readFile(dataFN)
		matches = findAllRegEx(data, CHANNEL_REGEX)
		if matches:
			for prog in matches:
				progList.append( {
						TVData.PROG_STARTTIME : float(prog[0]),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : decodeEntities(prog[2]),
						TVData.PROG_DESC : decodeEntities(prog[3])
					} )

			if progList:
				progList = setChannelEndTimes(progList)		# update endtimes
				saveChannelToFile(progList, channelFN)

		del data
		debug("< ListingData.createChannelFiles() progs count=%s" % len(progList))
		return progList


	############################################################################################################
	# create a SMB connection and fetch remote file
	############################################################################################################
	def getRemoteFile(self, remoteFilename, localFilename='', fetchAlways=True):
		debug("> ListingData().getRemoteFile() fetchAlways=%s" % fetchAlways)
		downloaded = False

		if not self.connectionError:
			if not self.remote:
				self.remote, self.remoteInfo = smbConnect(self.smbIP, self.smbPath)

			if self.remote and self.remoteInfo:
				if not localFilename:
					localFilename = os.path.join(self.cache, remoteFilename)

				if fetchAlways or isNewSMBFile(self.remote, self.remoteInfo, localFilename, remoteFilename):
					downloaded = smbFetchFile(self.remote, self.remoteInfo, localFilename, remoteFilename, silent=False)
					if not downloaded:
						self.connectionError = True
			else:
				self.connectionError = True

		debug("< ListingData.getRemoteFile() downloaded=%s connectionError=%s" % (downloaded, self.connectionError))
		return downloaded


	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)
		CONFIG_SECTION = 'DATASOURCE_' + self.getName()
		self.remote = None
		self.remoteInfo = None
		self.smbIP = None
		self.smbPath = None
		self.smbRemoteFile = None
		self.connectionError = False

		configSMB = ConfigSMB(config, CONFIG_SECTION, self.name, fnDefaultValue=DAY_FILENAME)
		if reset:
			configSMB.ask()

		smbDetails = configSMB.checkAll(silent=True)
		if smbDetails:
			self.smbIP, self.smbPath, self.smbRemoteFile = smbDetails
			self.isConfigured = True

		debug("< ListingData.config() self.isConfigured=%s" % self.isConfigured)
		return self.isConfigured

