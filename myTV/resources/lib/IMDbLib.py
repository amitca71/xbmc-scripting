""" IMDbLib Movie Information Library:
Movie Information parsing from http://www.imdb.com

Originally Written By:
---------------------

No1CaNTeL
AllTheKillx

MODIFIED by BigBellyBilly AT gmail DOT com
-------------------------
Fixed and modified in several areas. NO NOT REPLACE THIS LIBRARY FILE
Changelog:
02/11/06 Change: IMDBSearch lookupstr to ensure it always replaces space with +
28/04/07 Fix: IMDb site changes and added extra tags.
05/06/07 Fix: Gallery regex
09/07/07 Fix: Seach for title. caused by site change
11/12/07 Fix: Scraping regex (see date comments)
18/01/08 Fix: regex for Cast
29/08/08 Fix: looks for Popular and Exact , Approx matches, fix unicode lookups
"""

import os,sys,re,urllib,string, urlparse,traceback,unicodedata
from string import find, translate

DEBUG = True
def log(s):
    if DEBUG:
        print s

fixReg = re.compile(r"&#[0-9]{1,3};")

reFlags = re.MULTILINE+re.IGNORECASE+re.DOTALL
# full page RE
titleReg        = '<title>(.*?)<'
taglineReg      = '>Tagline:<.*?>([^<]*)'									# 11/12/07
plotOutlineReg  = 'h5>Plot.*?:<.*?>(.*?)<'					                # 06/06/08
yearReg         = 'Sections/Years/.*?>(.*?)<'
ratingReg       = '<b>User Rating:</b>[^<]*<b>(.*?)<.*?">(.*?)<'			# 11/12/07
runtimeReg      = '>Runtime:<.*?>([^<]*)'									# 11/12/07
countriesReg    = '>Country:<.*?>([^<]*)</a'								# 11/12/07
languagesReg    = '>Language:<.*?>([^<]*)</a'								# 11/12/07
awardsReg       = '>Awards:<.*?>([^<]*)'									# 11/12/07
releaseDateReg  = '>Release Date:<.*?>(.*?)<'
userCommentReg  = '>User Comments:<.*?>(.*?)<'
akaReg          = '>Also Known As:<.*?>(.*?)<'
aspectReg       = '>Aspect Ratio:<.*?>(.*?)<'
triviaReg       = '>Trivia:<.*?>(.*?)</div'									# 11/12/07
goofsReg        = '>Goofs:<.*?>(.*?)</div'									# 11/12/07
soundtrackReg   = '>Soundtrack:<.*?>(.*?)</div'								# 11/12/07
soundMixReg     = '>Sound Mix:<.*?>(.*?)</div'								# 11/12/07
posterURLReg    = '"photo">.*?src="(.*?)" height="(\d+)" width="(\d+)"'
companyReg		= '"/company/[^/]*/">([^<]*)</a>'							# 11/12/07
genresReg       = re.compile(r'/Genres/.*?>(.*?)<', reFlags)
certsReg        = re.compile(r'certificates=.*?>(.*?)<', reFlags)

# per line RE
directorsReg   = re.compile(r'.*?Director:.*')
writersReg     = re.compile(r'.*?Writer.*')
castReg        = re.compile(r'.*?class="cast".*')
creatorsReg   = re.compile(r'.*?Creator.*')

in_directorsReg = re.compile(r'href="/name/.*?>(.*?)</')
in_writersReg   = re.compile(r'href="/name/.*?>(.*?)</')
in_castReg   = re.compile(r'href="/name/[nm0-9]*/">(.*?)<.*?(?:/character/|"char").*?>(.*?)(?:</a|</t)')	# 25/01/08
in_creatorsReg = re.compile(r'href="/name/.*?>(.*?)</')

# gallery RE
#galleriesRE = re.compile('href="photogallery(-.*?)"',reFlags)
#galleryRE = re.compile('<a href="/gallery.*? src="(.*?)".*?(?:width|height)="(\d+)".*?(?:width|height)="(\d+)".*?</a>',reFlags)
galleryThumbsRE = re.compile('img alt="(.*?)".*?src="(.*?)"') # 18/03/08
galleryPageCountRE = re.compile(r'page=(\d+)', reFlags)


class IMDb:
	def __init__(self,url):
		log("IMDb()")

		NA = 'N/A'
		self.Title           = NA
		self.Tagline         = NA
		self.PlotOutline     = NA
		self.Year            = NA
		self.Rating          = NA
		self.Runtime         = NA
		self.Countries       = NA
		self.Languages       = NA
		self.Awards          = NA
		self.ReleaseDate     = NA
		self.UserComment     = NA
		self.AKA             = ''
		self.Aspect          = NA
		self.Trivia          = NA
		self.Goofs           = NA
		self.Soundtrack      = NA
		self.SoundMix        = NA
		self.PosterURL      = None
		self.Cast            = []
		self.Certs            = NA
		self.Creators         = NA
		self.Writers         = NA
		self.Directors		= NA
		self.Genres          = NA

		page = readPage(url)
		if not page:
			return

		# FUL PAGE REGEX
		log("do full page regex searches ...")
		matches = re.search(titleReg, page, reFlags)
		if matches:
			self.Title = clean(matches.group(1))

		# TAGLINE
		matches = re.search(taglineReg, page, reFlags)
		if matches:
			self.Tagline = clean(matches.group(1))

		# YEARS
		matches = re.search(yearReg, page, reFlags)
		if matches:
			self.Year = clean(matches.group(1))

		# PLOT SUMMARY
		matches = re.search(plotOutlineReg, page, reFlags)
		if matches:
			self.PlotOutline = clean(matches.group(1)).replace('full summary','')

		# RATING
		matches = re.search(ratingReg, page, reFlags)
		if matches:
			self.Rating = "%s %s" % (matches.group(1).strip(), matches.group(2).strip())

		# RUNTIME
		matches = re.search(runtimeReg, page, reFlags)
		if matches:
			self.Runtime = clean(matches.group(1))

		# COUNTRY
		matches = re.search(countriesReg, page, reFlags)
		if matches:
			self.Countries = clean(matches.group(1))

		# LANG
		matches = re.search(languagesReg, page, reFlags)
		if matches:
			self.Languages = clean(matches.group(1))

		# AWARDS
		matches = re.search(awardsReg, page, reFlags)
		if matches:
			self.Awards = clean(matches.group(1)).replace('more','')

		# RELEASE DATE
		matches = re.search(releaseDateReg, page, reFlags)
		if matches:
			self.ReleaseDate = clean(matches.group(1))

		# USER COMMENT
		matches = re.search(userCommentReg, page, reFlags)
		if matches:
			self.UserComment = clean(matches.group(1)).replace('more','')

		# AKA
		matches = re.search(akaReg, page, reFlags)
		if matches:
			self.AKA = clean(matches.group(1))

		# ASPECT
		matches = re.search(aspectReg, page, reFlags)
		if matches:
			self.Aspect = clean(matches.group(1))

		# TRIVIA
		matches = re.search(triviaReg, page, reFlags)
		if matches:
			self.Trivia = clean(matches.group(1)).replace('more','')

		# GOOFS
		matches = re.search(goofsReg, page, reFlags)
		if matches:
			self.Goofs = clean(matches.group(1)).replace('more','')

		# SOUNDTRACK
		matches = re.search(soundtrackReg, page, reFlags)
		if matches:
			self.Soundtrack = clean(matches.group(1)).replace('more','')

		# SOUNDMIX
		matches = re.search(soundMixReg, page, reFlags)
		if matches:
			self.SoundMix = clean(matches.group(1)).replace('more','')

		# POSTER PHOTO
		matches = re.search(posterURLReg, page, reFlags)
		if matches:
			self.PosterURL = clean(matches.group(1))

		# GENRES
		matches = genresReg.findall(page)
		if matches:
			self.Genres = ','.join(matches)

		# CERTS
		matches = certsReg.findall(page)
		if matches:
			self.Certs = ','.join(matches)

		log("do pre line regex searches ...")
		pageLines = page.split('\n')
		i = 0
		while i < len(pageLines):
			if directorsReg.match(pageLines[i]):
				i += 1
				matches = in_directorsReg.findall(pageLines[i])
				if matches:
					self.Directors = clean(','.join(matches))

			elif writersReg.match(pageLines[i]):
				i += 1
				matches = in_writersReg.findall(pageLines[i])
				if matches:
					self.Writers = clean(','.join(matches))

			elif castReg.match(pageLines[i]):
				matches = in_castReg.findall(pageLines[i])
				for actor,role in matches:
					self.Cast.append([clean(actor), clean(role)])

			if creatorsReg.match(pageLines[i]):
				i += 1
				matches = in_creatorsReg.findall(pageLines[i])
				if matches:
					self.Creators = clean(','.join(matches))

			i+=1

		if DEBUG:	# switch on for debug results
			print "Title            =%s" %  self.Title
			print "Tagline          =%s" %  self.Tagline   
			print "PlotOutline      =%s" %  self.PlotOutline
			print "Year             =%s" %  self.Year
			print "Rating           =%s" %  self.Rating
			print "Runtime          =%s" %  self.Runtime
			print "Countries        =%s" %  self.Countries
			print "Languages        =%s" %  self.Languages
			print "Awards           =%s" %  self.Awards
			print "ReleaseDate      =%s" %  self.ReleaseDate
			print "UserComment      =%s" %  self.UserComment
			print "AKA              =%s" %  self.AKA
			print "Aspect           =%s" %  self.Aspect
			print "Trivia           =%s" %  self.Trivia
			print "Goofs            =%s" %  self.Goofs
			print "Soundtrack       =%s" %  self.Soundtrack
			print "SoundMix         =%s" %  self.SoundMix
			print "PosterURL        =%s" %  self.PosterURL
			print "Certs            =%s" %  self.Certs
			print "Creators         =%s" %  self.Creators
			print "Writers          =%s" %  self.Writers
			print "Directors        =%s" %  self.Directors
			print "Genres           =%s" %  self.Genres
			print "Cast             =%s" %  self.Cast


###########################################################################################################
class IMDbSearch:
	def __init__(self, findStr):
		log("IMDbSearch()")
		self.YEAR = 0
		self.TITLE = 1
		self.URL = 2
		try:
			trantab = string.maketrans('','')
			lookupStr = findStr.strip().translate(trantab,'~!@#$%^&*()_+`-={}|[]\:";\'<>?,./').replace(' ','+')
		except:
			try:
				lookupStr = findStr.replace(' ','+')
			except:
				lookupStr = findStr
				log( "lookupStr assigned" )

		self.SearchResults = None
#		url = 'http://www.imdb.com/find?s=tt&q='
		url = 'http://www.imdb.com/find?s=tt&q=' + lookupStr
#		if isinstance(lookupStr,unicode):
#			try:
#				url += lookupStr.encode('latin-1')
#			except:
#				url += lookupStr
#		else:
#			url += lookupStr

		page = readPage(url)
		if not page:
			return
		self.SearchResults = []

		if string.find(page, 'No Matches') != -1:
			log( "found 'No Matches'" )
		elif string.find(page, '>Popular') != -1 or string.find(page, 'Exact Matches') != -1 \
			  or string.find(page, 'Approx Matches') != -1:
			log( "found 'Popular' and/or 'Exact' or 'Approx' matches" )
			# title code, title, year
			search = re.compile('href="/title/([t0-9]*)/">(.*?)</a> *\(([0-9]*)')		# updated 11/12/2007
			matches = search.findall(page)
			if matches:
				for a in matches:
					url = "http://www.imdb.com/title/%s/" % (a[0])
					title = urlTextToASCII(a[1])
					year = a[2]
					self.SearchResults.append((year, title, url))

				# sort resul tuple into year reverse order
				if self.SearchResults:
					self.SearchResults.sort()
					self.SearchResults.reverse()
			else:
				log( "no matches on page" )
		elif string.find(page, '<h1>'+findStr) or string.find(page, '>User Rating:<'):
			log("exact match")
			search = re.compile('/Years/([0-9]*).*?/title/([t0-9]*)/', re.DOTALL + re.MULTILINE + re.IGNORECASE)
			matches = search.findall(page)
			if matches:
				year = matches[0][0]
				url = "http://www.imdb.com/title/%s/" % (matches[0][1])
				self.SearchResults.append((year, findStr, url))
			else:
				log( "no matches on page" )
		else:
			log( "search 'Years'" )
			search = re.compile('/Years/([0-9]*)\".*?/title/([t0-9]*)/', re.DOTALL + re.MULTILINE + re.IGNORECASE)
			matches = search.findall(page)
			if matches:
				year = matches[0][0]
				url = "http://www.imdb.com/title/%s/" % (matches[0][1])
				self.SearchResults.append((year, findStr, url))
			else:
				log( "no matches on page" )

	def getSearchResults(self):
		return self.SearchResults
	def getSearchResult(self, idx):
		try:
			return self.SearchResults[idx]
		except:
			return None
	def getTitle(self, idx):
		self.SearchResults[idx][self.TITLE]
	def getURL(self, idx):
		self.SearchResults[idx][self.URL]
	def getYear(self, idx):
		self.SearchResults[idx][self.YEAR]


###########################################################################################################
# http://www.imdb.com/title/tt0076759/mediaindex
###########################################################################################################
class IMDbGallery:
	def __init__(self, url):

		if url[-1] != '/': url += '/'
		self.baseURL = url + 'mediaindex'
		log("IMDbGallery() " + self.baseURL)

		self.galleyThumbs = []	# [[url title], [url title], ... ]
		self.pageCount = 1

		page = readPage(self.baseURL)
		if not page:
			return

		# how many pages ?
		matches = galleryPageCountRE.findall(page)
		if matches:
			# finds them twice, so half the count
			self.pageCount = int(len(matches) /2)
		else:
			self.pageCount = 1
		log("pageCount=%s" % self.pageCount)

		# get thumb urls from each page
		for pageIdx in range(1, self.pageCount+1):
			log("fetching pageIdx=%s" % pageIdx)
			if pageIdx > 1:
				url = self.baseURL + '?page=%s' % pageIdx
				urlList = self.getGalleryThumbs(url)
			else:
				urlList = self.getGalleryThumbs(doc=page)
			if urlList:
				self.galleyThumbs += urlList

#		print self.galleyThumbs
		log("galleyThumbs count=%s" % len(self.galleyThumbs))

	# GET GALLERY THUMB IMAGES
	def getGalleryThumbs(self, url='', doc=''):
		if url:
			doc = readPage(url)
		if doc:
			return galleryThumbsRE.findall(doc)
		return None

	def getGalleryImageCount(self):
		return len(self.galleyThumbs)

	def getThumb(self, idx):
		try:
			return self.galleyThumbs[idx]
		except:
			return ('','')

	def getThumbTitle(self, idx):
		try:
			return self.getThumb(idx)[0]
		except:
			return ''

	def getThumbURL(self, idx):
		try:
			return self.getThumb(idx)[1]
		except:
			return ''

	def getLargeThumbURL(self, idx):
		url = self.getThumbURL(idx)
#		url_info = urlparse.urlsplit(url)		# ( )
#		print url_info
#		urlpath = urlparse.urlsplit(url)[2]		# dir/dir/dir/name.ext
#		head, tail = os.path.split(urlpath)		# dir/dir/dir/, name.ext
#		name, ext = os.path.splitext(tail)		# name, ext
#		url = "%s://%s%s" % (url_info[0],url_info[1], head + '/VM._SY400_SX600_' + ext)

		head, tail = os.path.split(url)
		name, ext = os.path.splitext(tail)

		# try  reg repl of known fn format -
		# eg /VM._CR0,0,255,255_SS80_.jpg   -> /VM._SY400_SX600_.jpg
		# eg. _V1._CR0,0,216,216_SS80_.jpg  -> _V1._SY400_SX600_.jpg
		result = re.sub(r"CR\d+,\d+,\d+,\d+_.*?_", 'SY400_SX600_', name)
		if result != name:			# if sub done OK, will be diff
			# re matched and replaced
			url = head + '/' + result + ext
		else:
			# normal replace which works most of the time
			url = head + '/VM._SY400_SX600_' + ext
		log("getLargeThumbURL() " + url)
		return url

###########################################################################################################
def readPage(url, readLines=False):
	log("readPage() readLines=%s" % readLines)
	page = None
	try:
		sock = urllib.urlopen(urllib.quote_plus(url,'/:&?=+#@'))
		if not readLines:
			page = sock.read()
		else:
			page = sock.readlines()
		sock.close()
		if not page:
			log("page not found")
	except:
		log("urlopen() except")
		e=sys.exc_info()
		print traceback.format_exception(e[0],e[1],e[2],3)
		page = None
	return page

###########################################################################################################
def clean(text):
	return urlTextToASCII(cleanHTML(text)).strip()


###########################################################################################################
def cleanHTML(data):
	try:
		reobj = re.compile('<.+?>', re.IGNORECASE+re.DOTALL+re.MULTILINE)
		return (re.sub(reobj, '', data)).strip()
	except:
		return data

###########################################################################################################
def urlTextToASCII(text):
	try:
		compile_obj = re.compile('(&#x(.*?);)',  re.IGNORECASE + re.MULTILINE + re.DOTALL)
		match_obj = compile_obj.findall(text)
		for match in match_obj:
			ch = chr(int('0x'+match[1], 16))
			text = text.replace(match[0], ch)

		compile_obj = re.compile('(&#(\d+);)',  re.IGNORECASE + re.MULTILINE + re.DOTALL)
		match_obj = compile_obj.findall(text)
		for match in match_obj:
			ch = chr(int(match[1]))
			text = text.replace(match[0], ch)

		text = text.replace('&amp;','&').replace('\n',' ').replace('\r',' ').replace('\t',' ')

		compile_obj = re.compile('(&(.*?);)', re.IGNORECASE+re.DOTALL+re.MULTILINE)
		text = (re.sub(compile_obj, '', text))

	except: pass
	return text
