"""
 Python XBMC script to playback BBC radio and podcasts (also with music plugin)

	Written By BigBellyBilly
	bigbellybilly AT gmail DOT com	- bugs, comments, ideas, help ...

 THANKS:
 To everyone who's ever helped in anyway, or if I've used code from your own scripts, MUCH APPRECIATED!

 Please don't alter or re-publish this script without authors persmission.

	CHANGELOG: see changelog.txt or view throu Settings Menu
	README: see ..\resources\language\<language>\readme.txt or view throu Settings Menu

 Additional support may be found on xboxmediacenter forum.	
"""

import xbmc, xbmcgui
import sys, os, os.path
from string import replace,split,find,capwords

# Script doc constants
__scriptname__ = "BBC PodRadio"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__svn_url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/BBC%20PodRadio"
__date__ = '16-10-2008'
__version__ = "2.2"
xbmc.output(__scriptname__ + " Version: " + __version__ + " Date: " + __date__)

# Shared resources
if os.name=='posix':    
    DIR_HOME = os.path.abspath(os.curdir).replace(';','')		# Linux case
else:
	DIR_HOME = os.getcwd().replace( ";", "" )
DIR_RESOURCES = os.path.join( DIR_HOME , "resources" )
DIR_RESOURCES_LIB = os.path.join( DIR_RESOURCES , "lib" )
DIR_USERDATA = os.path.join( "T:"+os.sep,"script_data", __scriptname__ )
sys.path.insert(0, DIR_RESOURCES_LIB)

# Load Language using xbmc builtin
try:
    # 'resources' now auto appended onto path
    __language__ = xbmc.Language( DIR_HOME ).getLocalizedString
except:
	print str( sys.exc_info()[ 1 ] )
	xbmcgui.Dialog().ok("xbmc.Language Error (Old XBMC Build)", "Script needs at least XBMC 'Atlantis' build to run.","Use script v1.7.2 instead.")

from bbbLib import *
from bbbSkinGUILib import TextBoxDialogXML
import update


#################################################################################################################
# MAIN
#################################################################################################################
class BBCPodRadio(xbmcgui.WindowXML):
	# control id's
	CLBL_DATASOURCE = 21
	CLBL_VERSION = 22
	CLBL_TITLE = 23
	CLBL_DESC = 24
	CFLBL_NOWPLAYING = 25
	CLST_SOURCE = 60
	CLST_DIR = 70
	CLST_CAT = 80
	CLST_STREAM = 90
	CGROUP_LIST_CAT = 2200
	CGROUP_LIST_STREAM = 3000

	def __init__( self, *args, **kwargs ):
		debug("> BBCPodRadio().__init__")

		self.startup = True
		self.controlID = 0

		self.IMG_PODCAST = "bpr-podcast.png"
		self.IMG_RADIO = "bpr-radio.png"

		self.URL_PAGE_LIVE = '/live.shtml'
		self.URL_PAGE_AUDIOLIST = '/audiolist.shtml'
		self.URL_PAGE_LIST = '/list.shtml'
	
		self.URL_HOME = 'http://www.bbc.co.uk/'
		self.URL_POD_HOME = self.URL_HOME + 'radio/podcasts/directory/'
		self.URL_RADIO_HOME = self.URL_HOME + 'radio/aod/index_noframes.shtml'		
		self.URL_RADIO_LIVE_HOME = self.URL_HOME + 'radio/aod/networks/$STATION/' + self.URL_PAGE_LIVE
		self.URL_PODCAST = 'http://downloads.bbc.co.uk/podcasts/$STATION/$PROG/rss.xml'
		self.URL_RADIO_AOD = "radio/aod/"
		self.URL_RADIO_STREAM = self.URL_HOME + self.URL_RADIO_AOD + "genres/classicpop/"

		self.SOURCE_POD = __language__(200)
		self.SOURCE_RADIO = __language__(201)
		self.SOURCE_RADIO_LIVE = __language__(202)
		self.source = ""

		# PODCATS DIRECTORY LIST OPTIONS
		self.POD_DIR_OPT_BROWSE_RADIO = __language__(203)
		self.POD_DIR_OPT_BROWSE_GENRE = __language__(204)
		self.POD_DIR_OPT_BROWSE_AZ = __language__(205)

		self.directoriesDict = {}
		self.directoriesDict[self.SOURCE_POD] = {self.POD_DIR_OPT_BROWSE_RADIO : self.URL_POD_HOME + 'station/',
												self.POD_DIR_OPT_BROWSE_GENRE : self.URL_POD_HOME + 'genre/',
												self.POD_DIR_OPT_BROWSE_AZ : self.URL_POD_HOME + 'title/'}

		# RADIO DIRECTORY LIST OPTIONS
		self.RADIO_DIR_OPT_BROWSE_RADIO = __language__(206)
		self.RADIO_DIR_OPT_BROWSE_MUSIC = __language__(207)
		self.RADIO_DIR_OPT_BROWSE_SPEECH = __language__(208)

		self.directoriesDict[self.SOURCE_RADIO] = {self.RADIO_DIR_OPT_BROWSE_RADIO : self.URL_RADIO_HOME,
												self.RADIO_DIR_OPT_BROWSE_MUSIC : self.URL_RADIO_HOME,
												self.RADIO_DIR_OPT_BROWSE_SPEECH : self.URL_RADIO_HOME}


		# RADIO LIVE DIRECTORY LIST OPTIONS
		self.RADIO_LIVE_DIR_OPT_BROWSE_RADIO = __language__(209)

		self.directoriesDict[self.SOURCE_RADIO_LIVE] = {self.RADIO_LIVE_DIR_OPT_BROWSE_RADIO : self.URL_RADIO_HOME}


		# dict to hold a dict for each category within a directory
		# additional categories added as each directory selected and downloaded
		# to be populated as found
		self.categoriesDict = { self.SOURCE_POD : {},
								self.SOURCE_RADIO : {},
								self.SOURCE_RADIO_LIVE: {}
							}
		
		# PODCAST REC
		self.STREAM_DETAILS_TITLE = 0
		self.STREAM_DETAILS_STREAMURL = 1
		self.STREAM_DETAILS_IMGURL = 2
		self.STREAM_DETAILS_IMG_FILENAME = 3
		self.STREAM_DETAILS_STATION = 4
		self.STREAM_DETAILS_SHORTDESC = 5
		self.STREAM_DETAILS_DUR = 6
		self.STREAM_DETAILS_DATE = 7
		self.STREAM_DETAILS_LONGDESC = 8

		self.rssparser = RSSParser2()
		self.lastSaveMediaPath = DIR_USERDATA

		debug("< __init__")


	#################################################################################################################
	def onInit( self ):
		debug("> onInit() startup=%s" % self.startup)
		if self.startup:
			xbmcgui.lock()
			self.startup = False
			self.getControl( self.CLBL_VERSION ).setLabel( "v" + __version__ )
			self.getControl( self.CLST_SOURCE ).addItem( xbmcgui.ListItem( self.SOURCE_POD, "", self.IMG_PODCAST, self.IMG_PODCAST) )
			self.getControl( self.CLST_SOURCE ).addItem( xbmcgui.ListItem( self.SOURCE_RADIO, "", self.IMG_RADIO, self.IMG_RADIO) )
			self.getControl( self.CLST_SOURCE ).addItem( xbmcgui.ListItem( self.SOURCE_RADIO_LIVE, "", self.IMG_RADIO, self.IMG_RADIO) )
			self.getControl( self.CLST_SOURCE ).setVisible( True )

			self.clearAll()
			xbmcgui.unlock()
			self.ready = True

		debug("< onInit()")


	#################################################################################################################
	def onAction(self, action):
		if not action:
			return
		buttonCode =  action.getButtonCode()
		actionID   =  action.getId()
		if not actionID:
			actionID = buttonCode

		if ( buttonCode in EXIT_SCRIPT or actionID in EXIT_SCRIPT):
			self.ready = False
			self.close()
		elif not self.ready:
			return

		self.ready = False
		if actionID in CONTEXT_MENU:
			self.mainMenu()
		elif (actionID in MOVEMENT_UP or actionID in MOVEMENT_DOWN):
			debug("MOVEMENT_UP or MOVEMENT_DOWN")
		elif (actionID in MOVEMENT_LEFT or actionID in MOVEMENT_RIGHT):
			debug("MOVEMENT_LEFT or MOVEMENT_RIGHT")
			self.isFocusNavLists = ( not self.controlID in (self.CLST_STREAM, self.CGROUP_LIST_STREAM) )
		elif actionID in CANCEL_DIALOG:			# B button
			debug("CANCEL_DIALOG")
			self.stopPlayback()
		elif actionID in (ACTION_Y, ACTION_X):
			debug("ACTION_Y or ACTION_X")
			if self.streamDetails:				# only toggle if streams available
				self.toggleNavListFocus()

		self.ready = True

	#################################################################################################################
	def onClick(self, controlID):
		if not controlID or not self.ready:
			return

		self.ready = False
		if (controlID == self.CLST_SOURCE):
			debug("CLST_SOURCE")
			self.isFocusNavLists = True
			self.source = self.getControl( self.CLST_SOURCE ).getSelectedItem().getLabel()
			self.clearAll()
			self.showDirectory()
			self.getControl( self.CLBL_TITLE ).setLabel(self.source)
			if self.source == self.SOURCE_RADIO_LIVE:
				self.onClick(self.CLST_DIR)

		elif (controlID == self.CLST_DIR):
			debug("CLST_DIR")
			self.isFocusNavLists = True
			self.clearCategory()
			directory = self.getControl( self.CLST_DIR ).getSelectedItem().getLabel()
			self.getControl( self.CLBL_TITLE ).setLabel(self.source + " > " + directory)
			if self.getCategories(directory):
				self.showCategory(directory)

		elif (controlID == self.CLST_CAT):
			debug("CLST_CAT")
			self.isFocusNavLists = True
			self.clearStream()
			directory = self.getControl( self.CLST_DIR ).getSelectedItem().getLabel()
			category = self.getControl( self.CLST_CAT ).getSelectedItem().getLabel()
			self.getControl( self.CLBL_TITLE).setLabel(self.source + " > " + directory + " > " + category)
			if self.source == self.SOURCE_POD:
				success = self.getStreamsPodcast(directory, category)
			elif self.source == self.SOURCE_RADIO:
				success = self.getStreamsRadio(directory, category)
			else:
				success = self.getStreamsRadioLive(directory, category)
			if success:
				self.showStreams()

		elif (controlID == self.CLST_STREAM):
			debug("CLST_STREAM")
			self.isFocusNavLists = False
			self.showNowPlaying(True)	# clear
			idx = self.getControl( self.CLST_STREAM ).getSelectedPosition()
			self.getControl( self.CLBL_DESC).setLabel(__language__(403))

			# "check if it always need downloading first"
			mediaURL = self.streamDetails[idx][self.STREAM_DETAILS_STREAMURL]
			if mediaURL:
				if mediaURL[-3:].lower() in ('mp3','m4a','mp4'):
					isPodcast = True
				else:
					isPodcast = False
					mediaURL = self.getMediaStreamURL(idx)

			if mediaURL:
				saveFile = False
				if (mediaURL[-2:].lower() != 'ra'):
					debug(" prompt to save or play ")
					details = self.streamDetails[idx]
					save_fn = ''
					saveFile = xbmcgui.Dialog().yesno(__language__(104), \
									details[self.STREAM_DETAILS_TITLE], details[self.STREAM_DETAILS_STATION], \
									details[self.STREAM_DETAILS_DATE], \
									__language__(409),__language__(410))

				debug("saveFile=%s isPodcast=%s" % (saveFile, isPodcast))
				if saveFile or isPodcast:
					if not saveFile and isPodcast:
						save_fn = "podcast" + mediaURL[-4:]	# add correct ext

					mediaURL = self.saveMedia(mediaURL, save_fn)		# returns full path+fn

				if not saveFile and mediaURL:
					isPlaying = playMedia(mediaURL)
				else:
					isPlaying = False

				if isPlaying:
					if self.source == self.SOURCE_RADIO:
						# redraw stream list as we've got more info
						self.getControl( self.CLST_STREAM).reset()
						self.getIcons(idx)
						self.showStreams()
						self.getControl( self.CLST_STREAM).selectItem(idx)
					title = "%s %s" % (self.streamDetails[idx][self.STREAM_DETAILS_TITLE],
									   self.streamDetails[idx][self.STREAM_DETAILS_STATION])
					self.getControl( self.CLBL_TITLE).setLabel(title)
					self.getControl( self.CLBL_DESC).setLabel(self.streamDetails[idx][self.STREAM_DETAILS_SHORTDESC])
					self.showNowPlaying()
				else:
					self.showNowPlaying(clear=True)
			else:
				self.getControl(self.CLBL_DESC).setLabel(__language__(304))

		self.ready = True


	###################################################################################################################
	def onFocus(self, controlID):
		debug("onFocus(): controlID %i" % controlID)
		self.controlID = controlID

	###################################################################################################################
	def exit(self):
		debug ("exit()")
		self.close()

	####################################################################################################################
	def clearAll(self):
		debug("clearAll()")
		xbmcgui.lock()

		self.clearDirectory()

		self.getControl( self.CLBL_DATASOURCE ).setLabel(self.source)
		if not self.source:
			self.getControl( self.CLBL_TITLE ).setLabel(__language__(100))

		self.isFocusNavLists = True
		self.streamDetails = []
		if not xbmc.Player().isPlaying():
			self.getControl(self.CFLBL_NOWPLAYING).reset()

		self.setFocus(self.getControl(self.CLST_SOURCE))
		xbmcgui.unlock()

	####################################################################################################################
	def clearDirectory(self):
		debug("clearDirectory()")
		self.clearCategory()
		try:
			self.getControl( self.CLST_DIR ).reset()
			self.getControl( self.CLST_DIR ).setVisible(False)
			self.getControl( self.CLST_DIR ).selectItem(0)
		except: pass

	####################################################################################################################
	def clearCategory(self):
		debug("clearCategory()")
		self.clearStream()
		try:
			self.getControl( self.CLST_CAT ).reset()
			self.getControl( self.CGROUP_LIST_CAT ).setVisible( False )
			self.getControl( self.CLST_CAT ).selectItem(0)
		except: pass

	####################################################################################################################
	def clearStream(self):
		debug("clearStream()")
		try:
			self.getControl( self.CLST_STREAM ).reset()
			self.getControl( self.CGROUP_LIST_STREAM ).setVisible( False )
			self.getControl( self.CLST_STREAM ).selectItem(0)
		except: pass
		self.getControl( self.CLBL_TITLE ).setLabel("")
		self.getControl( self.CLBL_DESC ).setLabel("")

	####################################################################################################################
	def showDirectory(self):
		debug("> showDirectory()")
		# add items to NAV LIST DIRECTORY
		menu = self.directoriesDict[self.source].keys()
		menu.sort()
		for opt in menu:
			self.getControl( self.CLST_DIR ).addItem(xbmcgui.ListItem(opt))

		self.getControl( self.CLST_DIR ).setVisible(True)
		self.getControl( self.CLST_DIR ).selectItem(0)
		self.getControl( self.CLBL_DESC ).setLabel("Select a Directory")
		self.isFocusNavLists = True
		self.setFocus(self.getControl( self.CLST_DIR ))
		debug("< showDirectory()")

	####################################################################################################################
	def showCategory(self, directory):
		debug("> showCategory() directory="+directory)

		menu = self.categoriesDict[self.source][directory].keys()
		menu.sort()
		for opt in menu:
			self.getControl( self.CLST_CAT ).addItem(xbmcgui.ListItem(opt))

		self.getControl( self.CGROUP_LIST_CAT ).setVisible(True)
		self.getControl( self.CLST_CAT ).selectItem(0)
		self.getControl( self.CLBL_DESC ).setLabel("Select a Category")
		self.isFocusNavLists = True
		self.setFocus(self.getControl( self.CLST_CAT ))
		debug("< showCategory()")

	############################################################################################################
	def showStreams(self):
		debug("> showStreams()")

		if self.streamDetails:
			self.streamDetails.sort()
			for pcd in self.streamDetails:
				try:
					if not pcd[self.STREAM_DETAILS_DATE] and not pcd[self.STREAM_DETAILS_DUR]:
						label1 = "%s.  %s" % (unicodeToAscii(pcd[self.STREAM_DETAILS_TITLE]),
												pcd[self.STREAM_DETAILS_STATION])
						label2 = "%s" % unicodeToAscii(pcd[self.STREAM_DETAILS_SHORTDESC])
					else:
						label1 = "%s.  %s  %s" % (unicodeToAscii(pcd[self.STREAM_DETAILS_TITLE]),
												   pcd[self.STREAM_DETAILS_STATION],
												   unicodeToAscii(pcd[self.STREAM_DETAILS_SHORTDESC]))
						label2 = "%s  %s" % (pcd[self.STREAM_DETAILS_DATE], pcd[self.STREAM_DETAILS_DUR])
					li = xbmcgui.ListItem(label1, label2, \
										pcd[self.STREAM_DETAILS_IMG_FILENAME], \
										pcd[self.STREAM_DETAILS_IMG_FILENAME])
					self.getControl( self.CLST_STREAM ).addItem(li)
				except:
					handleException()

			self.getControl( self.CGROUP_LIST_STREAM ).setVisible(True)
			self.getControl( self.CLST_STREAM ).selectItem(0)
			self.getControl( self.CLBL_DESC ).setLabel(__language__(101))	# select a stream
			self.isFocusNavLists = False
			self.setFocus(self.getControl( self.CLST_STREAM ))

		debug("< showStreams()")

	########################################################################################################################
	def getCategories(self, directory):
		debug("> getCategories() directory="+directory)

		success = False
		try:
			categoryDict = self.categoriesDict[self.source][directory]
		except:
			# category not stored, download categories for selected directory
			debug("category not yet stored")
			url = self.directoriesDict[self.source][directory]
			categoryDict = {}

			fn = os.path.join(DIR_USERDATA, "categories.html")
			if fileExist(fn):
				doc = readFile(fn)
			else:
				dialogProgress.create(__language__(403), __language__(407), directory)
				doc = fetchURL(url)

			if doc:
				debug("got doc data source=%s" % self.source)
				if self.source == self.SOURCE_POD:
					startStr = '>Browse podcasts'
					endStr = '</div'
					regex = '<a href="(.*?)">(.*?)<'
				elif self.source == self.SOURCE_RADIO:
					# all sections on one page. Just get relevant directory section
					if directory == self.RADIO_DIR_OPT_BROWSE_RADIO:
						startStr = '>CHOOSE A RADIO STATION<'
					elif directory == self.RADIO_DIR_OPT_BROWSE_MUSIC:
						startStr = '>MUSIC:<'
					elif directory == self.RADIO_DIR_OPT_BROWSE_SPEECH:
						startStr = '>SPEECH:<'
					endStr = '</ul>'
					regex = '^<li><a href="(.*?)".*?>(.*?)</a'
				elif self.source == self.SOURCE_RADIO_LIVE:
					# PICK LIVE RADIO BY STATION
					startStr = '>CHOOSE A RADIO STATION<'
					endStr = '</ul>'
					regex = '^<li><a href="(.*?)".*?>(.*?)</a'
				else:
					print "unknown source", self.source

				debug("startStr=%s endStr=%s" % (startStr, endStr))
				matches = parseDocList(doc, regex, startStr, endStr)
				if matches:
					for match in matches:
						if not match[0] or not match[1] or match[0] == '#':
							continue
						url = ''
						if self.source == self.SOURCE_RADIO_LIVE:
							# may be a link to a page of stations which needs futher selecting
							# so dont translate url, just save orig url
							# eg /radio/aod/networks/1xtra/audiolist.shtml - normal
							# eg /radio/aod/networks/localradio/list.shtml - need futher selection
							if match[0].endswith(self.URL_PAGE_AUDIOLIST):
								url = self.URL_HOME + match[0].replace(self.URL_PAGE_AUDIOLIST, self.URL_PAGE_LIVE)
#							elif match[0].endswith( match[0].endswith(self.URL_PAGE_LIST):
#								url = self.URL_HOME + match[0].replace(self.URL_PAGE_LIST, self.URL_PAGE_LIVE)

						if not url:
							url = self.URL_HOME + match[0]
						title = cleanHTML(decodeEntities(match[1]))
						categoryDict[title] = url

					debug("categoryDict=%s" % categoryDict)
					self.categoriesDict[self.source][directory] = categoryDict

			dialogProgress.close()
		# load into categories nav list
		if categoryDict:
			success = True
		else:
			messageOK(__language__(402),__language__(404))

		debug("< getCategories() success="+str(success))
		return success

	############################################################################################################
	# scrape a page of stations and convert links to LIVE links
	############################################################################################################
	def getStationsPage(self, category, url):
		debug("> getStationsPage()")
		self.streamDetails = []
		stations = {}

		dialogProgress.create(__language__(403), category)
		doc = fetchURL(url)
		if doc:
#			regex = 'href="(/radio/aod/networks/.*?)".*?>(.*?)<'
			regex = '^<li><a href="(/radio/aod/.*?)".*?>(.*?)</a' # 3/9/08 - excludes disabled streams
#			matches = parseDocList(doc, regex)
			matches = findAllRegEx(doc, regex)
			for match in matches:
				if match[0].endswith(self.URL_PAGE_AUDIOLIST):
					if self.source == self.SOURCE_RADIO_LIVE:
						# convert link to LIVE links
						link = self.URL_HOME + match[0].replace(self.URL_PAGE_AUDIOLIST, self.URL_PAGE_LIVE)
					else:
						# store as found
						link = self.URL_HOME + match[0]
					title = cleanHTML(decodeEntities(match[1]))
					stations[title] = link
		dialogProgress.close()

		# show menu of stations if reqd
		if self.source == self.SOURCE_RADIO:
			menu = stations.keys()
			menu.sort()
			selectDialog = xbmcgui.Dialog()
			selected = selectDialog.select( __language__(102), menu )
			if selected >= 0:
				station = menu[selected]
				link = stations[title]
				self.streamDetails.append([station,link,'',self.IMG_RADIO,station,'','','',''])
		else:
			# fill streamDetails with all found as these are stream links
			for title, link in stations.items():
				# title, streamurl, imgurl, img_fn, station, shortdesc, dur, date, longdesc
				self.streamDetails.append([title,link,'',self.IMG_RADIO,'','','','',''])

		debug("streamDetails=%s" % self.streamDetails)
		debug("< getStationsPage()")

	############################################################################################################
	def getStreamsPodcast(self, directory, category):
		debug("> getStreamsPodcast() directory=%s category=%s"  %(directory,category))
		self.streamDetails = []
		feedElementDict = {'description':[],'pubDate':[],'link':[],'itunes:duration':[]}

		try:
			url = self.categoriesDict[self.source][directory][category]
		except:
			messageOK(__language__(402),__language__(300),category)
		else:
			dialogProgress.create(__language__(403), __language__(407), directory, category)
			doc = fetchURL(url)
			if doc:
				try:
					# station code, url, title, img src
					regex = 'cell_(\w+).*?<h3><a href="(.*?)">(.*?)</.*?img src="(.*?)"'
					matches = parseDocList(doc, regex, 'results_cells', 'begin footer')
					for match in matches:
						station = match[0]
						link = match[1]
						if link[-1] == '/': link = link[:-1]
						prog = link.split('/')[-1]		# eg /radio/podcasts/dancehall -> dancehall
						rssLink = self.URL_PODCAST.replace('$STATION', station).replace('$PROG',prog)
						title = cleanHTML(decodeEntities(match[2]))
						imgURL = match[3]
						fn = "%s_%s%s" % (station,prog,imgURL[-4:])
						imgFilename = os.path.join(DIR_USERDATA, xbmc.makeLegalFilename(fn))

						success = self.rssparser.feed(url=rssLink)
						if success:
							rssItems = self.rssparser.parse("item", feedElementDict)
							for rssItem in rssItems:
								longDesc = rssItem.getElement('description')
								showDate = rssItem.getElement('pubDate')
								shortDate = searchRegEx(showDate, '((.*?\d\d\d\d))')		# Thu, 20 Mar 2008
								mediaURL = rssItem.getElement('link')
								duration = "%smins" % searchRegEx(rssItem.getElement('itunes:duration'), '(\d+)')
								shortDesc = longDesc[:40]

								self.streamDetails.append([title,mediaURL,imgURL,imgFilename,station,shortDesc,duration,shortDate,longDesc])
								if DEBUG:
									print self.streamDetails[-1]

					# get thumb icons
					if self.streamDetails:
						self.getIcons()
				except:
					print "bad scrape"

				dialogProgress.close()
				if not self.streamDetails:
					messageOK(__language__(301), directory, category )

		debug("streamDetails=%s" % self.streamDetails)
		success = (self.streamDetails != [])
		debug("< getStreamsPodcast() success="+str(success))
		return success


	############################################################################################################
	def getStreamsRadio(self, directory, category):
		""" Discover a list of Streams within a Category for RADIO """
		debug("> getStreamsRadio() directory=%s category=%s" % (directory,category))
		success = False
		self.streamDetails = []

		try:
			url = self.categoriesDict[self.source][directory][category]
		except:
			messageOK(__language__(402),__language__(300),category)
		else:
			if not url.endswith(self.URL_PAGE_AUDIOLIST):
				# get next web page and find stations.
				# will put a single rec into streamDetails of choosen station
				self.getStationsPage(category, url)
				try:
					category = self.streamDetails[0][self.STREAM_DETAILS_STATION]
					url = self.streamDetails[0][self.STREAM_DETAILS_STREAMURL]
				except:
					debug("no station chosen, stop")
					url = ''

			if url:
				debug("find all shows on page")
				msg = "%s > %s > %s" % (self.source,directory,category)
				self.getControl( self.CLBL_TITLE).setLabel(msg)
				dialogProgress.create(__language__(403), __language__(407), directory, category)
				doc = fetchURL(url)
				if doc:
					# Find stream block
					regexStreams = '<li>(.*?<)/li'
					regexLinks = 'href="(.*?)".*?>(.*?)</a>(.*?)<'

					streamMatches = parseDocList(doc, regexStreams, 'ALL SHOWS', '</ul>')
					for streamMatch in streamMatches:
						try:
							streamTitle = ''
							streamDesc = ''

							# get all links for stream
							linkMatches = findAllRegEx(streamMatch, regexLinks)
							MAX = len(linkMatches)
							for idx in range(MAX):
								linkMatch = linkMatches[idx]
								if find(linkMatch[0], self.URL_RADIO_AOD) == -1:
									mediaURL = self.URL_RADIO_STREAM + linkMatch[0]
								else:
									mediaURL = self.URL_HOME + linkMatch[0]
								title = cleanHTML(decodeEntities(linkMatch[1]))
								shortDesc = cleanHTML(decodeEntities(linkMatch[2]))

								# if mutliple links, get first match details to be used on other matches
								if idx == 0 and MAX > 1:
									streamTitle = title
									streamDesc = shortDesc
									continue
								elif idx == 1:		# just put desc on first occurance
									title = "%s (%s)" % (streamTitle, title)
									shortDesc = streamDesc
								elif idx > 1:
									title = "%s (%s)" % (streamTitle, title)

								self.streamDetails.append([title,mediaURL,'',self.IMG_RADIO,'',shortDesc,'','',''])
						except:
							print "getStreamsRadio() bad streamMatch", streamMatch

				dialogProgress.close()
				if not self.streamDetails:
					messageOK(__language__(301), directory, category )

		success = (self.streamDetails != [])
		debug("< getStreamsRadio() success=%s" % success)
		return success


	############################################################################################################
	def getStreamsRadioLive(self, directory, category):
		debug("> getStreamsRadioLive() directory=%s category=%s" % (directory,category))
		self.streamDetails = []

		try:
			url = self.categoriesDict[self.source][directory][category]
			if not url.endswith(self.URL_PAGE_LIVE):
				# if url not live link, get next web page and choose station
				self.getStationsPage(category, url)
			else:
				self.streamDetails.append([category,url,'',self.IMG_RADIO,'','','','',''])
		except:
			messageOK(__language__(402),__language__(300), category)

		success = (self.streamDetails != [])
		debug("< getStreamsRadioLive() success=%s" % success)
		return success


	############################################################################################################
	def toggleNavListFocus(self, focusNavLists=None):
		if focusNavLists == None:			# toggle
			self.isFocusNavLists = not self.isFocusNavLists
		else:								# force state
			self.isFocusNavLists = focusNavLists

		if self.isFocusNavLists:
			debug("set focus to NAV LISTS")
			self.setFocus(self.getControl( self.CLST_CAT ))
		else:
			debug("set focus to CONTENT")
			self.setFocus(self.getControl( self.CLST_STREAM ))

	############################################################################################################
	def saveMedia(self, url, fn=''):
		debug("> saveMedia")
		success = False

		if not fn:
			# show and get save folder
			debug("lastSaveMediaPath=" + self.lastSaveMediaPath)
			savePath = xbmcgui.Dialog().browse(3, __language__(103), "files", "", False, False, self.lastSaveMediaPath)
			fn = os.path.basename(url)
			removeFile = False
		else:
			savePath = DIR_USERDATA
			removeFile = True

		debug("fn=%s" % fn)
		debug("savePath=" + savePath)
		if savePath:
			self.lastSaveMediaPath = savePath
			fn = xbmc.makeLegalFilename(os.path.join(savePath, fn))
			if removeFile:
				deleteFile(fn)
			elif os.path.exists(fn):
				if xbmcgui.Dialog().yesno(__language__(105), fn):
					deleteFile(fn)
				else:
					fn = ''
			if fn:
				dialogProgress.create(__language__(411), url, fn )
				success = fetchURL(url, fn, isBinary=True)
				dialogProgress.close()
				if not success:
					messageOK(__language__(305), url, fn)
					fn = ''

		debug("< saveMedia fn=%s" % fn)
		return fn

	############################################################################################################
	# 1. download stream URL
	# 2. regex to find .rpm link
	# 3. download .rpm link and read rtsp URL from it
	# 4. read rtsp link and extra .ra URL (realaudio)
	# eg . rtsp://rmv8.bbc.net.uk/radio2/r2_alfie.ra?BBC-UID=b4b67453bb304bea9849307f215fd3791027bd97d0a021579a046100f3a5e9a6&SSO2-UID='
	# becomes rtsp://rmv8.bbc.net.uk/radio2/r2_alfie.ra
	# 5. play rtsp URL
	############################################################################################################
	def getMediaStreamURL(self, idx):
		debug("> getMediaStreamURL() source=" + self.source)

		title = "%s %s" % (self.streamDetails[idx][self.STREAM_DETAILS_TITLE],
						   self.streamDetails[idx][self.STREAM_DETAILS_STATION])
		mediaURL = ''
		rpmURL = ''
		url = self.streamDetails[idx][self.STREAM_DETAILS_STREAMURL]
		if url[-3:].lower() in ('mp3','m4a','mp4'):
			debug("url is a media file - download required")
			mediaURL = url
		else:
			dialogProgress.create(__language__(403), __language__(407), title)
			doc = fetchURL(url, encodeURL=False)		# prevents removal of ?
			dialogProgress.close()
			if doc:
				debug("url doc requires parsing")
				if self.source == self.SOURCE_POD:
					regex = 'class="description">(.*?)<.*?class="download".*?href="(.*?)"'
					matches = findAllRegEx(doc, regex)
					if matches:
						# update long desc with better long desc from the subscriptions page
						longDesc = cleanHTML(decodeEntities(matches[0][0]))
						self.streamDetails[idx][self.STREAM_DETAILS_LONGDESC] = longDesc
						mediaURL = matches[0][1]
				elif self.source == self.SOURCE_RADIO:
					if find(doc, 'aod/shows/images') != -1:
						regex = 'AudioStream.*?"(.*?)".*?showtitle.*?txinfo.*?>(.*?)</span.*?img src="(.*?)".*?<td.*?>(.*?)<'
					else:
						regex = 'AudioStream.*?"(.*?)"'
					matches = findAllRegEx(doc, regex)

					try:
						if not matches:
							raise
						match = matches[0]
						dur = ''
						station = ''
						txDate =  ''
						txTime = ''
						imgURL = ''
						longDesc = ''
						if isinstance(match, str):
							rpmURL = self.URL_HOME + match + '.rpm'
							station = match.split('/')[-2]
						else:
							rpmURL = self.URL_HOME + match[0] + '.rpm'
							imgURL = self.URL_HOME + match[2]
							longDesc = cleanHTML(decodeEntities(match[3]))
							station = match[0].split('/')[-2]

							# break down txinfo if possible
							txinfo = match[1].replace('\n','')
							txinfoMatches = findAllRegEx(txinfo, '(.*?)<.*?>.*?((?:Sat|Sun|Mon|Tue|Wed|Thu|Fri).*?)-(.*?)$')
							if txinfoMatches:
								debug("full txinfo")
								dur = cleanHTML(txinfoMatches[0][0])
								txDate =  cleanHTML(decodeEntities(txinfoMatches[0][1]))
								txTime = cleanHTML(decodeEntities(txinfoMatches[0][2]))
							else:
								debug("minimal txinfo")
								txinfoMatches = findAllRegEx(txinfo, '(.*?)<.*?>(.*?)$')
								dur = cleanHTML(txinfoMatches[0][0])
								txDate =  cleanHTML(decodeEntities(txinfoMatches[0][1]))

	#					print "txinfo split=", dur, station, txDate, txTime
						self.streamDetails[idx][self.STREAM_DETAILS_DUR] = dur
						self.streamDetails[idx][self.STREAM_DETAILS_STATION] = capwords(station)
						self.streamDetails[idx][self.STREAM_DETAILS_DATE] = txDate + ' ' + txTime
						self.streamDetails[idx][self.STREAM_DETAILS_IMGURL] = imgURL
						self.streamDetails[idx][self.STREAM_DETAILS_IMG_FILENAME] = os.path.join(DIR_USERDATA, os.path.basename(imgURL))
						self.streamDetails[idx][self.STREAM_DETAILS_LONGDESC] = longDesc

					except:
						print "getMediaStreamURL() bad scrape"
#						handleException()

					debug("download .rpm URL to extract rtsp URL")
					rtspDoc = fetchURL(rpmURL)
					mediaURL = searchRegEx(rtspDoc, '(rtsp://rmlive.*?)\?')
					if not mediaURL:
						mediaURL = searchRegEx(rtspDoc, '(rtsp.*?)\?')
				else:
					debug(" RADIO LIVE - just find media link")
					matches = findAllRegEx(doc, 'AudioStream.*?"(.*?)"')
					rpmURL = self.URL_HOME + matches[0] + '.rpm'

					# download .rpm URL to extract rtsp URL
					rtspDoc = fetchURL(rpmURL)
					mediaURL = searchRegEx(rtspDoc, '(rtsp://rmlive.*?)\?')
					if not mediaURL:
						mediaURL = searchRegEx(rtspDoc, '(rtsp.*?)\?')

		if not mediaURL:
			if find(doc, "no episodes") != -1:
				messageOK(__language__(302),__language__(303))
			else:
				messageOK(__language__(402),__language__(304))	# no media link found

		debug("< getMediaStreamURL() mediaURL="+mediaURL)
		return mediaURL

	############################################################################################################
	def showNowPlaying(self, clear=False, text=""):
		debug("> showNowPlaying() clear=%s" % clear)

		self.getControl( self.CFLBL_NOWPLAYING ).reset()
		if not clear:
			if not text:
				idx = self.getControl( self.CLST_STREAM ).getSelectedPosition()
				pcd =  self.streamDetails[idx]
				text = "%s.  %s.  %s.  %s.  %s." % (pcd[self.STREAM_DETAILS_TITLE],
																 pcd[self.STREAM_DETAILS_STATION],
																 pcd[self.STREAM_DETAILS_DATE],
																 pcd[self.STREAM_DETAILS_DUR],
																 pcd[self.STREAM_DETAILS_LONGDESC])
			lblText = "%s %s" % (__language__(408), text)
			self.getControl( self.CFLBL_NOWPLAYING ).addLabel(lblText)
		debug("< showNowPlaying()")

	############################################################################################################
	def getIcons(self, streamDetailsIdx=None):
		debug("> getIcons()")

		def _getIcon(url, fn):
			if not fileExist(fn):
				result = fetchURL(url, fn, isBinary=True)
			else:
				result = True
			debug("_getIcon=" + str(result))
			return result

		if streamDetailsIdx == None:
			# get all missing icons 
			for pcd in self.streamDetails:
				fn = pcd[self.STREAM_DETAILS_IMG_FILENAME]
				url = pcd[self.STREAM_DETAILS_IMGURL]
				if not _getIcon(url, fn):
					if self.source == self.SOURCE_POD:
						pcd[self.STREAM_DETAILS_IMG_FILENAME] = self.IMG_PODCAST
					else:
						pcd[self.STREAM_DETAILS_IMG_FILENAME] = self.IMG_RADIO
		else:
			pcd = self.streamDetails[streamDetailsIdx]
			fn = pcd[self.STREAM_DETAILS_IMG_FILENAME]
			url = pcd[self.STREAM_DETAILS_IMGURL]
			if not _getIcon(url, fn):
				if self.source == self.SOURCE_POD:
					self.streamDetails[streamDetailsIdx][self.STREAM_DETAILS_IMG_FILENAME] = self.IMG_PODCAST
				else:
					self.streamDetails[streamDetailsIdx][self.STREAM_DETAILS_IMG_FILENAME] = self.IMG_RADIO

		debug("< getIcons()")

	#################################################################################################################
	def stopPlayback(self):
		xbmc.Player().stop()
		self.showNowPlaying(True)			# clears

	##############################################################################################
	def mainMenu(self):
		debug("> mainMenu()")

		menuTitle = "%s - %s" % (__language__(0), __language__(500))
		while True:
			options = [ __language__(501), __language__(502), __language__(505), __language__(503)]
			if xbmc.Player().isPlaying():
				options.append(__language__(504))

			selectDialog = xbmcgui.Dialog()
			selectedPos = selectDialog.select( menuTitle, options )
			if selectedPos < 0:
				break
			
			if selectedPos == 0:
				fn = getReadmeFilename()
				tbd = TextBoxDialogXML("DialogScriptInfo.xml", DIR_HOME, "Default")
				tbd.ask(options[selectedPos], fn=fn)
				del tbd
			elif selectedPos == 1:
				fn = os.path.join( DIR_HOME, "changelog.txt" )
				tbd = TextBoxDialogXML("DialogScriptInfo.xml", DIR_HOME, "Default")
				tbd.ask(options[selectedPos], fn=fn)
				del tbd
			elif selectedPos == 2:
				if removeDir(DIR_USERDATA, __language__(505) + '?'):
					xbmc.sleep(1000)
					makeScriptDataDir()
			elif selectedPos == 3:
				fn = xbmcgui.Dialog().browse(1, __language__(503), "files", ".mp3|.mp4|.m4a", False, False, self.lastSaveMediaPath)
				if fn and playMedia(fn):
					self.showNowPlaying(False, os.path.basename(fn))
			elif selectedPos == 4:
				self.stopPlayback()

			del selectDialog


		debug ("< mainMenu()")


######################################################################################
def updateScript(silent=False):
	xbmc.output( "> updateScript() silent=%s" % silent)

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
	xbmc.output( "< updateScript() updated=%s" % updated)
	return updated

#######################################################################################################################    
# BEGIN !
#######################################################################################################################
makeScriptDataDir() 

# check for script update
if DEBUG:
    updated = False
else:
    updated = updateScript(True)
if not updated:
	try:
		# check language loaded
		xbmc.output( "__language__ = %s" % __language__ )

		if not installPlugin('music', __scriptname__, True):
			installPlugin('music', __scriptname__, False, __language__(406))

		myscript = BBCPodRadio("script-BBC_PodRadio-main.xml", DIR_HOME, "Default")
		myscript.doModal()
		del myscript
	except:
		handleException()

# clean up on exit
moduleList = ['bbbLib','bbbSkinGUILib']
if not updated:
    moduleList += ['update']
for m in moduleList:
	try:
		del sys.modules[m]
		xbmc.output(__scriptname__ + " del sys.module=%s" % m)
	except: pass

# remove other globals
try:
	del dialogProgress
except: pass

# goto xbmc home window
#try:
#	xbmc.executebuiltin('XBMC.ReplaceWindow(0)')
#except: pass
