#!/usr/bin/python
# coding=utf-8
# This is useful: http://openbookproject.net//thinkCSpy/
# This, too: http://www.devshed.com/c/a/Python/Using-SQLite-in-Python/

# twitter: robo_dante/beatrice
# gmail: alighieribot2010/beatrice1265

import sys
import os
import sqlite3

import logging
LOG_FILENAME = '/Users/sth/library/logs/python.log'
logging.basicConfig(filename=LOG_FILENAME,level=logging.ERROR)

# tweepy stuff
import tweepy
auth=tweepy.BasicAuthHandler('robo_dante', 'beatrice')
api=tweepy.API(auth)




class Book:
	"Create a Book object from a text file"
	def __init__(self, fname=None):
		self.name = fname
		s = self.name.split(".")
		self.db_name = str(s[0]) + ".db"
		# create a SQLite connection, or create a new db and table
		self.connection=sqlite3.connect(self.db_name)
		self.cursor=self.connection.cursor()
		try:
			self.cursor.execute('SELECT * FROM position ORDER BY POSITION DESC LIMIT 1')
		except sqlite3.OperationalError:
			print "Couldn't find the specified table. Creating…"
			# set up a new blank table, and insert a row which starts off at line 0
			self.cursor.execute('CREATE TABLE position (id INTEGER PRIMARY KEY, position INTEGER, off_set INTEGER)')
			db_lastline=0
			self.cursor.execute('INSERT INTO position VALUES (null, ?, ?)',(db_lastline, 0))
			try:
				self.cursor.execute('SELECT * FROM position ORDER BY POSITION DESC LIMIT 1')
			except sqlite3.OperationalError:
				print "Still couldn't execute the SQL query, even though I created a new table. Giving up."
				# close the SQLite connection, and quit
				self.connection.commit()
				self.connection.close()
				sys.exit()
		# get the highest page number, and the line display offset
		row=self.cursor.fetchone()
		self.db_lastline=row[1]
		self.db_curpos=row[1]
		self.off_set=row[2]
		# the poem starts on line 1, not line 0, so increase by 1, then subtract offset from 'real' line display
		get_lines = list()
		try:
			with open(self.name, "r") as t_file:
				for a_line in t_file:
					if not a_line.strip():
						continue
						# if we encounter a blank line, do nothing and carry on
					else:
						get_lines.append(a_line)
						# would it be more efficient to open, read one line, and store byte position?
		except IOError:
			print "Couldn't open the text file for reading. Exiting."
			sys.exit()
		self.lastline = get_lines[self.db_lastline]
		self.nextline = get_lines[self.db_lastline+1]
		self.displayline=(self.db_lastline + 1) - self.off_set
		
		
		
	def format_tweet(self):
		""" Properly format an input string based on whether it's a header line, or a poetry line
		accepts 2 inputs: the current line from a book, and the following line. If the current line
		begins with "CANTO", it's a header, so instead of displaying a line number, we join the next line
		and increment both the line number and the line offset by 1. This means the line numbers
		don't jump when a header is encountered, as the offset is subtracted from the display line.
		Returns a ready-to-tweet string, either a canto, or a poetry line. """
		#pattern='^CANTO'
		#if re.search(pattern, input_string):
		if self.lastline.startswith("CANTO"):
			self.db_lastline=self.db_lastline + 1
			self.off_set=self.off_set + 1
			print str(self.lastline) + str(self.nextline)
		else:
			print 'l. ' + str(self.displayline) + ': ' + self.lastline
		# what if it's neither a header nor a poetry line?
		
		
		
	def emit_tweet(self):
		try:
			with self.connection:
				self.cursor.execute('UPDATE position SET position=?,off_set=? WHERE position=?',(self.db_lastline + 1, self.off_set, self.db_curpos))
			# don't print the line unless the DB is updateable
			self.format_tweet()
		except sqlite3.OperationalError:
			print "Wasn't able to update the DB."
			#	logging.error("Something went wrong, and the tweet couldn't be sent")
		self.connection.close()



b=Book('dc.txt')
b.emit_tweet()




# check for exceptions:
#try:
#	api.update_status(tweet)
#except:
#	sys.exit()

# we only need a single line in the DB, since we're only storing a 'pointer'


