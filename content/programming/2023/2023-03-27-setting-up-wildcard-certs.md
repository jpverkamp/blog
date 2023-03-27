---
title: "Wildcard Let's Encrypt certificates with Nginx Proxy Manager and Cloudflare"
date: '2023-03-27 00:02:00'
programming/topics:
- Nginx
- SSL
- TLS
- HTTPS
- Cloudflare
---
Another quick snippet that I figured out this weekend. It's not hard, but it's something that I really wanted to do and had to look up where it was, so perhaps it will help you.

Problem statement: 

I run a bunch of local services in my network. They aren't exposed publicly (I use Wireguard to access them when out and about), so I really don't *need* HTTPS. But (rightfully) a number of services behave better when they're behind HTTPS + if there's ever a service that's running amuck (Internet of Things devices?) that's listening, I don't want them to see anything. 

{{<toc>}}

## Options

Option 1: Use Nginx Proxy Manager to request certificates for each subdomain. It works quickly and well. Problem: All certificates are published to Certificate Transparency Logs. I don't immediately mind exposing what I'm running... but I'd still rather now. 

Option 2: Set up wildcard certificates. This requires integration with your DNS provider (since wildcards need a DNS challenge, not TCP). 

Of course (based on the title), we're going with option 2. :smile:

<!--more-->

Here's how you do it. 

## Start adding the certificate

In nginx proxy manager, go to `/nginx/certificates` and `Add Certificate`:

{{< figure src="/embeds/2023/wildcard-request-cert.png" >}}

You want to set up the domain name as the wildcard (subdomains of `home.jverkamp.com`) for me. Then select 'Use DNS challenge' + set up your provider. I use Cloudflare. 

## Generate a Cloudflare API token

In Cloudflare, click on a Domain, then under 'Quick Actions' on the right, all the way at the bottom, you can find [get an API token](https://dash.cloudflare.com/profile/api-tokens). Create a new token. The 'Edit zone DNS' template will do what you want:

{{< figure src="/embeds/2023/wildcard-cloudflare.png" >}}

You do need to specify which zone(s) you are setting this up for. Create token and copy it into the nginx proxy manager dialog above. 

Click 'Save' and wait a minute or two. It takes a moment for the DNS to propagate. 

Voila. You have a wildcard DNS cert that will automatically be renewed for you. 

## Change your proxy host to use it.

As an example (this domain isn't actually hosted externally any more):

{{< figure src="/embeds/2023/wildcard-edit-host.png" >}}

And on the SSL tab:

{{< figure src="/embeds/2023/wildcard-edit-ssl.png" >}}

And that's all there is to it. 

Hope that helps someone!