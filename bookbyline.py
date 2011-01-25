#! /usr/bin/env python
# coding=utf-8
""" 
Tweets lines of poetry from a text file.

This module reads a text file from disk, and tweets properly-
formatted lines from it, one or two lines at a time, depending on
whether it's a header line, or body text.  The line position is stored in
a sqlite3 database, which will be created in the current working directory.
The module takes a number of arguments: 
- the file name (including path)
- words whose presence at the beginning of a line will cause it to be treated as
a header
- a "live" switch, which will cause the line to be tweeted
- a "verbose" switch, which will cause a full stack trace to be printed if an
error occurs.
The second argument can be given as a single word, or a space-separated list
Requires the Tweepy library: http://github.com/joshthecoder/tweepy

"""
import sys
import sqlite3
import logging
import re
import hashlib
import argparse
import traceback
import itertools

try:
    import tweepy
except ImportError:
    print "The tweepy module could not be found.\n\
Please install using easy_install, or obtain it from GitHub at \n\
http://github.com/joshthecoder/tweepy"
    sys.exit()


# logging stuff
logging.basicConfig(level=logging.DEBUG,
format='%(asctime)s %(levelname)s %(message)s',
datefmt='%a, %d %b %Y %H:%M:%S',
filename='/var/log/twitter_books.log',
filemode='a')


# define command-line arguments
parser = argparse.ArgumentParser(
description='Tweet lines of poetry from a text file')
parser.add_argument("-l", help = "live switch: will tweet the line. \
Otherwise, it will be printed to stdout", action = "store_true",
default = False, dest = "live")
parser.add_argument(
"-file", metavar = "filename",
help = "the full path to a text file", required = True,
type = argparse.FileType("r",0))
parser.add_argument(
"-header", metavar = "header-line word to match",
help = "a case-sensitive list of words (and punctuation) which will be \
treated as header lines. Enter as many as you wish, separated by a \
space. Example - Purgatory: BOOK Passus", nargs = "+",
required = True)
parser.add_argument(
"-v", help = "Print stack trace to stdout",
action = "store_true", default = False, dest = "errs")


class MatchError(Exception):
    """ Basic error which is raised if no header line is matched on initial run.
    """
    def __init__(self, detail):
        Exception.__init__(self)
        self.error = detail
    def __str__(self):
        return repr(self.error)



class DBconn(object):
    """ Create a SQLite connection, or create a new db and table
    """
    def __init__(self, digest = None, loc = 'tweet_books.sl3'):
        # create a tuple for db insertion
        # NB do not use this value if you're explicitly specifying tuples
        # see the insert statement, for instance
        self.book_digest = digest
        self.db_name = loc
        self.schema = 'CREATE TABLE position \
(id INTEGER PRIMARY KEY, position INTEGER, displayline INTEGER, \
header TEXT, digest TEXT, conkey TEXT, consecret TEXT, \
acckey TEXT, accsecret TEXT)'
        self.connection = None
        self.cursor = None
        self.row = None


    def open_connection(self):
        """ Open a db connection, or create a new db
        """
        try:
            self.connection = sqlite3.connect(self.db_name)
        except IOError:
            logging.critical(
            "Couldn't read from, or create a db. That's a show-stopper."
            )
            raise
        with self.connection:
            self.cursor = self.connection.cursor()
            try:
                self.cursor.execute(
                'SELECT * FROM position WHERE digest = ?', (self.book_digest,)
                )
            except sqlite3.OperationalError:
                logging.info(
                "Couldn't find table \'position\'. Creating…"
                )
                # set up a new blank table and index
                idx = 'CREATE UNIQUE INDEX \"digest_idx\" \
on position (digest ASC)'
                self.cursor.execute(self.schema)
                self.cursor.execute(idx)


    def get_row(self):
        """ Select a row based on the input file SHA1 hash, or create a new
        entry, and new OAuth credentials
        """
        # try to select the correct row, based on the SHA1 digest
        self.row = self.cursor.fetchone()
        if self.row == None:
            with self.connection:
                # no rows were returned, insert default values + new digest
                logging.info(
"New file found, inserting row.\nSHA1: %s", str(self.book_digest)
                    )
                try:
                    oavals = self._create_oauth()
                except sqlite3.OperationalError:
                    logging.critical(
                    "Couldn't insert new row into table. Exiting")
                    # close the SQLite connection, and quit
                    raise
                self.cursor.execute \
                ('INSERT INTO position VALUES \
                (null, ?, ?, null, ?, ?, ?, ?, ?)',(0, 0, self.book_digest,
                oavals["conkey"], oavals["consecret"],
                oavals["acckey"], oavals["accsecret"]))
                # and select it
                self.cursor.execute \
                ('SELECT * FROM position WHERE digest = ?', (self.book_digest,))
                self.row = self.cursor.fetchone()


    def _create_oauth(self):
        """ Obtain OAuth creds from Twitter, using the Tweepy lib
        """
        try:
            # attempt to create OAuth credentials
            import getOAuth
        except ImportError:
            logging.critical("Couldn't import getOAuth module")
            raise
        try:
            oav = {}
            getOAuth.get_creds(oav)
        except tweepy.TweepError, err:
            print "Couldn't complete OAuth setup for %s. Fatal. Exiting.\n\
Error was: %s" % (self.book_digest, err)
            logging.critical(
            "Couldn't complete OAuth setup for %s.\nError was: %s",\
            self.book_digest, err
            )
            # not much point in writing anything to the db in this case
            self.connection.rollback()
            raise
        return oav


    def write_vals(self, last_l, disp_l, prefix):
        """ Write new line and header values to the db
        """
        with self.connection:
            try:
                self.cursor.execute(
                'UPDATE position SET position = ?,\
displayline = ?, header = ?, digest = ? WHERE digest = ?',
                (last_l, disp_l, prefix, self.book_digest, self.book_digest))
            except (sqlite3.OperationalError, IndexError):
                logging.error("%s Couldn't update the db") % (str(sys.argv[0]))
                raise



class BookFromTextFile(object):
    """ Create a book object from a text file.

    Accepts two arguments:
    1. a filename, from which text will be read
    2. a list object used to identify header lines
    A sqlite3 connection object is created, and an attempt is made to
    retrieve a row from a db matching the filename which was
    passed.  If no db is found, a new db, table, row and OAuth credentials
    are created.
    """
    def __init__(self, fname = None, hid = None):
        self.headers = hid
        self.database = None
        self.oavals = None
        self.position = None
        # try to read the specified text file
        self.lines = imp_file(fname)
        # try to get hash of returned list
        self.sha = get_hash(self.lines)


    def open_connection(self):
        """ Open/create a db, and retrieve/insert a row based on SHA1 hash
        """
        # try to open a db connection
        self.database = DBconn(self.sha)
        self.database.open_connection()
        self.database.get_row()
        # set instance attrs from the db
        self.position = {
            "lastline": self.database.row[1],
            "displayline": self.database.row[2],
            "prefix": self.database.row[3]
            }
        # set OAuth credentials
        self.oavals = {
            "conkey": self.database.row[5],
            "consecret": self.database.row[6],
            "acckey": self.database.row[7],
            "accsecret": self.database.row[8]
            }
        # now slice the lines list so we have the next two untweeted lines
        self.lines = itertools.islice(
        self.lines,
        self.database.row[1],
        self.database.row[1] + 2,
        None
        )


    def format_tweet(self):
        """ Properly format an input string depending on whether it's a header
        line, or a poetry line.

        If the current line is a header (see self.headers),
        we join the next line and reset the line number to 1.
        Prints a properly-formatted poetry line, including book/canto/line.
        """
        # match against any single member of self.headers
        # re.match should be more efficient
        try:
            cur_line = next(self.lines)
        # means we've reached the end of the file
        except StopIteration:
            logging.info("Reached %s EOF on line %s", self.sha,
            self.position["lastline"] - 1)
            raise
        comped = re.compile("(%s)" % "|".join(self.headers))
        # If a header word is matched at the beginning of a line
        if comped.match(cur_line):
            logging.info(
            "New header line found on line %s. Content: %s",
            self.position["lastline"] + 1,
            cur_line
            )
            self.position["displayline"] = 1
            # counter skips the next line, since we're tweeting it
            self.position["lastline"] += 2
            self.position["prefix"] = cur_line
            output_line = ('%s\nl. %s: %s') \
            % (cur_line.strip(), str(self.position["displayline"]),
            next(self.lines).strip())
            return output_line
        # no header match, so check to see if we're on line 0
        if self.position["lastline"] == 0:
            print """You're running the script for the first time, but none
of your specified header words were matched. Your configuration details have
been saved.\nPlease check the text file and re-run the script. Remember that
headers are case-sensitive.\nThe first line is: \n%sYou specified the \
following header(s):\n%s""" \
            % (cur_line, " ".join(self.headers))
            logging.error("Didn't match header lines on first run, not \
printing anything.")
            raise MatchError("No header match on initial run")
        # we didn't match a header, and aren't on line 0, so continue
        else:
            self.position["displayline"] += 1
            # move counter to the next line
            self.position["lastline"] += 1
            output_line = ('%sl. %s: %s') \
            % (self.position["prefix"], self.position["displayline"], \
            cur_line.strip())
            return output_line


    def emit_tweet(self, live_tweet):
        """ Outputs string as a tweet or as message to stdout.

        Calls the format_tweet() function, which correctly formats
        the current object's line[] members, depending
        on what they are, writes the updated file position, line display number,
        and header values to the db. then tweets the resulting string.
        """
        payload = self.format_tweet()
        auth = tweepy.OAuthHandler(self.oavals["conkey"],
        self.oavals["consecret"])
        auth.set_access_token(self.oavals["acckey"], self.oavals["accsecret"])
        api = tweepy.API(auth, secure = True)
        try:
            if live_tweet == True:
                api.update_status(payload)
            else:
                print payload
        except tweepy.TweepError, err:
            logging.critical("Couldn't update status. Error was: %s", err)
            raise
        self.database.write_vals(
            self.position["lastline"],
            self.position["displayline"],
            self.position["prefix"]
            )



def imp_file(list_from_file):
    """ Try to import a text file, strip blank lines, format as a list
    """
    try:
        return tuple(line for line in list_from_file if line.strip())
    except IOError:
        logging.critical("Couldn't read from file %s. exiting", list_from_file)


def get_hash(sha_dig):
    """ Derive SHA1 hash of a list
    """
    return hashlib.sha1("".join(sha_dig)).hexdigest()


def main():
    """ Main function.
    """
    fromcl = parser.parse_args()
    input_book = BookFromTextFile(fromcl.file, fromcl.header)
    input_book.open_connection()
    input_book.emit_tweet(fromcl.live)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        # actually raise these so it exits cleanly
        raise
    except Exception, error:
        # all other exceptions, so display the error
        if fromcl.errs == True:
            print "Stack trace:\n", traceback.print_exc(file = sys.stdout)
        else:
            pass
    else:
        pass
    finally:
        # exit cleanly once we've done everything else
        sys.exit(0)
