---
title: Adventures in OpenID land
date: 2012-07-19 04:59:49
programming/languages:
- CSS
- HTML
- PHP
programming/topics:
- Web Development
---
Today I started working on a little webapp. It's mostly to get me back in practice writing website code, but it does hopefully have the side effect of being useful. More on that later though, perhaps when it's actually working.

In any case, the first thing that I wanted to do for this app was to set up some sort of authentication system. Since I don't have HTTPS set up at the moment with my webhost (<a title="Dreamhost Homepage" href="http://dreamhost.com/">Dreamhost</a>; they really are pretty good to work with and far better than my previous host) and it doesn't really make as much sense to send passwords in plaintext over the network, I decided to go ahead and give OpenID a try. Granted, it's still sending the authentication information in plaintext for at least part of the trip, but it's still something that I think is worth learning.

Since the backend of the website is written in PHP (I generally use Python for prototyping, but I have to admit that it's easier to just hammer out webpages  in PHP) so the first place that a simple web search landed me was <a title="Getting Started with OpenID and PHP" href="http://devzone.zend.com/1254/getting-started-with-openid-and-php/">this article</a> on DevZone, using <a title="Janrain's OpenID Library" href="http://janrain.com/openid-enabled/">Janrain's OpenID library</a>. I downloaded everything... and immediately ran into a roadblock. Turns out in hindsight, I wasn't actually sure how OpenID works, so just mashing the code into my own wasn't going as well as I'd hoped.

Off to [[wiki:Openid|Wikipedia]]()!

It turns out that OpenID basically works like this:

{{< figure src="/embeds/2012/openid.png" >}}

([[wiki:File:OpenIDvs.Pseudo-AuthenticationusingOAuth.svg|source]](), <a title="CC0 1.0 Universal (CC0 1.0)  Public Domain Dedication" href="http://creativecommons.org/publicdomain/zero/1.0/deed.en">license: CC0 1.0</a>)

So basically there were a number of redirects going on behind the scenes that I was having issues setting up, partially due to the relative complexity of the library that I was using. Looking around on the Internet, I found that I wasn't alone in thinking that the library that I was using was particularly powerful, but also a bit more complicated to get started with. So I went in search of a new library and eventually came across <a title="LightOpenID on Google Code" href="http://code.google.com/p/lightopenid/">LightOpenID</a>, with the promise that I could " code a functional client in less than ten lines of code". So off I went!

And really, it was only a tiny bit more than ten lines of code, based on the response to <a title="StackOverflow: Log-in the user with LightOpenID" href="http://stackoverflow.com/questions/3995011/log-in-the-user-with-lightopenid">this StackOverflow question</a>:

```php
session_start();

$openid = new LightOpenID('http://example.com/');
$openid->returnURL = 'http://example.com/';

// Login via google
if(isset($_POST['login-google'])) {
        $_SESSION['provider'] = 'Google';
        $openid->identity = 'https://www.google.com/accounts/o8/id';
        header('Location: ' . $openid->authUrl());
}

// We're returning from a login attempt
elseif ($openid->validate()) {
        $_SESSION['openid'] = $openid->identity;
}
```

That was easy. Next thing to get settled was what do I do with this information now that I have it? Well, the first problem is that the OpenID identifiers are kind of long winded. As an example, my OpenID from Google is 80 characters long, of which 39 are (as far as I can tell) the unique part of the ID. I could probably pull off just those 39 characters and that would be reasonable, but I wanted another solution.

Lo and behold, I can get the user's email address using only 3 more lines of code, one to add the request and two to process it when I get the response back:

```php
session_start();

$openid = new LightOpenID('http://example.com/');
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

I think this will also be helpful in the future as I can use it for this particular project to send out reports to the user whenever they might want them and use it for a sort of sharing system where users can share information with others based on their email address.

So two problems solved and everything seems peachy. So far I have it working with both Google and Yahoo, although adding more should be pretty much trivial. Not too bad for only an hour or so of work.
