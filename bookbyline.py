#! /usr/bin/env python
# coding=utf-8
""" 
Tweets lines of poetry from a text file.

This module reads a text file from disk, and tweets properly-
formatted lines from it, one or two lines at a time, depending on
whether it's a header line, or body text.  The line position is stored in
a sqlite3 database, which will be created in the current working directory.
The module takes exactly two arguments: the file name (including path), and
the text to match against in order to designate a header line.  The second
argument can be given as a single word, or a comma-separated list
Requires the Tweepy library: http://github.com/joshthecoder/tweepy

"""
import sys
import sqlite3
import logging
import re
import hashlib
import argparse
import traceback

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
parser = argparse.ArgumentParser\
(description='Tweet lines of poetry from a text file')
parser.add_argument("-l", help = "live switch: will tweet the line. \
Otherwise, it will be printed to stdout", action = "store_true",
default = False, dest = "live")
parser.add_argument("-file", metavar = "filename",
help = "the full path to a text file", required = True,
type = argparse.FileType("r",0))
parser.add_argument("-header", metavar = "header-line word to match",
help = "a case-sensitive list of words (and punctuation) which will be \
treated as header lines. Enter as many as you wish, separated by a \
space. Example - Purgatory: BOOK Passus", nargs = "+",
required = True)
parser.add_argument("-v", help = "Print stack trace to stdout",
action = "store_true", default = False, dest = "errs")
fromcl = parser.parse_args()


class MatchError(Exception):
    """Basic error which is raised if no header line is matched on initial run.
    """
    def __init__(self, detail):
        self.error = detail
    def __str__(self):
        return repr(self.error)

class BookFromTextFile:
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
        # will contain OAuth keys
        self.oavals = {}
        # will contain text file position, line and current prefix values
        self.position = {}
        self.headers = hid
        db_name = "tweet_books.sl3"

        # try to open the specified text file to read, and get its SHA1 digest
        # we're creating the digest from non-blank lines only, just because
        try:
            with fname:
                self.lines = tuple([line for line in fname if line.strip()])
        except IOError:
            logging.critical("Couldn't read from file %s. exiting", fname)
            raise
        self.sha = hashlib.sha1("".join(self.lines)).hexdigest()
        sl_digest = (self.sha,)
        # create a SQLite connection, or create a new db and table
        try:
            self.connection = sqlite3.connect(db_name)
        except IOError:
            logging.critical\
            ("Couldn't read from, or create a db. That's a show-stopper.")
            raise
        with self.connection:
            self.cursor = self.connection.cursor()
            try:
                self.cursor.execute \
                ('SELECT * FROM position WHERE digest = ?',sl_digest)
            except sqlite3.OperationalError:
                logging.info("Couldn't find table \'position\'. Creating…")
                # set up a new blank table
                self.cursor.execute('CREATE TABLE position \
(id INTEGER PRIMARY KEY, position INTEGER, displayline INTEGER, \
header TEXT, digest DOUBLE, conkey TEXT, consecret TEXT, \
acckey TEXT, accsecret TEXT)')
                self.cursor.execute('CREATE UNIQUE INDEX \"digest_idx\" \
on position (digest ASC)')
            # try to select the correct row, based on the SHA1 digest
            row = self.cursor.fetchone()
            if row == None:
                with self.connection:
                    # no rows were returned, insert default values + new digest
                    logging.info\
                    ("New file found, inserting row.\nSHA1: %s", str(self.sha))
                    try:
                        # attempt to create OAuth credentials
                        import getOAuth
                    except ImportError:
                        logging.critical("Couldn't import getOAuth module")
                        raise
                    try:
                        getOAuth.get_creds(self.oavals)
                    except tweepy.TweepError:
                        print "Couldn't complete OAuth setup. Fatal. Exiting."
                        logging.critical\
                        ("Couldn't complete OAuth setup. Unable to continue.")
                        raise
                    try:
                        self.cursor.execute \
                        ('INSERT INTO position VALUES \
                        (null, ?, ?, null, ?, ?, ?, ?, ?)',(0, 0, self.sha,
                        self.oavals["conkey"], self.oavals["consecret"],
                        self.oavals["acckey"], self.oavals["accsecret"]))
                        # and select it
                        self.cursor.execute \
                        ('SELECT * FROM position WHERE digest = ?',sl_digest)
                        row = self.cursor.fetchone()
                    except sqlite3.OperationalError:
                        logging.critical(
                        "Couldn't insert new row into table. Exiting")
                        # close the SQLite connection, and quit
                        raise

        # now slice the lines list so we have the next two untweeted lines
        # right slice index value is ONE LESS THAN THE SPECIFIED NUMBER)
        self.lines = self.lines[row[1]:row[1] + 2]
        # set instance attrs from the db
        self.position = {
            "lastline": row[1],
            "displayline": row[2],
            "prefix": row[3]
            }
        self.oavals = {
            "conkey": row[5],
            "consecret": row[6],
            "acckey": row[7],
            "accsecret": row[8]
            }

    def format_tweet(self):
        """ Properly format an input string based on whether it's a header
        line, or a poetry line.

        If the current line is a header (see self.headers),
        we join the next line and reset the line number to 1.
        Prints a properly-formatted poetry line, including book/canto/line.

        """
        # match against any single member of self.headers
        # re.match should be more efficient
        comped = re.compile("(%s)" % "|".join(self.headers))
        try:
            # If a header word is matched at the beginning of a line
            if comped.match(self.lines[0]):
                logging.info(
                "New header line found on line %s. Content: %s",
                self.position["lastline"], self.lines[0])
                self.position["displayline"] = 1
                # counter skips the next line, since we're tweeting it
                self.position["lastline"] += 2
                self.position["prefix"] = self.lines[0]
                output_line = ('%s\nl. %s: %s') \
                % (self.lines[0].strip(), str(self.position["displayline"]),
                self.lines[1].strip())
                return output_line
        # means we've reached the end of the file
        except IndexError:
            logging.info("%s Reached %s EOF on line %s",
            (str(sys.argv[0]), self.sha, str(self.position["lastline"])))
            raise
        # no header match, so check to see if we're on line 0
        if self.position["lastline"] == 0:
            print """You're running the script for the first time, but none
of your specified header words were matched. Your configuration details have
been saved.\nPlease check the text file and re-run the script. Remember that
headers are case-sensitive.\nThe first line is: \n%sHeader(s):\n%s""" \
            % (self.lines[0], " ".join(self.headers))
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
            self.lines[0].strip())
            return output_line

    def emit_tweet(self, live_tweet):
        """Outputs string as a tweet or as message to stdout.

        First call the format_tweet() function, which correctly formats
        the current object's line[] members, depending
        on what they are, then tweets the resulting string.  It then writes the
        updated file position, line display number, and header values to the
        db.

        """
        payload = self.format_tweet()
        auth = tweepy.OAuthHandler(self.oavals["conkey"],
        self.oavals["consecret"])
        auth.set_access_token(self.oavals["acckey"], self.oavals["accsecret"])
        api = tweepy.API(auth, secure=True)
        # don't print the line unless the db is updateable
        with self.connection:
            try:
                self.cursor.execute('UPDATE position SET position = ?, \
displayline = ?, header = ?, digest = ? WHERE digest = ?',
                (self.position["lastline"], self.position["displayline"],
                self.position["prefix"], self.sha, self.sha))
            except (sqlite3.OperationalError, IndexError):
                logging.error("%s Couldn't update the db") % (str(sys.argv[0]))
                raise
            try:
                if live_tweet == True:
                    api.update_status(payload)
                else:
                    print payload
            except tweepy.TweepError, err:
                logging.error("%s Couldn't update status. Error was: %s") \
                % (str(sys.argv[0]), err)
                raise


def main():
    """ main function.
    """
    input_book = BookFromTextFile(fromcl.file, fromcl.header)
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
