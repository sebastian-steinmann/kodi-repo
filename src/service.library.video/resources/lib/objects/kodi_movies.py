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
            SET strPath = ?, strContent = ?, strScraper = ?, noUpdate = ?, dateAdded = ?, strHash = ?
            WHERE idPath = ?
        '''
        self.cursor.execute(query, (full_path, 'movies', 'metadata.local', 1, last_update, version, pathid))

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
                VALUES (:pathid, :filename, :last_update)
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
            SET idPath = :pathid, strFilename = :filename, dateAdded = :last_update
            WHERE idFile = :fileid
        '''
        self.cursor.execute(query, kvargs)

    def get_filename(self, file_id):
        query = '''
            SELECT strFilename
            FROM files
            WHERE idFile = ?
        '''
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
            LEFT JOIN uniqueid imdb_uid on (
                imdb_uid.media_type = 'movie' AND
                imdb_uid.type = 'imdb' AND
                imdb_uid.media_id = movie.idMovie
            )
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
            LEFT JOIN uniqueid release_uid on (
                release_uid.media_type = 'movie' AND
                release_uid.type = 'release' AND
                release_uid.media_id = movie.idMovie
            )
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

    def set_streamdetails(self, fileid, language, **kvargs):
        """
            Updates streamdetails with language and common meta
        """
        query = '''
            INSERT OR REPLACE INTO streamdetails
            (idFile, iStreamType, strAudioLanguage, strVideoLanguage, strVideoCodec, iVideoWidth, iVideoHeight)
            values (?, 0, ?, ?, 'h264', '1920', '1040')
        '''

        self.cursor.execute(query, (fileid, language, language))

    def _add_genre_link(self, kodi_id, genre_id):
        query = (
            '''
            INSERT OR REPLACE INTO genre_link(
                genre_id, media_id, media_type)
            VALUES (?, ?, ?)
            '''
        )
        self.cursor.execute(query, (genre_id, kodi_id, 'movie'))


    def add_genres(self, kodi_id, genres):


        self.cursor.execute('''
            SELECT genre.genre_id, genre.name, genre_link.genre_id FROM genre
            LEFT JOIN genre_link on (
                genre_link.genre_id = genre.genre_id and
                genre_link.media_id = ? and
                genre_link.media_type = 'movie'
            )
            WHERE (genre.name in (?) OR genre_link.genre_id is not NULL);
        ''', (kodi_id, ','.join(genres)))

        current_genres = self.cursor.fetchall()

        removed_genres = [genre_id for genre_id, name, link in current_genres if name not in genres]
        # Delete removed genres
        query = '''
            DELETE FROM genre_link
            WHERE media_id = ?
            AND media_type = ?
            AND genre_id in (?)
        '''
        self.cursor.execute(query, (kodi_id, 'movie', ','.join(map(str, removed_genres))))

        existing_genres = [genre_id for genre_id, name, link in current_genres if not link]
        for genre_id in existing_genres:
            self._add_genre_link(kodi_id, genre_id)

        current_tag_names = set([name for _, name, _ in current_genres])
        new_genres = [name for name in genres if name not in current_tag_names]

        # Add genres
        for genre in new_genres:
            genre_id = self._add_genre(genre)
            self._add_genre_link(kodi_id, genre_id)

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

    def get_tags(self, movieid, remote_tags):
        ''' Gets tags for media_id with external ref '''
        query = '''
            select tag.tag_id, tag.name, uniqueid_id, tl.tag_id as existing from tag
            left join tag_link tl on (
                tl.media_id = ? and
                tl.media_type = 'movie' and
                tl.tag_id = tag.tag_id
            )
            left join uniqueid uid on (
                uid.media_id = ? AND
                uid.media_type = 'movie' AND
                uid.type = 'external_tag' AND
                uid.value = tag.tag_id
            )
            where (tag.name in (?) or tl.tag_id is not NULL);
        '''

        self.cursor.execute(query, (movieid, movieid, ','.join(remote_tags)))
        return self.cursor.fetchall()

    def remove_tag_links(self, moveid, tags):
        if not tags:
            return

        query = '''
            DELETE FROM tag_link
            WHERE tag_id in (?)
            AND media_id = ?
            AND media_type = 'movie'
        '''
        self.cursor.execute(query, (','.join(map(str, tags)), moveid))

        query = '''
            DELETE FROM uniqueid
            WHERE value in (?)
            AND media_id = ?
            AND media_type = 'movie'
            AND type = 'external_tag'
        '''
        self.cursor.execute(query, (','.join(map(str, tags)), moveid))

    def _get_or_add_tag(self, tag):
        query = '''
            select tag_id from tag
            where name = ?
            COLLATE NOCASE
        '''
        self.cursor.execute(query, (str(tag),))
        try:
            return self.cursor.fetchone()[0]
        except TypeError: # Add the artwork
            query = '''
                insert into tag (name) values (?)
            '''
            self.cursor.execute(query, (tag,))
            return self.cursor.lastrowid

    def add_tag_links(self, movieid, tag_ids):
        for tag_id in tag_ids:
            self._add_tag_link(movieid, tag_id)

    def _add_tag_link(self, movieid, tag_id):
        query = '''
            INSERT INTO tag_link
            (tag_id, media_id, media_type)
            VALUES (?, ?, 'movie')
        '''
        try:
            self.cursor.execute(query, (tag_id, movieid))
        except:
            log.error("failed to insert tagid: %s, movieid %s", tag_id, movieid)

        query = '''
            INSERT INTO uniqueid
            (media_id, media_type, type, value)
            VALUES (?, 'movie', 'external_tag', ?)
        '''
        self.cursor.execute(query, (movieid, tag_id))

    def add_tags(self, movieid, tags):
        for tag in tags:
            tag_id = self._get_or_add_tag(tag)
            self._add_tag_link(movieid, tag_id)