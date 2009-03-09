"""
  mytvLib.py
  Contains fuctions specific to myTV
 
  CHANGELOG:
  15/11/06 Updated for myTV v1.15
  11/01/07 Updated for myTV v1.16
  06/02/07 Updated to use new ConfigParser funcs in bbbLib
  08/08/07 Updated for myTV v1.17
  02/11/07 Modified getDescriptionLink() to replace more html tags to newline
  26/11/07 Modified getChannelsLIB() to use fetchCookieURL() which takes headers and reversed regex
  01/09/08 Updated for myTV v1.18
  12/09/08 Updated for myTV v1.18.1
  23/02/09 - translatePath()
"""

import sys,os.path
import xbmc, xbmcgui
import os, re
import urllib2, urlparse
import codecs, encodings, encodings.utf_8, encodings.latin_1
import time
from datetime import date
from string import strip, replace, find, capwords
import ConfigParser
from shutil import copytree

import mytvGlobals
from bbbLib import *
from bbbGUILib import *
from smbLib import enterSMB, selectSMB

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__title__ = "mytvLib"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '01-09-2008'
__version__ = sys.modules[ "__main__" ].__version__     	# should be in default.py
xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)

# script specific paths
DIR_USERDATA = sys.modules[ "__main__" ].DIR_USERDATA     	# should be in default.py
DIR_RESOURCES = sys.modules[ "__main__" ].DIR_RESOURCES     # should be in default.py
DIR_GFX = sys.modules[ "__main__" ].DIR_GFX     			# should be in default.py
DIR_CACHE = sys.modules[ "__main__" ].DIR_CACHE    			# should be in default.py
DIR_DATASOURCE = os.path.join( DIR_RESOURCES , "datasource" )
# just used in this module
DIR_LOGOS = os.path.join(DIR_USERDATA, "logos")
DIR_EPG = os.path.join(DIR_RESOURCES, "epg")
DIR_GENRE = os.path.join( DIR_RESOURCES , "genre" )
DIR_SAVEPROGRAMME = os.path.join( DIR_RESOURCES , "saveprogramme" )
DIR_DATASOURCE_GFX = os.path.join(DIR_GFX,'flags')

ICON_FAV_SHOWS = os.path.join(DIR_GFX,'fav.png')
ICON_TIMER = os.path.join(DIR_GFX,'timer.png')
ICON_NOW_TIME = os.path.join(DIR_GFX,'nowtime.png')
ICON_TIMERBAR = os.path.join(DIR_GFX,'timerbar.png')

__language__ = sys.modules[ "__main__" ].__language__

WEEKDAYS = [__language__(320),__language__(321),__language__(322),__language__(323),__language__(324),__language__(325),__language__(326)]

SAVE_METHOD_SMB = 'SMB'
SAVE_METHOD_CUSTOM = 'CUSTOM SCRIPT'
SAVE_METHOD_CUSTOM_SMB = 'CUSTOM SCRIPT then SMB'

############################################################################################################
# convert time to HHMM to secs since epoch. using fileDate as base date for time
############################################################################################################
def startTimeToSecs(lastStartTime, startTime, baseDate):
	# convert all forms to HHMM
	startTime = startTime.upper()
	isAM = (startTime.endswith('AM'))

	startTime = startTime.replace('.','').replace(':','').replace('H','').replace('AM','').replace('PM','')
	startTime = startTime.strip()

	sz = len(startTime)

	if sz == 1:		# eg 1AM
		hour = '0' + startTime[0]
		min = '00'
	elif sz == 2: 	# eg 10am
		hour = startTime[:2]
		min = '00'
	elif sz == 3: 	# eg 130am
		hour = '0' + startTime[0]
		min = startTime[1:3]
	else:			# eg 1030am
		hour = startTime[:2]
		min = startTime[2:4]

	# if we get 2400 convert to 0000
	if hour == '24':
		hour = '00'
	elif isAM and hour == '12':
		hour = '00'
	startTime = hour + min
	formatTime = time.strptime(baseDate+hour+min,"%Y%m%d%H%M")
	secs = time.mktime(formatTime)

	# if secs is < lastSecs, adjust, +12 hours
	if secs < lastStartTime:
		# add 12hr while < lastTime
		while secs < lastStartTime:
			secs += 43200		# 12hrs

	return int(secs)


############################################################################################################
# Download url and regex parse it to extract description.
############################################################################################################
def getDescriptionLink(link, regex, startStr='', endStr='', decodeSet='latin-1', headers={}):
	debug("> mytvLib.getDescriptionLink()")
	description = ''
	doc = fetchCookieURL(link, headers=headers)
	if doc and doc != -1:
		matches = parseDocList(doc, regex, startStr, endStr)
		if matches:
			try:
				description = decodeEntities(matches[0]).decode(decodeSet,'replace')
				# convert some HTML to newlines
				description = description.replace('</h2>','\n').replace('</p>','\n').replace('<BR>','\n').replace('<br>','\n').replace('<br />','\n').replace('</div>','\n')
				description = cleanHTML(description)
			except:
				description = "Error decoding html"
				handleException()

	if not description:
		debug("no description found")

	debug("< mytvLib.getDescriptionLink()")
	return description


############################################################################################################
# remove duplicate from a list, done this way to preserve order
# that pre-sorting wouldnt have.
# works against a list of two elemt list ie[[data, data],[data, data],[data, data] ...]
############################################################################################################
def removeDupList(list):
	finalList = []
	if list:
		for item in list:
			searchStr = item[0]						# use 1st element as the key
			found = False
			for flItem in finalList:
				if searchStr == flItem[0]:			# check same key
					found = True
					break
			if not found:
				finalList.append(item)
	return finalList


############################################################################################################
# Download a list of channels from a url based on a regex OR Load if file already exists.
# url		- URL to fetch page from
# filename	- save to filename
# regex		- regular expression to use to extract channels list
# reversed  - reverse the fetched ID / name
# RETURNS: list [ch ID, ch name] ie ['132','Channel 4']
# sorted	-  sort results
############################################################################################################
def getChannelsLIB(url, filename, regex, startStr='', endStr='', reversed=False, headers={}, sorted=True, removeStr=''):
	debug("> mytvLib.getChannelsLIB() %s" % filename)
	channelList = []

	# download if not got it
	if not fileExist(filename):
		dialogProgress.create(__language__(212), __language__(300), url)

		# download from url to file
#		doc = fetchURL(url)
		doc = fetchCookieURL(url, headers=headers)

		# process doc if no problem during download
		if doc:
			# use regex to find all channels on page
			if isinstance(regex, str):
				regex = [regex]

			cleanMatches = []
			for re in regex:
				matches = parseDocList(doc, re, startStr, endStr)
				for match in matches:
					cleanMatch = []
					for m in match:
						m = cleanHTML(m.replace(removeStr,''))
						if not reversed:
							cleanMatch.append(m)
						else:
							cleanMatch.insert(0, m)
					cleanMatches.append(cleanMatch)

			if cleanMatches:
				if sorted:		# name
					cleanMatches.sort()
				channels = removeDupList(cleanMatches)
				channelList = writeChannelsList(filename, channels)

		dialogProgress.close()
	else:
		channelList = readChannelsList(filename)

	debug("< mytvLib.getChannelsLIB() channels=%s" % len(channelList))
	return channelList

############################################################################################################
# Write a comma delimited channels list.  ie chID, chName
############################################################################################################
def writeChannelsList(filename, channels):
	debug("> mytvLib.writeChannelsList()")

	delimitedList = []
	if channels:
		f = open(xbmc.translatePath(filename),"w")

		# join & split so we can use decoded versions of data
		for channel in channels:
			outStr = unicodeToAscii(decodeEntities(','.join(channel)))
			f.write(outStr +'\n')
			chInfo = outStr.split(',')
			delimitedList.append(chInfo)

		f.close()

	debug("< mytvLib.writeChannelsList()")
	return delimitedList

############################################################################################################
# ignore 'hidden' channels, those with * as first ch
def readChannelsList(filename, loadHidden=False):
	debug("> mytvLib.readChannelsList()")

	channelList = []
	try:
		for readLine in file(filename):
			ch = readLine.replace('\n','').strip().split(',')
			if loadHidden or ch[1][0] != '*':		# ch name
				channelList.append(ch)
	except:
		print str( sys.exc_info()[ 1 ] )

	debug("< mytvLib.readChannelsList() channel count: %s" % len(channelList))
	return channelList


############################################################################################################
# Download XMTV data file. Defaults to zap2it site from which you need a regestered account (its free)
# fetchDate		- format YYYYMMDD
# fetchDate		- format YYYYMMDD
# now a paid for service
############################################################################################################
def fetchXMLTV(userName,
			passWord,
			fetchDate,
			fileName,
#			URL='http://datadirect.webservices.zap2it.com/tvlistings/xtvdService',  # discontinued service
			URL='http://webservices.schedulesdirect.tmsdatadirect.com/schedulesdirect/tvlistings/xtvdService',
			Realm='TMSWebServiceRealm',
			fileCoding='latin-1'):
	debug("> mytvLib.fetchXMLTV() " + fileName)
	success = False

	displayDate = getDisplayDate(fetchDate)
	dialogProgress.create("XMLTV: %s" % __language__(303), displayDate, URL)

	try:
		# convert string YYYYMMDD to secs
		startTimeSecs = time.mktime(time.strptime(fetchDate,"%Y%m%d"))
		startTime = time.strftime( '%Y-%m-%dT00:00:00Z', time.localtime(startTimeSecs))
		endTime   = time.strftime( '%Y-%m-%dT00:00:00Z', time.localtime(startTimeSecs + (86400.0)))

		strSoap = "<?xml version='1.0' encoding='utf-8'?>\n" \
				  "<SOAP-ENV:Envelope xmlns:SOAP-ENV='http://schemas.xmlsoap.org/soap/envelope/' " \
				  "xmlns:xsd='http://www.w3.org/2001/XMLSchema' " \
				  "xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' " \
				  "xmlns:SOAP-ENC='http://schemas.xmlsoap.org/soap/encoding/'>\n" \
				  "<SOAP-ENV:Body>\n" \
				  "<ns1:download xmlns:ns1='urn:TMSWebServices'>\n" \
				  "<startTime xsi:type='xsd:dateTime'>" + startTime + "</startTime>\n" \
				  "<endTime xsi:type='xsd:dateTime'>" + endTime + "</endTime>\n" \
				  "</ns1:download>\n" \
				  "</SOAP-ENV:Body>\n" \
				  "</SOAP-ENV:Envelope>\n"

		debug("XMLTV Requesting " + startTime + " to " + endTime)
		authinfo = urllib2.HTTPDigestAuthHandler()
		authinfo.add_password(Realm, urlparse.urlparse(URL)[1], userName, passWord)
		opener = urllib2.build_opener(authinfo)
		urllib2.install_opener(opener)
		try:
			debug('Logging in, fileCoding=' + fileCoding)
			if fileCoding == 'native':
				urldata = urllib2.urlopen(URL, strSoap)
				outfile = open(xbmc.translatePath(fileName),'wb',262144)
				repenc = False
			else:
				urldata = codecs.getreader('utf-8')(urllib2.urlopen(URL, strSoap), errors='replace')
				outfile = codecs.open(xbmc.translatePath(fileName),'wb', fileCoding, 'replace', 262144)
				repenc = True
		except IOError, errobj:
			debug("IOError")
			ErrorCode(errobj)
		except urllib2.HTTPError, errobj:
			debug("urllib2.HTTPError")
			ErrorCode(errobj.code)
		except:
			handleException("fetchXMLTV()")
		else:
			debug("XMLTV Receiving XML Data to File: " + fileName + ", Encoding: " + fileCoding)
			data = 'X'
			bytesRead = 0
			blockSZ= 24576				#8192, 24576
			totalSZ = 2621440			# based on approx 2.5meg file per day
			while data:
				data = urldata.read(blockSZ)
				dataSZ = len(data)
				bytesRead += dataSZ
				if repenc:
					data = replace(data, "encoding='utf-8'", "encoding='"+fileCoding+"'")
					repenc = False
				if data:
					outfile.write(data)
					pct=int(bytesRead*100.0/totalSZ)
				# just update every x%
				if pct and (pct % 5 == 0):
					dialogProgress.update(pct)

			debug('XMLTV download complete')
			try:
				urldata.close()
				outfile.close()
			except:
				pass
			success = fileExist(fileName)
	except:
		handleException("fetchXMLTV()")

	if not success:
		deleteFile(fileName)

	dialogProgress.close()
	debug("< mytvLib.fetchXMLTV() success=%s" % success)
	return success

#######################################################################################################################    
# VIEW TIMERS - Display a list of timers from timers_<date>.dat as DATE/TIME, PROG NAME, CH NAME
#######################################################################################################################
class ManageTimers:

	# timer rec field positions
	REC_STARTTIME = 0
	REC_CHID = 1
	REC_DUR = 2
	REC_CHNAME = 3
	REC_PROGNAME = 4
	REC_DEL_URL = 5
	REC_PROG_ID = 6

	def __init__(self, saveToFile=True):
		debug("> mytvLib.ManageTimers.init() saveToFile=%s" % saveToFile)
		self.saveToFile = saveToFile
		self.timers = []
		self.PREFIX = 'timers_'
		self.EXT = '.dat'
		self.DIR_CACHE = os.path.join(DIR_USERDATA, "timers")
		makeDir(self.DIR_CACHE)
		debug("< mytvLib.ManageTimers.init()")

	# get a list of all timer files.
	# Option to get only get files date >= today
	def getTimerFiles(self, anyDate=False):
		debug("> mytvLib.getTimerFiles() anyDate=%s" % anyDate)
		filelist = []

		if os.path.isdir(self.DIR_CACHE):
			today = getTodayDate()
			files = os.listdir(self.DIR_CACHE)
			for fname in files:
				name, ext = os.path.splitext(fname)
				matches = re.search(self.PREFIX+'(\d+)$', name)
				if matches:
					# if required, check this filedate is >= today
					fileDate = int(matches.group(1))
					if anyDate or fileDate >= today:
						filelist.append(fname)

		debug("< mytvLib.getTimerFiles() file count=%s" % len(filelist))
		return filelist

	def load(self):
		debug("> mytvLib.ManageTimers.load()")
		self.timers = []
		filelist = self.getTimerFiles()	# get all timer files

		# load timers from all timer files
		for fname in filelist:
			self.timers.extend(self.loadFile(fname))

		# sort into startTimeSecs order
		self.timers.sort()
#		self.timers.reverse()
		debug("< mytvLib.ManageTimers.load() timers=%s" % len(self.timers))
		return self.timers

	def loadFile(self, fname):
		debug("> mytvLib.ManageTimers.loadFile() fname="+fname)
		timers = []
		try:
			# open and read timers
			if not fname.startswith(self.DIR_CACHE):
				fname = os.path.join(self.DIR_CACHE,fname)
			for readLine in file(fname):
				try:
					split = (readLine.decode('latin-1')).split('~')
					startTimeSecs = float(split[self.REC_STARTTIME])
					chID = split[self.REC_CHID]
					durSecs = int(split[self.REC_DUR])
					chName = split[self.REC_CHNAME]
					progName = split[self.REC_PROGNAME].strip()
					delURL = split[self.REC_DEL_URL].strip()
					progID = split[self.REC_PROG_ID].strip()
					timers.append((startTimeSecs, chID, durSecs, chName, progName, delURL, progID))
				except:
					debug("record too short - ignoring it.")
		except:
			debug("file missing")

		debug("< mytvLib.ManageTimers.loadFile() timers=%s" % len(timers))
		return timers

	# get timers as a list [startTime, chID]
	# get timers as a list [progID]
	def getTimers(self, forceLoad=False):
		debug("> mytvLib.ManageTimers.getTimers()")

		if forceLoad:
			self.load()

		timersDict = {}
		timersProgIDList = []
		for timer in self.timers:
			try:
				chID = timer[self.REC_CHID]
				progID = timer[self.REC_PROG_ID]
				startTime = timer[self.REC_STARTTIME]
				endTime = startTime + timer[self.REC_DUR]
				# add starttime to channels list of timers
				timersDict[chID].append((startTime, endTime))
			except:
				# no timers on channel yet, create list
				timersDict[chID] = [(startTime, endTime)]
#			timersDict.append((timer[self.REC_STARTTIME], timer[self.REC_CHID]))

			# progID's list
			if progID:
				timersProgIDList.append(progID)

		debug("< mytvLib.ManageTimers.getTimers() timersDict sz=%s timersProgIDList sz=%s" % (len(timersDict), len(timersProgIDList)))
		return timersDict, timersProgIDList

	# load all timers in the file where this timers resides.
	# find timer, remove and write new file
	def deleteTimer(self, startTime):
		debug("> mytvLib.ManageTimers.deleteTimer() startTime=%s" % startTime)

		deleted = False
		if self.saveToFile:
			fname = self.getFilename(startTime) # prefixed with DIR_CACHE
			timers = self.loadFile(fname)
		else:
			timers = self.timers

		for i, timer in enumerate(timers):
			if timer[self.REC_STARTTIME] == startTime:
				deleted = True
				# remove timer
				try:
					self.timers.remove(timer)
				except:
					debug("failed to remove timer from internal timers")

				# if just working from mem, timers is same self.timers, so don't try and del
				# again as the above remove already done it and idx will now be out of sync
				if self.saveToFile:
					del timers[i]
				break

		# if needed, write remaining timers back to file
		if deleted and self.saveToFile:
			deleteFile(fname)
			for startTimeSecs,chID,durSecs,chName,progName,delURL,progID in timers:
				self.writeTimer(fname, startTimeSecs, chID, durSecs, chName, progName, delURL, progID)

		debug("< mytvLib.ManageTimers.deleteTimer() deleted=%s" % deleted)
		return deleted

	def deleteTimerFile(self, startTime):
		debug("ManageTimers.deleteTimerFile() startTime=%s" % startTime)
		fname = self.getFilename(startTime)	# prefixed with DIR_CACHE
		deleteFile(fname)

	def deleteAllTimerFiles(self):
		debug("ManageTimers.deleteAllTimerFiles()")
		removeDir(self.DIR_CACHE, force=True)
		makeDir(self.DIR_CACHE)

	def saveTimer(self, programme, channelInfo):
		debug("> mytvLib.ManageTimers.saveTimer()")

		startTimeSecs = programme[TVData.PROG_STARTTIME]
		endTimeSecs = programme[TVData.PROG_ENDTIME]
		fname = self.getFilename(startTimeSecs)
		progName = programme[TVData.PROG_TITLE].encode('latin-1', 'replace')
		if endTimeSecs:
			durSecs =  endTimeSecs - startTimeSecs
		else:
			durSecs = 0
		try:
			delURL = programme[TVData.PROG_SCHEDLINK]
		except:
			delURL = ''
		try:
			progID = programme[TVData.PROG_ID]
		except:
			progID = ''

		chID = channelInfo[TVChannels.CHAN_ID]
		chName = channelInfo[TVChannels.CHAN_NAME]
		if self.saveToFile:
			self.writeTimer(fname, startTimeSecs, chID, durSecs, chName, progName, delURL, progID)
		self.timers.append((startTimeSecs, chID, durSecs, chName, progName, delURL, progID))
		timersDict, timersProgIDList = self.getTimers()
		debug("< mytvLib.ManageTimers.saveTimer() timersDict sz=%s timersProgIDList sz=%s" % (len(timersDict), len(timersProgIDList)))
		return timersDict, timersProgIDList

	def writeTimer(self, fname, startTimeSecs, chID, durSecs, chName, progName, delURL="", progID=""):
		debug("ManageTimers.writeTimer() startTimeSecs=%s chID=%s fn=%s" % (startTimeSecs,chID,fname))
		try:
			f = open(xbmc.translatePath(fname),"a+")
			s = "%s~%s~%s~%s~%s~%s~%s\n" % \
				(float(startTimeSecs), chID, int(durSecs), chName, progName, delURL, progID)
			f.write(s)
			f.close()
		except:
			handleException("writeTimer()")

	def getFilename(self, startTimeSecs):
		fileDate = str(getTodayDate(startTimeSecs))
		return os.path.join(self.DIR_CACHE, self.PREFIX+fileDate+self.EXT)

	def checkTimerClash(self, programme):
		debug("> mytvLib.ManageTimers.checkTimerClash()")

		startTime = programme[TVData.PROG_STARTTIME]
		endTime = programme[TVData.PROG_ENDTIME]
		debug("checking for start=%s end=%s" % (startTime, endTime))
		if not self.timers:
			self.load()

		clash = False
		for timer in self.timers:
			timerStartTime = timer[self.REC_STARTTIME]
			timerEndTime = timerStartTime+timer[self.REC_DUR]
			if (startTime >= timerStartTime and startTime < timerEndTime) \
				or (endTime > timerStartTime and endTime <= timerEndTime) \
				or (startTime < timerStartTime and endTime > timerEndTime):

				displayStartTime = time.strftime("%H:%M",time.localtime(timerStartTime))
				displayEndTime = time.strftime("%H:%M",time.localtime(timerEndTime))
				if not xbmcgui.Dialog().yesno(__language__(129), timer[self.REC_PROGNAME],\
											  displayStartTime + ' - ' + displayEndTime, \
											  __language__(589)):
					clash = True
				break

		debug("< mytvLib.ManageTimers.checkTimerClash() clash=%s" % clash)
		return clash

	# list of timers [startTimeSecs, chID, durSecs, chName, progName, delURL, progID]
	def refreshTimerFiles(self, newTimersList):
		debug("> mytvLib.ManageTimers.refreshTimerFiles()")

		if self.saveToFile:
			self.deleteAllTimerFiles()
		self.timers = []

		for timer in newTimersList:
			# must have min of startTimeSecs & chID
			try:
				startTimeSecs = timer[self.REC_STARTTIME]
				chID = timer[self.REC_CHID]
				durSecs = timer[self.REC_DUR]
			except:
				continue
			try:
				chName = ''
				progName = ''
				delURL = ''
				progID = ''
				# these fields are optional
				chName = timer[self.REC_CHNAME]
				progName = timer[self.REC_PROGNAME]
				delURL = timer[self.REC_DEL_URL]
				progID = timer[self.REC_PROG_ID]
			except: pass

			# add timers
			if self.saveToFile:
				fname = self.getFilename(startTimeSecs)	# prefixed with DIR_CACHE
				self.writeTimer(fname, startTimeSecs, chID, durSecs, chName, progName, delURL, progID)
			self.timers.append((startTimeSecs, chID, durSecs, chName, progName, delURL, progID))

		timersDict, timersProgIDList = self.getTimers()
		debug("< mytvLib.ManageTimers.refreshTimerFiles()")
		return timersDict, timersProgIDList

	def __createMenu(self):
		debug("> mytvLib.ManageTimers.__createMenu()")

		menuList = []
		if self.timers:
			nowSecs = time.time()
			self.timers.sort()
			menuList.append(__language__(500))	# exit
			for startTimeSecs,chID,durSecs,chName,progName,delURL,progID in self.timers:
				displayDate = time.strftime("%d/%m/%Y %H:%M",time.localtime(startTimeSecs))
				durMins = int(durSecs/60)
				lbl1 = "%s, %s" % (progName,chName)
				lbl2 = "%s, %smins" % (displayDate,durMins)
				menuList.append(xbmcgui.ListItem(lbl1, label2=lbl2))

		debug("< mytvLib.ManageTimers.__createMenu()")
		return menuList


	# show menu of timers , return timer rec chosen
	def ask(self):
		debug("> mytvLib.ManageTimers.ask()")

		timer = []
		if not self.timers:
			self.load()							# load all timer files

		if self.timers:
			menu = self.__createMenu()
			header = "%s %s" % (__language__(511),__language__(586))
			while not timer:
				selectDialog = DialogSelect()
				selectDialog.setup(header, width=670, rows=len(menu),font=FONT10, panel=mytvGlobals.DIALOG_PANEL)
				selectedPos,action = selectDialog.ask(menu)
				if selectedPos <= 0:
					break

				progName = menu[selectedPos].getLabel()
				progDate = menu[selectedPos].getLabel2()
				if xbmcgui.Dialog().yesno(__language__(823), progName, progDate):		# delete ?
					timer = self.timers[selectedPos-1]	# allow for exit opt

		debug("< mytvLib.ManageTimers.ask()")
		return timer

#######################################################################################################################    
# Import<somename>_DataSource.py as determined by configuration file.
#######################################################################################################################    
def importDataSource(modFilename=''):
	debug("> mytvLib.importDataSource() modFilename="+modFilename)
	success = False
	try:
		del mytvGlobals.dataSource
	except: pass
	mytvGlobals.dataSource = None
	changedDS = False

	if not modFilename:
		try:
			modFilename = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_DATASOURCE)
		except:
			debug("MYTVConfig undefined, get new instance")
			mytvGlobals.config = MYTVConfig()
			modFilename = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_DATASOURCE)

		if not modFilename:
			modFilename = selectDataSource()
			if modFilename:
				changedDS = True

	debug("changedDS=%s" % changedDS)
	if modFilename:
		# import module
		try:
			debug("importing dataSource: " + modFilename)
			sys.path.insert(0, DIR_DATASOURCE)
			module = __import__(modFilename, globals(), locals(), [])
			mytvGlobals.dataSource = module.ListingData(DIR_CACHE)
			sys.path.remove(DIR_DATASOURCE)
			success = True
		except:
			mytvGlobals.dataSource = None
			handleException("importDataSource()")

		if not mytvGlobals.dataSource:
			messageOK(__language__(111), __language__(115))
		elif changedDS:
			deleteCacheFiles(0)	                                    # force cache clear
			prefSP = None
			if hasattr(mytvGlobals.dataSource, 'getPreferredSaveProgramme'):
				prefSP = mytvGlobals.dataSource.getPreferredSaveProgramme()
				debug("changed DataSource - preferred SaveProgramme=%s" % prefSP)
				# ask if want to use preferred
				if xbmcgui.Dialog().yesno(__language__(532), __language__(608), prefSP):
					mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_SAVE_PROG, prefSP)
				else:
					prefSP = None

			# only reset SP if currently using one
			currentSP = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SAVE_PROG)
			if prefSP == None and currentSP:
				# deleting saved saveProgramme, will force re-selection on reinit
				mytvGlobals.config.action(MTTVConfig.SECTION_SYSTEM, MYTVConfig.KEY_SYSTEM_SAVE_PROG, mode=ConfigHelper.MODE_REMOVE_OPTION)
				try:
					del mytvGlobals.saveProgramme
				except: pass
				mytvGlobals.saveProgramme = None

	sys.path
	debug("< mytvLib.importDataSource() dataSource: %s" % mytvGlobals.dataSource)
	return mytvGlobals.dataSource

#################################################################################################################
def canDataSourceConfig():
	if mytvGlobals.dataSource and hasattr(mytvGlobals.dataSource, "config"):
		return True
	else:
		return False

#################################################################################################################
# Choose a data source from a list of files named <somename>_DataSource.py in subfolder
#################################################################################################################
def selectDataSource():
	debug("> mytvLib.selectDataSource()")

	# create menu items from datasource files
	currModFilename = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_DATASOURCE)
	modFilename = ''
	menuList = []
	flags = ['']
	# get all the files <countrycode>_<sitename>.py  eg. uk_radiotimes.py
	# there should be a flag associated with each
	menuList = listDir(DIR_DATASOURCE, '.py')
	for fn in menuList:
		flags.append(os.path.join(DIR_DATASOURCE_GFX , fn[:2] + '.gif'))
	menuList.insert(0, __language__(500)) # exit

	# popup dialog to select choice
	selectDialog = DialogSelect()
	selectDialog.setup(__language__(531), rows=len(menuList), imageWidth=30, imageHeight=30, width=300, panel=mytvGlobals.DIALOG_PANEL)
	selectedPos, action = selectDialog.ask(menuList, icons=flags)
	if selectedPos > 0:
		modFilename = menuList[selectedPos]
		if currModFilename == modFilename:
			modFilename = False
		else:
			deleteCacheFiles(0)
			mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_DATASOURCE, modFilename)

			# clear SP
			mytvGlobals.config.action(MYTVConfig.SECTION_SYSTEM, MYTVConfig.KEY_SYSTEM_SAVE_PROG, mode=ConfigHelper.MODE_REMOVE_OPTION)

	del selectDialog

	debug("< mytvLib.selectDataSource() modFilename: %s" % modFilename)
	return modFilename

#################################################################################################################
# Re-configure datasource. Not all datasource require configuring.
#################################################################################################################
def configDataSource(forceReset=True):
	debug("> mytvLib.configDataSource() forceReset=%s" % forceReset)
	success = False

	while not success:
		try:
			success = mytvGlobals.dataSource.config(forceReset)	# force reset
			if not success:
				if not xbmcgui.Dialog().yesno(__language__(532), mytvGlobals.dataSource.getName(), __language__(216)):	# setup now?
					break
				else:
					forceReset = True
		except:
			handleException("configDataSource()")

	debug("< mytvLib.configDataSource() success=%s" % success)
	return success


#################################################################################################################
# Re-configure saveprogramme. Not all saveprogramme require configuring.
#################################################################################################################
def configSaveProgramme(reset=True):
	debug("> mytvLib.configSaveProgramme() reset=%s" % reset)
	success = False

#	global saveProgramme
	if mytvGlobals.saveProgramme:
		try:
			while not success:
				success = mytvGlobals.saveProgramme.config(reset)
				if not success:
					# setup now ?
					if xbmcgui.Dialog().yesno(mytvGlobals.saveProgramme.getName(), __language__(216)):
						reset = True
					else:
						break		# quit anyway
		except AttributeError:
			debug("saveProgramme has no config()")
			success = True
		except:
			handleException("configSaveProgramme()")

	debug("< mytvLib.configSaveProgramme() success=%s" % success)
	return success


#################################################################################################################
# Choose a SaveProgramme module from a list of files named SaveProgramme_<somename>.py in subfolder
#################################################################################################################
def selectSaveProgramme():
	debug("> mytvLib.selectSaveProgramme()")
	spName = None

	# create menu
	menuList = []
	# get all the files
	menuList = listDir(DIR_SAVEPROGRAMME, '.py')
	menuList.insert(0, MYTVConfig.VALUE_SAVE_PROG_NOTV)             # no tv card
	menuList.insert(0, __language__(500))                       # exit

	# popup dialog to select choice
	selectDialog = DialogSelect()
	selectDialog.setup(__language__(533), rows=len(menuList), width=270, panel=mytvGlobals.DIALOG_PANEL)
	selectedPos, action = selectDialog.ask(menuList)
	if selectedPos > 0:
		if selectedPos == 1:
			spName = ""		# no tv card
		else:
			spName = menuList[selectedPos]
		mytvGlobals.config.setSystem(MYTVConfig.KEY_SYSTEM_SAVE_PROG, spName)

	debug("< mytvLib.selectSaveProgramme() %s" % spName)
	return spName

#######################################################################################################################    
# Import SaveProgramme_<somename>.py as determined by configuration file.
# None (no config setting) is no SP set - force selection.
# "" is No TV Card to be used.
#######################################################################################################################    
def importSaveProgramme():
	debug("> mytvLib.importSaveProgramme()")
	success = False
#	global saveProgramme
	try:
		del mytvGlobals.saveProgramme
		gc.collect()
	except: pass
	mytvGlobals.saveProgramme = None

	# read config file
	spName = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_SAVE_PROG)
	if spName == None:      # setting not exist
		spName = selectSaveProgramme()

	if spName in ("",MYTVConfig.VALUE_SAVE_PROG_NOTV):		# no tv card
		success = True
	elif spName:
		# import module
		try:
			debug("importing SaveProgramme: %s" % spName)
			sys.path.insert(0, DIR_SAVEPROGRAMME)
			module = __import__(spName, globals(), locals(), [])
			mytvGlobals.saveProgramme = module.SaveProgramme(cachePath=DIR_CACHE)
			sys.path.remove(DIR_SAVEPROGRAMME)
			success = configSaveProgramme(False)
		except:
			messageOK(__language__(99), __language__(116))
			handleException()

	if not success:
		debug("no saveProgramme selected/imported/configured, removed tvcard setting")
		mytvGlobals.config.action(MYTVConfig.SECTION_SYSTEM, MYTVConfig.KEY_SYSTEM_SAVE_PROG, mode=ConfigHelper.MODE_REMOVE_OPTION)
		mytvGlobals.saveProgramme = None
		success = True              # pretend it all ok now
	sys.path
	debug("< mytvLib.importSaveProgramme() success=%s" % success)
	return success

#################################################################################################################
# clear listsings cache of files based on date in filename.
#################################################################################################################
def clearCache(forceDelete=False):
	debug("> mytvLib.clearCache() forceDelete=%s" % forceDelete)

	if forceDelete or xbmcgui.Dialog().yesno(__language__(0), __language__(530), __language__(200)):
		deleteCacheFiles(0)
		done = True
	else:
		done = False

	if not forceDelete and done:
		if xbmcgui.Dialog().yesno(__language__(0), __language__(530),__language__(201)):
			deleteFile(getChannelListFilename())

	debug("< mytvLib.clearCache() done=%s" % done)
	return done

#################################################################################################################
def getChannelListFilename():
	try:
#		global dataSource
		datasourceName = mytvGlobals.dataSource.getName()
	except:
		datasourceName = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_DATASOURCE)

	datasourceFile = "Channels_%s.dat" % datasourceName
	fn = os.path.join(DIR_CACHE, datasourceFile)
	debug("getChannelListFilename() " + fn)
	return fn

#################################################################################################################
# delete all files in cache (ending with YYYYMMDD) older than given time in secs.
# default to 3days
#################################################################################################################
def deleteCacheFiles(ageSecs=259200):
	debug("> mytvLib.deleteCacheFiles() ageSecs %s " % ageSecs)

	if os.path.exists(DIR_CACHE):
		# to clear all files, set delete time to a time in future
		if ageSecs == 0: ageSecs = -3000000		# about 2 months in advance, made neg to calc to be in future
		deleteDate = getTodayDate(time.time() - ageSecs)
		files = os.listdir(DIR_CACHE)
		for filename in files:
			fn, ext = os.path.splitext(filename)
			fileDate = searchRegEx(fn, '^.*?_(\d+)$')
			if fileDate and int(fileDate) <= deleteDate:
				deleteFile(os.path.join(DIR_CACHE, filename))

	debug("< mytvLib.deleteCacheFiles()")

#################################################################################################################
# Config a YES/No option and save if changed
#################################################################################################################
def configYesNo(title, prompt, key, section, yesButton="", noButton=""):
	debug("> mytvLib.configYesNo()")

	# load orig value
	currValue = mytvGlobals.config.action(section, key)
	if currValue in (True, False):
		newValue = not currValue			
	else:
		if yesButton or noButton:
			newValue = bool( xbmcgui.Dialog().yesno(title, prompt, '', '', noButton, yesButton))
		else:
			newValue = bool( xbmcgui.Dialog().yesno(title, prompt))	# lang default yes & no

	print currValue, newValue
	changed = (currValue != newValue)
	if changed:
		mytvGlobals.config.action(section, key, newValue, mode=ConfigHelper.MODE_WRITE)
	debug("< mytvLib.configYesNo() changed=%s" % changed)
	return changed

#############################################################################################################
class MYTVConfig:
	# EXTRA SECTIONS
	SECTION_SMB = "SMB"
	SECTION_SYSTEM = "SYSTEM"
	SECTION_DISPLAY = "DISPLAY"

	# SMB KEYS
	KEY_SMB_PATH = "smb_path"
	KEY_SMB_IP = "smb_pc_ip"
	KEY_SMB_FILE = "smb_filename"

#	VALUE_SMB_FILE = 'mytv_rec_$Y$M$D_$H$I_$l.bat'
	VALUE_SMB_PATH = 'smb://user:pass@PCNAME/share/folder/'

	VALUE_SAVE_PROG_NOTV = __language__(818)
	
	# SYSTEM KEYS
	KEY_SYSTEM_DATASOURCE = "datasource"
	KEY_SYSTEM_CLOCK = "24hrClock"
	KEY_SYSTEM_TIMER_CLASH_CHECK = "timer_clash_check"
	KEY_SYSTEM_FETCH_TIMERS_STARTUP = 'fetch_timers_startup'
	KEY_SYSTEM_SAVE_TEMPLATE = "save_template"
	KEY_SYSTEM_SAVE_PROG = "save_programme"
	KEY_SYSTEM_SHOW_CH_ID = 'show_chid'
	KEY_SYSTEM_USE_LSOTV = 'livesportontv'
	KEY_SYSTEM_CHECK_UPDATE = 'check_script_update'
	KEY_SYSTEM_WOL = 'wol_mac'

	# DISPLAY KEYS
	KEY_DISPLAY_COLOUR_CHNAMES = "colour_chnames"
	KEY_DISPLAY_NOFOCUS_ODD = "file_epg_nofocus_odd"
	KEY_DISPLAY_NOFOCUS_EVEN = "file_epg_nofocus_even"
	KEY_DISPLAY_NOFOCUS_FAV = "file_epg_nofocus_fav"
	KEY_DISPLAY_FOCUS = "file_epg_focus"
	KEY_DISPLAY_COLOUR_TITLE = "colour_title"
	KEY_DISPLAY_COLOUR_SHORT_DESC = "colour_title_desc"
	KEY_DISPLAY_COLOUR_TEXT_ODD = "colour_epg_text_odd"
	KEY_DISPLAY_COLOUR_TEXT_EVEN = "colour_epg_text_even"
	KEY_DISPLAY_COLOUR_TEXT_FAV = "colour_epg_text_fav"
	KEY_DISPLAY_FONT_TITLE = "font_title"
	KEY_DISPLAY_FONT_SHORT_DESC = "font_short_desc"
	KEY_DISPLAY_FONT_CHNAMES = "font_chname"
	KEY_DISPLAY_FONT_EPG = "font_epg"
	KEY_DISPLAY_EPG_ROW_HEIGHT = "height_epg_row"
	KEY_DISPLAY_EPG_ROW_GAP_HEIGHT = "height_epg_row_gap"
	KEY_DISPLAY_SKIN = "skin"
	KEY_DISPLAY_COLOUR_ARROWS = "colour_arrows"
	KEY_DISPLAY_COLOUR_NOWTIME = "colour_nowtime_line"
	KEY_DISPLAY_COLOUR_TIMERBAR = "colour_timerbar"
	KEY_DISPLAY_DIALOG_PANEL = "dialog_panel"
	KEY_SYSTEM_SHOW_DSSP = "show_dssp"

	# DISPLAY DEFAULT VALUES
	VALUE_DISPLAY_FONT_TITLE = FONT14
	VALUE_DISPLAY_FONT_SHORT_DESC = FONT12
	VALUE_DISPLAY_FONT_CHNAMES = FONT14
	VALUE_DISPLAY_FONT_EPG = FONT14
	VALUE_DISPLAY_EPG_ROW_HEIGHT = "30"
	VALUE_DISPLAY_EPG_ROW_GAP_HEIGHT = "3"
	VALUE_SYSTEM_SAVE_PROG_NOTV = "No TV"

	def __init__(self):
		debug("> mytvLib.MYTVConfig.__init__")
		self.configHelper = ConfigHelper(os.path.join(DIR_USERDATA, "Config.dat"))
		self.initAllDefaults()
		debug("< mytvLib.MYTVConfig.__init__")

	def initAllDefaults(self):
		debug("> mytvLib.mytvConfig.initAllDefaults()")
		# setting defaults will create options that are missing
		self.initSectionSystem()
		self.initSectionDisplay()	# setup default items
#		self.initSectionSMB()
		debug("< mytvLib.mytvConfig.initAllDefaults()")

	def reset(self):
		debug("> mytvLib.mytvConfig.reset()")
		if xbmcgui.Dialog().yesno(__language__(552),__language__(307)):
			self.configHelper.reset()
			self.configHelper.deleteConfigFile()
			self.initAllDefaults()
			reset = True
		else:
			reset = False
		debug("< mytvLib.mytvConfig.reset()")
		return reset

	def initSectionSystem(self):
		debug("> mytvLib.mytvConfig.initSectionSystem()")
		items = {}
		items[MYTVConfig.KEY_SYSTEM_DATASOURCE] = ""
		items[MYTVConfig.KEY_SYSTEM_CLOCK] = ConfigHelper.VALUE_YES
		items[MYTVConfig.KEY_SYSTEM_FETCH_TIMERS_STARTUP] = ConfigHelper.VALUE_YES
		items[MYTVConfig.KEY_SYSTEM_TIMER_CLASH_CHECK] = ConfigHelper.VALUE_YES
		items[MYTVConfig.KEY_SYSTEM_SAVE_TEMPLATE] = "$C~$T~$S~$l"
		items[MYTVConfig.KEY_SYSTEM_SAVE_PROG] = None
		items[MYTVConfig.KEY_SYSTEM_SHOW_CH_ID]= 1
		items[MYTVConfig.KEY_SYSTEM_USE_LSOTV]= ConfigHelper.VALUE_NO
		items[MYTVConfig.KEY_SYSTEM_CHECK_UPDATE]= ConfigHelper.VALUE_NO
		items[MYTVConfig.KEY_SYSTEM_WOL] = ""
		items[MYTVConfig.KEY_SYSTEM_SHOW_DSSP] = True
		# inits any missing values
		self.configHelper.initSection(MYTVConfig.SECTION_SYSTEM, items)
		debug("< mytvLib.mytvConfig.initSectionSystem()")

	def initSectionDisplay(self):
		debug("> mytvLib.mytvConfig.initSectionDisplay()")
		items = {}
		# set all keys with a default
		items[MYTVConfig.KEY_DISPLAY_NOFOCUS_ODD] = "DarkBlue.png"
		items[MYTVConfig.KEY_DISPLAY_NOFOCUS_EVEN] = "DarkBlue.png"
		items[MYTVConfig.KEY_DISPLAY_NOFOCUS_FAV] = "DarkYellow.png"
		items[MYTVConfig.KEY_DISPLAY_FOCUS] =  "LightBlue.png"
		items[MYTVConfig.KEY_DISPLAY_FONT_CHNAMES] = self.VALUE_DISPLAY_FONT_CHNAMES
		items[MYTVConfig.KEY_DISPLAY_FONT_EPG] = self.VALUE_DISPLAY_FONT_EPG
		items[MYTVConfig.KEY_DISPLAY_EPG_ROW_HEIGHT] = self.VALUE_DISPLAY_EPG_ROW_HEIGHT
		items[MYTVConfig.KEY_DISPLAY_EPG_ROW_GAP_HEIGHT] = self.VALUE_DISPLAY_EPG_ROW_GAP_HEIGHT
		items[MYTVConfig.KEY_DISPLAY_COLOUR_CHNAMES] = "0xFFFFFFFF"
		items[MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_ODD] = "0xFFFFFFFF"
		items[MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_EVEN] = "0xFFFFFFFF"
		items[MYTVConfig.KEY_DISPLAY_COLOUR_TEXT_FAV] = "0xFFFFFFFF"
		items[MYTVConfig.KEY_DISPLAY_COLOUR_TITLE] = "0xFFFFFFFF"
		items[MYTVConfig.KEY_DISPLAY_COLOUR_SHORT_DESC] = "0xFFFFFFFF"
		items[MYTVConfig.KEY_DISPLAY_COLOUR_ARROWS] = "0xFFFFFFCC"
		items[MYTVConfig.KEY_DISPLAY_COLOUR_NOWTIME] = "0xFFFFFFCC"
		items[MYTVConfig.KEY_DISPLAY_COLOUR_TIMERBAR] = "0xFF99FFFF"
		items[MYTVConfig.KEY_DISPLAY_DIALOG_PANEL] = "dialog_panel.png"
		skinName = getSkinName()
		items[MYTVConfig.KEY_DISPLAY_SKIN] = skinName

		# detect skin change
		savedSkin = self.getDisplay(MYTVConfig.KEY_DISPLAY_SKIN)
		if not savedSkin or savedSkin != skinName:
			debug("skin undefined or changed")
			self.action(section=MYTVConfig.SECTION_DISPLAY,mode=self.configHelper.MODE_REMOVE_SECTION)
			items = self.loadSkinConfig(items, skinName)

		# save section into cp
		self.configHelper.initSection(MYTVConfig.SECTION_DISPLAY, items)
		debug("< mytvLib.mytvConfig.initSectionDisplay()")

#	def initSectionSMB(self):
#		debug("mytvConfig.initSectionSMB()")
#		items = {}
#		items[MYTVConfig.KEY_SMB_PATH] = MYTVConfig.VALUE_SMB_PATH
#		items[MYTVConfig.KEY_SMB_IP] = ""
#		items[MYTVConfig.KEY_SMB_FILE] = MYTVConfig.VALUE_SMB_FILE
#		# inits any missing values
#		self.configHelper.initSection(MYTVConfig.SECTION_SMB, items)

	###############################################################################################################
	# if it exists, overright section settings with key/values from skin config file
	# loads associated skin config (if exists) for whatever the current xbmc skin is DIR_EPG
	###############################################################################################################
	def loadSkinConfig(self, displayItems, skinName):
		debug("> mytvLib.loadSkinConfig()")

		skinFN = os.path.join(DIR_EPG, skinName+".skin")
		debug("skinFN=%s" % skinFN)
		if not os.path.isfile(skinFN):
			debug("no skin file for skin, using defaults")
		else:
			try:
				skinConfig = ConfigParser.ConfigParser()
				skinConfig.readfp(open(skinFN))
				if DEBUG:
					print "Current items=", displayItems.items()
					print "loaded items=", skinConfig.items("SKIN")

				# using items of the current config dict, find in skin config and overright
				for key, value in skinConfig.items("SKIN"):
					displayItems[key] = value.strip()
			except:
				traceback.print_exc()
				messageOK("SKIN LOAD ERROR","Failed to load skin config file.",skinFN)

		debug("< mytvLib.loadSkinConfig()")
		return displayItems

	def getSystem(self, option):
		return self.configHelper.action(MYTVConfig.SECTION_SYSTEM, option)

	def setSystem(self, option, value):
		return self.configHelper.action(MYTVConfig.SECTION_SYSTEM, option, value, mode=ConfigHelper.MODE_WRITE)

	def getDisplay(self, option, usePrefixDir=True):
		value = self.configHelper.action(MYTVConfig.SECTION_DISPLAY, option)
		if value and usePrefixDir and (isinstance(value, str) and \
					(value.lower().endswith(".png") or \
					value.lower().endswith(".gif") or \
					value.lower().endswith(".jpg"))):
			return os.path.join(DIR_EPG, value)
		else:
			return value

	def setDisplay(self, option, value):
		return self.configHelper.action(MYTVConfig.SECTION_DISPLAY, option, value, mode=ConfigHelper.MODE_WRITE)

	def getSMB(self, option):
		return self.configHelper.action(self.SECTION_SMB, option)

	def setSMB(self, option, value):
		return self.configHelper.action(self.SECTION_SMB, option, value, mode=ConfigHelper.MODE_WRITE)

	def action(self, section="", option="", value="", mode=None):
		return self.configHelper.action(section, option, value, mode)

#############################################################################################################
# Used if script uses Config
#############################################################################################################
class ConfigHelper:

	# Config actions
	MODE_SECTIONS = "ls"			# list of sections
	MODE_OPTIONS = "lo"			# list options in the given section
	MODE_ITEMS = "li"				# list of items (name, value pairs) in the given section
	MODE_INIT_OPTION = "i"			# read, init option to a default value if not exists
	MODE_INIT_SECTION = "is"		# read, init option to a default value if not exists
	MODE_READ = "r"				# read in the given section
	MODE_WRITE = "w"				# write in the given section
	MODE_REMOVE_SECTION = "rs"		# remove section
	MODE_REMOVE_OPTION = "ro"		# remove option in the given section
	MODE_HAS_SECTION ="hs"			# check if section exists

	VALUE_YES = True
	VALUE_NO = False
	VALUE_NONE = "None"
	VALUE_NOT_SET = "?"

	def __init__(self, filename=''):
		debug("> mytvLib.ConfigHelper.__init__")

		self.reset()
		if filename:
			self.filename = xbmc.makeLegalFilename(xbmc.translatePath(filename))
			self.load()
			self.showCP()
		else:
			self.filename = ''
		debug("< mytvLib.ConfigHelper.__init__")

	def reset(self):
		try:
			del self.cp
		except: pass
		self.cp = ConfigParser.ConfigParser()

	def showCP(self):
		if DEBUG:
			sections = self.cp.sections()
			print "sections=",sections
			for s in sections:
				print "\nsection=", s
				print "  options=", self.cp.items(s)

	def setFilename(self, filename):
		self.filename = xbmc.makeLegalFilename(filename)

	def deleteConfigFile(self):
		deleteFile(self.filename)

	def save(self): 
		try:
			self.cp.write(open(self.filename, "w"))
			success = True
		except:
			success = False
			print filename
			traceback.print_exc()
			messageOK("Config Save Failed","Check filename/space etc.")
		return success

	def load(self):
		success = False
		if fileExist(self.filename):
			try:
				self.cp.read(self.filename)
				success = True
			except: pass
		debug("ConfigHelper.load() success=%s" % success)
		return success

	def boolToYesNo(self, value):
		if isinstance(value, bool):
			if value:
				return __language__(350)	# YES
			else:
				return __language__(351)	# NO
		else:
			return value

	def yesNoToBool(self, value):
		if value and value.lower() in ('yes', __language__(350)):	# YES
			return True
		else:
			return False

	# Create sections and set ConfigParser options from options supplied, 
	# only overwrite if no value exists, then saves to file.
	def initSection(self, sectionName, items, deleteSectionFirst=False):
		if deleteSectionFirst:
			self.action(sectionName, mode=ConfigHelper.MODE_REMOVE_SECTION)
		self.action(sectionName, items, mode=ConfigHelper.MODE_INIT_SECTION)
		return self.save()

	# this does all the real work on ConfigParser
	def action(self, section='', option='', value='', mode=None):
		if not mode: mode = self.MODE_READ
		debug("> mytvLib.ConfigHelper.action() mode=%s section=%s option=%s value=%s" % (mode,section,option, value))
		retValue = None

		if mode==self.MODE_READ:
			try:
				retValue = self.cp.get(section, option)
				# check for bool as a string, convert to bool
				if retValue.lower() == 'true':
					retValue = True
				elif retValue.lower() == 'false':
					retValue = False
			except:
				debug("MODE_READ: No such SECTION/OPTION")
		elif mode==self.MODE_SECTIONS:
			retValue = self.cp.sections()
		elif mode == self.MODE_OPTIONS:
			try:
				retValue = self.cp.options(section)
			except:
				debug("MODE_OPTIONS: no such section")
		elif mode==self.MODE_ITEMS:
			try:
				retValue = self.cp.items(section)
			except:
				debug("MODE_ITEMS: No such SECTION")
		elif mode==self.MODE_INIT_OPTION:
			try:
				retValue = self.cp.get(section, option)
			except:
				debug("MODE_INIT: No such SECTION/OPTION - set to WRITE mode")
				mode = self.MODE_WRITE
		elif mode==self.MODE_INIT_SECTION:
			# options in this case is a dict of {key, value} items
			for opt, value in option.items():
				try:
					self.cp.get(section, opt)	# leave if already exists
				except:
					self.__setOption(section, opt, value)
		elif mode == self.MODE_REMOVE_SECTION:
			try:
				if self.cp.remove_section(section):
					retValue = self.save()
			except:
				debug("MODE_REMOVE_SECTION: no such section")
		elif mode == self.MODE_REMOVE_OPTION:
			try:
				if self.cp.remove_option(section, option):
					retValue = self.save()
			except:
				debug("MODE_REMOVE_OPTION: no such section/option")
		elif mode == self.MODE_HAS_SECTION:
			try:
				retValue = self.cp.has_section(section)
			except:
				debug("MODE_HAS_SECTION: no such section")

		if mode == self.MODE_WRITE:
			retValue = self.__setOption(section, option, value)
			if retValue:
				retValue = self.save()

		# convert string None to proper None type
		if retValue == "None":
			retValue = None

		debug("< mytvLib.ConfigHelper.action() retValue=%s" % retValue)
		return retValue

	def __setOption(self, section, option, value):
		try:
			# create section if not exist
			if not self.cp.has_section(section):
				self.cp.add_section(section)
				debug("config __setOption() created section")
			self.cp.set(section, option, str(value))
			return True
		except:
			handleException("Config WRITE Error")
			return False


###################################################################################################################
def getDisplayDate(fileDate):
	return time.strftime("%A, %d %B %Y",time.strptime(fileDate,"%Y%m%d"))

###################################################################################################################
# return days from today
def getDayDelta(newDOW):
	debug("> mytvLib.getDayDelta() from newDOW=%s" % newDOW)
	dow = date.today().weekday()
	if newDOW == dow:
		dayDelta = 0
	elif newDOW > dow:
		dayDelta = (newDOW - dow)
	else:
		dayDelta = (7 - dow) + newDOW
	debug("< mytvLib.getDayDelta() dayDelta=%s" % dayDelta)
	return dayDelta

###################################################################################################################
# configOptionsMenu - menu to setup options
# configData = [configkey, label, defaultValue, kbType]
###################################################################################################################
def configOptionsMenu(section, configData, menuTitle, menuWidth=560):
	debug("> mytvLib.configOptionsMenu()")

	REC_KEY = 0
	REC_LABEL = 1
	REC_DEFAULT_VALUE = 2
	REC_KB_TYPE = 3

	def __enterValue(currValue, defaultValue, key, kbType, title):
		if currValue in (None,""):
			currValue = defaultValue
		value = doKeyboard(currValue, title, kbType)
		if value != None:	# cancelled
			mytvGlobals.config.action(section, key, value, mode=ConfigHelper.MODE_WRITE)
		return value

	def __enterSubMenu(currValue, options, key, title):
		# determine menu width
		maxChars = 0
		for opt in options:
			if len(opt) > maxChars:
				maxChars = len(opt)
		width = (maxChars * 20) + 40		# avg pixel w per ch, + min border

		# find currValue in options
		try:
			selectedPos = options.index(currValue)
		except:
			selectedPos = 0
		dlg = DialogSelect()
		dlg.setup(title, rows=len(options), panel=mytvGlobals.DIALOG_PANEL, width=width)
		selectedPos, action = dlg.ask(options, selectedPos)
		if selectedPos >= 0:
			value = options[selectedPos]
			mytvGlobals.config.action(section, key, value, mode=ConfigHelper.MODE_WRITE)
			return True
		else:
			return False

	def __makeMenu():
		menu = [xbmcgui.ListItem(__language__(500),'')]
		for rec in configData:
			configKey = rec[REC_KEY]
			label = rec[REC_LABEL]
			label2 = ''
			if configKey:
				if configKey in (MYTVConfig.KEY_SMB_PATH, MYTVConfig.KEY_SMB_IP, MYTVConfig.KEY_SMB_FILE):
					label2 = mytvGlobals.config.getSMB(configKey)
					menu.append(xbmcgui.ListItem(label, label2))
					menu.append(xbmcgui.ListItem(__language__(971), ''))	# select from existing
				else:
					label2 = mytvGlobals.config.action(section, configKey)
					label2 = mytvGlobals.config.configHelper.boolToYesNo(label2)
					if label2 == None:
						label2 = ''
					menu.append(xbmcgui.ListItem(label, label2))

		return menu

	# DO MENU, SELCT OPT, GET VALUE, SAVE TO CONFIG
	selectedPos = 0
	changed = False
	while True:
		menu = __makeMenu()
		selectDialog = DialogSelect()
		selectDialog.setup(menuTitle, width=menuWidth, rows=len(menu), panel=mytvGlobals.DIALOG_PANEL)
		selectedPos, action = selectDialog.ask(menu, selectedPos)
		if selectedPos <= 0:
			break # exit selected

		if menu[selectedPos].getLabel() == __language__(971):		# select from existing
			kbType = KBTYPE_SMB
			label = ""
			currValue = selectSMB()
			if not currValue: continue
		else:
			key, label, defaultValue, kbType = configData[selectedPos-1]    # defaultValue could be a list of options
			currValue = menu[selectedPos].getLabel2()
			

		# enter new value and save to config
		if kbType == KBTYPE_SMB:
			smbPath, ip = enterSMB(currValue, label)
			if smbPath and smbPath != currValue:
				changed = True
		elif kbType == KBTYPE_YESNO:
			if configYesNo(menuTitle, label, key, section):
				changed = True
		else:
			if isinstance(defaultValue, list) or isinstance(defaultValue, tuple):
				# menu of options reqd
				if __enterSubMenu(currValue, defaultValue, key, label):
					changed = True
			else:
				if __enterValue(currValue, defaultValue, key, kbType, label):
					changed = True
		del selectDialog

	debug("< mytvLib.configOptionsMenu() changed=%s" % changed)
	return changed


###################################################################################################################
# Channels (list) of a list of programmes. each prog is a dict
# [ [ {}, {}, ... ], [ {}, {}, ... ], ... ]
###################################################################################################################
class TVData:

	PROG_STARTTIME = 'start'
	PROG_ENDTIME = 'end'
	PROG_TITLE = 'title'
	PROG_SUBTITLE = 'subtitle'
	PROG_DESC = 'desc'
	PROG_DESCLINK = 'descurl'
	PROG_GENRE = 'genre'
	PROG_SCHEDLINK = 'schedurl'
	PROG_ID = 'id'
	PROG_DUR = 'dur'

	def __init__(self):
		debug("TVData init")
		self.reset()

	def reset(self):
		debug("TVData.reset()")
		self.channels = []

	def showChannels(self, chIDX=-1):
		if chIDX == -1:
			# show all channels
			print "ch count=%i" % len(self.channels)
			for i, ch in enumerate(self.channels):
				print "chIDX=%i %s" % (i, ch)
		else:
			try:
				print self.channels[chIDX]
			except: pass

	def showProg(self, chIDX, progIdx):
		try:
			print self.channels[chIDX][progIdx]
		except: pass

	def addChannel(self, listOfProgs, chID, chName, chIDAlt=''):
		self.channels.append(listOfProgs)

	# append a single prog dict to a channels list of progs
	def addProg(self, chIDX, prog):
		try:
			self.channels[chIDX].append(prog)
		except:
			self.channels[chIDX] = []
			self.channels[chIDX].append(prog)

	# extend a channel with a list of progs
	def extendChannel(self, chIDX, listOfProgs):
		try:
			self.channels[chIDX].extend(listOfProgs)
		except:
			self.channels[chIDX] = listOfProgs

	def getChannelsCount(self):
		return len(self.channels)

	def getChannelProgCount(self, chIDX):
		try:
			return len(self.channels[chIDX])
		except:
			return 0

	def getChannel(self, chIDX):
		try:
			return self.channels[chIDX]
		except:
			return None

	def getProg(self, chIDX, progIdx):
		try:
			return self.channels[chIDX][progIdx]
		except:
			return None

	def getProgAttrByIdx(self, chIDX, progIdx, attr):
		try:
			return self.channels[chIDX][progIdx][attr]
		except:
			return ''

	def getProgAttr(self, prog, attr):
		try:
			return prog[attr]
		except:
			return ''

	def setProgAttrByIdx(self, chIDX, progIdx, attr, value):
		try:
			self.channels[chIDX][progIdx][attr] = value
			return True
		except:
			return None

	def setProgAttr(self, prog, attr, value):
		prog[attr] = value

	def setChannel(self, chIDX, progList):
		self.channels[chIDX] = progList

	def clearChannel(self, chIDX):
		try:
			self.channels[chIDX] = []
		except: pass

	def delChannel(self, chIDX):
		try:
			del self.channels[chIDX]
		except: pass

	def clearProg(self, chIDX, progIdx):
		try:
			self.channels[chIDX][progIdx] = []
		except: pass

	def delProg(self, chIDX, progIdx):
		try:
			del self.channels[chIDX][progIdx]
		except: pass

	def updateProgs(self, chIDX, listOfProgs):
		try:
			self.channels[chIDX] = listOfProgs
		except:
			self.channels.insert(chIDX, listOfProgs)

	def getChannelID(self, chIDX):
		try:
			self.channels[chIDX]
			return True
		except:
			return False

	def hasChannel(self, chIDX):
		try:
			self.channels[chIDX]
			value = True
		except:
			value = False
		debug("TVData.hasChannel() %s" % value)
		return value

def loadChannelFromFile(filename):
    debug("> mytvLib.loadChannelFromFile()")
    progList = []
    try:
        # each row is a prog dict
        filename = xbmc.makeLegalFilename(xbmc.translatePath(filename))
        debug("legal filename=%s" % filename)
        for rec in open(filename,'r'):
            progList.append(eval( rec.strip() ))
    except:
        debug("error opening file")
    debug("< mytvLib.loadChannelFromFile() prog count=%s" % len(progList))
    return progList

def saveChannelToFile(progList, filename):
	debug("> mytvLib.saveChannelToFile()")
	saved = False
	if progList:
		filename = xbmc.makeLegalFilename(xbmc.translatePath(filename))
		debug("legal filename=%s" % filename)
		if not fileExist(filename):
			try:
				progList = checkProgContinuity(progList)
				fout = open(filename,'w')
				for prog in progList:
					fout.write( repr( prog ) +'\n')
				fout.close()
				saved = True
			except:
				handleException()
		else:
			debug("file exists, progs not written")
	else:
		deleteFile(filename)
	debug("< mytvLib.saveChannelToFile() saved=%s" % saved)
	return saved

# check all progs times follow and fill in gaps
def checkProgContinuity(channel):
	debug("> mytvLib.checkProgContinuity()")
	if len(channel) > 1:
		# 1) all start/end times match up
		# 2) any gap in progs filled in with empty prog
		# 3) check prog dont finish after next prog starts
		lastEndTime = 0
		progIdx = 0
		added = 0
		overlapping = 0
		for prog in channel[:]:						# work against channel copy
			startTime = prog[TVData.PROG_STARTTIME]
			endTime = prog[TVData.PROG_ENDTIME]
			if progIdx > 0 and startTime != lastEndTime:
				# create empty prog if its a gap
				if lastEndTime < startTime:
					debug( "create empty prog to fill gap progIdx=%s lastEndTime=%s to=%s" % \
						   (progIdx, lastEndTime,startTime) )
					channel.insert(progIdx, createEmptyProg(lastEndTime, startTime))
					progIdx += 1
					added += 1
				else:
					debug( "overlapping times, set start to last end startTime=%s to lastEndTime=%s" % (startTime,lastEndTime) )
					prog[TVData.PROG_STARTTIME] = lastEndTime
					overlapping += 1
			lastEndTime = endTime
			progIdx += 1

		if added or overlapping:
			debug( "checkProgContinuity() added=%s overlapping=%s prog sz=%s" % (added,overlapping,len(channel)) )
	debug("< mytvLib.checkProgContinuity()")
	return channel

###################################################################################################################
def createEmptyProg(startTime, endTime, progORChannel=True):
	if progORChannel:
		title = __language__(204)		# no progs
	else:
		title = __language__(203)		# ch unavailable
	debug("createEmptyProg() %s %s" % (startTime, endTime))
	return {TVData.PROG_STARTTIME:startTime,
			 TVData.PROG_ENDTIME:endTime,
			 TVData.PROG_TITLE:title
			 }

###################################################################################################################
def createEmptyChannel(startTime, endTime):
	return [ createEmptyProg(startTime, endTime, __language__(203)) ]

###################################################################################################################
# set end times to be that of next prog start time. apart from last prog set endtime = 0
# save last prog details
###################################################################################################################
def setChannelEndTimes(progList):
	for progIDX in range(len(progList)):
		try:
			progList[progIDX][TVData.PROG_ENDTIME] = progList[progIDX+1][TVData.PROG_STARTTIME]
		except:
			# last prog
			progList[progIDX][TVData.PROG_ENDTIME] = 0
	return progList


    
###################################################################################################################
class TVChannels:

	CHAN_ID = 0
	CHAN_NAME = 1
	CHAN_IDALT = 2

	def __init__(self):
		debug("> mytvLib.TVChannels() init")

		# how to load channel programmes into channel data store
		self.LOAD_DATA_PREFIX = -1
		self.LOAD_DATA_CLEAR = 0
		self.LOAD_DATA_APPEND = 1
		self.tvdata = TVData()
		self.reset()
		self.loadLogoFilenames()

		debug("< mytvLib.TVChannels() init ")

	def reset(self):
		debug("TVChannels.reset()")
		self.fileDate = None
		self.channelNames = []			# list of all channel ID/Names/IDAlt available. List order is ch display order
		self.errorFiles = []			# additional list of downloaded data files that are in err and need del
		self.connError = False
		self.clearData()

	# not a full reset
	def clearData(self):
		debug("TVChannels.clearData()")
		self.loadedFiles = []			# filenames of channel files. used to prevent reloading
		self.channelsFirstProg = {}		# the first prog displayed for each channel
		self.tvdata.reset()

	def loadLogoFilenames(self):
		debug("TVChannels.loadLogoFilenames()")
		self.datasourceLogos = {}					# dict of channel logo filenames of those viewed
		self.allLogoFiles = listDir(DIR_LOGOS, getFullFilename=True, lower=True) # logo filenames
		# ensure loaded fn are safe. eg change '+' to 'plus', ' ' to '_' etc
		for i, fn in enumerate(self.allLogoFiles):
			self.allLogoFiles[i] = logoSafeName(fn)

	def isFileLoaded(self, filename):
		try:
			self.loadedFiles.index(filename)
			isLoaded = True
		except:
			isLoaded = False
		debug("isFileLoaded() filename=%s %s" % (filename, isLoaded))
		return isLoaded

	# These are used to get/set the first prog displayed for each channel
	def setChannelFirstProgIDX(self, chIDX, idx):
		self.channelsFirstProg[chIDX] = idx

	def getChannelFirstProgIDX(self, chIDX):
		try:
			idx = self.channelsFirstProg[chIDX]
		except:
			idx = 0
		debug("getChannelFirstProgIDX() chIDX=%s btn idx=%s" % (chIDX,idx))
		return idx

	def resetChannelFirstProgIDX(self):
		self.channelsFirstProg = {}

	def getLogo(self, allChIDX):
		debug("> mytvLib.getLogo() allChIDX=%i" % allChIDX)

		def getLogoFilesIdx(name):
			idx = -1
			extList = ('.gif','.png','.jpg')
			for ext in extList:
				try:
					idx = self.allLogoFiles.index(name + ext)
					break
				except ValueError:
					idx = -1
			return idx

		filename = ''
		try:
			# check if already stored
			chID = ''
			chListData = self.channelNames[allChIDX]
			chID = logoSafeName(chListData[0]).lower()
			filename = self.datasourceLogos[chID]
		except:
			# " filename compare against chName"
			try:
				chName = logoSafeName(chListData[1]).lower()
				idx = getLogoFilesIdx(chName)
				if idx < 0:
					raise	# not found
				filename = os.path.join(DIR_LOGOS, self.allLogoFiles[idx])
			except:
				# " filename compare against chID"
				try:
					idx = getLogoFilesIdx(chID)
					if idx < 0:
						raise	# not found
					filename = os.path.join(DIR_LOGOS, self.allLogoFiles[idx])
				except:
					# " filename compare against chAltID"
					try:
						chAltID = logoSafeName(chListData[2]).lower()
						idx = getLogoFilesIdx(chAltID)
						if idx < 0:
							raise	# not found
						filename = os.path.join(DIR_LOGOS, self.allLogoFiles[idx])
					except:
						debug("logo not found by any match! (chName,chID,chAltID)")

			if not filename:
				filename = LOGO_FILENAME

			if chID and filename:
				self.datasourceLogos[chID] = xbmc.makeLegalFilename(filename)

		debug("< mytvLib.getLogo() " + filename)
		return filename


	################################################################################################################
	# append or prefix programme list into channel.
	# ensure channel doesnt contain duplicate starttimes
	# ensure channel prog start/end continuity
	################################################################################################################
	def storeChannel(self, appendORprefix, chIDX, progList, chID, chName, chAltID):
		debug("> mytvLib.storeChannel() appendORprefix=%s chIDX=%s chID=%s" % (appendORprefix,chIDX,chID))
		changed = False

		# is channel in data store?
		if not self.tvdata.hasChannel(chIDX):
			self.tvdata.addChannel(progList, chID, chName, chAltID)
		else:
			# ADD NEW PROGS TO EXISTING CHANNEL
			changed = False
			channel = self.tvdata.getChannel(chIDX)
			debug("existing channel sz=%i progList sz=%i" % (len(channel), len(progList)))

			# append or prefix programmes to channels programmeList
			if appendORprefix:						# APPEND
				debug("APPEND progs")
				lastEndTime = channel[-1][TVData.PROG_ENDTIME]
				newFirstStartTime = progList[0][TVData.PROG_STARTTIME]
				newFirstEndTime = progList[0][TVData.PROG_ENDTIME]

				if lastEndTime == 0 and newFirstStartTime == 0:
					debug("set last end to new first end")
					channel[-1][TVData.PROG_ENDTIME] = newFirstEndTime
					# del first of new
					del progList[0]

				elif lastEndTime == 0 and newFirstStartTime:
					debug("set last end to new first start. 0 %s" % newFirstStartTime)
					channel[-1][TVData.PROG_ENDTIME] = newFirstStartTime

				elif lastEndTime and newFirstStartTime == 0:
					debug("set new first start to last end %s 0" % lastEndTime)
					progList[0][TVData.PROG_STARTTIME] = lastEndTime

				elif lastEndTime and newFirstStartTime:
					# check for gap
					if lastEndTime != newFirstStartTime:
						debug("fill gap lastEndTime=%s to=%s" % (lastEndTime,newFirstStartTime))
						channel.append(createEmptyProg(lastEndTime, newFirstStartTime, True))

				# append new progs to existing
				if progList:
					channel.extend(progList)
					self.tvdata.setChannel(chIDX, channel)
					changed = True
			else:									# PREFIX
				debug("PREFIX progs")
				firstStartTime = channel[0][TVData.PROG_STARTTIME]
				newLastEndTime = progList[-1][TVData.PROG_ENDTIME]

				if newLastEndTime == 0 and firstStartTime:
					debug("set new last end to first start 0 %s" % firstStartTime)
					progList[-1][TVData.PROG_ENDTIME] = firstStartTime

				elif newLastEndTime and firstStartTime == 0:
					debug("set first start to new last end %s 0 " % newLastEndTime)
					channel[0][TVData.PROG_STARTTIME] = newLastEndTime

				elif newLastEndTime and firstStartTime:
					# check for gap
					if newLastEndTime != firstStartTime:
						debug("fill gap lastEndTime=%s to=%s" % (newLastEndTime,firstStartTime))
						progList.append(createEmptyProg(newLastEndTime, firstStartTime, True))

				channel = progList + channel
				self.tvdata.setChannel(chIDX, channel)
				changed = True

			if changed:
				debug("updated channel sz=%i using progList sz=%i" % \
					  (len(self.tvdata.getChannel(chIDX)), len(progList)))

		debug("< mytvLib.storeChannel() changed=%s" % changed)
		return changed

	################################################################################################################
	# Fetch/Load as many channels that will fill a screen.
	# allChIDX - idx into all channels list
	# epgChIDX - idx of onscreen channel and used for data store access to channel
	# maxFetch - max channels to load for a screen full
	# dayDelta - day offset from today
	# fileDate - YYYYMMDD based on dayDelta
	# loadDataAction - indicates to prefix or append new programmes into channels store
	################################################################################################################
	def loadChannels(self, actualChIDX, epgChIDX, maxFetch, dayDelta, fileDate, loadDataAction):
		debug("> mytvLib.******* loadChannels() actualChIDX=%s epgChIDX=%s maxFetch=%s dayDelta=%s fileDate=%s loadDataAction=%s" % \
				  (actualChIDX, epgChIDX, maxFetch, dayDelta, fileDate, loadDataAction))

		logFreeMem("loadChannels start")
#		global dataSource
		
		# clear data store if required
		if loadDataAction == self.LOAD_DATA_CLEAR:
			self.clearData()

		def isErrorFile(fn, addFile=False):
			if fn in self.errorFiles:
				found = True
			else:
				found = False
				if addFile:
					self.errorFiles.append(fn)
			debug("isErrorFile() addFile=%s found=%s" % (addFile,found))
			return found

		# determine epg chIDX of channelID
		if epgChIDX < maxFetch:
			MAX_FETCH = maxFetch - epgChIDX
		elif epgChIDX == maxFetch:
			MAX_FETCH = 1
		else:
			MAX_FETCH = maxFetch

		if len(self.channelNames) < MAX_FETCH:
			MAX_FETCH = len(self.channelNames)
		fetchCount = 0
		showingDialog = False
		displayDate = getDisplayDate(fileDate)

		while actualChIDX < len(self.channelNames) and fetchCount < MAX_FETCH:
			debug("FETCHING actualChIDX=%s epgChIDX=%s fetchCount=%s/%s" % (actualChIDX,epgChIDX,fetchCount+1,MAX_FETCH))

			try:
				# make filename
				chID, chName, chIDAlt = self.getChannelInfo(actualChIDX)
				filename =  os.path.join(DIR_CACHE, "%s_%s.dat" % (chID,fileDate))
				filename = xbmc.makeLegalFilename(filename)

				if not self.isFileLoaded(filename):
					progList = []
					fetchStr = "%s / %s" % (fetchCount+1,MAX_FETCH)

					if fileExist(filename):
						# load channel from file
						progList = loadChannelFromFile(filename)
					elif not self.connError and not isErrorFile(filename) and dayDelta > -2 and dayDelta < 7:
						# LOAD FROM DATASOURCE
						if not showingDialog:
							try:
								dsName = mytvGlobals.dataSource.getName()
								dialogProgress.create(dsName, displayDate, chName, fetchStr)
								showingDialog = True
							except: pass
						else:
							percent = int( float( fetchCount * 100) / MAX_FETCH )
							dialogProgress.update(percent, displayDate, chName, fetchStr)

						progList = mytvGlobals.dataSource.getChannel(filename, chID, chName, dayDelta, fileDate)
						if progList:
							# CHECK CONTINUITY AND SAVE TO FILE
							saveChannelToFile(progList, filename)
						elif progList == "":                        # no data, not comms err
							progList = []
						elif progList == None:  		# could be None, -1 - comms err
							if xbmcgui.Dialog().yesno(__language__(0), __language__(100), __language__(306)):	# retry ?
								continue
							else:
								self.connError = True				# net conn is unavailable, no more downloads
								progList = []

					# conn error or empty progList make an empty prog list
					if self.connError or not progList:
						debug("no progs loaded")
						isErrorFile(filename, True)					# add if not already added
						# set endtime to end of day in secs
						startSecs = time.mktime(time.strptime(time.strftime(fileDate+"000000"),"%Y%m%d%H%M%S"))
						endSecs = startSecs + TVTime.DAY_SECS
						if self.connError:
							debug("make connError empty")
							progList = [createEmptyProg(startSecs, endSecs, False)]		# ch unavailable
						else:
							progList = [createEmptyProg(startSecs, endSecs, True)]		# no progs

					# store channel
					appendORprefix = (loadDataAction != self.LOAD_DATA_PREFIX)
					self.storeChannel(appendORprefix, epgChIDX, progList, chID, chName, chIDAlt)
					self.loadedFiles.append(filename)
			except:
				handleException("loadChannels()")

			fetchCount += 1
			epgChIDX += 1
			actualChIDX += 1

		if showingDialog:
			dialogProgress.close()

#		print "showChannels=", self.tvdata.showChannels()
#		print "self.tvdata.channelInfo=", self.tvdata.channelInfo

		logFreeMem("loadChannels end")
		debug("< mytvLib.loadChannels() fetchCount=%s" % fetchCount)
		return fetchCount

	#############################################################################################################
	# get prog on channel whos end time is after given time.
	#############################################################################################################
	def getProgAtTime(self, chIDX, intervalSecs):
		debug("> mytvLib.getProgAtTime() chIDX=%s intervalSecs=%s" % (chIDX, intervalSecs))
#		startSecs = time.clock()
#		print "startSecs=%s" % startSecs

		progList = self.tvdata.getChannel(chIDX)
		progCount = len(progList)

		# set prog to start searching from
		progSearchIDX = self.getChannelFirstProgIDX(chIDX)-4 # assumed max # of progs in a time interval
		if progSearchIDX < 0:
			progSearchIDX = 0

		debug( "checking progIDX range %s to %s" % (progSearchIDX, progCount) )
		progIDX = progSearchIDX
		for checkedCount, prog in enumerate(progList[progSearchIDX:]):	# start IDX to end
			startTime = self.tvdata.getProgAttr(prog, TVData.PROG_STARTTIME)
			endTime = self.tvdata.getProgAttr(prog, TVData.PROG_ENDTIME)
			title = self.tvdata.getProgAttr(prog, TVData.PROG_TITLE)
			if startTime <= intervalSecs and (endTime > intervalSecs or endTime==0):
				# found
				debug("getProgAtTime() FOUND checkedCount=%s start=%s end=%s" % \
											  (checkedCount, startTime, endTime))
				self.setChannelFirstProgIDX(chIDX, progIDX)
				break
			elif startTime > intervalSecs and checkedCount == 0:
				debug("getProgAtTime() first prog checked started after time, set to load PREV data")
				self.setChannelFirstProgIDX(chIDX, 0)
				progIDX = -1			
				break
			elif endTime <= intervalSecs and progIDX == progCount-1:
				debug("getProgAtTime() last prog checked ended before time, set to load NEXT data")
				self.setChannelFirstProgIDX(chIDX,progIDX)
				progIDX = -2			
				break
			progIDX += 1

#		endSecs = time.clock()
#		print "endSecs=%s" % endSecs
#		print "process secs=%s" % (endSecs - startSecs)
		debug("< mytvLib.getProgAtTime() progIDX=%i" % progIDX)
		return progIDX

# data file date
	def getFileSaveDate(self):
		debug("getFileSaveDate() date: " + self.fileDate)
		return self.fileDate

	def setFileSaveDate(self, fileDate):
		debug("setFileSaveDate() date: %s" % fileDate)
		self.fileDate = fileDate

# Channel list, each channel is a list holding [chid, ch name<,alt ch id>]
	def loadDatasourceChannelNames(self, justHDChannels=False):
		debug("> mytvLib.loadDatasourceChannelNames() justHDChannels=%s" % justHDChannels)
#		global dataSource
		self.channelNames = mytvGlobals.dataSource.getChannels()
		sz = 0
		if not self.channelNames:
			messageOK(__language__(111),__language__(112))  # no ch list
		elif justHDChannels:
			sz = self.getHDChannels()
		else:
			sz = len(self.channelNames)

		debug("< mytvLib.loadDatasourceChannelNames() channels=%s" % sz)
		return sz

	def getHDChannels(self, countOnly=False):
		debug("> mytvLib.getHDChannels() countOnly=%s" % countOnly)
		hdList = []
		if self.channelNames:
			for ch in self.channelNames:
				if find(ch[1], 'HD') >=0 or find(ch[0], 'HD') >=0:	# check cName and chID
					hdList.append(ch)

			if not countOnly and hdList:
				self.channelNames = hdList[:]	# copy
		sz = len(hdList)
		debug("< mytvLib.getHDChannels() count=%s" % sz)
		return sz

	def getChannelNames(self):
		return self.channelNames

	def getChannelNamesSZ(self):
		return len(self.channelNames)

	def getChannelName(self, allChIDX):
		return self.getChannelAttr(allChIDX, TVChannels.CHAN_NAME)
	def getChannelID(self, allChIDX):
		return self.getChannelAttr(allChIDX, TVChannels.CHAN_ID)
	def getChannelIDAlt(self, allChIDX):
		return self.getChannelAttr(allChIDX, TVChannels.CHAN_IDALT)

	def getChannelAttr(self, allChIDX, attr):
		try:
			return self.channelNames[allChIDX][attr]
		except:
			return ''

	def getChannelInfo(self, allChIDX):
		try:
			chID, chName, chIDAlt = self.channelNames[allChIDX]
		except:
			try:
				chIDAlt = ''
				chID, chName = self.channelNames[allChIDX]
			except:
				chID = ''
				chName = ''
		debug( "getChannelInfo() chID=%s, chName=%s, chIDAlt=%s" %  (chID, chName, chIDAlt))
		return chID, chName, chIDAlt

# Channels
	def addChannel(self, progList, chID, chName, chIDAlt):
		self.tvdata.addChannel(progList, chID, chName, chIDAlt)

	def getChannelsSZ(self):
		return self.tvdata.getChannelsCount()

	def getChannelSZ(self, chIDX):
		return self.tvdata.getChannelProgCount(chIDX)

	def getChannel(self, chIDX):
		return self.tvdata.getChannel(chIDX)

# Channel Programmes
	def getProgramme(self, chIDX, progIDX):
		return self.tvdata.getProg(chIDX, progIDX)

	def getProgAttr(self, prog, attr):
		return self.tvdata.getProgAttr(prog, attr)

	def getProgAttrByIdx(self, chIDX, progIDX, attr):
		return self.tvdata.getProgAttrByIdx(chIDX, progIDX, attr)

	def deleteErrorFiles(self):
		debug("deleteErrorFiles()")
		for file in self.errorFiles:
			deleteFile(file)

	def cleanup(self):
		debug("TVChannels().cleanup()")
		deleteFile(os.path.join(DIR_CACHE, "temp.dat"))
		deleteFile(os.path.join(DIR_CACHE, "temp.html"))
		deleteCacheFiles()
		self.deleteErrorFiles()


########################################################################################################
class myTVFavShows(xbmcgui.Window):

	FAVSHOWS_FILENAME = os.path.join(DIR_USERDATA, 'favshows.dat')
	
	def __init__(self):
		debug("> mytvLib.myTVFavShows().init")

		self.favShowsList = []
#		global dataSource
#		if not mytvGlobals.dataSource:
#			self.dataSource = importDataSource()
#		else:
#			self.dataSource = dataSource

		# init start time
		self.currentTime = time.mktime(time.localtime(time.time()))
		self.startupCurrentTime = self.currentTime
		if not mytvGlobals.dataSource:
			messageOK("No DataSource imported","Use myTV to configure a DataSource.")

		self.tvdata = TVData()
		debug("< mytvLib.myTVFavShows().init")

	def deleteSaved(self):
		debug("favShows.deleteSaved()")
		deleteFile(self.FAVSHOWS_FILENAME)
		self.favShowsList = []

	def onAction(self, action):
		try:
			actionID = action.getId()
			buttonCode = action.getButtonCode()
		except: return

		if actionID in CANCEL_DIALOG + EXIT_SCRIPT or buttonCode in CANCEL_DIALOG +EXIT_SCRIPT:
			self.close()

	def onControl(self, control):
		if control == self.favShowsCONTROLS[self.CTRL_PREV_BTN]:
			debug("favShowsCONTROL_PREV_BTN")
			if self.currentTime > self.startupCurrentTime:
				self.currentTime -= (86400 * 7)					# sub 7 days
				daysList = self.searchFavShows(self.favShowsList, self.currentTime)
				self.loadLists(daysList)
			else:
				debug("action ignored, going back past startup time")

			# turn off/on prev btn as needed
			visible = self.currentTime > self.startupCurrentTime
			self.favShowsCONTROLS[self.CTRL_PREV_BTN].setVisible(visible)
			if not visible:
				self.setFocus(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])

		elif control == self.favShowsCONTROLS[self.CTRL_NEXT_BTN]:
			debug("favShowsCONTROL_NEXT_BTN")
			self.currentTime += (7 * 86400)					# add 7 days
			daysList = self.searchFavShows(self.favShowsList, self.currentTime)
			self.loadLists(daysList)

			# turn off/on prev btn as needed
			self.favShowsCONTROLS[self.CTRL_PREV_BTN].setVisible(self.currentTime > self.startupCurrentTime)

	def ask(self):
		debug("> mytvLib.myTVFavShows.ask()")

		if not self.favShowsList:
			messageOK(__language__(508), __language__(213))
		else:
			self.setupFavShowDisplay()
			daysList = self.searchFavShows(self.favShowsList, self.currentTime)
			self.loadLists(daysList)
			self.doModal()

		debug("< mytvLib.myTVFavShows.FavSHows().ask()")

	def setupFavShowDisplay(self):
		debug("> mytvLib.myTVFavShows.setupFavShowDisplay")

		setResolution(self)
		xbmcgui.lock()

		# BACKGROUND SKIN
		try:
			self.addControl(xbmcgui.ControlImage(0,0, REZ_W, REZ_H, BACKGROUND_FILENAME))
		except: pass

		# fav show display controls
		self.CTRL_PREV_BTN = 'prevbtn'
		self.CTRL_NEXT_BTN = 'nextbtn'
		self.favShowsCONTROLS = {}
		self.favShowsCONTROLS_LIST = []
		self.favShowsCONTROLS_LBL = []
		self.favShowsCONTROLS_BTN = []

		titleH = 23
		labelH = 20
		xpos = 5
		ypos = titleH

		# listH determined by rez
		numListRows = 3
		listW = 230
		epgH = REZ_H - titleH - (labelH * numListRows)
		debug("epgH = " + str(epgH))
		listH = epgH / numListRows
		debug("listH = " + str(listH))
		btnH = 30
		btnW = listW-10

		# display title
		self.addControl(xbmcgui.ControlLabel(xpos, 0, 0, titleH, __language__(508), FONT13, "0xFFFFFF00"))

		# create each day , incl. prev/next btns as a day each
		for day in range(7):
			# day header label
			ctrl = xbmcgui.ControlLabel(xpos, ypos, listW, labelH, '', FONT11, "0xFFFFFF99")
			self.favShowsCONTROLS_LBL.append(ctrl)
			self.addControl(ctrl)

			# create a control btn as background
			ctrl = xbmcgui.ControlButton(xpos-3, ypos+labelH-3, listW+6, listH+6, '', \
											FRAME_FOCUS_FILENAME, FRAME_NOFOCUS_FILENAME)
			self.favShowsCONTROLS_BTN.append(ctrl)
			self.addControl(ctrl)

			# list - allow for extra unused spinner space at bottom
			ctrl = xbmcgui.ControlList(xpos, ypos + labelH, listW+5, listH+20, FONT10, imageWidth=0, \
									   itemTextXOffset=0, itemHeight=16, alignmentY=XBFONT_CENTER_Y)
			self.favShowsCONTROLS_LIST.append(ctrl)
			self.addControl(ctrl)
			ctrl.setPageControlVisible(False)

			# new row
			if day == 2:
				xpos = 5
				ypos += labelH + listH + 4
			elif day == 5:
				xpos = listW + 10
				ypos += labelH + listH + 4
			else:
				xpos += listW +10

		# PREV btn
		x = 5
		y = int(REZ_H - (listH/2) - (btnH/2))
		ctrl = xbmcgui.ControlButton(x, y, btnW, btnH, '< ' + __language__(588),alignment=XBFONT_CENTER_X)
		self.favShowsCONTROLS[self.CTRL_PREV_BTN]=ctrl
		self.addControl(ctrl)

		# NEXT btn
		x += listW + listW + 15
		ctrl = xbmcgui.ControlButton(x, y, btnW, btnH, __language__(587) + ' >',alignment=XBFONT_CENTER_X)
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN]=ctrl
		self.addControl(ctrl)

		# NAVIGATION - any ctrl to next adjacent ctrl
		day = 0
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS_BTN[day+1])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS[self.CTRL_PREV_BTN])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS_BTN[day+3])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS_BTN[day+1])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS_BTN[day-1])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS_BTN[6])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS_BTN[day+3])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS_BTN[day+1])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS_BTN[day-1])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS_BTN[day+3])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS_BTN[day+1])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS_BTN[day-1])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS_BTN[day-3])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS[self.CTRL_PREV_BTN])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS_BTN[day+1])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS_BTN[day-1])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS_BTN[day-3])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS_BTN[6])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS[self.CTRL_PREV_BTN])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS_BTN[day-1])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS_BTN[day-3])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])

		day += 1
		self.favShowsCONTROLS_BTN[day].controlRight(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])
		self.favShowsCONTROLS_BTN[day].controlLeft(self.favShowsCONTROLS[self.CTRL_PREV_BTN])
		self.favShowsCONTROLS_BTN[day].controlUp(self.favShowsCONTROLS_BTN[4])
		self.favShowsCONTROLS_BTN[day].controlDown(self.favShowsCONTROLS_BTN[1])

		# prev btn
		self.favShowsCONTROLS[self.CTRL_PREV_BTN].controlRight(self.favShowsCONTROLS_BTN[6])
		self.favShowsCONTROLS[self.CTRL_PREV_BTN].controlLeft(self.favShowsCONTROLS_BTN[5])
		self.favShowsCONTROLS[self.CTRL_PREV_BTN].controlUp(self.favShowsCONTROLS_BTN[3])
		self.favShowsCONTROLS[self.CTRL_PREV_BTN].controlDown(self.favShowsCONTROLS_BTN[0])
		self.favShowsCONTROLS[self.CTRL_PREV_BTN].setVisible(False)

		# next btn
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN].controlRight(self.favShowsCONTROLS_BTN[0])
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN].controlLeft(self.favShowsCONTROLS_BTN[6])
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN].controlUp(self.favShowsCONTROLS_BTN[5])
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN].controlDown(self.favShowsCONTROLS_BTN[2])
		self.favShowsCONTROLS[self.CTRL_NEXT_BTN].setVisible(True)

		self.setFocus(self.favShowsCONTROLS[self.CTRL_NEXT_BTN])
		xbmcgui.unlock()
		debug("< mytvLib.myTVFavShows.setupFavShowDisplay")

	def addToFavShows(self, showName, chID, chName):
		debug("> mytvLib.myTVFavShows.addToFavShows()")
		success = False

		if not showName:
			messageOK(__language__(507), __language__(123))
			debug("< mytvLib.myTVFavShows.addToFavShows() bad prog")
			return False

		elif not xbmcgui.Dialog().yesno(__language__(507), chName, showName):	# add ?
			debug("< mytvLib.myTVFavShows.addToFavShows() cancelled")
			return False

		elif not self.favShowsList:
			self.loadFavShows()

		# check for duplicate show selection, unique to channel only
		dup = False
		for show in self.favShowsList:
			loadedShowName = show[0]
			loadedChID = show[1]
			if showName == loadedShowName and chID == loadedChID:
				dup = True
				break

		# save to file
		if not dup:
			self.favShowsList.append([showName, chID, chName])
			success = self.saveFavShows()
		else:
			messageOK(__language__(507), __language__(124))

		debug("< mytvLib.myTVFavShows.addToFavShows() success=%s" % success)
		return success

	def loadFavShows(self):
		debug("> mytvLib.myTVFavShows.loadFavShows()")
		self.favShowsList = []
		if fileExist(self.FAVSHOWS_FILENAME):
			for readLine in file(self.FAVSHOWS_FILENAME):
				title, chID, chName = readLine.split('~')
				self.favShowsList.append([title.decode('latin-1', 'replace').strip(), \
								chID, chName.decode('latin-1', 'replace').strip()])
		debug("< mytvLib.myTVFavShows.loadFavShows() sz: %s" % len(self.favShowsList))

	def saveFavShows(self):
		debug("> mytvLib.myTVFavShows.saveFavShows()")
		success = False
		if not self.favShowsList:
			deleteFile(self.FAVSHOWS_FILENAME)
			success = True
		else:
			try:
				fp = open(xbmc.translatePath(self.FAVSHOWS_FILENAME), 'w')
				for showName, chID, chName in self.favShowsList:
					chID = chID.encode('latin-1', 'replace').strip()
					if not isinstance(showName, unicode):
						showName = unicode(showName,'latin-1').strip()
					showName = showName.encode('latin-1', 'replace')
					if not isinstance(chName, unicode):
						chName = unicode(chName,'latin-1').strip()
					chName = chName.encode('latin-1', 'replace').strip()
					rec = "%s~%s~%s\n" % (showName, chID, chName)
					fp.write(rec)
				fp.close()
				success = True
			except:
				deleteFile(self.FAVSHOWS_FILENAME)
				handleException()
		debug("< mytvLib.myTVFavShows.saveFavShows() success=%s" % success)
		return success

	def getTitles(self):
		debug("> mytvLib.myTVFavShows.getTitles()")
		if not self.favShowsList:
			self.loadFavShows()

		titleList = []
		for title, chID, chName in self.favShowsList:
			titleList.append(title)

		debug("< mytvLib.myTVFavShows.getTitles() sz: %s" % len(titleList))
		return titleList

	def manageFavShows(self):
		debug("> mytvLib.myTVFavShows.manageFavShows()")

		deleted = False
		if not self.favShowsList:
			messageOK(__language__(510), __language__(213))
		else:
			heading = "%s %s" % (__language__(510), __language__(586))
			while True:
				# create menu
				menu = [__language__(500)]
				self.favShowsList.sort()
				for showName, chID, chName in self.favShowsList:
					showName = showName.encode('latin-1', 'replace')
					chName = chName.encode('latin-1', 'replace')
					menu.append(xbmcgui.ListItem(showName, chName))

				selectDialog = DialogSelect()
				selectDialog.setup(heading, rows=len(menu), width=600, panel=mytvGlobals.DIALOG_PANEL)
				selectedPos, acton = selectDialog.ask(menu)
				if selectedPos <= 0:
					break		# stop

				showName, chID, chName = self.favShowsList[selectedPos-1]
				if xbmcgui.Dialog().yesno(__language__(510), showName, chName, "", __language__(355), __language__(356)):
					del self.favShowsList[selectedPos-1]
					deleted = True

				del selectDialog

			if deleted:
				self.saveFavShows()	# write whole list
		debug("< mytvLib.myTVFavShows.manageFavShows() deleted="+str(deleted))
		return deleted

	def deleteShow(self, title, chID):
		debug("> mytvLib.myTVFavShows.deleteShow() title=%s chID=%s" % (title, chID))

		if xbmcgui.Dialog().yesno(__language__(510), title, "", "", __language__(355), __language__(356)):
			# find show on channel
			deleted = False
			for i, rec in enumerate(self.favShowsList):
				showName, showChID, chName = rec
				if showName == title and showChID == chID:
					del self.favShowsList[i]
					self.saveFavShows()
					deleted = True
					break

		debug("< mytvLib.myTVFavShows.deleteShow() deleted=%s" % deleted)
		return deleted

	def searchFavShows(self, showList, currentTime):
		debug("> mytvLib.myTVFavShows.searchFavShows() currentTime=" + str(currentTime))
		dialogProgress.create(__language__(508), __language__(300))

		# for each day, examine just the channel stored against show
		commsError = False
		daysList = []
		for day in range(7):
			fileDate = getTodayDate(currentTime)
			debug("day=%s fileDate=%s" % (day, fileDate))

			dayList = []
			# examine all progs on this channel, looking each occurance for show
			for showDetails in showList:
				try:
					show, chID, chName = showDetails
					chName = chName.strip()
				except:
					# unpack error, ignore show
					continue

				# load channel progs
				filename =  os.path.join(DIR_CACHE, "%s_%s.dat" % (chID,fileDate))
				filename = xbmc.makeLegalFilename(filename)
				if fileExist(filename):
					# load channel from file
					progList = loadChannelFromFile(filename)
				elif not commsError:
					progList = mytvGlobals.dataSource.getChannel(filename, chID, chName, day, fileDate)
					if progList:
						saveChannelToFile(progList, filename)

				if progList == None:
					commsError = True
				elif progList:
					# examine all progs on this channel for our fav show name
					showUPPER = show.upper()
					for prog in progList:
						title = prog[TVData.PROG_TITLE].upper()
						if title.startswith(showUPPER):
							startTime = prog[TVData.PROG_STARTTIME]
							dayList.append([show, chName[:6].strip(), startTime])

			daysList.append(dayList)
			currentTime += 86400					# add 1 day

		dialogProgress.close()
		debug("< mytvLib.myTVFavShows.searchFavShows()")
		return daysList

	# load shows into relevant day list
	def loadLists(self, daysList):
		debug("> mytvLib.myTVFavShows.loadLists()")
		xbmcgui.lock()

		currentTime = self.currentTime
		for dayIDX in range(7):
			dayList = daysList[dayIDX]

			# setup list title to be DATE
			listTitle = time.strftime("%a %d %b",time.localtime(currentTime))
			self.favShowsCONTROLS_LBL[dayIDX].setLabel(listTitle)

			self.favShowsCONTROLS_LIST[dayIDX].reset()
			for title, chName, startTime in dayList:
				if startTime:
					startDate = time.strftime("%H:%M", time.localtime(startTime))
					lbl2= chName + "," + startDate
				else:
					lbl2 = ''
				self.favShowsCONTROLS_LIST[dayIDX].addItem(xbmcgui.ListItem(title, label2=lbl2))

			currentTime += 86400	# add 1 day
		xbmcgui.unlock()
		debug("< mytvLib.myTVFavShows.loadLists()")


###################################################################################################################
class TVTime:

	HALF_HOUR_SECS = 1800
	HOUR_SECS = 3600
	DAY_SECS = 86400

	def __init__(self):
		debug("> mytvLib.**** TVTime() init ****")
		self.intervalMins = 30
		self.intervalSecs = self.intervalMins * 60
		debug("intervalMins: " + str(self.intervalMins) + "  intervalSecs: " + str(self.intervalSecs))
		self.maxTimeBarIntervals = 5					# incl date
		self.timeIntervals = []							# [HH:MM, secs]
		self.dayDelta = 0
		self.startupTime = 0

		self.reset()
		debug("< mytvLib.**** TVTime() currentTime: " + str(self.currentTime))

	def reset(self):
		debug("TVTime.reset()")
		self.setToSystemTime()
		self.dayDelta = 0

	def getStartupTime(self):
		return self.startupTime

	def getIntervalMins(self):
		return self.intervalMins

	def getMaxTimeBarIntervals(self):
		return self.maxTimeBarIntervals
	
	def getDayDelta(self):
		debug("getDayDelta() : " + str(self.dayDelta))
		return self.dayDelta

	def setDayDelta(self, delta):
		self.dayDelta = delta
		debug("setDayDelta() new dayDelta=%i" % self.dayDelta)

	def updateDayDelta(self, delta):
		self.dayDelta += delta
		debug("updateDayDelta() new dayDelta: " + str(self.dayDelta))

	def updateInterval(self, numIntervals):
		self.currentTime += (self.intervalSecs * numIntervals)
		debug("updateInterval() new currentTime: " + str(self.currentTime))
		return self.currentTime

	def nextTimeInterval(self, startTime):
		newTime = startTime + self.intervalSecs
		return newTime

	def setupTimeBar(self, intervals, use24Clock=True):
		debug("> mytvLib.setupTimeBar()  intervals=%s use24Clock=%s" % (intervals, use24Clock))
		
		self.timeIntervals = []
		date = time.strftime("%a %d %b",time.localtime(self.currentTime))
		self.timeIntervals.append([date, self.currentTime])

		# make number of time intervals
		secs = self.currentTime

		for i in range(intervals):
			if use24Clock:
				format = "%H:%M"
			else:
				format = "%I:%M %p"
			intervalTimeStr = time.strftime(format, time.localtime(secs))
			self.timeIntervals.append([intervalTimeStr, secs])
			secs += self.intervalSecs

		sz = len(self.timeIntervals)
		debug("< mytvLib.setupTimeBar() sz=%s" % sz)
		return sz

	def roundDownToInterval(self, secs):
		debug("> mytvLib.roundDownToInterval() secs: " + str(secs))
		localtime = time.localtime(secs)

		if(localtime.tm_min < self.intervalMins):
			debug("set tm_min to 00")
			leftoverSecs = (localtime.tm_min * 60) + localtime.tm_sec						# SETS TM_MIN = 00
		else:
			debug("set tm_min to 30")
			leftoverSecs = (localtime.tm_min * 60) + localtime.tm_sec - self.HALF_HOUR_SECS	# SETS TM_MIN = 30
		secs -= leftoverSecs
		debug("< mytvLib.roundDownToInterval() secs: " + str(secs))
		return secs

	def getTimeIntervalSZ(self):
		return len(self.timeIntervals)

	def getTimeInterval(self, interval):
		return self.timeIntervals[interval]

	def setToSystemTime(self):
		self.currentTime = self.getSystemTime()
		self.currentTime = self.roundDownToInterval(self.currentTime)
		self.startupTime = self.currentTime
		debug("setToSystemTime() new rounded down currentTime: " + str(self.currentTime))
		return self.currentTime

	def getSystemTime(self):
		return time.mktime(time.localtime())

	def getCurrentTime(self):
		debug("getCurrentTime() currentTime: " + str(self.currentTime))
		return int(self.currentTime)

	def setCurrentTime(self, newTime):
		self.currentTime = newTime
		debug("setCurrentTime() new currentTime: " + str(self.currentTime))

	def updateCurrentTime(self, updateSecs):
		self.currentTime += updateSecs
		debug("updateCurrentTime() new currentTime: " + str(self.currentTime))

	def timeToSecs(self, baseTime, hour, mins):
		debug("> mytvLib.timeToSecs() baseTime=%s hour=%s mins=%s" % (baseTime, hour, mins))
		newTimeStr = str(getTodayDate(baseTime))
		self.currentTime = time.mktime(time.strptime(newTimeStr,"%Y%m%d%H%M"))
		debug("< mytvLib.timeToSecs() currentTime=%s" % self.currentTime)

	def resetToMidnight(self):
		self.timeToSecs(time.localtime(), "00", "00")
		debug("resetToMidnight() NEW currentTime: " + str(self.currentTime))
		return self.currentTime

	def setCurrentTimeFromHHMM(self, HHMM):
		self.timeToSecs(time.localtime(self.currentTime), HHMM[:2], HHMM[-2:])
		debug("setCurrentTimeFromHHMM currentTime=%s"  % self.currentTime)
		return self.currentTime

	def timeToFileDate(self, baseTimeSecs=0):
		if not baseTimeSecs:
			baseTimeSecs = self.getCurrentTime()
		fileDate = str(getTodayDate(baseTimeSecs))
		return fileDate

	def timeToHHMM(self, secs, use24HourClock=True):
		if use24HourClock:
			format = "%H:%M"
		else:
			format = "%I:%M %p"
		text = time.strftime(format, time.localtime(secs))
		# strip leading 0 in 12hr mode
		if not use24HourClock:
			if text[0] == '0': text = text[1:]
		return text

###################################################################################################################
def logoSafeName(text):
    return text.lower().replace(' ','_').replace('+','plus')

#######################################################################################################################    
# View the save programme template options
#######################################################################################################################    
class ProgrammeSaveTemplate:
	def __init__(self):
		debug("> mytvLib.ProgrammeSaveTemplate.init()")

		self.TEMPLATES = [['C','Channel ID', self.getChannelID],
						['c','Channel Name', self.getChannelName],
						['T','Title', self.getTitle],
						['N','Description', self.getDesc],
						['S','Start Date/Time DD//MM//YYYY HH:MM', self.getDateFullS],
						['s','Start Date/Time MM//DD//YYYY HH:MM', self.getDateFulls],
						['E','End Date/Time DD//MM//YYYY HH:MM', self.getDateFullE],
						['e','End Date/Time MM//DD//YYYY HH:MM', self.getDateFulle],
						['D','Start Date (DD)', self.getStartDate],
						['d','End Date (DD)', self.getEndDate],
						['M','Start Month (MM)', self.getStartMonth],
						['m','End Month (MM)', self.getEndMonth],
						['Y','Start Year (YYYY)', self.getStartYear],
						['y','End Year (YYYY)', self.getEndYear],
						['H','Start Hour (HH 24hr)', self.getStartHour],
						['h','End Hour (HH 24hr)', self.getEndHour],
						['I','Start Minutes (MM)', self.getStartMins],
						['i','End Minutes (MM)', self.getEndMins],
						['T','Start Seconds since epoch', self.getStartSecs],
						['t','End Seconds since epoch', self.getEndSecs],
						['L','Duration (HH:MM)', self.getDuration],
						['l','Duration (Mins)', self.getDurationMins]]
		self.PREFIX = '$'
		self.KEY = 0
		self.VALUE = 1
		self.FUNC = 2
		self.prog = None
		debug("< mytvLib.ProgrammeSaveTemplate.init()")

	def viewTemplates(self):
		debug("> mytvLib.ProgrammeSaveTemplate.viewTemplates()")
		menu = [__language__(500)]
		for key,value,func in self.TEMPLATES:
			menu.append(xbmcgui.ListItem(self.PREFIX+key, label2=value))

		selectDialog = DialogSelect()
		selectDialog.setup(__language__(548), rows=len(menu), panel=mytvGlobals.DIALOG_PANEL)
		selectDialog.ask(menu)
		del selectDialog
		debug("< mytvLib.ProgrammeSaveTemplate.viewTemplates()")

	def getTemplates(self):
		return self.TEMPLATES

	def validTemplate(self, text):
		debug("> mytvLib.validTemplate: template: %s " % text)
		success = False

		if text:
			matches = self.parseTemplate(text)
			for key in matches:
				success = False
				for template in self.TEMPLATES:
					if template[self.KEY] == key:
						success = True	# found
						break

				if not success:
					break	# abort search

		debug("< mytvLib.validTemplate() success=%s" % success)
		return success

	def getFunc(self,key):
		for template in self.TEMPLATES:
			if template[self.KEY] == key:
				return template[self.FUNC]
		return None

	def parseTemplate(self, template):
		regex = "\\%s(.)" % self.PREFIX
		return findAllRegEx(template, regex)

	def format(self, channelInfo, prog, template):
		debug("> mytvLib.format()")
		self.channelInfo = channelInfo
		self.prog = prog
		try:
			matches = self.parseTemplate(template)
			for match in matches:
				func = self.getFunc(match)
				if func:
					template = replace(template, self.PREFIX+match, func())
		except:
			handleException("ProgrammeSaveTemplate().format()")
			template = ''

		debug("< mytvLib.format()")
		return template

	def getChannelID(self):
		self.channelInfo[TVChannels.CHAN_ID]

	def getChannelIDAlt(self):
		self.channelInfo[TVChannels.CHAN_IDALT]

	def getChannelName(self):
		self.channelInfo[TVChannels.CHAN_NAME]

	def getTitle(self):
		return mytv.tvChannels.getProgAttr(self.prog, TVData.PROG_TITLE)

	def getDesc(self):
		return mytv.tvChannels.getProgAttr(self.prog, TVData.PROG_DESC)

	def getDateFullS(self):
		return time.strftime("%d/%m/%Y %H:%M",time.localtime(self.getStartSecsEpoch()))
	def getDateFullE(self):
		return time.strftime("%d/%m/%Y %H:%M",time.localtime(self.getEndSecsEpoch()))

	def getDateFulls(self):
		return time.strftime("%m/%d/%Y %H:%M",time.localtime(self.getStartSecsEpoch()))
	def getDateFulle(self):
		return time.strftime("%m/%d/%Y %H:%M",time.localtime(self.getEndSecsEpoch()))

	def getStartDate(self):
		return time.strftime("%d",time.localtime(self.getStartSecsEpoch()))
	def getEndDate(self):
		return time.strftime("%d",time.localtime(self.getEndSecsEpoch()))

	def getStartMonth(self):
		return time.strftime("%m",time.localtime(self.getStartSecsEpoch()))
	def getEndMonth(self):
		return time.strftime("%m",time.localtime(self.getEndSecsEpoch()))

	def getStartYear(self):
		return time.strftime("%Y",time.localtime(self.getStartSecsEpoch()))
	def getEndYear(self):
		return time.strftime("%Y",time.localtime(self.getEndSecsEpoch()))

	def getStartHour(self):
		return time.strftime("%H",time.localtime(self.getStartSecsEpoch()))
	def getEndHour(self):
		return time.strftime("%H",time.localtime(self.getEndSecsEpoch()))

	def getStartMins(self):
		return time.strftime("%M",time.localtime(self.getStartSecsEpoch()))
	def getEndMins(self):
		return time.strftime("%M",time.localtime(self.getEndSecsEpoch()))

	def getDuration(self):
		durSecs = self.getEndSecsEpoch() - self.getStartSecsEpoch()
		return time.strftime("%H:%M",time.localtime(durSecs))

	def getDurationMins(self):
		durMins = int((self.getEndSecsEpoch() - self.getStartSecsEpoch()) / 60)
		return str(durMins)

	def getStartSecs(self):
		return str(self.getStartSecsEpoch())
	def getStartSecsEpoch(self):
		return mytv.tvChannels.getProgAttr(self.prog, TVData.PROG_STARTTIME)
	def getEndSecs(self):
		return str(self.getEndSecsEpoch())
	def getEndSecsEpoch(self):
		return mytv.tvChannels.getProgAttr(self.prog, TVData.PROG_ENDTIME)


#################################################################################################################
def downloadLogos(channelNames=[]):
	debug("> mytvLib.downloadLogos()")

	dialogTitle = __language__(556)
	debug("check which channels dont have a logo...")
	if not channelNames:
		channelNames = mytvGlobals.dataSource.getChannels()
	missingList = []
#	dialogProgress.create(dialogTitle, __language__(613) )		# missing logos
	for i, chData in enumerate(channelNames):
		chID = logoSafeName(chData[0])
		chName = logoSafeName(chData[1])
		chIDFn = xbmc.makeLegalFilename(os.path.join(DIR_LOGOS, chID+'.gif'))
		chNameFn = xbmc.makeLegalFilename(os.path.join(DIR_LOGOS, chName+'.gif'))
		
		if not fileExist(chIDFn) and not fileExist(chNameFn):
			missingList.append(i)                                   # save the idx into channelNames
#	dialogProgress.close()
	debug("missing logos=%i" % len(missingList))

	if not missingList:
		debug("< mytvLib.downloadLogos() No missing logos")
		return False

	# DOWNLOAD AVAILABLE COUNTRY LOGOS
	BASE_URL = "http://www.lyngsat-logo.com/tvcountry/"
	COUNTRIES_URL = BASE_URL + "tvcountry.html"
	COUNTRIES_FILE = os.path.join(DIR_CACHE, "tvcountry.html")
	COUNTRY_URL = BASE_URL + "$CCODE.html"

	if not fileExist(COUNTRIES_FILE):
		dialogProgress.create(dialogTitle,__language__(610))		# fetch country codes
		doc = fetchURL(COUNTRIES_URL, COUNTRIES_FILE)
		dialogProgress.close()
	else:
		doc = readFile(COUNTRIES_FILE)

	if not doc:
		messageOK(dialogTitle, "Missing countries logo webpage!", COUNTRIES_URL, os.path.basename(COUNTRIES_FILE))
		deleteFile(COUNTRIES_FILE)
		debug("< mytvLib.downloadLogos() no country page")
		return False

	# get datasource in use country code
	dsNameCC = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_DATASOURCE)[:2]			# eg uk_RadioTimes -> uk

	debug("parse available countries ...")
	menu = [xbmcgui.ListItem(__language__(500),'')]
	ccMatches = parseDocList(doc, 'icon/flags/.*?gif.*?tvcountry/(.*?).html">(.*?)</a')
	selectedPos = 0
	for i, match in enumerate(ccMatches):
		ccode = match[0]
		if ccode == dsNameCC:
			selectedPos = i+1		# allow for exit
		menu.append(xbmcgui.ListItem(cleanHTML(match[1]),ccode.upper()))

	# Choose country code
	selectDialog = DialogSelect()
	selectDialog.setup(__language__(611), rows=len(menu), width=300, panel=mytvGlobals.DIALOG_PANEL)
	selectedPos, action = selectDialog.ask(menu,selectedPos)
	if selectedPos <= 0:
		debug("< mytvLib.downloadLogos() no country picked")
		return False

	# get country page
	ccode,cname = ccMatches[selectedPos-1]
	country_url = COUNTRY_URL.replace('$CCODE', ccode)
	country_fn = os.path.join(DIR_CACHE, os.path.basename(country_url))
	dialogTitle = "%s: %s" % (__language__(556), ccode.upper())
	if fileExist(country_fn):
		doc = readFile(country_fn)
	else:
		dialogProgress.create(dialogTitle, __language__(612))	# fetch filenames
		doc = fetchURL(country_url, country_fn)
		dialogProgress.close()

	if not doc:
		messageOK(dialogTitle, "Failed to fetch logo page", country_url)
		deleteFile(country_fn)
		debug("< mytvLib.downloadLogos() False")
		return False

	# extract logo filename & name
	debug("find downloadable logo url/names ...")
	logonames = []
	urlMatches = parseDocList(doc, 'img src="(../icon/tv/.*?.gif)".*?html">(.*?)<')
	for match in urlMatches:
		logonames.append(match[1].lower().decode('latin-1', "ignore"))		# save name as lower for better comparison later

	if not logonames:
		messageOK(dialogTitle, "No logos found on webpage!", country_url)
		deleteFile(country_fn)
		debug("< mytvLib.downloadLogos() False")
		return False

	# make menu of available logo filenames
	menu = [__language__(500), __language__(614)]
	for logoURL, logoName in urlMatches:
		menu.append(logoName)

	debug("For each missing logo, prompt user to select nearest match...")
	for missingIdx in missingList:
		chData = channelNames[missingIdx]
		chName = chData[1]
		chName = unicode(chData[1], 'latin-1').lower()

		# attempt to match missing logo to nearest logo name
		chNameSZ = len(chName)
		if chNameSZ < 14:
			startPos = chNameSZ
		else:
			startPos = 14
		selectedPos = 1						# menu option 'skip logo'
		for chName_w in range(startPos, 0, -1):
			partChName = chName[:chName_w]
#			print "width=%d partChName='%s' type=%s" % (chName_w, partChName, type(partChName))
			# search throu downloadded logo names for partial match to missing logo name
			for i, logoname in enumerate(logonames):
				if logoname.startswith(partChName):
					selectedPos = i+2		# allow for exit, skip options
					break
			if selectedPos > 1:
				break

		# dialog to pick logo
		selectDialog = DialogSelect()
		title = "%s %s" % (__language__(615), chName)
		selectDialog.setup(title, rows=len(menu), width=320, panel=mytvGlobals.DIALOG_PANEL, useY=True)
		selectedPos, action = selectDialog.ask(menu, selectedPos)
		if selectedPos <= 0:		# exit
			break
		elif selectedPos == 1 or action in CLICK_X + CLICK_Y:		# skip
			continue
		else:
			url = BASE_URL + urlMatches[selectedPos-2][0]					# logo url
			fn = os.path.join(DIR_LOGOS, logoSafeName(chName)+'.gif')		# save logo using ch name
			fn = xbmc.makeLegalFilename(fn)
			dialogProgress.create(dialogTitle, urlMatches[selectedPos-2][1], os.path.basename(fn))
			fetchURL(url, fn, isBinary=True)
			dialogProgress.close()

	# reload logo filenames
	deleteFile(country_fn)
	debug("< mytvLib.downloadLogos() True")
	return True

######################################################################################
def updateScript(silent=False):
	xbmc.output( "> updateScript() silent=%s" % silent)

	import update
	updated = False
	up = update.Update(__language__, __scriptname__)
	version = up.getLatestVersion(silent)
	xbmc.output("Current Version: " + __version__ + " Tag Version: " + version)
	if version != "-1":
		if __version__ < version:
			if xbmcgui.Dialog().yesno( __language__(0), \
								"%s %s %s." % ( __language__(1006), version, __language__(1002) ), \
								__language__(1003 )):
				updated = True
				up.makeBackup()
				up.issueUpdate(version)
		elif not silent:
			dialogOK(__language__(0), __language__(1000))
#	elif not silent:
#		dialogOK(__language__(0), __language__(1030))				# no tagged ver found

	del up
	# dont del module if update in process
	if not updated:
		del sys.modules['update']
	xbmc.output( "< updateScript() updated=%s" % updated)
	return updated

############################################################################################################################
# send WOL if MAC in settings
# checkAwake - if have SMB path, checks HOST & port 139
############################################################################################################################
def sendWOL(checkAwake=True):
	debug("> mytvLib.sendWOL() checkAwake=%s" % checkAwake)
	isAwake = True
	mac = mytvGlobals.config.getSystem(MYTVConfig.KEY_SYSTEM_WOL)
	if mac:
		from wol import WakeOnLan,CheckHost
		WakeOnLan(mac)

		# if reqd, loop to check host is awake
		if checkAwake:
			isAwake = False
			# some saveprogrammes store detail in own config section
			if hasattr(mytvGlobals.saveProgramme, "getSMB"):
				smbPath = mytvGlobals.saveProgramme.getSMB()
			else:
				smbPath = mytvGlobals.config.getSMB(MYTVConfig.KEY_SMB_PATH)
			if not smbPath:
				messageOK(__language__(607),__language__(136))
			else:
				quit = False
				RETRIES = 25
				macMsg = "MAC: %s" % mac
				while not isAwake and not quit:
					for count in range(RETRIES):
						isAwake = CheckHost(smbPath, 139)		# using a SMB port
						if isAwake:
							break
						elif count == 0:
							dialogProgress.create(__language__(607), macMsg, __language__(300))
						else:
							dialogProgress.update(int( float( count * 100) / RETRIES ))

						if ( dialogProgress.iscanceled() ):
							quit = True
						else:
							time.sleep(3)

					try:
						dialogProgress.close()
					except: pass
					if not quit and not isAwake:
						if not xbmcgui.Dialog().yesno(__language__(607), __language__(135)):	# retry ?
							break

		del sys.modules['wol']

	debug("< mytvLib.sendWOL() isAwake=%s" % isAwake)
	return isAwake


###################################################################################################################
# create UserData folders
###################################################################################################################
makeScriptDataDir()
if not os.path.exists(DIR_CACHE):
	try:
		# copy the supplied cache to userdata
		copytree(os.path.join(DIR_RESOURCES, "cache"), DIR_CACHE)
	except:
		makeDir(DIR_CACHE)

# all config settings
mytvGlobals.config = MYTVConfig()

# setup DIALOG_PANEL by checking if exists in skins texture, else use supplied, else fallback to default
mytvGlobals.DIALOG_PANEL = mytvGlobals.config.getDisplay(MYTVConfig.KEY_DISPLAY_DIALOG_PANEL, usePrefixDir=False)
# is name in skin texture?
if not xbmc.skinHasImage(mytvGlobals.DIALOG_PANEL):
	# look throu list of (custom name, skin name, default name)
	panels = ( os.path.splitext(mytvGlobals.DIALOG_PANEL)[0], getSkinName().replace(' ','_'), 'dialog' )
	for panelName in panels:
		mytvGlobals.DIALOG_PANEL = os.path.join(DIR_GFX, "%s_panel.png" % panelName)
		if os.path.isfile(mytvGlobals.DIALOG_PANEL):
			break
debug("mytvLib() DIALOG_PANEL=%s" % mytvGlobals.DIALOG_PANEL)
