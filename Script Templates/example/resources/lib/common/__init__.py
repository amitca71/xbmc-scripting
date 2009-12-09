import os, sys

# derive script name from the name of the current working directory
scriptname = os.path.split( os.getcwd()[:-1] )[-1].replace( '_', ' ' )

# derive resource path by walking down the directory tree until encountered
resource_path = __file__
while not os.path.split( resource_path )[-1] == 'resources':
    resource_path, tail = os.path.split( resource_path )
    del tail

# set up the language localization
import language
localize = language.Language().localized
del language

# append the directory for this module to the sys.path to ease importing
sys.path.append( os.path.split( __file__ )[0] )

# import the gui module when this is imported
import gui

# clean up the namespace
del os, sys