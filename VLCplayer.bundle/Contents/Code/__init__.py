# import for regular expressions
import re
import datetime
import time
# for more complex JSON
#import demjson
# for urlopen
import urllib
# to launch/exit an application
import os, subprocess, signal
import errno
# for processing CSV strings
import csv

# http://dev.plexapp.com/docs/api/constkit.html

# VLC output parameters:
#1) :sout=#transcode{vcodec=h264,vb=800,acodec=mpga,ab=128,channels=2,samplerate=44100}:http{mux=ts,dst=:11223/} :sout-all :sout-keep
#2) :sout=#transcode{vcodec=h264,vb=800,acodec=mpga,ab=128,channels=2,samplerate=44100}:http{mux=ts,dst=:11223/stream.ts} :sout-all :sout-keep
# vb = video bitrate
# ab = audio bitrate
# acodec = mpga => MP3
# mux = ts => Transport Stream
# http://www.videolan.org/developers/vlc/share/lua/intf/modules/httprequests.lua
# an alternative:
# http://n0tablog.wordpress.com/2009/02/09/controlling-vlc-via-rc-remote-control-interface-using-a-unix-domain-socket-and-no-programming/
####################################################################################################

PREFIX       = '/video/vlcplayer'
NAME         = 'VLC Player'
TITLE        = 'VLC Plugin'
ART          = 'art-default.jpg'
ICON         = 'icon-vlc.png'
#URL_VLC      = 'http://%s:%s' % (Prefs['vlc_host'], Prefs['vlc_port_stream']) # filled once on start (static)
VLC_APP_PATH = 'C:\Program Files (x86)\VideoLAN\VLC\\'
VLC_APP_FILE = 'vlc.exe'
VLC_APP      = VLC_APP_PATH + VLC_APP_FILE + ' '
VLC_ARGS0    = '--sout=#'
VLC_ARGS1    = 'transcode{vcodec=h264,vb=800,acodec=mpga,ab=128,channels=2,samplerate=44100}'
VLC_ARGS2    = 'http{dst=:%s/%s} --sout-all --sout-keep'
VLC_ARGS3    = ' --extraintf=http --http-host=%s --http-port=%s --http-password=%s'
VLC_ARGS     = VLC_ARGS0+VLC_ARGS2+VLC_ARGS3
VLC_ARGS_T   = VLC_ARGS0+VLC_ARGS1+':'+VLC_ARGS2+VLC_ARGS3
VLC_REQ      = 'http://:%s@%s:%s/requests/status.xml'
VLC_CON      = 'http://:%s@%s:%s/?control='
PLEX_PREFS   = 'http://localhost:32400/:/plugins/com.plexapp.plugins.vlcplayer/prefs/set?'

# Great regex tester -> http://regex101.com/
ST_DOM_MAP   = '(?:(?:[0-9a-zA-Z_-]+\.){1,3})[a-zA-Z]{2,4}' #WARNING: group must be non-extracting due to use with ST_PATH_MAP in ST_URL_MAP2
RE_DOM_MAP   = Regex('^%s$' % (ST_DOM_MAP))
ST_IP_MAP    = '(?:[0-9]{1,3}\.){3}[0-9]{1,3}' #WARNING: group must be non-extracting due to use with ST_PATH_MAP in ST_URL_MAP
RE_IP_MAP    = Regex('^%s$' % (ST_IP_MAP))
ST_PORT_MAP  = '[1-9][0-9]{0,4}'
RE_PORT_MAP  = Regex('^%s$' % (ST_PORT_MAP))
ST_PATH_MAP  = '((/)(?(2)(?:[0-9a-zA-Z _-]+/)+))?' # added space character
ST_FILE_MAP  = '([0-9a-zA-Z _\-\.]+\.[0-9a-zA-Z]{2,4})?' # added space character
ST_PAGE_MAP  = '%s(?(2)|/?)%s' % (ST_PATH_MAP, ST_FILE_MAP) # WARNING: allows for filename only (initial slash optional)
RE_PAGE_MAP  = Regex('^%s$' % (ST_PAGE_MAP)) # path is group(1), file is group(3)
ST_URL_MAP   = 'http://%s:%s%s' % (ST_IP_MAP, ST_PORT_MAP, ST_PAGE_MAP)
RE_URL_MAP   = Regex('^%s$' % (ST_URL_MAP))
ST_URL_MAP2  = 'http://%s%s' % (ST_DOM_MAP, ST_PAGE_MAP)
RE_URL_MAP2  = Regex('^%s$' % (ST_URL_MAP2))
ST_FQFILE_MAP = '[a-zA-Z]:%s' % (ST_PAGE_MAP)
RE_FQFILE_MAP = Regex('^%s$' % (ST_FQFILE_MAP))
RE_YES_NO    = Regex('^(?i)(?:y(?:es)?|no?)$')
RE_COMMAS    = Regex('(,)(?=(?:[^\"]|\"[^\"]*\")*$)') # all commas not between quotes

VLC_VIDEO_FORMATS = ['360p',	'720p',		'1080p']
VLC_FMT           = [18,		22,			37]
VLC_CONTAINERS    = ['mpegts',	'mpegts',	'mpegts']
VLC_VIDEOCODEC    = ['h264',	'h264',		'h264']
VLC_AUDIOCODEC    = ['mp3',		'mp3',		'mp3']
VLC_VIDEORES      = ['360',		'720',		'1080']
VLC_STREAM_OPT    = 'mpegts'

METADATA     = '{"apiVersion":"2.1","data":{"id":"Hx9TwM4Pmhc","uploaded":"2013-04-25T14:00:46.000Z","updated":"2014-01-27T02:24:39.000Z","uploader":"Unknown","category":"Various","title":"VLC Video Stream","description":"This video is being streamed by VLC player from a direct video URL.","thumbnail":{"sqDefault":"http://i1.ytimg.com/vi/Hx9TwM4Pmhc/default.jpg","hqDefault":"http://i1.ytimg.com/vi/Hx9TwM4Pmhc/hqdefault.jpg"},"player":{"default":"http://www.youtube.com/watch?v=Hx9TwM4Pmhc&feature=youtube_gdata_player","mobile":"http://m.youtube.com/details?v=Hx9TwM4Pmhc"},"content":{"5":"http://www.youtube.com/v/Hx9TwM4Pmhc?version=3&f=videos&app=youtube_gdata","1":"rtsp://r6---sn-o097zuek.c.youtube.com/CiILENy73wIaGQkXmg_OwFMfHxMYDSANFEgGUgZ2aWRlb3MM/0/0/0/video.3gp","6":"rtsp://r6---sn-o097zuek.c.youtube.com/CiILENy73wIaGQkXmg_OwFMfHxMYESARFEgGUgZ2aWRlb3MM/0/0/0/video.3gp"},"duration":3600,"aspectRatio":"widescreen","rating":4.1,"likeCount":"1","ratingCount":1,"viewCount":1,"favoriteCount":1,"commentCount":0,"accessControl":{"comment":"allowed","commentVote":"allowed","videoRespond":"moderated","rate":"allowed","embed":"allowed","list":"allowed","autoPlay":"allowed","syndicate":"allowed"}}}'

# Shorthands:
# Resource.ExternalPath() => R()
# Resource.SharedExternalPath() => S()
# Resource.Load() => L()
####################################################################################################
# Global variables
vlc_proc = None
####################################################################################################
def Start():
	Log.Debug("EXECUTING: Start()")

	Plugin.AddPrefixHandler(PREFIX, MainMenu, TITLE, ICON, ART)

	ObjectContainer.title1 = NAME
	ObjectContainer.art = R(ART)
	ObjectContainer.no_cache = True

	DirectoryObject.thumb = R(ICON)
	DirectoryObject.art = R(ART)
	VideoClipObject.thumb = R(ICON)
	VideoClipObject.art = R(ART)

	TrackObject.thumb = R(ICON)

	HTTP.CacheTime = CACHE_1HOUR
	
	# Store user "globals" in the Dict
	Dict["Initialized"] = False
	Dict["Today"] = datetime.date.today()
	Dict["VLCpid"] = -1
	Dict["VLCconfigured"] = False
	Dict['fq_file_changed'] = False
	Dict['fq_file_current'] = ''
	Dict['fq_url_changed'] = False
	Dict['fq_url_current'] = ''
	
	Log.Debug('VLC_APP= '+VLC_APP)
	Log.Debug('VLC_ARGS= '+VLC_ARGS)
	Log.Debug('VLC_ARGS_T= '+VLC_ARGS_T)
	Log.Debug('ST_PAGE_MAP= '+ST_PAGE_MAP)
	Log.Debug('ST_URL_MAP= '+ST_URL_MAP)
	Log.Debug('ST_URL_MAP2= '+ST_URL_MAP2)
	Log.Debug('ST_FQFILE_MAP= '+ST_FQFILE_MAP)
	#InitializePrefs() => can't do this here.  It is too early.  Moved to MainMenu()

####################################################################################################
@route('/video/vlcplayer/InitializePrefs')
def InitializePrefs():
# All non-compliant Prefs will be reset to their default values
	if Dict["Initialized"]:
		return
	Log.Debug("EXECUTING: InitializePrefs()")
	Dict["Initialized"] = True

	match = re.search(RE_YES_NO, Prefs['url_service'])
	if match == None:
		u = urllib.urlopen(PLEX_PREFS+'url_service=')
		
	match = re.search(RE_YES_NO, Prefs['transcode'])
	if match == None:
		u = urllib.urlopen(PLEX_PREFS+'transcode=')
		
	match = re.search(RE_IP_MAP, Prefs['vlc_host'])
	if match == None:
		u = urllib.urlopen(PLEX_PREFS+'vlc_host=')

	match = re.search(RE_PORT_MAP, Prefs['vlc_port_stream'])
	if match == None:
		u = urllib.urlopen(PLEX_PREFS+'vlc_port_stream=')
		
	match = re.search(RE_PORT_MAP, Prefs['vlc_port_control'])
	if match == None:
		u = urllib.urlopen(PLEX_PREFS+'vlc_port_control=')
		
	match = re.search(RE_PAGE_MAP, Prefs['vlc_page'])
	if match == None:
		u = urllib.urlopen(PLEX_PREFS+'vlc_page=')
		
	match = re.search(RE_FQFILE_MAP, Prefs['fq_file'])
	if match == None:
		u = urllib.urlopen(PLEX_PREFS+'fq_file=')
	else:
		Dict['fq_file_current'] = Prefs['fq_file']
		
	match = re.search(RE_URL_MAP2, Prefs['fq_url'])
	if match == None:
		u = urllib.urlopen(PLEX_PREFS+'fq_url=')
	else:
		Dict['fq_url_current'] = Prefs['fq_url']
		
	return

# Force set a prference:
# u = urllib.urlopen('http://{PMS_IP}:32400/:/plugins/{PLUGIN STRING}/prefs/set?{VARIABLE}={VALUE}')
# set vlc_page to defualt >>
# u = urllib.urlopen('http://localhost:32400/:/plugins/com.plexapp.plugins.vlcplayer/prefs/set?vlc_page=')
	
####################################################################################################
def ValidatePrefs():
# NOTE: MessageContainer() is deprecated
# NOTE: Returning an ObjectContainer() with an error does not display the message.
#       Probably because Plex is already in a popup (Preferences).
	Log.Debug("EXECUTING: ValidatePrefs()")
	Log.Debug("***************************************")
	
	match = re.search(RE_YES_NO, Prefs['url_service'])
	if match != None:
		Log.Debug("SERV  url_service= "+match.group(0))
	else:
		Log.Debug("SERV  url_service= INVALID")
		
	match = re.search(RE_YES_NO, Prefs['transcode'])
	if match != None:
		Log.Debug("STRM  transcode= "+match.group(0))
	else:
		Log.Debug("STRM  transcode= INVALID")
		
	match = re.search(RE_IP_MAP, Prefs['vlc_host'])
	if match != None:
		Log.Debug("HOST  vlc_host= "+match.group(0))
	else:
		Log.Debug("HOST  vlc_host= INVALID")
		
	match = re.search(RE_PORT_MAP, Prefs['vlc_port_stream'])
	if match != None:
		Log.Debug("PORT  vlc_port_stream= "+match.group(0))
	else:
		Log.Debug("PORT  vlc_port_stream= INVALID")
		
	match = re.search(RE_PORT_MAP, Prefs['vlc_port_control'])
	if match != None:
		Log.Debug("PORT  vlc_port_control= "+match.group(0))
	else:
		Log.Debug("PORT  vlc_port_control= INVALID")
	str_page = Prefs['vlc_page']
	if str_page[0] != '/':
		if str_page == ' ':
			str_page = ''
		else:
			str_page = '/' + Prefs['vlc_page'] # does not start with a "/"
	
	match = re.search(RE_PAGE_MAP, str_page)
	if match != None:
		Log.Debug("PAGE  vlc_page= "+match.group(0))
	else:
		Log.Debug("PAGE  vlc_page= INVALID")

	url_vlc = 'http://%s:%s%s' % (Prefs['vlc_host'], Prefs['vlc_port_stream'], str_page) # dynamic
	match = re.search(RE_URL_MAP, url_vlc)
	if match != None:
		Log.Debug("URL  vlc_url= "+match.group(0))
	else:
		Log.Debug("URL  vlc_url= INVALID")
		
	fq_file = Prefs['fq_file']
	if fq_file:
		fq_file_chng = fq_file.find('\\')
		if fq_file_chng >= 0:
			fq_file = fq_file.replace('\\', '/') # change backslashes to frontslashes for pattern match
			Log.Debug('*****'+fq_file)
		match = re.search(RE_FQFILE_MAP, fq_file)
		if match != None:
			if fq_file_chng >= 0:
				u = urllib.urlopen(PLEX_PREFS+'fq_file='+fq_file)
			if fq_file != Dict['fq_file_current']:
				Dict['fq_file_current'] = fq_file
				Dict['fq_file_changed'] = True
			Log.Debug("FILE  fq_file= "+match.group(0))
		else:
			Log.Debug("FILE  fq_file= INVALID")
		
	if Prefs['fq_url']:
		match = re.search(RE_URL_MAP2, Prefs['fq_url'])
		if match != None:
			if Prefs['fq_url'] != Dict['fq_url_current']:
				Dict['fq_url_current'] = Prefs['fq_url']
				Dict['fq_url_changed'] = True
			Log.Debug("URL  fq_url= "+match.group(0))
		else:
			Log.Debug("URL  fq_url= INVALID")
		
	Log.Debug("***************************************")
	
	return
	
####################################################################################################
@route('/video/vlcplayer/PrefValidationNotice')
def PrefValidationNotice():
	Log.Debug("EXECUTING: PrefValidationNotice()")
	
	match = re.search(RE_YES_NO, Prefs['url_service'])
	if match == None:
		return ObjectContainer(header="Settings Error", message="The URL Service setting is invalid.", no_cache=True)

	match = re.search(RE_YES_NO, Prefs['transcode'])
	if match == None:
		return ObjectContainer(header="Settings Error", message="The stream Transcode setting is invalid.", no_cache=True)

	match = re.search(RE_IP_MAP, Prefs['vlc_host'])
	if match == None:
		return ObjectContainer(header="Settings Error", message="The IP address setting is invalid.", no_cache=True)

	match = re.search(RE_PORT_MAP, Prefs['vlc_port_stream'])
	if match == None:
		return ObjectContainer(header="Settings Error", message="The IP stream port setting is invalid.", no_cache=True)

	match = re.search(RE_PORT_MAP, Prefs['vlc_port_control'])
	if match == None:
		return ObjectContainer(header="Settings Error", message="The IP control port setting is invalid.", no_cache=True)

	str_page = Prefs['vlc_page']
	if str_page[0] != '/':
		if str_page == ' ':
			str_page = ''
		else:
			str_page = '/' + Prefs['vlc_page'] # does not start with a "/"
	
	match = re.search(RE_PAGE_MAP, str_page)
	if match == None:
		return ObjectContainer(header="Settings Error", message="The page setting is invalid.", no_cache=True)

	url_vlc = 'http://%s:%s%s' % (Prefs['vlc_host'], Prefs['vlc_port_stream'], str_page) # dynamic
	match = re.search(RE_URL_MAP, url_vlc)
	if match == None:
		return ObjectContainer(header="Settings Error", message="The settings do not result in a valid url.", no_cache=True)
	Log.Debug("PASSED: PrefValidationNotice()")

	if Prefs['fq_file']:
		match = re.search(RE_FQFILE_MAP, Prefs['fq_file'])
		if match == None:
			return ObjectContainer(header="Settings Error", message="The FQ File setting is invalid.", no_cache=True)

	if Prefs['fq_url']:
		match = re.search(RE_URL_MAP2, Prefs['fq_url'])
		if match == None:
			return ObjectContainer(header="Settings Error", message="The FQ URL setting is invalid.", no_cache=True)

	return None

####################################################################################################
# the following line performs the same as the Plugin.AddPrefixHandler() method above
#@handler(PREFIX, TITLE, thumb=ICON, art=ART)
def MainMenu():
	global vlc_proc
	InitializePrefs()

	do = DirectoryObject(key = Callback(SecondMenu), title = "Example Directory")

	voc = PrefValidationNotice()
	if not voc == None:
		voc.add(do)
		# attach the settings/preferences
		voc.add(PrefsObject(title = L('Preferences')))
		Log.Debug("FAILED: PrefValidationNotice()")
		return voc
		
# properties can be filled by parameters in the "New" or set as properties above
#	oc = ObjectContainer(title1=NAME, art=R(ART))
	oc = ObjectContainer()
	oc.add(do)
	
	if Prefs['transcode'][0] == 'y':
		vlc_args = VLC_ARGS_T
	else:
		vlc_args = VLC_ARGS
	vlc_args = vlc_args % (Prefs['vlc_port_stream'], Prefs['vlc_page'], Prefs['vlc_host'], Prefs['vlc_port_control'], Prefs['password'])
	
	# access requires no username, only a password
	url_vlc_req = VLC_REQ % (Prefs['password'], Prefs['vlc_host'], Prefs['vlc_port_control'])
	url_vlc_cmd = url_vlc_req + '?command='
#	url_vlc_cmd = VLC_CON % (Prefs['password'], Prefs['vlc_host'], Prefs['vlc_port_control'])

	# Check to see if VLC is actually running
	Dict["VLCpid"] = AppRunning(VLC_APP_FILE)
	if int(Dict["VLCpid"]) < 0:
#		fq_file = '"'+str(Prefs['fq_file']).replace('/', '\\')+'"' # change frontslashes to backslashes (Windows)
		fq_file = 'file:///'+str(Prefs['fq_file']).replace(' ', '%20')
		oc.add(DirectoryObject(key = Callback(StartApp, app_app=VLC_APP, app_file=fq_file, app_args=vlc_args), title = "Launch VLC"))
	elif not Dict["VLCconfigured"]:
		oc.add(DirectoryObject(key = Callback(ConfigureApp, app_url=url_vlc_cmd), title = "Configure VLC"))
	else:
		oc.add(DirectoryObject(key = Callback(StopApp, app_pid=Dict["VLCpid"]), title = "Exit VLC"))		
		
	# Log current settings/preferences click icon
	Log.Debug("#######################################")
	Log.Debug("### vlc_host= "+Prefs['vlc_host'])
	Log.Debug("### vlc_port_stream= "+Prefs['vlc_port_stream'])
	Log.Debug("### vlc_port_control= "+Prefs['vlc_port_control'])
	Log.Debug("### vlc_page= "+Prefs['vlc_page'])
	str_page = Prefs['vlc_page']
	if str_page[0] != '/':
		if str_page == ' ':
			str_page = ''
		else:
			str_page = '/' + Prefs['vlc_page'] # does not start with a "/"
	url_vlc = 'http://%s:%s%s' % (Prefs['vlc_host'], Prefs['vlc_port_stream'], str_page) # dynamic
	Log.Debug("### vlc_url= "+url_vlc)
	Log.Debug("#######################################")
	
	# https://wiki.videolan.org/VLC_HTTP_requests/
	oc.add(DirectoryObject(key = Callback(PlayVLC, url=url_vlc_cmd+'pl_play'), title = "Play VLC"))
	oc.add(DirectoryObject(key = Callback(PauseVLC, url=url_vlc_cmd+'pl_pause'), title = "Pause VLC"))
	oc.add(DirectoryObject(key = Callback(StopVLC, url=url_vlc_cmd+'pl_stop'), title = "Stop VLC"))
#	oc.add(DirectoryObject(key = Callback(GetStatusMetaVLC, url=url_vlc_req), title = "Status VLC"))
	oc.add(DirectoryObject(key = Callback(Refresh), title = "Refresh"))

	if Dict['fq_file_changed']:
		SourceVLC(url_vlc_cmd, Prefs['fq_file'])
	elif Dict['fq_url_changed']:
		SourceVLC(url_vlc_cmd, Prefs['fq_url'])

	if Prefs['url_service'][0] == 'y':
		mo = MediaObject(parts=[PartObject(key=HTTPLiveStreamURL(url_vlc))])
		# the following instruction causes the framework to call the URL service
		# see: \Contents\Info.plist -> PlexURLServices
		# see: \Contents\URL Services\VLCplayer\ServiceCode.pys
		vco = VideoClipObject(title="Play VLC Stream", url=url_vlc)
		vco.add(mo)
	else:
		vco = CreateVideoClipObject(url_vlc, Dict["Today"]) # date only
#		vco = CreateVideoClipObject(url_vlc, datetime.datetime.today()) -> CreateVideoClipObject() code commented out

	oc.add(vco)
	# provide for changing the host and port etc.
	oc.add(PrefsObject(title = L('Preferences')))
	
	Dict['fq_file_changed'] = False
	Dict['fq_url_changed'] = False

#	details = demjson.encode(oc) -> JSONEncodeError('can not encode object into a JSON representation',obj)
#	Log.Debug(details)
	return oc

####################################################################################################
@route('/video/vlcplayer/Refresh')
def Refresh():
	oc = ObjectContainer(title1='Refresh')
	return oc
	
####################################################################################################
@route('/video/vlcplayer/SecondMenu')
def SecondMenu():
	oc = ObjectContainer(title1='Second Menu')
	do = DirectoryObject(key = Callback(ThirdMenu), title = "Example Directory")
	oc.add(do)
	return oc
	
####################################################################################################
@route('/video/vlcplayer/ThirdMenu')
def ThirdMenu():
	oc = ObjectContainer(title1='Third Menu')
	do = DirectoryObject(key = Callback(FourthMenu), title = "Dead end")
	oc.add(do)
	return oc
	
####################################################################################################
@route('/video/vlcplayer/FourthMenu')
def FourthMenu():
	oc = ObjectContainer(title1='Fourth Menu')
	return oc
	
####################################################################################################
@route('/video/vlcplayer/PlayVLC')
def PlayVLC(url):
	if int(Dict["VLCpid"]) > 0:
		Log.Debug("EXECUTING: PlayVLC("+url+")")
		page = urllib.urlopen(url).read()
		# HTTP.Request won't accept HTTP Basic Authentication credentials in the URL
		#page = HTTP.Request(url).content
	oc = ObjectContainer(title1='VLC Play')
	return oc
	
####################################################################################################
@route('/video/vlcplayer/PauseVLC')
def PauseVLC(url):
	if int(Dict["VLCpid"]) > 0:
		Log.Debug("EXECUTING: PauseVLC("+url+")")
		page = urllib.urlopen(url).read()
	oc = ObjectContainer(title1='VLC Pause')
	return oc
	
####################################################################################################
@route('/video/vlcplayer/StopVLC')
def StopVLC(url):
	if int(Dict["VLCpid"]) > 0:
		Log.Debug("EXECUTING: StopVLC("+str(url)+")")
		page = urllib.urlopen(url).read()
	oc = ObjectContainer(title1='VLC Stop')
	return oc
	
####################################################################################################
@route('/video/vlcplayer/SourceVLC')
def SourceVLC(url, source):
	if int(Dict["VLCpid"]) > 0:
		Log.Debug("EXECUTING: SourceVLC("+str(url)+'in_enqueue&input=file:///'+source+")")
		page = urllib.urlopen(url+'pl_stop').read()
#		page = urllib.urlopen(url+'pl_empty').read()
		page = urllib.urlopen(url+'in_play&input=file:///'+source.replace(' ', '%20')).read()
		page = urllib.urlopen(url+'pl_pause').read()
#		time.sleep(1)
#		Log.Debug(url+'pl_next')
#		page = urllib.urlopen(url+'pl_next').read() # works in browser, not here?
	return
	
####################################################################################################
@route('/video/vlcplayer/GetStatusMetaVLC')
def GetStatusMetaVLC(url):
	if int(Dict["VLCpid"]) > 0:
		Log.Debug("EXECUTING: GetStatusMetaVLC("+url+")")
		page = urllib.urlopen(url).read()
		Log.Debug('STATUS: '+page)
	oc = ObjectContainer(title1='Status VLC')
	return oc
	
####################################################################################################
#   This function checks to see if the application is running.
#       app_app_file - application file name only (with extension)
#
@route('/video/vlcplayer/AppRunning')
def AppRunning(app_app_file):
	Log.Debug("EXECUTING: AppRunning()")
	# get PID for vlc.exe if running
	procs = subprocess.check_output(['tasklist', '/fo', 'csv']) # get the list of processes
	procEntry = [row for row in procs.split('\n') if row.find(app_app_file) > 0]
	if len(procEntry) > 0:
		if len(procEntry) > 1:
			Log.Debug("# App Procs= " + str(len(procEntry)))
#		Log.Debug("@@@@@@@ " + procEntry[0])
		temp = re.split(RE_COMMAS, procEntry[0])[0::2] # remove all commas not between quotes
#		Log.Debug("@@@@@@@ "+temp[1])
		procArray = list(csv.reader(temp, delimiter=','))
#		Log.Debug("@@@@@@@ "+str(procArray))
		ret = int(procArray[1][0]) # set the indicator
	else:
		ret = -1
	Log.Debug("APP_PID= "+str(ret))
	return ret
	
####################################################################################################
#   This function configures the application.
#       app_app_file - application file name only (with extension)
#
@route('/video/vlcplayer/ConfigureApp')
def ConfigureApp(app_url):
	Log.Debug("EXECUTING: ConfigureApp()")
	Dict["VLCconfigured"] = True
	oc = ObjectContainer(title1='Configured App')
	return oc
	
####################################################################################################
#   This function launches the application.
#       app_app - fully qualified application name
#       app_file - file to open using the application
#       app_args - application arguments
#
@route('/video/vlcplayer/StartApp')
def StartApp(app_app, app_file, app_args):
	global vlc_proc
	if int(Dict["VLCpid"]) < 0:
		Log.Debug("EXECUTING: StartApp()")
		# Start the app in a new thread in the security context of the calling process
		vlc_proc = subprocess.Popen([str(app_app), [app_file], [ClearNoneString(app_args)]])
		time.sleep(2)
#		Log.Debug('Running Application:  {' + str(app_app) + '}, with the following arguments {' + subprocess.list2cmdline([[ClearNoneString(app_file)], [ClearNoneString(app_args)]]) + '}')
		Dict["VLCpid"] = int(vlc_proc.pid)
		Dict["VLCconfigured"] = True
		oc = ObjectContainer(title1='Launched App')
	else:
		oc = ObjectContainer(title1='App is running')
	return oc
	
####################################################################################################
#   This function terminates the application.
#       [Takes no arguments]
#
@route('/video/vlcplayer/StopApp')
def StopApp(app_pid):
	global vlc_proc
	if int(app_pid) > 0:
		Log.Debug("EXECUTING: StopApp()")
		Dict["VLCconfigured"] = False
		if vlc_proc:
			Log.Debug("app_proc exists")
			vlc_proc.terminate()
			vlc_proc.wait() # wait for process to stop
		else:
			Log.Debug("no app_proc")
			try:
				os.kill(int(app_pid), signal.SIGTERM)
#				os.kill(pid, 0) #  test to see if process is running (pid > 0)
			except OSError as err:
				if err.errno == errno.ESRCH:
					# ESRCH == No such process
					Log.Debug("%%%%% No such process: "+str(app_pid))
				elif err.errno == errno.EPERM:
					# EPERM clearly means there's a process to deny access to
					Log.Debug("%%%%% Access denied to process: "+str(app_pid))
				else:
					# According to "man 2 kill" possible error values are
					# (EINVAL, EPERM, ESRCH)
					Log.Debug("%%%%% Error killing process: "+str(app_pid))
		oc = ObjectContainer(title1='Exited App')
	else:
		oc = ObjectContainer(title1='App is not running')
	return oc
	
####################################################################################################
#   Converts a string with a None value, to an empty string.
#       value - the value to convert to an empty string, if it is of None value
#
@route('/video/vlcplayer/ClearNoneString')
def ClearNoneString(value):
	if((value is None) or (value is '{noneText}')):
		return ''
	return value
	
####################################################################################################
@route('/video/vlcplayer/CreateVideoClipObject')
def CreateVideoClipObject(url, originally_available_at, include_container=False):

	try:
		details = JSON.ObjectFromString(METADATA, encoding=None)['data']
	except:
		raise Ex.MediaNotAuthorized

	try:
		title = details['title']
	except:
		title = 'No title'

	try:
		summary = details['description']
	except:
		summary = 'No description'

	thumb = ''
	
	try:
		rating = details['rating'] * 2
	except:
		rating = None
	
	try:
		tags = details['tags']
	except:
		tags = []
	
	try:
		duration = details['duration'] * 1000
	except:
		raise Ex.MediaNotAvailable
	if not isinstance(duration, int):
		raise Ex.MediaNotAvailable
	
	try:
		# can be more than one
		genres = [details['category']]
	except:
		genres = ['Unknown genre']
	
#	types = demjson.encode(Container) # Framework.api.constkit.Containers -> can't convert to JSON
#	Log.Debug("### "+Container.MP4)

	# When re-entering CreateVideoClipObject(), originally_available_at can become a string object instead of a datetime.date or a datetime.datetime object
	if isinstance(originally_available_at, str):
		# someting changes the space between the date and time to a '+' when using a datetime object
		originally_available_at = originally_available_at.replace('+',' ')
		originally_available_at = originally_available_at[0:10] # for date only
		Log.Debug("### STR OAA= "+originally_available_at)
		originally_available_at = datetime.datetime.strptime(originally_available_at, '%Y-%m-%d') # for date only
#		#originally_available_at = datetime.datetime.strptime(originally_available_at, '%Y-%m-%d %H:%M:%S.%f') => %f is not supported: use the following
#		nofrag, frag = originally_available_at.split('.')
#		nofrag_dt = datetime.datetime.strptime(nofrag, "%Y-%m-%d %H:%M:%S")
#		originally_available_at = nofrag_dt.replace(microsecond=int(frag))
		Log.Debug("### STR->DATE OAA= "+originally_available_at.isoformat())
	else:
		if isinstance(originally_available_at, datetime.date):
			Log.Debug("### DATE OAA= "+originally_available_at.strftime('%Y-%m-%d')) # for date only
#			Log.Debug("### DATE OAA= "+originally_available_at.isoformat())
		else:
			Log.Debug("### DATE OAA= ERROR")
	
	vco = VideoClipObject(
		key = Callback(CreateVideoClipObject, url=url, originally_available_at=originally_available_at, include_container=True),
		rating_key = 'VLC Player rating_key', #url,
		title = title,
		summary = summary,
		thumb = Resource.ContentsOfURLWithFallback(thumb),
		rating = rating,
		tags = tags,
		originally_available_at = originally_available_at,
		duration = duration,
		genres = genres,
		items = MediaObjectsForURL(url)
#		items = [
#			MediaObject(
#				parts = [PartObject(key=url)],
#				container = 'mpegts', # no Container.MPEGTS
#				video_codec = VideoCodec.H264,
#				video_resolution = '360',
#				audio_codec = AudioCodec.MP3,
#				audio_channels = 2,
#				optimized_for_streaming = True
#			)
#		]
	)

	if include_container:
		return ObjectContainer(objects=[vco])
	else:
		return vco
		
####################################################################################################
@route('/video/vlcplayer/MediaObjectsForURL')
def MediaObjectsForURL(url):

	items = []
	
	fmts = list(VLC_VIDEO_FORMATS)
	fmts.reverse()
	
	for fmt in fmts:
		index = VLC_VIDEO_FORMATS.index(fmt)
		
		items.append(MediaObject(
#			parts = [PartObject(key=Callback(PlayVideo, url=url, default_fmt=fmt))],
			parts = [PartObject(key=url)],
			container = VLC_CONTAINERS[index],
			video_codec = VLC_VIDEOCODEC[index],
			audio_codec = VLC_AUDIOCODEC[index],
			video_resolution = VLC_VIDEORES[index],
			audio_channels = 2,
			optimized_for_streaming = (VLC_CONTAINERS[index] == VLC_STREAM_OPT),
		))
			
	return items
	
####################################################################################################
@route('/video/vlcplayer/PlayVideo')
def PlayVideo(url=None, default_fmt=None, **kwargs):
	
	if not url:
		return None
	return IndirectResponse(VideoClipObject, key=url)
#	return Redirect(url) # this results in a file download of the stream

####################################################################################################
