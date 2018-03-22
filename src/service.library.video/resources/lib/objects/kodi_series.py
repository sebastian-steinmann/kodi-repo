from resources.lib.objects.kodi_objects import KodiObjects

class KodiSeries(KodiObjects):

    def get_serie(self, serie_id):
        query = '''
            select u.media_id from uniqueid u
            where
                u.media_type = 'tvshow'
                and value = ?
                and type = 'tvdb'
        '''

        self.cursor.execute(query, (serie_id,))
        try:
            return self.cursor.fetchone()
        except TypeError:
            return None



    def create_entry(self):
        self.cursor.execute("select coalesce(max(idMovie),0) from tvshow")
        return self.cursor.fetchone()[0] + 1


    def add_serie(self, title, plot, firstAired, genre, mpaa, studio, runtime):
        query = '''
            insert into tvshow (c1, c2, c3, c4, c5, c6, c7)
            VALUES (?, ?, ?,  ?, ?, ?, ?)
        '''

        self.cursor.execute(query, (title, plot, firstAired, genre, mpaa, studio, runtime))
        return self.cursor.lastrowid

    def get_season(self, tvshowid, season):
        query = '''
            select idSeason from seasons
            where idShow = ?
            and season = ?
        '''

        self.cursor.execute(query, (tvshowid, season))
        try:
            return self.cursor.fetchone()
        except TypeError:
            return None

    def get_episode(self, episode_id):
        query = '''
            select e.* from uniqueid u
            inner join episode e on (u.media_id = e.idEpisode)
            where
                u.media_type = 'episode'
                and value = ?
                and type = 'release'
        '''

        self.cursor.execute(query, (episode_id,))
        try:
            return self.cursor.fetchone()
        except TypeError:
            return None

    def link_tvshow(self, tvshowid, pathid):
        query = '''
            insert into tvshowlinkpath (idShow, idPath)
            VALUES (?, ?)
        '''

        self.cursor.execute(query, (tvshowid, pathid))