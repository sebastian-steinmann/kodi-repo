""" Class to call remote http api """
import logging
from http_client import HttpClient

log = logging.getLogger("DINGS.api") # pylint: disable=invalid-name

class Api(object):
    """ Class to call remote http api """
    def __init__(self, host, user, password):
        self.client = HttpClient("%s/api/" % host, user, password)

    def get_movies_from(self, last_update):
        """
        Returns a list of movies changed from last_update
        Arguments:
        last_update: string, datetime
        """
        return self.client.get('/movies/since/%s' % last_update)

    def get_all_movies(self):
        """ Fetch all movies from service """
        return self.client.get("/movies/all")


    def get_all_series(self):
        """ Gets all series from service """
        pass
