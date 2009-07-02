#!/usr/bin/python
# encoding: utf-8
# -*- coding: utf-8 -*-
import re, sgmllib, urllib2, urllib, os.path, threading
from urllib2 import URLError
import xbmc, xbmcgui

try: Emulating = xbmcgui.Emulating
except: Emulating = False

# 2008-02-15 tweaks by voidberg

# done: larger thumbs
# done: browse into categories
# done: add hourglass or something when waiting on network (progressmeter, disabled in code)
# done: handle jpgs as well as gifs 
# done: fix icons not visible, add folder icon

# todo: start videoindex at right index, now starts at beginning. (Might work with newer xbmc)
# todo: return to parent category (add '..' on top of show list)
# todo: simple link to play full video even if it has indexes inside (add 'Vis hele' on top of the indexes)

# todo: proper unicode handling, must now encode all strings for display as iso-8859-1 
# todo: cache for session or for one hour
# todo: cache thumbs in regular cache


#Thanks Phunck :)
ScriptPath = os.getcwd()
if ScriptPath[-1]==';': ScriptPath=ScriptPath[0:-1]
if ScriptPath[-1]!='\\': ScriptPath=ScriptPath+'\\'

SPEEDS = ['300', '650', '900']
USE_CACHE = 0
USE_PROGRESS = 0

MAIN_URL = "http://www1.nrk.no/nett-tv/"
SHOW_URL = MAIN_URL + "prosjekt/"
MOVIE_URL = MAIN_URL + "klipp/"


###Preparing cookie handling:
try:
	import cookielib
except ImportError:
	xbmcgui.Dialog().ok("Upgrade needed!", "You need Python 2.4 for this script to work.\nPlease update XBMC!")
	print "You need Python 2.4 for this script to work. Please update XBMC!"
	
	
urlopen = urllib2.urlopen
Request = urllib2.Request
cj = cookielib.LWPCookieJar()

COOKIEFILE = ScriptPath + 'cookies.lwp'

if os.path.isfile(COOKIEFILE):
	cj.load(COOKIEFILE)

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
urllib2.install_opener(opener)


HTTP_TIMEOUT = 10.0

try:
	f= open(ScriptPath + 'speed.dat', 'r')
	SPEED = f.read()
	f.close()
except:
	SPEED = 3500


class Nrk:
	def __init__(self):
		pass

	def get_categories(self):
		data = fetch_data(MAIN_URL, 1)
		query = re.compile('<li><a href="/nett-tv/tema/(.*?)".*?title=".*?">(.*?)</a></li>')
		result = re.findall(query, data)
		container = [(MAIN_URL + 'bokstav/@', 'Alle')]
		for x in result:
			container.append((MAIN_URL + 'tema/' + x[0], x[1]))
		return container

	# find list of shows in category, return list with [title, id, detail, thumburl]	
	def list_programs(self, catnumber):
		data = fetch_data(str(catnumber), 1)
		query = re.compile('<div class="intro-element intro-element-small">.*?<h2>.*?<a href="/nett-tv/prosjekt/(.*?)".*?>(.*?)</a>.*?</h2>.*?<a href=.*?">(.*?)</a>', re.DOTALL | re.IGNORECASE)
		progdata = re.findall(query, data)
		programlist = []
		for program in progdata:
			query = re.compile('<a href="/nett-tv/prosjekt/'+program[0]+'" id=".*?" title=".*?" onclick=".*?">\s*<img src="(.*?)"', re.DOTALL | re.MULTILINE)
			imgdata = re.findall(query, data)
			if len(imgdata) < 1:
				imgsrc = None
			else:
				imgsrc = imgdata[0]
			programlist.append([program[1].encode('iso-8859-1', 'replace'), program[0], program[2].encode('iso-8859-1', 'replace'), imgsrc])
		return programlist
	
	
	# return list with [id, title, type(video|sound|folder), class(category|broadcast)]	
	def list_shows(self, url):
		data = fetch_data(url, 1)
		query = re.compile('<li class="(expand|noexpand)" id="\w+">\s*<a\s+(?:id="\w+"\s+)?href="/nett-tv/(\w+)/(\d+)"\s+(?:onclick=".*?"\s+)?title="(.*?)"\s+(?:onclick=".*?"\s+)?class="icon-(\w+)-', re.DOTALL)
		shows = re.findall(query, data)
		final_shows = []
		for x in shows:
			id = x[2]
			title = x[3].encode('iso-8859-1', 'replace')
			typ = x[4]
			if x[4] == 'videoindex': typ = 'video'
			if x[0] == 'expand': typ = 'folder'
			cat = x[1]
			final_shows.append((id, title, typ, cat))
		return final_shows

	def get_show(self, typ, id):
		data = fetch_data(MAIN_URL + typ + '/'+ str(id), 1)
		query = re.compile("var WM_url = '(.*?)'")		
		result = re.findall(query, data)
		urldata = fetch_data(str(result[0]), 0)
		#xbmcgui.Dialog().ok('GET_SHOW', str(urldata))
		query = re.compile(r'<ref href="(mms.*?)" />', re.DOTALL)
		#query = re.compile(r'<starttime value="(\d+)" />\s*.*\s*<ref href="(mms.*?)" />.*<title>(.*)</title>.*\s*<author>.*?</author>\s*<abstract>(.*?)</abstract>', re.DOTALL)
		videos = re.findall(query, urldata)
#		xbmcgui.Dialog().ok('GET_SHOW', videos[0][0])
#		xbmcgui.Dialog().ok('GET_SHOW', videos[0][1])
#		xbmcgui.Dialog().ok('GET_SHOW', videos[0][2])
#		xbmcgui.Dialog().ok('GET_SHOW', videos[0][3])
		return videos
		#return [videos[0][1], videos[0][2].encode('iso-8859-1', 'replace'), videos[0][3].encode('iso-8859-1', 'replace'), videos[0][0]]
	
	def set_speed(self, speed):
		fetch_data(MAIN_URL + 'hastighet.aspx?hastighet=' + str(speed) + '&retururl=http%3a%2f%2fwww1.nrk.no%2fnett-tv%2f', 0)
		



# read cached data if any available
# todo: deprecate old data! one hour?
def get_cache(url):
	try:
		key = get_cache_key(url)
		f = open(key, 'rb')
		data = f.read()
		f.close()
		return data
	except Exception, inst:
		#xbmcgui.Dialog().ok('CACHE GET ERROR', url, str(inst))
		pass
	return 

# write data to cache		
def put_cache(url, data):
	try:
		key = get_cache_key(url)
		f = open(key, 'wbo')
		f.write(data)
		f.close()
	except Exception, inst:
		#xbmcgui.Dialog().ok('CACHE PUT ERROR', url, str(inst), key)
		pass
	return

def get_cache_key(url):
	key = url
	key = key.replace(':', '')
	key = key.replace('/', '')
	key = key.replace('?', '')
	key = key.replace('&', '')
	key = key.replace('-', '')
	key = key.replace('+', '')
	key = key.replace('=', '')
	key = key.replace('%', '')
	key = key.replace('.', '')
	return ScriptPath + 'cache\\' + key

#Process parameter tells this function whether to return unicode or not.
def fetch_data(url, process):
	data = fetch_data_raw(url)
	if process == 1:
		udata = unicode(data, 'utf-8')
	else:
		udata = data
	del data
	return udata

def fetch_data_raw(url):
	if type(url) == list:
		link = url[0]
		txdata = url[1]
	else:
		txdata = None
		link = url
		if USE_CACHE == 1:
			data = get_cache(url)
			if data:
				return data

	if USE_PROGRESS == 1:
		progress = xbmcgui.DialogProgress()
		progress.create('Browsing', link)

	req = Request(link, txdata)
	
	def SubThreadProc(url, result):
		try:
			f = urlopen(req)
		except Exception, inst:
			result.append(-1)
		else:
			result.append(f)
			
	result = []    
	subThread = threading.Thread(target=SubThreadProc, args=(url, result))
	subThread.setDaemon(True)
	subThread.start()
	if USE_PROGRESS == 1: progress.update(33)
	subThread.join(HTTP_TIMEOUT)
	if USE_PROGRESS == 1: progress.update(66)
	if [] == result:
		xbmcgui.Dialog().ok('TIMEOUT','Failed to retrieve page', link)
		return ''
	elif -1 == result[0]:
		xbmcgui.Dialog().ok('ERROR','Failed to retrieve page', link)
		return ''
	else:
		f = result[0]
		data = f.read()
		if data == None:
			data = ''
		f.close()
		if len(data) < 100:
			xbmcgui.Dialog().ok('SIZE ERROR','Failed to retrieve page', link)    

	if USE_PROGRESS == 1: progress.update(100)
	if USE_CACHE == 1 and txdata == None: put_cache(url, data)
	if USE_PROGRESS == 1: progress.close()		
	return data


class Nrkplayer(xbmc.Player):
	starttime = None
	def __init__( self):
		xbmc.Player.__init__( self )
		self.starttime = 0
	def setStarttime(self, starttime):
		self.starttime = starttime
	def onPlayBackStarted(self):
		if self.starttime > 0:
			try:
				self.seekTime(double(self.starttime))
			except Exception, impl:
				xbmcgui.Dialog().ok('SEEK ERROR','Could not seek', str(impl))    


		
#BEGINNING OF GUI module


ACTION_MOVE_LEFT                             = 1    
ACTION_MOVE_RIGHT                            = 2
ACTION_MOVE_UP                            = 3
ACTION_MOVE_DOWN                            = 4
ACTION_PAGE_UP                            = 5
ACTION_PAGE_DOWN                            = 6
ACTION_SELECT_ITEM                        = 7
ACTION_HIGHLIGHT_ITEM                        = 8
ACTION_PARENT_DIR                            = 9
ACTION_PREVIOUS_MENU                        = 10
ACTION_SHOW_INFO                            = 11

ACTION_PAUSE                            = 12
ACTION_STOP                                = 13
ACTION_NEXT_ITEM                          = 14
ACTION_PREV_ITEM                            = 15

PICK_PROGRAM_STATE = 1
PICK_SHOW_STATE = 2

class NRKBrowser(xbmcgui.Window):
	#Initialize GUI
	def __init__(self):
		if Emulating: xbmcgui.Window.__init__(self)

	def initialize(self, nrkInstance):
		try: int(SPEED)
		except: self.askSpeed()
		self.speed = SPEED
		
		self.dialogProgress = xbmcgui.DialogProgress()
		self.nrk = nrkInstance
		self.setCoordinateResolution(6)
		self.nrk.set_speed(self.speed)

		
		#Adding objects
		self.addControl(xbmcgui.ControlImage(0,0, 720, 576, ScriptPath + 'gfx\\bg.png'))
		self.xbutton = xbmcgui.ControlImage(65, 480, 21, 21, ScriptPath + "gfx\\xbutton.png")
		self.addControl(self.xbutton)
		self.speedtext = xbmcgui.ControlLabel(89, 481, 200, 50, "Endre hastighet")
		self.addControl(self.speedtext)
		self.list = xbmcgui.ControlList(253, 50, 425, 350)
		self.catlist = xbmcgui.ControlList(50, 50, 200, 400)
		self.descbox = xbmcgui.ControlTextBox(263, 400, 290, 500)
		self.addControl(self.list)
		self.list.setImageDimensions(17,17)
		self.addControl(self.catlist)
		self.catlist.setPageControlVisible(0)
		self.addControl(self.descbox)
		self.descbox.setText(u"Velkommen til NRKBrowser2! Vennligst velg kategori pÃ¥ venstre side.\n\nGjeldende fart er " + str(self.speed) + "kbps")
		
		#Assigning behaviour
		self.list.controlLeft(self.catlist)
		self.catlist.controlLeft(self.list)
		self.catlist.controlRight(self.list)
		self.list.controlRight(self.catlist)
		self.setFocus(self.catlist)
		
		self.state = PICK_PROGRAM_STATE
		
		#Starting with adding the categories
		self.addCategories()

		
	def askSpeed(self):
		
		speedlist = []
		for x in SPEEDS:
			speedlist.append(x +' kbps')
		
		sel = xbmcgui.Dialog().select('Velg hastighet:' , speedlist)
		self.speed = str(SPEEDS[sel])
		f = open(ScriptPath + 'speed.dat', 'wbo')
		f.write(self.speed)
		f.close()
		self.descbox.setText(u"\n\n\nGjeldende fart er satt til " + str(self.speed) + "kbps")

	def addCategories(self):
		self.catdata = self.nrk.get_categories()
		for x in self.catdata:
			self.catlist.addItem(str(x[1].encode('iso-8859-1', 'replace')))
	
	def addPrograms(self):
		self.list.reset()
		for x in self.progdata:
			listitem = xbmcgui.ListItem(str(x[0]))
			listitem.setIconImage(ScriptPath + 'gfx\\folder.png')		
			listitem.setThumbnailImage(ScriptPath + 'gfx\\folder.png')		
			self.list.addItem(listitem)
		self.state = PICK_PROGRAM_STATE
	
	def addShows(self):
		self.list.reset()
		for x in self.showdata:
			try:
				listitem = xbmcgui.ListItem(str(x[1]))
				listitem.setIconImage(ScriptPath + 'gfx\\' + str(x[2]) + '.png')
				listitem.setThumbnailImage(ScriptPath + 'gfx\\' + str(x[2]) + '.png')
				self.list.addItem(listitem)
			except:
				pass
		self.state = PICK_SHOW_STATE

	def startShow(self, typ, id):
		self.nrk.set_speed(self.speed)
		video = self.nrk.get_show(typ, id)
		url = video[0]
		#xbmcgui.Dialog().ok('VIDEO', str(url))
		#title = video[1]
		#abstract = video[2]
		#starttime = video[3]

		listitem = xbmcgui.ListItem()
		#listitem.setInfo('video', {'title': url, 'Genre': abstract}) # not shown: tagline, artist, writer, label, label2
		#listitem.setInfo('video', {'title': title, 'Genre': abstract}) # not shown: tagline, artist, writer, label, label2

		#if starttime == "0":
		player = xbmc.Player()
		#else
			# this is not working... seekTime eventually hangs mplayer in my old xbmc. must upgrade to a post 2007-10-15 and see
			#player = Nrkplayer()
			#player.setStarttime(starttime)
		#	player = xbmc.Player()
		
		try:
			player.play(url, listitem)
		except Exception, impl:
			xbmcgui.Dialog().ok('Start show ERROR', str(impl))		
			
	def addImage(self, file):
		try:
			self.removeImage()
			del self.image
		except:
			pass
		#self.image = xbmcgui.ControlImage(553, 420, 200, 114, file)
		self.image = xbmcgui.ControlImage(475, 435, 200, 114, file)
		self.addControl(self.image)
		
	def removeImage(self):
		self.removeControl(self.image)
		del self.image
		
	def checkState(self):
		pos = self.list.getSelectedPosition()
		if self.state == PICK_PROGRAM_STATE:
			#xbmcgui.Dialog().ok("PROGRAM SELECTION", "Position " + str(pos), str(self.progdata[pos][1]) + ": " + self.progdata[pos][0])
			self.showdata = self.nrk.list_shows(str(SHOW_URL + str(self.progdata[pos][1])))
			self.descbox.setText(self.progdata[pos][2])
			self.imageurl = self.progdata[pos][3]
			try:
				bitmap = fetch_data(self.imageurl, 0)
				if len(bitmap) > 5:
					if str(bitmap).startswith('GIF'):
						ext = 'gif'
					else:
						ext = 'jpg'
					file = ScriptPath + 'gfx\\temp.' + ext
					#f = open(file, 'wbo')
					#f.write(bitmap)
					#f.close()
					self.addImage(file)
				self.addShows()
			except Exception, inst:
				xbmcgui.Dialog().ok('PROGRAM SELECTION', self.progdata[pos][1], 'Failed: ' + str(inst))
				pass

		elif self.state == PICK_SHOW_STATE:
			# May be a video or audio link, or a category
			#xbmcgui.Dialog().ok("Folder?", str(self.showdata[pos][2]))
			if self.showdata[pos][2] == 'folder':
				cat = self.showdata[pos][3]
				if cat == 'kategori': cat = 'category'
				else: cat = 'broadcast'
				url = MAIN_URL + 'menyfragment.aspx?type=' + cat + '&id=' + self.showdata[pos][0]
				self.showdata = self.nrk.list_shows(url)
				self.addShows()
			else:
				#xbmcgui.Dialog().ok("SHOW SELECTED", str(self.showdata[pos][0]), self.showdata[pos][3])
				self.startShow(self.showdata[pos][3], self.showdata[pos][0])
		
	def onAction(self, action):
		if action == ACTION_PREVIOUS_MENU:
			self.close()
		elif action == ACTION_PARENT_DIR:
			if self.state == PICK_SHOW_STATE:
				self.addPrograms()
				self.removeImage()
			elif self.state == PICK_PROGRAM_STATE:
				self.list.reset()
				self.setFocus(self.catlist)
		elif action == ACTION_MOVE_DOWN or action == ACTION_MOVE_UP or action == 111 or action == 112:
			try:
				if self.state == PICK_PROGRAM_STATE and self.getFocus() == self.list and self.list.getSelectedPosition() != -1:
					self.descbox.setText(self.progdata[self.list.getSelectedPosition()][2])
			except:
				pass
		elif action == 18:
			self.askSpeed()
				
	def onControl(self, control):
		if control == self.catlist:
			try:
				self.removeImage()
				self.descbox.setText('')
			except: pass
			self.progdata = self.nrk.list_programs(self.catdata[self.catlist.getSelectedPosition()][0])
			self.addPrograms()
		
		#List can either be in program state where the programs are shown, or in show state where the different programs' shows are shown. We check for this:
		if control == self.list:
			self.checkState()

nrk = Nrk()
w = NRKBrowser()
w.initialize(nrk)
w.doModal()
cj.save(COOKIEFILE)
del w
