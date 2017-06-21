""" Class to call remote http api """
import logging
from http_client import HttpClient

log = logging.getLogger("DINGS.api") # pylint: disable=invalid-name

class Api(object):
    """ Class to call remote http api """
    def __init__(self, host, user, password):
        self.client = HttpClient("%s/api/" % host, user, password)

    def get_all_movies(self):
        """ Fetch all movies from service """
        return self.client.get("/movies/all")

        """ return [
            {
               x "id": "1",
               x "title": "Filmnavn",
               x "folder": "http://user:pass@server/filnavn.720p/",
               x "filename": "filnavn.720p.mkv",
               x "dateadded": "timestamp",
               x "writers": ["sdf"],
               x "directors": ["df"],
               x "genres": ["comedy"],
               x "plot": "sdfsdf",
                "shortplot": "",
                "tagline": "",
               x "votecount": 0,
               x "rating": "2.3",
               x "year": "",
               x "imdb": "t234234",
                "sorttitle": "",
               x "runtime": "",
               x "mpaa": "pg13",
               x "country": "",
                "studios": [""],
                "trailer": "http:",
                "boxset": "2"
            },
            {
                "id": "2",
                "title": "Filmnavn2",
                "folder": "http://user:pass@server/filnavn2.720p/",
                "filename": "filnavn2.720p.mkv",
                "dateadded": "timestamp",
                "writers": ["sdf"],
                "directors": ["df"],
                "genres": ["comedy"],
                "plot": "sdfsdf",
                "shortplot": "",
                "tagline": "",
                "votecount": 0,
                "rating": "2.3",
                "year": "",
                "imdb": "t234232",
                "sorttitle": "",
                "runtime": "",
                "mpaa": "pg13",
                "country": "",
                "studios": [""],
                "trailer": "http:",
                "boxset": "2"
            }
        ]"""

    def get_all_series(self):
        """ Gets all series from service """
        pass
