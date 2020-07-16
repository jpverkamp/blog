---
title: An SPF DNS Server
date: 2020-07-16
programming/topics:
- Email
- SPF
- DMARC
- DNS
- Twistd
programming/languages:
- Python
---
The {{< wikipedia "Sender Policy Framework" >}} is one of those things that's really powerful and useful to help prevent phishing and email spam, but can be a royal pain to work with. Specifically, SPF is a series of DNS TXT records[^history] with a specific format that can be looked up by any email service to verify that an email was sent by a server that should be authorized to send email on your behalf. For example

```bash
"v=spf1 ip4:192.0.2.0/24 ip4:198.51.100.123 a -all"
```

* `v=spf1` - tells the client this is an SPF record and should always start the record
* `{key}[:{value}]?` - one of many different key/value pairs that can define the record
    * in the case above a `ip4` key species an {{< wikipedia IPv4 >}} address range that can send emails on your behalf (the value can be optional)
    * the `a` above is another special case where if the sender domain (`jp@example.com` would be `example.com`) resolves via a `DNS A` record to the server that sent the email, it's allows
* `-all` is a fallthrough case meaning 'fail all that didn't match a previous case

There are a number of other cases, but we'll get to the other interesting ones in a bit.

<!--more-->

# Backstory

For the basic case of sending your own email, this isn't a problem. Specify either `a` if your application servers directly send email (and aren't behind a load balancer) or specify the IP(s) of your servers and you're golden. But what if you want to allow others to send emails on your behalf? Either for marketing purposes or because you are working with a third party email sender. 

Well, then you're going to want `include:mail-sender.example.com` records. That means that you're telling the email client to go fetch the SPF configuration from `mail-sender.example.com` and include those IP ranges as ones that can send email for your domain. 

But what if that mail-sender includes other domains? And what if you have multiple third parties? 

Unfortunately, this will quickly get out of hand with many many recursive DNS lookups for every email received, so in their infinite wisdom[^igetit], SPF is limited to 10 recursive calls. So if you have more than that... what next? 

Well, that's where we get to the meat of this post!

# SPF Macros

Because it turns out that the powers that be also gave SPF a more powerful macro language built right into DNS that you can use for exactly something like this. You have to find a service that will do it for you--or write your own--but you can offload all of the work of recursively looking up these records into a single record:

```bash
"v=spf1 include:%{i}._ip.%{h}._ehlo.%{d}._spf.example.com -all"
```

What's this? MAGIC!

Well, macro. What that means is that when a server tries to validate an email from `example.com`, they will fill in the IP (`%{i}`), the SMTP EHLO response (`%{h}`), and the SPF domain (`%{d}`). There is actually a pretty intense list:

* `%{s}`: The email sender (`jp@example.com`)
* `%{l}`: The username (`jp`)
* `%{o}`: The domain (`example.com`)
* `%{d}`: The current SPF authority (usually equal to `%{o}`)
* `%{i}`: The source IP (`10.123.45.67`)
* `%{p}`: A reverse DNS lookup of the domain, if configured (using `PTR` records)
* `%{v}`: Either `in-addr` for IPv4 or `ip6` for IPv6
* `%{h}`: The domain given by SMTP when connecting in the `EHLO`/`HELO` message (`mail.example.com`)

The `_ip` parts are basically so that I can parse the DNS record on my end more easily, but you really could just do something like this: `%{i}._spf.example.com` and only process the IP. Or get far more complicated and do something like `%{l}.%{i}._spf.example.com` to validate that a specific email address should be able to send from a specific IP. The possilibities are endless[^endless]!

Given just this information though, we want to return a custom DNS record. So if eventually `10.123.45.67` (a legit server) should be able to send email and `10.76.54.321` (an attacker) should not, this should work:

```bash
$ dig 10.123.45.67._ip.mail.example.com._ehlo.mail.example.com._spf.example.com TXT +short

"v=spf1 ip4:10.123.45.67 -all"

$ dig 10.76.54.321._ip.mail.example.com._ehlo.mail.example.com._spf.example.com TXT +short

"v=spf1 -all"
```

Including anything that would normally be in an `include` record. 

Let's do it. 

# Building a list of IP addresses

So the first thing to do will be to take an existing list of SPF records and recursively parsing them ourselves in order to get a list of all IPs that we should respond to. We don't have to listen to the standard 10 query limit, which is sort of the entire point of this thing:

```python
def _parse_spf_value(record, domain = None):
    '''Parse a SPF record to get all matching IPs/domains'''

    logging.debug('parse_spf_value({}, {})'.format(record, domain))

    match = _spf_regex.match(str(record))
    if not match:
        logging.warning('Failed to parse: {}'.format(record))
        return

    # We don't care about the mode
    elif match.group('key') == 'all':
        return

    # Resolve a records for the domain
    elif match.group('key') == 'a':
        for response in _simple_dns(match.group('value') or domain, 'A'):
            yield ipaddress.ip_network(response)

    # Resolve mx records for the domain
    elif match.group('key') == 'mx':
        for response in _simple_dns(match.group('value') or domain, 'MX'):
            for subresponse in _simple_dns(response, 'A'):
                yield ipaddress.ip_network(subresponse)

    # Resolve ptr records for the domain
    elif match.group('key') == 'ptr':
        logging.warning('NOT IMPLEMENTED: {}'.format(record))

    # Check if a given domain resolves
    elif match.group('key') == 'exists':
        yield ExistsNetwork(match.group('value'))

    # Literal IP addresses/subnets
    elif match.group('key') in ('ip4', 'ip6'):
        yield ipaddress.ip_network(match.group('value'))

    # Recursive lookup
    elif match.group('key') in ('include', 'redirect'):
        for response in _simple_dns(match.group('value'), 'TXT'):
            if response.startswith('v=spf1'):
                for part in response.split()[1:]:
                    yield from _parse_spf_value(part, match.group('value'))

    else:
        raise Exception('Unknown SPF record format: {}'.format(record))
```

This is going to take in an SPF record and parse through all of the different types of values it could be. An `a` record says query the domain and get the IP. An `mx` record does the same with a DNS `MX` record. `ip4` and `ip6` map to DNS ranges, while I'll represent using the {{< doc python ipaddress >}} module. `include` and `redirect` are recursive cases, so grab the DNS (using `_simple_dns`, I'll be right back to that) and recursively parse that as well. 

For doing DNS, I'm going to use [dnspython](https://www.dnspython.org/docs/1.15.0/dns.resolver.Resolver-class.html) to resolve the query and then just return the body of any results. This works for `A` and `MX` records (get the IPs) and `include`/`redirect` (get the recursive SPF record). 

```python
def _simple_dns(domain, type):
    '''Return a list of just DNS values of the given type for the given domain.'''

    logging.debug('simple_dns({}, {})'.format(domain, type))

    try:
        query = dnspython_resolver.query(domain, type)
        for answer in query.response.answer:
            for line in answer.to_text().split('\n'):
                # Remove domain, TTL, 'IN', and type
                line = line.split(' ', 4)[-1].strip('"')
                yield line

    except dnspython_resolver.NXDOMAIN:
        logging.warning('{} query failed for: {}'.format(type, domain))
```

The last case is `exists` records / `ExistsNetwork`. This is basically an IP rule that we need to look up dynamically later:

```python
class ExistsNetwork(object):
    '''A custom 'network' which matches SPF exists records by querying them.'''

    def __init__(self, host):
        '''Initialize this network with the hostname to match.'''

        self._host = host

    def __contains__(self, ip):
        '''Check if a given IP address can be resolved by this rule.'''

        try:
            response = dnspython_resolver.query(self._host.replace('%{ip}', str(ip)), 'A')
            return True

        except dnspython_resolver.NXDOMAIN:
            return False
```

Okay, so we have all of the data. How what? 

# Making a DNS server

This really should be easier (and perhaps sometime I'll solve that very problem), but for the moment, I'm going to use [Python's Twisted](https://twistedmatrix.com/trac/) to make the server, since that's the one that I found enough documentation for to put together a simple server without writing the guts of the packets myself. 

```python
class SPFResolver(object):
    '''Resolve SPF macros to IP addresses.'''

    def __init__(self, hostname, internal_records = [], external_records = [], ttl = 300):
        '''Create an SPF resolver based on a given macro format.'''

        self._internal_records = internal_records
        self._external_records = external_records
        self._ttl = ttl

        # Expand/reformat the hostname to a regular expression
        for key, name in _spf_macros:
            hostname = hostname.replace('%{' + key + '}', '(?P<' + name + '>.*?)')
        self._hostname_regex = re.compile(hostname)

        self._cache = []
        self._cache_refreshed = 0
        self._refresh_cache()

    def _refresh_cache(self):
        '''Update the list of networks based on the config file.'''

        self._cache = [
            network
            for values in [self._internal_records, self._external_records]
            for value in values
            for network in _parse_spf_value(value)
        ]
        self._cache_refreshed = time.time()



    def query(self, query, timeout = None):
        '''Resolve SPF queries using this resolver.'''

        logging.debug('dns query received: {}'.format(query))

        # Check if this is actually our job
        name = query.name.name.decode()
        if query.type != dns.TXT or not self._hostname_regex.match(name):
            return defer.fail(error.DomainError())

        # Check if the network needs refreshed
        if self._cache_refreshed + self._ttl < time.time():
            self._refresh_cache()

        # Check the incoming record against all known records
        match = self._hostname_regex.match(name)
        logging.info('resolving {}: {}'.format(name, match.groups()))

        target_ip = ipaddress.ip_address(match.group('ip'))
        authority = additional = answer = []

        data = 'v=spf1 -all'
        for network in self._cache:
            if target_ip in network:
                data = 'v=spf1 ip{mode}:{ip} -all'.format(mode = target_ip.version, ip = target_ip)
                break

        answer = [dns.RRHeader(type = dns.TXT, name = name, payload = dns.Record_TXT(data.encode()))]
        logging.debug('dns response generated: {}'.format([answer, authority, additional]))

        return defer.succeed((answer, authority, additional))
```

What this will do is:

1. Parse the parameters from the query (get the IP we're looking for)
2. Make a function that can update the SPF list periodically without having to do it for every request
3. Respond to a DNS query with either a SPF pass for the IP or an SPF fail

Then we just have to hook it up to `twisted`:

```python
if __name__ == '__main__':

    spf_resolver = spf.SPFResolver(
        hostname = config.get('dns/hostname'),
        internal_records = config.get('spf/internal'),
        external_records = config.get('spf/external'),
        ttl = config.get('spf/ttl', 300),
    )

    factory = server.DNSServerFactory(
        clients = [spf_resolver]
    )

    protocol = dns.DNSDatagramProtocol(controller = factory)

    dns_port = config.get('dns/port', 53)

    reactor.listenUDP(dns_port, protocol)
    reactor.listenTCP(dns_port, factory)

    logging.info('Starting DNS server on port {}'.format(dns_port))
    reactor.run()
```

And that's really it. Now the queries as I showed above work great:

```bash
$ dig 10.123.45.67._ip.mail.example.com._ehlo.mail.example.com._spf.example.com TXT +short

"v=spf1 ip4:10.123.45.67 -all"

$ dig 10.76.54.321._ip.mail.example.com._ehlo.mail.example.com._spf.example.com TXT +short

"v=spf1 -all"
```

I've had something just like this running on a single small server for years without issue. It doesn't respond to arbitrary queries, so the attack surface of an open resolver isn't an issue, although I could probably use a bit of rate limiting just in case. But it's been working fine for a while.

Now, it's been a bit, so I'm probably going to rewrite this in another language (I'm thinking golang) half because it's interesting and half to tune what I missed the first time. But it's pretty cool to me!

# Appendix: A note on NS records

You may have noticed that I used `%{i}._spf.example.com` as my domain. This is because this is going to be the authoritative nameserver for any DNS queries for a specific subdomain (and all children subdomains). So if you tried to host it at `%{i}.example.com` and you also have a server at `api.example.com`, things will go badly for you (or you need to resolve those IPs yourself). Once you have it running though, just configure a DNS NS record to point `_spf.example.com NS {this server}` and you're golden. 

[^history]: Historically, there was a SPF DNS record type, but that has been replaced by the more general purpose TXT record. 

[^igetit]: I get it. You don't want to DDoS DNS servers for every email. It's still annoying. 

[^endless]: Barring the death of the universe and all that. Oh, and the maximum length of DNS queries. 