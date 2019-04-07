""" Actual implementation of service """

import logging
import xbmc

import resources.lib.loghandler as loghandler
from librarysync import Library

loghandler.config()
log = logging.getLogger("DINGS.service")  # pylint: disable=invalid-name

class Service(object):
    """ Root service for sync """

    library_running = False
    library_thread = None

    def __init__(self):
        self.monitor = xbmc.Monitor()

    def run(self):
        """ Starts the service """
        self.library_thread = Library()

        log.debug("Starting service service.library.video...")
        while not self.monitor.abortRequested():
            if not self.library_running:
                self.library_running = True
                self.library_thread.start()

            # Sleep/wait for abort for 5 seconds
            if self.monitor.waitForAbort(10):
                log.info("Aborting!")
                # Abort was requested while waiting. We should exit
                break

        self.shutdown()

    def shutdown(self):
        """ cleanup in case of abort """
        xbmc.executebuiltin('InhibitIdleShutdown(false)')

        if self.library_running:
            self.library_thread.stopThread()
