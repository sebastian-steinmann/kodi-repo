# -*- coding: utf-8 -*-

##################################################################################################

import logging
import xbmc

from resources.lib.util import window
##################################################################################################

log = logging.getLogger("DINGS.db") # pylint: disable=invalid-name

##################################################################################################


class KodiMovies(object):

    def __init__(self, cursor):
        self.cursor = cursor
        self.kodi_version = int(xbmc.getInfoLabel('System.BuildVersion')[:2])

    def add_path(self, path, media_type, scraper):
        """ Adds path object """
        path_id = self.get_path(path)
        if path_id is None:
            # Create a new entry
            query = (
                '''
                INSERT INTO path(strPath, strContent, strScraper, noUpdate)
                VALUES (?, ?, ?, ?)
                '''
            )
            self.cursor.execute(query, (path, media_type, scraper, 1))
            path_id = self.cursor.lastrowid
        return path_id

    def get_path(self, path):

        query = ' '.join((

            "SELECT idPath",
            "FROM path",
            "WHERE strPath = ?"
        ))
        self.cursor.execute(query, (path,))
        try:
            path_id = self.cursor.fetchone()[0]
        except TypeError:
            path_id = None

        return path_id

    def get_path_by_media_id(self, file_id):
        ''' Returns path_id based on movie_id '''
        query = '''
            select idPath
            from files
            where idFile = ?
        '''
        self.cursor.execute(query, (file_id,))
        try:
            return self.cursor.fetchone()[0]
        except TypeError:
            return None

    def update_path(self, path_id, path, media_type, scraper):

        query = '''
            UPDATE path
            SET strPath = ?, strContent = ?, strScraper = ?, noUpdate = ?
            WHERE idPath = ?
        '''
        self.cursor.execute(query, (path, media_type, scraper, 1, path_id))

    def remove_path(self, path_id):
        self.cursor.execute("DELETE FROM path WHERE idPath = ?", (path_id,))

    def add_file(self, filename, path_id, dateAdded):

        query = '''
            SELECT idFile FROM files
            WHERE strFilename = ?
            AND idPath = ?
        '''
        self.cursor.execute(query, (filename, path_id,))
        try:
            file_id = self.cursor.fetchone()[0]
        except TypeError:
            # Create a new entry
            query = (
                '''
                INSERT INTO files(idPath, strFilename, dateAdded)

                VALUES (?, ?, ?)
                '''
            )
            self.cursor.execute(query, (path_id, filename, dateAdded))
            file_id = self.cursor.lastrowid

        return file_id

    def update_file(self, file_id, filename, path_id, date_added):

        query = ' '.join((

            "UPDATE files",
            "SET idPath = ?, strFilename = ?, dateAdded = ?",
            "WHERE idFile = ?"
        ))
        self.cursor.execute(query, (path_id, filename, date_added, file_id))

    def remove_file(self, path, filename):

        path_id = self.get_path(path)
        if path_id is not None:

            query = ' '.join((

                "DELETE FROM files",
                "WHERE idPath = ?",
                "AND strFilename = ?"
            ))
            self.cursor.execute(query, (path_id, filename,))

    def get_filename(self, file_id):

        query = ' '.join((

            "SELECT strFilename",
            "FROM files",
            "WHERE idFile = ?"
        ))
        self.cursor.execute(query, (file_id,))
        try:
            filename = self.cursor.fetchone()[0]
        except TypeError:
            filename = ""

        return filename

    def create_entry(self):
        self.cursor.execute("select coalesce(max(idMovie),0) from movie")
        kodi_id = self.cursor.fetchone()[0] + 1

        return kodi_id

    def get_movie(self, kodi_id):

        query = "SELECT * FROM movie WHERE idMovie = ?"
        self.cursor.execute(query, (kodi_id,))
        try:
            kodi_id = self.cursor.fetchone()[0]
        except TypeError:
            kodi_id = None

        return kodi_id
    
    def get_movie_from_imdb(self, imdb_id):

        query = ('''
            SELECT movie.idMovie, movie.idFile, u.uniqueid_id from uniqueid u
            LEFT JOIN movie on (u.media_id = movie.idMovie)
            WHERE u.media_type = 'movie' and u.type in ('unknown', 'imdb')
            and u.value = ?
        ''')
        self.cursor.execute(query, (imdb_id,))
        try:
            return self.cursor.fetchone()
        except TypeError:
            return None

    def add_movie(self, *args):
        # Create the movie entry
        query = (
            '''
            INSERT INTO movie(
                idMovie, idFile, c00, c01, c02, c03, c04, c05, c06, c07,
                c09, c10, c11, c12, c14, c15, c16, c18, c19, c21, premiered)

            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
        )
        self.cursor.execute(query, (args))

    def update_movie(self, *args):
        query = ' '.join((

            "UPDATE movie",
            "SET c00 = ?, c01 = ?, c02 = ?, c03 = ?, c04 = ?, c05 = ?, c06 = ?,",
            "c07 = ?, c09 = ?, c10 = ?, c11 = ?, c12 = ?, c14 = ?, c15 = ?,",
            "c16 = ?, c18 = ?, c19 = ?, c21 = ?, premiered = ?",
            "WHERE idMovie = ?"
        ))
        self.cursor.execute(query, (args))

    def add_genres(self, kodi_id, genres, media_type):
    
        # Delete current genres for clean slate
        query = '''
            DELETE FROM genre_link
            WHERE media_id = ?
            AND media_type = ?
        '''
        self.cursor.execute(query, (kodi_id, media_type,))

        # Add genres
        for genre in genres:
            genre_id = self._get_genre(genre)
            query = (
                '''
                INSERT OR REPLACE INTO genre_link(
                    genre_id, media_id, media_type)
                VALUES (?, ?, ?)
                '''
            )
            self.cursor.execute(query, (genre_id, kodi_id, media_type))

    def _add_genre(self, genre):
        query = "INSERT INTO genre(name) values(?)"
        self.cursor.execute(query, (genre))
        log.debug("Add Genres to media, processing: %s", genre)

        return self.cursor.lastrowid

    def _get_genre(self, genre):

        query = '''SELECT genre_id
            FROM genre
            WHERE name = ?
            COLLATE NOCASE
        '''
        self.cursor.execute(query, (genre,))

        try:
            genre_id = self.cursor.fetchone()[0]
        except TypeError:
            genre_id = self._add_genre(genre)

        return genre_id

    def add_studios(self, kodi_id, studios, media_type):
        for studio in studios:

            studio_id = self._get_studio(studio)
            query = (
                '''
                INSERT OR REPLACE INTO studio_link(studio_id, media_id, media_type)
                VALUES (?, ?, ?)
                ''')
            self.cursor.execute(query, (studio_id, kodi_id, media_type))

    def _add_studio(self, studio):
        query = "INSERT INTO studio(name) values(?)"
        self.cursor.execute(query, (studio))
        log.debug("Add Studios to media, processing: %s", studio)

        return self.cursor.lastrowid

    def _get_studio(self, studio):

        query = ' '.join((

            "SELECT studio_id",
            "FROM studio",
            "WHERE name = ?",
            "COLLATE NOCASE"
        ))
        self.cursor.execute(query, (studio,))
        try:
            studio_id = self.cursor.fetchone()[0]
        except TypeError:
            studio_id = self._add_studio(studio)

        return studio_id

    def remove_movie(self, kodi_id, file_id):
        self.cursor.execute("DELETE FROM movie WHERE idMovie = ?", (kodi_id,))
        self.cursor.execute("DELETE FROM files WHERE idFile = ?", (file_id,))

    def get_ratingid(self, media_id):

        query = "SELECT rating_id FROM rating WHERE media_id = ?"
        self.cursor.execute(query, (media_id,))
        try:
            ratingid = self.cursor.fetchone()[0]
        except TypeError:
            ratingid = None

        return ratingid

    def add_ratings(self, *args):
        '''
            takes (media_id, media_type, rating_type, rating, votes)
            returns new rating_id
        '''
        query = (
            '''
            INSERT INTO rating(
                media_id, media_type, rating_type, rating, votes)

            VALUES (?, ?, ?, ?, ?)
            '''
        )
        self.cursor.execute(query, (args))
        return self.cursor.lastrowid

    def update_ratings(self, *args):
        query = ' '.join((

            "UPDATE rating",
            "SET media_id = ?, media_type = ?, rating_type = ?, rating = ?, votes = ?",
            "WHERE rating_id = ?"
        ))
        self.cursor.execute(query, (args))

    def get_uniqueid(self, media_id):
        query = "SELECT uniqueid_id FROM uniqueid WHERE media_id = ?"
        self.cursor.execute(query, (media_id,))
        try:
            uniqueid = self.cursor.fetchone()[0]
        except TypeError:
            uniqueid = None

        return uniqueid

    def add_uniqueid(self, *args):
        '''
         takes (media_id, media_type, value, type)
         returns uniqueid_id

        '''
        query = (
            '''
            INSERT INTO uniqueid(
                media_id, media_type, value, type)

            VALUES (?, ?, ?, ?)
            '''
        )
        self.cursor.execute(query, (args))
        return self.cursor.lastrowid

    def update_uniqueid(self, *args):
        query = ' '.join((

            "UPDATE uniqueid",
            "SET media_id = ?, media_type = ?, value = ?, type = ?",
            "WHERE uniqueid_id = ?"
        ))
        self.cursor.execute(query, (args))

    def add_countries(self, kodi_id, countries):

        for country in countries:
            country_id = self._get_country(country)

            query = (
                '''
                INSERT OR REPLACE INTO country_link(country_id, media_id, media_type)
                VALUES (?, ?, ?)
                '''
            )
            self.cursor.execute(query, (country_id, kodi_id, "movie"))

    def _add_country(self, country):

        query = "INSERT INTO country(name) values(?)"
        self.cursor.execute(query, (country))
        log.debug("Add country to media, processing: %s", country)

        return self.cursor.lastrowid

    def _get_country(self, country):
        query = ' '.join((

            "SELECT country_id",
            "FROM country",
            "WHERE name = ?",
            "COLLATE NOCASE"
        ))
        self.cursor.execute(query, (country,))
        try:
            country_id = self.cursor.fetchone()[0]
        except TypeError:
            country_id = self._add_country(country)

        return country_id

    def add_update_art(self, image_url, kodi_id, media_type, image_type):
        # Possible that the imageurl is an empty string
        if image_url:

            cache_image = False

            query = '''
                SELECT url FROM art
                WHERE media_id = ?
                AND media_type = ?
                AND type = ?
            '''
            self.cursor.execute(query, (kodi_id, media_type, image_type,))
            try: # Update the artwork
                url = self.cursor.fetchone()[0]

            except TypeError: # Add the artwork
                cache_image = True
                log.debug("Adding Art Link for kodiId: %s (%s)", kodi_id, image_url)

                query = (
                    '''
                    INSERT INTO art(media_id, media_type, type, url)

                    VALUES (?, ?, ?, ?)
                    '''
                )
                self.cursor.execute(query, (kodi_id, media_type, image_type, image_url))

            else: # Only cache artwork if it changed
                if url != image_url:
                    cache_image = True

                    log.info("Updating Art url for %s kodiId: %s (%s) -> (%s)",
                             image_type, kodi_id, url, image_url)

                    query = '''
                        UPDATE art
                        SET url = ?
                        WHERE media_id = ?
                        AND media_type = ?
                        AND type = ?
                    '''
                    self.cursor.execute(query, (image_url, kodi_id, media_type, image_type))
