"""
 Shared global values for Plugin
 """
import os, sys

HOME_DIR = os.getcwd()
TEMP_DIR = "special://temp"
__plugin__ = sys.modules[ "__main__" ].__plugin__

BASE_PLUGIN_THUMBNAIL_PATH = "/".join( ["special://masterprofile", "Thumbnails", "Video"] )
DEFAULT_THUMB_IMAGE = "/".join( [HOME_DIR,"default.tbn"])
ITEM_REVIEWS_FILENAME = "/".join( [TEMP_DIR, __plugin__+"_%s.htm"] )
CAT_OBJ_FILENAME = "/".join( [TEMP_DIR, __plugin__+"_%s.dat"] )
CAT_RSS_FILENAME = "/".join( [TEMP_DIR, __plugin__+"_%s.xml"] )
ITEM_PHOTO_FILENAME = "/".join( [TEMP_DIR, __plugin__+"_%s.jpg"] )
BASE_URL = "http://www.metacritic.com"
RSS_URL = BASE_URL + "/rss/%s.xml"
PRINT_PAGE_URL = BASE_URL + "/print"
LABEL_COLOUR_GREEN = "[COLOR=FF00FF00]%s[/COLOR]"
LABEL_COLOUR_YELLOW = "[COLOR=FFFFFF33]%s[/COLOR]"
LABEL_COLOUR_RED = "[COLOR=FFFF0022]%s[/COLOR]"
LABEL_COLOUR_NONE = "[COLOR=DDFFFFFF]%s[/COLOR]"
