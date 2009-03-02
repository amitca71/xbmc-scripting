############################################################################################################
# TV Data source: OurGuide (Australia)
# Notes:
# Configure STATE and REGION
# ChangeLog:
# 10/06/08 Created
############################################################################################################

from bbbGUILib import *
from mytvLib import *
import mytvGlobals

import xbmcgui, re, time
from os import path
from base64 import decodestring

DIALOG_PANEL = sys.modules["mytvLib"].DIALOG_PANEL
__language__ = sys.modules["__main__"].__language__

STATES = ('NSW','NT','QLD','SA','TAS','VIC','WA')
REGIONS = {
	'NSW' : ('Albury','Balranald','Canberra','CoffsHarbour','Deniliquin','Griffith','Newcastle','Tamworth','Taree','WaggaWagga','Wentworth','Wollongong'),
	'NT' : ('AliceSprings','Darwin'),
	'QLD' : ('Brisbane','Cairns','GoldCoast','Mackay','Maryborough','MtIsa','Rockhampton','Toowoomba','Townsville'),
	'SA' : ('Agelaide','CooberPedy','MountGambier','PortAugusta','PortLincoln'),
	'TAS' : ('Hobart','Lanceston'),
	'VIC' : ('Melbourne','Geelong','Ballarat','Gippsland','Midura','Shepparton','WimmeraMallee','Wodonga'),
	'WA' : ('Perth','Albany','Broome','kalgoorie','Portheadland')
	}


class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")
		self.BASE_URL = "http://www.ourguide.com.au"
		self.channelURL = self.BASE_URL + "/WebPages/%s.html"
		self.isConfigured = False

	def getName(self):
		return self.name

	def makeChannelURL(self, dated=''):
		if dated:
			return self.channelURL % (self.fullChID + "_" + dated)
		else:
			return self.channelURL % self.fullChID

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		if not self.isConfigured:
			return []
		regex = 'station_images/(.*?)\.png.*?alt="(.*?)"'
		startStr='class="sm2"'
		url = self.makeChannelURL()
		return getChannelsLIB(url, self.CHANNELS_FILENAME, regex, startStr, removeStr='Logo')

	# download channel data, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("ListingData.getChannel() dayDelta: %s chID=%s fileDate=%s" % (dayDelta,chID,fileDate))
		if not self.isConfigured or dayDelta < 0:
			return None

		progList = []
		lastStartTime = 0
		# DOWNLOAD DATA WEB PAGE
		# one html contains all channels, make filename that represents STATE + REGION + DATE
		dataFilename = os.path.join(self.cache, "%s_%s_%s.html" % (self.state, self.region, fileDate))
		debug("dataFilename=%s" % dataFilename)
		if not fileExist(dataFilename):
			if dayDelta == 0:
				url = self.makeChannelURL()
			else:
				url = self.makeChannelURL(fileDate)
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		if not doc:
			return doc

		# PARSE DATA
		startStr ='/%s.png' % chID
		matches = parseDocList(doc, "ld\('(.*?)'(.*?)</td", startStr, '</table')
		if matches:
			convert12 = True
			for match in matches:
				try:
					# extract desc if has one
					title = cleanHTML(decodestring(match[0]))
					startTime = searchRegEx(title,'(\d+:\d+)')
					# remove time from title
					title = decodeEntities(title.replace(startTime+':',''))
					desc = cleanHTML(decodeEntities(searchRegEx(match[1], "ShowHideContent\('(.*?)'")))

					# convert 12's hour to 00 if AM
					if convert12 and startTime[:2] == '12':
						startTime = '00' + startTime[-3:]
					else:
						convert12 = False

					# convert starttime to secs since epoch
					secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
					lastStartTime = secsEpoch
#					print title, startTime, desc, secsEpoch

					progList.append( {
							TVData.PROG_STARTTIME : float(secsEpoch),
							TVData.PROG_ENDTIME : 0,
							TVData.PROG_TITLE : title,
							TVData.PROG_DESC : desc
						} )
				except:
					print "invalid match", match

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("ListingData.getLink()")
		return ''


	############################################################################################################
	# load, if not exist ask, then save
	############################################################################################################
	def config(self, reset=False):
		debug("> ListingData.config() reset=%s" % reset)

		CONFIG_SECTION = 'DATASOURCE_' + self.name
		CONFIG_KEY_STATE = 'state'
		CONFIG_KEY_REGION = 'region'

		if not reset:
			self.state = mytvGlobals.config.action(CONFIG_SECTION, CONFIG_KEY_STATE)
			self.region = mytvGlobals.config.action(CONFIG_SECTION, CONFIG_KEY_REGION)
		else:
			self.state = ''
			self.region = ''

		if reset or not self.state:
			selectDialog = DialogSelect()
			selectDialog.setup("Select STATE:", width=350, rows=len(STATES), panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(STATES)
			if selectedPos >= 0:
				self.state = STATES[selectedPos]
				mytvGlobals.config.action(CONFIG_SECTION, CONFIG_KEY_STATE, self.state, mode=ConfigHelper.MODE_WRITE)

		if not self.region and self.state:
			regionList = REGIONS[self.state]
			selectDialog = DialogSelect()
			selectDialog.setup("Select REGION:", width=350, rows=len(regionList), panel=DIALOG_PANEL)
			selectedPos, action = selectDialog.ask(regionList)
			if selectedPos >= 0:
				self.region = regionList[selectedPos]
				mytvGlobals.config.action(CONFIG_SECTION, CONFIG_KEY_REGION, self.region, mode=ConfigHelper.MODE_WRITE)
				deleteFile(self.CHANNELS_FILENAME)

		if self.state and self.region:
			self.fullChID = "%s_%s" % (self.state,self.region)
			self.isConfigured = True
		else:
			self.isConfigured = False
		debug("< ListingData.config() isConfigured=%s" % self.isConfigured)
		return self.isConfigured
