---
title: "Free\xB2 HTTPS blog hosting via GitHub and CloudFlare"
date: 2015-12-07
---
The eagle-eyed among you[^1] may have noticed something a bit different since last night:

{{< figure src="https.png" >}}

That's right, I'm finally using HTTPS!

<!--more-->

Coming on the heels of the <a href="https://letsencrypt.org/">Let's Encrypt</a> public beta, you might think I'm using that. If I were running this blog on my own servers, I probably would be. But since I'm actually (for the moment) using <a href="https://pages.github.com/">GitHub pages</a>, that's not actually the case. I'm actually using <a href="https://www.cloudflare.com/">CloudFlare's</a> free[^2] tier.

Basically, here is my tech stack:

Source files are written in Markdown(ish) stored in a GitHub git repo: <a href="https://github.com/jpverkamp/blog">github:jpverkamp/blog</a>
	
Source files are translated into static HTML via my custom blog generator: <a href="https://github.com/jpverkamp/blog-generator">github:jpverkamp/blog-generator</a>[^3]</li>

Files are deployed to a GitHub pages repo: <a href="https://github.com/jpverkamp/jpverkamp.github.io">github:jpverkamp/jpverkamp.github.io</a>, which you used to be able to directly access in the browser at <a href="http://jpverkamp.github.io">jpverkamp.github.io</a>[^4]

CloudFlare handles my DNS, with a [[wiki:CNAME]]() directing `blog.jverkamp.com` to `jpverkamp.github.io`:

{{< figure src="/embeds/2015/cloudflare-options.png" >}}

A custom Page Rule tells CloudFlare to automatically redirect incoming HTTP traffic to HTTPS:

{{< figure src="/embeds/2015/cloudflare-page-rule.png" >}}

In order to ease this transaction, I changed my config file so that all internal links to my own blog now use a relative protocol: `//blog.jverkamp.com`

And... that's it. 

I only had one hiccup transferring my DNS entries to CloudFlare (it missed email records on a subdomain), but other than that it was rather easy to set up. 

If you haven't given it a try, check it out! Between CloudFlare and now Let's Encrypt, there's really no good reason you shouldn't be encrypting just about everything.

[^1]: I would be surprised if anyone actually noticed; it's a blog.
[^2]: [[wiki:TINSTAAFL]](). I'm already very near the capacity of their free tier. But for the moment, it works.
[^3]: I'm getting that itch to completely rewrite it again though...
[^4]: This is no longer possible because of the automatic protocol upgrade CloudFlare does.