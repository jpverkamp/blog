---
title: Creating a temporary SMTP server to 'catch' domain validation emails
date: 2018-07-09
programming/languages:
- Bash
- Python
programming/topics:
- Command Line
- DNS
- Email
- SMTP
---
One problem that has come up a time or two is dealing with email-based domain validation (specifically in this case for the issuance of TLS certificates) on domains that aren't actually configured to receive email. Yes, in a perfect world, it would be easier to switch to DNS-based validation (since we have to have control of the DNS for the domain, we need it later), but let's just assume that's not an option. So, how do we 'catch' the activation email so we can prove we can receive email on that domain?

<!--more-->

Basic plan of attack:

- Set up or otherwise have a server with a public IP that we can run python on
- Run Python's built in SMTP server to catch emails
- Change DNS so that emails sent to the given domain will go to that server
- Capture the activation email, use the link to validate our domain

# Set up a server with a public IP

I'm going to skip over this case, since it depends on your specific setup. In our case, we're based in AWS, so I just requested a new `t2.nano` in a public part of our VPC.

# Run Python's built in SMTP server to catch emails

For this part, we could instead have run something more heavyweight--a full SMTP server. But that's exactly what I'm trying to avoid. I've had to configure those before, it's not the hardest thing I've ever done, but there are more than enough fiddly bits that I don't want to mess with them. Especially when running the debug server is so easy:

```bash
sudo python -m smtpd -n -c DebuggingServer 0.0.0.0:25
```

Since we're binding to port 25 (the standard SMTP port), we do need `sudo` (or to otherwise have root permissions). In theory, we could route a different port at a different level, but for that you'd need to have elevated permissions in AWS (or whatever system you're using), so somewhere you're going to just have to assume you have elevated permissions.

And that's it. You now have a working SMTP server.

# [optional] Test that the SMTP server is working

You can test it with TELNET in another prompt (on another machine):

```bash
$ telnet {ip} 25

> MAIL FROM:{your email address, does not actually matter}
< 250 Ok
> RCPT TO:webmaster@{domain}
< 250 Ok
> DATA
> Hello world
> .
< 250 Ok
```

If you go back to the still open terminal running the debug SMTP server, you should see the message you just sent in the console:

```bash
---------- MESSAGE FOLLOWS ----------
Hello world
------------ END MESSAGE ------------
```

One downside, it only writes to standard out. If you want to assume you'll only get a few messages (the activation emails), this is fine. But if you manage to get any spam (and eventually you will), it might be more handy to send the output to a file as well. Normally, you could just use `tee`, but it seems that this particular library buffers output fairly agressively. No problem. `stdbuf` to the rescue!

```bash
sudo stdbuf -oL python -m smtpd -n -c DebuggingServer 0.0.0.0:25 | tee mail.log
```

# Update/create DNS records

Now that we have the new SMTP server, we have to tell the world that it can receive email on behalf of our domain. To do that, we need to create a pair of DNS records:

```text
MX {domain} 10 smtp.{domain}
A smtp.{domain} {ip}
```

'Why can't you just put the IP address directly in the `MX` record?' you might say. Well, it turns out that the powers that be that set up DNS decided that MX records should resolve to a name and be independent of IPs directly. So they're almost always paired with an `A` or `CNAME` (and then an `A`) record.

# [optional] Verify that the DNS is set up correctly

In order to make sure that the DNS changes are propagating correctly, you can test at the command line with `dig`:

```bash
$ dig {domain} MX +short
10 smtp.{domain}.

$ dig smtp.{domain} +short
{IP}
```

If you're really thorough, you could also `telnet` again here, this time to the new domain name `smtp.{domain}` or even send a test email using your everyday email client. Couldn't hurt. Everything is set up so that could work now.

# Catch the validation email

Now that email is set up, all that's left is to tell whatever system you're trying to validate your domain to that they should (re)send validation email. It's possible it was waiting to be sent (it was in my case), but if you resend, it should show up more quickly. Then watch the logs on the debug server to see it arrive. You may have to scroll up past an HTML formatted section, but most validation emails should have both an HTML section and a plain text section. Copy that link and you're golden.

And that's it. Validation email without having to configure a 'real' SMTP server. You definitely want to clean up when you're done, removing the new DNS entries, shutting down the server, and (optionally) shutting down the instance that was running it. It's a debug server. Not the sort of thing you want to leave exposed to the public internet. And if you need it again in a year's time to validate the domain again... well, come right on back to this post. :smile:
