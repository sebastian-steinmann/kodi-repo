# -*- coding: utf-8 -*-

##################################################################################################

import logging
import xbmc

##################################################################################################

from resources.lib.artwork import Artwork

##################################################################################################

log = logging.getLogger("DINGS.db") # pylint: disable=invalid-name

##################################################################################################


class KodiMovies(object):

    def __init__(self, cursor):
        self.cursor = cursor
        self.kodi_version = int(xbmc.getInfoLabel('System.BuildVersion')[:2])
        self.artwork = Artwork()

    def add_path(self, full_path, last_update, version, **kvargs):
        """
        Adds path object and returns new id
        Arguments:
        path: string, path of folder
        last_update: date
        """
        path_id = self.get_path(full_path)
        if path_id is None:
            # Create a new entry
            query = (
                '''
                INSERT INTO path(strPath, strContent, strScraper, noUpdate, strHash, dateAdded)
                VALUES (?, ?, ?, ?, ?, ?)
                '''
            )
            self.cursor.execute(query, (full_path, 'movies', 'metadata.local', 1, version, last_update))
            path_id = self.cursor.lastrowid
        return path_id

    def get_path(self, path):
        query = '''
            SELECT idPath
            FROM path
            WHERE strPath = ?
        '''
        self.cursor.execute(query, (path,))
        try:
            return self.cursor.fetchone()[0]
        except TypeError:
            return None

    def update_path(self, pathid, full_path, last_update, version, **kvargs):
        """
        Updates path with new data
        Arguments:
        path_id: int, id of path to update
        path: string, path of folder
        """
        query = '''
            UPDATE path
            SET strPath = ?, strContent = ?, strScraper = ?, noUpdate = ?, strHash = ?
            WHERE idPath = ?
        '''
        self.cursor.execute(query, (full_path, 'movies', 'metadata.local', 1, version, pathid))

    def remove_path(self, path_id):
        self.cursor.execute("DELETE FROM path WHERE idPath = ?", (path_id,))

    def add_file(self, **kvargs):
        """
            Checks if file does not already excist and adds it, returns file_id
            Arguments:
            pathid: int
            filename: filename without folder, inkluding file ending
            dateadded: yyyy-mm-dd
        """
        query = '''
            SELECT idFile FROM files
            WHERE strFilename = :filename
            AND idPath = :pathid
        '''
        self.cursor.execute(query, kvargs)
        try:
            return self.cursor.fetchone()[0]
        except TypeError:
            # Create a new entry
            query = (
                '''
                INSERT INTO files(idPath, strFilename, dateAdded)
                VALUES (:pathid, :filename, :dateadded)
                '''
            )
            self.cursor.execute(query, kvargs)
            return self.cursor.lastrowid

    def update_file(self, **kvargs):
        """
            Updates the file with arguments
            Arguments:
            fileid: int
            pathid: int
            filename: filename without folder, inkluding file ending
        """
        query = '''
            UPDATE files
            SET idPath = :pathid, strFilename = :filename
            WHERE idFile = :fileid
        '''
        self.cursor.execute(query, kvargs)

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
        return self.cursor.fetchone()[0] + 1

    def get_movie(self, kodi_id):
        query = "SELECT * FROM movie WHERE idMovie = ?"
        self.cursor.execute(query, (kodi_id,))
        try:
            return self.cursor.fetchone()
        except TypeError:
            return None

    def get_movie_from_release(self, release_id):
        query = ('''
            SELECT movie.idMovie, movie.idFile, imdb_uid.uniqueid_id as imdb_uid, path.idPath, path.dateAdded, path.strHash, u.uniqueid_id from uniqueid u
            LEFT JOIN movie on (u.media_id = movie.idMovie)
			LEFT JOIN files on (files.idFile = movie.idFile)
			LEFT JOIN path on (path.idPath = files.idPath)
            LEFT JOIN uniqueid imdb_uid on (imdb_uid.media_type = 'movie' and imdb_uid.type = 'imdb' and imdb_uid.media_id = movie.idMovie)
            WHERE u.media_type = 'movie' and u.type = 'release'
            and u.value = ?
        ''')
        self.cursor.execute(query, (release_id,))
        try:
            return self.cursor.fetchone()
        except TypeError:
            return None

    def get_movie_from_imdb(self, imdb_id):

        query = ('''
            SELECT movie.idMovie, movie.idFile, u.uniqueid_id as imdb_uid, path.idPath, path.dateAdded, path.strHash, null as uniqueid_id from uniqueid u
            LEFT JOIN movie on (u.media_id = movie.idMovie)
			LEFT JOIN files on (files.idFile = movie.idFile)
			LEFT JOIN path on (path.idPath = files.idPath)
            LEFT JOIN uniqueid release_uid on (release_uid.media_type = 'movie' and release_uid.type = 'release' and release_uid.media_id = movie.idMovie)
            WHERE u.media_type = 'movie' and u.type in ('unknown', 'imdb')
            and u.value = ? and release_uid.uniqueid_id is null
        ''')
        self.cursor.execute(query, (imdb_id,))
        try:
            return self.cursor.fetchone()
        except TypeError:
            return None

    def add_movie(self, **kvargs):
        '''
            Create the movie entry
        '''

        query = (
            '''
            INSERT INTO movie(
                idMovie, idFile, c00, c01, c02, c03, c04, c05, c06, c07,
                c09, c10, c11, c12, c14, c15, c16, c18, c19, c21, premiered, c22, c23)

            VALUES (
                :movieid,
                :fileid,
                :title,
                :plot,
                :shortplot,
                :tagline,
                :votecount,
                :ratingid,
                :writers_list,
                :year,
                :imdb,
                :title,
                :runtime,
                :mpaa,
                :genres_list,
                :directors_list,
                :title,
                :studio,
                :trailer,
                :country_list,
                :released,
                :full_path,
                :pathid
                )
            '''
        )
        self.cursor.execute(query, kvargs)

    def update_movie(self, **kvargs):
        '''
            Update the movie entry
            movieid: kodi-id
            title,
            plot,
            None,
            None,
            votecount,
            uniqueid,
            writers,
            year,
            imdb,
            title,
            runtime in seconds,
            mpaa,
            genres,
            directors,
            title,
            None,
            None,
            country,
            released,
            full_path,
            pathid
        '''

        query = '''
            UPDATE movie
            SET c00 = :title,
            c01 = :plot,
            c02 = :shortplot,
            c03 = :tagline,
            c04 = :votecount,
            c05 = :ratingid,
            c06 = :writers_list,
            c07 = :year,
            c09 = :imdb,
            c10 = :title,
            c11 = :runtime,
            c12 = :mpaa,
            c14 = :genres_list,
            c15 = :directors_list,
            c16 = :title,
            c18 = :studio,
            c19 = :trailer,
            c21 = :country_list,
            premiered = :released,
            c22 = :full_path,
            c23 = :pathid
            WHERE idMovie = :movieid
        '''
        self.cursor.execute(query, kvargs)

    def add_genres(self, kodi_id, genres):

        # Delete current genres for clean slate
        query = '''
            DELETE FROM genre_link
            WHERE media_id = ?
            AND media_type = ?
        '''
        self.cursor.execute(query, (kodi_id, 'movie',))

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
            self.cursor.execute(query, (genre_id, kodi_id, 'movie'))

    def _add_genre(self, genre):
        query = "INSERT INTO genre(name) values(?)"
        self.cursor.execute(query, (genre,))
        log.debug("Add Genres to media, processing: %s", genre)

        return self.cursor.lastrowid

    def _get_genre(self, genre):

        query = '''
            SELECT genre_id
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

    def add_ratings(self, **kvargs):
        """
            Adds a new rating record and returns the id
            Arguments as kvargs:
            movieid: int
            rating: double
            votecount: int
        """
        query = (
            '''
            INSERT INTO rating(
                media_id, media_type, rating_type, rating, votes)

            VALUES (:movieid, 'movie', 'default', :rating, :votecount)
            '''
        )
        self.cursor.execute(query, kvargs)
        return self.cursor.lastrowid

    def update_ratings(self, rating, votecount, ratingid, **kvargs):
        """
            Adds a new rating record and returns the id
            Arguments as kvargs:
            ratingid: int
            rating: double
            votecount: int
        """
        query = '''
            UPDATE rating
            SET media_type = 'movie', rating_type = 'default', rating = ?, votes = ?
            WHERE rating_id = ?
        '''
        self.cursor.execute(query, (rating, votecount, ratingid,))

    def get_uniqueid(self, media_id):
        query = "SELECT uniqueid_id FROM uniqueid WHERE media_id = ?"
        self.cursor.execute(query, (media_id,))
        try:
            uniqueid = self.cursor.fetchone()[0]
        except TypeError:
            uniqueid = None

        return uniqueid

    def add_uniqueid(self, **kvargs):
        """
            Adds a refrence between a movie and external id and returns the new id
            Arguments
            movieid: int
            value: int, external id
            type: type of external id
        """
        query = (
            '''
            INSERT INTO uniqueid(
                media_id, media_type, value, type)

            VALUES (:movieid, 'movie', :value, :type)
            '''
        )
        self.cursor.execute(query, kvargs)
        return self.cursor.lastrowid

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
        query = '''
            SELECT country_id
            FROM country
            WHERE name = ?
            COLLATE NOCASE
        '''
        self.cursor.execute(query, (country,))
        try:
            return self.cursor.fetchone()[0]
        except TypeError:
            return self._add_country(country)

    def add_update_art(self, image_url, kodi_id, image_type, media_type):
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

            if cache_image and image_type in ("fanart", "poster"):
                self.artwork.cache_texture(image_url)

    def add_people(self, kodi_id, people, media_type):

        def add_thumbnail(person_id, person, type_):
            if 'imageurl' in person:
                thumbnail = person['imageurl']
                art = type_.lower()
                if "writing" in art:
                    art = "writer"

                self.add_update_art(thumbnail, person_id, art, "thumb")

        def add_link(link_type, person_id, kodi_id, media_type):
            query = (
                "INSERT OR REPLACE INTO " + link_type + "(actor_id, media_id, media_type)"
                "VALUES (?, ?, ?)"
            )
            self.cursor.execute(query, (person_id, kodi_id, media_type,))

        cast_order = 0

        for person in people:

            name = person['Name']
            type_ = person['Type']
            thumb_url = person.get('imageurl', "")

            person_id = self._get_person(name, thumb_url)

            # Link person to content
            if type_ == "Actor":
                role = ""
                query = (
                    '''
                    INSERT OR REPLACE INTO actor_link(
                        actor_id, media_id, media_type, role, cast_order)

                    VALUES (?, ?, ?, ?, ?)
                    '''
                )
                self.cursor.execute(query, (person_id, kodi_id, media_type, role, cast_order))
                cast_order += 1

            elif type_ == "Director":
                add_link("director_link", person_id, kodi_id, media_type)

            elif type_ in ("Writing", "Writer"):
                add_link("writer_link", person_id, kodi_id, media_type)

            elif type_ == "Artist":
                add_link("actor_link", person_id, kodi_id, media_type)

            add_thumbnail(person_id, person, type_)


    def _add_person(self, name, thumb_url):
        query = "INSERT INTO actor (name, art_urls) values(?, ?)"
        art_urls = "<thumb>%s</thumb>" % thumb_url
        self.cursor.execute(query, (name,art_urls,))
        log.debug("Add people to media, processing: %s", name)

        return self.cursor.lastrowid

    def _get_person(self, name, thumb_url):
        query = '''
            SELECT actor_id
            FROM actor
            WHERE name = ?
            COLLATE NOCASE
        '''
        self.cursor.execute(query, (name,))

        try:
            return self.cursor.fetchone()[0]
        except TypeError:
            return self._add_person(name, thumb_url)

    def get_movie_refs(self):
        ''' retrives a list of movierefs that has a release refrence to dings '''
        query = '''
            select media_id, value, movie.c00, movie.idFile from uniqueid uid
            left join movie on (movie.idMovie = uid.media_id)
            where uid.type='release' and uid.media_type='movie'
        '''
        self.cursor.execute(query)
        return self.cursor.fetchall()

