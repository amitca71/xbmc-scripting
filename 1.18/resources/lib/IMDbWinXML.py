"""

 Creates a window of IMDb information.

 ChangeLog:
 22/10/06 - Created.
 15/11/06 - tweaked
 24/01/07 - tweaked dialogSelect
 21/03/07 - Fixed due to site changes, also enhanced and rearranged.
 07/07/07 - Version that doesnt use latest bbbLib globals setup
 11/12/07 - tweaked layout
 21/01/08 - Uses DIR_IMDB_CACHE from USERDATA
 20/03/08 - Changed to use changed imdbLib gallery
 04/04/08 - Fix to use changed fetchURL() params
 04/06/08 - Converted to WindowXMLDialog
 27/08/08 - Fix cancel slideshow

"""

import sys,os,os.path, urlparse
import xbmc, xbmcgui

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__title__ = "IMDbWinXML"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '27-08-2008'
xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)

DIR_USERDATA = sys.modules[ "__main__" ].DIR_USERDATA           # should be in default.py
DIR_IMDB_CACHE = os.path.join(DIR_USERDATA, 'imdb')
DIR_GFX = sys.modules[ "__main__" ].DIR_GFX
__language__ = sys.modules[ "__main__" ].__language__

from IMDbLib import IMDb, IMDbSearch, IMDbGallery
from bbbLib import *
from bbbGUILib import *

#dialogProgress = xbmcgui.DialogProgress()
IMDB_LOGO_FILENAME = os.path.join(DIR_GFX, "imdb_logo.png")

#################################################################################################################
class IMDbWin(xbmcgui.WindowXMLDialog):
	# control id's
	CGRP_MAIN = 100
	CLBL_TITLE = 101
	CLBL_TITLETAG = 102
	CBTN_PHOTO_LEFT = 103
	CIMG_PHOTO = 104
	CBTN_PHOTO_RIGHT = 106
	CBTN_PHOTO_TITLE = 107
	CLBL_RATING = 110
	CLBL_DIRECTOR = 111
	CLBL_CREATOR = 112
	CLBL_WRITER = 113
	CLBL_RELEASED = 114
	CLBL_CERT = 115
	CLBL_RUNTIME = 116
	CLBL_SOUNDMIX = 117
	CLBL_ASPECT = 118
	CLBL_GENRE = 119
	CLBL_COUNTRY = 120
	CLBL_LANG = 121
	CLBL_SOUNDTRACK = 122
	CLBL_AWARD = 123
	CLBL_USERCOMMENT = 124
	CLBL_TRIVIA = 125
	CLBL_GOOF = 126
	CLST_CAST = 130
	CTB_DESC = 132	

	def __init__( self, *args, **kwargs ):
		debug("> IMDbWinXML()._init_")

		self.IMDB_PREFIX = 'imdb_'
		self.galleryIDX = 0
		self.galleryImgIDX = 0
		self.movie = None
		self.isStartup = True

		makeDir(DIR_IMDB_CACHE)

		debug("< IMDbWinXML()._init_")

	#################################################################################################################
	def onInit( self ):
		debug("> IMDbWinXML.onInit() isStartup=%s" % self.isStartup)
		if self.isStartup:
			self.isStartup = False
			self.setInfo()
			picCount = self.imdbGallery.getGalleryImageCount()
			if picCount:
				self.fetchImage()
			if picCount > 1:
				self.getControl(self.CBTN_PHOTO_TITLE).setLabel(__language__(989))
			else:
				self.getControl(self.CBTN_PHOTO_TITLE).setVisible(False)
				self.getControl(self.CBTN_PHOTO_LEFT).setVisible(False)
				self.getControl(self.CBTN_PHOTO_RIGHT).setVisible(False)

		debug("< IMDbWinXML.onInit()")

	################################################################################
	def onAction(self, action):
		try:
			actionID = action.getId()
			if not actionID:
				actionID = action.getButtonCode()
		except: return
		if actionID in CANCEL_DIALOG + EXIT_SCRIPT:
			removeDir(DIR_IMDB_CACHE, force=True)
			self.close()

	###############################################################################################################
	def onClick(self, controlID):
		if not controlID:
			return

		if controlID == self.CBTN_PHOTO_RIGHT:
			self.galleryImgIDX += 1
			# get next img in gallery or move to next gallery first image
			if self.galleryImgIDX >= self.imdbGallery.getGalleryImageCount():
				self.galleryImgIDX = 0
			self.fetchImage()
			self.setFocus(controlID)
		elif controlID == self.CBTN_PHOTO_LEFT:
			self.galleryImgIDX -= 1
			if self.galleryImgIDX < 0:
				self.galleryImgIDX = self.imdbGallery.getGalleryImageCount()-1
			self.fetchImage()
			self.setFocus(controlID)
		elif controlID == self.CBTN_PHOTO_TITLE:
			if self.slideshow():
				self.close()

	###################################################################################################################
	def onFocus(self, controlID):
		debug("onFocus(): controlID=%i" % controlID)
		self.controlID = controlID

	#################################################################################################
	def findTitle(self, title=''):
		debug("> findTitle()")
		url = None

		dialogProgress.create(__language__(982), title)
		imdbSearch = IMDbSearch(title)
		dialogProgress.close()
		if imdbSearch.SearchResults == None:
			messageOK("IMDb Error!","Failed to download web page for:", title)
		elif not imdbSearch.SearchResults:
			if xbmcgui.Dialog().yesno(__language__(980), title, __language__(984)):
				url = ''		# will cause manual entry
		else:
			# make menu list
			menu = [xbmcgui.ListItem(__language__(500),''), xbmcgui.ListItem(__language__(981),'')]
			for year, title, searchURL in imdbSearch.SearchResults:
				menu.append(xbmcgui.ListItem(title, year))

			# popup dialog to select choice
			selectDialog = DialogSelect()
			selectDialog.setup(__language__(985), width=600, rows=len(menu), banner=IMDB_LOGO_FILENAME)
			selectedPos,action = selectDialog.ask(menu)
			if selectedPos == 1:		# manual entry
				url = ''
			elif selectedPos > 1:		# title selected
				year, title, url = imdbSearch.SearchResults[selectedPos-2]	# allow for exit & Manual
#		else:
#			year, title, url = imdbSearch.SearchResults[0]

		if url:
			debug("call IMDB with url=" + url)
			dialogProgress.create(__language__(982),title + ' ' + year)
			self.movie = IMDb(url)
			if not self.movie:
				url = None		# failed to parse movie info
			dialogProgress.close()
		debug("< findTitle()")
		return url

	#################################################################################################
	# fetch & show image
	def fetchImage(self, url=''):
		debug("> fetchImage() " + url)
		exists = False
		imgTitle = ''
		fn = ''
		basename = ''

		if not url:
			debug("using galleryImgIDX=%s" % self.galleryImgIDX)
			imgTitle, url = self.imdbGallery.getThumb(self.galleryImgIDX)

		if url:
			fn, basename = self.makeThumbFilename(url)
			exists = fileExist(fn)
			if not exists:
				dialogProgress.create(__language__(986), basename)
				exists = fetchURL(url, fn, encodeURL=False, isBinary=True)
				dialogProgress.close()

		if exists:
			if not fn:
				fn = NOIMAGE_FILENAME
			self.getControl(self.CIMG_PHOTO).setImage(fn)

		debug("< fetchImage() exists=%s" % exists)
		return exists

	#################################################################################################
	def setInfo(self):
		debug("> setInfo()")
		xbmcgui.lock()

		labelData = [
			(self.CLBL_TITLETAG, self.movie.Tagline),
			(self.CLBL_RATING, self.movie.Rating),
			(self.CLBL_DIRECTOR, self.movie.Directors),
			(self.CLBL_CREATOR, self.movie.Creators),
			(self.CLBL_WRITER, self.movie.Writers),
			(self.CLBL_RELEASED, self.movie.ReleaseDate),
			(self.CLBL_CERT, self.movie.Certs),
			(self.CLBL_RUNTIME, self.movie.Runtime),
			(self.CLBL_SOUNDMIX, self.movie.SoundMix),
			(self.CLBL_ASPECT, self.movie.Aspect),
			(self.CLBL_GENRE, self.movie.Genres),
			(self.CLBL_COUNTRY, self.movie.Countries),
			(self.CLBL_LANG, self.movie.Languages),
			(self.CLBL_SOUNDTRACK, self.movie.Soundtrack),
			(self.CLBL_AWARD, self.movie.Awards),
			(self.CLBL_USERCOMMENT, self.movie.UserComment),
			(self.CLBL_TRIVIA, self.movie.Trivia),
			(self.CLBL_GOOF, self.movie.Goofs)
			]


		# TITLE
		title = self.movie.Title
		if self.movie.AKA:
			title += "(AKA: %s)" % self.movie.AKA 
		self.getControl(self.CLBL_TITLE).setLabel(decodeEntities(title))

		# SET INFO LABEL DATA
		for labelID, data in labelData:
			self.getControl(labelID).setLabel(decodeEntities(data))

		# PLOT TEXT BOX
		self.getControl(self.CTB_DESC).setText(decodeEntities(self.movie.PlotOutline))

		# CAST LIST
		try:
			for actor,role in self.movie.Cast:
				self.getControl(self.CLST_CAST).addItem(xbmcgui.ListItem(decodeEntities(actor), decodeEntities(role)))
		except:
			self.getControl(self.CLST_CAST).addItem('No Cast Details')

		xbmcgui.unlock()
		debug("< setInfo()")

	def slideshow(self):
		debug("> slideshow()")
		MAX = self.imdbGallery.getGalleryImageCount()
		if MAX:
			dialogProgress.create(__language__(988))
			for idx in range(MAX):
				pct = int(idx*100.0/MAX)

				small_url = self.imdbGallery.getThumbURL(idx)
				small_fn, small_basename = self.makeThumbFilename(small_url)
				large_fn = small_fn.replace(self.IMDB_PREFIX, self.IMDB_PREFIX + 'l_')
				large_url = self.imdbGallery.getLargeThumbURL(idx)
				dialogProgress.update(pct, "%s  (%s/%s)" % (os.path.basename(large_fn), idx, MAX))
				# try to get large image, but save using modified small filename
				if not fileExist(large_fn):
					result = fetchURL(large_url, large_fn, isBinary=True)
					if result == None:			# cancelled or error
						break
					elif result == False:
						# delete bad large_fn
						deleteFile(large_fn)
						debug("no large photo, get small photo")
						if not fileExist(small_fn):
							dialogProgress.update(pct, "%s  (%s/%s)" % (small_basename, idx, MAX))
							if fetchURL(small_url, small_fn, isBinary=True) == None:		# cancelled or error
								break
			dialogProgress.close()
			xbmc.executebuiltin('XBMC.SlideShow(%s)'% DIR_IMDB_CACHE)
		debug("< slideshow()")
		return MAX

	#######################################################################################################
	# attempt to make filename more unique by using some of its subfolder names from url
	# return full fn and basename
	#######################################################################################################
	def makeThumbFilename(self, url):
		split_info = urlparse.urlsplit(url)
		basename = split_info[2].replace('/media','').replace('/imdb','').replace('/','').replace('\\','').replace('_','')
		# restrict length
		l = len(basename)
		if l > 30:
			basename = basename[(l-30):]
		return xbmc.makeLegalFilename(os.path.join(DIR_IMDB_CACHE, self.IMDB_PREFIX + basename)), basename

	#######################################################################################################
	def ask(self, title=''):
		debug("> IMDbWinXML.ask()")
		url = ''
		# loop till we find a title or user quits manual entry
		while not url:
			if title:
				url = self.findTitle(title)

			if url == '':
				title = unicodeToAscii(doKeyboard(title, __language__(981)))
				if not title:
					break
			elif url == None:
				break

		if self.movie and url:
			dialogProgress.create(__language__(987))
			self.imdbGallery = IMDbGallery(url)
			dialogProgress.close()
			self.doModal()

		debug("< IMDbWinXML.ask()")
