---
title: Forcing Secure Cookies Behind an ELB in Ruby/Rails
date: 2019-04-30
programming/topics:
- Security
- AWS
- ELB
programming/languages:
- Ruby
---
As part of general security good practices, you should always (whenever possible):

- use HTTPS to serve all requests
- serve redirects to upgrade HTTP requests to HTTPS
- set session cookies to `secure` and `http_only`
- enable HTTP Strict Transport Security (`HSTS`)

<!--more-->

If you're writing a Ruby on Rails app, a great way to do all of this is with the [https://github.com/tobmatth/rack-ssl-enforcer](Rack::SslEnforcer) gem. For the most part, it works without issues. Install as a gem and include it in your app:

```ruby
require 'rack/ssl-enforcer'
use Rack::SslEnforcer

...

config.middleware.insert_before  ActionDispatch::Cookies, Rack::SslEnforcer
```

However, if you're hosted on AWS behind an ELB (or any other situation where you have a load balancer that's handling TCP termination for you), you may have issues convincing `SslEnforcer` that you are in fact part of a secure connection (since it will receive the request from the load balancer as HTTP) while at the same time allowing local development over HTTP. To deal with that, you can use the `ignore` option to check if the forward protocal (from the load balancer) is set and not if you're local:

```ruby
# Force HTTPS + HSTS + secure cookies when behind an ELB
config.middleware.insert_before 0, Rack::SslEnforcer, ignore: lambda { |request| request.env["HTTP_X_FORWARDED_PROTO"].blank? }, :hsts => true
```

There's something to be said for a solid ecosystem. 