
import logging
import xbmc

##################################################################################################

from resources.lib.artwork import Artwork


class KodiObjects(object):

    def __init__(self, cursor):
        self.cursor = cursor
        self.kodi_version = int(xbmc.getInfoLabel('System.BuildVersion')[:2])
        self.artwork = Artwork()


    def add_uniqueid(self, **kvargs):
        """
            Adds a refrence between a movie and external id and returns the new id
            Arguments
            mediaid: int
            media_type: movie,tvshow
            value: int, external id
            type: type of external id
        """
        query = (
            '''
            INSERT INTO uniqueid(
                media_id, media_type, value, type)

            VALUES (:mediaid, :media_type, :value, :type)
            '''
        )
        self.cursor.execute(query, kvargs)
        return self.cursor.lastrowid


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

    def add_path(self, full_path, dateadded, version, media_type, **kvargs):
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
            self.cursor.execute(query, (full_path, media_type, 'metadata.local', 1, version, dateadded))
            path_id = self.cursor.lastrowid
        return path_id


    ## Ratings
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

            VALUES (:media_id, :media_type, 'default', :rating, :votecount)
            '''
        )
        self.cursor.execute(query, kvargs)
        return self.cursor.lastrowid

    def update_ratings(self, rating, votecount, ratingid, media_type, **kvargs):
        """
            Adds a new rating record and returns the id
            Arguments as kvargs:
            ratingid: int
            rating: double
            votecount: int
        """
        query = '''
            UPDATE rating
            SET media_type = ?, rating_type = 'default', rating = ?, votes = ?
            WHERE rating_id = ?
        '''
        self.cursor.execute(query, (media_type, rating, votecount, ratingid,))