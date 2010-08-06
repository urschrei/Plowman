#!/usr/bin/python
# coding=utf-8
# This is useful: http://openbookproject.net//thinkCSpy/
# This, too: http://www.devshed.com/c/a/Python/Using-SQLite-in-Python/

# twitter: robo_dante/beatrice
# gmail: alighieribot2010/beatrice1265

import sys
import os
import sqlite3
import datetime
import logging
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
	logging.error(now.strftime("%Y-%m-%d %H:%M") + " " + str(sys.argv[0]) + " " + \
	"Incorrect number of arguments")
	sys.exit()

class Book:
	""" Create a Book object from a text file. Takes two arguments:
	1. a filename, from which text will be read
	2. a string used to identify header lines
	A sqlite3 connection object is created, and an attempt it made to
	retrieve a row matching from a DB matching that of the filename which was \
	passed. If no DB is found, a new
	DB is created and a table containing default values is inserted.
	"""
	def __init__(self, fname = None, hid = None):
		self.name = fname
		self.header_id = hid
		s = self.name.split(".")
		self.db_name = str(s[0]) + ".db"
		# create a SQLite connection, or create a new db and table
		self.connection = sqlite3.connect(self.db_name)
		self.cursor = self.connection.cursor()
		try:
			self.cursor.execute('SELECT * FROM position ORDER BY POSITION \
			DESC LIMIT 1')
		except sqlite3.OperationalError:
			print "Couldn't find the specified table. Creating…"
			# set up a new blank table, and insert a row which starts off at line 0
			self.cursor.execute('CREATE TABLE position (id INTEGER PRIMARY \
			KEY, position INTEGER, off_set INTEGER)')
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
		self.off_set = row[2]
		get_lines = list()
		try:
			# try to open the specified text file for reading
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
		# Check that we haven't reached the end of the file
		try:
			self.lastline = get_lines[self.db_lastline]
		except IndexError:
			now = datetime.datetime.now()
			logging.error(now.strftime("%Y-%m-%d %H:%M") + " " + \
			str(sys.argv[0]) + " " + "Reached " + self.name + " EOF")
			sys.exit()
		try:
			self.nextline = get_lines[self.db_lastline + 1]
		except IndexError:
			self.nextline = ""
		# the poem starts on line 1, not line 0, so increase by 1,
		# then subtract offset from 'real' line display
		self.displayline = (self.db_lastline + 1) - self.off_set
		
		
		
	def _format_tweet(self, newvals):
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
			self.off_set += 1
			newvals.append(self.off_set)
			message = str(self.lastline) + str(self.nextline)
			newvals.append(message)
		else:
			newvals.append(self.db_lastline)
			newvals.append(self.off_set)
			message = 'l. ' + str(self.displayline) + ': ' + self.lastline
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
		now = datetime.datetime.now()
		# updates() will be filled with values which will be emitted
		# following a successful DB update
		updates = list()
		self._format_tweet(updates)
		# don't print the line unless the DB is updateable
		try:
			with self.connection:
				self.cursor.execute('UPDATE position SET position = ?,\
				off_set = ? WHERE position = ?',(updates[0] + 1, updates[1] \
				, self.db_curpos))
			try:
				print str(updates[2])
				# api.update_status(str(updates[2]))
			except:
				print "Couldn't output the message."
				logging.error(now.strftime("%Y-%m-%d %H:%M") + " " + \
				 str(sys.argv[0]) + " " + "Couldn't output the message")
		except sqlite3.OperationalError:
			print "Wasn't able to update the DB."
			logging.error(now.strftime("%Y-%m-%d %H:%M") + " " + \
			str(sys.argv[0]) + " " + "Couldn't update the DB")
			# logging.error("The tweet couldn't be sent")
		self.connection.close()



# first argument (argv[0]) is always the filename – not what we want
b = Book(sys.argv[1], sys.argv[2])
b.emit_tweet()

