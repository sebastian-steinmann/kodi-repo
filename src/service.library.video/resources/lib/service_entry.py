""" Actual implementation of service """
import logging
import time

import xbmc

import resources.lib.loghandler as loghandler
from resources.lib.service_api import Api
from resources.lib.objects.movies import Movies
import resources.lib.objects.database as database
from resources.lib.util import window, settings, sourcesXML

loghandler.config()
log = logging.getLogger("DINGS.service") # pylint: disable=invalid-name

class Service(object):
    """ Root service for sync """

    def __init__(self):
        self.monitor = xbmc.Monitor()
        self.api = Api(settings("host"), settings("username"), settings("password"))
        self.run()

    def run(self):
        """ Starts the service """
        log.debug("Starting service service.library.video...")
        while not self.monitor.abortRequested():
            self.update()
            # Sleep/wait for abort for 10 seconds
            if self.monitor.waitForAbort(30):
                # Abort was requested while waiting. We should exit
                break

        self.shutdown()

    def update(self):
        """ Check if any new movies """
        if not self.monitor.abortRequested():
            count = 0
            all_movies = self.api.get_all_movies()
            total = len(all_movies)
            log.info("Fant %s filmer, oppdaterer %s", total, time.time())
            sourcesXML()
            with database.DatabaseConn() as cursor_video:
                window("dings_kodiscan", "true")
                movies_db = Movies(cursor_video)
                for movie in self.added(all_movies):
                    movies_db.update(movie)
                    log.info("La til filmen %s id: %s", movie.get('title'), movie.get('imdb'))
                    count += 1
                window("dings_kodiscan", clear=True)
                xbmc.executebuiltin('UpdateLibrary(video)')

            log.info("%s av %s filmer lagt til", count, total)

    def added(self, items):
        """ Handler to check abort, and to show notifications """
        for item in items:
            if self.monitor.abortRequested():
                break
            yield item

    def shutdown(self):
        """ cleanup in case of abort """
        pass
