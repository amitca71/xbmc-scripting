 
@Echo off
SET ScriptName=EvoxT-Trainers
:: Create Build folder
Echo ------------------------------
Echo Creating %ScriptName% Build Folder . . .
rmdir BUILD /S /Q
md BUILD
Echo.
:: Create exclude file
Echo ------------------------------
Echo Creating exclude.txt file . . .
Echo.
Echo .svn>"BUILD\exclude.txt"
Echo Thumbs.db>>"BUILD\exclude.txt"
Echo Desktop.ini>>"BUILD\exclude.txt"
Echo.
Echo ------------------------------
Echo Copying required files to \Build\%ScriptName%\ folder . . .
xcopy skins "BUILD\%ScriptName%\skins" /E /Q /I /Y /EXCLUDE:BUILD\exclude.txt
copy default.* "BUILD\%ScriptName%\"
copy changelog.* "BUILD\%ScriptName%\"
copy readme.* "BUILD\%ScriptName%\"
Echo.
Echo Build Complete - Scroll Up to check for errors.
Echo Final build is located in the BUILD folder.
Echo copy: \%ScriptName%\ folder in the \BUILD\ folder.
Echo to: /XBMC/scripts/ folder.
pause