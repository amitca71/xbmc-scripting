"""
	Category module: list of categories to use as folders
"""

# main imports
import os, sys
import time
#from pprint import pprint
from string import find
import xbmc, xbmcgui, xbmcplugin
from urllib import quote_plus, unquote_plus

from pluginAPI.xbmcplugin_const import *
from pluginAPI.bbbLib import *

__plugin__ = sys.modules[ "__main__" ].__plugin__
__lang__ = xbmc.Language( HOME_DIR ).getLocalizedString

#################################################################################################################
class _Info:
	def __init__(self, *args, **kwargs ):
		self.__dict__.update( kwargs )
		log( "Info() self.__dict__=%s" % self.__dict__ )
	def has_key(self, key):
		return self.__dict__.has_key(key)


#################################################################################################################
#################################################################################################################
class Main:
	# base paths

	def __init__( self ):
		self._parse_argv()                      # parse sys.argv

		if ( not sys.argv[ 2 ] ):
			# cleanup for new start
			for f in os.listdir(TEMP_DIR):
				if f.startswith(__plugin__):
#					print f
					deleteFile(os.path.join(TEMP_DIR, f))

			# start
			ok = self.get_categories( )
		else:
			exec "ok = self.%s()" % ( self.args.category, )

		xbmcplugin.endOfDirectory( handle=int( sys.argv[ 1 ] ), succeeded=ok)

	########################################################################################################################
	def _parse_argv(self):
		if ( not sys.argv[ 2 ] ):
			self.args = _Info( title="" )
		else:
			# call Info() with our formatted argv to create the self.args object
			# replace & with , first as they're the args split char.  Then decode.
			try:
				exec "self.args = _Info(%s)" % ( unquote_plus( sys.argv[ 2 ][ 1 : ].replace( "&", ", " ) ), )
			except:
				handleException("_parse_argv")

	########################################################################################################################
	def get_categories( self ):
		log( "> get_categories()")
		try:
			ok = True

			categories = (
					( __lang__( 30950 ), "fetch_rss", "movie/film", ),
					( __lang__( 30951 ), "fetch_rss", "movie/dvd", ),
					( __lang__( 30952 ), "fetch_rss", "music/album", ),
					( __lang__( 30953 ), "fetch_rss", "tv/show", ),
					( __lang__( 30954 ), "fetch_rss", "books/titles", ),
					( __lang__( 30955 ), "fetch_rss", "games/xbox360", ),
					( __lang__( 30956 ), "fetch_rss", "games/xbx", ),
					( __lang__( 30957 ), "fetch_rss", "games/wii", ),
					( __lang__( 30958 ), "fetch_rss", "games/cube", ),
					( __lang__( 30959 ), "fetch_rss", "games/ds", ),
					( __lang__( 30960 ), "fetch_rss", "games/gba", ),
					( __lang__( 30961 ), "fetch_rss", "games/ps3", ),
					( __lang__( 30962 ), "fetch_rss", "games/ps2", ),
					( __lang__( 30963 ), "fetch_rss", "games/psp", ),
					( __lang__( 30964 ), "fetch_rss", "games/pc", )
				)

			sz = len( categories )
			for ( ltitle, method, arg ) in categories:
				# set the callback url
				url = '%s?title=%s&category=%s' % ( sys.argv[ 0 ], encodeText( ltitle ), repr( method ), )
				if arg:
					url += "&arg=%s" % repr (arg )

				# only need to add label, icon and thumbnail, setInfo() and addSortMethod() takes care of label2
				li=xbmcgui.ListItem( ltitle )
				# add the item to the media list
				ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=url, listitem=li, isFolder=True, totalItems=sz )

			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_NONE )
			xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="files")
			xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=self.args.title )
		except:
			handleException("get_categories")
			ok = False

		log( "< get_categories() ok=%s" % ok)
		return ok


	########################################################################################################################
	def fetch_rss( self):
		log("> fetch_rss()")
		ok = False

		try:
			url = RSS_URL  % self.args.arg
			cat = self.args.arg.replace("/","_")
			title =  "RSS: " + self.args.title
			cat_fn = CAT_OBJ_FILENAME  % cat
			save = False

			# load existing parsed details obj file
			items = loadFileObj(cat_fn)
			if not items:
				items = []
				dialogProgress.create(__plugin__, "")

				# load existing rss file
				fn = CAT_RSS_FILENAME % cat
				doc = readFile(fn)
				if not doc:
					dialogProgress.update(0, __lang__(30921), title)
					doc = fetchURL(url, fn)
				if not doc: raise "empty"

				# parse rss - to get title, link, short desc, timestamp
				rssItems = self._parse_rss(doc)
				if rssItems:
					max_count = len(rssItems)
					for count, item in enumerate(rssItems):
						title, rssUrl, desc, timestamp = item
						percent = int( (count * 100.0) / max_count )
						dialogProgress.update(percent, __lang__(30920), title)
						details = self._fetch_item(title, rssUrl)
						if details:
							details['short_desc'] = desc
							details['timestamp'] = timestamp
							items.append( details )
				dialogProgress.close()
				if items:
					save = True

			if items:
				sz = len(items)
				icon = "DefaultFileBig.png"
				for idx, item in enumerate(items):
					# set the callback url
					desc =  item['short_desc']
					score_rated = color_score(item['score'])
						
#					date = time.strftime("%d-%m-%Y", time.localtime(item['timestamp']) )
					date = item['timestamp']	# as DD-MM-YYY
					thumb = item['photo_url']

					title_fmt = "%s  (%s)  [COLOR=66FFFFFF]%s[/COLOR]" % (item['title'], score_rated, desc)

					li_url = '%s?title=%s&category=%s&type=%s&data_idx=%s' % \
							( sys.argv[ 0 ], encodeText( item['title'] ), repr( 'show_item'), repr( cat ), repr( idx ), )

					# save generated thumb filename
					if not item.get('photo_fn',None):
						cacheFN = xbmc.getCacheThumbName( li_url )
						items[idx]['photo_fn'] = "/".join( [BASE_PLUGIN_THUMBNAIL_PATH, cacheFN[0], cacheFN] )
						save = True

					li=xbmcgui.ListItem( title_fmt,  desc, icon, thumb)
					li.setInfo("Video", {"Title" : title_fmt, "Tagline" : desc, "Plot" : desc, "PlotOutline" : desc, "Date" : date, "Genre": score_rated})
					# add the item to the media list
					ok = xbmcplugin.addDirectoryItem( handle=int( sys.argv[ 1 ] ), url=li_url, listitem=li, isFolder=False, totalItems=sz )

				# save all details to obj file
				if save:
#					pprint (items)
					saveFileObj(cat_fn, items)

			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_GENRE )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_DATE )
			xbmcplugin.addSortMethod( handle=int( sys.argv[ 1 ] ), sortMethod=xbmcplugin.SORT_METHOD_LABEL )
#			xbmcplugin.setContent( handle=int( sys.argv[ 1 ] ), content="files")
			xbmcplugin.setPluginCategory( handle=int( sys.argv[ 1 ] ), category=self.args.title )
		except "empty":
			messageOK(self.args.title, __lang__(30901), url)
		except:
			handleException("fetch_rss")
			ok = False

		log( "< fetch_rss() ok=%s" % ok)
		return ok

	########################################################################################################################
	def _parse_rss(self, data):
		log( "> _parse_rss()")
		items = []
		try:
			# use regex to parse feed
			regex = "<title>.*?CDATA\[(.*?)\]\]>.*?<link>(.*?)<.*?<description>.*?CDATA\[(.*?)\]\]>.*?<pubDate>(.*?)<"
			matches = findAllRegEx(data, regex)
			for match in matches:
#				secs = time.mktime( time.strptime(match[3][:-4], "%a, %d %b %Y %H:%M:%S") )	# remove end PDT etc
				date = time.strftime("%d-%m-%Y", time.strptime(match[3][:-4], "%a, %d %b %Y %H:%M:%S") )	# remove end PDT etc
				items.append( [match[0], match[1], match[2], date] )

			if not items:
				messageOK(__plugin__, __lang__(30902))
		except:
			handleException("_parse_rss")

#		print "parsed rss="
#		pprint (items)
		log( "< _parse_rss() count=%s" % len(items))
		return items

	########################################################################################################################
	def _fetch_item(self, title, rssUrl):
		"""  Fetch 'print' page that contains score  """
		log("> _fetch_item_details()")
		details = {}

		# create print page url from rss link
		basename = os.path.basename( rssUrl ).replace("?part=rss","")
		fn = ITEM_REVIEWS_FILENAME % basename
		printUrl = rssUrl.replace(".com/", ".com/print/").replace("?part=rss","")
		# get 'print' page
		doc = readFile(fn)
		if not doc:
			dialogProgress.update(0, __lang__(30921), title)
			doc = fetchURL(printUrl, fn)
		if doc:
			details['title'] = title
			details['rss_url'] = rssUrl
			details['print_url'] = printUrl
			details['print_fn'] = fn
			score = searchRegEx(doc, 'CLASS="metascore">(.*?)</')
			if not score: score = 0
			details['score'] = score
			details['photo_url'] = rssUrl.replace('.com','.com/media').replace('?part=rss','/picture.jpg')

#		print "details="
#		pprint (details)
		log("< _fetch_item()")
		return details

