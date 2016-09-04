# -*- coding: utf-8 -*-

import os
import sys
import xbmc
import urllib
import urllib2
import xbmcvfs
import xbmcaddon
import xbmcgui
import xbmcplugin
import uuid
import unicodedata
import re
import string
import difflib
import HTMLParser
from operator import itemgetter
from urlparse import urlparse
import base64

__addon__ = xbmcaddon.Addon()
__author__ = __addon__.getAddonInfo('author')
__scriptid__ = __addon__.getAddonInfo('id')
__scriptname__ = __addon__.getAddonInfo('name')
__version__ = __addon__.getAddonInfo('version')
__language__ = __addon__.getLocalizedString

__cwd__ = unicode(xbmc.translatePath(__addon__.getAddonInfo('path')), 'utf-8')
__profile__ = unicode(xbmc.translatePath(__addon__.getAddonInfo('profile')), 'utf-8')
__resource__ = unicode(xbmc.translatePath(os.path.join(__cwd__, 'resources', 'lib')), 'utf-8')
__temp__ = unicode(xbmc.translatePath(os.path.join(__profile__, 'temp', '')), 'utf-8')

sys.path.append(__resource__)

def append_subtitle(item):
    title = item['filename']
    listitem = xbmcgui.ListItem(label='English',
                                label2=title,
                                iconImage='5',
                                thumbnailImage='en')

    listitem.setProperty("sync", 'true')
    listitem.setProperty("hearing_imp", 'false')

    url = "plugin://%s/?action=download&link=%s" % (__scriptid__, item['link'])
    # add it to list, this can be done as many times as needed for all subtitles found
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=listitem, isFolder=False)

def get_params():
    param = {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = paramstring
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]

    return param

def parse_url(url):
    urlParts = urlparse(url)
    netlocParts = urlParts.netloc.split('@')
    user, password = netlocParts[0].split(':')
    cleanUrl = "%s://%s%s" % (urlParts.scheme, netlocParts[1], urlParts.path)
    return cleanUrl, user, password

def check_source(url):
    cleanUrl, username, password = parse_url(url)

    request = urllib2.Request(cleanUrl)
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    request.get_method = lambda : 'HEAD'
    result = urllib2.urlopen(request)

    return result.getcode() == 200

params = get_params()

if params['action'] == 'search' or params['action'] == 'manualsearch':
    item = {}
    file_original_path = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))  # Full path
    item['link'] = os.path.splitext(file_original_path)[0]+'.srt'
    item['filename'] = os.path.basename(item['link'])
    if (check_source(item['link'])):
        append_subtitle(item)

elif params['action'] == 'download':
    sub = params["link"]
    listitem = xbmcgui.ListItem(label=sub)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sub, listitem=listitem, isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))  # send end of directory to XBMC
