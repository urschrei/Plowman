#!/usr/bin/env python
# coding=utf-8
""" 
This module reads a text file from disk, and tweets properly-
formatted lines from it, one or two lines at a time, depending on
whether it's a header line, or body text. The line position is stored in
a sqlite3 database, in the same directory as the text file.
The module takes exactly two arguments: the file name (including path), and
the text to match against in order to designate a header line. The second
argument can be given as a single word, or a comma-separated list

Requires the Tweepy library: http://github.com/joshthecoder/tweepy
"""
import sys
import sqlite3
import datetime
import logging
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
	logging.error(now.strftime("%Y-%m-%d %H:%M") + " " + str(sys.argv[0]) \
	+ " " + "Incorrect number of arguments")
	sys.exit()

class BookFromTextFile:
	""" Create a Book object from a text file. Takes two arguments:
	1. a filename, from which text will be read
	2. a string used to identify header lines
	A sqlite3 connection object is created, and an attempt it made to
	retrieve a row matching from a db matching the filename which was
	passed. If no db is found, a new db is created and a table containing 
	default values is inserted.
	"""
	def __init__(self, fname = None, hid = None):
		self.name = fname
		self.headers = hid.split(",")
		spt = self.name.split(".")
		self.db_name = str(spt[0]) + ".db"
		
		# try to open the specified text file for reading
		self.lines = list()
		try:
			with open(self.name, "r") as t_file:
				for a_line in t_file:
					if not a_line.strip():
						continue
						# if we encounter a blank line, skip it, and carry on
					else:
						self.lines.append(a_line)
		except IOError:
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " Couldn't open text file for reading.")
			sys.exit()
			
		# create a SQLite connection, or create a new db and table
		try:
			self.connection = sqlite3.connect(self.db_name)
		except IOError:
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " Couldn't read from, or create a db. That's a show-stopper.")
			sys.exit()
		self.cursor = self.connection.cursor()
		try:
			self.cursor.execute('SELECT * FROM position ORDER BY POSITION \
			DESC LIMIT 1')
		except sqlite3.OperationalError:
			logging.error(now.strftime("%Y-%m-%d %H:%M") \
			+ " Couldn't find the specified table. Creating…")
			# set up a new blank table
			self.cursor.execute('CREATE TABLE position (id 
			INTEGER PRIMARY KEY, position INTEGER, displayline INTEGER,
			header STRING)')
			self.cursor.execute('INSERT INTO position VALUES (null, ?, ?, ?)' \
			,(0, 0, ""))
			self.cursor.commit()
			try:
				self.cursor.execute('SELECT * FROM position ORDER BY POSITION \
				DESC LIMIT 1')
			except sqlite3.OperationalError:
				logging.error(now.strftime("%Y-%m-%d %H:%M") \
				+ "Still couldn't execute query. Insert statement problem?")
				# close the SQLite connection, and quit
				self.connection.commit()
				self.connection.close()
				sys.exit()
		
		# get the highest page number, line number to display, last header
		row = self.cursor.fetchone()
		self.db_lastline = row[1]
		self.db_curpos = row[1]
		self.displayline = row[2]
		self.prefix = row[3]
		
		# Second slice index DOESN'T INCLUDE ITSELF
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
		for i in self.headers:
			try:
				if self.lines[0].startswith(i):
					self.displayline = 1
					# counter skips the next line, since we're tweeting it
					self.db_lastline += 2
					self.prefix = self.lines[0]
					self.lines.append(self.lines[0].strip() + '\nl. ' \
					+ str(self.displayline) + ': ' + self.lines[1].strip())
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
		self.lines.append(self.prefix + 'l. ' + str(self.displayline) + ': ' \
		+ self.lines[0].strip())
		return self.lines
		
	def emit_tweet(self):
		""" First call the format_tweet() function, which correctly formats
		the current object's line[] properties, depending
		on what they are, then tweets them. It then writes the
		updated position, line display offset, and header values to the db
		Appends the correctly-formatted line to the line[] list, so it can
		be tweeted
		"""
		self.format_tweet()
		# don't print the line unless the db is updateable
		with self.connection:
			try:
				self.cursor.execute('UPDATE position SET position = ?,\
				displayline = ?, header = ? WHERE position = ?', \
				(self.db_lastline, self.displayline, self.prefix, \
				self.db_curpos))
			except (sqlite3.OperationalError, IndexError):
				print "Wasn't able to update the DB."
				logging.error(now.strftime("%Y-%m-%d %H:%M") + " " + \
				str(sys.argv[0]) + " " + "Couldn't update the DB")
			try:
				api.update_status(str(self.lines[-1]))
			except tweepy.TweepError , err:
				logging.error(now.strftime("%Y-%m-%d %H:%M") + " " + \
				str(sys.argv[0]) + " " + "Couldn't update status. " + \
				"Error was: " + str(err))
				self.connection.rollback()
		self.connection.close()


# first argument (argv[0]) is the abs. path + filename -- not what we want
input_book = BookFromTextFile(sys.argv[1], sys.argv[2])
input_book.emit_tweet()

