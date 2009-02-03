"""
	Support module for reeplay.it script.
	Written by BigBellyBilly - 2009
"""
import urllib2, sys, os, os.path
import cookielib, traceback
import xbmc, xbmcgui
import xbmcutils.net as net
from xml.sax.saxutils import unescape
from pprint import pprint

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__title__ = "reeplayitLib"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '29-01-2009'
xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)

DIR_HOME = sys.modules[ "__main__" ].DIR_HOME
DIR_CACHE = sys.modules[ "__main__" ].DIR_CACHE
__lang__ = sys.modules[ "__main__" ].__lang__

from bbbLib import *
from bbbSkinGUILib import TextBoxDialogXML

##############################################################################################################
##############################################################################################################
class ReeplayitLib:
	""" Reeplay.it data gatherer / store """

	URL_BASE = "http://staging.reeplay.it/"        # LIVE is "http://reeplay.it/"

	def __init__(self, user, pwd, pageSize=200, vq=False, docType='xml', isPlugin=False):
		debug("ReeplayitLib() __init__ %s %s pageSize=%d vq=%s docType=%s isPlugin=%s" % (user, pwd, pageSize, vq, docType, isPlugin))

		self.user = user
		self.pageSize = pageSize
		self.docType = docType
		self.isPlugin = isPlugin
		self.setVideoProfile(vq)
		
		self.PROP_ID = "ID"					# pls id
		self.PROP_COUNT = "COUNT"			# pls video count
		self.PROP_URL = "URL"				# video url

		try:
			# password manager handler
			passman = urllib2.HTTPPasswordMgrWithDefaultRealm()
			passman.add_password(None, self.URL_BASE, user, pwd)

			# Basic Auth. handler
			authhandler = urllib2.HTTPBasicAuthHandler(passman)

			# Cookie handler
			cookiejar = cookielib.LWPCookieJar()
			cookiehandler = urllib2.HTTPCookieProcessor(cookiejar)

			# add our handlers
			urlopener = urllib2.build_opener(authhandler, cookiehandler)

			# install urlopener so all urllib2 calls use our handlers
			urllib2.install_opener(urlopener)
			debug("HTTP handlers installed")
		except:
			handleException("HTTP handlers")
			return

		self.URL_PLAYLISTS = self.URL_BASE + "users/%s/playlists." + self.docType
		self.URL_PLAYLIST = self.URL_BASE + "users/%s/playlists/%s."+self.docType+"?page=%s&page_size=%s"
		self.URL_VIDEO_INFO = self.URL_BASE + "users/%s/contents/%s." + self.docType + "?profile=%s"

		self.plsListItems = []
		self.videoListItems = []
		self.DEFAULT_THUMB_IMG = xbmc.makeLegalFilename(os.path.join(DIR_HOME, "default.tbn"))

	def debug(self, msg=""):
		debug("%s.%s" % (self.__class__.__name__, msg))

	##############################################################################################################
	def setVideoProfile(self, vq):
		self.vqProfile = ( 'xbmc_high', 'xbmc_standard' )[vq]
		self.debug("setVideoProfile() %s" % self.vqProfile)

	##############################################################################################################
	def setPageSize(self, pageSize):
		self.pageSize = pageSize

	##############################################################################################################
	def retrieve(self, url, post=None, headers={}, fn=None):
		""" Downloads an url. Returns: None = error , '' = cancelled """
		self.debug("retrieve() %s" % url)
		try:
			return net.retrieve (url, post, headers, self.report_hook, self.report_udata, fn)
		except net.AuthError, e:
			messageOK(__lang__(0), __lang__(108))
		except net.DownloadAbort, e:
			messageOK(__lang__(102), e.value)
			return "" # means aborted
		except net.DownloadError, e:
			messageOK(__lang__(102), e.value)
		except:
			handleException(__lang__(0))
		return None

	##############################################################################################################
	def set_report_hook(self, func, udata=None):
		"""Set the download progress report handler."""
		self.debug("set_report_hook()")
		self.report_hook = func
		self.report_udata = udata

	##############################################################################################################
	def getPlaylists(self):
		self.debug("> getPlaylists()")

		if not self.plsListItems:

			dialogProgress.create(__lang__(0), __lang__(215))
			self.set_report_hook(self.progressHandler, dialogProgress)

			# if exist, load from cache
			playlistsURL = self.URL_PLAYLISTS % self.user
			docFN = os.path.join( DIR_CACHE, os.path.basename(playlistsURL) )
			self.debug("docFN=" + docFN)
			data = readFile(docFN)
			if not data:
				# not in cache, download
				data = self.retrieve(playlistsURL)

			if data:
				items = self.parsePlaylists(data)

				# load data into content list
				self.debug("storing data to listItems ...")
				for item in items:
					try:
						title, id, desc, count, updatedDate, imgURL = item

						# get thumb image
						imgName = os.path.basename(imgURL)
						imgFN = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, imgName))
						if not fileExist(imgFN):
							data = self.retrieve(imgURL, fn=imgFN)
							if data == "": # aborted
								break
							elif not data:
								imgFN = self.DEFAULT_THUMB_IMG

						longTitle = "%s (%s)" % (title, count)
						li = xbmcgui.ListItem(longTitle, desc, imgFN, imgFN)
						li.setProperty(self.PROP_ID, id)
						li.setProperty(self.PROP_COUNT, str(count))
						li.setInfo("Video", {"Title" : title, "Size": count, \
											"Album" : desc, "Date" : updatedDate})
						self.plsListItems.append(li)
					except:
						traceback.print_exc()

				del items
			dialogProgress.close()

		count = len(self.plsListItems)
		self.debug("< getPlaylists() count=%s" % count)
		return count

	##############################################################################################################
	def getPlaylist(self, plsId="", page=1, pageSize=0):
		""" Download video list for playlist """
		self.debug("> getPlaylist() plsId=%s page=%d pageSize=%d" % (plsId, page, pageSize))

		# reset stored videos
		self.videoListItems = []
		totalsize = 0
		# use settings pageSize, unless overridden
		if not pageSize:
			pageSize = self.pageSize

		# load cached file
		docFN = os.path.join(DIR_CACHE, "pls_%s_page_%d.%s" % (plsId, page, self.docType))
		self.debug("docFN=" + docFN)
		data = readFile(docFN)
		if not data:
			# not cached, download
			url = self.URL_PLAYLIST % (self.user, plsId, page, pageSize)
			data = self.retrieve(url)
			saveData(data, docFN)

		if data:
			dialogProgress.update(0, __lang__(210), "") # parsing
			items = self.parsePlaylist(data)

			# load data into content list
			if items:
				self.debug("storing items as listitems ...")
				totalsize = len(items)
				
				dialogProgress.update(0, __lang__(210)) # + " (%d) % totalsize")
				lastPercent = 0
				for itemCount, item in enumerate(items):
					try:
						title, videoid, captured, link, imgURL, duration = item
						link += "?profile=%s" % self.vqProfile
						if not videoid:
							continue

						percent = int((itemCount * 100.0) / totalsize)
						if percent != lastPercent and percent % 5 == 0:
							lastPercent = percent
							countMsg = "(%d / %d)" % (itemCount+1, totalsize)
							dialogProgress.update(percent, __lang__(210), countMsg )
							if dialogProgress.iscanceled():
								self.debug("parsing cancelled")
								break

						# get thumb image
						imgName = videoid+".jpg"
						imgFN = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, imgName))
						if not fileExist(imgFN):
							result = self.retrieve(imgURL, fn=imgFN)
							if result == "": # aborted
								break
							elif not result:
								imgFN = self.DEFAULT_THUMB_IMG

						lbl2 = "%.1f mins" % (float(duration) / 60)
						li = xbmcgui.ListItem(title, lbl2, imgFN, imgFN)
						li.setInfo("video", {"Title" : title, "Date" : captured, "Duration" : duration})
						li.setProperty(self.PROP_ID, videoid)
						li.setProperty(self.PROP_URL, link)
						self.videoListItems.append(li)
					except:
						traceback.print_exc()

				del items

		dialogProgress.close()
		# delete file if failed to parse etc
		if not self.videoListItems:
			deleteFile(docFN)

		self.debug("< getPlaylist() totalsize=%s" % totalsize)
		return totalsize

	##############################################################################################################
	def getVideo(self, idx=-1, id="", title="", download=False):
		""" Download the selected video info doc to get video url """
		self.debug("> getVideo() idx=%s id=%s download=%s" % (idx, id, download))
		fn = None

		# get LI info
		if not id:
			li = self.getVideoLI(idx)
			title = li.getLabel()
			id = li.getProperty(self.PROP_ID)
#			infoUrl = li.getProperty(self.PROP_URL)
			self.debug("From idx; id=%s title=%s" % (id, title))
		else:
			# from plugin, create a video li
			li = xbmcgui.ListItem( title )

		dialogProgress.create(__lang__(0))
		self.set_report_hook(self.progressHandler, dialogProgress)
		dialogProgress.update(0, __lang__(222), title)

		videoURL = self.getVideoMediaUrl(id)
		
		# download and save video from its unique media-url
		if videoURL:
			# download video to cache
			basename = os.path.basename(videoURL)
			videoName = "%s_%s%s" % (id, self.vqProfile, os.path.splitext(basename)[1])		# eg ".mp4"
			fn = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, videoName))
			self.debug( "video fn=" + fn )
			if not fileExist(fn):
				# if not in cache, do stream or download
				if download:
					self.debug("download video")
					dialogProgress.update(0,  __lang__(223), title, videoName)
					if not self.retrieve(videoURL, fn=fn):
						deleteFile(fn)	# delete incase of partial DL
						fn = ''
				else:
					# stream, so return url
					self.debug("stream video")
					fn = videoURL
			else:
				self.debug("video file exists")

		dialogProgress.close()

		self.debug("< getVideo() fn=%s li=%s" % (fn, li))
		return (fn, li)

	##############################################################################################################
	def getVideoMediaUrl(self, videoId):
		""" Download the selected video info doc to get video url """
		self.debug("> getVideoMediaUrl() videoId=%s" % videoId)

		videoURL = ""
		infoUrl = self.URL_VIDEO_INFO % (self.user, videoId, self.vqProfile)
		self.debug("infoUrl=" + infoUrl)

		# if exist, load cached
		docFN = os.path.join(DIR_CACHE, "%s_%s.%s" % (videoId, self.vqProfile, self.docType))
		self.debug("docFN=" + docFN)
		data = readFile(docFN)
		if not data:
			if self.isPlugin:
				debug("http authenticate ...")
				# This is for Plugin; as it won't have done Auth. before getVideo() call
				dialogProgress.update(0, "User Authentication ...")
				if not self.retrieve(self.URL_PLAYLISTS % self.user):
					dialogProgress.close()
					messageOK("Error", __lang__(108))	# auth failed.
					self.debug("< getVideoMediaUrl() failed auth.")
					return ""
			# not cached, download
			data = self.retrieve(infoUrl)
			saveData(data, docFN)

		# parse video info to get media-url
		if data:
			videoURL = self.parseVideo(data)
		if not videoURL:
			messageOK(__lang__(0), "Video Media URL missing!")
			deleteFile(docFN) # incase its a bad info doc
		
		self.debug("< getVideoMediaUrl() videoURL=%s" % videoURL)
		return videoURL

	##############################################################################################################
	def getPlsLI(self, idx):
		try:
			return self.plsListItems[idx]
		except:
			return None

	##############################################################################################################
	def getVideoLI(self, idx):
		try:
			return self.videoListItems[idx]
		except:
			return None

	##############################################################################################################
	def getMaxPages(self, plsCount):
		maxPages = int(plsCount / self.pageSize)
		mod = plsCount % self.pageSize
		if mod:
			maxPages += 1
		self.debug("getMaxPages() %d" % maxPages)
		return maxPages

	##############################################################################################################
	def progressHandler(self, count, totalsize, dlg):
		"""Update progress dialog percent and return abort status."""

		try:
			if count and totalsize:
				percent = int((count * 100) / totalsize)
				if (percent % 5) == 0:
					dlg.update( percent )
		except:
			traceback.print_exc()

		return not dlg.iscanceled()

	##############################################################################################################
	def parsePlaylists(self, doc):
		""" Wrapper to call Playlists parsing """
		self.debug("parsePlaylists()")
		if self.docType == "json":
			return parsePlaylistsJSON(doc)
		else:
			return parsePlaylistsXML(doc)

	##############################################################################################################
	def parsePlaylist(self, doc):
		""" Wrapper to call Playlist parsing """
		self.debug("parsePlaylist()")
		if self.docType == "json":
			return parsePlaylistJSON(doc)
		else:
			return parsePlaylistXML(doc)

	##############################################################################################################
	def parseVideo(self, doc):
		""" Wrapper to parse Video info doc  """
		self.debug("parseVideo()")
		if self.docType == "json":
			return parseVideoJSON(doc)
		else:
			return parseVideoXML(doc)



##############################################################################################################
def parsePlaylistsXML(doc):
	""" Parse Playlists XML using regex to [ [], [], [] ... ] """
	debug("parsePlaylistsXML()")

	data = []
	idList = findAllRegEx(doc, '<id>(\d+)</')
	titleList = findAllRegEx(doc, '<title>(.*?)</')
	descList = findAllRegEx(doc, '<description>(.*?)</')
	countList = findAllRegEx(doc, '<contents_count>(\d+)</')
	updatedList = findAllRegEx(doc, '<updated_at>(\d\d\d\d.\d\d.\d\d)')
	imgList  = findAllRegEx(doc, '<img.*?src="(.*?)"')
	itemCount = len(idList)
	debug("ParsePlaylists.itemCount=%d" % itemCount)
	for i in range(itemCount):
		data.append((unescape(titleList[i]), idList[i], unescape(descList[i]), int(countList[i]), updatedList[i], imgList[i]))
	data.sort()
	return data


##############################################################################################################
def parsePlaylistXML(doc):
	""" Parse Playlist XML to get videos using regex """
	debug("parsePlaylistXML()")

	data = []
	videos = findAllRegEx(doc, '(<content>.*?</content>)')
	debug("ParsePlaylist.itemCount=%d" % len(videos))
	for video in videos:
		data.append( ( unescape(searchRegEx(video, '<title>(.*?)</')), \
						searchRegEx(video, '<id>(.*?)<'), \
						searchRegEx(video, '<captured_at>(\d\d\d\d.\d\d.\d\d)'), \
						searchRegEx(video, '<link>(.*?)</').strip() + ".xml", \
						searchRegEx(video, '<img.*?src="(.*?)"'), \
						searchRegEx(video, '<duration>(.*?)<')) )
#	if DEBUG:
#		pprint (data)
	return data

##############################################################################################################
def parsePlaylistsJSON(doc):
	""" Parse Playlists JSON using eval to [ [], [], [] ... ] """
	debug("parsePlaylistsJSON()")

	data = []
	try:
		# evals to [ {}, {}, .. ]
		items = eval( doc.replace('null', '\"\"' ) )
		# convert to [ [], [], .. ] as its easier to unpack without key knowlegde
		for item in items:
			try:
				updated = item.get('updated_at','')[:10]				# yyyy/mm/dd
			except:
				updated = ''
			data.append( (unescape(item.get('title','')), \
						str(item.get('id','')), \
						unescape(item.get('description','')), \
						item.get('contents_count',0), \
						updated, \
						item.get('icon_url','')) )
		data.sort()
	except:
		traceback.print_exc()
		data = []
#	if DEBUG:
#		pprint (data)
	return data


##############################################################################################################
def parsePlaylistJSON(doc):
	""" Parse Playlist JSON to get videos using eval """
	debug("parsePlaylistJSON()")

	data = []
	try:
		# evals to [ {}, {}, .. ]
		items = eval( doc )['contents']
		# convert to [ [], [], .. ] as its easier to unpack without key knowlegde
		for item in items:
			link = item.get('link','')
			id = link[link.rfind('/')+1:]							# extract ID off end of link eg /1167
			try:
				captured = item.get('captured','')[:10]				# yyyy/mm/dd
			except:
				captured = ''
			data.append( (
					unescape(item.get('title','')), \
					id, \
					captured, \
					link + ".json", \
					item.get('keyframe_url',''),
					str(item.get('duration','0'))
					) )
	except:
		traceback.print_exc()
		data = []
#	if DEBUG:
#		pprint (data)
	return data

##############################################################################################################
def parseVideoXML(doc):
    """ Parse Video ID XML to get media url using regex """
    return searchRegEx(doc, '<media[_-]url>(.*?)</')        # _ or - depending on XML in use

##############################################################################################################
def parseVideoJSON(doc):
	""" Parse Video ID XML to get media url using regex """

	items = eval( doc.replace('null', '\"\"' ) )
	data = items.get('media_url','')
#	if DEBUG:
#		pprint (data)
	return data

##############################################################################################################
def deleteScriptCache(deleteAll=True):
	""" Delete script cache contents according to settings """
	debug("deleteScriptCache() deleteAll=%s" % deleteAll)
	if deleteAll:
		# delete all by removing cache dir
		from shutil import rmtree
		rmtree( DIR_CACHE, ignore_errors=True )
	else:
		# Delete videos and xml
		allFiles = os.listdir( DIR_CACHE )
		for f in allFiles:
			fn, ext = os.path.splitext(f)
			if ext in ('.mp4','.ts,','.flv','.xml','.json'):
				deleteFN = os.path.join(DIR_CACHE, f)
				deleteFile(deleteFN)

##############################################################################################################
##############################################################################################################
class ReeplayitSettings:
	""" Settings for reeplay.it, allows same file to be shared by script and plugin """

	SETTINGS_FILENAME = os.path.join( DIR_USERDATA, "settings.txt" )
	SETTING_USER = "user"
	SETTING_PWD = "pwd"
	SETTING_CHECK_UPDATE = "check_script_update_startup"
	SETTING_PAGE_SIZE = "page_size"
	SETTING_VQ = "video_quality"
	SETTING_CACHE_ACTION = "cache_action"
	SETTING_PLAY_MODE = "play_mode"

	SETTINGS_DEFAULTS = {
		SETTING_USER : "",
		SETTING_PWD : "",
		SETTING_CHECK_UPDATE : False,
		SETTING_PAGE_SIZE : 200,
		SETTING_VQ : False,					# False = high, True = med
		SETTING_CACHE_ACTION : False,			# False == All, True == Videos Only
		SETTING_PLAY_MODE : False				# False == Stream, True == Download
		}

	def __init__(self):
		self.debug("__init__")
		self.load()

	def debug(self, msg=""):
		debug("%s.%s" % (self.__class__.__name__, msg))

	def load(self):
		self.debug("load()")
		self.settings = loadFileObj( self.SETTINGS_FILENAME, {} )
		self.check()

	def save(self):
		self.debug("save()")
		saveFileObj(self.SETTINGS_FILENAME, self.settings)

	def check(self):
		self.debug("check()")
		# put default values into any settings that are missing
		changed = False
		for key, defaultValue in self.SETTINGS_DEFAULTS.items():
			if not self.settings.has_key( key ) or self.settings[key] in [None,""]:
				self.settings[key] = defaultValue
				changed = True
				debug("using default value for key=%s" % key)

		if changed:
			self.save()
		return changed

	def reset(self):
		self.debug("reset()")
		self.settings = {}
		self.check()

	def get(self, key):
		return self.settings.get(key, '')

	def set(self, key, value):
		self.debug("set() key=%s value=%s" % (key, value))
		self.settings[key] = value
		self.save()

	def getSettings(self):
		return self.settings

	def boolToggle(self, key):
		value = not self.get(key)	# toggle
		self.set(key,value)
		self.debug("boolToggle() key=%s newValue=%s" % (key,value))
		return value

	def makeMenu(self, singleString=True):
		self.debug("makeMenu() singleString=%s" % singleString)

		def _makeBool(key, opt, no="", yes=""):
			""" return a (key, li) tuple """
#			self.debug("_makeBool() key=%s" % (key))
			value = self.get(key)
			if not no: no = __lang__(201)
			if not yes: yes = __lang__(200)
			yesno = (no, yes)[value]		# translate to yes/no for true/false
			if singleString:
				lbl1 = "%s %s" % (opt, yesno)
				lbl2 = ""
			else:
				lbl1 = opt
				lbl2 = yesno
			return (key, value, lbl1, lbl2)

		def _makeOpt(key, opt, hidden=False):
			""" make a menu optino from a key and opt name """
#			self.debug("_makeOpt() key=%s" % (key))
			value = self.get(key)
			if hidden:
				displayValue = ""
				for i in range(len(value)):
					displayValue += "*"
			else:
				displayValue = value

			if singleString:
				lbl1 = "%s %s" % (opt, displayValue)
				lbl2 = ""
			else:
				lbl1 = opt
				lbl2 = displayValue
			return (key, value, lbl1, lbl2)

		# START MENU
		menu = [
			_makeOpt('exit', __lang__(203)), \
			_makeOpt('readme', __lang__(300)), \
			_makeOpt('changelog', __lang__(301))
			]

		# check for scrit update at startup
		menu.append( _makeBool(self.SETTING_CHECK_UPDATE, __lang__(302)) )

		# USER
		menu.append( _makeOpt(self.SETTING_USER, __lang__(303)) )

		# PWD
		menu.append( _makeOpt(self.SETTING_PWD, __lang__(304), True) )

		# PAGE SIZE
		menu.append( _makeOpt(self.SETTING_PAGE_SIZE, __lang__(305)) )

		# VIDEO QUALITY
		menu.append( _makeBool(self.SETTING_VQ, __lang__(306), __lang__(225), __lang__(226)) )

		# CACHE ON EXIT
		menu.append( _makeBool(self.SETTING_CACHE_ACTION, __lang__(307), __lang__(227), __lang__(228)) )

		# PLAYBACK MODE
		menu.append( _makeBool(self.SETTING_PLAY_MODE, __lang__(308), __lang__(231), __lang__(232)) )

		return menu


	#################################################################################################################
	def changeOption(self, optionData):
		self.debug("> changeOption()")

		reset = False
		newValue = None
		key, value, optName, optValue = optionData
		if key == 'readme':
			home_dir = os.path.join( "Q:"+os.sep, "scripts", __scriptname__ )
			fn = getReadmeFilename(home_dir)
			tbd = TextBoxDialogXML("DialogScriptInfo.xml", DIR_HOME, "Default")
			tbd.ask(optName, fn=fn)
			del tbd
		elif key == 'changelog':
			home_dir = os.path.join( "Q:"+os.sep, "scripts", __scriptname__ )
			fn = os.path.join( home_dir, "changelog.txt" )
			tbd = TextBoxDialogXML("DialogScriptInfo.xml", home_dir, "Default")
			tbd.ask(optName, fn=fn)
			del tbd
		elif key == self.SETTING_CHECK_UPDATE:
			newValue = self.boolToggle(key)
		elif key == self.SETTING_USER:
			result = doKeyboard(value, optName)
			if result and result != value:
				self.set(key, result)
				reset = True
		elif key == self.SETTING_PWD:
			result = doKeyboard(value, optName, KBTYPE_ALPHA, True)
			if result and result != value:
				self.set(key, result)
				reset = True
		elif key == self.SETTING_PAGE_SIZE:
			result = doKeyboard(str(value), optName, KBTYPE_NUMERIC)
			if result:
				result = int(result)
				if result != value:
					# ensure range limits
					if result < 5:
						result = 5
					elif result > 10000: # limited by available ram - much less on xbox
						result = 10000
					self.set(key, result)
					reset = True
		elif key == self.SETTING_VQ:
			# video quality
			newValue = self.boolToggle(key)
		elif key == self.SETTING_CACHE_ACTION:
			# cache action on exit
			self.boolToggle(key)
		elif key == self.SETTING_PLAY_MODE:
			# playback mode
			self.boolToggle(key)

		self.debug("< changeOption() reset=%s newValue=%s" % (reset, newValue))
		return reset, newValue
