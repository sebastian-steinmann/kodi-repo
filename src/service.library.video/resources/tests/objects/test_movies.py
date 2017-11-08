""" Test movies implementation """

import unittest
from resources.lib.objects.movies import FullMovieUpdater, IncrementalMovieUpdater
from resources.lib.update_strategy import ForceStrategy
from resources.lib.date_utils import DateUtils

import resources.lib.loghandler as loghandler

import sys
import logging



from mock import MagicMock, patch, ANY


class MoviesTests(unittest.TestCase):
    dateutils = DateUtils()

    def setUp(self):
        logger = loghandler.config()
        logger.addHandler(logging.StreamHandler(sys.stdout))

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
            "dateadded": "2012-07-27T08:16:35.000Z",
            "last_update": "2012-07-27T08:16:35.000Z",
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
            "actors": ["Actor 1"],
            "version": "1"
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
            "http://myusername:password@host.no/movies/testFolder/", full_path)

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

        movies.update(movie.copy()) # copy so values is not overwritten

        kodi_db_mock.create_entry.assert_called_with()
        self._assert_args(kodi_db_mock.add_ratings,
                          movieid=movieid,
                          rating=rating,
                          votecount=votecount
                         )

        kodi_db_mock.add_uniqueid.assert_any_call(
            movieid=movieid,
            value=imdb_id,
            type="imdb")
        kodi_db_mock.add_uniqueid.assert_any_call(
            movieid=movieid,
            value=movie.get('id'),
            type="release")
        kodi_db_mock.add_movie.assert_called()

        self._assert_args(kodi_db_mock.add_movie,
                          runtime = int(movie.get('runtime')) * 60
                         )

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
            movieid, file_id, uniqueid, path_id, '2014-11-21 19:14:25', 1, None]
        kodi_db_mock.get_movie_from_release.return_value = None
        kodi_db_mock.get_ratingid.return_value = rating_id

        movies.update(movie.copy())

        kodi_db_mock.update_movie.assert_called()
        self._assert_args(kodi_db_mock.update_ratings, rating=movie.get('rating'),
            ratingid=rating_id,
            votecount=movie.get('votecount')
        )

        self._assert_args(kodi_db_mock.update_path,
            last_update = self.dateutils.get_kodi_date_format(movie.get('last_update')),
            full_path= movies._get_full_path(movie.get('folder')),
            pathid = path_id
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

    def _assert_args(self, method, **args):
        _, call_args = method.call_args
        for arg, value in args.iteritems():
            self.assertIn(arg, call_args)
            self.assertEqual(value, call_args[arg])

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
            movieid, file_id, uniqueid_imdbid, path_id, '2014-11-21 19:14:25', 1, None]
        kodi_db_mock.get_movie_from_release.return_value = None
        kodi_db_mock.create_entry.return_value = movieid
        kodi_db_mock.add_rating.return_value = rating_id
        kodi_db_mock.add_uniqueid.return_value = uniqueidid

        movies = FullMovieUpdater(MagicMock())
        movie = self.base_movie.copy()
        movies.update(movie.copy())

        kodi_db_mock.create_entry.assert_not_called()
        kodi_db_mock.add_ratings.assert_not_called()

        kodi_db_mock.add_uniqueid.assert_called_with(
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
            movieid, file_id, uniqueid_imdbid, path_id, '2014-11-21 19:14:25', 1, movie.get('id')]

        movies = FullMovieUpdater(MagicMock())
        movie = self.base_movie.copy()
        movies.update(movie.copy())

        kodi_db_mock.create_entry.assert_not_called()
        kodi_db_mock.add_ratings.assert_not_called()

        kodi_db_mock.add_uniqueid.assert_not_called()

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_compare_versions(self, mockClass):
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
            movieid, file_id, uniqueid_imdbid, path_id, '2014-11-21 19:14:25', "1:2012-07-27 08:16:35", movie.get('id')]

        movies = IncrementalMovieUpdater(MagicMock())
        res = movies.update(movie.copy())

        self.assertFalse(res)

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_compare_versions_and_update(self, mockClass):
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
            movieid, file_id, uniqueid_imdbid, path_id, '2014-11-21 19:14:25', "1:2012-07-25 08:16:35", movie.get('id')]

        movies = IncrementalMovieUpdater(MagicMock())
        res = movies.update(movie.copy())

        self.assertTrue(res)

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_map_movie_data(self, mockClass):
        movie = self.base_movie.copy()

        movies = FullMovieUpdater(MagicMock())
        result = movies._get_movie_data(movie.copy())

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

        result = movies._get_movie_data(movie.copy())

        self.assertIn('country', result)
        self.assertEqual('USA / UK', result.get('country'))

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_send_fileid_to_add_movies(self, mock_movies):
        db = mock_movies.return_value
        movie = self.base_movie.copy()

        movies = FullMovieUpdater(MagicMock())

        result = movies._add(movie.copy())

        args, kvargs = db.add_movie.call_args
        self.assertIn('fileid', kvargs)

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_not_fail_on_missing_runtime(self, mock_movies):
        db = mock_movies.return_value
        movie = self.base_movie.copy()
        movie.update({'runtime': None})

        movies = FullMovieUpdater(MagicMock())

        result = movies._get_movie_data(movie.copy())

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


    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_do_nithing_if_tags_equal(self, mock_movies):
        db = mock_movies.return_value

        db.get_tags.return_value = []
        new_tags = ['Drama', 'Comedy']
        movieid = 12
        movie = {
            'movieid': movieid,
            'tags': new_tags
        }
        movies = FullMovieUpdater(MagicMock())
        movies._sync_tags(movie)

        db.remove_tag_links.assert_called_with(movieid, [])
        db.add_tags.assert_called_with(movieid, new_tags)

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_remove_tags(self, mock_movies):
        db = mock_movies.return_value

        db.get_tags.return_value = [
            (1, 'Drama', 12, 1),
            (2, 'Romance', 13, 2)
        ]
        new_tags = ['Drama']
        movieid = 12
        movie = {
            'movieid': movieid,
            'tags': new_tags
        }
        movies = FullMovieUpdater(MagicMock())
        movies._sync_tags(movie)

        db.remove_tag_links.assert_called_with(movieid, [2])
        db.add_tags.assert_called_with(movieid, [])

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_add_tags(self, mock_movies):
        db = mock_movies.return_value

        db.get_tags.return_value = [
            (1, 'Drama', 12, 1)
        ]
        new_tags = ['Drama', 'Comedy']
        movieid = 12
        movie = {
            'movieid': movieid,
            'tags': new_tags
        }
        movies = FullMovieUpdater(MagicMock())
        movies._sync_tags(movie)

        db.remove_tag_links.assert_called_with(movieid, [])
        db.add_tags.assert_called_with(movieid, ['Comedy'])


    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_only_remove_remote_tags(self, mock_movies):
        db = mock_movies.return_value

        db.get_tags.return_value = [
            (1, 'Drama', 12, 1),
            (2, 'Romance', 13, 2),
            (3, 'Test', None, 3)
        ]
        new_tags = ['Drama']
        movieid = 12
        movie = {
            'movieid': movieid,
            'tags': new_tags
        }
        movies = FullMovieUpdater(MagicMock())
        movies._sync_tags(movie)

        db.remove_tag_links.assert_called_with(movieid, [2])
        db.add_tags.assert_called_with(movieid, [])

    @patch('resources.lib.objects.movies.KodiMovies')
    def test_should_reuse_tag_id(self, mock_movies):
        db = mock_movies.return_value

        db.get_tags.return_value = [
            (1, 'Drama', 12, 1),
            (2, 'Comedy', None, None)
        ]
        new_tags = ['Drama', 'Comedy', 'Action']
        movieid = 12
        movie = {
            'movieid': movieid,
            'tags': new_tags
        }
        movies = FullMovieUpdater(MagicMock())
        movies._sync_tags(movie)

        db.remove_tag_links.assert_called_with(movieid, [])
        db.add_tag_links.assert_called_with(movieid, [2])
        db.add_tags.assert_called_with(movieid, ['Action'])