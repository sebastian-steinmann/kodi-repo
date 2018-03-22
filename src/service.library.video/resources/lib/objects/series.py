""" Handle series """
import logging
from urlparse import urlparse

from resources.lib.util import settings
from resources.lib.objects.kodi_series import KodiSeries
from resources.lib.date_utils import DateUtils

log = logging.getLogger("DINGS.db.series")  # pylint: disable=invalid-name


class Series(object):

    def __init__(self, cursor):
        self.cursor = cursor
        self.kodi_db = KodiSeries(cursor)

    def get_update(self, serie):
        tvshowid = self.kodi_db.get_serie(
            serie.get('seriesId')) or self._add_serie(serie)

        for season, episodes in serie.get('seasons'):
            seasonid = self.kodi_db.get_season(tvshowid, season) or self._add_season(tvshowid, season)

            for episode in episodes:
                episode = self.kodi_db.get_episode(episode.get('releaseId'))
                if episode:
                    # check update
                    # get file/folder?
                    # compare checksum?
                    pass
                else:
                    self._add_episode(tvshowid, seasonid, episode)


    def _add_serie(self, serie):
        tvshowid = self.kodi_db.create_entry()
        serie['uniqueid'] = self.kodi_db.add_uniqueid({
            'mediaid': tvshowid,
            'media_type': 'tvshow',
            'type': 'tvdb',
            'value': serie.get('seriesId')
        })

        pathid = self.kodi_db.add_path('full_path', serie.get('last_updated'), 1, 'tvshow')
        self.kodi_db.link_tvshow(tvshowid, pathid)
        ratingid = self.kodi_db.add_ratings({
            'media_id': tvshowid,
            'media_type': 'tvshow',
            'rating': 0,
            'votecount': 0 # har ikke data?
        })

        ## TODO
        # Add genres
        # add actors
        # add studio
        # add writer?
        # Add art?
        # add anything else?

        self.kodi_db.add_serie(**serie)

        return tvshowid

    def _add_season(self, tvshowid, season):
        # Create entry
        # Add rating?
        # set data
        # add art?
        return 1

    def _add_episode(self, tvshowid. seasonid,, pathid, episode):
        # add entry
        # add rating
        # add file
        # add episode
        # Add art?
        pass
