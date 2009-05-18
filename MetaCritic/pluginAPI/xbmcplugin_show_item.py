"""
	Category module: list of categories to use as folders
"""

# main imports
import os, sys
import xbmc, xbmcgui, xbmcplugin
from urllib import unquote_plus
#from pprint import pprint

from pluginAPI.xbmcplugin_const import *
from pluginAPI.bbbLib import *

__plugin__ = sys.modules[ "__main__" ].__plugin__
__lang__ = xbmc.Language( HOME_DIR ).getLocalizedString
  
#################################################################################################################
class DialogInfo( xbmcgui.WindowXMLDialog ):
	""" Show skin DialogInfo with our information """

	XML_FILENAME = "script-Metacritic-iteminfo.xml"
	EXIT_CODES = (9, 10, 216, 257, 275, 216, 61506, 61467,)
	
	def __init__( self, *args, **kwargs):
		pass
		
	def onInit( self ):
		log( "> DialogInfo.onInit()" )

		xbmcgui.lock()		

#		date = time.strftime("%d-%m-%Y", time.localtime(self.info['timestamp']) )
		img = xbmc.translatePath(self.info.get('photo_fn', ''))
		desc = decodeText(self.info.get('info4',''))
		info1 = self.info.get('info1',)
		if not info1:
			info1 = self.info.get('short_desc','')

		self.getControl( 4 ).setLabel( decodeText(self.info.get('title','')) )
		self.getControl( 5 ).setLabel( color_score(self.info['score']) )
		self.getControl( 6 ).setLabel( decodeText( self.info['timestamp'] ) )
		self.getControl( 7 ).setLabel( decodeText(info1) )
		self.getControl( 8 ).setLabel( decodeText(self.info.get('info2','')) )
		self.getControl( 9 ).setLabel( decodeText(self.info.get('info3','')) )
		if desc:
			self.getControl( 10 ).setText( desc )
		else:
			self.getControl( 10 ).setVisible(False)
		if img:
			self.getControl( 12 ).setImage( img )

		# reviews
		reviews = self.info.get('reviews',[])
		ctrl = self.getControl( 11 )
		if reviews:
			for who, score, desc in reviews:
				score_rated = color_score(score)
				label1 = "[COLOR=FFFFFFFF]%s[/COLOR] | %s" % (decodeText(who), decodeText(desc))
				ctrl.addItem(xbmcgui.ListItem(label1, score_rated))
		else:
			ctrl.setVisible(False)

		xbmcgui.unlock()		
		log( "< DialogInfo.onInit()" )

		
	def onClick( self, controlId ):
		pass

	def onFocus( self, controlId ):
		pass

	def onAction( self, action ):
		try:
			buttonCode =  action.getButtonCode()
			actionID   =  action.getId()
		except: return
		if actionID in self.EXIT_CODES or buttonCode in self.EXIT_CODES:
			self.close()

	def ask(self, info ):
#		pprint (info)
		self.info = info
		self.doModal()

#################################################################################################################
class _Info:
	def __init__(self, *args, **kwargs ):
		self.__dict__.update( kwargs )
		log( "_Info() self.__dict__=%s" % self.__dict__ )
	def has_key(self, key):
		return self.__dict__.has_key(key)


#################################################################################################################
#################################################################################################################
class Main:
	def __init__( self ):
		self._parse_argv()                      # parse sys.argv

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
	def show_item(self):
		log("> show_item()")
		ok = False

		try:
			type = self.args.type
			# load items file and get reqd item using dataIdx
			details = loadFileObj(CAT_OBJ_FILENAME  % type)[self.args.data_idx]
#			print "idx loaded details="
#			pprint (details)

			# load PRINT webpage (local or DL)
			print_fn = details['print_fn']
			doc = readFile(print_fn)
			if not doc:
				dialogProgress.create(__plugin__, __lang__(30921), details['title'])
				doc = fetchURL(details['print_url'], print_fn)
				dialogProgress.close()

			# if missing, get score
			if not details.has_key('score'):
				details['score'] = self._parse_score(doc)

			# parse all info section, according to category
			details['info1'] = ""								# starring / subtitle
			details['info2'] = ""								# written by
			details['info3'] = ""								# details 
			details['info4'] = ""								# film synopsis etc

			# process each page with one or more parsing
			if type.startswith('movie') or type.startswith('tv'):
				details = self._parse_film_infos(doc, details)
			elif type.startswith('music') or type.startswith('book') or type.startswith('game'):
				details = self._parse_music_infos(doc, details)

			if type.startswith('book'):
				details = self._parse_book_infos(doc, details)
			elif type.startswith('game'):
				details = self._parse_game_infos(doc, details)

			# parse reviews
			details = self._parse_reviews(doc, details)

			# PHOTO - will DL if not exist
			if not fileExist(details['photo_fn']):
				details['photo_fn'] = ''
#				fn = xbmc.translatePath(details['photo_fn'])
#				dialogProgress.create(__plugin__, __lang__(30921), details['title'], "picture.jpg")
#				if not fetchURL(details['photo_url'], fn, isBinary=True):
#					details['photo_fn'] = ''
#				dialogProgress.close()

#			print "final details="
#			pprint (details)

			# show item
			DialogInfo(DialogInfo.XML_FILENAME,HOME_DIR, "Default", False ).ask(details)
			ok = True
		except:
			handleException("show_item()")

		log("< show_item()  ok=%s" % ok)
		return ok

	########################################################################################################################
	def _parse_score(self, doc):
		score = searchRegEx(doc, 'CLASS="metascore">(\d+)</')
		if not score: score = 0
		return score

	########################################################################################################################
	def _parse_reviews(self, doc, details={}):
		log("> _parse_reviews()")

		# REVIEWS
		section = searchRegEx(doc, '>Critic Reviews(.*?)</TABLE')
		cleanlist = []
		for match in findAllRegEx(section, '<TD CLASS="(?:green|yellow|red)".*?>(.*?)</.*?publication">(.*?)</.*?>(.*?)<BR>(.*?)</TD>'):
			score = match[0].strip()
			who = match[1].strip()
			criticname = searchRegEx(match[2], 'criticname">(.*?)<').strip()	# may contain critic
			review = match[3].strip()
			if criticname:
				who += " (%s)" % criticname
			cleanlist.append( (who, score, review) )
		details['reviews'] = cleanlist

		log("< _parse_reviews()")
		return details

	########################################################################################################################
	def _parse_film_infos(self, doc, details={}):
		log("> _parse_film_infos()")

		# INFO 1
		# STARRING
		section = searchRegEx(doc, '<P>Starring(.*?)</P>')
		cleanlist = []
		for match in findAllRegEx(section, '<B>(.*?)<'):
			cleanlist.append(cleanHTML(match).replace("\n","").strip())
		if cleanlist:
			s = ",".join(cleanlist)
		else:
			s = cleanHTML(section)
		if s:
			details['info1'] = "Starring: %s" % s.replace("\n","").replace("    ","").strip()

		# INFO 2
		# DIRECTED
		section = searchRegEx(doc, '<P>DIRECTED BY(.*?)</P>')
		cleanlist = []
		for match in findAllRegEx(section, '<BR>(.*?)<'):
			cleanlist.append(cleanHTML(match).replace("\n","").strip())
		if cleanlist:
			s = ",".join(cleanlist)
		else:
			s = cleanHTML(section)
		if s:
			details['info2'] = "Directed By: %s  " % s.replace("\n","").replace("    ","").strip()

		# WRITTEN
		section = searchRegEx(doc, '<P>WRITTEN BY(.*?)</P>')
		cleanlist = []
		for match in findAllRegEx(section, '<BR>(.*?)<'):
			cleanlist.append(cleanHTML(match).replace("\n","").replace("\r","").strip())
		if cleanlist:
			s = ",".join(cleanlist)
		else:
			s = cleanHTML(section)
		if s:
			details['info2'] += "Written By: %s  " % s.replace("\n","").replace("    ","").strip()

		# INFO 3
		# details eg mpaa etc
		row = searchRegEx(doc, '<TABLE.*?<TR (.*?)</TR>')
		col = searchRegEx(row, '<TD.*?>(.*?)</TD>')

		# store cleaned items to list
		cleanlist = []
		for item in findAllRegEx(col, '>(.*?)<'):
			if item:
				clean = cleanHTML(item).replace("\n","").strip()
				if clean:
					cleanlist.append( clean )
		if cleanlist:
			s = "|".join(cleanlist[:-1])
		else:
			s = cleanHTML(col)
		if s and not s.startswith('Starring'):
			details['info3'] = s.replace("\n","").replace("    ","").strip()

		# INFO 4
		if cleanlist:
			details['info4'] = cleanlist[-1]		# synopsis

		log("< _parse_film_infos()")
		return details

	########################################################################################################################
	def _parse_music_infos(self, doc, details={}):
		log("> _parse_music_infos()")

		# INFO 1
		# SUBTITLE
		details['info1'] = searchRegEx(doc, 'CLASS="subtitle">(.*?)<')

		row = searchRegEx(doc, '<TABLE.*?<TR (.*?)</TR>')
		cols = findAllRegEx(row, '<TD.*?>(.*?)</TD>')

		# INFO 2 - COL 2
		# Album synopsis
		if len(cols) >= 2:
			cleanlist = []
			for item in findAllRegEx(cols[1], '>(.*?)<'):
				if item:
					clean = cleanHTML(item).replace("\n","").strip()
					if clean:
						cleanlist.append( clean )
			if cleanlist:
				s = "|".join(cleanlist)
			else:
				s = cleanHTML(cols[1])
			details['info2'] = s.replace("\n","").replace("    ","").strip()

		# INFO 3 - COl 1
		# details 
		if len(cols) >= 1:
			cleanlist = []
			for item in findAllRegEx(cols[0], '>(.*?)<'):
				if item:
					clean = cleanHTML(item).replace("\n","").strip()
					if clean:
						cleanlist.append( clean )
			if cleanlist:
				s = "|".join(cleanlist)
			else:
				s = cleanHTML(cols[0])
			details['info3'] = s.replace("\n","").replace("    ","").strip()

		log("< _parse_music_infos()")
		return details

	########################################################################################################################
	def _parse_book_infos(self, doc, details={}):
		log("> _parse_book_infos()")

		# INFO 4
		details['info4'] = searchRegEx(doc, '</TABLE>.*?<p>(.*?)</p>')

		log("< _parse_book_infos()")
		return details

	########################################################################################################################
	def _parse_game_infos(self, doc, details={}):
		log("> _parse_game_infos()")

		# INFO 4
		details['info4'] = details['info3']
		details['info3'] = ""

		log("< _parse_game_infos()")
		return details
