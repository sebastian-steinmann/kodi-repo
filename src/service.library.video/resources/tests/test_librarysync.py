""" Test movies implementation """
import unittest
from datetime import datetime
from resources.lib.librarysync import Library


from mock import MagicMock, patch


class LibraryTests(unittest.TestCase):
    def setUp(self):
        # %Y-%m-%dT%H:%M:%SZ
        self.settings = {
            'username': 'myusername',
            'password': 'password',
            'host': 'http://host.no',
            'endpoint': 'http://host.no',
            'LastIncrementalSync': None,
            'LastFullSync': None,
            'ClientVersion': Library.client_version
        }
        self.settings_patch = patch(
            'resources.lib.librarysync.settings', side_effect=self._fake_settings_sideeffect)
        self.settings_patch.start()

    def tearDown(self):
        self.settings_patch.stop()

    def _fake_settings_sideeffect(self, key, value=None):
        if value is None:
            return self.settings[key]
        self.settings[key] = value

    @patch('resources.lib.librarysync.FullMovieUpdater')
    @patch('resources.lib.librarysync.xbmc')
    @patch('resources.lib.librarysync.Api')
    def test_should_do_full_sync(self, mocked_api, mocked_xbmc, mocked_movies):
        mocked_xbmc.Monitor.return_value = MagicMock()

        service = Library()

        full_sync = service._should_do_full_sync()
        self.assertTrue(full_sync)

    @patch('resources.lib.librarysync.FullMovieUpdater')
    @patch('resources.lib.librarysync.xbmc')
    @patch('resources.lib.librarysync.Api')
    def test_should_call_api_with_correct_date(self, mocked_api, mocked_xbmc, mocked_movies):
        mocked_xbmc.Monitor.return_value = MagicMock()

        api_instance = mocked_api.return_value

        service = Library()
        service.update()

        api_instance.get_all_movies.assert_called()

    @patch('resources.lib.librarysync.FullMovieUpdater')
    @patch('resources.lib.librarysync.xbmc')
    @patch('resources.lib.librarysync.Api')
    def test_should_not_do_full_sync(self, mocked_api, mocked_xbmc, mocked_movies):
        mocked_xbmc.Monitor.return_value = MagicMock()
        service = Library()

        last_full_sync = datetime.now()
        self.settings['LastFullSync'] = service.date_utils.get_str_date(last_full_sync)

        self.assertAlmostEqual(last_full_sync.day, service._get_last_full_sync().day)

        full_sync = service._should_do_full_sync()
        self.assertFalse(full_sync)

    @patch('resources.lib.librarysync.FullMovieUpdater')
    @patch('resources.lib.librarysync.xbmc')
    @patch('resources.lib.librarysync.Api')
    def test_should_not_crash_on_empty_date(self, mocked_api, mocked_xbmc, mocked_movies):
        mocked_xbmc.Monitor.return_value = MagicMock()
        service = Library()

        last_full_sync = datetime(1970, 1, 1)
        self.settings['LastFullSync'] = ''

        self.assertAlmostEqual(last_full_sync.day, service._get_last_full_sync().day)

    @patch('resources.lib.librarysync.IncrementalMovieUpdater')
    @patch('resources.lib.librarysync.xbmc')
    @patch('resources.lib.librarysync.Api')
    def test_should_call_api_with_date_as_text(self, mocked_api, mocked_xbmc, mocked_movies):
        mocked_xbmc.Monitor.return_value = MagicMock()
        api = mocked_api.return_value
        service = Library()

        last_full_sync = datetime.now()
        #self._fake_settings_sideeffect('LastFullSync', service.get_str_date(last_full_sync))
        #self._fake_settings_sideeffect('LastIncrementalSync', service.get_str_date(last_full_sync))
        self.settings['LastFullSync'] = service.date_utils.get_str_date(last_full_sync)
        self.settings['LastIncrementalSync'] = service.date_utils.get_str_date(last_full_sync)

        service.update()

        api.get_movies_from.assert_called_with(service.date_utils.get_str_date(last_full_sync))

