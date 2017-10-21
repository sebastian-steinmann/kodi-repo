""" http_client.py """

import urllib2
import base64
import json

import hashlib

from util import version

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
        request = urllib2.Request("%s%s" % (self.endpoint, path))
        base64string = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        request.add_header("Accepts", self._get_accepts_headers())
        response = urllib2.urlopen(request)
        content_version = response.info().getheader('Version')
        items = json.load(response)

        compiled_version = hashlib.md5(("%s-%s" % (content_version, version())).encode()).hexdigest()
        return self._with_version(items, compiled_version)

    def _with_version(self, items, compiled_version):
            return [dict(item, **{'version': compiled_version}) for item in items]
