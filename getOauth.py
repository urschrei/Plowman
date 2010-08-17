#!/usr/bin/env python
# coding=utf-8
import webbrowser
import sys
import tweepy

"""
    Query the user for their consumer key/secret
    then attempt to fetch a valid access token.
"""


def get_creds(creds):
	""" Obtain and return OAuth credentials from twitter.com
	Takes an empty list, and returns a list containing:
	consumer key
	consumer secret
	access key
	access secret
	"""
	print """I will now attempt to open a web browser to create an OAuth key.
	If you have previously obtained a consumer key and secret, you may close
	the browser window, and enter them below. Otherwise, follow the
	instructions on screen, and refer to
	http://jmillerinc.com/2010/05/31/twitter-from-the-command-line
	-in-python-using-oauth/
	for hints. Be sure to choose "client", and "read/write access"
	
	You may manually access the page at: https://dev.twitter.com/apps/new
	"""
	inp = raw_input("Press Enter to continue, or q to quit...")
	if inp == "q":
		print "Abandoning OAuth process."
		raise tweepy.error.TweepError("OAuth Abandoned")
	webbrowser.open("http://dev.twitter.com/apps/new")
	creds.append(raw_input('Consumer key: ').strip())
	creds.append(raw_input('Consumer secret: ').strip())
	autho = tweepy.OAuthHandler(creds[0], creds[1])
	
	# open authorisation URL in browser
	try:
		webbrowser.open(autho.get_authorization_url())
	except 	tweepy.error.TweepError:
		raise
	# ask user for verification pin
	pin = raw_input('Verification pin number from twitter.com: ').strip()
	# get access token
	token = autho.get_access_token(verifier=pin)

	# give user the access token
	print 'Access token:'
	print '  Key: %s' % token.key
	print '  Secret: %s' % token.secret
	creds.append(token.key)
	creds.append(token.secret)
	return creds