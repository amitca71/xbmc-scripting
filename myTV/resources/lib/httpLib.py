"""
 Collection of convenience funcs that use xbmc httpapi
"""

import sys, xbmc
from string import find

def httpFileCopy(remoteFilename, localFilename):
	return execHTTP("FileCopy(%s,%s)" % (remoteFilename, localFilename))

def execHTTP(cmd):
	try:
		response = xbmc.executehttpapi(cmd)
		xbmc.output("executehttpapi() response=%s" % response)
		return (response and find(response,"OK") >= 0)
	except:
		xbmc.output( str( sys.exc_info()[ 1 ] ) )
		return False
