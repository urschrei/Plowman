#! /usr/bin/env python
# coding=utf-8
"""
Tests for the bookbyline module
"""

import unittest
import sys
sys.path.insert(0, '..')

import bookbyline

class BookTests(unittest.TestCase):


    def setUp(self):
        """ set up known good values with which to test
        """
        self.book = bookbyline.BookFromTextFile('test_file.txt', 'This')
        self.database = bookbyline.DBconn(self.book.sha, ':memory:')
        # provide known correct SHA1 hash of a list of strings
        self.knownValues = ((['a', 'b', 'c', 'd', 'e'],
        '03de6c570bfe24bfc328ccd7ca46b76eadaf4334'),
        )
        # read lines from a test text file
        with open('test_file.txt', 'r') as f:
            self.lines = f.readlines()
        # made-up OAauth values
        self.database.oavals = {}
        self.database.oavals['conkey'] = 'A'
        self.database.oavals['consecret'] = 'B'
        self.database.oavals['acckey'] = 'C'
        self.database.oavals['accsecret'] = 'D'


    def tearDown(self):
        """ empty the database table and remove old known values when each
        test ends
        """
        # ensure we have a clean position table prior to each test
        del self.book
        del self.database
        del self.knownValues
        del self.lines


    def testDatabaseConnectionExists(self):
        """ should return a valid sqlite3 connection object
        """
        self.assertTrue(type(self.database.connection), 'sqlite3.Connection')


    def testInsertValuesIntoDatabase(self):
        """ should be able to insert rows into the db, and retrieve them
            the db digest value should be the same as the book object's
        """
        self.database._insert_values(self.database.oavals)
        self.database.get_row()
        self.assertEqual(self.database.row[4], self.book.sha)


    def testFormatTweet(self):
        """ will pass if the output var begins with 'This',
        which is the first word of the first line in the test text file,
        and contains the first two words of the second line
        """
        self.database._insert_values(self.database.oavals)
        self.book.get_db(self.database)
        output = self.book.format_tweet()
        self.assertTrue(output.startswith('This'))
        self.assertTrue(output.find('It has') > -1)


    def testEmitHeaderTweet(self):
        """ should pass if the lastline dict entry is 2
            which means that the first two lines of the file have been tweeted
        """
        self.database._insert_values(self.database.oavals)
        self.book.get_db(self.database)
        self.live = False
        self.book.emit_tweet(self.live)
        self.assertEqual(self.book.position['lastline'], 2)


    def testEmitNormalTweet(self):
        """ should pass if the lastline dict entry is 3
            which means that the first two lines of the file have been tweeted
            and no header is matched when we call emit_tweet
        """
        self.live = False
        self.database._insert_values(self.database.oavals)
        self.book.get_db(self.database)
        self.book.position['lastline'] = 2
        new_headers = ['foo', 'bar']
        self.book.headers = new_headers
        self.book.emit_tweet(self.live)
        self.assertEqual(self.book.position['lastline'], 3)


    def testEmitWrongHeader(self):
        """ should fail, because the headers don't match the text file
        """
        self.live = False
        self.database._insert_values(self.database.oavals)
        self.book.get_db(self.database)
        new_headers = ['foo', 'bar']
        self.book.headers = new_headers
        with self.assertRaises(bookbyline.MatchError):
            self.book.emit_tweet(self.live)


    def testWriteValuesToDatabase(self):
        """ will pass if we successfully write updated values to the db
        """
        self.database._insert_values(self.database.oavals)
        self.database.write_vals(33, 45, 'New Header')
        self.database.cursor.execute(
        'SELECT * FROM position'
        )
        r = self.database.cursor.fetchone()
        self.assertEqual(r[1],33)
        self.assertEqual(r[2],45)
        self.assertEqual(r[3],'New Header')


    def testCreateDatabaseConnectionFromBook(self):
        """ ensure that values are returned from db to book object
        """
        self.database._insert_values(self.database.oavals)
        self.book.get_db(self.database)
        self.assertEqual(self.book.oavals['conkey'], 'A')
        self.assertTrue(type(self.book.lines), 'itertools.islice object')


    def testBookByLineHashMethod(self):
        """ should return a SHA1 hash for a given list of strings
        """
        for string, sha_hash in self.knownValues:
            result = bookbyline.get_hash(string)
            self.assertEqual(sha_hash, result)


    def testGimmeLinesFromFile(self):
        """ test that gimme_lines works on closed files
        """
        lines = bookbyline.gimme_lines(
        'test_file.txt',
        bookbyline.open_file,
        bookbyline.imp_file
        )
        self.assertTrue(type(lines) == tuple)


    def testGimmeLinesFromFileObject(self):
        """ test that gimme_lines works on opened file objects
        """
        self.f = open('test_file.txt', 'r')
        lines = bookbyline.gimme_lines(
        self.f,
        bookbyline.open_file,
        bookbyline.imp_file
        )
        self.assertTrue(type(lines) == tuple)


    def testGimmeLinesFromFileFailure(self):
        """ gimme_lines should raise an error if it tries to open
            a nonexistent file
        """
        with self.assertRaises(IOError):
            lines = bookbyline.gimme_lines(
            'not_a_file.txt',
            bookbyline.open_file,
            bookbyline.imp_file
            )


    def testBookByLineTupleContents(self):
        """ tuple should contain no blank lines
        """
        result = bookbyline.imp_file(self.lines)
        for r in result:
            self.assertTrue(r != '\n')


    def testBookFileHashIncorrect(self):
        """ should fail, because the SHA property should be valid
        """
        self.assertNotEqual(self.book.sha, 'abc')


    def testBookFileHashCorrect(self):
        """ class property should be equal to known correct SHA value
            of test_file.txt
        """
        self.assertEqual(
        self.book.sha,
        'dd5c938011a40a91c49ca9564f3aac40b67c8d27')


if __name__ == "__main__":
    unittest.main()
