#!/usr/bin/python
# coding=utf-8
# This is useful: http://openbookproject.net//thinkCSpy/
# This, too: http://www.devshed.com/c/a/Python/Using-SQLite-in-Python/

# twitter: robo_dante/beatrice
# gmail: alighieribot2010/beatrice1265
""" 
This module reads a text file from disk, and outputs properly-
formatted lines from it, one or two lines at a time, depending on
whether it's a header line, or body text. The line position is stored in
a sqlite3 database, in the same directory as the text file.
The module takes exactly two arguments: the file name (including path), and
the text to match against in order to designate a header line
"""
import sys
import sqlite3
import datetime
import logging
import string
LOG_FILENAME = '/Users/sth/library/logs/python.log'
logging.basicConfig(filename=LOG_FILENAME, level=logging.ERROR)

# tweepy stuff
import tweepy
auth = tweepy.BasicAuthHandler('robo_dante', 'beatrice')
api = tweepy.API(auth)

if len(sys.argv) != 3:
	print "Incorrect number of arguments. Please call the script like this: \
	bookbyline.py filename.txt header"
	now = datetime.datetime.now()
	logging.error(now.strftime("%Y-%m-%d %H:%M") + " " + str(sys.argv[0]) \
	 + " " + "Incorrect number of arguments")
	sys.exit()

class BookFromTextFile:
	""" Create a Book object from a text file. Takes two arguments:
	1. a filename, from which text will be read
	2. a string used to identify header lines
	A sqlite3 connection object is created, and an attempt it made to
	retrieve a row matching from a DB matching the filename which was \
	passed. If no DB is found, a new
	DB is created and a table containing default values is inserted.
	"""
	def __init__(self, fname = None, hid = None):
		self.name = fname
		self.header_id = hid
		spt = self.name.split(".")
		self.db_name = str(spt[0]) + ".db"
		# create a SQLite connection, or create a new db and table
		try:
			self.connection = sqlite3.connect(self.db_name)
		except IOError:
			print "Couldn't read or create a blank DB. That's a show-stopper."
			sys.exit()
		self.cursor = self.connection.cursor()
		try:
			self.cursor.execute('SELECT * FROM position ORDER BY POSITION \
			DESC LIMIT 1')
		except sqlite3.OperationalError:
			print "Couldn't find the specified table. Creating…"
			# set up a new blank table
			self.cursor.execute('CREATE TABLE position (id INTEGER PRIMARY \
			KEY, position INTEGER, header STRING)')
			db_lastline = 0
			self.cursor.execute('INSERT INTO position VALUES (null, ?, ?)' \
			,(db_lastline, 0))
			try:
				self.cursor.execute('SELECT * FROM position ORDER BY POSITION \
				DESC LIMIT 1')
			except sqlite3.OperationalError:
				print "Still couldn't execute the SQL query, even though I \
				created a new table. Giving up."
				# close the SQLite connection, and quit
				self.connection.commit()
				self.connection.close()
				sys.exit()
		# get the highest page number, and the line display offset
		row = self.cursor.fetchone()
		self.db_lastline = row[1]
		self.db_curpos = row[1]
		self.displayline = row[2]
		self.prefix = row[3]
		get_lines = list()
		# try to open the specified text file for reading
		try:
			with open(self.name, "r") as t_file:
				for a_line in t_file:
					if not a_line.strip():
						continue
						# if we encounter a blank line, skip it, and carry on
					else:
						get_lines.append(a_line)
						# would it be more efficient to open, read one line,
						# and store byte position?
		except IOError:
			print "Couldn't open the text file for reading. Exiting."
			sys.exit()
		# check that we haven't reached the end of the file
		try:
			self.lastline = get_lines[self.db_lastline]
		except IndexError:
			curtime = datetime.datetime.now()
			logging.error(curtime.strftime("%Y-%m-%d %H:%M") + " " + \
			str(sys.argv[0]) + " " + "Reached " + self.name + " EOF")
			sys.exit()
		# catch error if nextline would be past EOF
		try:
			self.nextline = get_lines[self.db_lastline + 1]
		# This means we've reached the end of the file, so append "-- End"
		except IndexError:
			self.lastline = str(get_lines[self.db_lastline]) + "-- End"
		# the poem starts on line 1, not line 0, so increase by 1,
		# then subtract offset from 'real' line display
		
		
		
	def format_tweet(self, newvals):
		""" Properly format an input string based on whether it's a header
		line, or a poetry line. If the current line is a header
		(see self.header_id), instead of displaying a line number,
		we join the next line and increment both the line number and
		the line offset by 1. This means the line numbers don't jump when a
		header is encountered, as the offset is subtracted from the display
		line.
		
		Prints a properly-formatted string, either a canto or poetry line.
		"""
		#pattern="^" + self.header_id
		#if re.search(pattern, input_string):
		if self.lastline.startswith(self.header_id):
			self.db_lastline += 1
			newvals.append(self.db_lastline)
			self.prefix = str(self.lastline)
			# reset display line to 1
			self.displayline = 1
			message = 'l. ' + str(self.displayline) + ': ' \
			+ self.nextline.strip()
			newvals.append(message)
		else:
			newvals.append(self.db_lastline)
			# increment display line
			self.displayline += 1
			message = 'l. ' + str(self.displayline) + ': ' \
			+ self.lastline.strip()
			newvals.append(message)
		return newvals
		# what if it's neither a header nor a poetry line?
		
	def emit_tweet(self):
		""" First call the format_tweet() function, which correctly formats
		the current object's lastline and thisline properties, depending
		on what they are, and then prints / tweets them. It then writes the
		updated last line printed and line display offset values the DB
		
		Returns a list of values which are used to output the message and
		update the DB
		"""
		curtime = datetime.datetime.now()
		# updates() will be filled with values which will be emitted
		# following a successful DB update
		updates = list()
		self.format_tweet(updates)
		# don't print the line unless the DB is updateable
		try:
			with self.connection:
				self.cursor.execute('UPDATE position SET position = ?,\
				displayline = ?, header = ? WHERE position = ?',(updates[0] \
				+ 1, self.displayline, self.prefix, self.db_curpos))
				try:
					print self.prefix + str(updates[1])
					# api.update_status(str(updates[1]))
				# we need to define some exception types here
				except:
					# this exception should percolate back up one level
					print "Couldn't output the message."
					logging.error(curtime.strftime("%Y-%m-%d %H:%M") + " " + \
					 str(sys.argv[0]) + " " + "Couldn't output the message")
					self.connection.rollback()
		except sqlite3.OperationalError:
			print "Wasn't able to update the DB."
			logging.error(curtime.strftime("%Y-%m-%d %H:%M") + " " + \
			str(sys.argv[0]) + " " + "Couldn't update the DB")
			# logging.error("The tweet couldn't be sent")
		self.connection.close()



# first argument (argv[0]) is always the filename – not what we want
b = BookFromTextFile(sys.argv[1], sys.argv[2])
b.emit_tweet()

