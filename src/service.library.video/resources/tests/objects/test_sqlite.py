""" Test features of sqllite """

import unittest
import sqlite3

class TestSqlite(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect("test.db", isolation_level=None)
        self.cursor = self.db.cursor()

    def test_should_record_change(self):
        ''' Check if coalesce works without commit '''
        # Create table
        self.cursor.execute('''
            create table test (id INTEGER PRIMARY KEY, message text)
        ''')

        self.cursor.execute('''
            insert into test (message) values (?)
        ''', ('test',))

        lri = self.cursor.lastrowid
        self.assertEqual(1, lri)

        self.cursor.execute('''
            insert into test (message) values (?)
        ''', ('test2',))

        lri = self.cursor.lastrowid
        self.assertEqual(2, lri)

    def test_add_and_read_data(self):
        # Create table
        self.cursor.execute('''
            create table test (idTest INTEGER PRIMARY KEY, message text)
        ''')

        self.cursor.execute('''
            select coalesce(max(idTest),0) from test
        ''')
        lastid = self.cursor.fetchone()[0]
        self.assertEqual(0, lastid)

        self.cursor.execute('''
            insert into test (idTest, message) values (?, ?)
        ''', (lastid + 1, 'test',))

        self.cursor.execute('''
            select * from test
        ''')

        res = self.cursor.fetchone()
        self.assertEqual((1, u'test'), res)

        self.cursor.execute('''
            select coalesce(max(idTest),0) from test
        ''')
        lastid = self.cursor.fetchone()[0]
        self.assertEqual(1, lastid)

        self.cursor.execute('''
            insert into test (idTest, message) values (?, ?)
        ''', (lastid + 1, 'test2',))

        self.cursor.execute('''
            select coalesce(max(idTest),0) from test
        ''')
        lastid = self.cursor.fetchone()[0]
        self.assertEqual(2, lastid)


    def tearDown(self):
        self.cursor.execute('drop table test')
        self.cursor.close()
        self.db.close()
