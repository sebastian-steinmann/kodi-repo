""" Test movies implementation """
import unittest
from resources.lib.watched_movie_sync import WatchedSync
from resources.lib.date_utils import DateUtils

class WatchedStateSync(unittest.TestCase):
    def setUp(self):
        self.syncer = WatchedSync()
        self.date_utils = DateUtils()

    def tearDown(self):
        pass


    def test_should_save_watched_to_remote(self):
        movies = [
            {
                'id': 1,
                'imdb': 't1',
                'playCount': 1,
                'lastPlayed': '2017-11-04 13:17:30'
            }
        ]
        remote = {}

        expected_remote_changelog = {
            't1': {
                'imdb': 't1',
                'watched': True,
                'lastPlayed': self.date_utils.parse_kodi_date('2017-11-04 13:17:30')
            }
        }

        local_changelog, remote_changelog = self.syncer.sync(movies, remote)
        self.assertListEqual([], local_changelog)
        self.assertDictEqual(remote_changelog, expected_remote_changelog)

    def test_should_update_local_with_watched(self):
        movies = [
            {
                'id': 1,
                'imdb': 't1',
                'playCount': 0,
                'lastPlayed': None
            }
        ]
        remote = {
            't1': {
                'imdb': 't1',
                'watched': True,
                'lastPlayed': '2017-11-04 13:17:30'
            }
        }

        expected_local_changelog = [
            {
                'id': 1,
                'imdb': 't1',
                'playCount': 1,
                'lastPlayed': self.date_utils.parse_kodi_date('2017-11-04 13:17:30')
            }
        ]
        expected_remote_changelog = remote.copy()

        local_changelog, remote_changelog = self.syncer.sync(movies, remote)
        self.assertDictEqual(remote_changelog, expected_remote_changelog, "Remotes")
        self.assertListEqual(expected_local_changelog, local_changelog)


    def test_should_handle_multiple_movies(self):
        movies = [
            {
                'id': 1,
                'imdb': 't1',
                'playCount': 1,
                'lastPlayed': '2017-09-09 18:31:59'
            },
            {
                'id': 2,
                'imdb': 't1',
                'playCount': 0,
                'lastPlayed': '2016-09-09 18:31:59'
            }
        ]
        remote = {
            't1': {
                'imdb': 't1',
                'watched': False,
                'lastPlayed': '2017-11-04 13:17:30'
            }
        }

        expected_local_changelog = [
            {
                'id': 1,
                'imdb': 't1',
                'playCount': 0,
                'lastPlayed': self.date_utils.parse_kodi_date('2017-11-04 13:17:30')
            }
        ]
        expected_remote_changelog = remote.copy()

        local_changelog, remote_changelog = self.syncer.sync(movies, remote)
        self.assertListEqual(expected_local_changelog, local_changelog)
        self.assertDictEqual(remote_changelog, expected_remote_changelog)

    def test_should_update_local_with_unwatched(self):
        movies = [
            {
                'id': 1,
                'imdb': 't1',
                'playCount': 0,
                'lastPlayed': '2017-09-09 18:31:59'
            },
            {
                'id': 2,
                'imdb': 't1',
                'playCount': 1,
                'lastPlayed': '2016-09-09 18:31:59'
            }
        ]
        remote = {
            't1': {
                'imdb': 't1',
                'watched': False,
                'lastPlayed': '2017-11-04 13:17:30'
            }
        }

        expected_local_changelog = [
            {
                'id': 2,
                'imdb': 't1',
                'playCount': 0,
                'lastPlayed': self.date_utils.parse_kodi_date('2017-09-09 18:31:59')
            }
        ]
        expected_remote_changelog = remote.copy()

        local_changelog, remote_changelog = self.syncer.sync(movies, remote)
        self.assertListEqual(expected_local_changelog, local_changelog)
        self.assertDictEqual(remote_changelog, expected_remote_changelog)


    def test_should_update_all_locals_even_if_local_is_correct(self):
        movies = [
            {
                'id': 1,
                'imdb': 't1',
                'playCount': 1,
                'lastPlayed': '2017-09-09 18:31:59'
            },
            {
                'id': 2,
                'imdb': 't1',
                'playCount': 0,
                'lastPlayed': '2016-09-09 18:31:59'
            }
        ]
        remote = {
            't1': {
                'imdb': 't1',
                'watched': False,
                'lastPlayed': '2017-11-04 13:17:30'
            }
        }

        expected_local_changelog = [
            {
                'id': 2,
                'imdb': 't1',
                'playCount': 1,
                'lastPlayed': self.date_utils.parse_kodi_date('2017-09-09 18:31:59')
            }
        ]
        expected_remote_changelog = remote.copy()
        expected_remote_changelog['t1'].update({
            'watched': True,
            'lastPlayed': self.date_utils.parse_kodi_date('2017-09-09 18:31:59')
        })


        local_changelog, remote_changelog = self.syncer.sync(movies, remote)
        self.assertListEqual(expected_local_changelog, local_changelog)
        self.assertDictEqual(remote_changelog, expected_remote_changelog)

    def test_should_update_all_locals_even_if_local_is_correct2(self):
        movies = [
            {
                'id': 1,
                'imdb': 't1',
                'playCount': 1,
                'lastPlayed': '2017-09-09 18:31:59'
            },
            {
                'id': 2,
                'imdb': 't1',
                'playCount': 0,
                'lastPlayed': '2016-09-09 18:31:59'
            },
            {
                'id': 3,
                'imdb': 't2',
                'playCount': 1,
                'lastPlayed': '2016-09-09 18:31:59'
            }
        ]
        remote = {
            't1': {
                'imdb': 't1',
                'watched': False,
                'lastPlayed': '2017-11-04 13:17:30'
            }
        }

        expected_local_changelog = [
            {
                'id': 2,
                'imdb': 't1',
                'playCount': 1,
                'lastPlayed': self.date_utils.parse_kodi_date('2017-09-09 18:31:59')
            }
        ]
        expected_remote_changelog = remote.copy()
        expected_remote_changelog['t1'].update({
            'watched': True,
            'lastPlayed': self.date_utils.parse_kodi_date('2017-09-09 18:31:59')
        })
        expected_remote_changelog['t2'] = {
            'imdb': 't2',
            'watched': True,
            'lastPlayed': self.date_utils.parse_kodi_date('2016-09-09 18:31:59')
        }


        local_changelog, remote_changelog = self.syncer.sync(movies, remote)
        self.assertListEqual(expected_local_changelog, local_changelog)
        self.assertDictEqual(remote_changelog, expected_remote_changelog)