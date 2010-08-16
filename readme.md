# Description #

(With apologies to William Langland)  

A Python script designed to tweet an epic poem stored in a text file, line by line. Line position, line display number, current header, and a SHA1[^1] digest of the file which generated them are stored in a SQLite 3 database. The script is configured to take account of header lines, and thus maintain line numbering (i.e. line numbers are reset to 1, and the new header is prepended as necessary). In addition, the digest ensures that line generation will not continue if the file contents are edited in any way. If the file is modified (other than renaming), the script will reset all. This mechanism also allows a single db to be used for many poems, the digest providing an excellent primary key. The header configuration and display are particular to epic poetry in this case, allowing us to see the current book/passus/canto and line number, respectively.
[SQLite 3], The [Tweepy] library, as well as a valid Twitter username and password are required.
In order to authorise the script, *you will require a valid [twitter] account, and OAuth API access.* Instructions regarding the setup of this access can be found at Jeff Miller's [site].

A future update will include this OAuth setup functionality.

[Tweepy]: http://github.com/joshthecoder/tweepy
[twitter]: https://twitter.com/signup
[SQLite 3]: http://www.sqlite.org/
[site]: http://jmillerinc.com/2010/05/31/twitter-from-the-command-line-in-python-using-oauth/  

[^1]: Secure Hash Algorithm. For more information, see: <http://en.wikipedia.org/wiki/Sha1>

