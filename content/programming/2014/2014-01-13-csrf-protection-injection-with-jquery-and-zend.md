---
title: CSRF protection injection with jQuery and Zend
date: 2014-01-13 14:00:24
programming/languages:
- JavaScript
- PHP
- Zend
- jQuery
programming/topics:
- Security
- Web Development
---
[[wiki:Csrf|Cross-site request forgery]]() attacks are among the most common vulnerabilities against websites, listed as <a href="https://www.owasp.org/index.php/Top_10_2013-A8-Cross-Site_Request_Forgery_(CSRF)">number 8</a> on <a href="https://www.owasp.org/index.php/Top_10_2013-Top_10">OWASP's 2013 Top 10 list</a>.

<!--more-->

A CSRF attack involves an attacker identifying some state changing URL within a web application. Say, for example, that you have a website where you can change a user's nickname like this:

```html
POST /change-nickname.php

new-nickname=...
```

In that case, an attacker could copy the URL, edit the new nickname field, and send you a link via IM. So long as you're already logged into the site, when you click the link, the browser will helpfully send along your session information to the server and your username is changed.

How can you fix that though? You need the browser to automatically send session information since HTTP is a stateless protocol. Without that, it's much more difficult to maintain long running sessions.

What we really need is some bit of information that the client will send along with requests if they come from our server, but that won't be sent along if the user just clicks on a random link. You could do this by sending along a random token, stored in the session:

```php
// change-nickname.php
<?php
session_start();

// Choose a CSRF token if one hasn't already been assigned, tokens are unique to each user
if (!isset($_SESSION['csrf-token'])) {
    $_SESSION['csrf-token'] = base64_encode(openssl_random_pseudo_bytes(4));
}

// Check if the user is trying to update the page
if (isset($_POST['new-nickname'])) {
    // Validate the CSRF token
    if (isset($_POST['csrf-token']) && $_POST['csrf-token'] == $_SESSION['csrf_token']) {
        { ... logic to change nickname ... }
    } else {
        { ... logic to log CSRF validation failures ... }
    }
}

// Otherwise, send the update nickname form
} else {
?>
<form method="POST" action="/change-nickname.php">
    <input type="hidden" name="csrf-token" value="<?= $_SESSION['csrf-token'] ?>" />
    <input name="new-nickname" />
    <input type="submit" />
</form>
<?php
}
?>
```

This way, we'll send the CSRF token with the page and the client will automatically send it back--but only if they use our form. If the attacker could guess the session token, they could of course send it along as well, but assuming that we're using HTTPS for communication and a random (enough) token, this shouldn't be possible.

So this works. But what if you have a much larger code base? Do you really want to embed the CSRF token in every single form that you make? And what if you're using Ajax requests? It turns out that there's a much more elegant solution.

What we want to do is use jQuery to inject CSRF tokens into every request and every form. Then on the PHP end, we'll use Zend's plugin framework to check every post request for this token. That way, every bit of code you write is automatically protected and the protection is centralized if you ever have to make a change. Sounds good, yes?

First, the jQuery. We'll still need a bit of PHP to send the CSRF token from the server to the client. Something like this:

```php
// index.php
<script type="text/javascript">
csrf_token = '<?= $_SESSION['csrf-token']; ?>';
</script>
```

Yes, it's a global variable, but you could wrap that up in whatever other JavaScript objects you are already creating easily enough.

After that, we want to hook into all jQuery Ajax requests. The `ajaxPrefilter` function will do exactly what we want. It's called before any call to `$.ajax`, including functions that use it, such as `$.post` and friends.

```javascript
$.ajaxPrefilter(function(options) {
    if (options.type === 'POST') {
        options.data = options.data || {};
        options.data['csrf-token'] = csrf_token;
    }
});
```

That will add an additional field to any POST request. It doesn't protect against other types (such as GET), but that should be easy enough to change.

For the other half (forms that don't use Ajax, as in the original example), we need to get a little more sneaky. What we want is to add a event listener for form submits that will globally trigger on any form--even those that are added dynamically. Luckily, jQuery's `on` has exactly what we need:

```javascript
$(document).on('submit', 'form'), function(evt) {
    var form = $(e.target);
    if (form.attr('action') && form.attr('action').toUpperCase() === 'POST') {
        form.not(':has(input#csrf-token)').append(
            '<input type="hidden" id="csrf-token" name="csrf-token" value="' + csrf_token + '" />'
        );
    }
});
```

One note for both of these methods is that they will add the CSRF token to *every* request, even those that are going to other sites. For the increasingly common practice of mashups, this won't be quite what you want, but it shouldn't be difficult to add.

On the server side, we want to write a `Zend_Controller_Plugin_Abstract`, specifically the `preDispatch` function. Like the `ajaxPrefilter` function, this can be used to apply to *all* requests, globally enabling CSRF protection. We'll want something like this:

```php
// CSRFPlugin.php
<?php
class CSRFPlugin extends Zend_Controller_Plugin_Abstract {
    public function preDispatch(Zend_Controller_Request_Abstract $request) {
        if (request->getMethod() == 'POST') {
            if (!isset($_POST['csrf-token']) || $_POST['csrf-token'] != $_SESSION['csrf-token']) {
                { ... logic to log CSRF validation failures ... }
                exit(); // Stop the request from processing
            }
        }
   }
}
?>

// index.php
<?php
Zend_Controller_Front::getInstance()->registerPlugin(new CSRFPlugin());
?>
```

And that's all you need. Of course, in practice you'd likely want to more tightly integrate this with your own code base (use structures that you're already creating / hooking into error reporting frameworks / better filtering for requests that need or don't need CSRF protection), but at least it's a start.
