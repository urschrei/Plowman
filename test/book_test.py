#! /usr/bin/env python
# coding=utf-8
"""
Tests for the bookbyline module
"""

import unittest
import sys
sys.path.insert(0, '..')

import bookbyline
# import sync
from bookbyline import Position

class BookTests(unittest.TestCase):

    def setUp(self):
        """ Set up known good values with which to test
        """
        self.book = bookbyline.BookFromTextFile('test_file.txt', 'This')
        self.database = bookbyline.sync('sqlite:///')
        self.digest = u'dd5c938011a40a91c49ca9564f3aac40b67c8d27'
        # provide known correct SHA1 hash of a list of strings
        self.knownValues = (
            (['a', 'b', 'c', 'd', 'e'],
            '03de6c570bfe24bfc328ccd7ca46b76eadaf4334'),
        )
        # read lines from a test text file
        with open('test_file.txt', 'r') as f:
            self.lines = f.readlines()
        # made-up OAauth values
        oavals = {}
        oavals['conkey'] = 'A'
        oavals['consecret'] = 'B'
        oavals['acckey'] = 'C'
        oavals['accsecret'] = 'D'

        # populate db
        row = Position(
            position=0,
            displayline=0,
            headers='',
            digest=self.digest,
            conkey=oavals.get('conkey'),
            consecret=oavals.get('consecret'),
            acckey=oavals.get('acckey'),
            accsecret=oavals.get('accsecret')
        )
        self.database.add(row)
        self.database.commit()
        self.live = False
        self.book.get_db(self.database)

    def tearDown(self):
        """ Empty the database table and remove old known values when each
        test ends
        """
        # ensure we remove all objects and properties after each test
        del self.book
        del self.database
        del self.knownValues
        del self.lines
        del self.live

    def testDatabaseConnectionExists(self):
        """ Should return a valid sqlite3 connection object
        """
        self.assertTrue(type(self.database.connection), 'sqlite3.Connection')

    def testInsertValuesIntoDatabase(self):
        """ Should be able to insert rows into the db, and retrieve them
            the db digest value should be the same as the book object's
        """
        bookbyline.get_row(self.database, self.digest)
        self.assertEqual(self.book.row.digest, self.book.sha)

    def testFormatTweet(self):
        """ Will pass if the output var begins with 'This',
        which is the first word of the first line in the test text file,
        and contains the first two words of the second line
        """
        self.book.get_db(self.database)
        output = self.book.format_tweet()
        self.assertTrue(output.startswith('This'))
        self.assertTrue(output.find('It has') > -1)

    def testEmitHeaderTweet(self):
        """ Should pass if the lastline dict entry is 2
            which means that the first two lines of the file have been tweeted
        """
        self.book.get_db(self.database)
        self.book.emit_tweet(self.live)
        self.assertEqual(self.book.position['lastline'], 2)

    def testEmitNormalTweet(self):
        """ Should pass if the lastline dict entry is 3
            which means that the first two lines of the file have been tweeted
            and no header is matched when we call emit_tweet
        """
        self.book.get_db(self.database)
        self.book.position['lastline'] = 2
        new_headers = ['foo', 'bar']
        self.book.headers = new_headers
        self.book.emit_tweet(self.live)
        self.assertEqual(self.book.position['lastline'], 3)

    def testEmitWrongHeader(self):
        """ Should fail, because the headers don't match the text file
        """
        self.book.get_db(self.database)
        new_headers = ['foo', 'bar']
        self.book.headers = new_headers
        with self.assertRaises(bookbyline.MatchError):
            self.book.emit_tweet(self.live)

    def testReachedEndOfFile(self):
        """ Should fail because we've reached the end of the file.
            We're faking this test by emitting a tweet, which iterates to the
            end of the islice object. This is functionally identical to storing
            the final line of the text file in 'lastline', then calling next()
            on the resulting slice
        """
        self.book.get_db(self.database)
        self.book.emit_tweet(self.live)
        with self.assertRaises(StopIteration):
            self.book.emit_tweet(self.live)

    def testWriteValuesToDatabase(self):
        """ Will pass if we successfully write updated values to the db
        """
        bookbyline.write_vals(self.database, self.digest, 33, 45, 'New Header')
        r = self.database.query(Position).all()[0]
        self.assertEqual(r.position, 33)
        self.assertEqual(r.displayline, 45)
        self.assertEqual(r.headers,'New Header')

    def testCreateDatabaseConnectionFromBook(self):
        """ Ensure that values are returned from db to book object
        """
        self.book.get_db(self.database)
        self.assertEqual(self.book.oavals['conkey'], 'A')
        self.assertTrue(type(self.book.lines), 'itertools.islice object')

    def testBookByLineHashMethod(self):
        """ Should return a SHA1 hash for a given list of strings
        """
        for string, sha_hash in self.knownValues:
            result = bookbyline.get_hash(string)
            self.assertEqual(sha_hash, result)

    def testGimmeLinesFromFile(self):
        """ Test that gimme_lines works on closed files
        """
        lines = bookbyline.gimme_lines(
        'test_file.txt',
        bookbyline.open_file,
        bookbyline.imp_file
        )
        self.assertTrue(type(lines) == tuple)

    def testGimmeLinesFromFileObject(self):
        """ Test that gimme_lines works on opened file objects
        """
        self.f = open('test_file.txt', 'r')
        lines = bookbyline.gimme_lines(
        self.f,
        bookbyline.open_file,
        bookbyline.imp_file
        )
        self.assertTrue(type(lines) == tuple)

    def testGimmeLinesFromFileFailure(self):
        """ Gimme_lines should raise an error if it tries to open
            a nonexistent file
        """
        with self.assertRaises(IOError):
            lines = bookbyline.gimme_lines(
            'not_a_file.txt',
            bookbyline.open_file,
            bookbyline.imp_file
            )

    def testBookByLineTupleContents(self):
        """ Tuple should contain no blank lines
        """
        result = bookbyline.imp_file(self.lines)
        for r in result:
            self.assertTrue(r != '\n')

    def testBookFileHashIncorrect(self):
        """ Should fail, because the SHA property should be valid
        """
        self.assertNotEqual(self.book.sha, 'abc')

    def testBookFileHashCorrect(self):
        """ Class property should be equal to known correct SHA value
            of test_file.txt
        """
        self.assertEqual(
        self.book.sha,
        'dd5c938011a40a91c49ca9564f3aac40b67c8d27')

if __name__ == "__main__":
    unittest.main()
