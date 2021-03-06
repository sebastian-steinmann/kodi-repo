""" Actual implementation of service """
import logging

from datetime import datetime
import threading

import xbmc
import xbmcgui

from resources.lib.service_api import Api
from resources.lib.objects.movies import FullMovieUpdater, IncrementalMovieUpdater
import resources.lib.objects.database as database
from resources.lib.util import window, settings  # , sourcesXML
from resources.lib.date_utils import DateUtils

log = logging.getLogger("DINGS.library")  # pylint: disable=invalid-name

class Library(threading.Thread):
    """ Root service for sync """
    client_version = '5'
    _shared_state = {}
    stop_thread = False

    pdialog = None
    title = None
    count = 0
    total = 0

    date_utils = DateUtils()

    def __init__(self):
        super(Library, self).__init__(name='Library')
        self.__dict__ = self._shared_state
        self.monitor = xbmc.Monitor()
        self.player = xbmc.Player()

        self._abort_event = threading.Event()
        self._abort_event.clear()

        self.api = Api(
            settings("host"),
            settings("username"),
            settings("password")
        )

        threading.Thread.__init__(self)

    def run(self):
        try:
            self._run_internal()
        except Exception as e:
            log.exception(e)
        finally:
            window("dings_kodiscan", clear=True)
            if self.pdialog:
                self.pdialog.close()
            self.monitor = None
            self.pdialog = None
            self.player = None

    def _run_internal(self):
        """ Starts the service """
        log.debug("Starting service service.library.video...")
        if not self.player.isPlaying():
            self._start_sync()
        while not (self._should_stop()):
            if self._should_sync():
                self._start_sync()

            if self._should_stop():
                # Set in service.py
                log.debug("Service terminated thread.")
                break

            if self._should_stop() or self.monitor.waitForAbort(10):
                # Abort was requested while waiting. We should exit
                log.debug("waitForAbort")
                break

        log.warn("###===--- LibrarySync Stopped ---===###")

    def _start_sync(self):
        xbmc.executebuiltin('InhibitIdleShutdown(true)')
        try:
            start_time = datetime.now()

            total, count = self.update()
            if not self._should_stop():
                self.set_last_sync(start_time)

            elapsedtotal = datetime.now() - start_time
            log.info("%s av %s filmer lagt til. Det tok %s",
                    count, total, str(elapsedtotal).split('.')[0])
        except Exception as e:
            log.error(e)

        finally:
            window('dings_kodiScan', clear=True)
            if self.pdialog:
                self.pdialog.close()
            xbmc.executebuiltin('InhibitIdleShutdown(false)')

    def show_progress(self, title):
        dialog = None

        dialog = xbmcgui.DialogProgressBG()
        dialog.create("Dings for Kodi", title)
        dialog.update(1)

        return dialog

    def update(self):
        """
        Invokeds self._full_update if should_do_full_sync else _incremental_update()
        returns total, count
        """
        force = False
        if force or self._should_do_full_sync():
            return self._full_update()
        return self._incremental_update()

    def _delete_missing_movies(self, all_movies):
        all_release_ids = [m.get('id') for m in all_movies]
        window("dings_kodiscan", "true")
        self.pdialog = self.show_progress("Deleting movies")

        with database.DatabaseConn() as cursor_video:
            movies_db = FullMovieUpdater(cursor_video)
            movies_for_wipe = movies_db.get_movies_to_remove(all_release_ids)
            log.info("Found %s movies to remove", len(movies_for_wipe))

            for movie in self.added(movies_for_wipe):
                movies_db.delete(movie)
                log.info("Removed %s because it was not on remote", movie['title'])

            window("dings_kodiscan", clear=True)

        if self.pdialog:
            self.pdialog.close()
        log.info("Removing files done")

    def _full_update(self):
        start_time = datetime.now()
        all_movies = self.api.get_all_movies()
        total, count = self._do_update(all_movies, FullMovieUpdater)

        if not self._should_stop():
            self._delete_missing_movies(all_movies)
            self.save_last_full_sync(start_time)

        return total, count

    def _incremental_update(self):
        all_movies = self.api.get_movies_from(self.date_utils.get_str_date(self.get_last_sync()))

        return self._do_update(all_movies, IncrementalMovieUpdater)

    def _do_update(self, movies, db_factory):
        if self._should_stop():
            return 0, 0

        l_count = 0
        total = len(movies)

        window("dings_kodiscan", "true")
        self.pdialog = self.show_progress(db_factory.get_name())

        with database.DatabaseConn() as cursor_video:
            movies_db = db_factory(cursor_video)
            for movie in self.added(movies, total):
                if movies_db.update(movie):
                    log.debug("La til filmen %s id: %s, r: %s. %s/%s",
                              movie.get('title'), movie.get('imdb'), movie.get('id'), self.count, total)
                    l_count += 1

            window('dings_kodiScan', clear=True)

        if self.pdialog:
            self.pdialog.close()

        return total, l_count

    def save_last_full_sync(self, last_sync):
        """
        def save_last_full_sync(self, last_sync: datetime) -> None
        Saves last full sync to settings

        Arguments
        last_sync: date
        """
        settings('LastFullSync', self.date_utils.get_str_date(last_sync))
        self._update_client_version()

    def _get_last_full_sync(self):
        last_sync = settings('LastFullSync')
        if not last_sync:
            return datetime(1970, 1, 1)
        return self.date_utils.parse_str_date(last_sync)

    def set_last_sync(self, last_sync):
        settings('LastIncrementalSync', self.date_utils.get_str_date(last_sync))
        self._update_client_version()

    def get_sync_interval(self):
        interval = settings("interval")
        if not interval:
            return 10
        return int(interval)

    def get_last_sync(self):
        last_sync = settings('LastIncrementalSync')
        if not last_sync:
            return datetime(1970, 1, 1)
        return self.date_utils.parse_str_date(settings('LastIncrementalSync'))

    def _update_client_version(self):
        if self._is_outdated_client():
            settings('ClientVersion', self.client_version)

    def _get_client_version(self):
        client_version = settings('ClientVersion')
        if not client_version:
            return 1
        return client_version

    def _is_outdated_client(self):
        return self._get_client_version() != self.client_version

    def _should_do_full_sync(self):
        if self._is_outdated_client():
            return True
        last_full_sync = self._get_last_full_sync()
        interval_seconds = 24 * 60 * 60

        diff = datetime.now() - last_full_sync
        return diff.total_seconds() > interval_seconds

    def _should_sync(self):
        if self.player.isPlaying():
            return False
        last_sync = self.get_last_sync()
        sync_interval = self.get_sync_interval()
        interval_seconds = 60 * sync_interval # sync every 10 minutes

        diff = datetime.now() - last_sync
        return diff.total_seconds() > interval_seconds

    def added(self, items, total=None):
        """
        Generator to to check abort, and to show notifications yealds item of not abort
        Arguments:
        items: array
        """
        self.total = total or len(items)
        self.count = 0

        for item in items:
            if self._should_stop():
                log.debug('should_stop from added')
                break

            self.title = item.get('title', "unknown")

            yield item

            self.update_pdialog()
            self.count += 1


    def update_pdialog(self):
        if self.pdialog:
            percentage = int((float(self.count) / float(self.total))*100)
            self.pdialog.update(percentage, message=self.title)

    def _should_stop(self):
        return self._abort_event.is_set() or self.stop_thread or self.monitor.abortRequested()

    def stopThread(self):
        self.stop_thread = True
        self._abort_event.set()
        log.debug("Ending thread...")