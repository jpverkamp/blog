---
title: OpenID - Part 2
date: 2012-07-20 04:55:18
programming/languages:
- CSS
- HTML
- PHP
programming/topics:
- Web Development
---
I [wrote yesterday ]({{< ref "2012-07-19-adventures-in-openid-land.md" >}})about getting OpenID up and running, but when I played with the code a bit more today, I realized that something funny was going on. Yahoo worked exactly as I expected, when I clicked on the link for the first time, it would take me to the Yahoo login page and then to a page to grant the proper permissions. All well and good. The same with Google.

But when I logged out of the app and tried to log back in, Google would show the same authentication screen each time. Granted, it was working so far as getting the authentication that I wanted from it, but it was still a little frustrating having to go through that step each time. And if it was frustrating for me, I could only imagine how bad it would be for any users down the line. The strangest part was that it worked fine when I was just getting the identity, but not when I also requested the email.

I ended up spending about two hours (twice as long as getting everything set up in the first place) fruitlessly searching for something that would tell me what was going on, but I kept bouncing around on the same few StackOverflow <a title="LightOpenID forbidden when redirecting back" href="http://stackoverflow.com/questions/4696234/lightopenid-forbidden-when-redirecting-back">[1]</a> <a title="Log-in the user with LightOpenID" href="http://stackoverflow.com/questions/3995011/log-in-the-user-with-lightopenid">[2]</a> and Google App Engine <a title="Using Federated Authentication via OpenID in Google App Engine" href="https://developers.google.com/appengine/articles/openid">[1]</a> pages, none of which were particularly helpful to my particular case.

Finally, the query '<a title="Google Query for 'openid &quot;remember this approval&quot; not working'" href="http://www.google.com/search?q=openid+&quot;remember+this+approval&quot;+not+working">openid "remember this approval" not working</a>' led me to <a title="&quot;Remember this approval&quot; being asked every auth " href="https://groups.google.com/forum/?fromgroups#!topic/google-federated-login-api/yvJ2tmdtr00">this 2009 discussion</a> on Google Groups (with almost that exact same subject line). The final response, which was only sent to the entire list "because the answer may have general interest", has this little gem in it:

I think the problem here is that you are not setting any value for "openid.realm". As such, we are inferring the realm as the "openid.return_to" (as we should, per the OpenID spec). The problem is that your return_to includes some random number, so it is unique to each request. So basically, there is no fixed handle that allow us to use in storing the user's preferences.

Interesting.

After a few more minutes search and <a title="What should I set REALM to, using LightOpenID, for Google url's to remain consistent, for storage in my database?" href="http://stackoverflow.com/questions/5453156/what-should-i-set-realm-to-using-lightopenid-for-google-urls-to-remain-consis">another relevant StackOverflow post</a> (I really should get more involved with that site, it's an amazing resource for programmers), I realize that I had to set the LightOpenID realm to something consistent and relevant:

```php
$openid->realm = 'http://example.com/';
```

Bam. Now it works. It's always amazing when you spend hours working on a one line fix. Hopefully if anyone has this particular problem in the future, there's now one more post on the Internet about how to fix it.

For anyone interested, here is the complete code that I'm using for OpenID now:

```php
session_start();

$openid = new LightOpenID('http://example.com/');
$openid->realm = 'http://example.com/';
$openid->required = array('contact/email');
$openid->returnURL = 'http://example.com/';

// Login via google
if(isset($_POST['login-google'])) {
        $_SESSION['provider'] = 'Google';
        $openid->identity = 'https://www.google.com/accounts/o8/id';
        header('Location: ' . $openid->authUrl());
}

// We're returning from a login attempt
elseif ($openid->validate()) {
	$attrs = $openid->getAttributes();
	$_SESSION['id'] = $attrs['contact/email'];
        $_SESSION['openid'] = $openid->identity;
}
```