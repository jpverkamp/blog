---
title: SSRF Protection in Rails
date: 2020-06-30
programming/topics:
- Websites
- Security
- Rails
- DNS
- SSRF
programming/languages:
- Ruby
---
One of the more subtle bugs that a lot of companies miss is Server Side Request Forgery (SSRF). Like it's cousin CSRF (cross-site request forgery), SSRF involves carefully crafting a request that runs in a way that the original developers didn't expect to do things that shouldn't be done. In the case of CSRF, one site is making a request on behalf of another in a user's browser (cross-site), but in SSRF, a request is being made by a server on behalf of a client, but you can trick it into making a request that wasn't intended.

For a perhaps more obvious example, consider a website with a service that will render webpages as preview images--consider sharing links on a social network. A user makes a request such as `/render?url=https://www.google.com`. This goes to the server, which will then fetch https://www.google.com, render the page to a screenshot, and then return that as a thumbnail.

This seems like rather useful functionality, but what if instead, the user gives the url: `/render?url=https://secret-internal-site.company.com`. Normally, `company.com` would be an internal only domain that cannot be viewed by users, but in this case--the server is within the corporate network. Off the server goes, helpfully taking and returning a screenshot. Another option--if you're hosted on AWS--is the AWS [metadata endpoint](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-instance-metadata.html): `http://169.254.169.254/latest/meta-data/`. All sorts of interesting private things there. Or even more insidious, `/render?url=file:///etc/password`. That shouldn't work in most cases, since most libraries know better than to rener `file://` protocol URLs, but... not always!

<!--more-->

# Fix version 1: ssrf_filter

The easiest general solution to many problems is--don't solve the problem. Until you get deep into the weeks (which SSRF is not), someone has already solved the problem. 

In this case, I was working in a [Ruby on Rails](https://rubyonrails.org/) codebase, so the top answer is: [ssrf_filter](https://github.com/arkadiyt/ssrf_filter). It's actually pretty much just a direct drop in for the built in `open` functionality:

```ruby
require 'ssrf_filter'
response = SsrfFilter.get(params[:url]) # throws an exception for unsafe fetches
response.code
=> "200"
response.body
=> "<!doctype html>\n<html>\n<head>\n..."
```

And that's it. If the page is internal (such as the AWS metadata URL above, `file://` protocol, or even IPs in a [[wiki:private network]]()), `ssrf_filter` will refuse to load the page and throw an `Ssrf:Filter::Error`.

That's it. Trivial, no? 

# But it's not perfect

Well. No. Of course it isn't. 

It turns out that depending on exactly what you're doing with `ssrf_filter`, it can be bypassed. Now, this isn't actually a problem with the library, but rather in what you're doing with it. Instead of directly trying to fetch `https://secret-internal-site.company.com`, instead host a simple HTML document on your own server (anywhere as long as it's public):

```html
<script>document.location = "https://secret-internal-site.company.com"</script>
```

All this does is load the original site (bypassing `ssrf_filter`) and then instruct the page to use JavaScript to perform a redirect. If you're not rendering JavaScript (which the most basic thumbnail software would not be), this isn't a problem. But in modern websites, that isn't really an option. There are whole swaths of the internet that will not render without at least minimal JavaScript enabled. 

So now we have a problem: do we turn off JavaScript rendering? or do we try to make sure that even if the page redirects, we can still prevent SSRF?

(Side note: Making your server return an `HTTP 3xx redirect` will not bypass `ssrf_filter`, it automatically follows and allows/blocks those as expected). 

# Fix version 2: iptables

Okay, we tried to solve it at the network level, but now it's time to bring out the big guns. [[wiki:iptables]]()

In a nutshell, it's a Linux kernel level firewall. It allows you to do cool things like this:

```bash
iptables -N APP_FIREWALL
iptables -A APP_FIREWALL -d 169.254.169.254 -j DROP
iptables -A APP_FIREWALL -p tcp -d 10.0.0.0/8 -m multiport --dports http,https -j DROP
iptables -I FORWARD -i docker0 -j APP_FIREWALL
```

That required some testing, but essentially what we're doing is:

- Create a `N`ew `iptables` rule
- `A`ppend a rule to it that any packets to the `d`estination `169.254.169.254` should be `DROP`ed
- `A`ppend a rule that any `tcp` connections to the private subnet `10.0.0.0/8` from any port over `http` or `https` should be `DROP`ed
- `I`nsert a `FORWARD`ing rule that the subnet `docker0` should hand traffic over to the new `APP_FIREWALL` rules

This does exactly what we need. Any traffic that's coming from docker (I'll come back to that in a moment) cannot go to the metadata IP or a `10.*` IP. No matter how you do it, be it a direct request, an HTTP redirect, or a JavaScript redirect. All such traffic will be dropped and will then timeout.

So, back to [Docker](https://www.docker.com/): this solution is for the moment specific to Docker. I really do like what containers do for you, be the Docker or any of other solutions that have cropped up since. They let you run a reproducible image on a variety of systems without having to worry about what's installed or leaving behind state that might break other systems. In this case, the Docker process already sets up it's own `iptables` network: `docker0`. So that's why I'm appending to that. If you didn't have Docker, you could do much the same thing for `10.*` IPs, but outright blocking all traffic to `169.254.169.254` may break AWS specific services. Your milage may vary. 

All together though, it works. At least I haven't been able to get through this with any of the SSRF tricks I know. Of course, when you're working in security: you have to fix everything, but they only have to break one thing...

# Summary

So what have we learned? 

Well, attackers are tricky. Any way that they can convince a server to do something it's not supposed to is a way that you can leverage an attack. In this case, making a server request resources that it can access that the user shouldn't be able to see. It's often possible to fix such problems with a built in library (and that's a good start), but... sometimes you need to go a level deeper. 

Also, `iptables` are cool. I should look more into that. Before solving this particular problem, I had little experience with `iptables`, but a few hours of reading documentation, searching for examples, and fiddling with settings and I had something functional. A few more and I thought I understood the system well enough that I could probably put something more powerful into place. 