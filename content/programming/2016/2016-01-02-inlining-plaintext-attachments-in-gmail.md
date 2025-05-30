---
title: Inlining plaintext attachments in Gmail
date: 2016-01-02
aliases:
- /2016/12/02/inlining-plaintext-attachments-in-gmail/
programming/languages:
- JavaScript
programming/topics:
- Email
- Gmail
- Userscripts
---
When you send a text message to a Gmail email address (at least from an iPhone using AT&T), you get something like this:

{{< figure src="/embeds/2016/gpti-before.png" >}}

It's vaguely annoying to have to click through every single time just to see what the message is, especially when various extensions (such as <a href="https://github.com/gorhill/uMatrix">uMatrix</a>) break overlay rendering or when you have multiple attachments.

Much better would be to just display the plaintext attachments inline:

{{< figure src="/embeds/2016/gpti-after.png" >}}

<!--more-->

Let's do it!

Essentially, I'm going to write a Javascript userscript, compatible with <a href="https://addons.mozilla.org/en-US/firefox/addon/greasemonkey/">Greasemonkey</a> or <a href="https://chrome.google.com/webstore/detail/tampermonkey/dhdgffkkebhmkfjojejmpbldmpobfkfo?hl=en">Tampermonkey</a> for Chrome. Either allows you to insert small bits of Javascript into web pages to modify their behavior.

After digging around a bit in the structure of Gmail's message pages, here's roughly what I ended up with:

```javascript
var checkForPlaintexts = function(evt) {
    jQuery('span[download_url]').each(function(i, el) {
        var parts = el.getAttribute('download_url').split(':');
        if (!parts || parts[0] != 'text/plain') return;
        var url = parts[3];

        var newElement = jQuery('<pre id="GPTI_' + i + '"></pre>');
        newElement.text('Loading: ' + url);

        jQuery(el).replaceWith(newElement);
        jQuery.ajax({
            url: url,
            success: function(data) {
                newElement.text(data);
            }
        });
    });
};
```

Basically, we're going to look for a `span` containing a `download_url` attribute. For the moment at least, that's always present with attachments and not otherwise. If you take that `download_url` element, you get something like this:

`text/plain:text_0.txt:https://mail.google.com/mail/u/0/?ui=...``

The first part is a [[wiki:MIME type]]()--of which, we're only interested in plaintext. The last section is a URL under gmail which, when visited, contains the contents of the attachment.

Now that I have that (via jQuery[^1][^2]), I build a new `pre` element with the text content and shove it in place.

Voila.

All I have to do next is make sure that it's called when I either load the page or when I navigate from the Inbox (et al) to a message:

```javascript
jQuery(window).bind('hashchange', checkForPlaintexts);
jQuery(checkForPlaintexts);
```

Unfortunately, this has some issues as well. It works if the message has already been viewed once, but not on the first load. Basically, I'm running into timing issues.

My original solution to this was to put in a quick delay and call it a day. Unfortunately, when using satellite internet... even that didn't work. So instead, I built a system that will delay the initial call and then--if it fails--try a few more times with increasing timeouts between then.

Something like this:

```javascript
var delayedEvent = function(f, timeout, retries) {
    timeout = timeout || 0;
    retries = retries || 0;

    return function(evt) {
        setTimeout(f, timeout, evt, retries, timeout * 2);
    }
};

var checkForPlaintexts = function(evt, retries, delay) {
    retries = retries || 0;
    var foundOne = false;

    jQuery('span[download_url]').each(function(i, el) {
        foundOne = true;

        ...
    });

    if (!foundOne && retries) {
        setTimeout(checkForPlaintexts, delay, evt, retries - 1, delay * 2);
    }
};


jQuery(window).bind('hashchange', delayedEvent(checkForPlaintexts, 125, 3));
jQuery(delayedEvent(checkForPlaintexts, 125, 3));
```

So far, this has worked perfectly. Sometimes it takes a bit to fetch the ajax call in the background. That's why I put in the `Loading...` notification to tell the user it was working.

It's been a little while since I last wrote a userscript (pre-Chrome, to give you an idea). I forgot how much fun it can be to mess with websites a bit like that. I may write up a few more.

If you'd like to see the entire source (includes some debug messaging and the userscript header comments), you can do so on GitHub: <a href="https://github.com/jpverkamp/userscripts/blob/master/gmail-plaintext-inline.user.js">gmail-plaintext-inline.user.js</a>

If you want to install it directly (and have Greasemonkey/Tampermonkey installed), you can directly from GitHub as well: <a href="https://github.com/jpverkamp/userscripts/raw/master/gmail-plaintext-inline.user.js">install gmail-plaintext-inline.user.js</a>.

As a side note, 'optional' parameters in Javascript are weird...

[^1]: I know that including jQuery for just this is overkill when you can do both element selection and ajax calls without it, but hey. It works.
[^2]: If something is stupid but works, it's not stupid.
