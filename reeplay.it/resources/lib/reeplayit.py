"""
	Support module for Reeplay.It script.
	Written by BigBellyBilly.
"""
import urllib2, sys, os, os.path
import cookielib, traceback
import xbmc, xbmcgui
import xbmcutils.net as net
from xml.sax.saxutils import unescape

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__title__ = "ReeplayitLib"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '25-01-2009'
xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)

DIR_HOME = sys.modules[ "__main__" ].DIR_HOME
DIR_CACHE = sys.modules[ "__main__" ].DIR_CACHE
try:
    __lang__ = sys.modules[ "__main__" ].__lang__
except:
    __lang__ = None
from bbbLib import *

class ReeplayitLib:
	""" Data gatherer / store for reeplay.it """

	def __init__(self, user, pwd, pageSize=100, vq=False):
		debug("ReeplayitLib() __init__ %s %s pageSize=%d vq=%s" % (user, pwd, pageSize, vq))

		self.user = user
		self.pageSize = pageSize
		self.setVideoProfile(vq)

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

		self.URL_PLAYLISTS = self.URL_BASE + "users/%s/playlists.xml"
		self.URL_PLAYLIST = self.URL_BASE + "users/%s/playlists/%s.xml?page=%s&page_size=%s"

		self.plsListItems = []
		self.videoListItems = []

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

			# if exist, load from cache
			xmlFN = os.path.join(DIR_CACHE, "playlists.xml")
			debug("xmlFN=" + xmlFN)
			data = readFile(xmlFN)
			if not data:
				# not in cache, download
				dialogProgress.create(__lang__(0), __lang__(215))
				self.set_report_hook(self.progressHandler, dialogProgress)
				data = self.retrieve(self.URL_PLAYLISTS % self.user)

			if data:
				rssItems = parsePlaylists(data)

				# load data into content list
				debug("storing xml items ...")
				for item in rssItems:
					id, plsName, desc, count, updatedDate = item
					title = "%s (%s)" % (plsName, count)
					li = xbmcgui.ListItem(title, desc)
					li.setProperty(self.PROP_ID, id)
					li.setProperty(self.PROP_COUNT, count)
					li.setInfo("File", {"Title" : title, "Size": int(count), \
										"Album" : desc, "Date" : updatedDate})
					self.plsListItems.append(li)

				del rssItems
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
		xmlFN = os.path.join(DIR_CACHE, "pls_%s_page_%d.xml" % (plsID, page))
		debug("xmlFN=" + xmlFN)
		data = readFile(xmlFN)
		if not data:
			# not cached, download
			url = self.URL_PLAYLIST % (self.user, plsID, page, self.pageSize)
			data = self.retrieve(url)
			saveData(data, xmlFN)

		if data:
			self.set_report_hook(None, None)
			dialogProgress.update(0, __lang__(210), "") # XML parsing
			rssItems = parsePlaylist(data)

			# load data into content list
			if rssItems:
				debug("storing xml items ...")
				dialogProgress.update(0, __lang__(210)) # + " (%d) % totalsize")
				defaultThumbImg = xbmc.makeLegalFilename(os.path.join(DIR_HOME, "default.tbn"))
				totalsize = len(rssItems)
				lastPercent = 0
				for itemCount, item in enumerate(rssItems):
					videoid, title, desc, captured, link, imgURL = item
					if not videoid:
						continue

					percent = int((itemCount * 100.0) / totalsize)
					if percent != lastPercent and percent % 5 == 0:
						lastPercent = percent
						countMsg = "(%d / %d)" % (itemCount+1, totalsize)
						dialogProgress.update(percent, __lang__(210), countMsg )
						if dialogProgress.iscanceled():
							debug("xml parsing cancelled")
							break

					# get thumb image
					imgName = videoid+".jpg"
					imgFN = xbmc.makeLegalFilename(os.path.join(DIR_CACHE, imgName))
					if not fileExist(imgFN):
						# download thumb image
#						dialogProgress.update(percent, __lang__(210), countMsg, imgName)
						data = self.retrieve(imgURL, fn=imgFN)
						if data == "": # aborted
							break
						elif not data:
							imgFN = defaultThumbImg

					li = xbmcgui.ListItem(title, desc, imgFN, imgFN)
					li.setProperty(self.PROP_ID, videoid)
					li.setProperty(self.PROP_URL, link)
					li.setInfo("video", {"Title" : title, "Date": captured})
					li.setProperty( "releasedate", captured )
					self.videoListItems.append(li)

				del rssItems

		dialogProgress.close()
		# delete file if failed to parse etc
		if not totalsize:
			deleteFile(xmlFN)

		debug("< getPlaylist() totalsize=%s" % totalsize)
		return totalsize

	##############################################################################################################
	def getVideo(self, idx, download=False):
		""" Download the selected video XML, then the video from media-url """
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
		xmlFN = os.path.join(DIR_CACHE, "%s_%s.xml" % (id, self.vqProfile))
		debug("xmlFN=" + xmlFN)
		data = readFile(xmlFN)
		if not data:
			# not cached, download
			data = self.retrieve(url)
			saveData(data, xmlFN)

		# parse video XML to get media-url
		if data:
			videoURL = parseVideo(data)
			debug("videoURL=" + videoURL)

			# download and save video from its unique media-url
			if not videoURL:
				messageOK(__lang__(0), "Media URL missing from XML!", title)
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
			deleteFile(xmlFN)

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
        print "saveData() exception=", sys.exc_info()
        return False


def parsePlaylists(xmlDoc):
	""" Parse Playlists xml using regex """
	data = []
	idList = findAllRegEx(xmlDoc, '<id.*?>(\d+)</')
	titleList = findAllRegEx(xmlDoc, '<title.*?>(.*?)</')
	descList = findAllRegEx(xmlDoc, '<description.*?>(.*?)</')
	countList = findAllRegEx(xmlDoc, '<contents-count.*?">(\d+)</')
	updatedList = findAllRegEx(xmlDoc, '<updated-at.*?>(\d\d\d\d-\d\d-\d\d)')
	itemCount = len(idList)
	debug("ParsePlaylists.itemCount=%d" % itemCount)
	for i in range(itemCount):
		data.append((idList[i], unescape(titleList[i]), unescape(descList[i]), countList[i], updatedList[i]))
	return data


def parsePlaylist(xmlDoc):
    """ Parse Playlist ID xml to get videos using regex """

    data = []
    videos = findAllRegEx(xmlDoc, '(<video uid.*?</video>)')
    debug("ParsePlaylist.itemCount=%d" % len(videos))
    for video in videos:
        data.append( ( searchRegEx(video, '<video uid.*?id="(\d+)"'), \
                    unescape(searchRegEx(video, '<title.*?>(.*?)</')), \
                    unescape(searchRegEx(video, '<description>(.*?)</')), \
                    searchRegEx(video, '<captured>(\d\d\d\d-\d\d-\d\d)'), \
                    searchRegEx(video, '<link>(.*?)</') + ".xml", \
                    searchRegEx(video, '<img.*?src="(.*?)"') ) )
    return data

def parseVideo(xmlDoc):
    """ Parse Video ID xml to get media url using regex """

    data = searchRegEx(xmlDoc, '<media[_-]url>(.*?)</')        # _ or - depending on XML in use
    return data

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