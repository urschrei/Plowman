# Unit Tests #

These tests provide around 80% code coverage, the main exception being the `DBconn._create_oauth()` method. However, the [Tweepy][1] module on which the method primarily relies – essentially, it just calls a [wrapper][2] for Tweepy's OAuth functionality – is extensively covered by Tweepy's own [tests][3].  

[1]: https://github.com/joshthecoder/tweepy
[2]: https://github.com/urschrei/Plowman/blob/master/getOAuth.py
[3]: https://github.com/joshthecoder/tweepy/blob/master/tests.py