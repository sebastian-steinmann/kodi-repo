""" Test movies implementation """

import unittest
from resources.lib.objects.movies import Movies

from mock import MagicMock, patch, ANY

def fakeSettings(key):
    settings = {
        'username': 'myusername',
        'password': 'password',
        'host': 'http://host.no',
        'endpoint': 'http://host.no'
    }
    return settings[key]


class MoviesTests(unittest.TestCase):
    @patch('resources.lib.objects.movies.KodiMovies')
    def test_existing(self, mockClass):
        kodi_db_mock = mockClass.return_value
        imdb_id = "t123123"
        kodi_db_mock.get_movie_from_imdb.return_value = [1, 1, 1]
        movies = Movies(None)
        res = movies.existing(imdb_id)
        kodi_db_mock.get_movie_from_imdb.assert_called_with(imdb_id)
        self.assertTrue(res)

        @patch('resources.lib.objects.movies.KodiMovies')
        def test_not_existing(self, mockClass):
            kodi_db_mock = mockClass.return_value = kodi_db_mock
            imdb_id = "t123123"
            kodi_db_mock.get_movie_from_imdb.return_value = None
            movies = Movies(None)
            res = movies.existing(imdb_id)
            kodi_db_mock.get_movie_from_imdb.assert_called_with(imdb_id)
            self.assertFalse(res)

    @patch('resources.lib.objects.movies.settings', side_effect=fakeSettings)
    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_get_fullpath_from_settings(self, kodiMoviesMock, settingsMock):
        movies = Movies(None)
        full_path = movies.get_full_path("testFolder")
        self.assertEqual("http://myusername:password@host.no/movies/testFolder", full_path)


    @patch('resources.lib.objects.movies.settings', side_effect=fakeSettings)
    @patch('resources.lib.objects.movies.KodiMovies')
    def test_add(self, MockClass, fake_settings):
        kodi_db_mock = MockClass.return_value

        imdb_id = "t123123"
        movieid = 13
        rating_id = 12
        uniqueid = 14
        rating = 2.3
        votecount = 100

        kodi_db_mock.get_movie_from_imdb.return_value = None
        kodi_db_mock.create_entry.return_value = movieid
        kodi_db_mock.add_rating.return_value = rating_id
        kodi_db_mock.add_uniqueid.return_value = uniqueid

        movies = Movies(MagicMock())
        movie = {
            "id": "1",
            "title": "Filmnavn",
            "folder": "filnavn.720p",
            "filename": "filnavn.720p.mkv",
            "dateadded": "timestamp",
            "writers": ["sdf"],
            "directors": ["df"],
            "genres": ["comedy"],
            "plot": "sdfsdf",
            "shortplot": "",
            "tagline": "",
            "votecount": votecount,
            "rating": rating,
            "year": "",
            "imdb": imdb_id,
            "sorttitle": "",
            "runtime": "100",
            "mpaa": "pg13",
            "country": "",
            "studios": [""],
            "trailer": "http:",
            "boxset": "2",
            "actors": ["Actor 1"]
        }
        movies.update(movie)

        kodi_db_mock.create_entry.assert_called_with()
        kodi_db_mock.add_ratings.assert_called_with(movieid, "movie", "default", rating, votecount)

        kodi_db_mock.add_uniqueid.assert_called_with(movieid, "movie", imdb_id, "imdb")
        kodi_db_mock.add_movie.assert_called_with(ANY, ANY, ANY, ANY, None, None,
                            ANY, ANY, ANY, ANY, ANY, ANY,
                            int(movie.get('runtime')) * 60, ANY, ANY, ANY, ANY, None, None,
                            ANY, ANY, ANY, ANY)

    @patch('resources.lib.objects.movies.settings', side_effect=fakeSettings)
    @patch('resources.lib.objects.movies.KodiMovies')
    def test_update(self, mockClass, fakeSettings):
        kodi_db_mock = MagicMock()
        kodi_db_mock = mockClass.return_value
        imdb_id = "t123123"
        movies = Movies(None)

        movieid = 13
        rating_id = 12
        uniqueid = 14
        rating = 2.3
        votecount = 100
        path_id = 1
        file_id = 2

        movie = {
            "id": "1",
            "title": "Filmnavn",
            "folder": "filnavn.720p",
            "filename": "filnavn.720p.mkv",
            "dateadded": "timestamp",
            "writers": ["sdf"],
            "directors": ["df"],
            "genres": ["comedy"],
            "plot": "sdfsdf",
            "shortplot": "",
            "tagline": "",
            "votecount": votecount,
            "rating": rating,
            "year": "",
            "imdb": imdb_id,
            "sorttitle": "",
            "runtime": "104",
            "mpaa": "pg13",
            "country": "",
            "studios": [""],
            "trailer": "http:",
            "boxset": "2",
            "actors": ["Actor 1"]
        }

        kodi_db_mock.get_movie_from_imdb.return_value = [movieid, uniqueid, file_id]
        kodi_db_mock.get_ratingid.return_value = rating_id
        kodi_db_mock.get_path_by_media_id.return_value = path_id

        movies.update(movie)

        kodi_db_mock.update_movie.assert_called()
        kodi_db_mock.update_ratings.assert_called_with(movieid, "movie", "default", rating, votecount, rating_id)
        kodi_db_mock.update_path.assert_called_with(path_id, movies.get_full_path(movie.get('folder')), 'movies', 'metadata.local')

        expected_people = [
            {
                'Name': movie.get('actors')[0],
                'Type': 'Actor'
            },
            {
                'Name': movie.get('writers')[0],
                'Type': 'Writer'
            },
            {
                'Name': movie.get('directors')[0],
                'Type': 'Director'
            }
        ]

        kodi_db_mock.add_people.assert_called_with(movieid, expected_people, 'movie')
