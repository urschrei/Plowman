#! /usr/bin/env python
# coding=utf-8

import unittest
import sys
sys.path.insert(0, '..')

import bookbyline

class BookTests(unittest.TestCase):

    # create Book and DB instance
    @classmethod
    def setUpClass(cls):
        cls._book = bookbyline.BookFromTextFile('test_file.txt', 'It')
        cls._database = bookbyline.DBconn(cls._book.sha, ':memory:')


    # destroy Book and DB instance
    @classmethod
    def tearDownClass(cls):
        del cls._book
        del cls._database


    def setUp(self):
        # provide known correct SHA1 hash of a list of strings
        self.knownValues = ((['a', 'b', 'c', 'd', 'e'],
        '03de6c570bfe24bfc328ccd7ca46b76eadaf4334'),
        )
        # read lines from a test text file
        with open('test_file.txt', 'r') as f:
            self.lines = f.readlines()
        # made-up OAauth values
        self._database.oavals = {}
        self._database.oavals['conkey'] = 'A'
        self._database.oavals['consecret'] = 'B'
        self._database.oavals['acckey'] = 'C'
        self._database.oavals['accsecret'] = 'D'
        # insert some made-up values


    def tearDown(self):
        del self.knownValues
        del self.lines

    def testCreateDatabaseFail(self):
        """ Should create a sqlite3 database in memory, and insert a row
        based on input file hash. Passes if a row is successfully inserted
        """
        self._database.open_connection()
        self._database._insert_values(self._database.oavals)
        self._database.get_row()
        self.assertNotEqual(self._database.row[4],'blah')

    def testBookByLineHashMethod(self):
        """ Should return a SHA1 hash for a given list of strings
        """
        for string, sha_hash in self.knownValues:
            result = bookbyline.get_hash(string)
            self.assertEqual(sha_hash, result)


    def testBookByLineImpFile(self):
        """ Should return a tuple
        """
        result = bookbyline.imp_file(self.lines)
        self.assertTrue(type(result) == tuple)


    def testBookByLineTupleContents(self):
        """ Tuple should contain no blank lines
        """
        result = bookbyline.imp_file(self.lines)
        for r in result:
            self.assertTrue(r != '\n')


    def testBookFileHashIncorrect(self):
        """ Should fail, because the SHA property should be valid
        """
        self.assertNotEqual(self._book.sha, 'abc')


    def testBookFileHashCorrect(self):
        """ Class property should be equal to known correct value
        """
        self.assertEqual(
        self._book.sha,
        'dd5c938011a40a91c49ca9564f3aac40b67c8d27')


if __name__ == "__main__":
    unittest.main()
