"""
 A script to play BBC Podcast & Radio streams - PLUGIN VERSION

 Written By BigBellyBilly
 bigbellybilly AT gmail DOT com	- bugs, comments, ideas ...

 - url = sys.argv[ 0 ]
 - handle = sys.argv[ 1 ]
 - params =  sys.argv[ 2 ]

"""

__plugin__ = "BBC PodRadio"
__version__ = '1.4.1'
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '09-09-2008'

import sys, os.path
import xbmc, xbmcgui, xbmcplugin
import re, os, traceback, urllib, urllib2
from string import replace,split,find,capwords
from xml.dom.minidom import parse, parseString

if os.name=='posix':    
    DIR_HOME = os.path.abspath(os.curdir).replace(';','')		# Linux case
else:
    DIR_HOME= os.getcwd().replace(';','')
DIR_USERDATA = os.path.join( "T:"+os.sep,"script_data", __plugin__ )

dialogProgress = xbmcgui.DialogProgress()

#################################################################################################################
class BBCPodRadioPlugin:
	""" main plugin class """
	def __init__( self, *args, **kwargs ):

		debug("> BBCPodRadioPlugin.__init__()")
		
		# BASE URLS
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

		self.SOURCE_POD = 'Podcasts'
		self.SOURCE_RADIO = 'Radio'
		self.SOURCE_RADIO_LIVE = 'Radio Live'
		self.source = ''

		# define param key names
		self.PARAM_SOURCE = 'source'
		self.PARAM_DIR = 'dir'
		self.PARAM_CAT = 'cat'
		self.PARAM_STREAM = 'stream'
		self.PARAM_PLAY_URL = 'playurl'
		self.PARAM_URL = 'url'

		self.ICON_MUSIC = 'DefaultMusic.png'
		self.lastSaveMediaPath = DIR_USERDATA

		debug( "argv[ 2 ]=%s " % sys.argv[ 2 ] )

		if ( not sys.argv[ 2 ] ):
			self.getDirectories()							# make list of directories
		else:
			error = False

			# extract URL params and act accordingly
			try:
				paramDict = self._getParams()				# extract url args
				url = paramDict[self.PARAM_URL]
				self.source = paramDict[self.PARAM_SOURCE]
				debug("source=%s" % self.source)
				if paramDict.has_key(self.PARAM_DIR):		# directory, find categories
					debug("directory, find categories")
					dir = paramDict[self.PARAM_DIR]
					self.getCategories(dir, url)
				elif paramDict.has_key(self.PARAM_CAT):		# category, find streams
					debug("category, find streams")
					cat = paramDict[self.PARAM_CAT]
					if self.source == self.SOURCE_POD:
						self.getStreamsPodcast(cat, url)
					elif self.source == self.SOURCE_RADIO:
						self.getStreamsRadio(cat, url)
					else:
						self.getMediaRadioLive(cat, url)	# RADIO LIVE

				elif paramDict.has_key(self.PARAM_STREAM):	# stream, find media link
					debug("stream, find media link")
					title = paramDict[self.PARAM_STREAM]
					if self.source == self.SOURCE_POD:
						mediaURL = self.getMediaPodcast(url)
						if mediaURL:
							# play existing file rather than download
							fn = self.makeFilenameFromUrl(mediaURL)
							if not fileExist(fn):
								fn = self.saveMedia(mediaURL)		# always save anyway
							if fn:
								playMedia(fn)
					elif self.source == self.SOURCE_RADIO:
						self.getMediaRadio(title, url)

				else:
					error = True
			except:
				error = True
				print sys.exc_info()[ 1 ]

			if error:
				messageOK("Plugin Callback URL Error","Required URL params missing")

		debug("< BBCPodRadioPlugin.__init__()")

	########################################################################################################################
	def _getParams(self):
		""" extract params from argv[2] to make a dict (key=value) """
		paramDict = {}
		paramPairs=sys.argv[2][1:].split( "&" )
		for paramsPair in paramPairs:
			param = paramsPair.split('=')
			if len(param) > 1:
				paramDict[param[0]] = param[1]
		return paramDict

	########################################################################################################################
	def getDirectories(self):
		""" Return a list of Directories """
		ok = False
		try:
			debug( "getDirectories()")
			directoriesDict = {'Browse Podcasts by radio stations' : self.URL_POD_HOME + 'station/',
								'Browse Podcasts by genre' : self.URL_POD_HOME + 'genre/',
								'Browse Podcasts by A-Z' : self.URL_POD_HOME + 'title/',
								'Browse Radio by radio stations' : self.URL_RADIO_HOME,
								'Browse Radio by music genre' : self.URL_RADIO_HOME,
								'Browse Radio by speech genre' : self.URL_RADIO_HOME,
								'Browse Live Radio by radio stations' : self.URL_RADIO_HOME,
								'Browse Live Radio by music genre' : self.URL_RADIO_HOME,
								'Browse Live Radio by speech genre' : self.URL_RADIO_HOME
								}

			itemCount = len(directoriesDict)
			for title, link in directoriesDict.items():
				if find(title, 'Podcasts') != -1:
					source = self.SOURCE_POD
				elif find(title, 'Live') != -1:
					source = self.SOURCE_RADIO_LIVE
				else:
					source = self.SOURCE_RADIO
				li_url = "%s?%s=%s&%s=%s&%s=%s" % ( sys.argv[ 0 ], \
													self.PARAM_SOURCE, source, \
													self.PARAM_DIR, title, \
													self.PARAM_URL, link)

				li = xbmcgui.ListItem(title)
				li.setInfo(type="Music", infoLabels={ "Genre" : __plugin__, "Size": itemCount })

				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
								url=li_url, listitem=li, isFolder=True, totalItems=itemCount)
				if ( not ok ): raise
		except:
			print traceback.print_exc()
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )

	########################################################################################################################
	def getCategories(self, directory, url):
		""" Discover a list of Categories within a Directory """

		debug( "getCategories() %s %s %s" % (directory, url, self.source))
		ok = False
		try:
			dialogProgress.create("Downloading ...", "Categories for: ", directory)
			doc = fetchURL(url)
			dialogProgress.close()
			if not doc: raise

			if self.source == self.SOURCE_POD:
				startStr = '>Browse podcasts'
				endStr = '</div'
				regex = '<a href="(.*?)">(.*?)</'
			elif self.source == self.SOURCE_RADIO:
				# all sections on one page. Just get relevant directory section
				if find(directory, 'stations') != -1:
					startStr = '>CHOOSE A RADIO STATION<'
				elif find(directory, 'music') != -1:
					startStr = '>MUSIC:<'
				else:
					startStr = '>SPEECH:<'
				endStr = '</ul>'
				regex = '^<li><a href="(.*?)".*?>(.*?)</a'
			elif self.source == self.SOURCE_RADIO_LIVE:
				startStr = '>CHOOSE A RADIO STATION<'
				endStr = '</ul>'
				regex = '^<li><a href="(.*?)".*?>(.*?)</a'
			else:
				print "unknown source - stopping", self.source

			matches = parseDocList(doc, regex, startStr, endStr)
			if not matches:
				raise
			itemCount = len(matches)
			for match in matches:
				# ignore bad match
				if not match[0] or not match[1] or match[0] == '#':
					itemCount -= 1
					continue
				link = ''
				if self.source == self.SOURCE_RADIO_LIVE:
					# may be a link to a page of stations which needs futher selecting
					# so dont translate url, just save orig url
					# eg /radio/aod/networks/1xtra/audiolist.shtml - normal
					# eg /radio/aod/networks/localradio/list.shtml - need futher selection
					if match[0].endswith(self.URL_PAGE_AUDIOLIST):
						link = self.URL_HOME + match[0].replace(self.URL_PAGE_AUDIOLIST, self.URL_PAGE_LIVE)

				if not link:
					link = self.URL_HOME + match[0]
				title = cleanHTML(decodeEntities(match[1])).replace('&','and')
				li_url = "%s?%s=%s&%s=%s&%s=%s" % ( sys.argv[ 0 ], \
													self.PARAM_SOURCE, self.source, \
													self.PARAM_CAT, title, \
													self.PARAM_URL, link)

				li = xbmcgui.ListItem(title)
				li.setInfo(type="Music", infoLabels={ "Size": itemCount, "Genre": directory })
				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
								url=li_url, listitem=li, isFolder=True, totalItems=itemCount )

				if ( not ok ): raise
		except:
#			print traceback.print_exc()
			messageOK("No Categories Found", "Site may have changed ?", url)
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )

########################################################################################################################
	def getStreamsPodcast(self, category, url):
		""" Discover a list of Streams within a Category for PODCASTS """

		debug( "getStreamsPodcast() %s %s" % (category, url) )
		try:
			dialogProgress.create("Downloading ...", "Podcasts for: ", category)
			doc = fetchURL(url)
			dialogProgress.close()
			if not doc: raise
			
			# station code, url, title, img src
			regex = 'cell_(\w+).*?<h3><a href="(.*?)">(.*?)</.*?img src="(.*?)".*?<li>(.*?)</li>.*?<li>(.*?)</li>.*?Duration: (\d+).*?Episode: (.*?)</li>.*?<p>(.*?)</p>'
			matches = parseDocList(doc, regex, 'results_cells', 'begin footer')
			if not matches:
				raise

			MAX_MATCHES = len(matches)
			for match in matches:
				station = match[0]
				link = match[1]
				if link[-1] == '/': link = link[:-1]
				prog = link.split('/')[-1]		# eg /radio/podcasts/dancehall -> dancehall
				streamLink = self.URL_PODCAST.replace('$STATION', station).replace('$PROG',prog)
				title = cleanHTML(decodeEntities(match[2])).replace('&','and')
				imgURL = match[3]
				fn = "%s_%s%s" % (station,prog,imgURL[-4:])
				imgFilename = os.path.join(DIR_USERDATA, xbmc.makeLegalFilename(fn))

				# additional podcast details
				stationName = cleanHTML(decodeEntities(match[4]))
				shortDesc = cleanHTML(decodeEntities(match[5]))
				duration = cleanHTML(decodeEntities(match[6]))
				showDate = cleanHTML(decodeEntities(match[7]))
				longDesc = cleanHTML(decodeEntities(match[8]))
				year = showDate[-4:]

				# download icon if not exist
				if not fileExist(imgFilename) and not fetchURL(imgURL, imgFilename, isBinary=True):
					imgFilename = self.ICON_MUSIC

				label1 = "%s. %s" % (unicodeToAscii(title), shortDesc)
				li_url = "%s?%s=%s&%s=%s&%s=%s" % ( sys.argv[ 0 ],
													self.PARAM_SOURCE, self.source, \
													self.PARAM_STREAM, title, \
													self.PARAM_URL, streamLink)
				li = xbmcgui.ListItem(label1, '', imgFilename, imgFilename)
				li.setInfo(type="Music", infoLabels={ "Duration": int(duration), \
											"Size": MAX_MATCHES, \
											"Genre": category, \
											"Title" : title, \
											"Date" : showDate, \
											"Tagline" : shortDesc, \
											"PlotOutline" : longDesc, \
											"Artist" : stationName, \
											"Album" : shortDesc, \
											"Year" : year })

				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
							url=li_url, listitem=li, isFolder=False, totalItems=MAX_MATCHES )

				if ( not ok ): raise
		except:
			print traceback.print_exc()
			messageOK("No Streams Found","No episodes available or","Site may have changed ?")
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )



########################################################################################################################
	def getStreamsRadio(self, category, url):
		""" Discover a list of Streams within a Category for RADIO """
		debug( "getStreamsRadio() %s" % category)

		ok = False
		if not url.endswith(self.URL_PAGE_AUDIOLIST):
			# need to pick a station name
			try:
				category, url = self.getStationsPage(category, url)
			except:
				print "no station selected - stop"
				return

		try:
			dialogProgress.create("Downloading ...", "Radio Streams for: ", category)
			doc = fetchURL(url)
			dialogProgress.close()
			if not doc: raise

			# Find stream block
			regexStreams = '<li>(.*?<)/li'
			regexLinks = 'href="(.*?)".*?>(.*?)</a>(.*?)<'
			streamMatches = parseDocList(doc, regexStreams, 'ALL SHOWS', '</ul>')
			if not streamMatches:
				raise

			STREAMS_TOTAL = len(streamMatches)
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
						title = cleanHTML(decodeEntities(linkMatch[1])).replace('&','and')
						shortDesc = cleanHTML(decodeEntities(linkMatch[2]))

						# if mutliple links, get first match details to be used on other matches
						if idx == 0 and MAX > 1:
							streamTitle = unicodeToAscii(title)
							streamDesc = shortDesc
							continue
						elif idx == 1:		# just put desc on first occurance
							title = "%s (%s)" % (streamTitle, unicodeToAscii(title))
							shortDesc = streamDesc
						elif idx > 1:
							title = "%s (%s)" % (streamTitle, unicodeToAscii(title))

						label1 = "%s.  %s" % (title, unicodeToAscii(shortDesc))
						li_url = "%s?%s=%s&%s=%s&%s=%s" % ( sys.argv[ 0 ],
															self.PARAM_SOURCE, self.source, \
															self.PARAM_STREAM, title, \
															self.PARAM_URL, streamURL)

						li = xbmcgui.ListItem(label1)
						li.setInfo(type="Music", infoLabels={"Genre": category, \
													  "Title" : title, \
													  "Tagline" : shortDesc, \
													  "Album" : shortDesc })

						ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
									url=li_url, listitem=li, isFolder=True, totalItems=STREAMS_TOTAL )

				except:
					print "bad streamMatch", streamMatch
					print traceback.print_exc()
			if ( not ok ): raise
		except:
			print traceback.print_exc()
			messageOK("No Streams Found","No episodes available or","Site may have changed ?")
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )

	############################################################################################################
	# 1. download stream URL
	# 2. regex to find .rpm link
	# 3. download .rpm link and read rtsp URL from it
	# 4. read rtsp link and extract .ra URL upto ? (realaudio)
	# eg . rtsp://rmv8.bbc.net.uk/radio2/r2_alfie.ra?BBC-UID=b4b67453bb304bea9849307f215fd3791027bd97d0a021579a046100f3a5e9a6&SSO2-UID='
	# becomes rtsp://rmv8.bbc.net.uk/radio2/r2_alfie.ra
	# 5. play rtsp URL
	############################################################################################################
	def getMediaRadio(self, title, url):
		""" Discover media link from stream for RADIO """

		debug( "getMediaRadio()" )
		ok = False
		mediaURL = ''
		rpmURL = ''
		try:
			dialogProgress.create("Downloading ...", "Radio Stream: ", title)
			doc = fetchURL(url, encodeURL=False)
			dialogProgress.close()
			if not doc: raise

			if find(doc, 'aod/shows/images') != -1:
				regex = 'AudioStream.*?"(.*?)".*?showtitle.*?txinfo.*?>(.*?)</span.*?img src="(.*?)".*?<td.*?>(.*?)<'
			else:
				regex = 'AudioStream.*?"(.*?)"'
			matches = findAllRegEx(doc, regex)
			if not matches: raise

			match = matches[0]
			dur = ''
			durMins = 0
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
				imgPath = os.path.join(DIR_USERDATA,os.path.basename(imgURL))
				longDesc = cleanHTML(decodeEntities(match[3]))
				station = match[0].split('/')[-2]

				# break down txinfo if possible
				txinfo = match[1].replace('\n','')
#				txinfoMatches = searchRegEx(txinfo, '\((.*?)\)<.*?>(.*?)-(.*?)-(.*?)$')
				txinfoMatches = findAllRegEx(txinfo, '(.*?)<.*?>.*?((?:Sat|Sun|Mon|Tue|Wed|Thu|Fri).*?)-(.*?)$')
				if txinfoMatches:
					debug("full txinfo")
					dur = cleanHTML(txinfoMatches[0][0])
					txDate =  cleanHTML(decodeEntities(txinfoMatches[0][1]))
					txTime = cleanHTML(decodeEntities(txinfoMatches[0][2]))
				else:
					debug("minimal txinfo")
#					txinfoMatches = findAllRegEx(txinfo, '\((.*?)\)<.*?>(.*?)$')
					txinfoMatches = findAllRegEx(txinfo, '(.*?)<.*?>(.*?)$')
					dur = cleanHTML(txinfoMatches[0][0])
					txDate =  cleanHTML(decodeEntities(txinfoMatches[0][1]))

			# convert dur into mins
#			print "txinfo split=", dur, station, txDate, txTime
			durMins = self._convertDurToMins(dur)

			debug("download .rpm URL to extract rtsp URL")
			if rpmURL:
				rtspDoc = fetchURL(rpmURL)
				mediaURL = searchRegEx(rtspDoc, '(rtsp.*?)\?')

			if not mediaURL: raise

			# download icon
			if not fileExist(imgPath) and not fetchURL(imgURL, imgPath, isBinary=True):
				imgPath = self.ICON_MUSIC

			li = xbmcgui.ListItem(title,'',imgPath,imgPath)
			li.setInfo(type="Music", infoLabels={ "Size": 1, "Duration": int(durMins), \
										  "Genre": self.source, \
										  "Title" : title, \
										  "Date" : txDate, \
										  "PlotOutline" : longDesc, \
										  "Artist" : capwords(station) })

			ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
								  url=mediaURL, listitem=li, isFolder=False )

			if ( not ok ): raise
		except:
			print traceback.print_exc()
			messageOK("Radio Stream Failed","Media link not found.")
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )


	############################################################################################################
	def getMediaRadioLive(self, title, url):
		""" Discover media links from stream for RADIO LIVE """

		debug( "getMediaRadioLive() %s %s" % (title,url))
		ok = False
		mediaURL = ''
		if not url.endswith(self.URL_PAGE_LIVE):
			# if url not live link, get next web page and choose station
			try:
				title, url = self.getStationsPage(title, url)
			except:
				print "no station selected - stop"
				return None

		try:
			dialogProgress.create("Downloading ...", "Live Radio stream: ", title)
			doc = fetchURL(url, encodeURL=False)
			if not doc: raise

			matches = findAllRegEx(doc, 'AudioStream.*?"(.*?)"')
			rpmURL = self.URL_HOME + matches[0] + '.rpm'

			debug("download .rpm URL to extract rtsp URL")
			rtspDoc = fetchURL(rpmURL)
			mediaURL = searchRegEx(rtspDoc, '(rtsp://rmlive.*?)\?')
			if not mediaURL:
				mediaURL = searchRegEx(rtspDoc, '(rtsp.*?)\?')
			if not mediaURL:
				raise

			debug("found mediaURL=%s" % mediaURL)
			li = xbmcgui.ListItem(title)
			li.setInfo(type="Music", infoLabels={ "Size": 1 })
			ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), \
								  url=mediaURL, listitem=li, isFolder=False )
			if ( not ok ): raise
		except:
			messageOK("Live Radio","No Media links found!")
		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok )

	############################################################################################################
	def getMediaPodcast(self, url):
		""" Discover media link from RSS for PODCAST """

		mediaURL = ''
		try:
			self.rssparser = RSSParser2()
			success = self.rssparser.feed(url=url)
			if not success: raise

			feedElementDict = {'link':[]}
			rssItems = self.rssparser.parse("item", feedElementDict)
			if not rssItems: raise

			mediaURL = rssItems[0].getElement('link')	# mp3 link
		except:
			print traceback.print_exc()
			messageOK("Podcast Unavailable","Podcast file not found!")

		debug( "getMediaPodcast() %s" % mediaURL)
		return mediaURL

	############################################################################################################
	# scrape a page of stations and convert links to LIVE links
	############################################################################################################
	def getStationsPage(self, category, url):
		debug("> getStationsPage() %s %s " % (category, url))
		stations = []
		info = ()

		dialogProgress.create("Finding Stations ...", category)
		doc = fetchURL(url)
		if doc:
			regex = 'href="(/radio/aod/networks/.*?)".*?>(.*?)<'
			matches = parseDocList(doc, regex)
			for match in matches:
				if match[0].endswith(self.URL_PAGE_AUDIOLIST):
					if self.source == self.SOURCE_RADIO_LIVE:
						# convert link to LIVE links
						link = self.URL_HOME + match[0].replace(self.URL_PAGE_AUDIOLIST, self.URL_PAGE_LIVE)
					else:
						# store as found
						link = self.URL_HOME + match[0]
					title = cleanHTML(decodeEntities(match[1]))
					stations.append((title, link))
		dialogProgress.close()

		print "stations=", stations

		# show menu of stations if reqd
		if len(stations) > 1:
			stations.sort()
			menu = []
			for name, link in stations:
				menu.append(name)
			selectDialog = xbmcgui.Dialog()
			selectedPos = selectDialog.select("Choose Station:", menu )
			if selectedPos >= 0:
				info = stations[selectedPos]
		elif len(stations) == 1:
			# return all radio live links found
			info = stations[0]

		debug("< getStationsPage()")
		return info

	############################################################################################################
	def _convertDurToMins(self, durStr):
		hr = 0
		min = 0
		matches = searchRegEx(durStr, '(\d+) h')
		if matches:
			hr = int(matches[0][0])

		matches = searchRegEx(durStr, '(\d+) m')
		if matches:
			min = int(matches[0][0])
		
		mins = (hr * 60) + min
		print "_convertDurToMins() = ", durStr, mins
		return mins


	############################################################################################################
	def makeFilenameFromUrl(self, url):
		basename = os.path.basename(url)
		return xbmc.makeLegalFilename(os.path.join(self.lastSaveMediaPath, basename))

	############################################################################################################
	def saveMedia(self, url):
		debug("> saveMedia %s" % url)
		success = False

		fn = ''
		# show and get save folder
		savePath = xbmcgui.Dialog().browse(3, "Save To:", "files", "", False, False, self.lastSaveMediaPath)
		debug("savePath=" + savePath)
		if savePath:
			self.lastSaveMediaPath = savePath
			basename = os.path.basename(url)
			fn = xbmc.makeLegalFilename(os.path.join(savePath, basename))
			save = True
			if fileExist(fn):
				if xbmcgui.Dialog().yesno("Overwrite Existing File?", os.path.basename(fn)):
					deleteFile(fn)
				else:
					fn= ''
			if fn:
				dialogProgress.create("Downloading ...", savePath, basename )
				success = fetchURL(url, fn, isBinary=True)
				dialogProgress.close()
				if not success:
					fn = ''

		debug("< saveMedia fn=%s" % fn)
		return fn

#################################################################################################################
def debug(msg):
	xbmc.output(str(msg))

#################################################################################################################
# if success: returns the html page given in url as a string
# else: return -1 for Exception None for HTTP timeout, '' for empty page otherwise page data
#################################################################################################################
def fetchURL(url, file='', isBinary=False, encodeURL=True):
	if encodeURL:
		safe_url = urllib.quote_plus(url,'/:&?=+#@')
	else:
		safe_url = url
	debug("> fetchURL() %s" % safe_url)

	def _report_hook( count, blocksize, totalsize ):
		# just update every x%
		if count and totalsize:
			percent = int( float( count * blocksize * 100) / totalsize )
			if (percent % 5) == 0:
				dialogProgress.update( percent )
		if ( dialogProgress.iscanceled() ):
			debug("fetchURL() iscanceled()")
			raise "Cancel"

	success = False
	data = None
	if not file:
		# create temp file if needed
		file = os.path.join(DIR_USERDATA, "temp.html")

	# remove destination file if exists already
	deleteFile(file)

	try:
		opener = urllib.FancyURLopener()
		fn, resp = opener.retrieve(safe_url, file, _report_hook)
		opener.close()
#		print resp

		# check correct content type		
		content_type = resp["Content-Type"].lower()
		# fail if expecting an image but not corrent type returned
		if isBinary and (find(content_type,"text") != -1):
			raise "Not Binary"

	except IOError, errobj:
		ErrorCode(errobj)
	except "Not Binary":
		print("Returned Non Binary content")
		data = False
	except:
		print traceback.print_exc()
		messageOK("fetchURL() Exception", sys.exc_info()[ 1 ] )
	else:
		if not isBinary:
			data = readFile(file)		# read retrieved file
		else:
			data = fileExist(file)		# check image file exists

		if data:
			success = True

	debug( "< fetchURL success=%s" % success)
	return data

#################################################################################################################
def ErrorCode(e):
	print "except=%s" % e
	if hasattr(e, 'code'):
		code = e.code
	else:
		try:
			code = e[0]
		except:
			code = 'Unknown'
	title = 'Error, Code: %s' % code

	if hasattr(e, 'reason'):
		txt = e.reason
	else:
		try:
			txt = e[1]
		except:
			txt = 'Unknown reason'
	print "%s = %s" % (title, txt)
	messageOK(title, str(txt))

#################################################################################################################
def messageOK(title='', line1='', line2='',line3=''):
	xbmcgui.Dialog().ok(title ,line1,line2,line3)

#################################################################################################################
def deleteFile(filename):
	try:
		os.remove(filename)
	except: pass

#################################################################################################################
def readFile(filename):
	try:
		doc = file(filename).read()
	except:
		doc = ""
	return doc

#################################################################################################################
def fileExist(filename):
	exist = False
	try:
		if os.path.isfile(filename) and os.path.getsize(filename) > 0:
			exist = True
	except:
		pass
	return exist

#################################################################################################################
# look for html between < and > chars and remove it
def cleanHTML(data, breaksToNewline=False):
	if not data: return ""
	try:
		if breaksToNewline:
			data = data.replace('<br>','\n').replace('<p>','\n')
		reobj = re.compile('<.+?>', re.IGNORECASE+re.DOTALL+re.MULTILINE)
		return (re.sub(reobj, '', data)).strip()
	except:
		return data

#################################################################################################################
# Thanks to Arboc for contributing most of the translation in this function. 
#################################################################################################################
def decodeEntities(txt, removeNewLines=True):
	if not txt: return ""
	txt = txt.replace('\t','')

# % values
	if find(txt,'%') >= 0:
		txt = txt.replace('%21', "!")
		txt = txt.replace('%22', '"')
		txt = txt.replace('%25', "%")
		txt = txt.replace('%26', "&")
		txt = txt.replace('%27', "'")
		txt = txt.replace('%28', "(")
		txt = txt.replace('%29', ")")
		txt = txt.replace('%2a', "*")
		txt = txt.replace('%2b', "+")
		txt = txt.replace('%2c', ",")
		txt = txt.replace('%2d', "-")
		txt = txt.replace('%2e', ".")
		txt = txt.replace('%3a', ":")
		txt = txt.replace('%3b', ";")
		txt = txt.replace('%3f', "?")
		txt = txt.replace('%40', "@")

# 
	if find(txt,"&#") >= 0:
		txt = txt.replace('&#034;','"')
		txt = txt.replace('&#039;','\'')
		txt = txt.replace('&#13;&#10;','\n')
		txt = txt.replace('&#10;','\n')
		txt = txt.replace('&#13;','\n')
		txt = txt.replace('&#146;', "'")
		txt = txt.replace('&#156;', "oe")
		txt = txt.replace('&#160;', " ") # no-break space = non-breaking space U+00A0 ISOnum
		txt = txt.replace('&#161;', "!") # inverted exclamation mark U+00A1 ISOnum
		txt = txt.replace('&#162;', "c") # cent sign U+00A2 ISOnum
		txt = txt.replace('&#163;', "p") # pound sign U+00A3 ISOnum
		txt = txt.replace('&#164;', "$") # currency sign U+00A4 ISOnum
		txt = txt.replace('&#165;', "y") # yen sign = yuan sign U+00A5 ISOnum
		txt = txt.replace('&#166;', "|") # broken bar = broken vertical bar U+00A6 ISOnum
		txt = txt.replace('&#167;', "S") # section sign U+00A7 ISOnum
		txt = txt.replace('&#168;', "''") # diaeresis = spacing diaeresis U+00A8 ISOdia
		txt = txt.replace('&#169;', "(c)") # copyright sign U+00A9 ISOnum
		txt = txt.replace('&#170;', "e") # feminine ordinal indicator U+00AA ISOnum
		txt = txt.replace('&#171;', '"') # left-pointing double angle quotation mark = left pointing guillemet U+00AB ISOnum
		txt = txt.replace('&#172;', "-.") # not sign U+00AC ISOnum
		txt = txt.replace('&#173;', "-") # soft hyphen = discretionary hyphen U+00AD ISOnum
		txt = txt.replace('&#174;', "(R)") # registered sign = registered trade mark sign U+00AE ISOnum
		txt = txt.replace('&#175;', "-") # macron = spacing macron = overline = APL overbar U+00AF ISOdia
		txt = txt.replace('&#176;', "o") # degree sign U+00B0 ISOnum
		txt = txt.replace('&#177;', "+-") # plus-minus sign = plus-or-minus sign U+00B1 ISOnum
		txt = txt.replace('&#178;', "2") # superscript two = superscript digit two = squared U+00B2 ISOnum
		txt = txt.replace('&#179;', "3") # superscript three = superscript digit three = cubed U+00B3 ISOnum
		txt = txt.replace('&#180;', " ") # acute accent = spacing acute U+00B4 ISOdia
		txt = txt.replace('&#181;', "u") # micro sign U+00B5 ISOnum
		txt = txt.replace('&#182;', "|p") # pilcrow sign = paragraph sign U+00B6 ISOnum
		txt = txt.replace('&#183;', ".") # middle dot = Georgian comma = Greek middle dot U+00B7 ISOnum
		txt = txt.replace('&#184;', " ") # cedilla = spacing cedilla U+00B8 ISOdia
		txt = txt.replace('&#185;', "1") # superscript one = superscript digit one U+00B9 ISOnum
		txt = txt.replace('&#186;', "o") # masculine ordinal indicator U+00BA ISOnum
		txt = txt.replace('&#187;', '"') # right-pointing double angle quotation mark = right pointing guillemet U+00BB ISOnum
		txt = txt.replace('&#188;', "1/4") # vulgar fraction one quarter = fraction one quarter U+00BC ISOnum
		txt = txt.replace('&#189;', "1/2") # vulgar fraction one half = fraction one half U+00BD ISOnum
		txt = txt.replace('&#190;', "3/4") # vulgar fraction three quarters = fraction three quarters U+00BE ISOnum
		txt = txt.replace('&#191;', "?") # inverted question mark = turned question mark U+00BF ISOnum
		txt = txt.replace('&#192;', "A") # latin capital letter A with grave = latin capital letter A grave U+00C0 ISOlat1
		txt = txt.replace('&#193;', "A") # latin capital letter A with acute U+00C1 ISOlat1
		txt = txt.replace('&#194;', "A") # latin capital letter A with circumflex U+00C2 ISOlat1
		txt = txt.replace('&#195;', "A") # latin capital letter A with tilde U+00C3 ISOlat1
		txt = txt.replace('&#196;', "A") # latin capital letter A with diaeresis U+00C4 ISOlat1
		txt = txt.replace('&#197;', "A") # latin capital letter A with ring above = latin capital letter A ring U+00C5 ISOlat1
		txt = txt.replace('&#198;', "AE") # latin capital letter AE = latin capital ligature AE U+00C6 ISOlat1
		txt = txt.replace('&#199;', "C") # latin capital letter C with cedilla U+00C7 ISOlat1
		txt = txt.replace('&#200;', "E") # latin capital letter E with grave U+00C8 ISOlat1
		txt = txt.replace('&#201;', "E") # latin capital letter E with acute U+00C9 ISOlat1
		txt = txt.replace('&#202;', "E") # latin capital letter E with circumflex U+00CA ISOlat1
		txt = txt.replace('&#203;', "E") # latin capital letter E with diaeresis U+00CB ISOlat1
		txt = txt.replace('&#204;', "I") # latin capital letter I with grave U+00CC ISOlat1
		txt = txt.replace('&#205;', "I") # latin capital letter I with acute U+00CD ISOlat1
		txt = txt.replace('&#206;', "I") # latin capital letter I with circumflex U+00CE ISOlat1
		txt = txt.replace('&#207;', "I") # latin capital letter I with diaeresis U+00CF ISOlat1
		txt = txt.replace('&#208;', "D") # latin capital letter ETH U+00D0 ISOlat1
		txt = txt.replace('&#209;', "N") # latin capital letter N with tilde U+00D1 ISOlat1
		txt = txt.replace('&#210;', "O") # latin capital letter O with grave U+00D2 ISOlat1
		txt = txt.replace('&#211;', "O") # latin capital letter O with acute U+00D3 ISOlat1
		txt = txt.replace('&#212;', "O") # latin capital letter O with circumflex U+00D4 ISOlat1
		txt = txt.replace('&#213;', "O") # latin capital letter O with tilde U+00D5 ISOlat1
		txt = txt.replace('&#214;', "O") # latin capital letter O with diaeresis U+00D6 ISOlat1
		txt = txt.replace('&#215;', "x") # multiplication sign U+00D7 ISOnum
		txt = txt.replace('&#216;', "O") # latin capital letter O with stroke = latin capital letter O slash U+00D8 ISOlat1
		txt = txt.replace('&#217;', "U") # latin capital letter U with grave U+00D9 ISOlat1
		txt = txt.replace('&#218;', "U") # latin capital letter U with acute U+00DA ISOlat1
		txt = txt.replace('&#219;', "U") # latin capital letter U with circumflex U+00DB ISOlat1
		txt = txt.replace('&#220;', "U") # latin capital letter U with diaeresis U+00DC ISOlat1
		txt = txt.replace('&#221;', "Y") # latin capital letter Y with acute U+00DD ISOlat1
		txt = txt.replace('&#222;', "D") # latin capital letter THORN U+00DE ISOlat1
		txt = txt.replace('&#223;', "SS") # latin small letter sharp s = ess-zed U+00DF ISOlat1
		txt = txt.replace('&#224;', "a") # latin small letter a with grave = latin small letter a grave U+00E0 ISOlat1
		txt = txt.replace('&#225;', "a") # latin small letter a with acute U+00E1 ISOlat1
		txt = txt.replace('&#226;', "a") # latin small letter a with circumflex U+00E2 ISOlat1
		txt = txt.replace('&#227;', "a") # latin small letter a with tilde U+00E3 ISOlat1
		txt = txt.replace('&#228;', "a") # latin small letter a with diaeresis U+00E4 ISOlat1
		txt = txt.replace('&#229;', "a") # latin small letter a with ring above = latin small letter a ring U+00E5 ISOlat1
		txt = txt.replace('&#230;', "ae") # latin small letter ae = latin small ligature ae U+00E6 ISOlat1
		txt = txt.replace('&#231;', "c") # latin small letter c with cedilla U+00E7 ISOlat1
		txt = txt.replace('&#232;', "e") # latin small letter e with grave U+00E8 ISOlat1
		txt = txt.replace('&#233;', "e") # latin small letter e with acute U+00E9 ISOlat1
		txt = txt.replace('&#234;', "e") # latin small letter e with circumflex U+00EA ISOlat1
		txt = txt.replace('&#235;', "e") # latin small letter e with diaeresis U+00EB ISOlat1
		txt = txt.replace('&#236;', "i") # latin small letter i with grave U+00EC ISOlat1
		txt = txt.replace('&#237;', "i") # latin small letter i with acute U+00ED ISOlat1
		txt = txt.replace('&#238;', "i") # latin small letter i with circumflex U+00EE ISOlat1
		txt = txt.replace('&#239;', "i") # latin small letter i with diaeresis U+00EF ISOlat1
		txt = txt.replace('&#240;', "d") # latin small letter eth U+00F0 ISOlat1
		txt = txt.replace('&#241;', "n") # latin small letter n with tilde U+00F1 ISOlat1
		txt = txt.replace('&#242;', "o") # latin small letter o with grave U+00F2 ISOlat1
		txt = txt.replace('&#243;', "o") # latin small letter o with acute U+00F3 ISOlat1
		txt = txt.replace('&#244;', "o") # latin small letter o with circumflex U+00F4 ISOlat1
		txt = txt.replace('&#245;', "o") # latin small letter o with tilde U+00F5 ISOlat1
		txt = txt.replace('&#246;', "o") # latin small letter o with diaeresis U+00F6 ISOlat1
		txt = txt.replace('&#247;', "/") # division sign U+00F7 ISOnum
		txt = txt.replace('&#248;', "o") # latin small letter o with stroke = latin small letter o slash U+00F8 ISOlat1
		txt = txt.replace('&#249;', "u") # latin small letter u with grave U+00F9 ISOlat1
		txt = txt.replace('&#250;', "u") # latin small letter u with acute U+00FA ISOlat1
		txt = txt.replace('&#251;', "u") # latin small letter u with circumflex U+00FB ISOlat1
		txt = txt.replace('&#252;', "u") # latin small letter u with diaeresis U+00FC ISOlat1
		txt = txt.replace('&#253;', "y") # latin small letter y with acute U+00FD ISOlat1
		txt = txt.replace('&#254;', "d") # latin small letter thorn U+00FE ISOlat1
		txt = txt.replace('&#255;', "y") # latin small letter y with diaeresis U+00FF ISOlat1
		txt = txt.replace('&#338;', "OE") # latin capital ligature OE U+0152 ISOlat2
		txt = txt.replace('&#339;', "oe") # latin small ligature oe U+0153 ISOlat2
		txt = txt.replace('&#34;', '"') # quotation mark = APL quote U+0022 ISOnum
		txt = txt.replace('&#352;', "S") # latin capital letter S with caron U+0160 ISOlat2
		txt = txt.replace('&#353;', "s") # latin small letter s with caron U+0161 ISOlat2
		txt = txt.replace('&#376;', "Y") # latin capital letter Y with diaeresis U+0178 ISOlat2
		txt = txt.replace('&#38;', "&") # ampersand U+0026 ISOnum
		txt = txt.replace('&#39;','\'')
		txt = txt.replace('&#402;', "f") # latin small f with hook = function = florin U+0192 ISOtech
		txt = txt.replace('&#60;', "<") # less-than sign U+003C ISOnum
		txt = txt.replace('&#62;', ">") # greater-than sign U+003E ISOnum
		txt = txt.replace('&#710;', "") # modifier letter circumflex accent U+02C6 ISOpub
		txt = txt.replace('&#732;', "~") # small tilde U+02DC ISOdia
		txt = txt.replace('&#8194;', "") # en space U+2002 ISOpub
		txt = txt.replace('&#8195;', " ") # em space U+2003 ISOpub
		txt = txt.replace('&#8201;', " ") # thin space U+2009 ISOpub
		txt = txt.replace('&#8204;', "|") # zero width non-joiner U+200C NEW RFC 2070
		txt = txt.replace('&#8205;', "|") # zero width joiner U+200D NEW RFC 2070
		txt = txt.replace('&#8206;', "") # left-to-right mark U+200E NEW RFC 2070
		txt = txt.replace('&#8207;', "") # right-to-left mark U+200F NEW RFC 2070
		txt = txt.replace('&#8211;', "--") # en dash U+2013 ISOpub
		txt = txt.replace('&#8212;', "---") # em dash U+2014 ISOpub
		txt = txt.replace('&#8216;', '"') # left single quotation mark U+2018 ISOnum
		txt = txt.replace('&#8217;', '"') # right single quotation mark U+2019 ISOnum
		txt = txt.replace('&#8218;', '"') # single low-9 quotation mark U+201A NEW
		txt = txt.replace('&#8220;', '"') # left double quotation mark U+201C ISOnum
		txt = txt.replace('&#8221;', '"') # right double quotation mark U+201D ISOnum
		txt = txt.replace('&#8222;', '"') # double low-9 quotation mark U+201E NEW
		txt = txt.replace('&#8224;', "|") # dagger U+2020 ISOpub
		txt = txt.replace('&#8225;', "||") # double dagger U+2021 ISOpub
		txt = txt.replace('&#8226;', "o") # bullet = black small circle U+2022 ISOpub
		txt = txt.replace('&#8230;', "...") # horizontal ellipsis = three dot leader U+2026 ISOpub
		txt = txt.replace('&#8240;', "%0") # per mille sign U+2030 ISOtech
		txt = txt.replace('&#8242;', "'") # prime = minutes = feet U+2032 ISOtech
		txt = txt.replace('&#8243;', "''") # double prime = seconds = inches U+2033 ISOtech
		txt = txt.replace('&#8249;', '"') # single left-pointing angle quotation mark U+2039 ISO proposed
		txt = txt.replace('&#8250;', '"') # single right-pointing angle quotation mark U+203A ISO proposed
		txt = txt.replace('&#8254;', "-") # overline = spacing overscore U+203E NEW
		txt = txt.replace('&#8260;', "/") # fraction slash U+2044 NEW
		txt = txt.replace('&#8364;', "EU$") # euro sign U+20AC NEW
		txt = txt.replace('&#8465;', "|I") # blackletter capital I = imaginary part U+2111 ISOamso
		txt = txt.replace('&#8472;', "|P") # script capital P = power set = Weierstrass p U+2118 ISOamso
		txt = txt.replace('&#8476;', "|R") # blackletter capital R = real part symbol U+211C ISOamso
		txt = txt.replace('&#8482;', "tm") # trade mark sign U+2122 ISOnum
		txt = txt.replace('&#8501;', "%") # alef symbol = first transfinite cardinal U+2135 NEW
		txt = txt.replace('&#8592;', "<-") # leftwards arrow U+2190 ISOnum
		txt = txt.replace('&#8593;', "^") # upwards arrow U+2191 ISOnum
		txt = txt.replace('&#8594;', "->") # rightwards arrow U+2192 ISOnum
		txt = txt.replace('&#8595;', "v") # downwards arrow U+2193 ISOnum
		txt = txt.replace('&#8596;', "<->") # left right arrow U+2194 ISOamsa
		txt = txt.replace('&#8629;', "<-'") # downwards arrow with corner leftwards = carriage return U+21B5 NEW
		txt = txt.replace('&#8656;', "<=") # leftwards double arrow U+21D0 ISOtech
		txt = txt.replace('&#8657;', "^") # upwards double arrow U+21D1 ISOamsa
		txt = txt.replace('&#8658;', "=>") # rightwards double arrow U+21D2 ISOtech
		txt = txt.replace('&#8659;', "v") # downwards double arrow U+21D3 ISOamsa
		txt = txt.replace('&#8660;', "<=>") # left right double arrow U+21D4 ISOamsa
		txt = txt.replace('&#8764;', "~") # tilde operator = varies with = similar to U+223C ISOtech
		txt = txt.replace('&#8773;', "~=") # approximately equal to U+2245 ISOtech
		txt = txt.replace('&#8776;', "~~") # almost equal to = asymptotic to U+2248 ISOamsr
		txt = txt.replace('&#8800;', "!=") # not equal to U+2260 ISOtech
		txt = txt.replace('&#8801;', "==") # identical to U+2261 ISOtech
		txt = txt.replace('&#8804;', "<=") # less-than or equal to U+2264 ISOtech
		txt = txt.replace('&#8805;', ">=") # greater-than or equal to U+2265 ISOtech
		txt = txt.replace('&#8901;', ".") # dot operator U+22C5 ISOamsb
		txt = txt.replace('&#913;', "Alpha") # greek capital letter alpha U+0391
		txt = txt.replace('&#914;', "Beta") # greek capital letter beta U+0392
		txt = txt.replace('&#915;', "Gamma") # greek capital letter gamma U+0393 ISOgrk3
		txt = txt.replace('&#916;', "Delta") # greek capital letter delta U+0394 ISOgrk3
		txt = txt.replace('&#917;', "Epsilon") # greek capital letter epsilon U+0395
		txt = txt.replace('&#918;', "Zeta") # greek capital letter zeta U+0396
		txt = txt.replace('&#919;', "Eta") # greek capital letter eta U+0397
		txt = txt.replace('&#920;', "Theta") # greek capital letter theta U+0398 ISOgrk3
		txt = txt.replace('&#921;', "Iota") # greek capital letter iota U+0399
		txt = txt.replace('&#922;', "Kappa") # greek capital letter kappa U+039A
		txt = txt.replace('&#923;', "Lambda") # greek capital letter lambda U+039B ISOgrk3
		txt = txt.replace('&#924;', "Mu") # greek capital letter mu U+039C
		txt = txt.replace('&#925;', "Nu") # greek capital letter nu U+039D
		txt = txt.replace('&#926;', "Xi") # greek capital letter xi U+039E ISOgrk3
		txt = txt.replace('&#927;', "Omicron") # greek capital letter omicron U+039F
		txt = txt.replace('&#928;', "Pi") # greek capital letter pi U+03A0 ISOgrk3
		txt = txt.replace('&#929;', "Rho") # greek capital letter rho U+03A1
		txt = txt.replace('&#931;', "Sigma") # greek capital letter sigma U+03A3 ISOgrk3
		txt = txt.replace('&#932;', "Tau") # greek capital letter tau U+03A4
		txt = txt.replace('&#933;', "Upsilon") # greek capital letter upsilon U+03A5 ISOgrk3
		txt = txt.replace('&#934;', "Phi") # greek capital letter phi U+03A6 ISOgrk3
		txt = txt.replace('&#935;', "Chi") # greek capital letter chi U+03A7
		txt = txt.replace('&#936;', "Psi") # greek capital letter psi U+03A8 ISOgrk3
		txt = txt.replace('&#937;', "Omega") # greek capital letter omega U+03A9 ISOgrk3
		txt = txt.replace('&#945;', "alpha") # greek small letter alpha U+03B1 ISOgrk3
		txt = txt.replace('&#946;', "beta") # greek small letter beta U+03B2 ISOgrk3
		txt = txt.replace('&#947;', "gamma") # greek small letter gamma U+03B3 ISOgrk3
		txt = txt.replace('&#948;', "delta") # greek small letter delta U+03B4 ISOgrk3
		txt = txt.replace('&#949;', "epsilon") # greek small letter epsilon U+03B5 ISOgrk3
		txt = txt.replace('&#950;', "zeta") # greek small letter zeta U+03B6 ISOgrk3
		txt = txt.replace('&#951;', "eta") # greek small letter eta U+03B7 ISOgrk3
		txt = txt.replace('&#952;', "theta") # greek small letter theta U+03B8 ISOgrk3
		txt = txt.replace('&#953;', "iota") # greek small letter iota U+03B9 ISOgrk3
		txt = txt.replace('&#954;', "kappa") # greek small letter kappa U+03BA ISOgrk3
		txt = txt.replace('&#955;', "lambda") # greek small letter lambda U+03BB ISOgrk3
		txt = txt.replace('&#956;', "mu") # greek small letter mu U+03BC ISOgrk3
		txt = txt.replace('&#957;', "nu") # greek small letter nu U+03BD ISOgrk3
		txt = txt.replace('&#958;', "xi") # greek small letter xi U+03BE ISOgrk3
		txt = txt.replace('&#959;', "omicron") # greek small letter omicron U+03BF NEW
		txt = txt.replace('&#960;', "pi") # greek small letter pi U+03C0 ISOgrk3
		txt = txt.replace('&#961;', "rho") # greek small letter rho U+03C1 ISOgrk3
		txt = txt.replace('&#962;', "sigma") # greek small letter final sigma U+03C2 ISOgrk3
		txt = txt.replace('&#963;', "sigma") # greek small letter sigma U+03C3 ISOgrk3
		txt = txt.replace('&#964;', "tau") # greek small letter tau U+03C4 ISOgrk3
		txt = txt.replace('&#965;', "upsilon") # greek small letter upsilon U+03C5 ISOgrk3
		txt = txt.replace('&#966;', "phi") # greek small letter phi U+03C6 ISOgrk3
		txt = txt.replace('&#967;', "chi") # greek small letter chi U+03C7 ISOgrk3
		txt = txt.replace('&#968;', "psi") # greek small letter psi U+03C8 ISOgrk3
		txt = txt.replace('&#969;', "omega") # greek small letter omega U+03C9 ISOgrk3
		txt = txt.replace('&#977;', "theta") # greek small letter theta symbol U+03D1 NEW
		txt = txt.replace('&#978;', "upsilon") # greek upsilon with hook symbol U+03D2 NEW
		txt = txt.replace('&#982;', "pi") # greek pi symbol U+03D6 ISOgrk3
		# remove any uncaught &#<number>;
		if find(txt,"&#") >= 0:
			reHash = re.compile('&#.+?;', re.IGNORECASE)
			txt = re.sub(reHash, '', txt)

	if find(txt,'&') >= 0:
		txt = txt.replace('&Aacute;', "A") # latin capital letter A with acute U+00C1 ISOlat1
		txt = txt.replace('&aacute;', "a") # latin small letter a with acute U+00E1 ISOlat1
		txt = txt.replace('&Acirc;', "A") # latin capital letter A with circumflex U+00C2 ISOlat1
		txt = txt.replace('&acirc;', "a") # latin small letter a with circumflex U+00E2 ISOlat1
		txt = txt.replace('&acute;', " ") # acute accent = spacing acute U+00B4 ISOdia
		txt = txt.replace('&AElig;', "AE") # latin capital letter AE = latin capital ligature AE U+00C6 ISOlat1
		txt = txt.replace('&aelig;', "ae") # latin small letter ae = latin small ligature ae U+00E6 ISOlat1
		txt = txt.replace('&Agrave;', "A") # latin capital letter A with grave = latin capital letter A grave U+00C0 ISOlat1
		txt = txt.replace('&agrave;', "a") # latin small letter a with grave = latin small letter a grave U+00E0 ISOlat1
		txt = txt.replace('&alefsym;', "%") # alef symbol = first transfinite cardinal U+2135 NEW
		txt = txt.replace('&Alpha;', "Alpha") # greek capital letter alpha U+0391
		txt = txt.replace('&alpha;', "alpha") # greek small letter alpha U+03B1 ISOgrk3
		txt = txt.replace('&amp;amp;','&')
		txt = txt.replace('&amp;;','&')
		txt = txt.replace('&amp;', "&") # ampersand U+0026 ISOnum		
		txt = txt.replace('&amp','&')		
		txt = txt.replace('&apos;', "'")
		txt = txt.replace('&Aring;', "A") # latin capital letter A with ring above = latin capital letter A ring U+00C5 ISOlat1
		txt = txt.replace('&aring;', "a") # latin small letter a with ring above = latin small letter a ring U+00E5 ISOlat1
		txt = txt.replace('&asymp;', "~~") # almost equal to = asymptotic to U+2248 ISOamsr
		txt = txt.replace('&Atilde;', "A") # latin capital letter A with tilde U+00C3 ISOlat1
		txt = txt.replace('&atilde;', "a") # latin small letter a with tilde U+00E3 ISOlat1
		txt = txt.replace('&auml;', "a")
		txt = txt.replace('&Auml;', "A")
		txt = txt.replace('&Auml;', "A") # latin capital letter A with diaeresis U+00C4 ISOlat1
		txt = txt.replace('&auml;', "a") # latin small letter a with diaeresis U+00E4 ISOlat1
		txt = txt.replace('&bdquo;', '"') # double low-9 quotation mark U+201E NEW
		txt = txt.replace('&Beta;', "Beta") # greek capital letter beta U+0392
		txt = txt.replace('&beta;', "beta") # greek small letter beta U+03B2 ISOgrk3
		txt = txt.replace('&brvbar;', "|") # broken bar = broken vertical bar U+00A6 ISOnum
		txt = txt.replace('&bull;', "o") # bullet = black small circle U+2022 ISOpub
		txt = txt.replace('&Ccedil;', "C") # latin capital letter C with cedilla U+00C7 ISOlat1
		txt = txt.replace('&ccedil;', "c") # latin small letter c with cedilla U+00E7 ISOlat1
		txt = txt.replace('&cedil;', " ") # cedilla = spacing cedilla U+00B8 ISOdia
		txt = txt.replace('&cent;', "c") # cent sign U+00A2 ISOnum
		txt = txt.replace('&Chi;', "Chi") # greek capital letter chi U+03A7
		txt = txt.replace('&chi;', "chi") # greek small letter chi U+03C7 ISOgrk3
		txt = txt.replace('&circ;', "") # modifier letter circumflex accent U+02C6 ISOpub
		txt = txt.replace('&cong;', "~=") # approximately equal to U+2245 ISOtech
		txt = txt.replace('&copy;', "(c)") # copyright sign U+00A9 ISOnum
		txt = txt.replace('&crarr;', "<-'") # downwards arrow with corner leftwards = carriage return U+21B5 NEW
		txt = txt.replace('&curren;', "$") # currency sign U+00A4 ISOnum
		txt = txt.replace('&dagger;', "|") # dagger U+2020 ISOpub
		txt = txt.replace('&Dagger;', "||") # double dagger U+2021 ISOpub
		txt = txt.replace('&darr;', "v") # downwards arrow U+2193 ISOnum
		txt = txt.replace('&dArr;', "v") # downwards double arrow U+21D3 ISOamsa
		txt = txt.replace('&deg;', "o") # degree sign U+00B0 ISOnum
		txt = txt.replace('&Delta;', "Delta") # greek capital letter delta U+0394 ISOgrk3
		txt = txt.replace('&delta;', "delta") # greek small letter delta U+03B4 ISOgrk3
		txt = txt.replace('&divide;', "/") # division sign U+00F7 ISOnum
		txt = txt.replace('&Eacute;', "E") # latin capital letter E with acute U+00C9 ISOlat1
		txt = txt.replace('&eacute;', "e") # latin small letter e with acute U+00E9 ISOlat1
		txt = txt.replace('&Ecirc;', "E") # latin capital letter E with circumflex U+00CA ISOlat1
		txt = txt.replace('&ecirc;', "e") # latin small letter e with circumflex U+00EA ISOlat1
		txt = txt.replace('&Egrave;', "E") # latin capital letter E with grave U+00C8 ISOlat1
		txt = txt.replace('&egrave;', "e") # latin small letter e with grave U+00E8 ISOlat1
		txt = txt.replace('&emsp;', " ") # em space U+2003 ISOpub
		txt = txt.replace('&ensp;', " ") # en space U+2002 ISOpub
		txt = txt.replace('&Epsilon;', "Epsilon") # greek capital letter epsilon U+0395
		txt = txt.replace('&epsilon;', "epsilon") # greek small letter epsilon U+03B5 ISOgrk3
		txt = txt.replace('&equiv;', "==") # identical to U+2261 ISOtech
		txt = txt.replace('&Eta;', "Eta") # greek capital letter eta U+0397
		txt = txt.replace('&eta;', "eta") # greek small letter eta U+03B7 ISOgrk3
		txt = txt.replace('&ETH;', "D") # latin capital letter ETH U+00D0 ISOlat1
		txt = txt.replace('&eth;', "d") # latin small letter eth U+00F0 ISOlat1
		txt = txt.replace('&Euml;', "E") # latin capital letter E with diaeresis U+00CB ISOlat1
		txt = txt.replace('&euml;', "e") # latin small letter e with diaeresis U+00EB ISOlat1
		txt = txt.replace('&euro;', "EU$") # euro sign U+20AC NEW
		txt = txt.replace('&fnof;', "f") # latin small f with hook = function = florin U+0192 ISOtech
		txt = txt.replace('&frac12;', "1/2") # vulgar fraction one half = fraction one half U+00BD ISOnum
		txt = txt.replace('&frac14;', "1/4") # vulgar fraction one quarter = fraction one quarter U+00BC ISOnum
		txt = txt.replace('&frac34;', "3/4") # vulgar fraction three quarters = fraction three quarters U+00BE ISOnum
		txt = txt.replace('&frasl;', "/") # fraction slash U+2044 NEW
		txt = txt.replace('&Gamma;', "Gamma") # greek capital letter gamma U+0393 ISOgrk3
		txt = txt.replace('&gamma;', "gamma") # greek small letter gamma U+03B3 ISOgrk3
		txt = txt.replace('&ge;', ">=") # greater-than or equal to U+2265 ISOtech
		txt = txt.replace('&gt;', ">") # greater-than sign U+003E ISOnum
		txt = txt.replace('&hArr;', "<=>") # left right double arrow U+21D4 ISOamsa
		txt = txt.replace('&harr;', "<->") # left right arrow U+2194 ISOamsa
		txt = txt.replace('&hellip;', "...") # horizontal ellipsis = three dot leader U+2026 ISOpub
		txt = txt.replace('&Iacute;', "I") # latin capital letter I with acute U+00CD ISOlat1
		txt = txt.replace('&iacute;', "i") # latin small letter i with acute U+00ED ISOlat1
		txt = txt.replace('&Icirc;', "I") # latin capital letter I with circumflex U+00CE ISOlat1
		txt = txt.replace('&icirc;', "i") # latin small letter i with circumflex U+00EE ISOlat1
		txt = txt.replace('&iexcl;', "!") # inverted exclamation mark U+00A1 ISOnum
		txt = txt.replace('&Igrave;', "E") # latin capital letter I with grave U+00CC ISOlat1
		txt = txt.replace('&igrave;', "i") # latin small letter i with grave U+00EC ISOlat1
		txt = txt.replace('&image;', "|I") # blackletter capital I = imaginary part U+2111 ISOamso
		txt = txt.replace('&Iota;', "Iota") # greek capital letter iota U+0399
		txt = txt.replace('&iota;', "iota") # greek small letter iota U+03B9 ISOgrk3
		txt = txt.replace('&iquest;', "?") # inverted question mark = turned question mark U+00BF ISOnum
		txt = txt.replace('&Iuml;', "I") # latin capital letter I with diaeresis U+00CF ISOlat1
		txt = txt.replace('&iuml;', "i") # latin small letter i with diaeresis U+00EF ISOlat1
		txt = txt.replace('&Kappa;', "Kappa") # greek capital letter kappa U+039A
		txt = txt.replace('&kappa;', "kappa") # greek small letter kappa U+03BA ISOgrk3
		txt = txt.replace('&Lambda;', "Lambda") # greek capital letter lambda U+039B ISOgrk3
		txt = txt.replace('&lambda;', "lambda") # greek small letter lambda U+03BB ISOgrk3
		txt = txt.replace('&laquo;', '"') # left-pointing double angle quotation mark = left pointing guillemet U+00AB ISOnum
		txt = txt.replace('&larr;', "<-") # leftwards arrow U+2190 ISOnum
		txt = txt.replace('&lArr;', "<=") # leftwards double arrow U+21D0 ISOtech
		txt = txt.replace('&ldquo;', '"') # left double quotation mark U+201C ISOnum
		txt = txt.replace('&le;', "<=") # less-than or equal to U+2264 ISOtech
		txt = txt.replace('&lrm;', "") # left-to-right mark U+200E NEW RFC 2070
		txt = txt.replace('&lsaquo;', '"') # single left-pointing angle quotation mark U+2039 ISO proposed
		txt = txt.replace('&lsquo;', '"') # left single quotation mark U+2018 ISOnum
		txt = txt.replace('&lt;', "<") # less-than sign U+003C ISOnum
		txt = txt.replace('&macr;', "-") # macron = spacing macron = overline = APL overbar U+00AF ISOdia
		txt = txt.replace('&mdash;', "---") # em dash U+2014 ISOpub
		txt = txt.replace('&micro;', "u") # micro sign U+00B5 ISOnum
		txt = txt.replace('&middot;', ".") # middle dot = Georgian comma = Greek middle dot U+00B7 ISOnum
		txt = txt.replace('&Mu;', "Mu") # greek capital letter mu U+039C
		txt = txt.replace('&mu;', "mu") # greek small letter mu U+03BC ISOgrk3
		txt = txt.replace('&nbsp;&nbsp;',' ')
		txt = txt.replace('&nbsp;', " ") # no-break space = non-breaking space U+00A0 ISOnum
		txt = txt.replace('&ndash;', "--") # en dash U+2013 ISOpub
		txt = txt.replace('&ne;', "!=") # not equal to U+2260 ISOtech
		txt = txt.replace('&not;', "-.") # not sign U+00AC ISOnum
		txt = txt.replace('&Ntilde;', "N") # latin capital letter N with tilde U+00D1 ISOlat1
		txt = txt.replace('&ntilde;', "n") # latin small letter n with tilde U+00F1 ISOlat1
		txt = txt.replace('&Nu;', "Nu") # greek capital letter nu U+039D
		txt = txt.replace('&nu;', "nu") # greek small letter nu U+03BD ISOgrk3
		txt = txt.replace('&Oacute;', "O") # latin capital letter O with acute U+00D3 ISOlat1
		txt = txt.replace('&oacute;', "o") # latin small letter o with acute U+00F3 ISOlat1
		txt = txt.replace('&Ocirc;', "O") # latin capital letter O with circumflex U+00D4 ISOlat1
		txt = txt.replace('&ocirc;', "o") # latin small letter o with circumflex U+00F4 ISOlat1
		txt = txt.replace('&OElig;', "OE") # latin capital ligature OE U+0152 ISOlat2
		txt = txt.replace('&oelig;', "oe") # latin small ligature oe U+0153 ISOlat2
		txt = txt.replace('&Ograve;', "O") # latin capital letter O with grave U+00D2 ISOlat1
		txt = txt.replace('&ograve;', "o") # latin small letter o with grave U+00F2 ISOlat1
		txt = txt.replace('&oline;', "-") # overline = spacing overscore U+203E NEW
		txt = txt.replace('&Omega;', "Omega") # greek capital letter omega U+03A9 ISOgrk3
		txt = txt.replace('&omega;', "omega") # greek small letter omega U+03C9 ISOgrk3
		txt = txt.replace('&Omicron;', "Omicron") # greek capital letter omicron U+039F
		txt = txt.replace('&omicron;', "omicron") # greek small letter omicron U+03BF NEW
		txt = txt.replace('&ordf;', "e") # feminine ordinal indicator U+00AA ISOnum
		txt = txt.replace('&ordm;', "o") # masculine ordinal indicator U+00BA ISOnum
		txt = txt.replace('&Oslash;', "O") # latin capital letter O with stroke = latin capital letter O slash U+00D8 ISOlat1
		txt = txt.replace('&oslash;', "o") # latin small letter o with stroke = latin small letter o slash U+00F8 ISOlat1
		txt = txt.replace('&Otilde;', "O") # latin capital letter O with tilde U+00D5 ISOlat1
		txt = txt.replace('&otilde;', "o") # latin small letter o with tilde U+00F5 ISOlat1
		txt = txt.replace('&Ouml;', "O") # latin capital letter O with diaeresis U+00D6 ISOlat1
		txt = txt.replace('&ouml;', "o") # latin small letter o with diaeresis U+00F6 ISOlat1
		txt = txt.replace('&para;', "|p") # pilcrow sign = paragraph sign U+00B6 ISOnum
		txt = txt.replace('&permil;', "%0") # per mille sign U+2030 ISOtech
		txt = txt.replace('&Phi;', "Phi") # greek capital letter phi U+03A6 ISOgrk3
		txt = txt.replace('&phi;', "phi") # greek small letter phi U+03C6 ISOgrk3
		txt = txt.replace('&Pi;', "Pi") # greek capital letter pi U+03A0 ISOgrk3
		txt = txt.replace('&pi;', "pi") # greek small letter pi U+03C0 ISOgrk3
		txt = txt.replace('&piv;', "pi") # greek pi symbol U+03D6 ISOgrk3
		txt = txt.replace('&plusmn;', "+-") # plus-minus sign = plus-or-minus sign U+00B1 ISOnum
		txt = txt.replace('&pound;', "p") # pound sign U+00A3 ISOnum
		txt = txt.replace('&Prime;', "''") # double prime = seconds = inches U+2033 ISOtech
		txt = txt.replace('&prime;', "'") # prime = minutes = feet U+2032 ISOtech
		txt = txt.replace('&Psi;', "Psi") # greek capital letter psi U+03A8 ISOgrk3
		txt = txt.replace('&psi;', "psi") # greek small letter psi U+03C8 ISOgrk3
		txt = txt.replace('&quot;', '"') # quotation mark = APL quote U+0022 ISOnum
		txt = txt.replace('&raquo;', '"') # right-pointing double angle quotation mark = right pointing guillemet U+00BB ISOnum
		txt = txt.replace('&rArr;', "=>") # rightwards double arrow U+21D2 ISOtech
		txt = txt.replace('&rarr;', "->") # rightwards arrow U+2192 ISOnum
		txt = txt.replace('&rdquo;', '"') # right double quotation mark U+201D ISOnum
		txt = txt.replace('&real;', "|R") # blackletter capital R = real part symbol U+211C ISOamso
		txt = txt.replace('&reg;', "(R)") # registered sign = registered trade mark sign U+00AE ISOnum
		txt = txt.replace('&Rho;', "Rho") # greek capital letter rho U+03A1
		txt = txt.replace('&rho;', "rho") # greek small letter rho U+03C1 ISOgrk3
		txt = txt.replace('&rlm;', "") # right-to-left mark U+200F NEW RFC 2070
		txt = txt.replace('&rsaquo;', '"') # single right-pointing angle quotation mark U+203A ISO proposed
		txt = txt.replace('&rsquo;', '"') # right single quotation mark U+2019 ISOnum
		txt = txt.replace('&sbquo;', '"') # single low-9 quotation mark U+201A NEW
		txt = txt.replace('&Scaron;', "S") # latin capital letter S with caron U+0160 ISOlat2
		txt = txt.replace('&scaron;', "s") # latin small letter s with caron U+0161 ISOlat2
		txt = txt.replace('&sdot;', ".") # dot operator U+22C5 ISOamsb
		txt = txt.replace('&sect;', "S") # section sign U+00A7 ISOnum
		txt = txt.replace('&shy;', "-") # soft hyphen = discretionary hyphen U+00AD ISOnum
		txt = txt.replace('&Sigma;', "Sigma") # greek capital letter sigma U+03A3 ISOgrk3
		txt = txt.replace('&sigma;', "sigma") # greek small letter sigma U+03C3 ISOgrk3
		txt = txt.replace('&sigmaf;', "sigma") # greek small letter final sigma U+03C2 ISOgrk3
		txt = txt.replace('&sim;', "~") # tilde operator = varies with = similar to U+223C ISOtech
		txt = txt.replace('&sup1;', "1") # superscript one = superscript digit one U+00B9 ISOnum
		txt = txt.replace('&sup2;', "2") # superscript two = superscript digit two = squared U+00B2 ISOnum
		txt = txt.replace('&sup3;', "3") # superscript three = superscript digit three = cubed U+00B3 ISOnum
		txt = txt.replace('&szlig;', "SS") # latin small letter sharp s = ess-zed U+00DF ISOlat1
		txt = txt.replace('&Tau;', "Tau") # greek capital letter tau U+03A4
		txt = txt.replace('&tau;', "tau") # greek small letter tau U+03C4 ISOgrk3
		txt = txt.replace('&Theta;', "Theta") # greek capital letter theta U+0398 ISOgrk3
		txt = txt.replace('&theta;', "theta") # greek small letter theta U+03B8 ISOgrk3
		txt = txt.replace('&thetasym;', "theta") # greek small letter theta symbol U+03D1 NEW
		txt = txt.replace('&thinsp;', " ") # thin space U+2009 ISOpub
		txt = txt.replace('&THORN;', "D") # latin capital letter THORN U+00DE ISOlat1
		txt = txt.replace('&thorn;', "d") # latin small letter thorn U+00FE ISOlat1
		txt = txt.replace('&tilde;', "~") # small tilde U+02DC ISOdia
		txt = txt.replace('&times;', "x") # multiplication sign U+00D7 ISOnum
		txt = txt.replace('&trade;', "tm") # trade mark sign U+2122 ISOnum
		txt = txt.replace('&Uacute;', "U") # latin capital letter U with acute U+00DA ISOlat1
		txt = txt.replace('&uacute;', "u") # latin small letter u with acute U+00FA ISOlat1
		txt = txt.replace('&uarr;', "^") # upwards arrow U+2191 ISOnum
		txt = txt.replace('&uArr;', "^") # upwards double arrow U+21D1 ISOamsa
		txt = txt.replace('&Ucirc;', "U") # latin capital letter U with circumflex U+00DB ISOlat1
		txt = txt.replace('&ucirc;', "u") # latin small letter u with circumflex U+00FB ISOlat1
		txt = txt.replace('&Ugrave;', "U") # latin capital letter U with grave U+00D9 ISOlat1
		txt = txt.replace('&ugrave;', "u") # latin small letter u with grave U+00F9 ISOlat1
		txt = txt.replace('&uml;', "''") # diaeresis = spacing diaeresis U+00A8 ISOdia
		txt = txt.replace('&upsih;', "upsilon") # greek upsilon with hook symbol U+03D2 NEW
		txt = txt.replace('&Upsilon;', "Upsilon") # greek capital letter upsilon U+03A5 ISOgrk3
		txt = txt.replace('&upsilon;', "upsilon") # greek small letter upsilon U+03C5 ISOgrk3
		txt = txt.replace('&Uuml;', "U") # latin capital letter U with diaeresis U+00DC ISOlat1
		txt = txt.replace('&uuml;', "u") # latin small letter u with diaeresis U+00FC ISOlat1
		txt = txt.replace('&weierp;', "P") # script capital P = power set = Weierstrass p U+2118 ISOamso
		txt = txt.replace('&Xi;', "Xi") # greek capital letter xi U+039E ISOgrk3
		txt = txt.replace('&xi;', "xi") # greek small letter xi U+03BE ISOgrk3
		txt = txt.replace('&Yacute;', "Y") # latin capital letter Y with acute U+00DD ISOlat1
		txt = txt.replace('&yacute;', "y") # latin small letter y with acute U+00FD ISOlat1
		txt = txt.replace('&yen;', "y") # yen sign = yuan sign U+00A5 ISOnum
		txt = txt.replace('&Yuml;', "Y") # latin capital letter Y with diaeresis U+0178 ISOlat2
		txt = txt.replace('&yuml;', "y") # latin small letter y with diaeresis U+00FF ISOlat1
		txt = txt.replace('&Zeta;', "Zeta") # greek capital letter zeta U+0396
		txt = txt.replace('&zeta;', "zeta") # greek small letter zeta U+03B6 ISOgrk3
		txt = txt.replace('&zwj;', "|") # zero width joiner U+200D NEW RFC 2070
		txt = txt.replace('&zwnj;', " ") # zero width non-joiner U+200C NEW RFC 2070

	if removeNewLines:
		txt = txt.replace('\n','')
		txt = txt.replace('\r','')

	return txt


#######################################################################################################################    
def parseDocList(doc, regex, startStr='', endStr=''):
	if not doc: return []
	# find section
	startPos = -1
	endPos = -1
	if startStr:
		startPos = find(doc,startStr)
		if startPos == -1:
			print "parseDocList() start not found " + startStr

	if endStr:
		endPos = find(doc, endStr, startPos+1)
		if endPos == -1:
			print "parseDocList() end not found " + endStr

	if startPos < 0:
		startPos = 0
	if endPos < 0 or endPos <= startPos:
		endPos = len(doc)-1

	# do regex on section
	try:
		findRe = re.compile(regex, re.DOTALL + re.MULTILINE + re.IGNORECASE)
		matchList = findRe.findall(doc[startPos:endPos])
	except:
		matchList = []

	if matchList:
		sz = len(matchList)
	else:
		sz = 0
	print( "parseDocList() matches=%s" % sz)
	return matchList

#################################################################################################################
def searchRegEx(data, regex, flags=re.IGNORECASE):
	if not data: return ""
	try:
		value = re.search(regex, data, flags).group(1)
	except:
		value = ""
	return value

#################################################################################################################
def findAllRegEx(data, regex, flags=re.MULTILINE+re.IGNORECASE+re.DOTALL):
	if not data: return ""
	try:
		matchList = re.compile(regex, flags).findall(data)
	except:
		matchList = []

	if matchList:
		print "parseDocList() matches = ", len(matchList)
	else:
		print "parseDocList() matches = 0"
	return matchList

#############################################################################################################
def safeFilename(path):
	head, tail = os.path.split(path)
	name, ext = os.path.splitext(tail)
	return  os.path.join(head, cleanPunctuation(name, replaceCh) + ext)

#################################################################################################################
def cleanPunctuation(text, replaceCh='_'):
	if not text: return ""
	try:
		return re.sub(r'[\'\";:?*<>|+\\/,=!\.]', replaceCh, text)
	except:
		debug("cleanPunctuation() re failed")
		return text

#################################################################################################################
def unicodeToAscii(text, charset='utf8'):
	if not text: return ""
	try:
		newtxt = text.decode(charset)
		newtxt = unicodedata.normalize('NFKD', newtxt).encode('ASCII','replace')
		return newtxt
	except:
		return text

#################################################################################################################
class RSSParser2:
	def __init__(self):
		debug("RSSParser2().init()")

	# feeds the xml document from given url or file to the parser
	def feed(self, url="", file="", doc="", title=""):
		debug("> RSSParser2().feed()")
		success = False
		self.dom = None

		if url:
			debug("parseString from URL")
			if not file:
				dir = os.getcwd().replace(';','')
				file = os.path.join(dir, "temp.xml")
			doc = fetchURL(url, file)
		elif file:
			debug("parseString from FILE " + file)
			doc = readFile(file)
		else:
			debug("parseString from DOC")

		if doc:
			success = self.__parseString(doc)

		debug("< RSSParser2().feed() success: " + str(success))
		return success

	def __parseString(self, xmlDocument):
		debug("> RSSParser2().__parseString()")
		success = True
		try:
			self.dom = parseString(xmlDocument.encode( "utf-8" ))
		except UnicodeDecodeError:
			try:
				debug("__parseString() UnicodeDecodeError, try unicodeToAscii")
				self.dom = parseString(unicodeToAscii(xmlDocument))
			except:
				debug("__parseString() unicodeToAscii failed")
				self.dom = parseString(xmlDocument)
		except:
			success = False

		if not self.dom:
			messageOK("XML Parser Failed","Empty/Bad XML file","Unable to parse data.")

		debug("< RSSParser2().__parseString() success: " + str(success))
		return success


	# parses RSS document items and returns an list of objects
	def __parseElements(self, tagName, elements, elementDict):
		debug("> RSSParser2().__parseElements() element count=%s" % len(elements))

		# extract required attributes from element attribute
		def _get_element_attributes(el, attrNameList):
			attrDataList = {}
			for attrName in attrNameList:
				data = el.getAttribute( attrName )
				if data:
					attrDataList[attrName] = data
			return attrDataList
		
		objectsList = []
		for index, el in enumerate(elements):
			dict = {}
			# check element attributes
			elAttrItems = el.attributes.items()

			# get data from item with attributes
			if elAttrItems and elementDict.has_key(tagName):
				attrDataList= _get_element_attributes(el, elementDict[tagName])
				if attrDataList:
					dict[tagName] = attrDataList

			# get data from item
			for elTagName, attrNameList in elementDict.items():
				if elTagName == tagName:
					# skip element tagName - already processed it attributes
					continue

				data = None

				try:
					# get value for tag (without any attributes)
					data = el.getElementsByTagName(elTagName)[0].childNodes[0].data
				except:
					try:
						# get required attributes from tag
						subEl = el.getElementsByTagName(elTagName)[0]
						attrItems = subEl.attributes.items()
						data = _get_element_attributes(subEl, attrNameList)
					except: pass

				if data:
#					debug("Tag: %s = %s" % (elTagName, data)
					dict[elTagName] = data
#				else:
#					debug("Tag: %s No Data found" % (elTagName, )

			if debug:
				print "%s %s" % (index, dict)
			objectsList.append(RSSNode(dict))

		debug("< RSSParser2().__parseElements() No. objects= %s" % len(objectsList))
		return objectsList


	# parses the RSS document
	def parse(self, tagName, elementDict):
		debug("> RSSParser2().parse() tagName: %s %s" % (tagName,elementDict))

		parsedList = None
		if self.dom:
			try:
				elements = self.dom.getElementsByTagName(tagName)
				parsedList = self.__parseElements(tagName, elements, elementDict)
			except:
				debug("exception No parent elements found for tagName")

		debug("< RSSParser2().parse()")
		return parsedList

#################################################################################################################
class RSSNode:
	def __init__(self, elements):
		self.elements = elements
		
	def getElement(self, element):
		try:
			return self.elements[element]
		except:
			return ""
		
	def getElementNames(self):
		return self.elements.keys()
		
	def hasElement(self, element):
		return self.elements.has_key(element)

##############################################################################################################    
def playMedia(filename):
	debug("> playMedia() " + filename)
	success = False

	try:
		xbmc.Player().stop()
		xbmc.Player().play(filename)
		success = xbmc.Player().isPlaying()
	except: pass

	if not success:
		debug('xbmc.Player().play() failed, trying xbmc.PlayMedia() ')
		try:
			cmd = 'xbmc.PlayMedia(%s)' % filename
			result = xbmc.executebuiltin(cmd)
			success = True
		except:
			traceback.print_exc()
	debug("< playMedia() success=%s" % success)
	return success

#######################################################################################################################    
# BEGIN !
#######################################################################################################################
try:
	os.makedirs(DIR_USERDATA)
except: pass

if ( __name__ == "__main__" ):
	app = BBCPodRadioPlugin()
	del app

# remove other globals
try:
	del dialogProgress
except: pass

