# Description #

(With apologies to William Langland)  

A Python script designed to tweet an epic poem stored in a text file, line by line. Line position, line display number, current header, and a SHA1[^1] digest of the file which generated them are stored in a SQLite 3 database. The script is configured to take account of header lines, and thus maintain line numbering (i.e. line numbers are reset to 1, and the new header is prepended as necessary). In addition, the digest ensures that line generation will not continue if the file contents are edited in any way. If the file is modified (other than renaming), the script will reset to the first line of the text file. This mechanism also allows a single db to be used for many poems, the digest providing an excellent primary key. The header configuration and display are particular to epic poetry in this case, allowing us to see the current book/passus/canto and line number, respectively.
[SQLite 3], The [Tweepy] library, as well as a valid Twitter username and password are required.
In order to authorise the script, *you will require a valid [twitter] account, and OAuth API access to it.*  

# Initial Setup #

These setup steps assume that you are familiar with a terminal, and that you have a terminal window open.

1. Place bookbyline.py, getOAuth.py and the text file containing your poem in a directory of your choosing (cron should be able to access it). Ensure that both of the files have been chmodded a+x.
2. Switch back to your home directory (`cd ~`), and call the script as follows: `python /path/to/bookbyline.py /path/to/text.txt header_1,header_2,…header_n`, where "header_n" are strings which are to be considered "header" lines.
3. When you first run the script, you will be prompted to create OAuth credentials, and the script will attempt to open your default browser on the <https://dev.twitter.com/apps/new> page.
4. Once you have signed into Twitter, you will have to complete a form with the following fields:
	1. `Application Name:` this is the name of the application which will appear in your tweets, feel free to personalise it
	2. `Description:` enter a brief description of what this application does
	3. `Application Website:` if you wish to point your bot's followers at a particular website, enter its URL here. Alternatively, you may wish to enter the GitHub repository's URL
	4. `Organization:` if you are an organisation, say so here
	5. `Website:` if you or your organisation have a website, enter its URL here
	6. `Application Type:` **ensure that this is set to `client`**
	7. `Callback URL:` leave this blank
	8. `Default Access type:` **ensure that this is set to `Read & Write`**
	9. `Use Twitter for login:`leave this unchecked
5. Now, complete the Captcha, and press the `save` button.
6. On the next page, look for the following: `Consumer Key` and `Consumer Secret`. Copy the first, then switch back to the terminal, and paste it at the prompt, then press return. Repeat this process. The browser will then be redirected to a page asking you if you would like to allow the application name you just chose to connect to your account. Click `allow`
7. On the next page, you will see a PIN. Copy this, switch back to the terminal, and paste it, then press return. A key and secret will be displayed, the terminal will complete its initial setup, and tweet the first line of your chosen poem.
8. You may now add the command detailed in step 2 to your crontab if you wish it to be fully automated, or call it from the command line whenever you like.
9. You should see a new file, `tweet_books.sl3` in your home directory. This contains various settings and access keys for the account you just set up. If you remove it, or alter its contents, the script will reset, and you'll have to set up a new OAuth instance. Don't move it unless you know what you're doing.

[Tweepy]: http://github.com/joshthecoder/tweepy
[twitter]: https://twitter.com/signup
[SQLite 3]: http://www.sqlite.org/
[^1]: Secure Hash Algorithm. For more information, see: <http://en.wikipedia.org/wiki/Sha1>

