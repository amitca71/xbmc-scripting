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
import sys, os
import xbmc, xbmcgui
from sgmllib import SGMLParser
import urllib
import traceback
from string import lower, capwords
from shutil import copytree, rmtree, copy, move
import filecmp
import time
import re
import zipfile

# Script constants
__scriptname__ = "T3CH Upgrader"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__url__ = "http://code.google.com/p/xbmc-scripting/"
__svn_url__ = "http://xbmc-scripting.googlecode.com/svn/trunk/T3CH%20Upgrader"
__date__ = '19-06-2009'
__version__ = "1.9.3"
xbmc.log( "[SCRIPT]: %s v%s Dated: %s module loaded!" % (__scriptname__, __version__, __date__), xbmc.LOGNOTICE)

# Shared resources
DIR_HOME = os.getcwd().replace( ";", "" )
DIR_RESOURCES = os.path.join( DIR_HOME, "resources")
DIR_LIB = os.path.join( DIR_RESOURCES, "lib")
sys.path.append( DIR_RESOURCES )
sys.path.append( DIR_LIB )

# imports that rely on DIR_LIB being in sys path
import update
import zipstream
import SFVCheck

# Load Language using xbmc builtin
try:
	# 'resources' now auto appended onto path
	__language__ = xbmc.Language( DIR_HOME ).getLocalizedString
except:
	xbmcgui.Dialog.ok("XBMC Incompatible!", "Please update your XBMC build.", str(sys.exc_info()[ 1 ]))


dialogProgress = xbmcgui.DialogProgress()
EXIT_SCRIPT = ( 9, 10, 247, 275, 61467, )
CANCEL_DIALOG = EXIT_SCRIPT + ( 216, 257, 61448, )
TEXTBOX_XML_FILENAME = "DialogScriptInfo.xml"       # xbmc skin supplied textbox viewer

def log(msg, loglevel=xbmc.LOGDEBUG):
	try:
		xbmc.log("[%s]: %s" % (__scriptname__, msg), loglevel)
	except: pass

# check if build is special:// aware - set roots paths accordingly
XBMC_HOME = 'special://home'
XBMC_PROFILE = 'special://masterprofile'
if not os.path.isdir(xbmc.translatePath(XBMC_HOME)):	# if fails to convert to Q:, old builds
	XBMC_HOME = 'Q:'
	XBMC_PROFILE = 'T:'
log("XBMC_HOME=%s" % XBMC_HOME)
log("XBMC_PROFILE=%s" % XBMC_PROFILE)

#############################################################################################################
class T3CHParser( SGMLParser ):
	def reset( self ):
		self.url = None
		SGMLParser.reset( self )

	def start_a( self, attrs ):
		# check for SVN build
		for key, value in attrs:
			if ( key == "href" and value.find( "/STABLE/" ) == -1 and value.find( "ARCHIVE/" ) == -1 \
				and value.find( "/t3ch/XBMC-SVN" ) != -1 and value.find( ".rar" ) != -1 ):
				self.url = value
				log("T3CH build archive found! " + self.url)
				break

		if not self.url:
			# check for other build - maybe a stable?
			for key, value in attrs:
				if key == "href" and value.find( "/repository/" ) != -1 and value.find( "ARCHIVE/" ) == -1 \
					and value.find( "/XBMC-" ) != -1 and value.find( ".rar" ) != -1:
					self.url = value
					log("STABLE T3CH build archive found! " + self.url)
					break

#############################################################################################################
class Main:
	def __init__( self, runMode ):
		log("> __init__()")

		self.runMode = runMode
		log("runMode=" + str(runMode))
		self.isSilent = (runMode != RUNMODE_NORMAL)
		log("isSilent=" + str(self.isSilent))
		self.isT3CHbuilder = True

		self.HOME_URL_LIST = ("http://t3ch.yi.se/", "http://217.118.215.116/")
		self.FTP_URL_LIST = ("http://ftp1.srv.endpoint.nu/", "http://ftp3.srv.endpoint.nu/")
		self.FTP_REPOSITORY_URL = "pub/repository/t3ch/"
		self.FTP_REPOSITORY_ARCHIVE_URL = self.FTP_REPOSITORY_URL + "ARCHIVE/"

		# SVN Nightly builds
		URL_NIGHTLY_ROOT = "http://www.sshcs.com/xbmc/"
		URL_NIGHTLY_MODE = URL_NIGHTLY_ROOT + "inc/EVA.asp?mode="
		self.URL_NIGHTLY_BUILD_INFO = URL_NIGHTLY_MODE + "Build"
		self.URL_NIGHTLY_README = URL_NIGHTLY_MODE + "BNRaw"
#		self.URL_NIGHTLY_ARCHIVE = URL_NIGHTLY_MODE + "NDLC&FN=XBOX&BN="
		self.URL_NIGHTLY_ARCHIVE = URL_NIGHTLY_ROOT + "binaries/Builds/"

		# init settings folder
		SCRIPT_DATA_DIR = xbmc.translatePath("/".join( [XBMC_PROFILE, "script_data", __scriptname__] ))
		makeDir(SCRIPT_DATA_DIR)

		# SETTINGS
		self.SETTINGS_FILENAME = os.path.join( SCRIPT_DATA_DIR, "settings.txt" )
		self.SETTING_SHORTCUT_DRIVE = "shortcut_drive"
		self.SETTING_SHORTCUT_NAME = "dash_shortcut_name"
		self.SETTING_UNRAR_PATH = "unrar_path"
		self.SETTING_NOTIFY_NOT_NEW = "notify_when_not_new"
		self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP = "check_script_update_startup"
		self.SETTING_XFER_USERDATA = "transfer_userdata"
		self.SETTING_PROMPT_DEL_RAR = "prompt_del_rar"
		self.SETTING_CHECK_NEW_BUILD = "check_new_build"

		# COPY INCLUDES
		self.INCLUDES_FILENAME = os.path.join( SCRIPT_DATA_DIR, "includes.txt" )
		self.EXCLUDES_FILENAME = os.path.join( SCRIPT_DATA_DIR, "excludes.txt" )

		self._init_includes_excludes()
		self.settings = self._load_file_obj( self.SETTINGS_FILENAME, {} )

		self._check_settings()
		scriptUpdated = False
		if self.settings[self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP]:	# check for update ?
			scriptUpdated = self._update_script(True)

		if not scriptUpdated:
			remote_archive_name = ""
			remote_short_build_name = ""
			url = ""
			# only check for online new build if settings allow OR autoexec launched
			if (self.runMode != RUNMODE_NORMAL) or self.settings[self.SETTING_CHECK_NEW_BUILD]:
				url, remote_archive_name, remote_short_build_name = self._get_latest_version()		# discover latest build

			# Main Menu
			if (self.runMode == RUNMODE_NORMAL) or (remote_short_build_name and self.runMode == RUNMODE_SILENT):
				self._menu( url, remote_archive_name, remote_short_build_name )

		log("< __init__() done")


	######################################################################################
	def _check_settings( self, forceSetup=False ):
		log( "_check_settings() forceSetup=%s" % forceSetup)
		while forceSetup or not self._set_default_settings(False):
			self.isSilent = False							# come out of silent inorder to setup
			self._settings_menu()							# enter settings
			forceSetup = False								# cancel force entry, can now exit when ok

	######################################################################################
	def _set_default_settings( self, forceReset=False ):
		""" set settings to default values if not exist """
		log( "> _set_default_settings() forceReset="+str(forceReset) )
		success = True
		# __language__(402), # yes
		# __language__(403), # no

		items = {
			self.SETTING_CHECK_NEW_BUILD : True,
			self.SETTING_SHORTCUT_DRIVE : "C:\\",
			self.SETTING_SHORTCUT_NAME : "xbmc",
			self.SETTING_UNRAR_PATH : "E:\\apps",
			self.SETTING_NOTIFY_NOT_NEW :  False,
			self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP : True,
			self.SETTING_XFER_USERDATA : True,
			self.SETTING_PROMPT_DEL_RAR : True
			}

		for key, defaultValue in items.items():
			if forceReset or not self.settings.has_key( key ) or self.settings[key] in ("",None):
				self.settings[key] = defaultValue
				if not forceReset:
					log( "Using default value for setting: %s" % key )
					success = False
			elif key in (self.SETTING_CHECK_NEW_BUILD, self.SETTING_NOTIFY_NOT_NEW, \
						 self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP, self.SETTING_XFER_USERDATA, self.SETTING_PROMPT_DEL_RAR):
				# convert old settings that used YES, NO to True, False
				if not isinstance(self.settings[key], bool) or self.settings[key] not in (True, False):
					self.settings[key] = (self.settings[key] == __language__(402))	# yes = True
					log("translated old setting to bool. %s %s" % (key, self.settings[key]))
					success = False													# will force a save from menu

		log( "< _set_default_settings() success=%s" % success)
		return success
		
	######################################################################################
	def _load_file_obj( self, filename, dataType ):
		log( "_load_file_obj() " + filename)
		load_obj = None
		try:
			if os.path.isfile(filename):
				file_handle = open( filename, "r" )
				load_obj = eval( file_handle.read() )
				file_handle.close()
		except:
			handleException()

		if load_obj == None:
			log( "_load_file_obj() file missing, setting to empty.")
			if isinstance(dataType, dict):
				load_obj = {}
			elif isinstance(dataType, list):
				load_obj = []
			else:
				load_obj = None
		return load_obj

	######################################################################################
	def _save_file_obj( self, filename, save_obj ):
		log( "_save_file_obj() " + filename)
		try:
			file_handle = open( filename, "w" )
			file_handle.write( repr( save_obj ) )
			file_handle.close()
		except:
			handleException( "_save_file_obj()" )


	######################################################################################
	def _browse_for_path( self, heading, default_path='', dialog_type=3):
		log( "_browse_for_path() default_path=%s dialog_type=%s" % (default_path, dialog_type) )
		dialog = xbmcgui.Dialog()
		skinName = xbmc.getSkinDir()
		if skinName.find("MC360") >= 0:		# for just MC360
			dialogOK( __language__( 0 ), heading )
		return dialog.browse( dialog_type, heading, "files", '', False, False, default_path)

	######################################################################################
	def _pick_shortcut_drive( self):
		log( "_pick_shortcut_drive()" )
		options = [__language__(650), "C:\\", "E:\\", "F:\\"]
		selectDialog = xbmcgui.Dialog()
		selected = selectDialog.select( __language__( 202 ), options )
		if selected >= 1:
			return options[selected]
		else:
			return None

	######################################################################################
	def _browse_dashname(self, dash_name=''):
		log( "> _browse_dashname() curr dash_name="+dash_name)
		try:
			xbeFiles = [__language__(650), __language__(652)]

			# include current dash name into list after Exit and Manual
			xbeFiles.append(dash_name)

			# get shortcut drive to check for existing dash names
			try:
				drive = self.settings["shortcut_drive"]
			except:
				drive = "C:\\"
			log( "checking for names on drive=" + drive)
			# find all existing dash name
			for f in os.listdir( drive ):
				if f in ['.','..']: continue
				fn, ext = os.path.splitext(f)
				if fn != 'msdash' and (ext.lower() in ['.xbe','.cfg']):
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
				elif selected == 1:						# keyboard
					dash_name = getKeyboard(dash_name, __language__( 201 ))
					if dash_name and dash_name[-1] in ['\\','/']:
						dash_name = dash_name[:-1]
				else:									# selected from existing
					dash_name = xbeFiles[selected]

				if dash_name:
					break
				else:
					dialogOK(  __language__( 0 ), __language__( 309 ) )

		except:
			handleException("_browse_dashname()")
		log( "< _browse_dashname() final dash_name="+dash_name)
		return dash_name


	######################################################################################
	## eg. http://.../ARCHIVE/XBMC-SVN_2009-03-04_rev1 8221-T3CH.rar
	######################################################################################
	def _check_build_date( self, url ):
		log( "> _check_build_date() %s" % url )

		archive_name = ''
		short_build_name = ''
		try:
			# get system build date info
			curr_build_date_secs, curr_build_date = self._get_current_build_info()	# secs, YYYYMMDD

			# extract new build date from url archive name
			filenameInfo = self._get_archive_info(url)
			if filenameInfo:
				archive_name, found_build_date, found_build_date_secs, short_build_name = filenameInfo

				if curr_build_date_secs >= found_build_date_secs:							# No new build
					log("Build is older than current. Found: %s Current: %s" % (found_build_date, curr_build_date))
					archive_name = ''
					short_build_name = ''
					if self.settings[self.SETTING_NOTIFY_NOT_NEW]:							# notify of Not New
						dialogOK( __language__( 0 ), __language__( 517 ), isSilent=True )	# always use xbmc.notification
				elif self.runMode != RUNMODE_NORMAL:										# new build
					dialogOK( __language__( 0 ), __language__( 518 ), short_build_name, isSilent=True )	# always use xbmc.notification
		except:
			handleException("_check_build_date()")

		log("< _check_build_date() archive_name=%s short_build_name=%s" % (archive_name, short_build_name))
		return (archive_name, short_build_name)

	######################################################################################
	def _getBuilderName(self):
		return ( "SVN", "T3CH" )[self.isT3CHbuilder]

	######################################################################################
	def _get_archive_info(self, source):
		""" parse local file or url to get build info """
		log( "> _get_archive_info()")
		filenameInfo = ()
		orig_archive_name = os.path.basename( source )
		builder = self._getBuilderName()
		while not filenameInfo:
			try:
				# parse archive filename
				log( "parsing source=%s" % source)
				archive_name = os.path.basename( source )
				# extract date from filename, as YYYYMMDD
				found_build_date = self._parseArchiveName( archive_name )
				if found_build_date:
					# convert date to secs
					found_build_date_secs = time.mktime( time.strptime(found_build_date,"%Y%m%d") )
					short_build_name = "%s_%s" % (builder, found_build_date)		# used as installation folder name
					filenameInfo = (orig_archive_name, found_build_date, found_build_date_secs, short_build_name)
			except:
				print str( sys.exc_info()[ 1 ] )

			if not filenameInfo:
				# unable to parse, ask for save name with a date
				if dialogYesNo( __language__(0), __language__(321), archive_name, __language__(535) + " ?"):
					title = "%s. (YYYYMMDD)" % __language__(535)
					fname, fext = os.path.splitext(archive_name)
					source = "%s_%s.%s" % (builder, getKeyboard("", title), fext )
				else:
					filenameInfo = ()
					break
		log(filenameInfo)
		log("< _get_archive_info()")
		return filenameInfo

	######################################################################################
	def _menu( self, url, remote_archive_name="", remote_short_build_name="" ):
		log( "> _menu() url=%s" % url )
		log( "remote_archive_name=" + remote_archive_name)
		log( "remote_short_build_name=" + remote_short_build_name)

		recheckOnline = False
		selectDialog = xbmcgui.Dialog()
		heading = "%s v%s (XBMC:%s): %s" % (__language__( 0 ), __version__, \
												xbmc.getInfoLabel('System.BuildDate'), \
												__language__( 600 ))

		def _make_menu(local_archive_name=''):
			log("_make_menu()")
			self.opt_exit = __language__(650)
			self.opt_view_logs = __language__(611)
			# if archive name, show it on menu for download
			# if not checked show Check Now
			# else show Not Found
			if remote_archive_name:
				self.opt_download = "%s  %s"  % (__language__(612), remote_archive_name)# download w/ rar name
			elif self.settings[self.SETTING_CHECK_NEW_BUILD]:
				self.opt_download = "%s  %s"  % (__language__(612),__language__(517))	# no new build
			else:
				self.opt_download = "%s"  % __language__(622)							# Check Now

			self.opt_builder = "%s  %s" % ( __language__(623), ( __language__(417), __language__(411) )[self.isT3CHbuilder] )
			self.opt_maint_copy = __language__(615)
			self.opt_maint_del = __language__(618)
			self.opt_switch = __language__(616)
			self.opt_del_build = __language__(617)
			self.opt_settings = __language__(610)
			self.opt_local = "%s  %s" % (__language__(620), local_archive_name)

			options = [self.opt_exit,
					   self.opt_builder,
					   self.opt_view_logs,
					   self.opt_download,
					   self.opt_local,
					   self.opt_maint_copy,
					   self.opt_maint_del,
					   self.opt_switch,
					   self.opt_del_build,
					   self.opt_settings
					   ]

			# remove local install opt if no archive found
			if not local_archive_name:
				options.remove(self.opt_local)

			return options

		quit = False
		while not quit:
			# Only include found rar if not a result of a previous cancelled download, as may be partial.
			local_archive_name = ''
			local_short_build_name = ''
			archive_list = []
			if not self.isSilent:
				archive_list = self._get_local_archive()
				if len(archive_list) == 1:
					local_archive_name = archive_list[0]
				elif len(archive_list) > 1:
					local_archive_name = __language__(536)		# choose multiple

			# fetch remote archive name (if not got it & settings allow)
			if recheckOnline:
				url, remote_archive_name, remote_short_build_name = self._get_latest_version()
				recheckOnline = False

			# build menu
			options = _make_menu(local_archive_name)

			# show menu
			if not self.isSilent:
				selectedIdx = selectDialog.select( heading, options )
				log("menu selectedIdx=%s" % selectedIdx)
				if selectedIdx <= 0:		# quit
					return
				selectedOpt = options[selectedIdx]
			else:
				selectedOpt = self.opt_download											# force process

			if selectedOpt == self.opt_exit:
				break
			elif selectedOpt == self.opt_builder:										# switch XBMC Builder
				self.isT3CHbuilder = not self.isT3CHbuilder
				# reset archiv info so causes to re-fetch
				remote_archive_name = ""
				remote_short_build_name = ""
				recheckOnline = True
			elif selectedOpt == self.opt_view_logs:										# view logs
				self._doc_menu()
			elif selectedOpt == self.opt_download:										# Download
				if remote_archive_name:
					self.archive_name = remote_archive_name
					self.short_build_name = remote_short_build_name
					# ask if to just DL or DL & install ?
					downloadOnly = dialogYesNo( __language__( 0 ), __language__( 533 ), \
						yesButton=__language__( 400 ), noButton=__language__( 416 ))

					if self._process(url, useSFV=self.isT3CHbuilder, downloadOnly=downloadOnly):
						if not downloadOnly:
							if self.isSilent or dialogYesNo( __language__( 0 ), __language__( 512 )):		# reboot ?
								xbmc.executebuiltin( "XBMC.Reboot" )
							break
					else:
						self.isSilent = False											# failed, show menu
					if self.isSilent:
						break
				elif selectedOpt == __language__(622):									# Check for build
					recheckOnline = True
			elif selectedOpt == self.opt_local:											# local archive install
				if len(archive_list) == 1:
					local_rar_file = archive_list[0]
				else:
					local_rar_file = ""
					selectDialog = xbmcgui.Dialog()
					selectedPos = selectDialog.select( __language__( 536 ), archive_list )
					if selectedPos >= 0:
						local_rar_file = archive_list[selectedPos]
				if local_rar_file:
					local_archive_name, found_build_date, found_build_date_secs, local_short_build_name = self._get_archive_info(local_rar_file)
					if local_archive_name:
						self.archive_name = local_archive_name
						self.short_build_name = local_short_build_name
						if self._process('', False, False):
							if dialogYesNo( __language__( 0 ), __language__( 512 )):		# reboot ?
								xbmc.executebuiltin( "XBMC.Reboot" )
							quit = True
			elif selectedOpt == self.opt_maint_copy:									# copy includes
				self._maintain_incl_excl(True)
			elif selectedOpt == self.opt_maint_del:										# delete excludes
				self._maintain_incl_excl(False)
			elif selectedOpt == self.opt_switch:										# change to another t3ch
				quit = self._switch_builds_menu()
			elif selectedOpt == self.opt_del_build:										# delete old t3ch
				self._delete_old_build()
			elif selectedOpt == self.opt_settings:										# settings
				quit = self._check_settings(forceSetup=True)

		log( "< _menu() quit=%s" % quit)

	#####################################################################################
	def _switch_builds_menu(self):
		log( "> _switch_builds_menu() ")

		reboot = False
		selectedBuildName = ''

		while not selectedBuildName:
			# find all LOCAL installed t3ch builds dirs
			buildsList = self._find_build_dirs()
			if self.isT3CHbuilder:
				buildsList.insert(0, __language__( 621 ))		# select old web build archive
			buildsList.insert(0, __language__( 650 ))			# exit - 1st option
			
			# select
			selectDialog = xbmcgui.Dialog()
			selected = selectDialog.select( __language__( 616 ), buildsList )
			if selected <= 0:							# quit
				break
			
			if self.isT3CHbuilder and selected == 1:							# web build archive
				self._web_builds_menu()
			else:
				selectedBuildName = buildsList[selected]
				# do build switch by writing path into Shortcut
				path = os.path.join( self.settings[ self.SETTING_UNRAR_PATH ], selectedBuildName)
				if self._update_shortcut(path):
					if dialogYesNo( __language__( 0 ), __language__( 512 )):				# reboot ?
						reboot = True
						xbmc.executebuiltin( "XBMC.Reboot" )

		log( "< _switch_builds_menu() ")
		return reboot

	######################################################################################
	def _parseArchiveName(self, name):
		# restrict archives to the selected builder
		if self.isT3CHbuilder:
			date = searchRegEx(name.replace('-',''), '(?:XBMC|T3CH).*(\d\d\d\d\d\d\d\d).*?(?:.rar|.zip)')
		else:
			date = searchRegEx(name, '(?:SVN|XBMC_XBOX).*(\d\d\d\d\d\d\d\d).*?(?:.rar|.zip)')
		log("_parseArchiveName() from=%s  date=%s" % (name, date))
		return date

	######################################################################################
	def _get_local_archive(self):
		""" return list of archives found in install dir. """
		log("> _get_local_archive()")
		archive_list = []
		try:
			unrar_path = self.settings[self.SETTING_UNRAR_PATH]
			log("SETTING_UNRAR_PATH=" + unrar_path)
			for f in os.listdir( unrar_path ):
				if f in ('.','..'): continue
				filepath = os.path.join(unrar_path, f)
				if os.path.isfile(filepath) and self._parseArchiveName(f):
					# assume local build rars under a certain size are partial downloads and delete them
					fsize = os.path.getsize(filepath)
					if fsize < 30000000:
						log("deleting suspected incompleted rar, fsize=%s %s" % (fsize, filepath))
						deleteFile(filepath)
					else:
						archive_list.append(f)

			# sort to get latest
			if archive_list and len(archive_list) > 1:
				archive_list.sort()
				archive_list.reverse()
		except:
			traceback.print_exc()
		log("< _get_local_archive() count=%s" % len(archive_list))
		return archive_list


	######################################################################################
	def _check_sfv(self, archive_local_filepath):
		""" Download SFV for latest T3CH build, then check against RAR """
		log( "> _check_sfv()" )
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
				log("checking sfv entry for %s %s" % (split_name, archive_local_filepath))
				sfv = SFVCheck.SFVCheck(sfvDoc=doc)
				success = sfv.check(split_name, archive_local_filepath)
				if success == None:
					# entry name not found, try with full name+ext
					success = sfv.check(self.archive_name, archive_local_filepath)

		if success == None:		# filename entry not found in SFV doc
			success = dialogYesNo( __language__( 0 ), __language__( 320 ) )
		elif not success:
			dialogOK( __language__( 0 ), __language__(315) )
		log( "< _check_sfv() success=%s" % success)
		return success

	######################################################################################
	# processAction: 0 = Download & install, 1 = Install Existing, 2 = Download only
	######################################################################################
	def _check_free_mem(self, driveSpaceRequiredMb=180, ramCheck=True):
		""" check installation drive has enough freespace and enough free ram """
		log( "> _check_free_mem() driveSpaceRequiredMb=%s ramCheck=%s" % (driveSpaceRequiredMb, ramCheck))

		success = False
		drive = os.path.splitdrive( self.settings[self.SETTING_UNRAR_PATH] )[0][0]	# eg C from (C:, path)
		drive_freespace_info = xbmc.getInfoLabel('System.Freespace(%s)' % drive)

		# convert info to MB
		drive_freespaceMb = int(searchRegEx(drive_freespace_info, '(\d+)'))		# extract space number
		log("Drive=%s  Freespace=%sMB  Required=%sMB" % (drive, drive_freespaceMb, driveSpaceRequiredMb))

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
			log( "Freemem=%sMB  Recommended=%sMB" % ( freememMb, freeMemRecMb ) )
			if freememMb < freeMemRecMb:
				msg = __language__( 531 ) % (freememMb, freeMemRecMb)
				success = xbmcgui.Dialog().yesno( __language__( 0 ), __language__(317), msg, __language__(532) )
			else:
				success = True

		log( "< _check_free_mem() success=%s" % success)
		return success

	######################################################################################
	def _process( self, url='', useSFV=True, downloadOnly=False ):
		""" Download, Extract and Install new build, from a url or local archive """
		log( "> _process() url=%s useSFV=%s downloadOnly=%s" % (url, useSFV, downloadOnly))

		success = False
		try:
			# ensure remote filename doesnt exceed xbox filesystem local filename length limit
			if url and ( not self.isT3CHbuilder or len(self.archive_name) > 42):
				# use shortened save filename
				name, ext = os.path.splitext(self.archive_name)				# T3CH and Nigthly both are rars, find just to be safe
				archive_name = "%s%s" % (self.short_build_name, ext)		# eg SVN_20090617.rar or T3CH_20090617.rar
				log("renamed saving archive_name from %s to %s" % (self.archive_name, archive_name))
			else:
				archive_name = self.archive_name							# use existing local archive filename

			# create work paths
			extract_path = os.path.join( self.settings[ self.SETTING_UNRAR_PATH ], self.short_build_name)
			log( "extract_path= " + extract_path )
			archive_file = os.path.join( self.settings[ self.SETTING_UNRAR_PATH ], archive_name )
			log( "archive_file= " + archive_file )

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
				log("< _process() success=False")
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

			log( "OK to continue using archive file? %s" % have_file)
			if downloadOnly:
				success = True
			elif have_file:
				if self._extract( archive_file, extract_path ):

					if self.isSilent or dialogYesNo( __language__( 0 ), __language__( 507 ), __language__( 508 ), "" ):

						if not self.isSilent:
							dialogProgress.create( __language__( 0 ) )

						if self.settings[self.SETTING_XFER_USERDATA]:
							success = self._copy_user_data(extract_path)
						else:
							success = True

						if success:
							# do Custom Copies
							self._copy_includes()

							# do Custom Deletes
							self._delete_excludes()

						if not self.isSilent:
							dialogProgress.close()

					# update shortcuts ?
					if success:
						success = self._update_shortcut(extract_path)		# create shortcut

						# del rar according to del setting
						if fileExist(archive_file):
							# always del if no prompt reqd or isSilent
							if self.isSilent or not self.settings[self.SETTING_PROMPT_DEL_RAR] or \
								dialogYesNo( __language__( 0 ), __language__( 528 ), archive_file, \
											yesButton=__language__( 412 ), noButton=__language__( 413 )):
								deleteFile(archive_file)					# remove RAR
		except:
			handleException("process()")
		log("< _process() success=%s" % success)
		return success

	######################################################################################
	def _init_includes_excludes(self, forceReset=False):
		log("_init_includes_excludes() forceReset=%s" % forceReset)

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
			log("includes; removed 'plugins\\'")
			changed = True
		except: pass
		if forceReset or changed:
			self._save_file_obj(self.INCLUDES_FILENAME, self.includes)

		changed = self._hardcoded_excludes()
		if forceReset or changed:
			self._save_file_obj(self.EXCLUDES_FILENAME, self.excludes)

	######################################################################################
	def _hardcoded_includes(self):
		""" Additional files/folders for post installation copying. All relative to XBMC root """
		log("_hardcoded_includes()")
		changed = False
		# add if not already included
		srcList = [ "skin\\", "screensavers\\", "scripts\\", "plugins\\video", "plugins\\pictures", \
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
		log("_hardcoded_excludes()")
		changed = False
		srcList = [ "..\\_tools", "..\\win32", "..\\Changelog.txt", "..\\copying.txt", "..\\keymapping.txt" ]
		for src in srcList:
			if src not in self.excludes:
				self.excludes.append(src)
				changed = True
		return changed

	######################################################################################
	def _get_latest_version( self ):
		log( "> _get_latest_version()" )
		url = ""
		remote_archive_name = ""
		remote_short_build_name = ""
		if self.isT3CHbuilder:
			# T3CH
			for baseUrl in self.HOME_URL_LIST:
				doc = readURL( baseUrl, __language__( 502 ), self.isSilent )
				if doc:
					url = self._parse_html_source( doc )
					break

			if url:
				remote_archive_name, remote_short_build_name = self._check_build_date( url )
				# not a new build, cancel url
				if not remote_archive_name:
					url = ""
		else:
			# SVN Nightly
			url, remote_archive_name, rev, buildDate = self._get_nightly_archive_info()
			if url and remote_archive_name and rev and buildDate:
				remote_short_build_name = "SVN_%s" % buildDate

#		if not url:
#			dialogOK( __language__( 0 ), self._getBuilderName(), __language__( 301 ), isSilent=self.isSilent)
		log( "< _get_latest_version() url=%s  remote_archive_name=%s  remote_short_build_name=%s" % (url, remote_archive_name, remote_short_build_name))
		return (url, remote_archive_name, remote_short_build_name)

	######################################################################################
	def _get_nightly_archive_info(self):
		log( "> _get_nightly_archive_info()" )
		# get page that has revision and date (XXXXX YYYYMMDD)
		url = self.URL_NIGHTLY_BUILD_INFO
		doc = readURL( url, __language__( 502 ), self.isSilent )
		matches = re.search("^(\d+) (\d+)$", doc)		# rev, date
		if matches:
			rev = matches.group(1)
			buildDate = matches.group(2)
			fn = "XBMC_XBOX_%s.rar" % rev
			url = self.URL_NIGHTLY_ARCHIVE + fn
		else:
			dialogOK(__language__( 0 ), "Archive build information not found!", url)
			url = ""
			fn = ""
			buildDate = ""
			rev = ""
		log( "< _get_nightly_archive_info() url=%s fn=%s rev=%s builddate=%s"  % (url, fn, rev, buildDate))
		return (url, fn, rev, buildDate)

	######################################################################################
	def _parse_html_source( self, htmlsource ):
		try:
			parser = T3CHParser()
			parser.feed( htmlsource )
			parser.close()
			log("_parse_html_source() url=%s" % parser.url)
			return parser.url
		except:
			handleException("_parse_html_source()", __language__( 305 ))
			return ""

	######################################################################################
	def _fetch_current_build( self, url, file_name ):
		log( "> _fetch_current_build() %s -> %s" % (url, file_name) )
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
			if not fileExist(file_name) or os.path.getsize(file_name) < 30000000:
				dialogProgress.close()
				dialogOK(__language__( 0 ), "File not found or failed download!", file_name)
				deleteFile(file_name)
			else:
				success = True
		except:
			traceback.print_exc()
			dialogProgress.close()
			dialogOK( __language__( 0 ), __language__( 303 ), isSilent=self.isSilent )

		urllib.urlcleanup()
		log("< _fetch_current_build() success=%s " % (success))
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
		log( "> _extract() file_name=%s extract_path=%s"  % (file_name, extract_path))
		success = False

		# check extract destination folder doesnt exist
		if os.path.exists(extract_path):
			# ask to overwrite 
			if not dialogYesNo(__language__( 0 ), __language__( 314 ), extract_path, \
							yesButton=__language__( 402 ), noButton=__language__( 403 )):
				log( "< _extract() no overwrite. False")
				return False

		# use a new dialog cos an update shows an empty bar that ppl expect to move
		if not self.isSilent:
			dialogProgress.create( __language__( 0 ), __language__( 504 ), extract_path )
		else:
			showNotification(__language__( 0 ), "%s %s" % (__language__( 504 ), extract_path), 60 )

		# determine which extract to do, RAR (xbmc builtin) or ZIP (Python module)
		try:
			fsize = os.path.getsize(file_name)
			if file_name.endswith("rar"):
				log("RAR filetype... fsize=%s" % fsize)
				if fsize > 69000000 and not dialogYesNo( __language__( 0 ), __language__( 322 ) ):
					success = False
				else:
					log("extraction started")
					xbmc.executebuiltin( "XBMC.extract(%s,%s)" % ( file_name, extract_path, ), )
					log("extraction finished")
					success = True
			else:
				log("ZIP filetype... fsize=%s" % fsize)
				# unpack ZIP, then rename to reqd short path name
				success, installed_path = unzip(self.settings[ self.SETTING_UNRAR_PATH ], file_name, self.isSilent, __language__(504))
				if success:
					if os.path.isdir(extract_path):
						removeTree(extract_path)

					for retry in range(3):
						try:
							time.sleep(2)
							os.rename(installed_path, extract_path)
							log("ZIP install: renamed %s to %s" % (installed_path, extract_path))
							break
						except: pass

		except:
			handleException("_extract()")
			success = False

		if success:
			success = self._check_extract(extract_path)
			dialogProgress.close()
			if not success:
				# remove partial extract
				removeTree(extract_path)
				dialogOK( __language__( 0 ), __language__( 312 ), extract_path )

		dialogProgress.close()
		log( "< _extract() success=%s" % success )
		return success

	######################################################################################
	def _check_dir_exists(self, dir, max_retrys=5):
		log("> _check_dir_exists() " + dir)
		exists = False

		for count in range(max_retrys):
			if os.path.isdir(dir):
				exists = True
				break
			else:
				percent = int( (count * 100.0) / max_retrys )
				msg1 = "%s (%d/%d)" % (__language__( 522 ), count, max_retrys)
				dialogProgress.update( percent, msg1, dir)
				if ( dialogProgress.iscanceled() ): break
				time.sleep(1)
		log("< _check_dir_exists() exists=%s" % exists)
		return exists

	######################################################################################
	def _check_extract(self, extract_path):
		log( "> _check_extract() extract_path=" + extract_path)
		success = False

		# inform user of os path checking
		if not self.isSilent:
			self._dialog_update( __language__(0), __language__( 522 ))

		if self._check_dir_exists(extract_path):
			# got root dir (may be a subsolder)
			check_base_path = self._get_extraction_root(extract_path)
			if check_base_path:
				log("Root dir exists, checking for other dirs...")
				check_file = os.path.join(check_base_path,'default.xbe' )
				check_path_list = ( os.path.join(check_base_path,'UserData'),
									os.path.join(check_base_path,'system'),
									os.path.join(check_base_path,'skin'),
									os.path.join(check_base_path,'media'),
									os.path.join(check_base_path,'language'),
									os.path.join(check_base_path,'sounds') )

				# loop to find other mandatory dirs
				MAX = 30
				isFile = False
				isPath = False
				for count in range(MAX):
					if not isFile:
						isFile = fileExist(check_file)
					for p in check_path_list:
						isPath = os.path.isdir(p)
						log("%s %s" % (p, isPath))
						if not isPath:
							break
					log("checkCount=%d isPath=%s isFile=%s" % (count,isPath,isFile))

					if isFile and isPath:
						success = True
						break
					elif not self.isSilent:
						percent = int( (count * 100.0) / MAX )
						msg1 = "%s (%d/%d)" % (__language__( 522 ), count, MAX)
						msg2 = "%s  %s" % (__language__(526), str(isPath))
						msg3 = "%s  %s" % (__language__(527), str(isFile))
						dialogProgress.update( percent, msg1, msg2, msg3)
						if ( dialogProgress.iscanceled() ): break
					time.sleep(2)

				# all paths exist, rename out of a subdir if necessary
				expectedPath = os.path.join(extract_path, 'XBMC')
				if success and check_base_path and check_base_path != expectedPath:
					success = self._extractionRename(check_base_path, expectedPath)
		dialogProgress.close()
		log( "< _check_extract() success=%s" % success )
		return success

	######################################################################################
	def _extractionRename(self, currPath, expectedPath):
		""" Check if installation is within a further sub-folder, then move to expected folder """
		log("> _extractionRename() currPath=" + currPath)
		ok = False

		if currPath == expectedPath:
			log("extraction root path as expected")
			ok = True
		else:
			max_retrys = 5
			for count in range(max_retrys):
				try:
					log("count: %d  renaming %s to %s" % (count, currPath, expectedPath))
					time.sleep(1)
					os.chmod(currPath, 0777)
					os.rename(currPath, expectedPath)
					log("rename done")
					break
				except:
					print str(sys.exc_info()[ 1 ])
					percent = int( (count * 100.0) / max_retrys )
					msg1 = "%s (%d/%d)" % ("Renaming folder ... :", count, max_retrys)
					dialogProgress.update( percent, msg1, currPath, expectedPath)

			try:
				# after rename, remove unwanted path
				time.sleep(1)
				if os.path.isdir(expectedPath):
					# discover root of paths then delete if not as expected.
					# eg for E:\\apps\\T3CH_20090501\\unwanted_dir\\XBMC"
					# removes "E:\\apps\\T3CH_20090501\\unwanted_dir"

					currPathSplit = os.path.split(currPath)[0]
					expectedPathSplit = os.path.split(expectedPath)[0]
					if currPathSplit != expectedPathSplit:
						removeTree(currPathSplit)
					ok = True
			except:
				handleException("_extractionRename()", "Removing path:", currPath)

		log("< _extractionRename() ok=%s" % ok)
		return ok

	######################################################################################
	def _get_extraction_root(self, extract_path):
		log( "> _get_extraction_root() extract_path=" + extract_path)
		# check if our expected installation root is inside an unwanted folder

		base_path = ""
		base_pathXBMC = os.path.join(extract_path, 'XBMC')
		base_pathBUILD = os.path.join(extract_path, 'BUILD')
		if os.path.isdir(base_pathXBMC):
			base_path = base_pathXBMC
		elif os.path.isdir(base_pathBUILD):
			base_path = base_pathBUILD
		else:
			for entry in os.listdir(extract_path):
				if entry in ('.','..'): continue

				base_pathXBMC = os.path.join(extract_path, entry, "XBMC")
				base_pathBUILD = os.path.join(extract_path, entry, "BUILD")
				if os.path.isdir(base_pathXBMC):
					base_path = base_pathXBMC
				elif os.path.isdir(base_pathBUILD):
					base_path = base_pathBUILD
				if base_path:
					break

		log( "< _get_extraction_root() base_path=" + base_path)
		return base_path

	######################################################################################
	def _fetch_xbmc_trac_changelog( self ):
		log( "_fetch_xbmc_trac_changelog()" )
		doc = ""
		url = "http://xbmc.org/trac/timeline?changeset=on&milestone=on&max=50&daysback=90&format=rss"
		rss = readURL( url, __language__( 502 ), self.isSilent )
		if rss:
			# parse rss into a doc
			regex = "<item>.*?<title>(.*?)</.*?creator>(.*?)</.*?pubDate>(.*?)</.*?<description>(.*?)</"
			findRe = re.compile(regex, re.DOTALL + re.MULTILINE + re.IGNORECASE)
			matches = findRe.findall(rss)
			for match in matches:
				title = match[0]
				who = match[1]
				when = match[2]
				desc = match[3].replace("&lt;","<").replace("&gt;",">").replace("&quot;","'").replace("&amp;","&").replace("<p>","").replace("</p>","")
				doc += "%s   |   %s\n%s\n%s" % (when, who, title, desc)
				doc += "-----------------------------------------------------------------------\n"
			
		return doc

	######################################################################################
	def _fetch_script_doc( self, viewReadme):
		log( "_fetch_script_doc() viewReadme=%s" % viewReadme)
		if viewReadme:		# readme
			title = "%s: %s" % (__language__(0), __language__(414))

			# determine language path
			base_path, language = getLanguagePath()
			fn = os.path.join( base_path, language, "readme.txt" )
			if ( not fileExist( fn ) ):
				fn = os.path.join( base_path, "English", "readme.txt" )
		else:
			# changelog
			title = "%s: %s" % (__language__(0), __language__(415))
			fn = os.path.join(DIR_HOME, "changelog.txt")

		# read and display
		if not fileExist(fn):
			doc = "File is missing! " + fn
		else:
			doc = file(fn).read()
		return doc

	######################################################################################
	def _doc_menu(self):
		log("_doc_menu")
		options = [ __language__(650),
					"T3CH: " + __language__( 414 ),
					"T3CH: " + __language__( 415 ),
					"%s: %s" % (  __language__( 417 ), __language__( 414 ) ),
					"XBMC TRAC: " + __language__( 415 ),
					"%s: %s" % (__language__(0), __language__(414)),
					"%s: %s" % (__language__(0), __language__(415)) ]

		selectDialog = xbmcgui.Dialog()
		while True:
			doc = ""
			url = ""
			selectedIdx = selectDialog.select( __language__(611), options )
			if selectedIdx <= 0:
				break
			elif selectedIdx == 1:
				url = "%s%sT3CH-README_1ST.txt" % (self.FTP_URL_LIST[0], self.FTP_REPOSITORY_URL)
			elif selectedIdx == 2:
				url = "%sChangelog.txt" % self.HOME_URL_LIST[0]
			elif selectedIdx == 3:
				url = self.URL_NIGHTLY_README
			elif selectedIdx == 4:
				doc = self._fetch_xbmc_trac_changelog()
			elif selectedIdx in (5, 6):
				doc = self._fetch_script_doc(viewReadme=(selectedIdx == 5))

			if url:
				doc = readURL( url, __language__( 502 ), self.isSilent )
			if doc:
				tbd = TextBoxDialogXML(TEXTBOX_XML_FILENAME, DIR_HOME, "Default")
				tbd.ask(options[selectedIdx], doc.replace("<BR>","\n").replace("<P>","").replace("&nbsp;"," "))
				del tbd
			else:
				dialogOK( __language__( 0 ), __language__( 310 ))

	######################################################################################
	def _copy_user_data(self, extract_path):
		log( "> _copy_user_data() to " + extract_path )
		success = False

		try:
			curr_build_userdata_path = xbmc.translatePath(XBMC_PROFILE + '/')
			log("curr_build_userdata_path=" + curr_build_userdata_path)
			new_build_userdata_path = os.path.join( extract_path, "XBMC", "userdata")
			log("new_build_userdata_path=" + new_build_userdata_path)

			# remove new build UserData
			checkMAX = 15
			checkCount = 0
			while os.path.isdir(new_build_userdata_path):
				log("rmtree UserData checkCount=%i" % checkCount)
				checkCount += 1
				percent = int( (checkCount * 100.0) / checkMAX )
				self._dialog_update( __language__(0), __language__( 510 ), pct=percent, time=2)
				rmtree( new_build_userdata_path, ignore_errors=True )
				time.sleep(2)	# give os chance to complete

				if (checkCount > checkMAX) and os.path.isdir(new_build_userdata_path):
					checkCount = 0
					if not dialogYesNo( __language__(0), "Failed to remove new XBMC User Data, Retry?"):
						break

			# Copytree current UserData to new build
			if not os.path.isdir(new_build_userdata_path):
				try:
					log("copytree UserData %s -> %s" % (curr_build_userdata_path,new_build_userdata_path) )
					self._dialog_update( __language__(0), __language__( 511 ), time=2) 
					copytree( curr_build_userdata_path, new_build_userdata_path )
					success = True
				except:
					traceback.print_exc()
					dialogOK("CopyTree on UserData Error",curr_build_userdata_path, new_build_userdata_path,str(sys.exc_info()[ 1 ]))
		except:
			handleException("_copy_user_data()", __language__( 306 ))
		log( "< _copy_user_data() success=%s" % success )
		return success


	######################################################################################
	def _update_shortcut(self, extract_path):
		log( "> _update_shortcut() " +extract_path )

		success = False
		# get users prefered booting dash name eg. XBMC.xbe
		# if required, copy SHORTCUT by TEAM XBMC to root\<dash_name>
		dash_name = self.settings[self.SETTING_SHORTCUT_NAME]
		shortcut_drive = self.settings[self.SETTING_SHORTCUT_DRIVE]
		shortcut_xbe_file = os.path.join( shortcut_drive, dash_name + ".xbe" )
		log( "shortcut_xbe_file= " + shortcut_xbe_file )
		shortcut_cfg_file = os.path.join( shortcut_drive, dash_name + ".cfg" )
		log( "shortcut_cfg_file= " + shortcut_cfg_file )

		# backup CFG shortcut
		if fileExist( shortcut_cfg_file ):
			copy( shortcut_cfg_file, shortcut_cfg_file + "_old" )
			log( "backup of cfg made to _old" )

		# if shortcutname has dir prefix, ensure it exists
		prefix_dir = os.path.dirname(shortcut_xbe_file)
		log("prefix_dir="+prefix_dir)
		if prefix_dir and not os.path.isdir(prefix_dir):
			makeDir(prefix_dir)

		# check if TEAM XBMC shortcut needs copying
		copy_xbe = True
		src_xbe_file = os.path.join( DIR_RESOURCES, "SHORTCUT by TEAM XBMC.xbe" )
		if fileExist( shortcut_xbe_file ):
			# DOES EXIST, check if diff
			if not filecmp.cmp( src_xbe_file, shortcut_xbe_file ):
				log( "Shortcuts differ. Backup shortcut XBE: copy %s -> %s" % (shortcut_xbe_file, shortcut_xbe_file + "_old"))
				copy( shortcut_xbe_file, shortcut_xbe_file + "_old" )
			else:
				copy_xbe = False		# same file, no copy reqd

		# create new shortcut cfg path - this points to the new XBMC build xbe
		log("extra check for new paths default xbe ...")
		boot_path = os.path.join(extract_path, "XBMC", "default.xbe")
		if not os.path.isfile(boot_path):
			dialogOK(__language__(0), "Unable to locate default.xbe in", extract_path, "Update Shortcut aborted!")
		else:
			try:
				# write new cfg to .CFG_NEW
				shortcut_cfg_file_new = shortcut_cfg_file + "_new"
				log( "shortcut_cfg_file_new= " + shortcut_cfg_file_new )
				# delete any existing .CFG_NEW
				deleteFile(shortcut_cfg_file_new)
				log( "write '%s' into file %s" % (boot_path, shortcut_cfg_file_new) )
				file(shortcut_cfg_file_new,'w').write(boot_path)

				# switch to new cfg now ?
				log( "Copy TEAM XBMC xbe required? %s" % copy_xbe)
				if self.isSilent or dialogYesNo( __language__( 0 ), __language__( 519 ), __language__( 520 ),__language__( 521  ),yesButton=__language__( 404 ), noButton=__language__(405) ):
					# copy TEAM XBMC shortcut xbe into place (if reqd)
					if copy_xbe:
						log( "TEAM XBMC xbe: copy %s -> %s" % (src_xbe_file, shortcut_xbe_file))
						copy(src_xbe_file, shortcut_xbe_file)

					log( "AUTO cfg copies: copy %s -> %s" % (shortcut_cfg_file_new, shortcut_cfg_file) )
					copy(shortcut_cfg_file_new, shortcut_cfg_file)
					time.sleep(1)
					success = True
				else:
					log( "MANUAL cfg copies" )
			except:
				handleException("_update_shortcut()", __language__( 307 ))

		log( "< _update_shortcut() success=%s" % success )
		return success

	######################################################################################
	def _copy_folder(self, src_path, dest_path):
		log( "_copy_folder() src_path=" + src_path + " dest_path=" + dest_path)

		try:
			# check source folder exists!
			if not os.path.exists( src_path ):
				log( "source folder doesnt exist, abort copy!" )
				return

			# start copy of source tree
			self._dialog_update( __language__(0), __language__( 515 ), src_path) 
			# make dest root folder otherwise copytree will fail
			makeDir( dest_path )

			files = os.listdir(src_path)
			TOTAL = len(files)
			for count, f in enumerate(files):
				# ignore parent dirs
				if f in ['.','..']: continue

				src_file = os.path.join( src_path, f )
				dest_file = os.path.join( dest_path, f )

				if not fileExist( dest_file ):
					if not self.isSilent:
						percent = int( (count * 100.0) / TOTAL )
						dialogProgress.update( percent, __language__( 515 ), src_file)
						if dialogProgress.iscanceled(): break
					if os.path.isdir( src_file ):
						# copy directory
						copytree( src_file, dest_file )
						log("copied tree OK " + src_file)
					else:
						# copy file
						copy( src_file, dest_file )
						log("copied file OK " + src_file)
				else:
					log( "ignored as exists: " + dest_file)
		except:
			handleException("_copy_folder()", __language__( 308 ))

	######################################################################################
	def _copy_includes(self): 
		log( "_copy_includes() ")

		TOTAL = len(self.includes)
		extract_path = self.settings[self.SETTING_UNRAR_PATH]
		for count, path in enumerate(self.includes):
			try:
				if not path.startswith(XBMC_HOME): 
					src_path = xbmc.translatePath( "/".join( [XBMC_HOME, path] ) )
				else:
					src_path = xbmc.translatePath( path )
					path = path.replace(XBMC_HOME,'')
					if path[0] in ('\\','/'):
						path = path[1:]

				dest_path = os.path.join( extract_path, self.short_build_name, "XBMC", path )
				if not self.isSilent:
					percent = int( (count * 100.0) / TOTAL )
					self._dialog_update( __language__(0), __language__( 515 ), src_path, dest_path, pct=percent )
					if dialogProgress.iscanceled(): break

				localCopy(src_path, dest_path, self.isSilent)
			except:
				handleException("_copy_includes() path="+path)


	######################################################################################
	def _delete_excludes(self):
		log( "> _delete_excludes() ")

		TOTAL = len(self.excludes)
		count = 0
		extract_path = self.settings[self.SETTING_UNRAR_PATH]
		for path in self.excludes:
			try:
				if path.startswith(".."):
					path = path.replace("..\\","").replace("../","")
					dest_path = os.path.join( extract_path, self.short_build_name, path )
				else:
					path = path.replace(XBMC_HOME, "")
					if path[0] in ('\\','/'):
						path = path[1:]
					dest_path = os.path.join( extract_path, self.short_build_name, "XBMC", path )

				if not self.isSilent:
					percent = int( (count * 100.0) / TOTAL )
					self._dialog_update( __language__(0), __language__( 516 ), dest_path, pct=percent )

				dest_path = xbmc.translatePath(dest_path)
				if path[-1] in ["\\","/"] or os.path.isdir(dest_path):
					removeTree(dest_path)
				else:
					deleteFile(dest_path)
				count += 1
			except:
				handleException("_delete_excludes() path="+path)
		log( "< _delete_excludes() ")

	######################################################################################
	def _maintain_incl_excl(self, isIncludes):
		log( "> _maintain_incl_excl() isIncludes=%s" % isIncludes)
		try:
			# make menu
			options = [__language__(650), __language__(651)]    # exit, add new
			if isIncludes:
				title = __language__( 615 )
				self.includes.sort()
				options.extend(self.includes)
			else:
				title = __language__( 618 )
				self.excludes.sort()
				options.extend(self.excludes)

			selectDialog = xbmcgui.Dialog()
			while True:
				# show menu
				selected = selectDialog.select( title, options )
				if selected <= 0:						# quit
					break

				path = ""
				deleteOption = False
				addOption = False
				if selected == 1:						# add new
					path, type = self._select_file_folder()
					if path and \
						((type in [0,3] and self._isRestrictedFolder(path)) or (type == 1 and self._isRestrictedFile(path))):
						path = ''
						log("ignore restricted file \ folder")
					else:
						addOption = True
				else:									# remove or edit
					deleteOption = True					# to del orig opt
					path = options[selected]
					# ask what action to take (remove, edit)
					if not dialogYesNo( __language__( 0 ), path, yesButton=__language__(406), noButton=__language__(407)):
						path = getKeyboard(path, __language__(207))		# edit - (if not cancelled or changed)
						if path:
							if not os.path.exists(xbmc.translatePath(path)):
								log("path not exist: %s" % path)
								xbmcgui.Dialog().ok(__language__( 0 ), __language__( 311 ), path)
								path = ''
							else:
								addOption = True							# to add amended as new
								path 

				if path:
					# remove home from beginning of path, so they're all stored as relative paths
					if deleteOption:
						del options[selected]

					if addOption:
						# add if not a duplicate
						try:
							options.index(path)
						except:
							options.append(path)

			# save to file
			if isIncludes:
				self.includes = options[2:]
				self._save_file_obj(self.INCLUDES_FILENAME, self.includes)
			else:
				self.excludes = options[2:]
				self._save_file_obj(self.EXCLUDES_FILENAME, self.excludes)
		except:
			handleException("_maintain_incl_excl()")
		log( "< _maintain_incl_excl()")

	#####################################################################################
	def _isRestrictedFolder(self, path):
		p = os.path.dirname(path)
		if p and p.lower() in ["special://xbmc", "q:/","credits","language","media","screensavers","scripts","skin","sounds","system","credits","visualisations"]:
			dialogOK(__language__(0), __language__(313), p)
			restricted = True
		else:
			restricted = False
		log("_isRestrictedFolder() %s %s" % (restricted, p))
		return restricted

	#####################################################################################
	def _isRestrictedFile(self, path):
		p = os.path.basename(path)
		if p and p.lower() in ["default.xbe"]:
			dialogOK(__language__(0), __language__(313), p)
			restricted = True
		else:
			restricted = False
		log("_isRestrictedFile() %s %s" % (restricted, p))
		return restricted

	#####################################################################################
	def _select_file_folder(self, path=""):
		log( "> _select_file_folder() path="+path)
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
			if not path.startswith(XBMC_HOME):
				path = "/".join( [XBMC_HOME, path] )
			if path[-1] in ["\\","/"]:
				type = FOLDER
			else:
				type = FILE

		try:
			if not path:
				path = XBMC_HOME +'/' # just incase

			if type == FILE:
				msg = __language__(203)
			else:
				msg = __language__(204)
			value = self._browse_for_path(msg, path, type)
			if not value or value == path or value == XBMC_HOME or not value.startswith(XBMC_HOME):
				log("none, unchanged or restricted value %s" % value)
				raise
			path = value

			bare_dest_path = str(os.path.splitdrive( path )[1])			# get path+filename, no drive
			if bare_dest_path and bare_dest_path[0] in ["/", "\\"]:
				bare_dest_path = bare_dest_path[1:]
			path = bare_dest_path			#.replace('/','\\')
		except:
			log("selection ignored.  %s" % sys.exc_info()[ 1 ])
			path = ''

		log("< _select_file_folder() final path=%s type=%s" % (path, type))
		return path, type

	#####################################################################################
	def _dialog_update(self, title="", line1="", line2="", line3="", pct=0, time=4):
		if not self.isSilent:
			dialogProgress.update( pct, line1, line2,line3 )
		else:
			msg = ("%s %s %s" % (line1, line2, line3)).strip()
			showNotification(title, msg, time)


	#####################################################################################
	def _delete_old_build(self):
		log( "> _delete_old_build() ")

		# find all intalled builds
		oldBuilds = self._find_build_dirs()
		oldBuilds.insert(0, __language__( 650 ))

		# select
		selectDialog = xbmcgui.Dialog()
		while True:
			selected = selectDialog.select( __language__( 617 ), oldBuilds )
			if selected <= 0:						# quit
				break

			selectedBuildName = oldBuilds[selected]

			# delete path
			path = os.path.join( self.settings[ self.SETTING_UNRAR_PATH ], selectedBuildName)
			if dialogYesNo(__language__( 0 ), __language__( 523 ), selectedBuildName,yesButton=__language__(412), noButton=__language__(413), ):
				try:
					dialogProgress.create(__language__( 0 ), __language__( 516 ), path)
					removeTree(path)
					del oldBuilds[selected]
					dialogProgress.close()
				except:
					handleException("_delete_old_build()")
		log( "< _delete_old_build() ")

	#####################################################################################
	def _find_build_dirs(self):
		log( "> _find_build_dirs() ")
		dirList = []

		# get curr build name
		curr_build_date_secs, curr_build_date = self._get_current_build_info()	# secs, YYYYMMDD
		# make list of folders, excluding curr build folder
		for f in os.listdir(self.settings[ self.SETTING_UNRAR_PATH ] ):
			# ensure its a dir
			if os.path.isdir(os.path.join(self.settings[ self.SETTING_UNRAR_PATH ], f)):
				fileBuildDate = searchRegEx(f.replace("-",""), "^(?:XBMC|T3CH|SVN).*?(\d\d\d\d\d\d\d\d)")
				if fileBuildDate and fileBuildDate != curr_build_date:
					dirList.append(f)

		log( "< _find_build_dirs() dir count=%s" % len(dirList))
		return dirList
	
	#####################################################################################
	def _find_web_t3ch_builds(self):
		log( "> _find_web_t3ch_builds() ")
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

		log( "< _find_web_t3ch_builds() build count=%s" % len(buildList))
		return buildList

	#####################################################################################
	def _web_builds_menu(self):
		""" Find web old archive, show in a menu, select and download archive """
		log( "> _web_builds_menu() ")

		buildsList = self._find_web_t3ch_builds()
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

		log("< _web_builds_menu()")

	#####################################################################################
	def _get_current_build_info(self):
		buildDate = xbmc.getInfoLabel( "System.BuildDate" )
		curr_build_date_t = time.strptime(buildDate,"%b %d %Y")
		curr_build_date_secs = time.mktime(curr_build_date_t)
#		curr_build_date = time.strftime("T3CH_%Y-%m-%d", curr_build_date_t)
		curr_build_date = time.strftime("%Y%m%d", curr_build_date_t)
		log( "_get_current_build_info() secs=%s  date=%s" % (curr_build_date_secs, curr_build_date))
		return (curr_build_date_secs, curr_build_date)

	######################################################################################
	def _update_script( self, isSilent=False):
		log( "> _update_script() isSilent=%s" % isSilent)

		updated = False
		up = update.Update(__language__, __scriptname__)
		version = up.getLatestVersion(isSilent)
		log("Current Version: " + __version__ + " Tag Version: " + version)
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
		log( "< _update_script() updated=%s" % updated)
		return updated

	#####################################################################################
	def _settings_menu(self):
		log( "> _settings_menu() ")

		def _translate_bool(value):
			return (__language__( 403 ), __language__( 402 ))[value]

		def _make_menu(settings):
			options = [__language__(650),
					__language__(639),
					__language__(619),
					"%s -> %s" %(__language__(640),_translate_bool(self.settings[self.SETTING_CHECK_NEW_BUILD])),
					"%s -> %s" %(__language__(630),self.settings[self.SETTING_SHORTCUT_DRIVE]),
					"%s -> %s" %(__language__(631),self.settings[self.SETTING_SHORTCUT_NAME]),
					"%s -> %s" %(__language__(632),self.settings[self.SETTING_UNRAR_PATH]),
					"%s -> %s" %(__language__(633),_translate_bool(self.settings[self.SETTING_NOTIFY_NOT_NEW])),
					"%s -> %s" %(__language__(634),_translate_bool(self.settings[self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP])),
					"%s -> %s" %(__language__(635),_translate_bool(self.settings[self.SETTING_XFER_USERDATA])),
					"%s -> %s" %(__language__(638),_translate_bool(self.settings[self.SETTING_PROMPT_DEL_RAR])),
					__language__(636),
					__language__(637)
						]
			return options

		selectDialog = xbmcgui.Dialog()
		heading = "%s: %s" % (__language__( 0 ), __language__( 601 ) )
		quit = False
		while not quit:
			options = _make_menu(self.settings)
			selected = selectDialog.select( heading, options )
			if selected <= 0:						# quit
				break

			elif selected == 1:														# view readme/changelogs
				self._doc_menu()
			elif selected == 2:														# check for script update
				if self._update_script(False):											# never silent from config menu
					log("script updating ... closing current instance")
					quit = True
			elif selected == 3:														# check for new build
				self.settings[self.SETTING_CHECK_NEW_BUILD] = not self.settings[self.SETTING_CHECK_NEW_BUILD]

			elif selected == 4:															# shortcut drive
				value = self._pick_shortcut_drive()
				if value:
					self.settings[self.SETTING_SHORTCUT_DRIVE] = value

			elif selected == 5:															# shortcut name
				value = self._browse_dashname(self.settings[self.SETTING_SHORTCUT_NAME])
				if value:
					self.settings[self.SETTING_SHORTCUT_NAME] = value

			elif selected == 6:															# unrar path
				value = self._browse_for_path( __language__( 200 ), self.settings[self.SETTING_UNRAR_PATH] )
				if value and not value.startswith(XBMC_HOME):
					self.settings[self.SETTING_UNRAR_PATH] = value

			elif selected == 7:															# notify when not new
				self.settings[self.SETTING_NOTIFY_NOT_NEW] = not self.settings[self.SETTING_NOTIFY_NOT_NEW]

			elif selected == 8:															# check for update
				self.settings[self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP] = not self.settings[self.SETTING_CHECK_SCRIPT_UPDATE_STARTUP]

			elif selected == 9:															# xfer userdata
				self.settings[self.SETTING_XFER_USERDATA] = not self.settings[self.SETTING_XFER_USERDATA]

			elif selected == 10:															# prompt del rar
				self.settings[self.SETTING_PROMPT_DEL_RAR] = not self.settings[self.SETTING_PROMPT_DEL_RAR]

			elif selected == 11:														# reset settings
				if dialogYesNo(__language__(0), __language__( 636 ) + " ?"):
					self._set_default_settings(forceReset=True)

			elif selected == 12:														# reset incl & excl
				if dialogYesNo(__language__(0), __language__( 637 ) + " ?"):
					self._init_includes_excludes(forceReset=True)

		# DO SOME POST SETTINGS MENU checks
		# ensure unrar path exists
		makeDir(self.settings[ self.SETTING_UNRAR_PATH ])
		self._save_file_obj( self.SETTINGS_FILENAME, self.settings )
		log( "< _settings_menu() quit=%s" % quit)
		return quit


######################################################################################
# GLOBAL FUNCS
######################################################################################


######################################################################################
# copies a folder or file to dest.
# If dest exists, not overwritten unlexx overwrite = True
######################################################################################
def localCopy(src_path, dest_path, isSilent=False, overwrite=False):
	log( "localCopy() %s -> %s overwrite=%s" % (src_path, dest_path, overwrite))

	try:	
		if not os.path.exists(src_path):
			log("src_path not exist, stop")
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
				log( "isFile; dest file exists, ignored: " + dest_path)
		else:
			# DIR
			files = os.listdir(src_path)
			log("isdir; file count=%s" % len(files))
			for f in files:
				if f in ('.','..'): continue
				src_file = os.path.join( src_path, f )
				dest_file = os.path.join( dest_path, f )

				try:
					if os.path.isdir( src_file ):
						do_copy = True
						if os.path.isdir( dest_file ):					# does dest dir exist ?
							if overwrite:								# overwrite if requested
								log("isDir; overwrite; remove existing: " + dest_file)
								os.rmdir(dest_file)
								time.sleep(2)
							else:
								do_copy = False

						if do_copy:
							# copy directory
							log("isDir; copytree dir: %s -> %s" % (src_file, dest_file))
							makeDir( os.path.dirname(dest_file) )
							copytree( src_file, dest_file )
						else:
							log("isDir; dest dir exists, ignored: " + dest_file)
					else:
						if overwrite or not fileExist( dest_file ):
							copy( src_file, dest_file )
						else:
							log("isDir; dest file exists, ignored: " + dest_file)
				except:
					handleException("localCopy() DIR COPY", src_file, dest_file )
	except:
		handleException("localCopy() Unhandled", src_path, dest_path )


#################################################################################################################
def getKeyboard(default, heading, hidden=False):
	keyboard = xbmc.Keyboard( default, heading, hidden )
	keyboard.doModal()
	if ( keyboard.isConfirmed() ):
		text = keyboard.getText().strip()
		if text != default:		# changed
			return text
	return ''

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
	log( "handleException()" )
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
		os.makedirs(xbmc.translatePath(dir))
		log( "made dir: " + dir)
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
				log( "file deleted: " + file_name )
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
	return value

######################################################################################
def readURL( url, msg='', isSilent=False):
	log( "readURL() isSilent=%s %s" % (isSilent,url))
	if not url:
		return ""

	if not isSilent:
		root, name = os.path.split(url)
		dialogProgress.create( __language__(0), msg, root, name )

	doc = None
	try:
		sock = urllib.urlopen( url )
		doc = sock.read()
		sock.close()
	except IOError, errobj:
		dialogOK(__language__(0),"IOError", sys.exc_info()[ 1 ])
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
		log( "TextBoxDialogXML.onInit()" )
		try:
			self.getControl( 5 ).setText( self.text )
			self.getControl( 3 ).setLabel( self.title )		# may not have an ID assigned
		except: pass

	def onClick( self, controlId ):
		pass

	def onFocus( self, controlId ):
		pass

	def onAction( self, action ):
		if action and (action.getButtonCode() in CANCEL_DIALOG or action.getId() in CANCEL_DIALOG):
			self.close()

	def ask(self, title, text ):
		log("TextBoxDialogXML().ask()")
		self.title = title
		self.text = text
		self.doModal()		# causes window to be drawn

#################################################################################################################
def unzip(extract_path, filename, silent=False, msg=""):
	""" unzip an archive, using ChunkingZipFile to write large files as chunks if necessery """
	log("> unzip() extract_path=" + extract_path + " filename=" + filename)
	success = False
	cancelled = False
	installed_path = ""

	zip=zipstream.ChunkingZipFile(filename, 'r')
	infos=zip.infolist()
	namelist = zip.namelist()
	max_files = len(namelist)
	log("max_files=%s" % max_files)

	for file_count, entry in enumerate(namelist):
		info = infos[file_count]

		if not silent:
			percent = int( (file_count * 100.0) / max_files )
			root, name = os.path.split(entry)
			dialogProgress.update( percent, msg, root, name)
			if ( dialogProgress.iscanceled() ):
				cancelled = True
				break

		filePath = os.path.join(extract_path, entry)
		if filePath[-1] in ('/','\\'):
			if not os.path.isdir(filePath):
				os.makedirs(filePath)
		elif (info.file_size + info.compress_size) > 25000000:
			log( "LARGE FILE: f sz=%s  c sz=%s  reqd sz=%s %s" % (info.file_size, info.compress_size, (info.file_size + info.compress_size), entry ))
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
	log("< unzip() success=%s installed_path=%s" % (success, installed_path))
	return success, installed_path

##############################################################################################################    
def getLanguagePath():
	try:
		base_path = os.path.join( os.getcwd().replace(';',''), 'resources', 'language' )
		language = xbmc.getLanguage()
		langPath = os.path.join( base_path, language )
		if not os.path.exists(langPath):
			log("getLanguagePath() path not exist: " + langPath)
			raise
	except:
		language = 'English'
	log("getLanguagePath() path=%s lang=%s" % ( base_path, language ))
	return base_path, language

##############################################################################################################    
def removeTree(top):
	log("removeTree() " + top)
	for root, dirs, files in os.walk(top, topdown=False):
		for name in files:
			try:
				os.remove(os.path.join(root, name))
			except: pass

		for name in dirs:
			rmtree(os.path.join(root, name), ignore_errors=True)

		rmtree(root, ignore_errors=True)

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

try:
	log( "__language__ = %s" % __language__ )
	Main(runMode)
except:
	log( str(sys.exc_info()[ 1 ]) )

log(" EXIT and housekeeping ...")
# clean up on exit
moduleList = ['zipstream','SFVCheck']
for m in moduleList:
	try:
		del sys.modules[m]
		log(" Removed module: " + m)
	except: pass

# remove globals
try:
	del dialogProgress
except: pass
