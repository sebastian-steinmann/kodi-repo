""" http_client.py """

import urllib2
import base64
import json

class HttpClient(object):
    """ Client to do http-calls """
    def __init__(self, endpoint, user, password):
        self.endpoint = endpoint
        self.user = user
        self.password = password

    def get(self, path):
        """ Returns content from path """
        request = urllib2.Request("%s%s" % (self.endpoint, path))
        base64string = base64.encodestring('%s:%s' % (self.user, self.password)).replace('\n', '')
        request.add_header("Authorization", "Basic %s" % base64string)
        response = urllib2.urlopen(request)
        return json.load(response)
