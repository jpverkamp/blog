---
title: Adding HSTS to Redirects in Apache
date: 2018-07-18
programming/topics:
- Apache
- HTTPS
---
TLDR:

```apache
# Use 'always' so headers are also set for non-2XX and unset to avoid duplicates
<IfModule headers_module>
	header unset Strict-Transport-Security
	header always set Strict-Transport-Security "max-age=16070400; includeSubDomains;"
</IfModule>
```

Slightly[^1] longer version:

[HTTPS everywhere](https://www.eff.org/https-everywhere) is a worthwhile goal. Even when you have traffic that isn't super interesting or sensitive by itself, the fact that you're encrypting it makes traffic that really does need to be encrypted safer against tools that grab all of the encrypted traffic they can to decrypt later if/when possible.

One of the downsides of using HTTPS though is that without certain things in place, many users will still type `domain.com` in their address bar from time to time, completely missing out on the `https://`. While you can immediately redirect them, that very first request is a risk, since if a [[wiki:man-in-the-middle attack]]() happens to catch that request, they can downgrade the entire connection.

Enter [[wiki:HTTP Strict Transport Security]]() (HSTS). It's a HTTP header that you can send on the first `HTTPS` connection you establish with a compatible client. Once you've done that, any further requests (until the header's TTL expires without being renewed) will be sent to `https://` no matter what the user types. Which solves the first request problem for all sessions... but it still doesn't fix the very first time you have to get the header. So how do you fix that?

<!--more-->

[HSTS Preload lists](https://hstspreload.org/).

Both Firefox and Chrome allow you to submit your domain to be preloaded into a built in HSTS list. Once this is set up, even the very first request to your domain (and any subdomains, if you configure that) will be automatically sent to `https://`. Nice.

One interesting bit that has developed on the HSTS preload lists though is that it's actually Chrome that maintains the 'core' HSTS preload list. Firefox and [the Tor project](https://www.torproject.org/) both derive their lists from Chrome's. Which leads us to the weird gotcha that I ran into recently: in order for Firefox to preload a domain, it has to be present in Chrome's list and it has to return the HSTS header (with a sufficiently long TTL). Pretty straight forward, no?

```bash
$ curl -I 'https://example.com'

HTTP/2 301
date: ...
content-type: text/html; charset=iso-8859-1
location: https://www.example.com/
server: Apache
```

Hmm. So the problem is that we have a redirect on the bare domain that redirects to `www`. We can fix that in the Apache configs.

```apache
<IfModule headers_module>
header set Strict-Transport-Security "max-age=16070400; includeSubDomains;"
</IfModule>
```

Reload and we should be good to go.

```bash
$ curl -I 'https://example.com'

HTTP/2 301
date: ...
content-type: text/html; charset=iso-8859-1
location: https://www.example.com/
server: Apache
```

Hmm. That didn't work as well as I would have hoped. Did a bit more reading and it turns out that Apache won't actually set headers on non-2XX responses by default. You need to specify an additional option:

```apache
# Use 'always' so headers are also set for non-2XX
<IfModule headers_module>
	header always set Strict-Transport-Security "max-age=16070400; includeSubDomains;"
</IfModule>
```

Try again:

```bash
$ curl -I 'https://example.com'

HTTP/2 301
date: ...
content-type: text/html; charset=iso-8859-1
location: https://www.example.com/
server: Apache
strict-transport-security: max-age=16070400; includeSubDomains;
```

That's exactly what I was looking for. But now we have another problem. The application itself is actually still configured to send the HSTS header on normal requests that make it past the Apache layer. So when I make a normal request:

```bash
$ curl -I 'https://www.example.com'

HTTP/2 200
date: ...
content-type: text/html
server: Apache
strict-transport-security: max-age=16070400; includeSubDomains
strict-transport-security: max-age=16070400; includeSubDomains;
...
```

Which isn't exactly the end of the world, but I'd rather it be a bit cleaner. Enter `unset`:

```apache
# Use 'always' so headers are also set for non-2XX and unset to avoid duplicates
<IfModule headers_module>
	header unset Strict-Transport-Security
	header always set Strict-Transport-Security "max-age=16070400; includeSubDomains;"
</IfModule>
```

This will first remove the old header the application is setting and then add one of our own.

One more try:

```bash
$ curl -I 'https://www.example.com'

HTTP/2 200
date: ...
content-type: text/html
server: Apache
strict-transport-security: max-age=16070400; includeSubDomains;
...
```

Golden. One final downside is that we also still send the header over `http://`, but it doesn't actually hurt anything to do this, it will just be ignored. But the entire point is to properly configured preload lists, so I'm not overly concerned.

[^1]: Long blog post for what amounts to two config lines. But it took me a bit of Google-fu to figure out why it wasn't working in the first place, so if this saves even one person the time it took me, it will be worth it.
