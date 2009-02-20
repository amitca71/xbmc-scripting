"""

  smbLib.py - Functions to help with SMB connection and files fetching etc.
  This version for myTV only.

  ChangeLog:
  22/10/06 - Created.
  12/01/07 - Updated, smbConnect(), parseSMBPath()
  12/02/07 - Added selectSMB(), updated other funcs
  10/05/07 - Added getSMBFileSize()
  06/03/08 - Updated for myTV v1.18

"""
import sys,os.path
import xbmc, xbmcgui

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__title__ = "smbLib"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '17-11-2008'
xbmc.output("Imported From: " + __scriptname__ + " title: " + __title__ + " Date: " + __date__)

import smb, nmb
import os.path
import re
from string import find
from bbbLib import *
from bbbGUILib import *

__language__ = sys.modules[ "__main__" ].__language__

dialogProgress = xbmcgui.DialogProgress()

###################################################################################################
def smbConnect(hostIP, smbPath):
	debug("> smbConnect() hostIP=%s smbPath=%s" % (hostIP, smbPath))
	success = False
	remote = None
	remoteInfo = None

	if not hostIP or not smbPath:
		messageOK(__language__(951), __language__(959), __language__(950))
	else:
#		dialogProgress.create(__language__(960), __language__(964))
		remoteInfo = parseSMBPath(smbPath)
		if DEBUG: print "remoteInfo=", remoteInfo
		if not remoteInfo:
			messageOK(__language__(951), smbPath)
		else:
			domain,user,password,pcname,service,dirPath = remoteInfo
			try:
				remote = smb.SMB(pcname, hostIP)
				debug("SMB connection established")
			except:
				messageOK(__language__(952), __language__(953),  pcname+" -> "+hostIP)
			else:
				useLogin = remote.is_login_required()
				debug("useLogin = %s" % useLogin)
				if useLogin:
					if not user or not password:
						messageOK(__language__(954), "SMB User / Password missing!" )
					else:
						try:
							remote.login(user, password, domain)
						except smb.SessionError, ex:
							handleExceptionSMB(ex,"SMB Login")
						except:
							handleException(__language__(954))
						else:
							debug("SMB login OK")
							success = True
				else:
					success = True
#		dialogProgress.close()

		if not success:
			remote = None
			remoteInfo = None
	debug("< smbConnect() success="+str(success))
	return remote, remoteInfo

###################################################################################################
def getSMBFileSize(remote, remoteInfo, remoteFile):
    debug("> getSMBFileSize() remoteFile: " + remoteFile)
    fileSize = -1
    connected = False
    if not remoteFile:
        messageOK(__language__(957), __language__(965))
    elif not remote or not remoteInfo:
        messageOK(__language__(957), __language__(966))
    else:
        domain,user,password,pcname,service,dirPath = remoteInfo
        remotePath = "%s%s" % (dirPath,remoteFile)
        debug("remotePath=%s" % remotePath)
        try:
            fileSize = remote.list_path(service, remotePath)[0].get_filesize()
        except:
            debug("remote file not found")

    debug("< getSMBFileSize() fileSize: " + str(fileSize))
    return fileSize


###################################################################################################
def smbFetchFile(remote, remoteInfo, localPath, remoteFile, silent=True):
	debug("> smbFetchFile() localPath="+localPath + " remoteFile="+remoteFile)
	success = False

	if not remote or not remoteInfo:
		messageOK(__language__(957),__language__(966))
	else:
		domain,user,password,pcname,service,dirPath = remoteInfo
		if DEBUG: print remoteInfo
		if not remoteFile:
			messageOK(__language__(957), __language__(965))
		else:
			remotePath = "%s%s" % (dirPath,remoteFile)
			debug("remotePath="+remotePath)
			if not silent:
				dialogProgress.create(__language__(962), remotePath, localPath)

			try:
				f = open(localPath, "wb")
				remote.retr_file(service, remotePath, f.write)
				f.close()
			except smb.SessionError, ex:
				if not silent or (ex[1] != 1 and ex[2] != 2):	# not found
					handleExceptionSMB(ex, __language__(951), remotePath)
			except:
				handleException()
			else:
				success = fileExist(localPath)

			if not silent:
				dialogProgress.close()
			if not success:
				deleteFile(localPath)

	debug("< smbFetchFile() success="+str(success))
	return success

###################################################################################################
def smbSendFile(remote, share, localPath, remotePath, silent=False):
	debug("> smbSendFile()")
	success = False

	if DEBUG:
		print remote, share, localPath, remotePath, silent

	if not remote:
		messageOK(__language__(963), __language__(966))
	else:
		if not silent:
			dialogProgress.create(__language__(963), localPath, remotePath)

		try:
			debug("opening local file")
			f = open(localPath, "rb")
			debug("sending file to share")
			remote.stor_file(share, remotePath, f.read)
			f.close()
			success = True
		except smb.SessionError, ex:
			handleExceptionSMB(ex, __language__(951), remotePath)
		except:
			messageOK(__language__(951), remotePath, localPath)
			handleException()

		if not silent:
			dialogProgress.close()

	debug("< smbSendFile() success="+str(success))
	return success

###############################################################################################################
# fetch a file from SMB if the remote file is newer than the local file
###############################################################################################################
def isNewSMBFile(remote, remoteInfo, localPath, remoteFile, silent=True):
	debug("> isNewSMBFile() localPath="+localPath + " remoteFile="+remoteFile)
	remoteFileSecs = 0
	localFileSecs = 0

	if not remote or not remoteInfo:
		messageOK(__language__(951), __language__(966))
	else:
		if DEBUG: print remoteInfo
		if not remoteFile:
			messageOK(__language__(959),__language__(965))
		else:
			domain,user,password,pcname,service,dirPath = remoteInfo
			remotePath = "%s%s" % (dirPath,remoteFile)
			if not silent:
				dialogProgress.create(__language__(967), remotePath)

			if fileExist(localPath):
				localFileSecs = os.path.getmtime(localPath)

			# list files on SMB of remote filename, check modified timestamp
			try:
				remoteFileSecs = remote.list_path(service, remotePath)[0].get_mtime_epoch()
			except:
				debug("remote file not found")

			if not silent:
				dialogProgress.close()

	debug("local timestamp: %s  Remote timestamp: %s" % (localFileSecs,remoteFileSecs))
	# check secs since epoch of files.
	newFileFound = (remoteFileSecs > localFileSecs) # greater secs means newer
	debug("< isNewSMBFile() newFileFound: %s" % newFileFound)
	return newFileFound

###############################################################################################################
def listDirSMB(remote, remoteInfo):
	debug("> listDirSMB()")
	fileList = []

	if not remote or not remoteInfo:
		messageOK(__language__(951), __language__(966))
	else:
		if DEBUG: print remoteInfo
		domain,user,password,pcname,service,dirPath = remoteInfo

		# list files on SMB of remote
		fileList = remote.list_path(service, dirPath+'/*')

	debug("< listDirSMB() count=%d" % len(fileList))
	return fileList

###############################################################################################################
def handleExceptionSMB(ex, title, msg=""):
	print "handleExceptionSMB()"
	try:
		xbmcgui.unlock()
	except: pass
	try:
		t = "%s ErrCodes: %s, %s" % (title, ex[1], ex[2])
		if ex[1] == 1 and ex[2] == 2:			# file not found
			messageOK(t,msg,"Remote file not found.")
		elif ex[1] == 1 and ex[2] == 3:
			messageOK(t,msg,"Directory invalid","Please correct SMB Path")
		elif ex[1] == 1 and ex[2] == 5:			# Access denied
			messageOK(t,msg,"Remote file Access Denied.","Check remote Permissions/User/Password are correct.")
		elif ex[1] == 1 and ex[2] == 15:
			messageOK(t,msg,"Invalid drive specified.","Please correct SMB Path.")
		elif ex[1] == 1 and ex[2] == 32:
			messageOK(t,msg,"Share mode can't be granted.","Please check remote share.")
		elif ex[1] == 1 and ex[2] == 67:
			messageOK(t,msg,"Invalid Share Name.","Please correct SMB Path.")
		else:									# trap other SMB err
			messageOK(t, msg,"UnTrapped error codes, Check smb.h for definition.")
	except:
		handleException("handleExceptionSMB()")


#################################################################################################################
def parseSMBPath(path):
	if not path:
		return None
	# smb://domain;user:pass@pcname/share/folder
#	m = re.match('^smb://(\w+);(\w+):([^@]+)@([^/]+)/([^/]+)(/?.*?)([^/]*)$', path) # with fn
	m = re.match('^smb://(\w+);(\w+):([^@]+)@([^/]+)/([^/]+)(/?.*?)$', path) # without fn
	if m:
		xbmc.output("matches smb://domain;user:pass@pcname/share")
		return m.groups() # 6 groups

	# smb://user:pass@pcname/share/folder
#	m = re.match('^smb://(\w+):([^@]+)@([^/]+)/([^/]+)(/?.*?)([^/]*)$', path)
	m = re.match('^smb://(\w+):([^@]+)@([^/]+)/([^/]+)(/?.*?)$', path)   # without fn
	if m:
		xbmc.output("matches smb://user:pass@pcname/share/folder")
		return '', m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)

	# smb://pcname/share/folder
#	m = re.match('^smb://([^/]+)/([^/]+)(/?.*?)([^/]*)$', path)
	m = re.match('^smb://([^/]+)/([^/]+)(/?.*?)$', path)   # without fn
	if m:
		xbmc.output("matches smb://pcname/share/folder")
		return '', '', '', m.group(1), m.group(2), m.group(3)
	return None

#################################################################################################################
def getIPFromName(pcname):
	debug("> getIPFromName() pcname=%s" % pcname)
	ip = ''
	dialogProgress.create(__language__(976), __language__(964))
	try:
		ip = nmb.NetBIOS().gethostbyname(pcname)[0].get_ip()
		dialogProgress.close()
		if not xbmcgui.Dialog().yesno(__language__(973), pcname, ip):
			ip = ''
	except:
		dialogProgress.close()
		messageOK(__language__(956), pcname)
		ip=''
	debug("< getIPFromName() ip=%s" % ip)
	return ip


#######################################################################################################################    
# Discover a list of pre-defined SMB
#######################################################################################################################    
def selectSMB(currentValue=''):
	debug("> selectSMB()")
	returnValue = ''
	doc = ''

	doc = readFile(os.path.join('Q:' + os.sep,'UserData','sources.xml'))
	if doc:
		# extract SMB paths from XBMC config file
		menuList = []
		prefix = 'smb://'
		regex = '<path>('+prefix+'.*)</path>'
		findRe = re.compile(regex, re.IGNORECASE)
		matches = findRe.findall(doc)
		if matches:
			# remove empty & examples
			for match in matches:
				if match == prefix or 'username' in match or 'DOMAIN' in match:
					continue
				try:
					menuList.index(match)
				except:
					menuList.append(match)	# not exist already, add

		# set to currentValue
		try:
			currentIdx = menuList.index(currentValue)
		except:
			currentIdx = 0
		# select from list
		selectedPos = xbmcgui.Dialog().select(__language__(971), menuList)
		if selectedPos >= 0:
			returnValue = menuList[selectedPos]

	debug("< selectSMB() returnValue= " + returnValue)
	return returnValue


#################################################################################################################
# MENU ITEM - config SMB PC connection
# fnTitle - Menu option title to use that represents Remote Filename
#################################################################################################################
class ConfigSMB:
	def __init__(self, parentConfig, section="SMB", title="", \
				fnTitle='Remote Filename:',fnDefaultValue='', pathDefaultValue='', ipDefaultValue=''):
		debug("> smbLib.ConfigSMB().__init__ section="+section)

		self.config = parentConfig
		self.configSection = section
		if title:
			self.title = title
		else:
			self.title = __language__(976)
		self.EXAMPLE_SMB_PATH = 'smb://user:pass@pcname/share/folder/'

		self.KEY_SMB_PATH = "smb_path"
		self.KEY_SMB_IP = "smb_pc_ip"
		self.KEY_SMB_FILE = "smb_filename"

		self.MENU_OPT_SMB_PATH = __language__(969)
		self.MENU_OPT_SMB_IP = __language__(970)
		self.MENU_OPT_SMB_FILE = fnTitle
		self.MENU_OPT_SMB_SETUP_FROM_EXIST = __language__(971)
		self.MENU_OPT_SMB_CONN_CHECK = __language__(972)

		self.menuOptions = [
			[__language__(500), None, None],
			[self.MENU_OPT_SMB_PATH, self.KEY_SMB_PATH, pathDefaultValue],
			[self.MENU_OPT_SMB_IP, self.KEY_SMB_IP, ipDefaultValue],
			[self.MENU_OPT_SMB_FILE, self.KEY_SMB_FILE, fnDefaultValue],
			[self.MENU_OPT_SMB_SETUP_FROM_EXIST, None, None],
			[self.MENU_OPT_SMB_CONN_CHECK, None, None]
			]

		self.TITLE = 0
		self.CONFIG_KEY = 1
		self.DEFAULT_VALUE = 2
		self.NO_VALUE = '?'
		self.menu = []

		debug("< smbLib.ConfigSMB().__init__")

	def createMenuList(self):
		debug("> ConfigSMB.createMenuList()")
		menu = []  # exit
		for option, configKey, defaultValue in self.menuOptions:
			if configKey == None:		# no config KEY
				label2 = ''
			else:
				value = self.config.action(self.configSection, configKey)
				if not value:
					label2 = ''
				else:
					label2 = str(value)

			menu.append(xbmcgui.ListItem(option, label2))
		debug("< ConfigSMB.createMenuList()")
		return menu

	def saveSMBPath(self, smbPath):
		debug("> saveSMBPath() smbPath="+smbPath)
		success = False
		remoteInfo = parseSMBPath(smbPath)
		if DEBUG: print "remoteInfo=", remoteInfo
		if not remoteInfo:
			messageOK(__language__(951), __language__(966))
		else:
			if smbPath[-1] != '/': smbPath += '/'
			domain,user,password,pcname,service,dirPath = remoteInfo
			self.config.action(self.configSection, self.KEY_SMB_PATH, \
							   smbPath, self.config.configHelper.MODE_WRITE)
			if find(pcname,'.') < 0:				# is a PCNAME?
				success = True	                    # save & parse was OK
				ip = getIPFromName(pcname)			# discover IP
				if ip:
					self.config.action(self.configSection, self.KEY_SMB_IP, ip, self.config.configHelper.MODE_WRITE)
			else:
				messageOK(__language__(959),__language__(955), self.EXAMPLE_SMB_PATH)

		debug("< saveSMBPath() success="+str(success))
		return success

	def checkAll(self, silent=False):
		debug("smbLib.checkAll()")
		ip, path, fn = self.getSMBDetails()
		if ip and path and fn:
			debug("ConfigSMB.checkAll() True")
			return (ip, path, fn)
		else:
			debug("ConfigSMB.checkAll() False")
			if not silent:
				messageOK(__language__(972), __language__(959))
			return None

	def getSMBDetails(self):
		details = (self.config.action(self.configSection, self.KEY_SMB_IP), \
				self.config.action(self.configSection, self.KEY_SMB_PATH), \
				self.config.action(self.configSection, self.KEY_SMB_FILE))
		return details

	# show this dialog and wait until it's closed
	def ask(self):
		debug("> ConfigSMB.ask()")

		selectedPos = 0 	# start on exit
		changed = False
		while True:
			menu = self.createMenuList()
			selectDialog = DialogSelect()
			selectDialog.setup(self.title, width=620, rows=len(menu))
			selectedPos, action = selectDialog.ask(menu, selectedPos)
			if selectedPos <= 0:
				break # exit selected

			# get menu selected value
			key = menu[selectedPos].getLabel()
			value = menu[selectedPos].getLabel2()
			if not value or value == self.NO_VALUE:
				try:
					value = self.menuOptions[selectedPos][self.DEFAULT_VALUE]
					if value == None:
						value = ''
				except:
					value = ''

			if key == self.MENU_OPT_SMB_PATH:
				title = "%s eg. %s" % (self.MENU_OPT_SMB_PATH, self.EXAMPLE_SMB_PATH)
				value = doKeyboard(value, title)
				if value:
					changed = self.saveSMBPath(value)

			elif key == self.MENU_OPT_SMB_IP:
				value = doKeyboard(value, self.MENU_OPT_SMB_IP, KBTYPE_IP)
				if value:
					self.config.action(self.configSection, self.KEY_SMB_IP, value, self.config.configHelper.MODE_WRITE)
					changed = True

			elif key == self.MENU_OPT_SMB_FILE:
				value = doKeyboard(value, self.MENU_OPT_SMB_FILE)
				if value:
					self.config.action(self.configSection, self.KEY_SMB_FILE, value, self.config.configHelper.MODE_WRITE)
					changed = True

			elif key == self.MENU_OPT_SMB_SETUP_FROM_EXIST:
				value = selectSMB(value)
				if value:
					changed = self.saveSMBPath(value)

			elif key == self.MENU_OPT_SMB_CONN_CHECK:
				smbDetails = self.checkAll()
				if smbDetails:
					ip, smbPath, remoteFile = smbDetails
					remote, remoteInfo = smbConnect(ip, smbPath)
					if remote and remoteInfo:
						messageOK(self.MENU_OPT_SMB_CONN_CHECK,__language__(961))

		debug("< ConfigSMB.ask() changed=%s" % changed)
		return changed

#################################################################################################################
def enterSMB(smbPath='', title=''):
	if not title:
		title = "Enter SMB Path:"
	value = doKeyboard(smbPath, title, KBTYPE_ALPHA)
	if value:
		smbPath, ip = getSMBPathIP(value)
	else:
		ip = ''
		smbPath = ''
	return smbPath, ip

#################################################################################################################
def isIP(host):
	result = re.match('^\d+\.\d+\.\d+\.\d+$', host)
	debug("isIP(): host=%s %s" % (host, result))
	return result

#################################################################################################################
def getSMBPathIP(smbPath, isSMBBasePathOnly=False):
	debug("> getSMBPathIP() %s" % smbPath)
	success = False
	ip = ""
	if smbPath.endswith('/'): smbPath = smbPath[:-1]
	if not isSMBBasePathOnly:
		remoteInfo = parseSMBPath(smbPath)
	else:
		remoteInfo = parseSMBBasePath(smbPath)
	if DEBUG: print remoteInfo

	if remoteInfo and smbPath:
		domain,user,password,pcname,share,dirPath = remoteInfo
		if '.' not in pcname:										# PCNAME not an IP
			ip = getIPFromName(pcname)								# discover IP
		else:
			messageOK(__language__(974),__language__(955),"eg. OFFICE")
	else:
		messageOK(__language__(974), __language__(950))
		smbPath = ""

	debug("< getSMBPathIP()")
	return smbPath, ip

#################################################################################################################
def parseSMBBasePath(path):
	# smb://user:pass@pcname
	m = re.match('^smb://(\w+):([^@]+)@([^/]+)$', path)
	if m:
		xbmc.output("matches smb://user:pass@pcname")
		return ('', m.group(1), m.group(2), m.group(3), '', '', '')

	# smb://pcname
	m = re.match('^smb://([^/]+)$', path)
	if m:
		xbmc.output("matches smb://pcname")
		return ('', '', '', m.group(1), '', '', '')

	return None
