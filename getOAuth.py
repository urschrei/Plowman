#!/usr/bin/env python
# coding=utf-8
"""
A wrapper for tweepy's OAuth functionality:
Attempt to obtain a consumer key/secret,
then attempt to fetch a valid access token.
"""
import webbrowser
import tweepy
import sys

def get_creds(creds):
    """ Obtain and return OAuth credentials from twitter.com
    Takes an empty list, and returns a list containing:
    consumer key
    consumer secret
    access key
    access secret
    """
    print """Now attempting to open a web browser to create an OAuth key.
If you have previously obtained a Consumer key and secret, you may close
the browser window, and enter them below. Otherwise, follow the
instructions on screen, and refer to
https://github.com/urschrei/Plowman/blob/master/readme.md
for instructions. Be sure to choose "client", and "Read & Write access"
"""
    inp = raw_input("Press Return to continue, or q then Return to quit...")
    if inp == "q":
        print "Abandoning OAuth process."
        raise tweepy.TweepError("OAuth process was abandoned")
    webbrowser.open("http://dev.twitter.com/apps/new")
    creds["conkey"] = (raw_input('Consumer Key: ').strip())
    creds["consecret"] = (raw_input('Consumer Secret: ').strip())
    autho = tweepy.OAuthHandler(creds["conkey"], creds["consecret"])

    # open authorisation URL in browser
    try:
        webbrowser.open(autho.get_authorization_url())
    except tweepy.TweepError:
        raise
    # ask user for verification pin
    pin = raw_input('Verification PIN from twitter.com: ').strip()
    # get access token
    token = autho.get_access_token(verifier=pin)

    # give user the access token
    print "Access token:\n  Key: %s\n   Secret: %s" % (token.key, token.secret)
    creds["acckey"] = token.key
    creds["accsecret"] = token.secret
    return creds


def main():
    """ main function
    """
    oac = {}
    get_creds(oac)
    print "Key values:\n    Consumer key: %s\n  Consumer secret: %s\n\
    Access key: %s\n    Access secret: %s" % (oac["conkey"], oac["consecret"], \
    oac["acckey"], oac["accsecret"])


if __name__ == '__main__':  
    # only do comprehensive error handling if running in standalone mode
    # thanks to Brad Wright (github.com/bradleywright) for this
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        # actually raise these so it exits cleanly
        raise
    except Exception, error:
        # all other exceptions, so display the error
        print error
    else:
        pass
    finally:
        # exit cleanly once we've done everything else
        sys.exit(0)
