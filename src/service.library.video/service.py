""" Rootfile forservice """
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *

from resources.lib.service_entry import Service
import xbmc

def run():
    service = Service()

    try:
        service.run()
    except Exception as e:
        xbmc.log(e, xbmc.LOGERROR)
        service.shutdown()

if __name__ == '__main__':
    run()
