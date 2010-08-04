#!/usr/bin/python
# coding=utf-8
# This is useful: http://openbookproject.net//thinkCSpy/
# This, too: http://www.devshed.com/c/a/Python/Using-SQLite-in-Python/

# twitter: robo_dante/beatrice
# gmail: alighieribot2010/beatrice1265

import sys
import os
import sqlite3
import re
import tweepy
sys.path.append("/Users/sth/scripts")
# tweepy stuff
auth=tweepy.BasicAuthHandler('robo_dante', 'beatrice')
api=tweepy.API(auth)


connection=sqlite3.connect('dc.db')
cursor=connection.cursor()
try:
	cursor.execute('SELECT * FROM position ORDER BY POSITION DESC LIMIT 1')
except sqlite3.OperationalError:
	print "Couldn't find the specified table. Creating…" 
	cursor.execute('CREATE TABLE position (id INTEGER PRIMARY KEY, position INTEGER, tweeted INTEGER, off_set INTEGER)')
	lastline=0
	cursor.execute('INSERT INTO position VALUES (null, ?, ?, ?)',(lastline, "1", 0))
	# set up a new blank table, and start off at line 0
	# retry logic goes here

# get the highest page number, and the line display offset
row=cursor.fetchone()
lastline=row[1]
off_set=row[3]

# The poem starts on line 1, not line 0. Subtract offset value from 'real' line display number
printline=(lastline + 1) - off_set



def format_tweet(input_string,next_string):
	""" Properly format an input string based on whether it's a header line, or a poetry line
	accepts 3 inputs: the current line from a book, the following line, and the current line display
	off_set, which is incremented each time a header line is encountered, and subtracted from the
	"real" line number, in order to display the correct line number.
	returns a ready-to-tweet string, either a canto, or a poetry line. """
	
	# If line is a new Canto, append the following line to it, instead of "l. "
	#pattern='^CANTO'
	#if re.search(pattern, input_string):
	if input_string.startswith("CANTO"):
		global lastline
		global off_set
		lastline = lastline + 1
		off_set = off_set + 1
		return input_string + next_string
	else:
		return 'l. ' + str(printline) + ': ' + input_string
		# Maybe we need to create a new object with properties tweet_text and off_set


get_lines = list()
try:
	with open('dc.txt', "r") as t_file:
		for a_line in t_file:
			if not a_line.strip():
				continue
				# if we encounter a blank line, do nothing and carry on
			else:
				get_lines.append(a_line)
				# we could just jump to a specific line in the file, but that appears to be tricky in Python
except IOError:
	print "Couldn't open the text file for reading. Exiting."
	sys.exit()

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

