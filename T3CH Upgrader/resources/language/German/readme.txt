T3CH Aktualisierer - Skript zum downloaden, installieren und umstellen auf das letzte T3CH Build.

Installation:
 Kopiere nach \scripts\T3CH Upgrader (Unterordnerstruktur beibehalten!)


Gebrauch: 
 default.py ausführen

Beim Starten wird erkannt ob ein neues T3CH Build verfügbar ist.
Auswählen der Download Option: <build_name> wird den Vorgang starten.

Vor-Installation-Einstellungen:
-----------------------------

Man kann verschiedene Aspekte der Installation in den Einstellungen verändern:

1) Welches Laufwerk & Pfad der Installation:

   z.B. E:\apps

   Dann wird das Build entpackt nach:
         E:\apps\<t3ch_build_name>\XBMC

2) Den Pfad der Xbox Verknüpfung, die das XBMC als Dashboard lädt; und somit auch den Namen der Verknüpfung, den dein Modchip lädt.
   Es ist der Pfad, der auch in eine neue Verknüpfung geschrieben wird, damit das neu installierte T3CH XBMC Build geladen werden kann.
   Es wird die TEAM XBMC Shortcut.xbe verwendet. Diese benötigt eine .cfg Datei, in der der Pfad gespeichert wird.


   Laufwerk: z.B. C:

   DashName:  z.B. xbmc
   Man kann auch Unterordner im DashNamen angeben:
   
   z.B. dashboard\xbmc

3) Kopierliste:  
   Dies ist eine Liste mit Ordnern und Dateien, die vom aktuellen Build mit in das neue Build kopiert werden sollen.

4) Löschliste:   
   Dies ist eine Liste mit Ordnern und Dateien, die aus dem neuen Build gelöscht werden sollen.


Installation eines neuen T3CH Build
----------------------------------

Wähle im Hauptmenü die Option "Download: <build_name>"

Folgendes wird passieren:

1) Download der aktuellsten T3CH .rar
2) Entpackt die .rar in den gewählten Pfad.
3) Kopiert alte Userdata (falls in XBMC Ordnerstruktur vorhanden).
4) Kopiert Skripts (wenn nicht im neuen Build bereits vorhanden) - das Gleiche gilt für Visualisierungen, Skins etc.
5) Kopiert zusätzliche Dateien/Ordner aus der 'Kopierliste'.
6) Löscht Dateien/Ordner aus der 'Löschliste'.
7) Aufforderung zum erstellen und installieren einer neuen Dashverknüpfung.
   Backups werden immer gemacht, sie werden in *.xbe_old und *.cfg_old umbenannt.
8) Aufforderung zum Neustart.

Wenn nach dem Neustart alles in Ordnung ist, sollte nun das aktuellste T3CH Build laufen!

Lokale Installation:
------------------
Wenn man ein T3CH Build (RAR oder ZIP) per FTP in den angegebenen Downloadpfad (z.B. E:\apps\) kopiert, wird im Hauptmenü eine Option zum installieren des Builds angezeigt.
Zulässige Archivnamen für lokale Installation:

  T3CH:    T3CH_YYYYMMDD.rar|.zip  or  XBMC_YYYYMMDD.rar|.zip
  Nightly: SVN_YYYYMMDD.rar|.zip   or  XBMC_XBOX_YYYYMMDD.rar|.zip
    


SVN Nightly Builds
------------------
Anmerkung: Es handelt sich hierbei um Xbox builds, welche keine Extras wie Skins, Addons etc.
WEB INSTALLATION:

  1) Script starten, ändere den 'XBMC BUILDER' zu 'SVN Nightly'
  2) Nun wie bei einem T3CH Build vorgehen

LOKALE INSTALLATION:
Nightly Builds bekommt man unter www.sshcs.com/xbmc

  1) Browse zur Website und downloade ein Xbox Build
  2) Benenne den Archivnamen um, zu XBMC-YYYYMMDD_<was auch immer hier>.rar
     z.B. XBMC_XBOX_r19801.rar -> XBMC-20090429-r19801.rar
     oder
     z.B. XBMC_XBOX_r19801.rar -> SVN_20090429.rar
  3) Ftp zur Xbox
  4) Archiv bei der Lokalen Installation auswählen.




Zu einem anderen Build wechseln
------------------------------
Die Option 'Zu einem anderen T3CH wechseln' ermöglichst folgendes:
1) Zu einen bereits lokal installierten T3CH Build wechseln.
oder
2) Aus dem Webarchiv ein altes T3CH Build wählen, runterladen und anschließend installieren.

Anmerkung: Falls bei älteren T3CH Builds das Erstellungsdatum entfernt wurde, muss drauf geachtet werden, dass das aktuelle Build nicht überschrieben wird!


Auto Start mit XBMC Start:
--------------------------
Es ist möglich das Skript mit Start des XBMC zu starten. Dazu verwendet man die autoexec.py.
Diese ist mitinbegriffen, man muss sie nur noch nach 'Q:\scripts' kopieren.

Das Skript kann in 3 Modi gestartet werden:
# SILENT = macht den ganzen Aktualisierungsvorgang ohne GUI.
# NOTIFY = informiert nur über ein neues Build.
# NORMAL = mit GUI und Aufforderungen usw.

Der gewünschte Mode muss in der autoexec.py angegeben werden.  Das Skript hat standardmäßig den 'NOTIFY' Mode angegeben.
Beispiel:
xbmc.executebuiltin("XBMC.RunScript(Q:\\scripts\\T3CH Upgrader\\default.py, NOTIFY)")

Bekannte Probleme:
-------------------
Wenn das XBMC weniger als ~ 31MB freien Speicher hat, *kann* es zu unrar-Problemen kommen. Falls dies passiert, probiere es mit einer geringeren Bildschirmauflösung (NTSC 4:3).

Wenn du nicht mehr weiterkommst, melde dich im dafür vorgesehenen Forum: http://www.xboxmediacenter.com/forum/


Skript geschrieben von BigBellyBilly

Thanks to others for ideas, testing, graphics ... VERY MUCH APPRECIATED !

bigbellybilly AT gmail DOT com


Deutsche Übersetzung (Strings und Readme) von bootsy

bootsy82 AT gmail DOT com