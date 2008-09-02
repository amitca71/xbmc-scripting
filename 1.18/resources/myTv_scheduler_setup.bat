@echo off
REM Intended mostly for Hauppauge TV Cards.
REM This will setup a scheduled task that runs a batch file which inturn checks for myTV programme files.
REM Runs every MINUTE
REM
REM Put the full folder path in /TR parameter.
REM
schtasks /create /TN "myTV Recording Scheduler" /SC MINUTE /TR "\"G:\My Documents\myTV\myTV_scheduler.bat\"" /RU SYSTEM
