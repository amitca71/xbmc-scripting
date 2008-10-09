@echo off
REM
REM Each programme file (eg. myTV_rec_<name>.bat contains a SCHTASKS cmd
REM CALL each file that exists, this will setup a Schedule Task for each programme.
REM Change the folder path to be the location where your XBMC myTV script sends programme files 'myTV_rec_<date>_<time>_title.bat'
REM
FOR /F %%A IN ('DIR "G:\My Documents\myTV\myTV_rec_*.bat" /b /OD') DO ECHO %%A >> "G:\My Documents\myTV\Scheduled_log.txt"
FOR /F %%A IN ('DIR "G:\My Documents\myTV\myTV_rec_*.bat" /b /OD') DO CALL "G:\My Documents\myTV\%%A"
REM
REM Now delete the file
REM
FOR /F %%A IN ('DIR "G:\My Documents\myTV\myTV_rec_*.bat" /b /OD') DO DEL "G:\My Documents\myTV\%%A"
