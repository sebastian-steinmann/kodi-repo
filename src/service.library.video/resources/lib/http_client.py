""" http_client.py """

import urllib
import base64
import json

import hashlib
import logging

from resources.lib.util import version

log = logging.getLogger("DINGS.HttpClient")

class HttpClient(object):
    """ Client to do http-calls """
    def __init__(self, endpoint, user, password):
        self.endpoint = endpoint
        self.user = user
        self.password = password
        self.versions = [1]

    def _get_accepts_header(self, api_version):
        return "application/vnd+dings.movies.v%s+json" % api_version

    def _get_accepts_headers(self):
        return ",".join(self._get_accepts_header(version) for version in self.versions)

    def get(self, path):
        """ Returns content from path """
        try:
            fullPath = "%s%s" % (self.endpoint, path)
            request = urllib.request.Request(fullPath)
            
            base64bytes = base64.encodestring(bytes('%s:%s' % (self.user, self.password), 'utf-8'))
            base64string = base64bytes.decode('utf-8').replace('\n', '')
            request.add_header("Authorization", ("Basic %s" % base64string))
            request.add_header("Accepts", self._get_accepts_headers())
            # import web_pdb; web_pdb.set_trace()
            response = urllib.request.urlopen(request)
            content_version = response.headers.get('Version')
            items = json.load(response)
            
            compiled_version = hashlib.md5(("%s-%s" % (content_version, version())).encode()).hexdigest()
            
            return self._with_version(items, compiled_version)
        except Exception as e:
            log.exception("error trying to connect to %s with error %s", fullPath, e)

    def _with_version(self, items, compiled_version):
            return [dict(item, **{'version': compiled_version}) for item in items]
