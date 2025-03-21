---
title: Setting up Postfix and OpenDKIM
date: 2015-08-10
programming/topics:
- Cryptography
- Email
- Public-key cryptography
---
Last week, I was presented with a fairly interesting challenge: add DKIM (via <a href="http://www.opendkim.org/">OpenDKIM</a>) support to our mail servers (running <a href="http://www.postfix.org/">Postfix</a>). Given that I've never actually worked on a mail server before, it sounded fun. :smile:

<!--more-->

First, a bit of background on what exactly DKIM is:


> DomainKeys Identified Mail (DKIM) is an email validation system designed to detect email spoofing by providing a mechanism to allow receiving mail exchangers to check that incoming mail from a domain is authorized by that domain's administrators and that the email (including attachments) has not been modified during transport. A digital signature included with the message can be validated by the recipient using the signer's public key published in the DNS.
> -- Wikipedia: [[wiki:DKIM]]()


Sounds nice. So what in the world does that mean?

## A bit of background

Starting in the details, we have [[wiki:public key cryptography]](). The basic idea of public key cryptography is that you have some sort of algorithm with two keys: one of which can be used to encrypt things and can be made public and another separate piece of information which can be used to decrypt things and should remain private. That way, you can publish your public key, well, publically. Then anyone that wants to send you a message can do so, knowing that only you (since only you possess the private key) can read it.

If we take this a step further, we can swap the roles of the public and private key[^1]. Instead of encrypting with the public key, we will use the private key, requiring the *public* key for decryption. This sounds mad, since the public key is, by definition public. So what's the point of a message that only you can write but anyone can read?

Well, that's exactly the point: *only you* can write it. This is what's called a digital signature. Since only your private key could have encoded the message and since only you have the private key, this allows anyone to read your message and be safe in the knowledge that you wrote it.

This is exactly what DKIM does.

By creating an public/private key pair, publishing the public key to a DNS record, and using the private key to sign messages, you are allowing any receiver to verify that *you* were person who sent them. Don't get me wrong, there are still a few problems with this approach (we'll get to them later), but it's a cool idea.

## Implementation

So how do you actually implement it in practice?

Given that I don't have any particular previous experience with mail servers, the answer involves a lot of Google. Here are the steps that worked for me.

####  - Have a previously configured server correctly delivering mail via <a href="http://www.postfix.org/">Postfix</a>

####  - Install <a href="http://www.opendkim.org/">OpenDKIM</a>

```bash
sudo apt-get install -y opendkim opendkim-tools
```

####  - Generate a new keypair

```bash
sudo opendkim-genkey -s mail -d example.com
```

The `-s` argument specifies a selector, which allows us to have multiple keypairs specified on the same domain (if we wanted to), while the `-d` is the domain we are signing for. In this case, we are generating a record for `mail._domainkey.example.com`.

This will generate two files. The first is `mail.private`, which we will move to `/etc/opendkim/keys/example.com.private` (to match the `KeyFile` later). Also, we need to make sure that the file has correctly narrow Unix permissions, or OpenDKIM will refuse to use it (for our own safety):

```bash
sudo chmod 0400 /etc/opendkim/keys/example.com.private
sudo chown opendkim:opendkim /etc/opendkim/keys/example.com.private
sudo adduser postfix opendkim
```

The second file is `mail.txt`, which is a DNS record for the above domain. Set it up so this returns successfully:

```bash
$ dig mail._domainkey.example.com TXT

...
;; ANSWER SECTION:
mail._domainkey.example.com. 599	IN TXT "v=DKIM1; k=rsa; p=MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC5N3lnvvrYgPCRSoqn+awTpE+iGYcKBPpo8HHbcFfCIIV10Hwo4PhCoGZSaKVHOjDm4yefKXhQjM7iKzEPuBatE7O47hAx1CJpNuIdLxhILSbEmbMxJrJAG0HZVn8z6EAoOHZNaPHmK2h4UUrjOG8zA5BHfzJf7tGwI+K619fFUwIDAQAB" ; ----- DKIM key mail for example.com
...
```

That's (almost) all we have to do to configure the public half of the key pair. (We still have to use the same selector later in the `KeyFile`, but that's it.)

####  - Create an OpenDKIM configuration file (`/etc/opendkim.conf`)

```bash
Canonicalization        relaxed/relaxed
ExternalIgnoreList      refile:/etc/opendkim/TrustedHosts
InternalHosts           refile:/etc/opendkim/TrustedHosts
KeyTable                refile:/etc/opendkim/KeyTable
LogWhy                  Yes
MinimumKeyBits          1024
Mode                    sv
PidFile                 /var/run/opendkim/opendkim.pid
SigningTable            refile:/etc/opendkim/SigningTable
Socket                  inet:8891@localhost
Syslog                  Yes
SyslogSuccess           Yes
UMask                   022
UserID                  opendkim:opendkim
```

What in the world do those all mean? Well, (based somewhat on documentation and somewhat on expirimentation):


* `Canonicalization` - controls whether further mail servers can edit the message contents with destroying the signature. `relaxed` allows more modification, `simple` is more strict. `relaxed` seems to be the more common option.
* `ExternalIgnoreList` - hosts that we trust to send us mail; do not validate their DKIM signatures (if present). Specifying `refile` means that we can use wildcards.
* `InternalHosts` - hosts that will relay mail through us; if we see an unsigned message coming from one of them, sign it before forwarding it along (This is important! I'll get to why in a bit)
* `KeyTable` - a list of private keys we can use to sign messages (included later)
* `LogWhy` - log errors to `/var/log/mail.log` (useful for debugging)
* `MinimumKeyBits` - flag an error if we try to specify a private key shorter (less secure) than this
* `Mode` - various options, `sv` is fairly common and means `s`ign outgoing messages and `v`erify incoming ones
* `PidFile` - where to store the [[wiki:PID file]]()
* `SigningTable` - specify which key from the `KeyTable` should be used for a given message
* `Socket` - how Postfix and OpenDKIM communicate
* `Syslog`, `SyslogSuccess` - log to [[wiki:syslog]]() as well as `mail.log`; log successes as well as failures
* `UMask` - allows other Linux users (such as Postfix's) to talk to OpenDKIM
* `UserID` - the user that OpenDKIM runs as


Fairly straight forward.

####  - Next, another copy of the socket definition in `/etc/default/opendkim` (I'm actually not sure why this one is necessary)

```bash
SOCKET="inet:8891@localhost"
```

Next, specify our keys in `/etc/opendkim/KeyTable`:

```bash
example.com example.com:mail:/etc/opendkim/keys/example.com.private
```

The first entry is a name for the key. It can be anything and doesn't necessary have to match the domain, just so long as the corresponding entry in `SigningTable` matches. After that, you have the domain where your public key is hosted, the selector on that domain, and where the private key is locally located. So in the above example, `example.com:mail` corresponds to a key at `mail._domainkey.example.com`.

And what emails to sign in `/etc/opendkim/SigningTable`:

```bash
*@example.com example.com
*@*.example.com example.com
*@*.example.org example.com
```

This one is a bit more complicated, since for my particular case, I had emails coming from two different domains, along with subdomains in both cases (the first field). They can (and in this case) all use the same key, since the second entry matches the value specified in `KeyTable`.

Note again: Since we're using wildcards here, we have to specify `refile` up above in `opendkim.conf`.

####  - Next, `/etc/opendkim/TrustedHosts`

This file will be used to specify both incoming message we trust and outgoing message we will sign (although it doesn't have to do both).

```bash
127.0.0.1
10.77.0.0/16
example.com
*.example.com
*.example.org
*.*.example.org
```

Entries here can be either IP addresses, [[wiki:CIDR]]() style IP ranges, or hostnames (including wildcards, since this is a `refile`), all of which I use above. This actually took a bit to figure out, since originally I was signing email directly from the box (successfully), but when I attempted to actually send a signed email from the product, it didn't work (since the frontends relay mail to the mail servers).

####  - Okay, that's enough to configure OpenDKIM. Next, we need to tell Postfix to talk to it

This one is relatively straight forward as well. Just add a few lines to the bottom of `/etc/postfix/main.cf`:

```bash
# DKIM
milter_default_action = accept
milter_protocol = 2
smtpd_milters = inet:localhost:8891
non_smtpd_milters = inet:localhost:8891
```

Essentially, milter is a protocol Postfix uses for plugins. We want to configure all mail traffic (both from smptd and not) to go to OpenDKIM, via the port we specified (twice) earlier. Shiny.

####  - Finally, restart both OpenDKIM and Postfix, so they can take advantage of their new settings

```bash
sudo service opendkim restart
sudo service postfix restart
```

This should only take a few seconds.

And that's it. We can send a test email:

```bash
echo "test email" | mail -s `hostname` me@example.com
```

That will send an email with the `hostname` of the current machine to the specified address, useful if you're working with multiple different machines and need to know which are up to date.

Check the message headers and you should see a block that looks like this:

```bash
DKIM-Signature: v=1; a=rsa-sha256; c=relaxed/relaxed; d=example.com; s=mail;
	t=1439063676; bh=RnRlt9pNo9HfghopMAD1V157IZOFVrE6piv9xdXYFNs=;
	h=To:Subject:Reply-To:From:Date;
	b=LekoRRQgOX97WUHP/ELtl/yhMzZsiCPr8kqaYUpZER5sYZ1dyAwgOKKvuI3mL3IMo
	 4Y90NDGv+CHm2ZmAaGmFOgGnDPsDxLE+ptleVBP/cQny9grftwA8Emc3MKS6aJ/w5P
	 E1bh2wFE8LiRTl/wcof6JL0MyeoR8R63FCKMgnA8=
```

Bam.

## A few caveats

So, what is DKIM actually used for?

The original claim is that it's an *email validation system designed to detect email spoofing*. Which is all well and good, but there's one big problem: adaptation.

Numbers are a little hard to come by, but one site that I found is builtWith trends: <a href="https://trends.builtwith.com/mx/DKIM">DKIM Usage Statistics</a>. Their reported coverage notes:


* Quantcast Top 10k - 14 of 10,000
* Quantcast Top 100k - 104 of 100,000
* Quantcast Top Million - 585 of 865,105
* Entire Internet - 24,064 of 328,844,222


That's less than 0.1% in any category. Not so great.

This is a problem, not because it means that mail servers aren't using it, but rather because there is little reason for mail *clients* to support it. It's easy enough to verify a DKIM signature if present, but they're so rarely present, that most will not go through that effort.

Furthmore, the header does not sign the message headers and (unless you are using SMTP over TLS), it is trivial to remove. If the DKIM header is not present, the message is trivial to modify with the recipient none the wiser. This could be offset--for some business models--by requiring messages to contain a DKIM header and rejecting those that don't.

Still, it's an interesting technology and there's no particular harm (other than a small amount of extra CPU effort to do the signing) in implementing it.

[^1]: If I understand, all of the public key systems in general use have this property, although they don't strictly speaking have to.