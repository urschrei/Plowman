#! /usr/bin/env python
# coding=utf-8

import bookbyline
import unittest

class KnownValues(unittest.TestCase):
    knownValues = ((['a', 'b', 'c', 'd', 'e'], '03de6c570bfe24bfc328ccd7ca46b76eadaf4334'),
    )


    def testBookByLineKnownValues(self):
        """ get_hash should give known result with known input
        """
        for string, sha_hash in self.knownValues
            result = bookbyline.get_hash(string)
            self.assertEqual(sha_hash, result)







if __name__ == "__main__":
    unittest.main()