@ECHO OFF
CLS
COLOR 1B

:Begin
:: Set script name based on current directory
FOR /F "Delims=" %%D IN ('ECHO %CD%') DO SET ScriptName=%%~nD

:: Set window title
TITLE %ScriptName% Build Script!

:MakeBuildFolder
:: Create Build folder
ECHO ----------------------------------------------------------------------
ECHO.
ECHO Creating \BUILD\%ScriptName%\ folder . . .
IF EXIST BUILD (
    RD BUILD /S /Q
)
MD BUILD
ECHO.


:MakeExcludeFile
:: Create exclude file
ECHO ----------------------------------------------------------------------
ECHO.
ECHO Creating exclude.txt file . . .
ECHO.
ECHO .svn>"BUILD\exclude.txt"
ECHO Thumbs.db>>"BUILD\exclude.txt"
ECHO Desktop.ini>>"BUILD\exclude.txt"

Echo ------------------------------
Echo Copying required files to \Build\%ScriptName%\ folder . . .
xcopy resources "BUILD\%ScriptName%\resources" /E /Q /I /Y /EXCLUDE:BUILD\exclude.txt
copy default.* "BUILD\%ScriptName%\"
copy readme.* "BUILD\%ScriptName%\"
copy changelog.* "BUILD\%ScriptName%\"
Echo.


:Cleanup
:: Delete exclude.txt file
ECHO ----------------------------------------------------------------------
ECHO.
ECHO Cleaning up . . .
DEL "BUILD\exclude.txt"
ECHO.
ECHO.

:Finish
:: Notify user of completion
ECHO ======================================================================
ECHO.
ECHO Build Complete
ECHO.
ECHO Final build is located in the \BUILD\ folder.
ECHO.
ECHO copy: \%ScriptName%\ folder from the \BUILD\ folder.
ECHO to: /XBMC/scripts/ folder.
ECHO.
ECHO ======================================================================
ECHO.
PAUSE