"""

  smbLib.py - Functions to help with SMB connection and files fetching etc.

  ChangeLog:
  22/10/06 - Created.
  12/01/07 - Updated, smbConnect(), parseSMBPath()
  12/02/07 - Added selectSMB(), updated other funcs
  10/05/07 - Added getSMBFileSize()
  07/04/08 - Updated with language strings

"""
import sys,os.path
import xbmc, xbmcgui

__scriptname__ = sys.modules[ "__main__" ].__scriptname__
__title__ = "smbLib"
__author__ = 'BigBellyBilly [BigBellyBilly@gmail.com]'
__date__ = '29-05-2008'
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
			domain,user,password,pcname,service,dirPath,fileName = remoteInfo
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
						messageOK(__language__(954), "%s:%s" % (user,password))
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
        if DEBUG: print remoteInfo
        domain,user,password,pcname,service,dirPath,fileName = remoteInfo
        remotePath = "%s%s" % (dirPath,remoteFile)
        debug("remotePath=%s" % remotePath)
        try:
            fileSize = remote.list_path(service, remotePath)[0].get_filesize()
        except:
            debug("remote file not found")

    debug("< getSMBFileSize() fileSize: " + str(fileSize))
    return fileSize


###################################################################################################
def smbFetchFile(smbPath, localPath, remote=None, hostIP='', silent=True):
	debug("> smbFetchFile() smbPath="+smbPath + " localPath="+localPath)
	success = False

	smbPath = "smb://" + smbPath.replace('smb://','').replace('//','/').replace('\\','/')
	debug( "new smbPath=" + smbPath )

	# if no remote connection supplied, establish one now
	if not remote:
		remote, remoteInfo = smbConnect(hostIP, smbPath)

	if not remote:
		messageOK(__language__(957),__language__(966))
	else:
		remoteInfo = parseSMBPath(smbPath)
		if DEBUG: print remoteInfo
		if not remoteInfo:
			messageOK(__language__(957), __language__(965))
		else:
			domain,user,password,pcname,service,dirPath,fileName = remoteInfo
			remotePath = "%s%s" % (dirPath,fileName)
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
def isNewSMBFile(smbPath, localPath, remote=None, hostIP='', silent=False):
	debug("> isNewSMBFile() smbPath=%s localPath=%s" % (smbPath, localPath))
	remoteFileSecs = 0
	localFileSecs = 0

	smbPath = "smb://" + smbPath.replace('smb://','').replace('//','/').replace('\\','/')
	debug( "new smbPath=" + smbPath )

	# if no remote connection supplied, establish one now
	if not remote:
		remote, remoteInfo = smbConnect(hostIP, smbPath)

	if not remote:
		messageOK(__language__(951), __language__(966))
	else:
		remoteInfo = parseSMBPath(smbPath)
		if DEBUG: print remoteInfo
		if not remoteInfo:
			messageOK(__language__(959),__language__(965))
		else:
			domain,user,password,pcname,service,dirPath,fileName = remoteInfo
			remotePath = "%s%s" % (dirPath,fileName)
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
	# smb://domain;user:pass@pcname/share/folder/filename
	m = re.match('^smb://(\w+);(\w+):([^@]+)@([^/]+)/([^/]+)(/?.*?)([^/]*)$', path)
	if m:
		xbmc.output("matches smb://domain;user:pass@pcname/share/folder/filename")
		return m.groups()

	# smb://user:pass@pcname/share/folder/filename
	m = re.match('^smb://(\w+):([^@]+)@([^/]+)/([^/]+)(/?.*?)([^/]*)$', path)
	if m:
		xbmc.output("matches smb://user:pass@pcname/share/folder/filename")
		return '', m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), m.group(6)

	# smb://user:pass@pcname/share/folder/
	m = re.match('^smb://(\w+):([^@]+)@([^/]+)/([^/]+)(/?.*?)$', path)
	if m:
		xbmc.output("matches smb://user:pass@pcname/share/folder/")
		return '', m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), ''

	# smb://pcname/share/folder/filename
	m = re.match('^smb://([^/]+)/([^/]+)(/?.*?)([^/]*)$', path)
	if m:
		xbmc.output("matches smb://pcname/share/folder/filename")
		return '', '', '', m.group(1), m.group(2), m.group(3), m.group(4)

	# smb://pcname/share/folder/
	m = re.match('^smb://([^/]+)/([^/]+)(/?.*?)$', path)
	if m:
		xbmc.output("matches smb://pcname/share/folder/")
		return '', '', '', m.group(1), m.group(2), m.group(3), ''

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
		selectDialog = DialogSelect()
		selectDialog.setup(__language__(971), rows=len(menuList), width=620)
		selectedPos, action = selectDialog.ask(menuList, currentIdx)
		if selectedPos >= 0:
			returnValue = menuList[selectedPos]

	debug("< selectSMB() returnValue= " + returnValue)
	return returnValue


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
#		if smbPath[-1] not in ["\\","/"]: smbPath += '/'
		
		domain,user,password,pcname,share,dirPath,fileName = remoteInfo
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
