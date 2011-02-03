#! /usr/bin/env python
# coding=utf-8

import unittest
import sys
sys.path.insert(0, '..')

import bookbyline

class BookTests(unittest.TestCase):

    # provide known correct SHA1 hash of a list of strings
    knownValues = ((['a', 'b', 'c', 'd', 'e'],
    '03de6c570bfe24bfc328ccd7ca46b76eadaf4334'),
    )
    # read lines from a test text file
    with open('test_file.txt', 'r') as f:
        lines = f.readlines()


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






if __name__ == "__main__":
    unittest.main()