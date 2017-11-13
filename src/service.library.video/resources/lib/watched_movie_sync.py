""" Utils to help sync watch state of movies """

from resources.lib.date_utils import DateUtils
class WatchedSync(object):
    """ Class to facilitate watchedstate syncing """

    def __init__(self):
        self.date_utils = DateUtils()

    def sync(self, movies, remote_state):
        """
            returns local changes, remote state
        """
        movie_map = self._flatten_movies(movies)

        for imdb_id, local_movie in movie_map.iteritems():
            remote_movie = remote_state.get(imdb_id)
            if not remote_movie:
                remote_state[imdb_id] = self._get_remote(local_movie)
                continue

            if remote_movie.get('watched') == local_movie.get('watched'):
                continue # Nothing to sync

            # Update remote_movie in case we need it
            remote_last_played = self.date_utils.parse_kodi_date(remote_movie.get('lastPlayed'))
            remote_movie['lastPlayed'] = remote_last_played

            last_played = local_movie.get('lastPlayed')

            if not last_played and remote_last_played:
                self._update_movie(local_movie, remote_movie)
                continue

            if last_played > remote_last_played:
                self._update_movie(remote_movie, local_movie)
            else:
                self._update_movie(local_movie, remote_movie)

        local_changelog = self._get_local_changelog(movie_map)
        return local_changelog, remote_state

    def _get_local_changelog(self, movie_map):
        local_changelog = []
        for local_movie in movie_map.itervalues():
            watched = local_movie.get('watched')
            last_played = local_movie.get('lastPlayed')
            diff = [movie for movie in local_movie.get('movies')
                    if not self._is_watched(movie.get('playCount')) == watched]

            for movie in diff:
                movie['playCount'] = self._watched_to_playcount(watched)
                movie['lastPlayed'] = last_played
                local_changelog.append(movie)

        return local_changelog

    def _flatten_movies(self, movies):
        movie_map = {}
        # Flatmap movies
        for movie in movies:
            imdb_id = movie.get('imdb')
            last_played = self.date_utils.parse_kodi_date(movie.get('lastPlayed'))
            mapped_movie = movie_map.get(imdb_id)
            if not mapped_movie:
                movie_map[imdb_id] = {
                    'imdb': imdb_id,
                    'watched': self._is_watched(movie.get('playCount')),
                    'lastPlayed': last_played,
                    'movies': [movie]
                }
            elif (last_played and mapped_movie.get('lastPlayed') < last_played):
                mapped_movie['watched'] = self._is_watched(movie.get('playCount'))
                mapped_movie['lastPlayed'] = last_played
                mapped_movie['movies'].append(movie)
            else:
                mapped_movie['movies'].append(movie)

        return movie_map

    def _update_movie(self, org_movie, other_movie):
        return org_movie.update({
            'watched': other_movie.get('watched'),
            'lastPlayed': other_movie.get('lastPlayed')
        })

    def _watched_to_playcount(self, watched):
        if watched:
            return 1
        return 0

    def _is_watched(self, play_count):
        return play_count > 0

    def _get_remote(self, movie):
        return {
            'imdb': movie.get('imdb'),
            'watched': movie.get('watched'),
            'lastPlayed': movie.get('lastPlayed')
        }