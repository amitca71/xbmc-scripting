############################################################################################################
# TV Data source: 
# Notes:
# Pulls DM cretaed day files from Dreambox Enigma2.
#
# REVISION HISTORY:
# 20/02/09 - Created
############################################################################################################

import re, time, os, smb
from string import split
from mytvLib import *
from smbLib import ConfigSMB, smbConnect, smbFetchFile, listDirSMB
import mytvGlobals
from pprint import pprint

__language__ = sys.modules["__main__"].__language__

CHANNELS_REGEX = '^(\d+)=[1|2|3],(.*?)[,\n]'
CHANNEL_REGEX = '^(\d+)###(.*?)###(.*?)###(.*?)$'
DM_FILENAME_REGEX = 'australiasat###(.*?)_(\d+)-(\d+)###(\d+)'
DM_CONF_FILENAME = 'australiasat-channel_list.conf'

class ListingData:
	def __init__(self, cache):
		debug("ListingData().__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.isConfigured = False
		self.checkedRemoteFileToday = False
		self.connectionError = False

		# smb vars
		self.remote = None
		self.remoteInfo = None
		self.smbPath = ""

	def getName(self):
		return self.name

	############################################################################################################
	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	############################################################################################################
	def getChannels(self):
		debug("> ListingData.getChannels()")
		channelList = []
		if self.isConfigured:
			# fetch file if not exists
			if not fileExist(self.CHANNELS_FILENAME):
				# fetch from SMB
				remoteFN = "/".join( [self.smbPath, DM_CONF_FILENAME] )
				localFN = os.path.join(self.cache, DM_CONF_FILENAME)
				response = xbmc.executehttpapi("FileCopy(%s,%s)" % (remoteFN, localFN))
				debug("httpapi response=%s" % response)

				# extract data from file using regex - this is specific to this file format
				data = readFile(localFN)
				if data:
					matches = parseDocList(data, CHANNELS_REGEX, "[channel_list]")
					if matches:
						channelList = writeChannelsList(self.CHANNELS_FILENAME, matches)
				deleteFile(localFN)
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

		if self.isConfigured and not self.connectionError and not self.checkedRemoteFileToday:
#			if not self.remote or not self.remoteInfo:
#				self.remote, self.remoteInfo = smbConnect(self.smbIP, self.smbPath)

			# fetch all DM day files for chID
			dialogProgress.update(0, "Querying Dreambox ...", " ", " ")
			time.sleep(.2)
			remoteFileList = []
			response = xbmc.executehttpapi("GetDirectory(%s)" % self.smbPath)
			debug("httpapi response=%s" % response)
			if find(response,'Error') < 0:
				remoteFileList = response.split('<li>')
				MAX_COUNT = len(remoteFileList)
				debug("remoteFileList sz=%d" % MAX_COUNT)
#				if DEBUG:
#					pprint (remoteFileList)
			else:
				messageOK(self.name, __language__(138), self.smbPath)

			if remoteFileList:
				# fetch all DM data files we dont have mytv data files for
				fetchedDMDict = {}
				for count, remoteBMFilename in enumerate(remoteFileList):
					try:
						match = re.search(DM_FILENAME_REGEX, remoteBMFilename.strip())
						if not match: continue
						fnChName = match.group(1)
						fnChID = match.group(2)
						fnDate = match.group(4)

						channelFN = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, "%s_%s.dat" % (fnChID,fnDate)))
						if not fileExist(channelFN):
							remoteBMBasename = os.path.basename(remoteBMFilename.strip())
							localBMFilename = xbmc.makeLegalFilename(os.path.join(self.cache, "DM_%s_%s.dat" % (fnChID,fnDate)))
							percent = int( (count * 100.0) / MAX_COUNT )
							dialogProgress.update(percent, __language__(962), fnChName, remoteBMBasename)

							response = xbmc.executehttpapi("FileCopy(%s,%s)" % (remoteBMFilename, localBMFilename))
							debug("httpapi response=%s" % response)
							if (response and find(response,"OK") >= 0):
								fetchedDMDict[channelFN] = localBMFilename
								self.createChannelFiles(localBMFilename, channelFN, fnDate)
								deleteFile(localBMFilename)
						else:
							debug("not downloaded, file already exists=" + channelFN)
					except:
						print str( sys.exc_info()[ 1 ] )
						print "except during remoteFilename=" + localBMFilename

				# now process all the DM data file into myTV data files
#				pprint (fetchedDMDict.items())
#				MAX_COUNT = len(fetchedDMDict)
#				debug("fetchedDMDict count=%d" % MAX_COUNT)
#				if DEBUG:
#					pprint (fetchedDMDict)
#				count = 0
#				for channelFN, localBMFilename in fetchedDMDict.items():
#					percent = int( (count * 100.0) / MAX_COUNT )
#					dialogProgress.update(percent, __language__(312), \
#										os.path.basename(localBMFilename), os.path.basename(channelFN))
#					self.createChannelFiles(localBMFilename, channelFN, localBMFilename[-8:])
#					count += 1

				# remove all DM files
#				dialogProgress.update(percent, __language__(217), " ", " ")
#				for localBMFilename in fetchedDMDict.values():
#					deleteFile(localBMFilename)

				print "check for filename=" + filename
				if fileExist(filename):
					print "found filename"
					progList = loadChannelFromFile(filename)

			self.checkedRemoteFileToday = True
		debug("< ListingData.getChannel() prog count=%d" % len(progList))
		return progList


	############################################################################################################
	# extract data from file using regex - this is specific to TSReader file format
	############################################################################################################
	def createChannelFiles(self, dataFN, channelFN, dataDate=""):
		debug("> ListingData.createChannelFiles() dataFN=%s dataDate=%s" % (dataFN, dataDate))

		progList = []
		data = readFile(dataFN)
		if data:
			# parse data records and save
			matches = findAllRegEx(data, CHANNEL_REGEX)
			for prog in matches:
#				print "rec secs=%s = %s" % (prog[0], time.localtime(int(prog[0])))

				dateTime = "%s %s" % (dataDate, prog[1])	# display time
				dateTime_t = time.strptime(dateTime, "%Y%m%d %H:%M:%S")
				startTimeSecs = float(time.mktime(dateTime_t))
#				print "filedate+displaysecs=%s = %s = %s" % (dateTime, dateTime_t, startTimeSecs)
				
				progList.append( {
						TVData.PROG_STARTTIME : float(startTimeSecs),
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
	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)

		title = "%s - %s" % (self.name, __language__(976))
		configSMB = ConfigSMB(title)
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

