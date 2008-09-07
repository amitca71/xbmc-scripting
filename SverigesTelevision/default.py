"""
 Copyright (c) 2007 Daniel Svensson

 Permission is hereby granted, free of charge, to any person
 obtaining a copy of this software and associated documentation
 files (the "Software"), to deal in the Software without
 restriction, including without limitation the rights to use,
 copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the
 Software is furnished to do so, subject to the following
 conditions:

 The above copyright notice and this permission notice shall be
 included in all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
 EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
 OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
 NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
 HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
 WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 OTHER DEALINGS IN THE SOFTWARE.
"""

import xbmcgui
import xbmc
import os
import sys
import traceback

from xbmcutils.net import DownloadAbort, DownloadError

import xbmcutils.gui

from SVT import SVTMedia, ParseError

class Logger:
	def write(data):
		xbmc.log(data)
	write = staticmethod(write)
sys.stdout = Logger
sys.stderr = Logger

class SVTGui(xbmcgui.WindowXML):
	CONTENT_LIST = 50
	ABOUT_BUTTON = 10
	SEARCH_BUTTON = 11

	def __init__(self, *args, **kwargs):
		self.stack = []
		self.data = []

		self.base_path = os.getcwd().replace(';','')

		self.svt = SVTMedia()

		self.player = xbmc.Player(xbmc.PLAYER_CORE_MPLAYER)

		self.stack.append(self.svt.get_start_url())

		self.inited = False

	def onInit(self):
		if not self.inited:
			try:
				self.list_contents(self.stack.pop())
				self.inited = True
			except:
				xbmc.log('Exception (init): ' + str(sys.exc_info()[0]))
				traceback.print_exc()
				self.close()

	def show_about(self):
		dlg = xbmcgui.Dialog()
		dlg.ok('Om', 'Av: Daniel Svensson, 2007',
		       'Paypal: dsvensson@gmail.com',
		       'Felrapporter: XBMC Forum - Python Script Development')

	def list_contents(self, url):
		data = self.download_data(url, self.svt.list_directory)
		if not self.populate_content_list(data):
			# Nothing to update.
			return False

		# Push directory to browsing stack
		self.stack.append(url)

		return True

	def search(self, term=None):
		if term is None:
			term = xbmcutils.gui.get_input('Search')

		# Only update the list if the user entered something.
		if term is None:
			return False

		data = self.download_data(term, self.svt.search)
		if not self.populate_content_list(data):
			return False

		# Dummy entry on the stack, search will only
		# return clips so no problemo.
		self.stack.append('search')

		return True

	def populate_content_list(self, data):
		if data is None:
			return False

		self.data = data

		list = self.getControl(SVTGui.CONTENT_LIST)

		xbmcgui.lock()
		list.reset()
		for desc, url, type in self.data:
			item = xbmcgui.ListItem (label=desc)
			if type is SVTMedia.DIR:
				item.setThumbnailImage('folder.png')
			elif type is SVTMedia.VIDEO:
				item.setThumbnailImage('video-x-generic.png')
			list.addItem(item)
		xbmcgui.unlock()

		return True

	def play_clip(self, url):
		file = self.download_data(url, self.svt.parse_video)
		if file is not None:
			self.player.play(str(file[0]))

	def update_progress(self, done, size, dlg):
		msg = 'Hamtar data (%dkB)' % int(done / 1024)
		percent = min(int((done * 100.0) / size), size)
		dlg.update(percent, msg)

		return not dlg.iscanceled()

	def download_data(self, url, func):
		data = None

		dlg = xbmcgui.DialogProgress()
		dlg.create('Sveriges Television', 'Hämtar data')

		self.svt.set_report_hook(self.update_progress, dlg)

		try:
			data = func(url)
		except ParseError, e:
			err_dlg = xbmcgui.Dialog()
			err_dlg.ok('Sveriges Television',
			           'Ett fel i programmet har påträffats.',
			           'Posta din XBMC\\xbmc.log på forumet.')
			print e
		except DownloadError, e:
			err_dlg = xbmcgui.Dialog()
			err_dlg.ok('Sveriges Television', 'Fel vid hämtning av data.')
			print e
		except DownloadAbort, e:
			pass

		dlg.close()

		return data

	def onFocus(self, control_id):
		pass

	def onClick(self, control_id):
		try:
			if control_id == SVTGui.CONTENT_LIST:
				list = self.getControl(SVTGui.CONTENT_LIST)
				pos = list.getSelectedPosition()
				desc, url, type = self.data[pos]
				if type is SVTMedia.DIR:
					self.list_contents(url)
				elif type is SVTMedia.VIDEO:
					self.play_clip(url)
			elif control_id is SVTGui.ABOUT_BUTTON:
				self.show_about()
			elif control_id is SVTGui.SEARCH_BUTTON:
				self.search()
		except:
			xbmc.log('Exception (onControl): ' + str(sys.exc_info()[0]))
			traceback.print_exc()
			self.close()

	def onAction(self, action):
		try:
			if action == xbmcutils.gui.ACTION_PREVIOUS_MENU:
				self.close()
			elif action == xbmcutils.gui.ACTION_PARENT_DIR and len(self.stack) > 1:
				cur = self.stack.pop()
				prev = self.stack.pop()
				if not self.list_contents(prev):
					# User aborted, still at the same ol' position.
					self.stack.append(prev)
					self.stack.append(cur)

		except:
			xbmc.log('Exception (onAction): ' + str(sys.exc_info()[0]))
			traceback.print_exc()
			self.close()


res_path = os.getcwd().replace(';','')
svt = SVTGui('main.xml', res_path)
svt.doModal()
del svt
