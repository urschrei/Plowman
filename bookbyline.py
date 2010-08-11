#!/usr/bin/env python
# coding=utf-8
""" 
This module reads a text file from disk, and tweets properly-
formatted lines from it, one or two lines at a time, depending on
whether it's a header line, or body text. The line position is stored in
a sqlite3 database, which will be created in the current working directory.
The module takes exactly two arguments: the file name (including path), and
the text to match against in order to designate a header line. The second
argument can be given as a single word, or a comma-separated list

Requires the Tweepy library: http://github.com/joshthecoder/tweepy
"""
import sys
import hashlib
import sqlite3
import datetime
import logging
import re

# logging stuff
log_filename = '/var/log/twitter_books.log'
logging.basicConfig(filename=log_filename, level=logging.ERROR)
now = datetime.datetime.now()

# tweepy stuff
import tweepy
auth = tweepy.BasicAuthHandler('user', 'pass')
api = tweepy.API(auth, secure="True")

if len(sys.argv) != 3:
	print "Incorrect number of arguments. Please call the script like this: \
	bookbyline.py filename.txt header"
	logging.error(now.strftime("%Y-%m-%d %H:%M") + " %s " +  \
	+ " Incorrect number of arguments") % (str(sys.argv[0]))
	sys.exit()

class BookFromTextFile:
	""" Create a Book object from a text file. Takes two arguments:
	1. a filename, from which text will be read
	2. a string used to identify header lines
	A sqlite3 connection object is created, and an attempt is made to
	retrieve a row matching from a db matching the filename which was
	passed. If no db is found, a new db is created and a table containing 
	default values is inserted.
	"""
	def __init__(self, fname = None, hid = None):
		self.name = fname
		self.headers = hid.split(",")
		self.db_name = "tweet_books.sl3"
		
		# try to open the specified text file to read, and get its SHA1 digest
		# we're creating the digest from non-blank lines only, just because
		self.lines = list()
		try:
			with open(self.name, "r") as t_file:
				get_lines = t_file.readlines()
		except IOError:
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " Couldn't open text file for reading.")
			sys.exit()
		self.lines = [l for l in get_lines if l.strip()]
		self.sha = hashlib.sha1("".join(self.lines)).hexdigest()
		sl_digest = (self.sha,)
		
		# create a SQLite connection, or create a new db and table
		try:
			self.connection = sqlite3.connect(self.db_name)
		except IOError:
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " Couldn't read from, or create a db. That's a show-stopper.")
			sys.exit()
		self.cursor = self.connection.cursor()
		try:
			self.cursor.execute \
			('SELECT * FROM position WHERE digest = ?',sl_digest)
		except sqlite3.OperationalError:
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " Couldn't find table \'position\'. Creating…")
			# set up a new blank table
			self.cursor.execute('CREATE TABLE position \
			(id INTEGER PRIMARY KEY, position INTEGER, displayline INTEGER, \
			header STRING, digest DOUBLE)')
		
		# try to select the correct row, based on the SHA1 digest
		row = self.cursor.fetchone()
		if row == None:
			# no rows were returned, so insert default values with new digest
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " New file found, inserting row. Digest:\n" + str(self.sha)) 
			try:
				self.cursor.execute \
				('INSERT INTO position VALUES \
				(null, ?, ?, null, ?)',(0, 0, self.sha))
				# and select it
				self.cursor.execute \
				('SELECT * FROM position WHERE digest = ?',sl_digest)
				row = self.cursor.fetchone()
			except sqlite3.OperationalError:
				logging.error(now.strftime("%Y-%m-%d %H:%M") \
				+ " Couldn't insert new row into db. Exiting")
				# close the SQLite connection, and quit
				self.connection.commit()
				self.connection.close()
				sys.exit()
		# set instance attrs from the db
		self.db_lastline = row[1]
		self.displayline = row[2]
		self.prefix = row[3]
		# now slice the lines list so we have the next two untweeted lines
		# right slice index value is ONE LESS THAN THE SPECIFIED NUMBER)
		self.lines = self.lines[self.db_lastline:self.db_lastline + 2]
		
	def format_tweet(self):
		""" Properly format an input string based on whether it's a header
		line, or a poetry line. If the current line is a header
		(see self.headers),
		we join the next line and reset the line number to 0.
		This means the line numbers don't jump when a
		header is encountered, as the offset is subtracted from the display
		line.
		Prints a properly-formatted poetry line, including book/canto/line.
		"""
		# match against any single member of self.headers
		comped = re.compile("^(" + "|".join(self.headers) + ")")
		if comped.search(self.lines[0]):
			try:
				self.displayline = 1
				# counter skips the next line, since we're tweeting it
				self.db_lastline += 2
				self.prefix = self.lines[0]
				output_line = ('%s\nl. %s: %s') \
				% (self.lines[0].strip(), str(self.displayline), \
				self.lines[1].strip())
				self.lines.append(output_line)
				return self.lines
			# means we've reached the end of the file
			except IndexError:
				logging.error(now.strftime("%Y-%m-%d %H:%M") + " " + \
				str(sys.argv[0]) + " " + "Reached " + self.name \
				+ " EOF on line " + str(self.db_lastline))
				sys.exit()
		# proceed by using the latest untweeted line
		self.displayline += 1
		# move counter to the next line
		self.db_lastline += 1
		output_line = ('%sl. %s: %s') \
		% (self.prefix, self.displayline, self.lines[0].strip())
		self.lines.append(output_line)
		return self.lines
		
	def emit_tweet(self):
		""" First call the format_tweet() function, which correctly formats
		the current object's line[] properties, depending
		on what they are, then tweets them. It then writes the
		updated position, line display offset, and header values to the db.
		Appends the correctly-formatted line to the line[] list, so it can
		be tweeted
		"""
		self.format_tweet()
		# don't print the line unless the db is updateable
		with self.connection:
			try:
				self.cursor.execute('UPDATE position SET position = ?,\
				displayline = ?, header = ?, digest = ? WHERE digest = ?', \
				(self.db_lastline, self.displayline, self.prefix, \
				self.sha, self.sha))
			except (sqlite3.OperationalError, IndexError):
				print "Wasn't able to update the db."
				logging.error(now.strftime("%Y-%m-%d %H:%M") + " " + \
				str(sys.argv[0]) + " " + "Couldn't update the db")
			try:
				#api.update_status(str(self.lines[-1]))
				print self.lines[-1]
			except tweepy.TweepError, err:
				logging.error(now.strftime("%Y-%m-%d %H:%M") + 
				"%s Couldn't update status. Error was: %s") \
				% (str(sys.argv[0]), err)
				#self.connection.rollback()
				sys.exit()
		self.connection.close()


def main():
	""" main function
	"""
	# first argument (argv[0]) is the abs. path + filename -- not what we want
	input_book = BookFromTextFile(sys.argv[1], sys.argv[2])
	input_book.emit_tweet()

if __name__ == '__main__':
	main()

