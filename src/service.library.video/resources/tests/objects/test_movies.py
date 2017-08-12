""" Test movies implementation """

import unittest
from resources.lib.objects.movies import FullMovieUpdater, IncrementalMovieUpdater
from resources.lib.update_strategy import ForceStrategy

from mock import MagicMock, patch, ANY


class MoviesTests(unittest.TestCase):
    def setUp(self):
        self.settings = {
            'username': 'myusername',
            'password': 'password',
            'host': 'http://host.no',
            'endpoint': 'http://host.no'
        }
        self.settings_patch = patch(
            'resources.lib.objects.movies.settings', side_effect=self.fake_settings_sideeffect)
        self.settings_patch.start()
        self.base_movie = {
            "id": "100",
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
            "votecount": 100,
            "rating": 6.4,
            "year": "",
            "imdb": "t123123",
            "sorttitle": "",
            "runtime": "100",
            "mpaa": "pg13",
            "country": [""],
            "studios": [""],
            "trailer": None,
            "boxset": "2",
            "actors": ["Actor 1"]
        }

    def tearDown(self):
        self.settings_patch.stop()

    def fake_settings_sideeffect(self, key):
        return self.settings[key]

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_get_fullpath_from_settings(self, kodiMoviesMock):
        movies = FullMovieUpdater(None)
        full_path = movies._get_full_path("testFolder")
        self.assertEqual(
            "http://myusername:password@host.no/movies/testFolder", full_path)

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_add(self, mock_class):
        kodi_db_mock = mock_class.return_value

        movie = self.base_movie.copy()
        imdb_id = movie.get('imdb')
        movieid = 13
        rating_id = 12
        uniqueid = 14
        rating = movie.get('rating')
        votecount = movie.get('votecount')

        kodi_db_mock.get_movie_from_imdb.return_value = None
        kodi_db_mock.get_movie_from_release.return_value = None
        kodi_db_mock.create_entry.return_value = movieid
        kodi_db_mock.add_rating.return_value = rating_id
        kodi_db_mock.add_uniqueid.return_value = uniqueid

        movies = FullMovieUpdater(MagicMock())

        movies.update(movie)

        kodi_db_mock.create_entry.assert_called_with()
        kodi_db_mock.add_ratings.assert_called_with(
            media_type='movie',
            movieid=movieid,
            rating=rating,
            rating_type='default',
            votecount=votecount)

        kodi_db_mock.add_uniqueid.assert_any_call(
            movieid=movieid,
            media_type="movie",
            value=imdb_id,
            type="imdb")
        kodi_db_mock.add_uniqueid.assert_any_call(
            movieid=movieid,
            media_type="movie",
            value=movie.get('id'),
            type="release")
        kodi_db_mock.add_movie.assert_called()
        args, kwargs = kodi_db_mock.add_movie.call_args
        self.assertEqual(int(movie.get('runtime')) * 60, kwargs.get('runtime'))

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_update(self, mockClass):
        kodi_db_mock = mockClass.return_value

        movies = FullMovieUpdater(None)

        movieid = 13
        rating_id = 12
        uniqueid = 14

        path_id = 1
        file_id = 2

        movie = dict(self.base_movie)

        kodi_db_mock.get_movie_from_imdb.return_value = [
            movieid, file_id, uniqueid, path_id, '2014-11-21 19:14:25', None]
        kodi_db_mock.get_movie_from_release.return_value = None
        kodi_db_mock.get_ratingid.return_value = rating_id
        kodi_db_mock.get_path_by_media_id.return_value = path_id

        movies.update(movie)

        kodi_db_mock.update_movie.assert_called()
        kodi_db_mock.update_ratings.assert_called_with(
            media_type='movie',
            rating=movie.get('rating'),
            rating_type='default',
            ratingid=rating_id,
            votecount=movie.get('votecount')
        )
        kodi_db_mock.update_path.assert_called_with(
            last_update=movie.get('last_update'),
            media_type='movie',
            path=movies._get_full_path(movie.get('folder')),
            path_id=path_id,
            scraper='metadata.local'
        )
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

        kodi_db_mock.add_people.assert_called_with(
            movieid, expected_people, 'movie')

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_add_release_id_when_missing(self, mockClass):
        kodi_db_mock = mockClass.return_value

        movieid = 13
        rating_id = 12
        uniqueid_imdbid = 14
        uniqueidid = 15
        path_id = 1
        file_id = 2
        movie = self.base_movie.copy()

        kodi_db_mock.get_movie_from_imdb.return_value = [
            movieid, file_id, uniqueid_imdbid, path_id, '2014-11-21 19:14:25', None]
        kodi_db_mock.get_movie_from_release.return_value = None
        kodi_db_mock.create_entry.return_value = movieid
        kodi_db_mock.add_rating.return_value = rating_id
        kodi_db_mock.add_uniqueid.return_value = uniqueidid

        movies = FullMovieUpdater(MagicMock())
        movie = self.base_movie.copy()
        movies.update(movie)

        kodi_db_mock.create_entry.assert_not_called()
        kodi_db_mock.add_ratings.assert_not_called()

        kodi_db_mock.add_uniqueid.assert_called_with(
            media_type='movie',
            movieid=movieid,
            type='release',
            value=movie.get('id')
        )

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_use_release_id(self, mockClass):
        kodi_db_mock = mockClass.return_value

        movieid = 13
        rating_id = 12
        uniqueid_imdbid = 14
        path_id = 1
        file_id = 2
        movie = self.base_movie.copy()

        kodi_db_mock.get_movie_from_imdb.return_value = None
        kodi_db_mock.get_ratingid.return_value = rating_id
        kodi_db_mock.get_movie_from_release.return_value = [
            movieid, file_id, uniqueid_imdbid, path_id, '2014-11-21 19:14:25', movie.get('id')]

        movies = FullMovieUpdater(MagicMock())
        movie = self.base_movie.copy()
        movies.update(movie)

        kodi_db_mock.create_entry.assert_not_called()
        kodi_db_mock.add_ratings.assert_not_called()

        kodi_db_mock.add_uniqueid.assert_not_called()

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_map_movie_data(self, mockClass):
        movie = self.base_movie.copy()

        movies = FullMovieUpdater(MagicMock())
        result = movies._get_movie_data(movie)

        self.assertIn('studio', result)
        self.assertEqual(' / '.join(movie.get('writers')),
                         result.get('writers'))

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_pick_fields(self, mock_movies):
        movie = self.base_movie.copy()

        movies = FullMovieUpdater(MagicMock())
        movie = self.base_movie.copy()
        result = movies._pick(movie, ['title'])

        self.assertEqual({
            'title': movie.get('title')
        }, result)

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_add_extras(self, mock_movies):
        movie = self.base_movie.copy()

        movies = FullMovieUpdater(MagicMock())
        movie = self.base_movie.copy()

        result = movies._pick(movie, ['title'], {
            'banana': 'tree'
        })

        self.assertEqual({
            'title': movie.get('title'),
            'banana': 'tree'
        }, result)

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_include_trailer(self, mock_movies):
        movie = self.base_movie.copy()

        movies = FullMovieUpdater(MagicMock())
        movie = self.base_movie.copy()
        movie.update(country=["USA","UK"])

        result = movies._get_movie_data(movie)

        self.assertIn('country', result)
        self.assertEqual('USA / UK', result.get('country'))

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_send_fileid_to_add_movies(self, mock_movies):
        db = mock_movies.return_value
        movie = self.base_movie.copy()

        movies = FullMovieUpdater(MagicMock())

        result = movies._add(movie)

        args, kvargs = db.add_movie.call_args
        self.assertIn('fileid', kvargs)

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_not_fail_on_missing_runtime(self, mock_movies):
        db = mock_movies.return_value
        movie = self.base_movie.copy()
        movie.update({'runtime': None})

        movies = FullMovieUpdater(MagicMock())

        result = movies._get_movie_data(movie)

        self.assertEqual(None, result.get('runtime'))

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_return_moves_to_remove(self, mock_movies):
        db = mock_movies.return_value
        db.get_movie_refs.return_value = [
            (101, '1', "movie 1", 11),
            (102, '2', "movie 2", 12),
            (103, '3', "movie 3", 13),
            (104, '4', "movie 4", 14)
        ]
        all_movies = [
            {'id': 1},
            {'id': 2},
            {'id': 3}
        ]
        release_ids = [m.get('id') for m in all_movies]
        self.assertEqual(release_ids, [1,2,3])

        movies = FullMovieUpdater(MagicMock())

        result = movies.get_movies_to_remove(release_ids)

        self.assertEqual(1, len(result))
        self.assertEqual(104, result[0]['media_id'])

