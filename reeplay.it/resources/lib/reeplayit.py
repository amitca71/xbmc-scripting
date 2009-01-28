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
__date__ = '28-01-2009'
xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)

DIR_HOME = sys.modules[ "__main__" ].DIR_HOME
DIR_CACHE = sys.modules[ "__main__" ].DIR_CACHE
try:
    __lang__ = sys.modules[ "__main__" ].__lang__
except:
    __lang__ = None
from bbbLib import *

DOC_EXT = "xml"		# xml or json

class ReeplayitLib:
	""" Data gatherer / store for reeplay.it """

	def __init__(self, user, pwd, pageSize=100, vq=False):
		debug("ReeplayitLib() __init__ %s %s pageSize=%d vq=%s" % (user, pwd, pageSize, vq))

		self.user = user
		self.pageSize = pageSize
		self.setVideoProfile(vq)
		
		DOC_EXT = "xml"       # json or xml

		self.PROP_ID = "ID"					# pls id
		self.PROP_COUNT = "COUNT"			# pls video count
		self.PROP_URL = "URL"				# video url
		self.URL_BASE = "http://staging.reeplay.it/"                    # LIVE is "http://reeplay.it/"

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
		debug("install_opener done")

		self.URL_PLAYLISTS = self.URL_BASE + "users/%s/playlists." + DOC_EXT
		self.URL_PLAYLIST = self.URL_BASE + "users/%s/playlists/%s."+DOC_EXT+"?page=%s&page_size=%s"

		self.plsListItems = []
		self.videoListItems = []
		self.defaultThumbImg = xbmc.makeLegalFilename(os.path.join(DIR_HOME, "default.tbn"))

	##############################################################################################################
	def setVideoProfile(self, vq):
		self.vqProfile = ( 'xbmc_high', 'xbmc_standard' )[vq]
		debug("setVideoProfile() %s" % self.vqProfile)

	##############################################################################################################
	def setPageSize(self, pageSize):
		self.pageSize = pageSize

	##############################################################################################################
	def retrieve(self, url, post=None, headers={}, fn=None):
		""" Downloads an url. Returns: None = error , '' = cancelled """
		debug("retrieve() %s" % url)
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
		debug("set_report_hook()")
		self.report_hook = func
		self.report_udata = udata

	##############################################################################################################
	def getPlaylists(self):
		debug("> getPlaylists()")

		if not self.plsListItems:

			dialogProgress.create(__lang__(0), __lang__(215))
			self.set_report_hook(self.progressHandler, dialogProgress)

			# if exist, load from cache
			playlistsURL = self.URL_PLAYLISTS % self.user
			docFN = os.path.join( DIR_CACHE, os.path.basename(playlistsURL) )
			debug("docFN=" + docFN)
			data = readFile(docFN)
			if not data:
				# not in cache, download
				data = self.retrieve(playlistsURL)

			if data:
				items = parsePlaylists(data)

				# load data into content list
				debug("storing data to listItems ...")
				for item in items:
					try:
						print item
						name, id, desc, count, updatedDate, imgURL = item

						# get thumb image
						imgName = os.path.basename(imgURL)
						imgFN = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, imgName))
						print "imgFN=" + imgFN
						if not fileExist(imgFN):
							data = self.retrieve(imgURL, fn=imgFN)
							if data == "": # aborted
								break
							elif not data:
								imgFN = self.defaultThumbImg

						title = "%s (%s)" % (name, count)
						li = xbmcgui.ListItem(title, desc, imgFN, imgFN)
						li.setProperty(self.PROP_ID, id)
						li.setProperty(self.PROP_COUNT, count)
						li.setInfo("File", {"Title" : name, "Size": int(count), \
											"Album" : desc, "Date" : updatedDate})
						self.plsListItems.append(li)
					except:
						traceback.print_exc()

				del items
				dialogProgress.close()

		count = len(self.plsListItems)
		debug("< getPlaylists() count=%s" % count)
		return count

	##############################################################################################################
	def getPlaylist(self, plsIdx, page=1):
		""" Download video list for playlist """
		debug("> getPlaylist() plsIdx=%s" % plsIdx)

		# reset stored videos
		self.videoListItems = []
		totalsize = 0

		# get selected playlist info
		li = self.getPlsLI(plsIdx)
		plsID = li.getProperty(self.PROP_ID)
		plsTitle = li.getLabel()
		debug("plsID=%s  plsTitle=%s" % (plsID, plsTitle))

		msg = "%s - %s %s" % (plsTitle, __lang__(219), page)
		dialogProgress.create(__lang__(0), __lang__(217), msg) # DL playlist content
		dialogProgress.update(0)
		self.set_report_hook(self.progressHandler, dialogProgress)

		# load cached file
		docFN = os.path.join(DIR_CACHE, "pls_%s_page_%d.%s" % (plsID, page, DOC_EXT))
		debug("docFN=" + docFN)
		data = readFile(docFN)
		if not data:
			# not cached, download
			url = self.URL_PLAYLIST % (self.user, plsID, page, self.pageSize)
			data = self.retrieve(url)
			saveData(data, docFN)

		if data:
			self.set_report_hook(None, None)
			dialogProgress.update(0, __lang__(210), "") # parsing
			items = parsePlaylist(data)

			# load data into content list
			if items:
				debug("storing items as listitems ...")
				totalsize = len(items)
				
				dialogProgress.update(0, __lang__(210)) # + " (%d) % totalsize")
				lastPercent = 0
				for itemCount, item in enumerate(items):
					try:
						title, videoid, captured, link, imgURL, duration = item
						if not videoid:
							continue

						percent = int((itemCount * 100.0) / totalsize)
						if percent != lastPercent and percent % 5 == 0:
							lastPercent = percent
							countMsg = "(%d / %d)" % (itemCount+1, totalsize)
							dialogProgress.update(percent, __lang__(210), countMsg )
							if dialogProgress.iscanceled():
								debug("parsing cancelled")
								break

						# get thumb image
						imgName = videoid+".jpg"
						print "imgName=", imgName
						imgFN = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, imgName))
						print "imgFN=" + imgFN
						if not fileExist(imgFN):
							data = self.retrieve(imgURL, fn=imgFN)
							if data == "": # aborted
								break
							elif not data:
								imgFN = self.defaultThumbImg

						li = xbmcgui.ListItem(title, "%smins" % duration, imgFN, imgFN)
						li.setProperty(self.PROP_ID, videoid)
						li.setProperty(self.PROP_URL, link)
						li.setInfo("video", {"Title" : title, "Date": captured, "Duration" : duration})
						self.videoListItems.append(li)
					except:
						traceback.print_exc()

				del items

		dialogProgress.close()
		# delete file if failed to parse etc
		if not totalsize:
			deleteFile(docFN)

		debug("< getPlaylist() totalsize=%s" % totalsize)
		return totalsize

	##############################################################################################################
	def getVideo(self, idx, download=False):
		""" Download the selected video info doc to get video url """
		debug("> getVideo() idx=%s download=%s" % (idx,download))
		fn = None

		# get LI info
		li = self.getVideoLI(idx)
		title = li.getLabel()
		id = li.getProperty(self.PROP_ID)
		url = li.getProperty(self.PROP_URL) + "?profile=" + self.vqProfile
		debug("id=%s url=%s" % (id, url))

		dialogProgress.create(__lang__(0), __lang__(222), title)
		dialogProgress.update(0)
		self.set_report_hook(self.progressHandler, dialogProgress)

		# if exist, load cached
		docFN = os.path.join(DIR_CACHE, "%s_%s.%s" % (id, self.vqProfile, DOC_EXT))
		debug("docFN=" + docFN)
		data = readFile(docFN)
		if not data:
			# not cached, download
			data = self.retrieve(url)
			saveData(data, docFN)

		# parse video info to get media-url
		if data:
			videoURL = parseVideo(data)
			debug("videoURL=" + videoURL)

			# download and save video from its unique media-url
			if not videoURL:
				messageOK(__lang__(0), "Media URL missing!", title)
			else:
				# download video to cache
				basename = os.path.basename(videoURL)
				videoName = "%s_%s%s" % (id, self.vqProfile, os.path.splitext(basename)[1])		# eg ".mp4"
				fn = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, videoName))
				debug( "video fn=" + fn )
				if not fileExist(fn):
					# if not in cache, do stream or download
					if download:
						dialogProgress.update(0,  __lang__(223), title, videoName)
						if not self.retrieve(videoURL, fn=fn):
							deleteFile(fn)	# delete incase of partial DL
							fn = ''
					else:
						# stream, so return url
						fn = videoURL

		dialogProgress.close()
		# delete file if failed to parse etc
		if not fn:
			deleteFile(docFN)

		debug("< getVideo() fn=%s li=%s" % (fn, li))
		return (fn, li)

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
def saveData(data, fn, mode="w"):
    """ Save data to a file """
    if not data or not fn or not mode: return False
    debug("saveData() fn=%s" % fn)
    try:
        f = open(fn, mode)
        f.write(data)
        f.flush()
        f.close()
        del f
        return True
    except:
        traceback.print_exc()
        return False


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
		data.append((unescape(titleList[i]), idList[i], unescape(descList[i]), countList[i], updatedList[i], imgList[i]))
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
						searchRegEx(video, '<captured>(\d\d\d\d.\d\d.\d\d)'), \
						searchRegEx(video, '<link>(.*?)</').strip() + ".xml", \
						searchRegEx(video, '<img.*?src="(.*?)"'), \
						int(searchRegEx(video, '<duration>(\d+)<')) ) )

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
						   item.get('id',''), \
						   unescape(item.get('description','')), \
						   item.get('contents_count',''), \
						   updated ) )
		print "unsorted json data=", data
		data.sort()
		print "sorted json data=", data

	except:
		traceback.print_exc()
		data = []
	if DEBUG:
		pprint (data)
	return data


##############################################################################################################
def parsePlaylistJSON(doc):
	""" Parse Playlist JSON to get videos using eval """
	debug("parsePlaylistJSON()")

	data = []
	try:
		# evals to [ {}, {}, .. ]
		items = eval( doc.replace('null', '\"\"' ) )
		# convert to [ [], [], .. ] as its easier to unpack without key knowlegde
		for item in items:
			link = item.get('link','')
			id = link[link.rfind('/'):]							# extract ID off end of link eg /1167
			try:
				captured = item.get('captured','')[:10]				# yyyy/mm/dd
			except:
				captured = ''
			data.append( (id, \
						   unescape(item.get('title','')), \
						   unescape(item.get('description','')), \
						   captured, \
						   link + ".json", \
						   item.get('img','')
						  ) )
	except:
		traceback.print_exc()
		data = []
	if DEBUG:
		pprint (data)
	return data


##############################################################################################################
def parsePlaylists(doc):
	""" Wrapper to call Playlists parsing """
	if DOC_EXT == "json":
		return parsePlaylistsJSON(doc)
	else:
		return parsePlaylistsXML(doc)

##############################################################################################################
def parsePlaylist(doc):
	""" Wrapper to call Playlist parsing """
	if DOC_EXT == "json":
		return parsePlaylistJSON(doc)
	else:
		return parsePlaylistXML(doc)

##############################################################################################################
def parseVideoXML(doc):
    """ Parse Video ID XML to get media url using regex """
    return searchRegEx(doc, '<media[_-]url>(.*?)</')        # _ or - depending on XML in use

##############################################################################################################
def parseVideo(doc):
	""" Wrapper to parse Video info doc  """
	if DOC_EXT == "json":
		return parseVideoJSON(doc)
	else:
		return parseVideoXML(doc)

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
			if ext in ('.mp4','.ts,','.flv','.xml'):
				deleteFN = os.path.join(DIR_CACHE, f)
				if not DEBUG:
					deleteFile(deleteFN)
				else:
					debug("DEBUG mode: File not deleted: " + deleteFN)
