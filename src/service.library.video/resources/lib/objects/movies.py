""" Handle movies """
from abc import ABCMeta, abstractmethod
import logging
from urlparse import urlparse

from resources.lib.util import settings
from resources.lib.objects.kodi_movies import KodiMovies
from resources.lib.date_utils import DateUtils

log = logging.getLogger("DINGS.db")  # pylint: disable=invalid-name


class Movies(object):
    """ Class to handle sync to kodi-db """
    __metaclass__ = ABCMeta

    def __init__(self, cursor):
        self.kodi_db = KodiMovies(cursor)
        self.date_utils = DateUtils()

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

    def _map_existing_data(self, movie_entity, excisting_data):
        movieid, fileid, imdb_uid, pathid, last_update, content_version, uniqueid = excisting_data
        movie_entity.update({
            'movieid': movieid,
            'fileid': fileid,
            'imdb_uid': imdb_uid,
            'pathid': pathid,
            'uniqueid': uniqueid
        })
        return movie_entity, {
            'version': content_version,
            'last_update': last_update
        }


    def _update(self, movie, excisting_data):
        movie_entity = self._map_move_data(movie.copy())
        movie_entity, org_movie = self._map_existing_data(movie_entity, excisting_data)

        if not self._should_update(org_movie, movie_entity):
            return False

        movie_entity['full_path'] = self._get_full_path(movie.get('folder'))

        movie_entity['ratingid'] = self.kodi_db.get_ratingid(movie_entity.get('movieid'))

        if movie_entity.get('uniqueid') is None:
            movie_entity['uniqueid'] = self.kodi_db.add_uniqueid(**self._get_release_unique_id(movie_entity))
        if movie_entity.get('imdb_uid') is None:
            movie_entity['imdb_uid'] = self.kodi_db.add_uniqueid(**self._get_imdb_unique_id(movie_entity))

        self.kodi_db.update_ratings(**movie_entity)
        self.kodi_db.update_path(**movie_entity)
        self.kodi_db.update_file(**movie_entity)

        self.kodi_db.update_movie(**movie_entity)

        self._add_or_update_meta(movie_entity)
        return True

    def _add(self, movie):
        movie_entity = self._map_move_data(movie.copy())

        movie_entity['movieid'] = self.kodi_db.create_entry()
        movie_entity['full_path'] = self._get_full_path(movie_entity.get('folder'))
        # add ratings
        movie_entity['ratingid'] = self.kodi_db.add_ratings(**movie_entity)

        # add imdb unique id for ref
        self.kodi_db.add_uniqueid(**self._get_imdb_unique_id(movie_entity))
        # add release id to support multiple releases of same movie
        movie_entity['uniqueid'] = self.kodi_db.add_uniqueid(**self._get_release_unique_id(movie_entity))

        # add path
        movie_entity['pathid'] = self.kodi_db.add_path(**movie_entity)
        movie_entity['fileid'] = self.kodi_db.add_file(**movie_entity)

        # Add the movie
        self.kodi_db.add_movie(**movie_entity)

        self._add_or_update_meta(movie_entity)
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
        thumb = None
        people = [{'Name': actor, 'Type': 'Actor'}
                  for actor in movie.get('actors')]
        people.extend([{'Name': writer, 'Type': 'Writer'}
                       for writer in movie.get('writers')])
        people.extend([{'Name': director, 'Type': 'Director'}
        for director in movie.get('directors')])

        self.kodi_db.add_people(movieid, people, 'movie')

    def _add_or_update_meta(self, movie):
        movieid = movie.get('movieid')
        self.kodi_db.add_update_art(
            movie.get('poster'), movieid, 'poster', 'movie')
        self.kodi_db.add_update_art(movie.get('poster'), movieid, 'thumb', 'movie')
        self.kodi_db.add_genres(movieid, movie.get('genres'))

        self._add_people(movieid, movie)

    def _get_imdb_unique_id(self, movie):
        """
        Retrives imdb unique data from movie for uniqueid insert as a dict
        Arguments
        movie: dict with movie info
        """

        return {
            'movieid': movie.get('movieid'),
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
            'movieid': movie.get('movieid'),
            'value': movie.get('id'),
            'type': 'release'
        }

    def _get_ratings_data(self, movie):
        return self._pick(movie, ['rating', 'votecount', 'moveid'])

    def _map_move_data(self, movie):
        last_update = self.date_utils.get_kodi_date_format(movie.get('last_update'))
        movie.update({
            'shortplot': None,
            'tagline': None,
            'runtime': self._get_runtime_in_seconds(movie.get('runtime')),
            'studio': None,
            'trailer': None,
            'last_update': last_update,
            'version': self._generate_str_hash(movie.get('version'), last_update)
        })
        list_items = {}
        for key, value in movie.iteritems():
            if type(value) is list:
                list_items["%s_list" % key] = self._map_array(value)
        movie.update(list_items)
        return movie

    def _generate_str_hash(self, version, last_update):
        return "%s:%s" % (version, last_update)

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
    def _should_update(self, orgMovie, newMovie):
        pass

class IncrementalMovieUpdater(Movies):
    '''Does an check to only update changed movies '''

    @staticmethod
    def get_name():
        return 'Incremental Update'

    def _should_update(self, orgMovie, newMovie):
        return (orgMovie.get('version') != newMovie.get('version'))

class FullMovieUpdater(Movies):
    ''' Updates all movies regardless of last update '''

    @staticmethod
    def get_name():
        return 'Full Update'

    def _should_update(self, orgMovie, newMovie):
            return True