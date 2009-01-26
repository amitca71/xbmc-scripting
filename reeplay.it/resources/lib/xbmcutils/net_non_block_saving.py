"""
 Copyright (c) 2007 Daniel Svensson, <dsvensson@gmail.com>

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

import urllib, urllib2
import traceback

from xml.sax.saxutils import unescape
from xml.sax.saxutils import escape

class AuthError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class DownloadError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)

class DownloadAbort(Exception):
	def __init__(self):
		self.value = 'Operation aborted'
	def __str__(self):
		return repr(self.value)

def retrieve(url, data=None, headers={}, rhook=None, rudata=None):
	"""Downloads an url."""

	if rhook is not None:
		rhook(0, -1, rudata)

	try:
		if data is not None:
			data = urllib.urlencode(data)
		req = urllib2.Request(unescape(url), data, headers)
		fp = urllib2.urlopen(req)
	except urllib2.HTTPError, e:
		print e
		code = e.code
		if code == 401:
			raise AuthError(code)
		else:
			raise DownloadError('%s' % e)
	except urllib2.URLError, e:
		print e
		raise DownloadError('%s' % e)
	except:
		raise DownloadError('%s' % traceback.print_exc())
	else:
		hdr = fp.info()
		print hdr
		size = int(hdr.get('Content-length', -1))
#		print "Download Content-length=%s" % size

		bs = max(int(size / 100.0), 1024)

		data = ''
		read = 0
		while True:
			block = fp.read(bs)
			if block in("", None):
				break
			read += len(block)
			data += block

			if rhook is not None:
				keep_going = rhook(read, size, rudata)
				if keep_going is not None and not keep_going:
					raise DownloadAbort()

		if size > 0 and read < size:
			msg = 'Download incomplete. Got only %d out of %d.' % (read, size)
			raise DownloadError(msg)

	if fp:
		fp.close()

	return data
