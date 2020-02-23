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
from urllib.parse import urlparse
import base64
import shutil

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

def log(module, msg):
    xbmc.log((u"### [%s] %s" % (module, msg,)), level=xbmc.LOGERROR)

def append_subtitle(item):
    title = item['filename']
    listitem = xbmcgui.ListItem(label='English',
                                label2=title,
                                iconImage='5',
                                thumbnailImage='en')

    listitem.setProperty("sync", 'true')
    listitem.setProperty("hearing_imp", 'false')

    url = "plugin://%s/?action=download&link=%s&filename=%s" % (__scriptid__, item['link'], title)

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

def createRequestResult(url, head):
    cleanUrl, username, password = parse_url(url)

    request = urllib2.Request(cleanUrl)
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    if head:
        request.get_method = lambda : 'HEAD'
    return urllib2.urlopen(request)

def check_source(url):
    result = createRequestResult(url, True)

    return result.getcode() == 200

class FileListParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.data = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == 'href' and value != '../':
                    self.data.append(value)
                    return



def listFiles(url):
    cleanUrl, username, password = parse_url(url)

    request = urllib2.Request(cleanUrl)
    base64string = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
    request.add_header("Authorization", "Basic %s" % base64string)
    result = urllib2.urlopen(request)
    content = result.read()

    parser = FileListParser()
    parser.feed(content)
    for sub in parser.data:
        append_subtitle({
            'filename': sub,
            'link': url + sub
        })


def checkSubsFolder(path):
    url = os.path.splitext(path)[0]+'/Subs/'
    try:
        if (check_source(url)):
            listFiles(url)
    except:
        pass


def get_file_in_dir(dir, fileType):
    for file in xbmcvfs.listdir(dir)[1]:
        if os.path.splitext(file)[1] == fileType:
            return file


def extract_file(dir, fileType):
    file = get_file_in_dir(dir, fileType)
    xbmc.executebuiltin(('XBMC.Extract("%s","%s")' % (os.path.join(dir, file), dir,)).encode('utf-8'), True)
    return os.path.join(dir, get_file_in_dir(dir, '.sub'))

def download(url, filename):
    uid = uuid.uuid4()
    tempdir = os.path.join(__temp__, unicode(uid))
    response = createRequestResult(url, False)

    xbmcvfs.mkdirs(tempdir)

    local_tmp_file = os.path.join(tempdir, filename)
    local_file_handle = xbmcvfs.File(local_tmp_file, "wb")
    local_file_handle.write(response.read())
    local_file_handle.close()

    if os.path.splitext(filename)[1] != '.rar':
        return os.path.join(tempdir, filename)

    xbmc.executebuiltin(('XBMC.Extract("%s","%s")' % (local_tmp_file, tempdir,)).encode('utf-8'), True)
    return extract_file(tempdir, '.rar')

params = get_params()

if params['action'] == 'search' or params['action'] == 'manualsearch':
    file_original_path = urllib.unquote(xbmc.Player().getPlayingFile().decode('utf-8'))  # Full path
    checkSubsFolder(file_original_path)

elif params['action'] == 'download':
    sub = download(params["link"], params["filename"])

    listitem = xbmcgui.ListItem(label=sub)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=sub, listitem=listitem, isFolder=False)

xbmcplugin.endOfDirectory(int(sys.argv[1]))  # send end of directory to XBMC
