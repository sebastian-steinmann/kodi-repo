""" Random util methods """
import json
import xbmcgui
import xbmcaddon
import xbmc

import xml.etree.ElementTree as etree

ADDON_ID = "service.library.video"

def window(property_, value=None, clear=False, window_id=10000):
    """ Get or set window property """
    WINDOW = xbmcgui.Window(window_id)

    if clear:
        WINDOW.clearProperty(property_)
    elif value is not None:
        if ".json" in property_:
            value = json.dumps(value)
        WINDOW.setProperty(property_, value)
    else:
        result = WINDOW.getProperty(property_)
        if result and ".json" in property_:
            result = json.loads(result)
        return result

def settings(setting, value=None):
    """ Get or add addon setting """
    addon = xbmcaddon.Addon(id=ADDON_ID)

    if value is not None:
        addon.setSetting(setting, value)
    else: # returns unicode object
        return addon.getSetting(setting)

def sourcesXML():
    # To make Master lock compatible
    path = xbmc.translatePath("special://profile/").decode('utf-8')
    xmlpath = "%ssources.xml" % path

    try:
        xmlparse = etree.parse(xmlpath)
    except: # Document is blank or missing
        root = etree.Element('sources')
    else:
        root = xmlparse.getroot()


    video = root.find('video')
    if video is None:
        video = etree.SubElement(root, 'video')
        etree.SubElement(video, 'default', attrib={'pathversion': "1"})

    # Add elements
    count = 2
    for source in root.findall('.//path'):
        if source.text == "smb://":
            count -= 1

        if count == 0:
            # sources already set
            break
    else:
        # Missing smb:// occurences, re-add.
        for i in range(0, count):
            source = etree.SubElement(video, 'source')
            etree.SubElement(source, 'name').text = "Dings"
            etree.SubElement(source, 'path', attrib={'pathversion': "1"}).text = "smb://"
            etree.SubElement(source, 'allowsharing').text = "true"
    # Prettify and write to file
    try:
        indent(root)
    except: pass
    etree.ElementTree(root).write(xmlpath)

    def indent(elem, level=0):
        # Prettify xml trees
        i = "\n" + level*"  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = i + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = i
            for elem in elem:
                indent(elem, level+1)
                if not elem.tail or not elem.tail.strip():
                    elem.tail = i
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = i

class JSONRPC(object):

    id_ = 1
    jsonrpc = "2.0"

    def __init__(self, method, **kwargs):

        self.method = method

        for arg in kwargs: # id_(int), jsonrpc(str)
            self.arg = arg

    def _query(self):

        query = {

            'jsonrpc': self.jsonrpc,
            'id': self.id_,
            'method': self.method,
        }
        if self.params is not None:
            query['params'] = self.params

        return json.dumps(query)

    def execute(self, params=None):

        self.params = params
        return json.loads(xbmc.executeJSONRPC(self._query()))