T3CH Upgrader - Skrypt do zarz�dzania, pobierania i instalacji wyda� XBMC grupy T3CH.

Ustawienia wst�pne "Opcje ustawie�"
- Jest par� opcji ustawie� wst�pnych, kt�re musisz wprowadzi� zanim zaczniesz u�ywa� skryptu:

1) "Dysk z plikiem startowym dasha" i "Nazwa pliku startowego dasha"
Umiejscowienie pliku startowego dasha i jego nazwa, s� zwi�zane z Twoj� przer�bk� i u�ywanym biosem ( w Polsce najcz�ciej jest to plik o nazwie evoxdash.xbe na dysku C konsoli - dla przer�bek z czipkiem lub default.xbe umiejscowiony w katalogu dashboard na dysku E konsoli - dla tzw. bezczipowych).
To na bazie tych ustawie� b�dziesz mia� mo�liwo�� ustawienia xbmc jako dashboardu i swobodnego prze��czania si� pomi�dzy wersjami XBMC ( w tym miejscu b�dzie u�yty TEAM XBMC Shortcut.xbe jako skr�t i powi�zany z nim plik konfiguracyjny .cfg )
Nazwa pliku startowego dasha ( np. evoxdash lub mo�esz tutaj wprowadzi� �cie�k� np. dashbord\default )

2) "�cie�ka instalacji"
Jaki dysk i jaki katalog ma by� u�ywany jako roboczy  ( np. E:\MY_BUILDS ) .To do tego katalogu skrypt b�dzie pobiera� archiwa z wersjami XBMC i do niego b�dzie je wypakowywa�. Tak�e do tego katalogu wgrywasz archiwum, je�eli nie masz po��czenia z Internetem i chcesz zainstalowa� now� wersj� z dysku.
Struktura katalog�w po wypakowaniu b�dzie wygl�da�a na przyk�ad tak ( np.  E:\MY_BUILDS\T3CH_2008-01-27\XBMC\ )

3) "Powiadamiaj, gdy nie ma nowej wersji T3CH"
Do skryptu jest do��czony autoexec.py, gdy przekopiujesz go do Q:\scripts b�dziesz otrzymywa� na starcie powiadomienia czy jest nowa wersja czy jej nie ma. Dla wi�kszo�ci z nas wiedza, �e nie ma nowej wersji jest niepotrzebna.

4) "Sprawdzaj aktualizacje skryptu na starcie"
Nic doda� nic uj�� - nowsza wersja prawie zawsze lepsza

5) "Kopiuj UserData do nowej wersji T3CH"
Podstawowa zaleta skryptu - nie tracimy swoich ustawie�, zapisanych ok�adek, miniaturek zdj��, informacji o mediach... itd.
S� tylko dwie znane mi sytuacje, gdzie by�my nie chcieli kopiowa� zawarto�ci UserData:
 - chcemy nie� ca�kowicie czyst� wersj� i zacz�� wszystko od zera
 - mamy ustawion� w pliku profiles.xml w�asn� �cie�k� do katalogu UserData ( na zewn�trz dysku Q ), nie potrzebujemy kopiowa� czego�, co nie jest nam potrzebne.
 
6) "Zawsze pytaj zanim usuniesz archiwum"
Jak kto� lubi jak go pytaj� to zostawi sobie t� opcje - tak naprawd� XBMC ma problemy z wypakowaniem du�ych archiw�w i jest niezr�cznie, gdy wypakowanie si� nie uda�o a skrypt usun�� paczk� i trzeba zacz�� pobieranie od nowa.

7) "Wyczy�� ustawienia"
Czasami stare ustawienia przeszkadzaj� - warto wyczy�ci� i wprowadzi� na nowo, gdy co� nie dzia�a a powinno.

=======================================================================================================
Ekran g��wny "Menu"
- W nag��wku ekranu g��wnego mamy podane informacje o wersji skryptu i aktualnie u�ywanej wersji XBMC ( dobrze jest by� doinformowanym nawet jak nie jest to potrzebne)

1) "Pobierz: <nazwa_wersji>
Wybieramy i skrypt zainstaluje najnowsz� wersj�, ale zanim to zrobimy warto dopasowa� j� do naszych potrzeb ( personalizacja XBMC to podstawa, co cz�owiek to inne wymagania ). S�u�� to tego dwie pozycje menu, umiejscowione zaraz poni�ej i o nich teraz b�dzie mowa (pozycje te niczego nie usuwaj� ani niczego nie kopiuj� tworz� tylko list�, wed�ug kt�rej pliki b�d� kasowane z nowo pobranej wersji lub kopiowane z naszej aktualnej wersji do nowo pobranej podczas procesu instalacji - raz zestawiona listy mo�e s�u�y� nam latami)

2) "Pliki, kt�re zawsze kopiujesz"
Tutaj prawie wszystko jasne - lista plik�w i folder�w, w kt�rych co� zmienili�my �eby nasz xbmc by� bardziej nasz taki i chcemy, aby tak zosta�o. ( nale�y pami�ta�, �e skrypt nie nadpisuje folder�w a jedynie konkretne pliki.)

3) "Pliki, kt�re zawsze usuwasz"
Pozycja ta przydaje si� do usuwania niepotrzebnych scraper�w, wersji j�zykowych, d�wi�k�w startowych, splashy z pobranej wersji.

4) "Wybierz inn� wersj� T3CH"
Z czasem w katalogu roboczym b�dziemy mieli par� wersji XBMC, najnowsza nie znaczy najlepsza. Dzi�ki tej pozycji mo�emy swobodnie prze��cza� si� pomi�dzy wersjami zapisanymi na dysku, a tak�e pobiera� i zainstalowa� dowoln� archiwaln� wersj� XBMC kompilowan� przez T3CH.

5) "Usu� niepotrzebn� wersj� T3CH"
Dysk nie jest z gumy, w ko�cu sko�czy si� na nim miejsce. Jak ju� nazbieramy par� wersji to warto si� zdecydowa� na usuni�cie niekt�rych z nich. Skrypt robi to znacznie szybciej ni� eksplorator w XBMC.

6) "Aktualizuj skrypt"
Aktualizacj� skryptu mo�na aktywowa� r�cznie i takie ustawienia s� domy�lne. Osobi�cie polecam w��czenie opcji automatycznej aktualizacji, trzeba tylko pami�ta�, �e skrypt b�dzie si� za ka�dym razem (na starcie) ��czy� i sprawdza� dost�pno��.

========================================================================================================
Jak dzia�a skrypt i jak zachowywa� si� podczas instalacji
---------------------------
Aby si� wszystko zacz�o wybierz z menu pozycj� "Pobierz: <nazwa_wersji>"
Co si� dzieje podczas instalowania nowej wersji;
1) Pobierane jest archiwum zawieraj�ce XBMC grupy T3CH
2) Paczka jest wypakowywana do katalogu roboczego ustawionego w "opcjach ustawie�".
3) Zostaniesz zapytany czy kopiowa� z aktualnej wersji wszystko, co jest tam dlatego, �e jest to tw�j XBMC.
3) Kopiowana jest zawarto�� twojego UserData ( chyba, �e �wiadomie z tego zrezygnowa�e�).
4) Kopiowane s� skrypty, (je�eli takie same nie istniej� ju� w pobranej wersji) - to samo dzieje si� z wizualizacjami, sk�rami itp.
5) Kopiowane s� pliki i katalogi z w�asnej listy "Pliki, kt�re zawsze kopiujesz".
6) Usuwane s� pliki i katalogi z w�asnej listy "Pliki, kt�re zawsze usuwasz".
7) Zostaniesz zapytany czy chcesz si� prze��czy� na now� wersj�. Kopie bezpiecze�stwa s� zawsze wykonywane poprzez dodanie do nazwy plik�w dodatk�w _new i _old.
8) Zostaniesz zapytany czy uruchomi� ponownie konsole.
Jest bardzo du�a szansa, �e po restarcie twoim oczom uka�e si� nowa wersja XBMC i w dodatku kompilowana przez T3CH!

Opcje dodatkowe;
"Instaluj z zapisanego na dysku":
Je�eli wgrasz do katalogu roboczego paczk� z archiwum od T3CH to w menu g��wnym pojawi ci si� pozycja, dzi�ki kt�rej b�dziesz m�g� przeprowadzi� ca�� instalacj� bez po��czenia z Internetem. Prawie niemo�liwe, �e s� jeszcze takie sytuacje, ale jakby co to w trybie offline te� da si� u�ywa� skryptu T3CH Upgrader.

Zawansowane tryby pracy i instalacja automatyczna;
Skrypt mo�e pracowa� w trzech trybach:
# SILENT = ca�a instalacja w tle,
# NOTIFY = proste informowanie o dost�pnej wersji,
# NORMAL = normalna wsp�praca z u�ytkownikiem, pyta si� prawie o wszystko,

Tak jest mo�liwe, aby skrypt instalowa� nowe wersje bez �adnego pytania nas o zgod� - tzn. bez przesady na ko�cu zapyta si� czy ma wykona� restart. S� dwie opcje takiej zaawansowanej pracy i obie wymagaj� dodatkowej edycji plik�w np. przy u�yciu notepada:

1) po przekopiowaniu do��czonego autoexec.py do Q:\scripts\
edycja pliku Q:\scripts\autoexec.py
wymieniamy argument NOTIFY na SILENT - skrypt zamiast nas powiadamia� o dost�pnej nowej wersji to j� instaluje na starcie konsoli
------------------------------------------------------------------------------------------------------
xbmc.executebuiltin("XBMC.RunScript(Q:\\scripts\\T3CH Upgrader\\default.py, SILENT)")
------------------------------------------------------------------------------------------------------

2) po dodaniu skryptu do ulubionych
edycja pliku \UserData\favourites.xml dodajemy argument SILENT i mamy mo�liwo�� odpalenia trybu w tle wtedy, gdy chcemy.
------------------------------------------------------------------------------------------------------
<favourite name="T3CH Upgrader" thumb="c:\xbmc\userdata\Thumbnails\Programs\e4649b7c.tbn">
RunScript(Q:\scripts\T3CH Upgrader\default.py, SILENT)</favourite>
------------------------------------------------------------------------------------------------------

Znane problemy:
---------------
*czasami* wypakowane archiwum nie zawiera wszystkich folder�w lub plik�w - skrypt wtedy nie kontynuuje instalacji. Najlepszym lekarstwem na to jest restart konsoli i rozpocz�cie od nowa. Problem jest znany, ale co najwa�niejsze nic si� nie dzieje z twoj� aktualnie u�ywan� wersj�.
Jakiekolwiek inne problemy, zapraszam na forum http://www.xboxmediacenter.com/forum/

Skrypt napisany przez BigBellyBilly
bigbellybilly AT gmail DOT com
je�eli masz jakie� pytania po polsku, zapraszam
smuto.promyk AT gmail DOT com
=======================================================================================================
Oryginalny plik readme.txt
T3CH Upgrader - Script to download, install and migrate to latest T3CH builds.

SETUP:
 Install to \scripts\T3CH Upgrader (keep sub folder structure intact)


USAGE: 
 run default.py

At startup Main Menu will indicate the availability of a new T3CH build.

Pre Installation Settings:
--------------------------

You can setup several aspects of the installation using the Settings Menu:

1) Which drive & location to install to

   eg. E:\apps

   Will then result in build being unpacked to;
   eg.  E:\apps\<t3ch_build_name>\XBMC

2) The location of your xbox shortcut that boots to the XBMC as a dashboard, and the name of the shortcut that your mod chip boot too
   It is this location that a new shortcut will be wrutten too inorder to boot to the newly installed T3CH build XBMC.
   It uses the TEAM XBMC Shortcut.xbe  and associated .cfg inorder to achieve this.


   Drive: eg. C:

   DashName:  eg. xbmc
   You can also use a subfolder in the dashname;
   
   eg. dashboard\xbmc

3) Maintain Copies;  
   This is a list of Folders and Files that you want to the post installation to be forced to COPY to new build.

4) Maintain Deletes;  
   This is a list of Folders and Files that you want to the post installation to be forced to DELETE from new build.


To Install a new T3CH Build
---------------------------

Select the Main Menu option "Download: <build_name>"

The following will happen;

1) Downloads T3CH rar
2) Extracts rar to location specified in Settings Menu.
3) Copies old build UserData (if still located within XBMC folder structure).
4) Copies Scripts (if they don't exist in new build) - same for vizualisations, skins etc.
5) Copies additional files/folders as per 'Maintain Copies'.
6) Deletes files/folders as per 'Maintain Deletes'.
7) Prompts to create and install new dash booting shortcuts.
   Backups are always made, named *.xbe_old and *.cfg_old on boot drive.
8) Prompt to Reboot

If all is well after reboot, you will be now running the latest T3CH build!


Local Installation:
-------------------
If you ftp a T3CH build archive (RAR or ZIP) to the designed rar download location (eg. E:\apps\) the Main Menu will show an option to install from that.


Switch To Another Build
-----------------------
The Menu option 'Switch to Another T3CH Build' will allow to either;
1) Switch to an existing local T3CH installation.
or
2) Select from the web archive of old T3CH builds, download, then install.

NB. Although the presented lists of available builds should have had the current build date removed, take caution not to overwrite current build!


Auto startup with XBMC Startup:
-------------------------------
It is possible to have the script start with XBMC by the use of autoexec.py.
It is included, all you need to do is copy it to Q:\scripts

It can startup in three modes:
# SILENT = do whole upgrade without GUI interaction.
# NOTIFY = just inform of new build
# NORMAL = Interactive prompt driven

The required mode needs to be edited into autoexec.py executebuiltin.  The script comes with it set to NOTIFY


Knonw Problems:
---------------
*sometimes* the newly extracted rar folder strcture doesnt appear to exist, and the script won't continue.
This is known problem and the best thing to do is, reboot and try again, your existing XBMC installation has not been touched.

If you're stuck, post in the appropiate forum at http://www.xboxmediacenter.com/forum/


Written By BigBellyBilly

Thanks to others for ideas, testing, graphics ... VERY MUCH APPRECIATED !

bigbellybilly AT gmail DOT com