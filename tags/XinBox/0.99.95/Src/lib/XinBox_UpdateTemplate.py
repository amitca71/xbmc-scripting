import xbmc, xbmcgui, sys, os, time
origpath =
newpath =

for root, dirs, files in os.walk(origpath, topdown=False):
    for name in files:
        os.remove(os.path.join(root, name))
    for name in dirs:
        os.rmdir(os.path.join(root, name))
os.rmdir(origpath)
os.rename(newpath,origpath)
xbmc.executescript(origpath + "\\default.py")
