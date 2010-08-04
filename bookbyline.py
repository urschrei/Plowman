#!/usr/bin/python
# coding=utf-8
# This is useful: http://openbookproject.net//thinkCSpy/
# This, too: http://www.devshed.com/c/a/Python/Using-SQLite-in-Python/

# twitter: robo_dante/beatrice
# gmail: alighieribot2010/beatrice1265

import sys
import os
import sqlite3
import tweepy

# tweepy stuff
auth=tweepy.BasicAuthHandler('robo_dante', 'beatrice')
api=tweepy.API(auth)



# create a SQLite connection, or create a new db and table
connection=sqlite3.connect('dc.db')
cursor=connection.cursor()
try:
	cursor.execute('SELECT * FROM position ORDER BY POSITION DESC LIMIT 1')
except sqlite3.OperationalError:
	print "Couldn't find the specified table. Creating…"
	# set up a new blank table, and insert a row which starts off at line 0
	cursor.execute('CREATE TABLE position (id INTEGER PRIMARY KEY, position INTEGER, tweeted INTEGER, off_set INTEGER)')
	lastline=0
	cursor.execute('INSERT INTO position VALUES (null, ?, ?, ?)',(lastline, "1", 0))
	try:
		cursor.execute('SELECT * FROM position ORDER BY POSITION DESC LIMIT 1')
	except sqlite3.OperationalError:
		print "Still couldn't execute the SQL query, even though I created a new table. Giving up."
		# close the SQLite connection, and quit
		connection.commit()
		sys.exit()



# get the highest page number, and the line display offset
row=cursor.fetchone()
lastline=row[1]
off_set=row[3]
# the poem starts on line 1, not line 0, so increase by 1, then subtract offset from 'real' line display
displayline=(lastline + 1) - off_set



def format_tweet(input_string,next_string):
	""" Properly format an input string based on whether it's a header line, or a poetry line
	accepts 2 inputs: the current line from a book, and the following line. If the current line
	begins with "CANTO", it's a header, so instead of displaying a line number, we join the next line
	and increment both the line number and the line offset by 1. This means the line numbers
	don't jump, when a header is encountered, as the offset is subtracted from the display line.
	Returns a ready-to-tweet string, either a canto, or a poetry line. """
	#pattern='^CANTO'
	#if re.search(pattern, input_string):
	if input_string.startswith("CANTO"):
		global lastline
		global off_set
		lastline=lastline + 1
		off_set=off_set + 1
		return input_string + next_string
	else:
		return 'l. ' + str(displayline) + ': ' + input_string



get_lines = list()
try:
	with open('dc.txt', "r") as t_file:
		for a_line in t_file:
			if not a_line.strip():
				continue
				# if we encounter a blank line, do nothing and carry on
			else:
				get_lines.append(a_line)
				
except IOError:
	print "Couldn't open the text file for reading. Exiting."
	sys.exit()

# take the raw text lines, and correctly format them for display
tweet=format_tweet(get_lines[lastline],get_lines[lastline + 1])

# check for exceptions:
#try:
#	api.update_status(tweet)
#except:
#	print "Something's gone wrong…"
#	sys.exit()

print tweet
cursor.execute('INSERT INTO position VALUES (null, ?, ?, ?)',(lastline + 1, "1", off_set))
connection.commit()

