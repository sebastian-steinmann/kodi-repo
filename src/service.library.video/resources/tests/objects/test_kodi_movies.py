""" Test features of kodie_movies """

import unittest
import sqlite3
import logging
import sys

from mock import patch

from resources.lib.objects.kodi_movies import KodiMovies

root = logging.getLogger()
root.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)

class TestKodiMovies(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.cursor = self.db.cursor()

        self.artwork_patch = patch('resources.lib.objects.kodi_movies.Artwork')
        self.artwork_patch.start()

        self.xbmc_patch = patch('resources.lib.objects.kodi_movies.xbmc')
        self.xbmc_patch.start()

        self.kodi_movies = KodiMovies(self.cursor)
        self._create_tables()

    def _create_tables(self):
        self.cursor.execute('''
            CREATE TABLE tag (tag_id integer primary key, name TEXT)
        ''')
        self.cursor.execute('''
            CREATE TABLE tag_link (tag_id integer, media_id integer, media_type TEXT)
        ''')
        self.cursor.execute('''
            CREATE TABLE uniqueid (uniqueid_id INTEGER PRIMARY KEY, media_id INTEGER, media_type TEXT, value TEXT, type TEXT)
        ''')
        self.cursor.execute('CREATE TABLE genre ( genre_id integer primary key, name TEXT)')
        self.cursor.execute('CREATE TABLE genre_link (genre_id integer, media_id integer, media_type TEXT)')
        self.cursor.execute('CREATE INDEX ix_genre_link_3 ON genre_link (media_type)')
        self.cursor.execute('CREATE UNIQUE INDEX ix_genre_1 ON genre (name)')
        self.cursor.execute('CREATE UNIQUE INDEX ix_genre_link_1 ON genre_link (genre_id, media_type, media_id)')
        self.cursor.execute('CREATE UNIQUE INDEX ix_genre_link_2 ON genre_link (media_id, media_type, genre_id)')

    def _add_tag(self, tag):
        query = '''
            INSERT INTO tag (name) values (?)
        '''
        self.cursor.execute(query, (tag,))
        return self.cursor.lastrowid

    def _add_taglink(self, tag_id, media_id):
        self.cursor.execute('''
            INSERT INTO tag_link (tag_id, media_id, media_type)
            VALUES (?, ?, 'movie')
        ''', (tag_id, media_id))

    def _add_internal_tags(self, media_id, tags):
        for tag in tags:
            tag_id = self._add_tag(tag)
            self._add_taglink(tag_id, media_id)

    def test_should_add_tags(self):
        remote_tags = ['test', 'test2']
        media_id = 1

        self.kodi_movies.add_tags(media_id, remote_tags)
        res = self.kodi_movies.get_tags(media_id, remote_tags)
        remote_tag_names = [name for _, name, uid, _ in res if uid]
        self.assertItemsEqual(remote_tags, remote_tag_names)

    def test_should_get_tags(self):
        remote_tags = ['test']

        media_id = 1
        self.kodi_movies.add_tags(media_id, remote_tags)

        res = self.kodi_movies.get_tags(media_id, remote_tags)
        res_names = [name for tag_id, name, uid, _ in res]
        self.assertItemsEqual(remote_tags, res_names)

    def test_should_get_external_and_internal_tags(self):
        remote_tags = ['test']
        internal_tags = ['test2']

        media_id = 1
        self.kodi_movies.add_tags(media_id, remote_tags)
        self._add_internal_tags(media_id, internal_tags)

        res = self.kodi_movies.get_tags(media_id, remote_tags)
        res_names = [name for _, name, _, _ in res]
        self.assertItemsEqual(['test', 'test2'], res_names)

        remote_tag_names = [name for _, name, uid, _ in res if uid]
        self.assertItemsEqual(remote_tags, remote_tag_names)

    def test_should_remove_tags(self):
        remote_tags = ['test', 'test2']

        media_id = 1
        self.kodi_movies.add_tags(media_id, remote_tags)

        self.kodi_movies.remove_tag_links(media_id, [2])
        res = self.kodi_movies.get_tags(media_id, remote_tags)
        self.assertEqual(1, len(res))
        self.assertEqual('test', res[0][1])

    def test_should_add_tags_if_exists(self):
        tag_id = self._add_tag('test')
        remote_tags = ['test']
        media_id = 1

        self.kodi_movies.add_tags(media_id, remote_tags)
        res = self.kodi_movies.get_tags(media_id, remote_tags)
        self.assertItemsEqual((tag_id, 'test', 1, tag_id), res[0])

    def test_should_get_existing_tags_from_get(self):
        tag_id = self._add_tag('test')
        remote_tags = ['test']
        media_id = 1

        res = self.kodi_movies.get_tags(media_id, remote_tags)
        self.assertTupleEqual((tag_id, 'test', None, None), res[0])

    def test_should_not_add_genre_with_case(self):
        tag_id = self.kodi_movies._add_genre('test')
        remote_genres = ['Test']
        media_id = 1

        self.kodi_movies.add_genres(media_id, remote_genres)
        res = self.kodi_movies._get_genre("Test")

    def test_should_not_add_genre_with_case2(self):
        self.kodi_movies._add_genre('Test')
        remote_genres = ['Test']
        media_id = 1

        self.kodi_movies.add_genres(media_id, remote_genres)

    def tearDown(self):
        self.cursor.close()
        self.db.close()

        self.artwork_patch.stop()
        self.xbmc_patch.stop()
