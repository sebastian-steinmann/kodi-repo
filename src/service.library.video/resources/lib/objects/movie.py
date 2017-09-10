
class Movie(object):
    movieid = None
    title = None
    imdb = None

    def __init__(self, movie_info):
        self.__dict__.update(movie_info)