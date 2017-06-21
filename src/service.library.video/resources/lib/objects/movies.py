""" Handle movies """
import logging
from urlparse import urlparse

from resources.lib.util import settings
from resources.lib.objects.kodi_movies import KodiMovies

log = logging.getLogger("DINGS.db") # pylint: disable=invalid-name

class Movies(object):
    """ Class to handle sync to kodi-db """

    def __init__(self, cursor):
        self.kodi_db = KodiMovies(cursor)

    def existing(self, imdb_id):
        """ Check if movie exists in db """
        movie = self.get_by_imdb(imdb_id)
        return movie != None

    def get_by_imdb(self, imdb_id):
        """ Retrives movie based on imdb_id """
        return self.kodi_db.get_movie_from_imdb(imdb_id)

    def get_full_path(self, folder):
        """ Add host, username and password to folderpath """
        url_parts = urlparse(settings("endpoint"))
        return "%s://%s:%s@%s%s/movies/%s" % (
            url_parts.scheme,
            settings("username"),
            settings("password"),
            url_parts.netloc,
            url_parts.path,
            folder
            )

    def update(self, movie):
        ''' Update or add a movie '''
        rating = movie.get("rating")
        votecount = movie.get("votecount")
        imdb = movie.get("imdb")
        folder = movie.get("folder")
        filename = movie.get("filename")
        dateadded = movie.get("dateadded")

        title = movie.get("title")
        plot = movie.get("plot")
        writer = " / ".join(movie.get("writers"))
        year = movie.get("year")
        runtime = movie.get("runtime")
        mpaa = movie.get("mpaa")
        genres = movie.get("genres")
        genre = " / ".join(genres)
        director = " / ".join(movie.get("directors"))
        country = " / ".join(movie.get("country"))

        update = True

        original_movie = self.kodi_db.get_movie_from_imdb(imdb)
        if original_movie is None:
            update = False
            movieid = self.kodi_db.create_entry()
        else:
            movieid, fileid, uniqueid = original_movie


        if update:
            ratingid = self.kodi_db.get_ratingid(movieid)

            pathid = self.kodi_db.get_path_by_media_id(movieid)
            log.info(pathid)

            self.kodi_db.update_ratings(movieid, 'movie', 'default', rating, votecount, ratingid)
            self.kodi_db.update_path(pathid, self.get_full_path(folder), 'movies', 'metadata.local')
            self.kodi_db.update_file(fileid, filename, pathid, dateadded)
            self.kodi_db.update_movie(
                title, plot, None, None,
                votecount, uniqueid, writer, year, uniqueid, title,
                runtime, mpaa, genre, director, title, None, None,
                country, year, movieid)
        else:
            #add ratings
            ratingid = self.kodi_db.add_ratings(movieid, "movie", "default", rating, votecount)

            # add unique id
            uniqueid = self.kodi_db.create_entry_uniqueid()
            uniqueid = self.kodi_db.add_uniqueid(movieid, "movie", imdb, "imdb")

            #add path
            pathid = self.kodi_db.add_path(self.get_full_path(folder), "movies", "metadata.local")
            fileid = self.kodi_db.add_file(filename, pathid, dateadded)

            # Add the movie
            self.kodi_db.add_movie(
                movieid, fileid, title, plot, None, None,
                votecount, uniqueid, writer, year, uniqueid, title,
                runtime, mpaa, genre, director, title, None, None,
                country, year)

        self.kodi_db.add_genres(movieid, genres, "movie")
