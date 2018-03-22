""" Test movies implementation """
import unittest
from datetime import datetime
from resources.lib.seriesync import SeriesSync
import logging
import sys


from mock import MagicMock, patch
import json


root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

log = logging.getLogger("DINGS.series") # pylint: disable=invalid-name

class FakeApi:
    def __init__(self):
        self.data = json.load(open('./src/service.library.video/resources/tests/series/test.1.json'))

    def get_all_series(self):
        return self.data

class SeriesSyncTest(unittest.TestCase):
    def setUp(self):
        self.api = FakeApi()

    @patch('resources.lib.librarysync.xbmc')
    def test_should_do_full_sync(self, mocked_xbmc):
        mocked_xbmc.Monitor.return_value = MagicMock()
        pdialog = MagicMock()

        service = SeriesSync(self.api, pdialog)
        res = service._map_episodes_to_struct(self.api.get_all_series())
        log.debug(res)
        self.assertEqual(2, len(res))