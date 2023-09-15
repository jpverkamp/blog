---
title: Scanning for DNS resolvers
date: 2013-01-31 14:00:00
programming/languages:
- Python
programming/topics:
- Censorship
- DNS
- Networks
- Security
---
For a research project I'm working on, it has become necessary to scan potentially large [[wiki:Cidr|IPv4 prefixes]]() in order to find any [[wiki:DNS resolver|DNS revolvers]]() that I can and classify them as either open (accepting queries from anyone) or closed.

Disclaimer: This is a form of [[wiki:port scanning]]() and thus has associated ethical and legal considerations. Use it at your own risk. 

This project is available on GitHub: <a href="https://github.com/jpverkamp/dnsscan" title="GitHub: jpverkamp: dnsscan">jpverkamp/dnsscan</a>

<!--more-->

The idea is pretty simple. I want to be able to do something like this:

```css
$ ./dnsscan.py 8.8.4.4/30    

8.8.4.4,open
```

(8.8.4.4 is one of <a href="https://developers.google.com/speed/public-dns/" title="Google Public DNS">Google's Public DNS</a> servers.)

What do we need to do to get there? Well, most of the code is framework, parsing command line arguments and looping over IP prefixes. The interesting part comes down to using the <a href="http://www.dnspython.org/" title="dnspython home page">dnspython library</a> to make DNS requests to any arbitrary IP. 

It's not actually straightforward how to do that (by default dnspython will read your `/etc/resolv.conf` file), but digging a bit into the documentation, I found that you can change the `nameservers` property to get what I'm looking for. Something like this:

```python
resolver = dns.resolver.Resolver()
for ip in prefix_to_ips(prefix):
    resolver.nameservers = [ip]
    answers = resolver.query(target, 'A')
```

That way you will get all of the default configuration, but you can swap out nameservers.

After that, you have to process the response. Basically, there are three possible responses:


* You get an answer: this is an open resolver
* You contact the server, but it doesn't give you an IP: this is a resolver, but it's closed
* The connection times out: this isn't a resolver (or there's a firewall, etc)


I can process these to output what we need:

```python
for ip in prefix_to_ips(prefix):
    resolver.nameservers = [ip]

    # If we get an answer, it's open
    try:
        answers = resolver.query(target, 'A')
        print '%s,open' % (ip)

    # NoAnswer: Contacted a server but didn't get a valid response
    # NoNameservers: Couldn't get a valid answer from any of the nameservers
    # These probably mean it's closed
    except (dns.resolver.NoAnswer, dns.resolver.NoNameservers), ex:
        print '%s,closed' % (ip)

    # No response
    except dns.resolver.Timeout, ex:
        pass
```

And that's all there is to it. You can scan individual IPs or prefixes, set the target URL (in case of measuring censorship, which is my eventual goal), and change the timeout. I'm sure there are other features I could work on, but that's what I have for now.

This project is available on GitHub: <a href="https://github.com/jpverkamp/dnsscan" title="GitHub: jpverkamp: dnsscan">jpverkamp/dnsscan</a>

If you have any questions/comments/concerns, let me know below.