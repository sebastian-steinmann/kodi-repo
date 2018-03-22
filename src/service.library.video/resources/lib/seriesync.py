from datetime import datetime
from resources.lib.objects.series import Series
import resources.lib.objects.database as database
import logging

log = logging.getLogger("DINGS.series") # pylint: disable=invalid-name

class SeriesSync(object):
    client_version = '1'

    stop_thread = False

    pdialog = None
    title = None
    count = 0
    total = 0

    def __init__(self, api, pdialog):
        self.api = api;
        self.pdialog = pdialog

    def _map_episodes_to_struct(self, data):
        series = dict((s.get('id'), s) for s in data.get('tvshows'))

        for episode in data.get("episodes"):
            serie = series.get(episode.get('serie'))
            seasons = serie.get('seasons');
            if not seasons:
                seasons = serie['seasons'] = {}

            season = seasons.get(episode.get('season'))
            if not season:
                season = seasons[episode.get('season')] = []

            season.append(episode)
        return series

    def full_sync(self):
        start_time = datetime.now()
        data = self.api.get_all_series()

        series = self._map_episodes_to_struct(data)
        with database.DatabaseConn() as cursor_video:
            tvshow_db = Series(cursor_video)
            for serie in self._added(series):
                tvshow_db.update(serie)

        return start_time, 0

    def _added(self, items, total=None):
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

