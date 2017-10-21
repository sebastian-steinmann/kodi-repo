# -*- coding: utf-8 -*-

#################################################################################################

import logging
import sys
import urlparse

from resources.lib.util import settings

#################################################################################################
_ADDON_ID = 'service.library.video'

#################################################################################################

#log = logging.getLogger("DINGS.plugin")  # pylint: disable=invalid-name

#################################################################################################


class Main(object):
    def __init__(self):

        # Parse parameters
        path = sys.argv[2]
        params = urlparse.parse_qs(path[1:])
        #log.warn("Parameter string: %s", path)
        try:
            mode = params['mode'][0]
        except (IndexError, KeyError):
            mode = ""

        if mode == 'reset':
            settings('LastIncrementalSync', None)
            settings('LastFullSync', None)

if __name__ == '__main__':
    pass
    #log.info("%s started", _ADDON_ID)
    #try:
        #Main()
   # except Exception as error:
        #log.exception(error)
     #   raise

    #log.info("%s stopped", _ADDON_ID)
