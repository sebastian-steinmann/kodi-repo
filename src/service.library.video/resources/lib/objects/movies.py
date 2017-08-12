""" Handle movies """
from abc import ABCMeta, abstractmethod
import logging
from urlparse import urlparse

from resources.lib.util import settings
from resources.lib.objects.kodi_movies import KodiMovies

log = logging.getLogger("DINGS.db")  # pylint: disable=invalid-name


class Movies(object):
    """ Class to handle sync to kodi-db """
    __metaclass__ = ABCMeta

    def __init__(self, cursor):
        self.kodi_db = KodiMovies(cursor)

    @staticmethod
    def get_name():
        ''' Gets the name that describes tha class '''
        return 'AbstractMovieUpdater'

    def update(self, movie):
        ''' Update or add a movie '''

        original_movie = self._get_move_from_release_or_imdb(
            movie.get('id'),
            movie.get('imdb')
        )
        if original_movie is None:
            return self._add(movie)

        return self._update(movie, original_movie)

    def _update(self, movie, excisting_data):
        movieid, fileid, imdb_uid, pathid, last_update, uniqueid = excisting_data
        full_path = self._get_full_path(movie.get('folder'))

        if not self._should_update(last_update, movie):
            return False

        ratingid = self.kodi_db.get_ratingid(movieid)

        if uniqueid is None:
            uniqueid = self.kodi_db.add_uniqueid(
                movieid=movieid, **self._get_release_unique_id(movie))
        if imdb_uid is None:
            imdb_uid = self.kodi_db.add_uniqueid(
                movieid=movieid, **self._get_imdb_unique_id(movie))

        self.kodi_db.update_ratings(
            ratingid=ratingid, **self._get_ratings_data(movie))
        self.kodi_db.update_path(
            path_id=pathid, path=full_path, **self._get_path_data(movie))
        self.kodi_db.update_file(
            file_id=fileid, path_id=pathid, **self._get_file_data(movie))

        self.kodi_db.update_movie(movieid=movieid,
                                  uniqueid=uniqueid,
                                  path=full_path,
                                  pathid=pathid,
                                  fileid=fileid,
                                  **self._get_movie_data(movie))

        self._add_or_update_meta(movieid, movie)
        return True

    def _add(self, movie):
        movieid = self.kodi_db.create_entry()
        full_path = self._get_full_path(movie.get('folder'))

        # add ratings
        self.kodi_db.add_ratings(
            movieid=movieid, **self._get_ratings_data(movie))

        # add imdb unique id for ref
        self.kodi_db.add_uniqueid(
            movieid=movieid, **self._get_imdb_unique_id(movie))
        # add release id to support multiple releases of same movie
        uniqueid = self.kodi_db.add_uniqueid(
            movieid=movieid, **self._get_release_unique_id(movie))

        # add path
        pathid = self.kodi_db.add_path(
            path=full_path, **self._get_path_data(movie))
        fileid = self.kodi_db.add_file(pathid=pathid, **self._get_file_data(movie))

        # Add the movie
        self.kodi_db.add_movie(
            movieid=movieid,
            uniqueid=uniqueid,
            path=full_path,
            pathid=pathid,
            fileid=fileid,
            **self._get_movie_data(movie))

        self._add_or_update_meta(movieid, movie)
        return True

    def _get_full_path(self, folder):
        """ Add host, username and password to folderpath """
        url_parts = urlparse(settings("endpoint"))
        return "%s://%s:%s@%s%s/movies/%s/" % (
            url_parts.scheme,
            settings("username"),
            settings("password"),
            url_parts.netloc,
            url_parts.path,
            folder
        )

    def _get_move_from_release_or_imdb(self, release_id, imdb_id):
        result = self.kodi_db.get_movie_from_release(release_id)
        if result is None:
            return self.kodi_db.get_movie_from_imdb(imdb_id)

        return result

    def _add_people(self, movieid, movie):
        thumb = 'https://images-na.ssl-images-amazon.com/images/M/MV5BMTg5ODk1NTc5Ml5BMl5BanBnXkFtZTYwMjAwOTI4._V1_UY317_CR6,0,214,317_AL_.jpg'
        people = [{'Name': actor, 'Type': 'Actor', 'imageurl': thumb}
                  for actor in movie.get('actors')]
        people.extend([{'Name': writer, 'Type': 'Writer'}
                       for writer in movie.get('writers')])
        people.extend([{'Name': director, 'Type': 'Director'}
        for director in movie.get('directors')])

        self.kodi_db.add_people(movieid, people, 'movie')

    def _add_or_update_meta(self, movieid, movie):
        self.kodi_db.add_update_art(
            movie.get('poster'), movieid, 'movie', 'poster')
        self.kodi_db.add_update_art(
            movie.get('poster'), movieid, 'movie', 'thumb')
        self.kodi_db.add_genres(movieid, movie.get('genres'), "movie")

        self._add_people(movieid, movie)

    def _get_file_data(self, movie):
        return self._pick(movie, ['filename', 'dateadded'])

    def _get_path_data(self, movie):
        """
        Retrives arguments for path from movie as dict
        Arguments:
        movie: dict
        path, media_type, scraper, 1, last_update
        """
        return {
            'media_type': 'movies',
            'scraper': 'metadata.local',
            'last_update': movie.get('last_update')
        }

    def _get_imdb_unique_id(self, movie):
        """
        Retrives imdb unique data from movie for uniqueid insert as a dict
        Arguments
        movie: dict with movie info
        """
        return {
            'media_type': 'movie',
            'value': movie.get('imdb'),
            'type': 'imdb'
        }

    def _get_release_unique_id(self, movie):
        """
        Retrives release unique data from movie for uniqueid insert as a dict
        Arguments
        movie: dict with movie info
        """
        return {
            'media_type': 'movie',
            'value': movie.get('id'),
            'type': 'release'
        }

    def _get_ratings_data(self, movie):
        return self._pick(movie, ['rating', 'votecount'], {
            'media_type': 'movie',
            'rating_type': 'default',
        })

    def _get_movie_data(self, movie):
        return self._pick(movie, [
            'title',
            'plot',
            'votecount',
            'year',
            'imdb',
            'mpaa',
            'released',
            'writers',
            'genres',
            'directors',
            'country'
        ], {
            'shortplot': None,
            'tagline': None,
            'runtime': self._get_runtime_in_seconds(movie.get('runtime')),
            'studio': None,
            'trailer': None,
        })

    def _pick(self, data, fields, extras={}):
        new_dict = {key: value for key,
                    value in data.iteritems() if key in fields}
        new_dict.update(extras)

        return {key.encode('ascii', 'ignore'): self._map_array(value)
                for key, value in new_dict.iteritems()}

    def _map_array(self, value):
        if type(value) is list:
            return self._array_to_string(value)
        return value

    def _array_to_string(self, array, delimiter=' / '):
        return delimiter.join(array)

    def _get_runtime_in_seconds(self, runtime):
        if runtime:
            return int(runtime) * 60
        return None

    def delete(self, movie):
        self.kodi_db.remove_movie(movie['movie_id'], movie['idFile'])

    def get_movies_to_remove(self, release_ids):
        '''
            Compares release_ids to releases in kodidb
            Parameters:
            release_ids: array, external releases
            Returns:
            List of media ids in kodi thats not external
        '''
        all_refs = self.kodi_db.get_movie_refs()
        release_set = set(release_ids)
        return [{'media_id': media_id, 'title': title, 'idFile': idFile}
            for media_id, release_id, title, idFile in all_refs
            if int(release_id) not in release_set]

    @abstractmethod
    def _should_update(self, last_update, movie):
        pass

class IncrementalMovieUpdater(Movies):
    '''Does an check to only update changed movies '''

    @staticmethod
    def get_name():
        return 'Incremental Update'

    def _should_update(self, last_update, movie):
        return last_update != movie.get('last_update')

class FullMovieUpdater(Movies):
    ''' Updates all movies regardless of last update '''

    @staticmethod
    def get_name():
        return 'Full Update'

    def _should_update(self, last_update, movie):
            return True