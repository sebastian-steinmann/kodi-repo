# -*- coding: utf-8 -*-

#################################################################################################

import logging
import sqlite3
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.util import window

#################################################################################################

log = logging.getLogger("DINGS."+__name__)
KODI = xbmc.getInfoLabel('System.BuildVersion')[:2]

#################################################################################################

def video_database():
    db_version = {

        '13': 78, # Gotham
        '14': 90, # Helix
        '15': 93, # Isengard
        '16': 99, # Jarvis
        '17': 107 # Krypton
    }
    return xbmc.translatePath("special://database/MyVideos%s.db"
                              % db_version.get(KODI, "")).decode('utf-8')

def kodi_commit():
    # verification for the Kodi video scan
    kodi_scan = window('dings_kodiScan') == "true"
    count = 0

    while kodi_scan:
        log.info("kodi scan is running, waiting...")

        if count == 10:
            log.info("flag still active, but will try to commit")
            window('emby_kodiScan', clear=True)

        elif xbmc.Monitor().abortRequested() or xbmc.Monitor().waitForAbort(1):
            log.info("commit unsuccessful. sync terminating")
            return False

        kodi_scan = window('emby_kodiScan') == "true"
        count += 1

    return True


class DatabaseConn(object):
    # To be called as context manager - i.e. with DatabaseConn() as conn: #dostuff

    def __init__(self, database_file="video", commit_on_close=True, timeout=120):
        """
        database_file can be custom: emby, texture, music, video, :memory: or path to the file
        commit_mode set to None to autocommit (isolation_level). See python documentation.
        """
        self.db_file = database_file
        self.commit_on_close = commit_on_close
        self.timeout = timeout

    def __enter__(self):
        # Open the connection
        self.path = self._SQL(self.db_file)

        self.conn = sqlite3.connect(self.path, isolation_level=None, timeout=self.timeout)

        log.info("opened: %s - %s", self.path, id(self.conn))
        self.cursor = self.conn.cursor()

        return self.cursor

    def _SQL(self, media_type):

        databases = {
            'video': video_database
        }
        return video_database()

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Close the connection
        changes = self.conn.total_changes

        if exc_type is not None:
            # Errors were raised in the with statement
            log.error("Type: %s Value: %s", exc_type, exc_val)

        if self.commit_on_close == True and changes:
            log.info("number of rows updated: %s", changes)
            if self.db_file == "video":
                kodi_commit()
            self.conn.commit()
            log.info("commit: %s", self.path)

        log.info("closing: %s - %s", self.path, id(self.conn))
        self.cursor.close()
        self.conn.close()
