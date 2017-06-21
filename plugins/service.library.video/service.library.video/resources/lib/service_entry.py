import logging
import xbmc


class Service(object):
    """ Root service for sync """
    monitor = xbmc.Monitor()
    log = logging.getLogger("DINGS."+__name__)

    def __init__(self):
        pass

    def update(self):
        """ Check if any new movies """
        if not self.monitor.abortRequested():
            self.log.debug("Sjekk for endringer")

    def shutdown(self):
        """ cleanup in case of abort """
        pass
