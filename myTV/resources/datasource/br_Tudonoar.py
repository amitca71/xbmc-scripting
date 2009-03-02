############################################################################################################
# TV Data source: Brazil
#
# Notes:
# From http://tudonoar.uol.com.br/tudonoar/
#
#
# CHANGELOG
# ---------
# 13/01/06 Created.
# 10-03-2008 Updated for myTV v1.18
############################################################################################################

from mytvLib import *

import xbmcgui, re, time
from string import split, replace, find, rfind, atoi, zfill
from os import path

class ListingData:
	def __init__(self, cache):
		debug("ListingData.__init__")

# detalheCanal.aspx?IDcanal=131&amp;data=13/1/2006

		self.cache = cache
		self.name = os.path.splitext(os.path.basename( __file__))[0]	# get filename without path & ext
		self.BASE_URL = "http://tudonoar.uol.com.br/tudonoar/"
		self.channelListURL = self.BASE_URL + "gradeProgramacao.aspx"
		self.channelURL = self.BASE_URL + "detalheCanal.aspx?IDcanal=$CHID&data=$DATE"
		self.CHANNELS_FILENAME = os.path.join(cache,"Channels_"+ self.name + ".dat")

	def getName(self):
		return self.name

	# download or load if exists, a list of all available channels.
	# return: list [chID, chName]
	def getChannels(self):
		debug("ListingData.getChannels()")
		return getChannelsLIB(self.channelListURL, self.CHANNELS_FILENAME , \
							"IDcanal=(\d+)(?:.*?)>(.*?)<", startStr='Canais')


	# download channel data, using either dayDelta or dataDate.
	# filename = filename to save downloaded data file as.
	# chID = unique channel ID, used to reference channel in URL.
	# chName = display name of channel
	# dayDelta = day offset from today. ie 0 is today, 1 is tomorrow ...
	# fileDate = use to calc programme start time in secs since epoch.
	# return Channel class or -1 if http fetch error, or None for other
	#
	def getChannel(self, filename, chID, chName, dayDelta, fileDate):
		debug("ListingData.getChannel() dayDelta: %s chID=%s fileDate=%s" % (dayDelta,chID,fileDate))
		if dayDelta < 0:
			return []
		progList = []
		lastStartTime = 0 

		# download data file if file doesnt exists
		dataFilename = os.path.join(self.cache, "%s_%s.html" % (chID, fileDate))
		if not fileExist(dataFilename):
			formatTime = time.strptime(fileDate,"%Y%m%d")
			urlDate = time.strftime("%d/%m/%y", formatTime)
			url = self.channelURL.replace('$CHID',chID).replace('$DATE',urlDate)
			doc = fetchURL(url, dataFilename)
		else:
			doc = readFile(dataFilename)

		# check for timout, exception error, or empty page
		if not doc:
			return doc

		doc = doc.decode('latin-1','replace')
		debug("process data ...")
		# HH:MM, data -  which may/not contain href and name
		regex = ">(\d\d:\d\d)<(?:.*?)\">(.*?)</td"
		matches = parseDocList(doc, regex, 'tblProgramacao')
		if matches:
			for match in matches:
				startTime = match[0]
				link, title = extractURLName(match[1])	# extract link & name
				if not startTime or not title:
					continue

				if link:
					descLink = self.BASE_URL + link
				else:
					descLink = ''

				# convert starttime to secs since epoch
				secsEpoch = startTimeToSecs(lastStartTime, startTime, fileDate)
				lastStartTime = secsEpoch
				progList.append( {
						TVData.PROG_STARTTIME : float(secsEpoch),
						TVData.PROG_ENDTIME : 0,
						TVData.PROG_TITLE : decodeEntities(title),
						TVData.PROG_DESCLINK : descLink
					} )

			progList = setChannelEndTimes(progList)		# update endtimes

		return progList

	#
	# Download url and regex parse it to extract description.
	#
	def getLink(self, link, title):
		debug("> ListingData.getLink()")
		html = fetchURL(link)
		if not html:
			return ''

		# [regex, display text]
		searchData = [
			['Original\" class=\"textos\">(.*?)<', '\nTítulo Original: '],
			['Genero\" class=\"textos\">(.*?)<', 'Gênero: '],
			['Diretor_(?:.*?)>(.*?)<', 'Diretor: '],
			['Elenco_(?:.*?)>(.*?)<', 'Elenco: '],
			['SinopseSite\" class=\"textos\">(.*?)<', '\nSinopse: '],
			['Ano\" class=\"textos\">(.*?)<', '\nAno: '],
			['Origem\" class=\"textos\">(.*?)<', 'Origem: '],
			['Cor\" class=\"textos\">(.*?)<', 'Cor: ']
			]

		finalDesc = ''
		startStr = 'Título Original'
		endStr = 'tblProgramacao'
		for regex, displayText in searchData:
			# SEARCH for episode title
			matches = parseDocList(html, regex, startStr,endStr)
			count = 0
			for match in matches:
				detail = cleanHTML(decodeEntities(match))
				if detail:
					if count == 0:
						finalDesc += displayText + detail
					else:
						finalDesc += ',' + detail
					count += 1
			if count:
				finalDesc += '\n'

		debug("< ListingData.getLink()")
		return finalDesc.decode('utf8','replace')
