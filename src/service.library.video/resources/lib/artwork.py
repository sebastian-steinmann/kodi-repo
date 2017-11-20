# -*- coding: utf-8 -*-

#################################################################################################

import logging
import urllib

import requests

from resources.lib.util import JSONRPC

##################################################################################################

log = logging.getLogger("DINGS."+__name__)

##################################################################################################


class Artwork(object):
    xbmc_host = 'localhost'
    xbmc_port = None
    xbmc_username = None
    xbmc_password = None

    def __init__(self):
        if not self.xbmc_port:
            self._set_webserver_details()

    def _double_urlencode(self, text):
        text = self.single_urlencode(text)
        text = self.single_urlencode(text)

        return text

    @classmethod
    def single_urlencode(cls, text):
        # urlencode needs a utf- string
        text = urllib.urlencode({'blahblahblah': text.encode('utf-8')})
        text = text[13:]

        return text.decode('utf-8') #return the result again as unicode

    def _set_webserver_details(self):
        # Get the Kodi webserver details - used to set the texture cache
        get_setting_value = JSONRPC('Settings.GetSettingValue')

        web_query = {
            "setting": "services.webserver"
        }
        result = get_setting_value.execute(web_query)
        try:
            xbmc_webserver_enabled = result['result']['value']
        except (KeyError, TypeError):
            xbmc_webserver_enabled = False

        if not xbmc_webserver_enabled:
            # Enable the webserver, it is disabled
            set_setting_value = JSONRPC('Settings.SetSettingValue')

            web_port = {
                "setting": "services.webserverport",
                "value": 8080
            }
            set_setting_value.execute(web_port)
            self.xbmc_port = 8080

            web_user = {
                "setting": "services.webserver",
                "value": True
            }
            set_setting_value.execute(web_user)
            self.xbmc_username = "kodi"
        else:
            # Webserver already enabled
            web_port = {
                "setting": "services.webserverport"
            }
            result = get_setting_value.execute(web_port)
            try:
                self.xbmc_port = result['result']['value']
            except (TypeError, KeyError):
                pass

            web_user = {
                "setting": "services.webserverusername"
            }
            result = get_setting_value.execute(web_user)
            try:
                self.xbmc_username = result['result']['value']
            except (TypeError, KeyError):
                pass

        web_pass = {
            "setting": "services.webserverpassword"
        }
        result = get_setting_value.execute(web_pass)
        try:
            self.xbmc_password = result['result']['value']
        except (TypeError, KeyError):
            pass

    def cache_texture(self, url):
        # Cache a single image url to the texture cache
        if url:
            log.debug("Processing: %s", url)

            url = self._double_urlencode(url)
            try: # Add image to texture cache by simply calling it at the http endpoint
                requests.head(url=("http://%s:%s/image/image://%s"
                                    % (self.xbmc_host, self.xbmc_port, url)),
                                auth=(self.xbmc_username, self.xbmc_password),
                                timeout=(0.1, 0.1))
            except Exception: # We don't need the result
                pass