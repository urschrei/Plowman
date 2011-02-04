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
        cls._book = bookbyline.BookFromTextFile('test_file.txt', 'This')
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
        # insert them into the db


    def tearDown(self):
        del self.knownValues
        del self.lines


    def testCreateDB(self):
        """ Should create a sqlite3 database in memory
        """
        self._database.open_connection()
        self.assertTrue(type(self._database.connection), 'sqlite3.Connection')


    def testInsertValuesIntoDB(self):
        """ Should be able to insert rows into the db
            the db digest value should be the same as the book object's
        """
        self._database.open_connection()
        self._database._insert_values(self._database.oavals)
        self._database.get_row()
        self.assertEqual(self._database.row[4],self._book.sha)


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


    #def testBookGetDB(self):
    #    """ Should return expected DB values
    #    """



if __name__ == "__main__":
    unittest.main()
