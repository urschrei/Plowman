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
- words whose presence at the beginning of a line will cause it to be treated
as a header
- a "live" switch, which will cause the line to be tweeted
- a "verbose" switch, which will cause a full stack trace to be printed if an
error occurs.
The second argument can be given as a single word, or a space-separated list

"""
import sys
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
Please install using e.g. pip, or obtain it from GitHub at \n\
https://github.com/tweepy/tweepy"
    raise

from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.dialects import sqlite
from sqlalchemy import Column, Integer, BigInteger, String
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import DateTime
from sqlalchemy.sql import expression
from sqlalchemy.ext.compiler import compiles
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm.exc import NoResultFound


# SO much boilerplate

BigIntegerType = BigInteger()
BigIntegerType = BigIntegerType.with_variant(sqlite.INTEGER(), 'sqlite')


# create a custom utcnow function
class utcnow(expression.FunctionElement):
    type = DateTime()


@compiles(utcnow, 'sqlite')
def sqlite_utcnow(element, compiler, **kw):
    return "CURRENT_TIMESTAMP"


class AppMixin(object):
    """
    Provide common attributes to our models
    In this case, lowercase table names, timestamp, and a primary key column
    """

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    __mapper_args__ = {'always_refresh': True}

    id = Column(BigIntegerType, primary_key=True)
    # the correct function is automatically selected based on the dialect
    # timestamp = Column(DateTime, server_default=utcnow())

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """
    Emit a PRAGMA statement enforcing foreign-key integrity when an Engine
    instance connects to the DB
    """
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# boilerplate ends

Base = declarative_base()


class Position(Base, AppMixin):
    """stores book details"""
    field_length = 50
    position = Column(Integer)
    displayline = Column(Integer)
    headers = Column(String(field_length))
    digest = Column(String(field_length))
    conkey = Column(String(field_length))
    consecret =  Column(String(field_length))
    acckey = Column(String(field_length))
    accsecret = Column(String(field_length))


def sync(db_name):
    """
    Connect to the DB, return a usable session
    """
    # first, bind to or create the db
    engine = create_engine(
        db_name,
        encoding="utf8")
    # create the tables by syncing metadata from the models
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    return session

# logging stuff
# could also do: LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG,
format='%(asctime)s %(levelname)s %(message)s',
datefmt='%a, %d %b %Y %H:%M:%S',
filename='/var/log/twitter_books.log',
filemode='a')


class MatchError(Exception):
    """ Basic error which is raised if no header line is matched on initial run.
    """

    def __init__(self, detail):
        Exception.__init__(self)
        self.error = detail

    def __str__(self):
        return repr(self.error)


def get_row(sess, digest):
    """ Select a row based on the input file SHA1 hash, or create a new
    entry, and new OAuth credentials
    """
    # try to select the correct row, based on the SHA1 digest
    try:
        row = sess.query(Position).filter_by(digest=digest).one()
    except NoResultFound:
        logging.info(
            "New file found, inserting row.\nSHA1: %s", str(digest))
        oavals = create_oauth(sess, digest)
        row = Position(
            position=0,
            displayline=0,
            headers='',
            digest=digest,
            conkey=oavals.get('conkey'),
            consecret=oavals.get('consecret'),
            acckey=oavals.get('acckey'),
            accsecret=oavals.get('accsecret')
        )
        sess.add(row)
        # try to catch an insertion error here
        sess.commit()
    return row

def create_oauth(sess, digest):
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
Error was: %s" % (digest, err)
        logging.critical(
        "Couldn't complete OAuth setup for %s.\nError was: %s",\
        digest, err)
        sess.rollback()
        sess.flush()
        raise
    return oav

def write_vals(sess, digest, last_l, disp_l, prefix):
    """ Write new line and header values to the db
    """
    sess.query(Position).filter(Position.digest == digest).update({
        'position':last_l,
        'displayline':disp_l,
        'headers':prefix,
        'digest':digest})
    sess.commit()


class BookFromTextFile(object):
    """ Create a book object from a text file.

    Accepts two arguments:
    1. a filename, from which text will be read
    2. a list object used to identify header lines
    A sqlite3 connection object is created, and an attempt is made to
    retrieve a row from a db matching the filename which was
    passed. If no db is found, a new db, table, row and OAuth credentials
    are created.
    """

    def __init__(self, fname = None, hid = None):
        self.headers = hid
        self.database = None
        self.oavals = None
        self.position = None
        self.lines = gimme_lines(fname, open_file, imp_file)
        # try to get hash of returned list
        self.sha = get_hash(self.lines)

    def get_db(self, sess):
        """ Open/create a db, and retrieve/insert a row based on SHA1 hash
        """

        # try to open a db connection
        self.database = sess
        # self.database.get_row()
        self.row = get_row(self.database, self.sha)
        # set instance attrs from the db
        self.position = {
            "lastline": self.row.position,
            "displayline": self.row.displayline,
            "prefix": self.row.headers
            }
        # set OAuth credentials
        self.oavals = {
            "conkey": self.row.conkey,
            "consecret": self.row.consecret,
            "acckey": self.row.acckey,
            "accsecret": self.row.acckey
            }
        # now slice the lines list so we have the next two untweeted lines
        self.lines = itertools.islice(
            self.lines,
            self.row.displayline,
            self.row.displayline + 2,
            None)

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
                cur_line)
            self.position["displayline"] = 1
            # counter skips the next line, since we're tweeting it
            self.position["lastline"] += 2
            self.position["prefix"] = cur_line
            output_line = ('%s\nl. %s: %s') \
            % (
                cur_line.strip(),
                str(self.position["displayline"]),
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
        on what they are, writes the updated file position, line display
        number, and header values to the db. then tweets the resulting string.
        """
        payload = self.format_tweet()
        auth = tweepy.OAuthHandler(self.oavals["conkey"],
        self.oavals["consecret"])
        auth.set_access_token(self.oavals["acckey"], self.oavals["accsecret"])
        api = tweepy.API(auth)
        try:
            if live_tweet == True:
                api.update_status(payload)
            else:
                print payload
        except tweepy.TweepError as err:
            logging.critical("Couldn't update status. Error was: %s" % err.reason)
            raise
        write_vals(
            self.database,
            self.sha,
            self.position["lastline"],
            self.position["displayline"],
            self.position["prefix"])


def open_file(to_read):
    """ Open a text file for reading

        if this module is imported, the command-line parser won't be
        called, so we need this to give us a file object, which is then
        passed to imp_file()
    """
    import codecs
    try:
        with codecs.open(to_read, mode='r', encoding='utf-8') as got_file:
            return imp_file(got_file)
    except IOError:
        logging.critical("Couldn't read from file %s. exiting", to_read)
        raise


def imp_file(list_from_file):
    """ Try to import a text file, strip its blank lines, and return a tuple
    """
    return tuple(line for line in list_from_file if line.strip())


def gimme_lines(fname, not_file, is_file):
    """ Checks to see if fname is a file object

    if it is, it's read into a list
    if it isn't, it's opened for reading first, then read into a list
    """
    if type(fname) != file:
        return not_file(fname)
    else:
        return is_file(fname)


def get_hash(sha_dig):
    """ Derive SHA1 hash of a list
    """
    return hashlib.sha1("".join(sha_dig)).hexdigest()


def main():
    """ Main function, called from command line
    """
    # define command-line arguments
    parser = argparse.ArgumentParser(
    description='Tweet lines of poetry from a text file')
    parser.add_argument("-l", help = "live switch: will tweet the line. \
    Otherwise, it will be printed to stdout", action = "store_true",
    default = False, dest = "live")
    parser.add_argument(
    "-file", metavar = "filename",
    help = "the full path to a text file", required = True,
    type = argparse.FileType("r", 0))
    parser.add_argument(
    "-header", metavar = "header-line word to match",
    help = "a case-sensitive list of words (and punctuation) which will be \
    treated as header lines. Enter as many as you wish, separated by a \
    space. Example - Purgatory: BOOK Passus", nargs = "+",
    required = True)
    parser.add_argument(
    "-v", help = "Print stack trace to stdout",
    action = "store_true", default = False, dest = "errs")


    try:
        fromcl = parser.parse_args()
    except IOError, err:
        print "Can't open the file you specified:"
        print err
        logging.critical(err)
        raise
    location = 'tweet_books.sl3'
    sess = sync('sqlite:///%s' % location)
    input_book = BookFromTextFile(fromcl.file, fromcl.header)
    input_book.get_db(sess)
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
