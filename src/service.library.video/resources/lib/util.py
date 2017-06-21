""" Random util methods """
import json
import xbmcgui
import xbmcaddon

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
