# T3CH Upgrader - Update your current T3CH Build to latest release.
#
# Process:
# Find & DL & unrar new build (keeping T3CH build name)
# Copies your UserData, preserving keymap.xml (if reqd).
# Create a dash boot shortcut cfg that points to new build path.
# Copies your scripts (preserving new build scripts).
# Reboots (if reqd).
#
# Included is an autoexec.py
# When installed to Q:\scripts it will run this script in 'SILENT' or 'NOTIFY' mode
#
# Many Thanks to Team AMT for code used.
#
import sys
import os
import xbmc
import xbmcgui
import urllib
from sgmllib import SGMLParser
import traceback
from string import lower, capwords
from shutil import copytree, rmtree, copy
import filecmp
import time
import re
import zipfile

# Script constants
__scriptname__ = "T3CH Upgrader"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__url__ = "http://code.google.com/p/xbmc-scripting/"
__svn_url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/T3CH%20Upgrader"
__date__ = '26-08-2008'
__version__ = "1.7.2"
xbmc.output( __scriptname__ + " Version: " + __version__  + " Date: " + __date__)

# Shared resources
DIR_HOME = os.path.join( os.getcwd().replace( ";", "" ) )
DIR_RESOURCES = os.path.join( DIR_HOME, "resources")
DIR_LIB = os.path.join( DIR_RESOURCES, "lib")
sys.path.append( DIR_RESOURCES )
sys.path.append( DIR_LIB )

import language
mylanguage = language.Language()
__language__ = mylanguage.localized
import update
import zipstream
import SFVCheck

dialogProgress = xbmcgui.DialogProgress()

EXIT_SCRIPT = ( 9, 10, 247, 275, 61467, )
CANCEL_DIALOG = EXIT_SCRIPT + ( 216, 257, 61448, )
TEXTBOX_XML_FILENAME = "script-bbb-textbox.xml"

class Parser( SGMLParser ):
	def reset( self ):
		self.url = None
		SGMLParser.reset( self )

	def start_a( self, attrs ):
		for key, value in attrs:
			if ( key == "href" and value.find( "/STABLE/" ) == -1 and value.find( "ARCHIVE/" ) == -1 
				and value.find( "/t3ch/XBMC-SVN" ) != -1 and value.find( ".rar" ) != -1 ):
				self.url = value

#############################################################################################################
class Main:
	def __init__( self, runMode ):
		xbmc.output("> __init__()")

		self.runMode = runMode
		xbmc.output("runMode=" + str(runMode))
		self.isSilent = (runMode != RUNMODE_NORMAL)
		xbmc.output("isSilent=" + str(self.isSilent))

		self.HOME_URL_LIST = ("http://217.118.215.116/", "http://t3ch.yi.se/")
		self.FTP_URL_LIST = ("http://ftp1.srv.endpoint.nu/", "http://ftp3.srv.endpoint.nu/")
		self.FTP_REPOSITORY_URL = "pub/repository/t3ch/"
		self.FTP_REPOSITORY_ARCHIVE_URL = self.FTP_REPOSITORY_URL + "ARCHIVE/"

		self.isPartialDownload = False		# indicate that last download was cancelled, rar might be partial

		# init settings folder
		self.SCRIPT_DATA_DIR = os.path.join( "T:\\script_data", __scriptname__ )
		makeDir(self.SCRIPT_DATA_DIR)

		# SETTINGS
		self.SETTINGS_FILENAME = os.path.join( self.SCRIPT_DATA_DIR, "settings.txt" )
		self.SETTING_SHORTCUT_DRIVE = "shortcut_drive"
		self.SETTING_SHORTCUT_NAME = "dash_shortcut_name"
		self.SETTING_UNRAR_PATH = "unrar_path"
		self.SETTING_NOTIFY_NOT_NEW = "notify_when_not_new"
		self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP = "check_script_update_startup"
		self.SETTING_XFER_USERDATA = "transfer_userdata"
		self.SETTING_PROMPT_DEL_RAR = "prompt_del_rar"

		# COPY INCLUDES
		self.INCLUDES_FILENAME = os.path.join( self.SCRIPT_DATA_DIR, "includes.txt" )
		self.EXCLUDES_FILENAME = os.path.join( self.SCRIPT_DATA_DIR, "excludes.txt" )

		self._init_includes_excludes()
		self.settings = self._load_file_obj( self.SETTINGS_FILENAME, {} )

		self._check_settings()
		scriptUpdated = False
		if self.settings[self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP] == __language__(402):	# check for update ?
#			if self.isSilent:
#				showNotification(__language__(0), __language__(619), 3)
			scriptUpdated = self._update_script(True)

		if not scriptUpdated:
			url = self._get_latest_version()										# discover latest build
#			url = "http://somehost/XBMC-SVN_2008-01-27_rev11426-T3CH.rar"			# DEV ONLY!!, saves DL it
			if url:
				remote_archive_name, remote_short_build_name = self._check_build_date( url )
			else:
				remote_archive_name = ""
				remote_short_build_name = ""

			# empty short_build_name indicates No New Build found.
			if self.runMode == RUNMODE_NORMAL or (remote_short_build_name and self.runMode == RUNMODE_SILENT):
				self._menu( url, remote_archive_name, remote_short_build_name )

		xbmc.output("< __init__() done")


	######################################################################################
	def _check_settings( self, forceSetup=False ):
		xbmc.output( "_check_settings()" )
		while forceSetup or not self._set_default_settings(False):
			self.isSilent = False							# come out of silent inorder to setup
			self._settings_menu()							# enter settings
			forceSetup = False								# cancel force entry, can now exit when ok

	######################################################################################
	def _set_default_settings( self, forceReset=False ):
		""" set settings to default values if not exist """
		xbmc.output( "> _set_default_settings() forceReset="+str(forceReset) )
		success = True

		items = {
			self.SETTING_SHORTCUT_DRIVE : "C:\\",
			self.SETTING_SHORTCUT_NAME : "xbmc",
			self.SETTING_UNRAR_PATH : "E:\\apps",
			self.SETTING_NOTIFY_NOT_NEW :  __language__(402), # yes
			self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP : __language__(403),	# No
			self.SETTING_XFER_USERDATA : __language__(402),	# yes
			self.SETTING_PROMPT_DEL_RAR : __language__(402)	# yes
			}

		for key, defaultValue in items.items():
			if forceReset or not self.settings.has_key( key ) or not self.settings[key]:
				self.settings[key] = defaultValue
				if not forceReset:
					xbmc.output( "missing setting: " + key )
					success = False

		xbmc.output( "< _set_default_settings() success=%s" % success)
		return success
		
	######################################################################################
	def _load_file_obj( self, filename, dataType ):
		xbmc.output( "_load_file_obj() " + filename)
		try:
			file_handle = open( filename, "r" )
			load_obj = eval( file_handle.read() )
			file_handle.close()
		except:
			if isinstance(dataType, dict):
				load_obj = {}
			elif isinstance(dataType, list):
				load_obj = []
			else:
				load_obj = None
		return load_obj

	######################################################################################
	def _save_file_obj( self, filename, save_obj ):
		xbmc.output( "_save_file_obj() " + filename)
		try:
			file_handle = open( filename, "w" )
			file_handle.write( repr( save_obj ) )
			file_handle.close()
		except:
			handleException( "_save_file_obj()" )


	######################################################################################
	def _browse_for_path( self, heading, default_path='', dialog_type=3):
		xbmc.output( "_browse_for_path() default_path=" + default_path + " dialog_type="+str(dialog_type) )
		dialog = xbmcgui.Dialog()
		skinName = xbmc.getSkinDir()
		if skinName.find("MC360") >= 0:		# for just MC360
			dialogOK( __language__( 0 ), heading )
		return dialog.browse( dialog_type, heading, "files", '', False, False, default_path)

	######################################################################################
	def _pick_shortcut_drive( self):
		xbmc.output( "_pick_shortcut_drive()" )
		options = [__language__(650), "C:\\", "E:\\", "F:\\"]
		selectDialog = xbmcgui.Dialog()
		selected = selectDialog.select( __language__( 202 ), options )
		if selected >= 1:
			return options[selected]
		else:
			return None

	######################################################################################
	def _browse_dashname(self, dash_name=''):
		xbmc.output( "> _browse_dashname() curr dash_name="+dash_name)
		try:
			xbeFiles = [__language__(650), __language__(652)]

			# include current dash name into list after Exit and Manual
			xbeFiles.append(dash_name)

			# get shortcut drive to check for existing dash names
			try:
				drive = self.settings["shortcut_drive"]
			except:
				drive = "C:\\"
			xbmc.output( "checking for names on drive=" + drive)
			# find all existing dash name
			allFiles = os.listdir( drive )
			for f in allFiles:
				fn, ext = os.path.splitext(f)
				if fn != 'msdash' and (ext in ['.xbe','.cfg']):
					try:
						xbeFiles.index(fn)
					except:
						xbeFiles.append(fn)

			# select from list or use keyboard
			selectDialog = xbmcgui.Dialog()
			while True:
				selected = selectDialog.select( __language__( 201 ), xbeFiles )
				if selected <= 0:						# quit
					break
				elif selected == 1:
					dash_name = getKeyboard(dash_name, __language__( 201 ))
					if dash_name[-1] in ['\\','/']:
						dash_name = dash_name[:-1]
				else:
					# select dash name form list
					dash_name = xbeFiles[selected]

				if dash_name:
					break
				else:
					dialogOK(  __language__( 0 ), __language__( 309 ) )

		except:
			handleException("_browse_dashname()")
		xbmc.output( "< _browse_dashname() final dash_name="+dash_name)
		return dash_name


	######################################################################################
	def _check_build_date( self, url ):
		xbmc.output( "> _check_build_date() " + url )

		archive_name = ''
		short_build_name = ''
		try:
			# get system build date info
			curr_build_date_secs, curr_build_date = self._get_current_build_info()

			# extract new build date from name
			archive_name, found_build_date, found_build_date_secs, short_build_name = self._get_archive_info(url)

			if curr_build_date_secs >= found_build_date_secs:							# No new build
				short_build_name = ''
				archive_name = ''
				if self.settings[self.SETTING_NOTIFY_NOT_NEW] == __language__(402):		# YES, show notification
					dialogOK( __language__( 0 ), __language__( 517 ), isSilent=True )	# always use xbmc.notification
			elif self.runMode != RUNMODE_NORMAL:										# new build
				dialogOK( __language__( 0 ), __language__( 518 ), short_build_name, isSilent=True )		# always use xbmc.notification
		except:
			traceback.print_exc()

		xbmc.output("< _check_build_date() new available = " +str(short_build_name != ""))
		return (archive_name, short_build_name)

	######################################################################################
	def _get_archive_info(self, source):
		""" parse local file or url to get build info """
		xbmc.output( "_get_archive_info() %s" % source)
		filenameInfo = ()
		try:
			archive_name = os.path.basename( source )       		# with ext
			found_build_date = searchRegEx(archive_name, '(\d+-\d+-\d+)') 
			found_build_date_secs = time.mktime( time.strptime(found_build_date,"%Y-%m-%d") )
			short_build_name = "T3CH_%s" % (found_build_date)		# used as installation folder name
			filenameInfo = (archive_name, found_build_date, found_build_date_secs, short_build_name)
		except:
			xbmc.output("exception parsing filename")
			traceback.print_exc()

		if not filenameInfo:
			dialogOK(__language__(0), "Unable to parse archive filename!", \
					 "EG.: XBMC-SVN_2007-12-23_rev11071-T3CH.rar", archive_name)
		else:
			xbmc.output(str(filenameInfo))
		return filenameInfo

	######################################################################################
	def _menu( self, url, remote_archive_name="", remote_short_build_name="" ):
		xbmc.output( "_menu() url=" + url )
		xbmc.output( "remote_archive_name=" + remote_archive_name)
		xbmc.output( "remote_short_build_name=" + remote_short_build_name)

		selectDialog = xbmcgui.Dialog()
		heading = "%s v%s (XBMC:%s): %s" % (__language__( 0 ), __version__, \
												xbmc.getInfoLabel('System.BuildDate'), \
												__language__( 600 ))

		def _make_menu(local_archive_name=''):
			self.opt_exit = __language__(650)
			self.opt_view_logs = __language__(611)
			if remote_archive_name:
				self.opt_download = "%s  %s"  % (__language__(612), remote_archive_name)# download w/ rar name
			else:
				self.opt_download = "%s  %s"  % (__language__(612),__language__(517))	# no new build
			self.opt_maint_copy = __language__(615)
			self.opt_maint_del = __language__(618)
			self.opt_switch = __language__(616)
			self.opt_del_build = __language__(617)
			self.opt_update_script = __language__(619)
			self.opt_settings = __language__(610)
			self.opt_local = "%s  %s" % (__language__(620), local_archive_name)

			options = [self.opt_exit,
					   self.opt_view_logs,
					   self.opt_download,
					   self.opt_local,
					   self.opt_maint_copy,
					   self.opt_maint_del,
					   self.opt_switch,
					   self.opt_del_build,
					   self.opt_update_script,
					   self.opt_settings
					   ]

			# remove local install opt if no archive found
			if not local_archive_name:
				options.remove(self.opt_local)

			# remove Update Script option if check enabled at startup
			if self.settings[self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP] == __language__(402): # yes
				options.remove(self.opt_update_script)

			return options

		while True:
			# Only include found rar if not a result of a previous cancelled download, as may be partial.
			local_archive_name = ''
			local_short_build_name = ''
			if not self.isSilent:
				local_rar_file = self._get_local_archive()
				if local_rar_file:
					# assume local rars under 50meg are partial downloads and delete them
					rar_filepath = os.path.join( self.settings[ self.SETTING_UNRAR_PATH ], local_rar_file)
					fsize = os.path.getsize(rar_filepath)
					if self.isPartialDownload or fsize < 50000000:
						xbmc.output("suspected incompleted rar, fsize=%s self.isPartialDownload=%s" % (fsize, self.isPartialDownload))
						deleteFile(rar_filepath)
					else:
						try:
							local_archive_name, found_build_date, found_build_date_secs, local_short_build_name = self._get_archive_info(local_rar_file)
						except:
							local_archive_name = '' # failed parsing local rar, don't add to menu

			# build menu
			options = _make_menu(local_archive_name)

			# show menu
			if not self.isSilent:
				selectedIdx = selectDialog.select( heading, options )
				xbmc.output("menu selectedIdx="+ str(selectedIdx))
				if selectedIdx <= 0:		# quit
					return
				selectedOpt = options[selectedIdx]
			else:
				selectedOpt = self.opt_download											# force process

			if selectedOpt == self.opt_exit:
				break
			elif selectedOpt == self.opt_view_logs:										# view logs (XBMC or T3CH)
				if dialogYesNo( __language__( 0 ), __language__( 611 ), \
								yesButton=__language__( 411 ), noButton=__language__( 410 )):
					self._view_t3ch_changelog()
				else:
					self._view_xbmc_changelog()
			elif selectedOpt == self.opt_download:										# new build remote install
				if remote_archive_name:
					self.archive_name = remote_archive_name
					self.short_build_name = remote_short_build_name
					# ask if to just DL or DL & install ?
					downloadOnly = dialogYesNo( __language__( 0 ), __language__( 533 ), \
						yesButton=__language__( 400 ), noButton=__language__( 416 ))

					if self._process(url, True, downloadOnly):
						if not downloadOnly:
							if self.isSilent or dialogYesNo( __language__( 0 ), __language__( 512 )):		# reboot ?
								xbmc.executebuiltin( "XBMC.Reboot" )
							break
					else:
						self.isSilent = False											# failed, show menu
					if self.isSilent:
						break
			elif selectedOpt == self.opt_local:											# local archive install
				if local_archive_name:
					self.archive_name = local_archive_name
					self.short_build_name = local_short_build_name
					if self._process('', False, False):
						if dialogYesNo( __language__( 0 ), __language__( 512 )):		# reboot ?
							xbmc.executebuiltin( "XBMC.Reboot" )
						break
			elif selectedOpt == self.opt_maint_copy:									# copy includes
				self._maintain_includes()
			elif selectedOpt == self.opt_maint_del:										# delete excludes
				self._maintain_excludes()
			elif selectedOpt == self.opt_switch:										# change to another t3ch
				if self._switch_builds_menu():
					break
			elif selectedOpt == self.opt_del_build:										# delete old t3ch
				self._delete_old_t3ch()
			elif selectedOpt == self.opt_update_script:									# update script
				if self._update_script(False):											# never silent from config menu
					xbmc.output("script updating ... closing current instance")
					break
			elif selectedOpt == self.opt_settings:										# settings
				self._check_settings(forceSetup=True)

	#####################################################################################
	def _switch_builds_menu(self):
		xbmc.output( "> _switch_builds_menu() ")

		reboot = False
		selectedBuildName = ''

		while not selectedBuildName:
			# find all LOCAL installed t3ch builds dirs
			buildsList = self._find_local_t3ch_dirs()
			buildsList.insert(0, __language__( 621 ))	# web builds - 2nd option
			buildsList.insert(0, __language__( 650 ))	# exit - 1st option
			
			# select
			selectDialog = xbmcgui.Dialog()
			selected = selectDialog.select( __language__( 205 ), buildsList )
			if selected <= 0:							# quit
				break
			
			if selected == 1:							# web build archive
				self._web_builds_menu()
			else:
				selectedBuildName = buildsList[selected]
				# do build switch by writing path into Shortcut
				path = os.path.join( self.settings[ self.SETTING_UNRAR_PATH ], selectedBuildName)
				if self._update_shortcut(path):
					if dialogYesNo( __language__( 0 ), __language__( 512 )):				# reboot ?
						reboot = True
						xbmc.executebuiltin( "XBMC.Reboot" )

		xbmc.output( "< _switch_builds_menu() ")
		return reboot


	######################################################################################
	def _get_local_archive(self):
		""" return latest T3CH archive found in install dir. Matches filenames of XBMC*YYYY-DD-MM*.<zip|rar> """
		xbmc.output("> _get_local_archive()")
		archive_file = ""
		flist = []
		try:
			files = os.listdir( self.settings[ self.SETTING_UNRAR_PATH ] )
			for f in files:
				if searchRegEx(f, '(XBMC.*?\d+-\d+-\d+.*?(?:.rar|.zip))'):
					flist.append(f)

			# sort to get latest
			if flist:
				flist.sort()
				flist.reverse()
				archive_file = flist[0]
		except:
			traceback.print_exc()
		xbmc.output("< _get_local_archive() archive_file=" + archive_file)
		return archive_file


	######################################################################################
	def _check_sfv(self, archive_local_filepath):
		""" Download SFV for latest T3CH build, then check against RAR """
		xbmc.output( "> _check_sfv()" )
		success = False

		# make full path + filename using remote archive filename
		if self.archive_name and archive_local_filepath:
			(split_name, split_ext) = os.path.splitext( self.archive_name )

			# download remote sfv doc
			doc = ""
			for ftpUrl in self.FTP_URL_LIST:
				url = "%s%s%s.sfv" % (ftpUrl, self.FTP_REPOSITORY_URL, split_name)
				doc = readURL( url, __language__( 502 ), self.isSilent )
				if doc: break

			if doc:
				# compare against archive actual local filename, which may be diff. to remote filename
				# due to being renamed cos of filename length.
				xbmc.output("checking sfv entry for %s %s" % (split_name, archive_local_filepath))
				sfv = SFVCheck.SFVCheck(sfvDoc=doc)
				success = sfv.check(split_name, archive_local_filepath)
				if success == None:
					# entry name not found, try with full name+ext
					success = sfv.check(self.archive_name, archive_local_filepath)

		if success == None:		# filename entry not found in SFV doc
			success = dialogYesNo( __language__( 0 ), __language__( 320 ) )
		elif not success:
			dialogOK( __language__( 0 ), __language__(315) )
		xbmc.output( "< _check_sfv() success=%s" % success)
		return success

	######################################################################################
	# processAction: 0 = Download & install, 1 = Install Existing, 2 = Download only
	######################################################################################
	def _check_free_mem(self, driveSpaceRequiredMb=180, ramCheck=True):
		""" check installation drive has enough freespace and enough free ram """
		xbmc.output( "> _check_free_mem() driveSpaceRequiredMb=%s ramCheck=%s" % (driveSpaceRequiredMb, ramCheck))

		success = False
		drive = os.path.splitdrive( self.settings[self.SETTING_UNRAR_PATH] )[0][0]	# eg C from (C:, path)
		drive_freespace_info = xbmc.getInfoLabel('System.Freespace(%s)' % drive)

		# convert info to MB
		drive_freespaceMb = int(searchRegEx(drive_freespace_info, '(\d+)'))		# extract space number
		xbmc.output("Drive=%s  Freespace=%sMB  Required=%sMB" % (drive, drive_freespaceMb, driveSpaceRequiredMb))

		if drive_freespaceMb < driveSpaceRequiredMb:
			msg = __language__(530)  % (drive, drive_freespaceMb, driveSpaceRequiredMb)
			dialogOK(__language__(0), __language__(316), msg, isSilent=False, time=5)
		elif not ramCheck:
			# DL only, no RAM check required
			success = True
		else:
			# warn if low, but can continue if OK'd
			freememMb = xbmc.getFreeMem()
			freeMemRecMb = 31		# 31 seems ok, always rez dependant eg. 480p 16:9 == 42mb
			xbmc.output( "Freemem=%sMB  Recommended=%sMB" % ( freememMb, freeMemRecMb ) )
			if freememMb < freeMemRecMb:
				msg = __language__( 531 ) % (freememMb, freeMemRecMb)
				success = xbmcgui.Dialog().yesno( __language__( 0 ), __language__(317), msg, __language__(532) )
			else:
				success = True

		xbmc.output( "< _check_free_mem() success=%s" % success)
		return success

	######################################################################################
	def _process( self, url='', useSFV=True, downloadOnly=False ):
		""" Download, Extract and Install new T3CH build, from a url or local archive """
		xbmc.output( "> _process() url=%s useSFV=%s downloadOnly=%s" % (url, useSFV, downloadOnly))

		success = False
		try:
			# ensure remote filename doesnt exceed xbox filesystem local filename length limit
			if url and len(self.archive_name) > 42:		# xbox filename limit
				archive_name = "%s.rar" % self.short_build_name.replace("T3CH", "XBMC")
				xbmc.output("remote archive filename too long, renamed")
			else:
				archive_name = self.archive_name

			# create work paths
			extract_path = os.path.join( self.settings[ self.SETTING_UNRAR_PATH ], self.short_build_name)
			xbmc.output( "extract_path= " + extract_path )
			archive_file = os.path.join( self.settings[ self.SETTING_UNRAR_PATH ], archive_name )
			xbmc.output( "archive_file= " + archive_file )

			# determine which mem (RAM / hdd) check to do according to process action
			ramCheck = True
			if downloadOnly:
				driveSpaceRequiredMb = 60		# DL only hdd space
				ramCheck = False
			elif url:
				driveSpaceRequiredMb = 180		# DL & unpack, install hdd space
			else:
				driveSpaceRequiredMb = 120		# local archive unpack, install

			if not downloadOnly and not self._check_free_mem(driveSpaceRequiredMb, ramCheck):
				xbmc.output("< _process() success=False")
				return False

			if url:
				# download build
				have_file = False
				if self._fetch_current_build( url, archive_file ):
					# check against SFV if reqd
					if not useSFV or self._check_sfv(archive_file):
						have_file = True
			else:
				have_file = fileExist(archive_file)

			xbmc.output( "have_file=%s" % have_file)
			if downloadOnly:
				success = True
			elif have_file:
				if self._extract( archive_file, extract_path ):

					if self.isSilent or dialogYesNo( __language__( 0 ), __language__( 507 ), __language__( 508 ), "" ):

						if not self.isSilent:
							dialogProgress.create( __language__( 0 ) )

						if self.settings[self.SETTING_XFER_USERDATA] == __language__(402):
							self._copy_user_data(extract_path)

						# do Custom Copies
						self._copy_includes()

						# do Custom Deletes
						self._delete_excludes()

						if not self.isSilent:
							dialogProgress.close()

					# update shortcuts ?
#					if self.isSilent or dialogYesNo( __language__(0), __language__(529), yesButton=__language__( 402 ), noButton=__language__( 403 )):
					success = self._update_shortcut(extract_path)		# create shortcut

				# del rar according to del setting
				if fileExist(archive_file):
					# always del if no prompt reqd or isSilent
					if self.isSilent or self.settings[self.SETTING_PROMPT_DEL_RAR] == __language__(403) or \
						dialogYesNo( __language__( 0 ), __language__( 528 ), archive_file, \
									yesButton=__language__( 412 ), noButton=__language__( 413 )):
						deleteFile(archive_file)					# remove RAR
		except:
			handleException("process()")
		xbmc.output("< _process() success=%s" % success)
		return success

	######################################################################################
	def _init_includes_excludes(self, forceReset=False):
		xbmc.output("_init_includes_excludes() forceReset=%s" % forceReset)

		self.includes = []
		self.excludes = []
		if forceReset:
			deleteFile( self.INCLUDES_FILENAME )
			deleteFile( self.EXCLUDES_FILENAME )
		else:
			if fileExist(self.INCLUDES_FILENAME):
				self.includes = self._load_file_obj( self.INCLUDES_FILENAME, [] )
			if fileExist(self.EXCLUDES_FILENAME):
				self.excludes = self._load_file_obj( self.EXCLUDES_FILENAME, [] )

		changed = self._hardcoded_includes()		# ensure mandatory include folders
		# remove old bad include paths
		try:
			self.includes.remove("plugins\\")
			xbmc.output("includes; removed 'plugins\\'")
			changed = True
		except: pass
		if forceReset or changed:
			self._save_file_obj(self.INCLUDES_FILENAME, self.includes)

		changed = self._hardcoded_excludes()
		if forceReset or changed:
			self._save_file_obj(self.EXCLUDES_FILENAME, self.excludes)

	######################################################################################
	def _hardcoded_includes(self):
		""" Additional files/folders for post installation copying. All relative to Q:\ """
		xbmc.output("_hardcoded_includes()")
		changed = False
		# add if not already included
		srcList = [ "skin\\", "screensavers\\", "scripts\\", "plugins\\videos", "plugins\\pictures", \
					"plugins\\music", "plugins\\programs", "system\\profiles.xml" ]
		# ensure hardcoded in includes
		for src in srcList:
			if src not in self.includes:
				self.includes.append(src)
				changed = True
		return changed

	######################################################################################
	def _hardcoded_excludes(self):
		""" Additional files/folders for post installation deleting. All relative to extract_path\\XBMC """
		xbmc.output("_hardcoded_excludes()")
		changed = False
		srcList = [ "..\\_tools", "..\\win32", "..\\Changelog.txt", "..\\copying.txt", "..\\keymapping.txt" ]
		for src in srcList:
			if src not in self.excludes:
				self.excludes.append(src)
				changed = True
		return changed

	######################################################################################
	def _get_latest_version( self ):
		xbmc.output( "_get_latest_version()" )
		url = ""
		for baseUrl in self.HOME_URL_LIST:
			doc = readURL( baseUrl, __language__( 502 ), self.isSilent )
			if doc:
				url = self._parse_html_source( doc )
				break

		if not url:
			dialogOK( __language__( 0 ), __language__( 301 ), isSilent=self.isSilent)
		return url

	######################################################################################
	def _parse_html_source( self, htmlsource ):
		xbmc.output( "_parse_html_source()" )
		try:
			parser = Parser()
			parser.feed( htmlsource )
			parser.close()
			return parser.url
		except:
			handleException("_parse_html_source()", __language__( 305 ))
			return None

	######################################################################################
	def _fetch_current_build( self, url, file_name ):
		xbmc.output( "> _fetch_current_build() " + url +" " + file_name )
		success = False
		try:
			self.reporthook_msg1 = __language__( 503 )
			self.reporthook_msg2 = file_name
			if not self.isSilent:
				dialogProgress.create( __language__( 0 ), self.reporthook_msg1, self.reporthook_msg2 )
			else:
				showNotification(__language__(0), "%s -> %s" % (__language__( 503 ), file_name), 240)

			urllib.urlretrieve( url , file_name, self._report_hook )

			dialogProgress.close()
			success = fileExist(file_name)
		except:
			traceback.print_exc()
			dialogProgress.close()
			dialogOK( __language__( 0 ), __language__( 303 ), isSilent=self.isSilent )

		urllib.urlcleanup()
		self.isPartialDownload = not success
		xbmc.output("< _fetch_current_build() success=" + str(success) + " isPartialDownload=" + str(self.isPartialDownload))
		return success

	######################################################################################
	def _report_hook( self, count, blocksize, totalsize ):
		if not self.isSilent:
			# just update every x%
			if count and totalsize > 0:
				percent = int( float( count * blocksize * 100) / totalsize )
			else:
				percent = 0
			if count == 0 or (percent and percent % 5 == 0):
				dialogProgress.update( percent, self.reporthook_msg1, self.reporthook_msg2 )
			if ( dialogProgress.iscanceled() ):
				raise

	######################################################################################
	def _extract( self, file_name, extract_path ):
		xbmc.output( "> _extract() file_name=%s extract_path=%s"  % (file_name, extract_path))
		success = False

		# check extract destination folder doesnt exist
		if os.path.exists(extract_path):
			# ask to overwrite 
			if not dialogYesNo(__language__( 0 ), __language__( 314 ), extract_path, \
							yesButton=__language__( 402 ), noButton=__language__( 403 )):
				xbmc.output( "< _extract() no overwrite. False")
				return False

		# use a new dialog cos an update shows an empty bar that ppl expect to move
		if not self.isSilent:
			dialogProgress.create( __language__( 0 ), __language__( 504 ), extract_path )
		else:
			showNotification(__language__( 0 ), "%s %s" % (__language__( 504 ), extract_path), 60 )

		time.sleep(1)
		# determine which extract to do, RAR (xbmc builtin) or ZIP (Python module)
		try:
			if file_name.endswith("rar"):
				xbmc.output("extracting RAR ...")
				xbmc.executebuiltin( "XBMC.extract(%s,%s)" % ( file_name, extract_path, ), )
			else:
				# unpack ZIP, then rename to reqd short path name
				success, installed_path = unzip(self.settings[ self.SETTING_UNRAR_PATH ], file_name, self.isSilent, __language__(504))
				if success:
					if os.path.isdir(extract_path):
						os.rmdir(extract_path)
						xbmc.output("removed existing dir we wish to rename too " + extract_path)

					for retry in range(3):
						try:
							time.sleep(2)
							os.rename(installed_path, extract_path)
							xbmc.output("installation dir renamed to " + extract_path)
							break
						except:
							traceback.print_exc()
		except:
			dialogProgress.close()
			traceback.print_exc()
			dialogOK( __language__( 0 ), __language__( 304 ))
		else:
			success = self._check_extract(extract_path)
			dialogProgress.close()
			if not success:
				# remove partial extract
				try:
					rmtree( extract_path, ignore_errors=True )
					xbmc.output("extract failed, extract path rmtree done")
				except: pass
				dialogOK( __language__( 0 ), __language__( 312 ), extract_path )

		xbmc.output( "< _extract() success=%s" % success )
		return success

	######################################################################################
	def _check_extract(self, extract_path):
		xbmc.output( "> _check_extract() extract_path=" + extract_path)
		success = False

		# inform user of os path checking
		if not self.isSilent:
			self._dialog_update( __language__(0), __language__( 522 ))

		# loop to check if extract path appears
		check_base_path = os.path.join(extract_path, 'XBMC')
		check_path_list = [os.path.join(check_base_path,'UserData'),
							os.path.join(check_base_path,'system'),
							os.path.join(check_base_path,'skin'),
							os.path.join(check_base_path,'media'),
							os.path.join(check_base_path,'language'),
							os.path.join(check_base_path,'sounds')
						]
		check_file = os.path.join(check_base_path,'default.xbe' )
		time.sleep(2)
		MAX = 40
		for count in range(MAX):
			isFile = fileExist(check_file)
			isPath = True
			for p in check_path_list:
				isPath = os.path.isdir(p)
				xbmc.output("%s %s" % (p, isPath))
				if not isPath:
					break
			xbmc.output("checkCount=" + str(count) + " isPath="+str(isPath) + " isFile="+str(isFile))

			if not isFile or not isPath:
				if count < MAX-1:
					if not self.isSilent:
						percent = int( count * 100.0 / MAX )
						msg1 = "%s (%d/%d)" % (__language__( 522 ), count, MAX)
						msg2 = "%s  %s" % (__language__(526), str(isPath))
						msg3 = "%s  %s" % (__language__(527), str(isFile))
						dialogProgress.update( percent, msg1, msg2, msg3)
						if ( dialogProgress.iscanceled() ): break
					time.sleep(2)
			else:
				success = True
				break

		dialogProgress.close()
		xbmc.output( "< _check_extract() success=%s" % success )
		return success

	######################################################################################
	def _view_t3ch_changelog( self, ):
		xbmc.output( "_view_t3ch_changelog()" )
		doc = ""
		for ftpUrl in self.FTP_URL_LIST:
			url = "%s%sT3CH-README_1ST.txt" % (ftpUrl, self.FTP_REPOSITORY_URL)
			doc = readURL( url, __language__( 502 ), self.isSilent )
			if doc: break

		if doc:
			tbd = TextBoxDialogXML(TEXTBOX_XML_FILENAME, DIR_RESOURCES, "Default")
			tbd.ask("T3CH Changelog", doc)
			del tbd
		else:
			dialogOK( __language__( 0 ), __language__( 310 ))

	######################################################################################
	def _view_xbmc_changelog( self, ):
		xbmc.output( "_view_xbmc_changelog()" )
		doc = ""
		# read from several home urls until get connection and doc
		for url in self.HOME_URL_LIST:
			doc = readURL( os.path.join( url, "latest.txt" ), __language__( 502 ), self.isSilent )
			if doc: break

		if doc:
			tbd = TextBoxDialogXML(TEXTBOX_XML_FILENAME, DIR_RESOURCES, "Default")
			tbd.ask("XBMC Changelog", doc )
			del tbd
		else:
			dialogOK( __language__( 0 ), __language__( 310 ))

	######################################################################################
	def _view_script_doc( self, readmeORchangelog):
		xbmc.output( "_view_script_doc() readmeORchangelog=" +str(readmeORchangelog))
		if readmeORchangelog:		# readme
			title = "%s: %s" % (__language__(0), __language__(414))

			# determine language path
			base_path = mylanguage.get_base_path()
			language = xbmc.getLanguage().lower()
			fn = os.path.join( base_path, language, "readme.txt" )
			if ( not fileExist( fn ) ):
				fn = os.path.join( base_path, "english", "readme.txt" )
		else:
			title = "%s: %s" % (__language__(0), __language__(415))
			fn = os.path.join(DIR_RESOURCES, "changelog.txt")

		xbmc.output("fn=" + fn)
		# read and display
		if not fileExist(fn):
			doc = "File is missing!"
		else:
			doc = file(fn).read()

		tbd = TextBoxDialogXML(TEXTBOX_XML_FILENAME, DIR_RESOURCES, "Default")
		tbd.ask(title, doc)
		del tbd

	######################################################################################
	def _copy_user_data(self, extract_path):
		xbmc.output( "> _copy_user_data() " + extract_path )
		success = False

		try:
			curr_build_userdata_path = "T:\\"
			new_build_userdata_path = os.path.join( extract_path, "XBMC", "UserData")

			# remove new build UserData
			checkMAX = 5
			for checkCount in range(checkMAX):
				xbmc.output("rmtree UserData checkCount=%i" % checkCount)
				percent = int( checkCount * 100.0 / checkMAX )
				self._dialog_update( __language__(0), __language__( 510 ), pct=percent, time=2)
				rmtree( new_build_userdata_path, ignore_errors=True )
				time.sleep(2)	# give os chance to complete rmdir
				if not os.path.isdir(new_build_userdata_path):
					break

			# Copytree current UserData to new build
			try:
				xbmc.output("copytree UserData %s -> %s" % (curr_build_userdata_path,new_build_userdata_path) )
				self._dialog_update( __language__(0), __language__( 511 ), time=2) 
				copytree( curr_build_userdata_path, new_build_userdata_path )
				success = True
			except:
				dialogOK("Copy UserData Error","Failed to copytree:", curr_build_userdata_path, new_build_userdata_path)
		except:
			handleException("_copy_user_data()", __language__( 306 ))
		xbmc.output( "< _copy_user_data() success=%s" % success )
		return success


	######################################################################################
	def _update_shortcut(self, extract_path):
		xbmc.output( "> _update_shortcut() " +extract_path )

		success = False
		# get users prefered booting dash name eg. XBMC.xbe
		# if required, copy SHORTCUT by TEAM XBMC to root\<dash_name>
		dash_name = self.settings[self.SETTING_SHORTCUT_NAME]
		shortcut_drive = self.settings[self.SETTING_SHORTCUT_DRIVE]
		shortcut_xbe_file = os.path.join( shortcut_drive, dash_name + ".xbe" )
		xbmc.output( "shortcut_xbe_file= " + shortcut_xbe_file )
		shortcut_cfg_file = os.path.join( shortcut_drive, dash_name + ".cfg" )
		xbmc.output( "shortcut_cfg_file= " + shortcut_cfg_file )

		# backup CFG shortcut
		if fileExist( shortcut_cfg_file ):
			copy( shortcut_cfg_file, shortcut_cfg_file + "_old" )
			xbmc.output( "backup of cfg made to _old" )

		# if shortcutname has dir prefix, ensure it exists
		prefix_dir = os.path.dirname(shortcut_xbe_file)
		xbmc.output("prefix_dir="+prefix_dir)
		if prefix_dir and not os.path.isdir(prefix_dir):
			makeDir(prefix_dir)

		# check if TEAM XBMC shortcut needs copying
		copy_xbe = True
		src_xbe_file = os.path.join( DIR_RESOURCES, "SHORTCUT by TEAM XBMC.xbe" )
		if fileExist( shortcut_xbe_file ):
			# DOES EXIST, check if diff
			if not filecmp.cmp( src_xbe_file, shortcut_xbe_file ):
				xbmc.output( "Shortcuts differ. Backup shortcut XBE: copy %s -> %s" % (shortcut_xbe_file, shortcut_xbe_file + "_old"))
				copy( shortcut_xbe_file, shortcut_xbe_file + "_old" )
			else:
				copy_xbe = False		# same file, no copy reqd

		try:
			# create new shortcut cfg path - this points to the new T3CH XBMC build xbe
			boot_path = os.path.join( extract_path, "XBMC", "default.xbe" )
			xbmc.output( "new cfg boot_path= " + boot_path )
			# write new cfg to .CFG_NEW
			shortcut_cfg_file_new = shortcut_cfg_file + "_new"
			xbmc.output( "shortcut_cfg_file_new= " + shortcut_cfg_file_new )
			# delete any existing .CFG_NEW
			deleteFile(shortcut_cfg_file_new)
			xbmc.output( "write '%s' into file %s" % (boot_path, shortcut_cfg_file_new) )
			file(shortcut_cfg_file_new,'w').write(boot_path)

			# switch to new cfg now ?
			xbmc.output( "Copy TEAM XBMC xbe required? %s" % copy_xbe)
			if self.isSilent or dialogYesNo( __language__( 0 ), __language__( 519 ), __language__( 520 ),__language__( 521  ),yesButton=__language__( 404 ), noButton=__language__(405) ):
				# copy TEAM XBMC shortcut xbe into place (if reqd)
				if copy_xbe:
					xbmc.output( "TEAM XBMC xbe: copy %s -> %s" % (src_xbe_file, shortcut_xbe_file))
					copy(src_xbe_file, shortcut_xbe_file)

				xbmc.output( "AUTO cfg copies: copy %s -> %s" % (shortcut_cfg_file_new, shortcut_cfg_file) )
				copy(shortcut_cfg_file_new, shortcut_cfg_file)
				time.sleep(1)
				success = True
			else:
				xbmc.output( "MANUAL cfg copies" )
		except:
			handleException("_update_shortcut()", __language__( 307 ))

		xbmc.output( "< _update_shortcut() success=%s" % success )
		return success

	######################################################################################
	def _copy_folder(self, src_path, dest_path):
		xbmc.output( "_copy_folder() src_path=" + src_path + " dest_path=" + dest_path)

		try:
			# check source folder exists!
			if not os.path.exists( src_path ):
				xbmc.output( "source folder doesnt exist! abort copy" )
				return

			# start copy of source tree
			self._dialog_update( __language__(0), __language__( 515 ), src_path) 
			# make dest root folder otherwise copytree will fail
			makeDir( dest_path )

			files = os.listdir(src_path)
			TOTAL = len(files)
			count = 0
			for f in files:
				# ignore parent dirs
				if f in ['.','..']: continue

				src_file = os.path.join( src_path, f )
				dest_file = os.path.join( dest_path, f )

				if not fileExist( dest_file ):
					if not self.isSilent:
						dialogProgress.update( int(100 / TOTAL) * count, __language__( 515 ), src_file)
						if dialogProgress.iscanceled(): break
					if os.path.isdir( src_file ):
						# copy directory
						copytree( src_file, dest_file )
						xbmc.output("copied tree OK " + src_file)
					else:
						# copy file
						copy( src_file, dest_file )
						xbmc.output("copied file OK " + src_file)
				else:
					xbmc.output( "ignored as exists in T3CH: " + dest_file)
				count += 1
		except:
			handleException("_copy_folder()", __language__( 308 ))

	######################################################################################
	def _copy_includes(self):
		xbmc.output( "_copy_includes() ")

		TOTAL = len(self.includes)
		count = 0
		extract_path = self.settings[self.SETTING_UNRAR_PATH]
		for path in self.includes:
			try:
				if not path.startswith("Q:\\"): 
					src_path = os.path.join("Q:\\", path)
				else:
					src_path = path
				dest_path = os.path.join( extract_path, self.short_build_name, "XBMC", path )
				if not self.isSilent:
					percent = int( count * 100.0 / TOTAL )
					self._dialog_update( __language__(0), __language__( 515 ), src_path, dest_path, pct=percent )
					if dialogProgress.iscanceled(): break
				localCopy(src_path, dest_path, self.isSilent)
				count += 1
			except:
				handleException("_copy_includes() path="+path)


	######################################################################################
	def _delete_excludes(self):
		xbmc.output( "_delete_excludes() ")

		TOTAL = len(self.excludes)
		count = 0
		extract_path = self.settings[self.SETTING_UNRAR_PATH]
		for path in self.excludes:
			try:
				if path.startswith(".."):
					path = path.replace("..\\","").replace("../","")
					dest_path = os.path.join( extract_path, self.short_build_name, path )
				else:
					dest_path = os.path.join( extract_path, self.short_build_name, "XBMC", path )

				if not self.isSilent:
					percent = int( count * 100.0 / TOTAL )
					self._dialog_update( __language__(0), __language__( 516 ), dest_path, pct=percent )
				if path[-1] in ["\\","/"] or os.path.isdir(dest_path):
					xbmc.output( "rmtree " + dest_path )
					rmtree(dest_path, ignore_errors=True)
				else:
					deleteFile(dest_path)
				count += 1
			except:
				handleException("_delete_excludes() path="+path)

	######################################################################################
	def _maintain_includes(self):
		xbmc.output( "_maintain_includes() ")

		try:
			selectDialog = xbmcgui.Dialog()
			while True:
				# make menu
				self.includes.sort()
				options = [__language__(650), __language__(651)]
				options.extend(self.includes)

				# show menu
				selected = selectDialog.select( __language__( 615 ), options )
				if selected <= 0:						# quit
					break

				path = ""
				deleteOption = False
				addOption = False
				if selected == 1:						# add new
					addOption = True
					path, type = self._select_file_folder(path)
					if path and \
						((type in [0,3] and self._isRestrictedFolder(path)) or \
						(type == 1 and self._isRestrictedFile(path))):
						path = ''
				else:									# remove or edit
					deleteOption = True
					path = options[selected]
					# ask what action to take (remove, edit)
					if not dialogYesNo( __language__( 0 ), path, yesButton=__language__(406), noButton=__language__(407)):
						path, type = self._select_file_folder(path)		# edit
						addOption = True

				if path:
					if deleteOption:
						del self.includes[selected-2]									# del

					if addOption:
						# add if not a duplicat
						try:
							self.includes.index(path)
						except:
							self.includes.append(path)

			# save options to file
			self._save_file_obj(self.INCLUDES_FILENAME, self.includes)
		except:
			handleException("_maintain_includes()")

	######################################################################################
	def _maintain_excludes(self):
		xbmc.output( "_maintain_excludes() ")
		try:
			def _pick_file(path=''):
				FILE = 1
				FOLDER = 0
				if not path:
					# add new
					if dialogYesNo(__language__(0), __language__(525), yesButton=__language__(408), noButton=__language__(409)):
						type = FOLDER
					else:
						type = FILE
				else:
					# editing existing
					path = os.path.join("Q:\\", path)
					path,filename = os.path.split(path)
					if not filename:
						type = FOLDER
					else:
						type = FILE

				try:
					if not path:
						path = "Q:\\"

					# always pick folder first
					path = self._browse_for_path(__language__(204), path, FOLDER)
					if not path or path[0] != "Q":
						raise

					if path[-1] not in ["\\","/"]:
						path += "\\"

					# enter filename using keyboard
					if type == FILE:
						path = getKeyboard(path, __language__(207))
						# ensure filename entered
						basename = os.path.basename(path)
						if not basename:
							raise

					bare_dest_path = str(os.path.splitdrive( path )[1])	# get path+filename, no drive
					if bare_dest_path and bare_dest_path[0] in ["/", "\\"]:
						bare_dest_path = bare_dest_path[1:]
					path = bare_dest_path.replace('/','\\')
				except:
					path = ''

				xbmc.output("_pick_file() final path=" + path + " type="+str(type))
				return path, type
			
			selectDialog = xbmcgui.Dialog()
			while True:
				# make menu
				self.excludes.sort()
				options = [__language__(650), __language__(651)]
				options.extend(self.excludes)

				# show menu
				selected = selectDialog.select( __language__( 618 ), options )
				if selected <= 0:						# quit
					break

				path = ""
				deleteOption = False
				addOption = False
				if selected == 1:						# add new
					addOption = True
					path, type = _pick_file()
					if path and \
						((type in [0,3] and self._isRestrictedFolder(path)) or \
						(type == 1 and self._isRestrictedFile(path))):
						path = ''

				else:									# remove or edit
					deleteOption = True
					path = options[selected]
					# ask what action to take (remove, edit)
					if not dialogYesNo( __language__( 0 ), path, yesButton=__language__(406), noButton=__language__(407)):
						path, type = _pick_file(path)					# edit
						addOption = True

				if path:
					if deleteOption:
						del self.excludes[selected-2]									# del

					if addOption:
						# add if not a duplicat
						try:
							self.excludes.index(path)
						except:
							self.excludes.append(path)

			# save options to file
			self._save_file_obj(self.EXCLUDES_FILENAME, self.excludes)
		except:
			handleException("_maintain_excludes()")

	#####################################################################################
	def _isRestrictedFolder(self, path):
		if (os.path.dirname(path).lower() in ["q:\\","credits","language","media","screensavers","scripts","skin","sounds","system","credits","visualisations"]):
			dialogOK(__language__(0), __language__(313))
			restricted = True
		else:
			restricted = False
		xbmc.output("_isRestrictedFolder() " + str(restricted))
		return restricted

	#####################################################################################
	def _isRestrictedFile(self, path):
		if (os.path.basename(path).lower() in ["default.xbe"]):
			dialogOK(__language__(0), __language__(313))
			restricted = True
		else:
			restricted = False
		xbmc.output("_isRestrictedFile() " + str(restricted))
		return restricted

	#####################################################################################
	def _select_file_folder(self, path=""):
		xbmc.output( "> _select_file_folder() path="+path)
		FILE = 1
		FOLDER = 0
		if not path:
			# add new
			if dialogYesNo(__language__(0), __language__(525), yesButton=__language__(408), noButton=__language__(409)):
				type = FOLDER
			else:
				type = FILE
		else:
			# editing existing
			path = os.path.join("Q:\\", path)
			if path[-1] in ["\\","/"]:
				type = FOLDER
			else:
				type = FILE

		try:
			if not path:
				path = "Q:\\"

			if type == FILE:
				msg = __language__(203)
			else:
				msg = __language__(204)
			path = self._browse_for_path(msg, path, type)
			if not path or path[0] != "Q":
				raise

			bare_dest_path = str(os.path.splitdrive( path )[1])	# get path+filename, no drive
			if bare_dest_path and bare_dest_path[0] in ["/", "\\"]:
				bare_dest_path = bare_dest_path[1:]
			path = bare_dest_path.replace('/','\\')
		except:
			path = ''

		xbmc.output("< _select_file_folder() final path=" + path + " type=" +str(type))
		return path, type

	#####################################################################################
	def _dialog_update(self, title="", line1="", line2="", line3="", pct=0, time=4):
		if not self.isSilent:
			dialogProgress.update( pct, line1, line2,line3 )
		else:
			msg = ("%s %s %s" % (line1, line2, line3)).strip()
			showNotification(title, msg, time)


	#####################################################################################
	def _delete_old_t3ch(self):
		xbmc.output( "_delete_old_t3ch() ")

		# find all t3ch builds
		oldBuilds = self._find_local_t3ch_dirs()
		oldBuilds.insert(0, __language__( 650 ))

		# select
		selectDialog = xbmcgui.Dialog()
		while True:
			selected = selectDialog.select( __language__( 206 ), oldBuilds )
			if selected <= 0:						# quit
				break

			selectedBuildName = oldBuilds[selected]

			# delete path
			path = os.path.join( self.settings[ self.SETTING_UNRAR_PATH ], selectedBuildName)
			if dialogYesNo(__language__( 0 ), __language__( 523 ), selectedBuildName ):
				try:
					dialogProgress.create(__language__( 0 ), __language__( 524 ))
					rmtree(path, ignore_errors=True)
					del oldBuilds[selected]
					dialogProgress.close()
				except:
					handleException("_delete_old_t3ch()")

	#####################################################################################
	def _find_local_t3ch_dirs(self):
		xbmc.output( "> _find_local_t3ch_dirs() ")
		dirList = []

		# get curr build name
		curr_build_date_secs, curr_build_date = self._get_current_build_info()
		# make list of folders, excluding curr build folder
		files = os.listdir(self.settings[ self.SETTING_UNRAR_PATH ] )
		for f in files:
			buildName = searchRegEx(f, "(T3CH_\d+-\d+-\d+)")
			if buildName and buildName != curr_build_date:
				dirList.append(buildName)

		xbmc.output( "< _find_local_t3ch_dirs() dir count=%s" % len(dirList))
		return dirList
	
	#####################################################################################
	def _find_web_builds(self):
		xbmc.output( "> _find_web_builds() ")
		buildList = []
		doc = ""
		for baseUrl in self.HOME_URL_LIST:
			doc = readURL( baseUrl, __language__( 502 ), self.isSilent )
			if doc: break

		if doc:
			# do regex on section
			findRe = re.compile('<option value="(XBMC-SVN_.*?)"', re.DOTALL + re.MULTILINE + re.IGNORECASE)
			reList = findRe.findall(doc)
			if reList:
				# remove current running build from list
				curr_build_date_secs, curr_build_date = self._get_current_build_info()
				for filename in reList:
					try:
						archive_name, build_date, build_date_secs, short_build_name = self._get_archive_info(filename)
						if curr_build_date != short_build_name:
							buildList.append(filename)
					except: pass

		xbmc.output( "< _find_web_builds() build count=%s" % len(buildList))
		return buildList

	#####################################################################################
	def _web_builds_menu(self):
		""" Find web old archive, show in a menu, select and download archive """
		xbmc.output( "> _web_builds_menu() ")

		buildsList = self._find_web_builds()
		if buildsList:
			buildsList.insert(0, __language__( 650 ))	# exit - 1st option
			while True:
				# select
				selectDialog = xbmcgui.Dialog()
				selected = selectDialog.select( __language__( 205 ), buildsList )
				if selected <= 0:						# quit
					break

				# extract new build date from name
				filename = buildsList[selected]
				info = self._get_archive_info(filename)
				if info:
					doc = ""
					url = ""
					self.archive_name, found_build_date, found_build_date_secs, self.short_build_name = info
					# check ftp server available by reading web page, if fails try next ftp address
					for ftpUrl in self.FTP_URL_LIST:
						url = "%s%s%s" % (ftpUrl, self.FTP_REPOSITORY_ARCHIVE_URL, filename)
						doc = readURL(url, __language__( 502 ), self.isSilent )
						if doc: break

					if doc:
						if self._process(url, useSFV=False):
							if dialogYesNo( __language__( 0 ), __language__( 512 )):	# reboot ?
								xbmc.executebuiltin( "XBMC.Reboot" )
					else:
						xbmcgui.Dialog().ok(__language__( 0 ), __language__( 318 ))		# all servers unavailable
						break

		xbmc.output("< _web_builds_menu()")

	#####################################################################################
	def _get_current_build_info(self):
		buildDate = xbmc.getInfoLabel( "System.BuildDate" )
		curr_build_date_fmt = time.strptime(buildDate,"%b %d %Y")
		curr_build_date_secs = time.mktime(curr_build_date_fmt)
		curr_build_date = time.strftime("T3CH_%Y-%m-%d", curr_build_date_fmt)
		xbmc.output( "_get_current_build_info() curr_build_date="+curr_build_date + " curr_build_date_secs= " + str(curr_build_date_secs ))
		return (curr_build_date_secs, curr_build_date)

	######################################################################################
	def _update_script( self, isSilent=False):
		xbmc.output( "> _update_script() isSilent=%s" % isSilent)

		updated = False
		up = update.Update(__language__, __scriptname__)
		version = up.getLatestVersion(isSilent)
		xbmc.output("Current Version: " + __version__ + " Tag Version: " + version)
		if version != "-1":				# check for err
			if __version__ < version:
				if ( dialogYesNo( __language__(0), \
					  "%s %s %s." % ( __language__( 1006 ), version, __language__( 1002 ), ), __language__( 1003 ),\
					  "", noButton=__language__( 403 ), \
					  yesButton=__language__( 402 ) ) ):
					updated = True
					up.makeBackup()
					up.issueUpdate(version)
			elif not isSilent:
				dialogOK(__language__(0), __language__(1000))
		elif not isSilent:
			dialogOK(__language__(0), __language__(1030))

		del up
		xbmc.output( "< _update_script() updated=%s" % updated)
		return updated

	#####################################################################################
	def _settings_menu(self):
		xbmc.output( "_settings_menu() ")

		def _set_yes_no(key, prompt):
			if dialogYesNo( __language__( 0 ), prompt ):
				self.settings[key] = __language__( 402 )	# YES
			else:
				self.settings[key] = __language__( 403 )	# NO


		def _make_menu(settings):
			options = [__language__(650),
						__language__(639),
						"%s -> %s" %(__language__(630),self.settings[self.SETTING_SHORTCUT_DRIVE]),
						"%s -> %s" %(__language__(631),self.settings[self.SETTING_SHORTCUT_NAME]),
						"%s -> %s" %(__language__(632),self.settings[self.SETTING_UNRAR_PATH]),
						"%s -> %s" %(__language__(633),self.settings[self.SETTING_NOTIFY_NOT_NEW]),
						"%s -> %s" %(__language__(634),self.settings[self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP]),
						"%s -> %s" %(__language__(635),self.settings[self.SETTING_XFER_USERDATA]),
						"%s -> %s" %(__language__(638),self.settings[self.SETTING_PROMPT_DEL_RAR]),
						__language__(636),
						__language__(637)
						]
			return options

		selectDialog = xbmcgui.Dialog()
		heading = "%s: %s" % (__language__( 0 ), __language__( 601 ) )
		while True:
			options = _make_menu(self.settings)
			selected = selectDialog.select( heading, options )
			if selected <= 0:						# quit
				break

			# match option name to settings key
			if selected == 1:														# readme/changelog
				if dialogYesNo(__language__( 0 ), __language__( 639 ), \
								yesButton=__language__( 414 ), noButton=__language__( 415 )):
					self._view_script_doc(True)			# readme
				else:
					self._view_script_doc(False)		# changelog
			if selected == 2:															# shortcut drive
				value = self._pick_shortcut_drive()
				if value:
					self.settings[self.SETTING_SHORTCUT_DRIVE] = value

			elif selected == 3:															# shortcut name
				value = self._browse_dashname(self.settings[self.SETTING_SHORTCUT_NAME])
				if value:
					self.settings[self.SETTING_SHORTCUT_NAME] = value

			elif selected == 4:															# unrar path
				value = self._browse_for_path( __language__( 200 ), self.settings[self.SETTING_UNRAR_PATH] )
				if value and value[0] != "Q":
					self.settings[self.SETTING_UNRAR_PATH] = value

			elif selected == 5:															# notify when not new
				_set_yes_no(self.SETTING_NOTIFY_NOT_NEW, __language__( 633 ))

			elif selected == 6:															# check for update
				_set_yes_no(self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP, __language__( 634 ))

			elif selected == 7:															# xfer userdata
				_set_yes_no(self.SETTING_XFER_USERDATA, __language__( 635 ))

			elif selected == 8:															# prompt del rar
				_set_yes_no(self.SETTING_PROMPT_DEL_RAR, __language__( 638 ))

			elif selected == 9:															# reset settings
				if dialogYesNo(__language__(0), __language__( 636 ) + " ?"):
					self._set_default_settings(forceReset=True)

			elif selected == 10:														# reset incl & excl
				if dialogYesNo(__language__(0), __language__( 637 ) + " ?"):
					self._init_includes_excludes(forceReset=True)

		# DO SOME POST SETTINGS MENU checks
		# ensure unrar path exists
		makeDir(self.settings[ self.SETTING_UNRAR_PATH ])

		self._save_file_obj( self.SETTINGS_FILENAME, self.settings )


######################################################################################
# GLOBAL FUNCS
######################################################################################


######################################################################################
# copies a folder or file to dest.
# If dest exists, not overwritten unlexx overwrite = True
######################################################################################
def localCopy(src_path, dest_path, isSilent=False, overwrite=False):
	xbmc.output( "localCopy() %s -> %s overwrite=%s" % (src_path, dest_path, overwrite))

	try:	
		if not os.path.exists(src_path):
			xbmc.output("src_path not exist, stop")
			return

		# if source is a path, ensure dest_path root exists
		if os.path.isdir( src_path ):
			makeDir( os.path.dirname(dest_path) )

		if os.path.isfile(src_path):
			# FILE
			if overwrite or not fileExist(dest_path):
				try:
					copy( src_path, dest_path )
				except:
					handleException("localCopy() FILE COPY", src_path, dest_path )
			else:
				xbmc.output( "isFile; dest file exists, ignored: " + dest_path)
		else:
			# DIR
			files = os.listdir(src_path)
			xbmc.output("isdir; file count=%s" % len(files))
			for f in files:
				src_file = os.path.join( src_path, f )
				dest_file = os.path.join( dest_path, f )

				try:
					if os.path.isdir( src_file ):
						do_copy = True
						if os.path.isdir( dest_file ):					# does dest dir exist ?
							if overwrite:								# overwrite if requested
								xbmc.output("isDir; overwrite; remove existing: " + dest_file)
								os.rmdir(dest_file)
								time.sleep(2)
							else:
								do_copy = False

						if do_copy:
							# copy directory
							xbmc.output("isDir; copytree dir: %s -> %s" % (src_file, dest_file))
							makeDir( os.path.dirname(dest_file) )
							copytree( src_file, dest_file )
						else:
							xbmc.output("isDir; dest dir exists, ignored: " + dest_file)
					else:
						if overwrite or not fileExist( dest_file ):
							copy( src_file, dest_file )
						else:
							xbmc.output("isDir; dest file exists, ignored: " + dest_file)
				except:
					handleException("localCopy() DIR COPY", src_file, dest_file )
	except:
		handleException("localCopy() Unhandled", src_path, dest_path )


#################################################################################################################
def getKeyboard(default, heading, hidden=False):
	keyboard = xbmc.Keyboard( default, heading )
	keyboard.doModal()
	if ( keyboard.isConfirmed() ):
		default = keyboard.getText().strip()
	return default

#################################################################################################################
def dialogOK(title, line1='', line2='',line3='', isSilent=False, time=3):
	if isSilent:
		msg = ("%s %s %s" % (line1, line2, line3)).strip()
		showNotification(title, msg, time)
	else:
		xbmcgui.Dialog().ok(title ,line1,line2,line3)

#################################################################################################################
def showNotification(title, msg, time=4):
	time *= 1000		# make into milliseconds
	cmdArg = '"%s","%s",%d' % (title, msg, time)
	xbmc.executebuiltin( "XBMC.Notification(" + cmdArg +")" )

#################################################################################################################
def dialogYesNo(title="", line1="", line2="",line3="", yesButton="", noButton=""):
	if not title:
		title = __language__( 0 )
	if not yesButton:
		yesButton= __language__( 402 )
	if not noButton:
		noButton= __language__( 403 )
	return xbmcgui.Dialog().yesno(title, line1, line2, line3, noButton, yesButton)

#################################################################################################################
def handleException(title="", msg="", msg2=""):
	xbmc.output( "handleException()" )
	try:
		dialogProgress.close()
		title += " EXCEPTION!"
		msg3 = str( sys.exc_info()[ 1 ] )
		traceback.print_exc()
	except: pass
	dialogOK(title, msg, msg2, msg3)

#################################################################################################################
def makeDir( dir ):
	try:
		os.makedirs(dir)
		xbmc.output( "made dir: " + dir)
		return True
	except:
		return False

#################################################################################################################
def deleteFile( file_name ):
	if fileExist(file_name):
		success = False
		urllib.urlcleanup()
		for count in range(3):
			try:
				os.remove( file_name )
				xbmc.output( "file deleted: " + file_name )
				success = True
				break
			except:
				xbmc.sleep(1000)
	else:
		success = True
	return success

#################################################################################################################
def searchRegEx(data, regex, flags=re.IGNORECASE):
	try:
		value = re.search(regex, data, flags).group(1)
	except:
		value = ""
	xbmc.output("searchRegEx() value: " + value)
	return value

######################################################################################
def readURL( url, msg='', isSilent=False):
	xbmc.output( "readURL() isSilent=%s %s" % (isSilent,url))

	if not isSilent:
		root, name = os.path.split(url)
		dialogProgress.create( __language__(0), msg, root, name )

	doc = None
	try:
		sock = urllib.urlopen( url )
		doc = sock.read()
		sock.close()
	except:
		traceback.print_exc()

	if not isSilent:
		dialogProgress.close()
	return doc

#################################################################################################################
def fileExist(filename):
	try:
		return os.path.exists(filename)
	except:
		return False

#################################################################################################################
class TextBoxDialogXML( xbmcgui.WindowXML ):
	""" Create a skinned textbox window """
	def __init__( self, *args, **kwargs):
		pass
		
	def onInit( self ):
		xbmc.output( "TextBoxDialogXML.onInit()" )
		self.getControl( 3 ).setLabel( self.title )
		self.getControl( 5 ).setText( self.text )

	def onClick( self, controlId ):
		pass

	def onFocus( self, controlId ):
		pass

	def onAction( self, action ):
#		print( "onAction(): actionID=%i buttonCode=%i " % ( action.getId(), action.getButtonCode()) )
		if action:
			if action.getButtonCode() in CANCEL_DIALOG or action.getId() in CANCEL_DIALOG:
				self.close()

	def ask(self, title, text ):
		xbmc.output("TextBoxDialogXML().ask()")
		self.title = title
		self.text = text
		self.doModal()		# causes window to be drawn

#################################################################################################################
def unzip(extract_path, filename, silent=False, msg=""):
	""" unzip an archive, using ChunkingZipFile to write large files as chunks if necessery """
	xbmc.output("> unzip() extract_path=" + extract_path + " filename=" + filename)
	success = False
	cancelled = False
	installed_path = ""

	zip=zipstream.ChunkingZipFile(filename, 'r')
	namelist = zip.namelist()
	names=zip.namelist()
	infos=zip.infolist()
	max_files = len(namelist)
	xbmc.output("max_files=%s" % max_files)

	for file_count, entry in enumerate(namelist):
		info = infos[file_count]

		if not silent:
			percent = int( file_count * 100.0 / max_files )
			root, name = os.path.split(entry)
			dialogProgress.update( percent, msg, root, name)
			if ( dialogProgress.iscanceled() ):
				cancelled = True
				break

		filePath = os.path.join(extract_path, entry)
		if filePath.endswith('/'):
			if not os.path.isdir(filePath):
				os.makedirs(filePath)
		elif (info.file_size + info.compress_size) > 25000000:
			xbmc.output( "LARGE FILE: f sz=%s  c sz=%s  reqd sz=%s %s" % (info.file_size, info.compress_size, (info.file_size + info.compress_size), entry ))
			outfile=file(filePath, 'wb')
			fp=zip.readfile(entry)
			fread=fp.read
			ftell=fp.tell
			owrite=outfile.write
			size=info.file_size

			# write out in chunks
			while ftell() < size:
				hunk=fread(4096)
				owrite(hunk)

			outfile.flush()
			outfile.close()
		else:
			file(filePath, 'wb').write(zip.read(entry))

	if not cancelled:
		success = True
		installed_path = os.path.join(extract_path, namelist[0][0:-1])
	
	zip.close()
	del zip
	xbmc.output("< unzip() success=" + str(success) + " installed_path=" + installed_path)
	return success, installed_path


#################################################################################################################
 # Script starts here
#################################################################################################################
RUNMODE_NORMAL = "NORMAL"
RUNMODE_NOTIFY = "NOTIFY"
RUNMODE_SILENT = "SILENT"
try:
	# get runMode as arg
	runMode = sys.argv[1].strip()
	if not runMode in [RUNMODE_NORMAL, RUNMODE_NOTIFY, RUNMODE_SILENT]:
		print "unknown runmode"
		raise
except:
	runMode = RUNMODE_NORMAL

Main(runMode)

xbmc.output("script exit and housekeeping")
# clean up on exit
moduleList = ['zipstream','SFVCheck']
for m in moduleList:
	try:
		del sys.modules[m]
		xbmc.output("removed module: " + m)
	except: pass

# remove globals
try:
	del dialogProgress
except: pass
