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

    def create_entry_path(self):
        self.cursor.execute("select coalesce(max(idPath),0) from path")
        kodi_id = self.cursor.fetchone()[0] + 1

        return kodi_id

    def create_entry_file(self):
        self.cursor.execute("select coalesce(max(idFile),0) from files")
        kodi_id = self.cursor.fetchone()[0] + 1

        return kodi_id

    def create_entry_uniqueid(self):
        self.cursor.execute("select coalesce(max(uniqueid_id),0) from uniqueid")
        kodi_id = self.cursor.fetchone()[0] + 1

        return kodi_id

    def create_entry_genre(self):
        self.cursor.execute("select coalesce(max(genre_id),0) from genre")
        kodi_id = self.cursor.fetchone()[0] + 1

        return kodi_id

    def add_path(self, path, media_type, scraper):
        """ Adds path object """
        path_id = self.get_path(path)
        if path_id is None:
            # Create a new entry
            path_id = self.create_entry_path()
            query = (
                '''
                INSERT INTO path(idPath, strPath, strContent, strScraper, noUpdate)

                VALUES (?, ?, ?, ?, ?)
                '''
            )
            self.cursor.execute(query, (path_id, path, media_type, scraper, 1))

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

        query = ' '.join((

            "SELECT idFile",
            "FROM files",
            "WHERE strFilename = ?",
            "AND idPath = ?"
        ))
        self.cursor.execute(query, (filename, path_id,))
        try:
            file_id = self.cursor.fetchone()[0]
        except TypeError:
            # Create a new entry
            file_id = self.create_entry_file()
            query = (
                '''
                INSERT INTO files(idFile, idPath, strFilename, dateAdded)

                VALUES (?, ?, ?, ?)
                '''
            )
            self.cursor.execute(query, (file_id, path_id, filename, dateAdded))

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


    def create_entry_rating(self):
        self.cursor.execute("select coalesce(max(rating_id),0) from rating")
        kodi_id = self.cursor.fetchone()[0] + 1

        return kodi_id

    def create_entry(self):
        self.cursor.execute("select coalesce(max(idMovie),0) from movie")
        kodi_id = self.cursor.fetchone()[0] + 1

        return kodi_id

    def create_entry_set(self):
        self.cursor.execute("select coalesce(max(idSet),0) from sets")
        kodi_id = self.cursor.fetchone()[0] + 1

        return kodi_id

    def create_entry_country(self):
        self.cursor.execute("select coalesce(max(country_id),0) from country")
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
        query = ' '.join((

            "DELETE FROM genre_link",
            "WHERE media_id = ?",
            "AND media_type = ?"
        ))
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

        genre_id = self.create_entry_genre()
        query = "INSERT INTO genre(genre_id, name) values(?, ?)"
        self.cursor.execute(query, (genre_id, genre))
        log.debug("Add Genres to media, processing: %s", genre)

        return genre_id

    def _get_genre(self, genre):

        query = ' '.join((

            "SELECT genre_id",
            "FROM genre",
            "WHERE name = ?",
            "COLLATE NOCASE"
        ))
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
    def create_entry_studio(self):
        self.cursor.execute("select coalesce(max(studio_id),0) from studio")
        kodi_id = self.cursor.fetchone()[0] + 1

        return kodi_id

    def _add_studio(self, studio):

        studio_id = self.create_entry_studio()
        query = "INSERT INTO studio(studio_id, name) values(?, ?)"
        self.cursor.execute(query, (studio_id, studio))
        log.debug("Add Studios to media, processing: %s", studio)

        return studio_id

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
        query = (
            '''
            INSERT INTO rating(
                rating_id, media_id, media_type, rating_type, rating, votes)

            VALUES (?, ?, ?, ?, ?, ?)
            '''
        )
        self.cursor.execute(query, (args))

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
        query = (
            '''
            INSERT INTO uniqueid(
                uniqueid_id, media_id, media_type, value, type)

            VALUES (?, ?, ?, ?, ?)
            '''
        )
        self.cursor.execute(query, (args))

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

        country_id = self.create_entry_country()
        query = "INSERT INTO country(country_id, name) values(?, ?)"
        self.cursor.execute(query, (country_id, country))
        log.debug("Add country to media, processing: %s", country)

        return country_id

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
