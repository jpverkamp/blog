---
title: Rack::Cors Configuration Tricks
date: 2020-01-16
programming/topics:
- Security
- CORS
programming/languages:
- Ruby
---
<a href="https://github.com/cyu/rack-cors">cyu's Rack::Cors middleware</a> is rather handy if want to control your {{< wikipedia "CORS" >}} (Cross-Origin Resource Sharing) settings in a Ruby-on-Rails project. Previously, there was a fairly major issue where `:credentials => true` was the default (which you generally do not want), but there were also some more complicated tweaks that I wanted to make. 

One problem I recently had to deal with was wanting to:

- Allow CORS connections from arbitrary domains (this site functions as an API)
- Do not allow CORS from http domains at all
- Only allow cookies (`Access-Control-Allow-Credentials`) to be sent for sibling subdomains
- Prevent cookies from being sent from specific sibling subdomains (that are actually run by a third party)
- On development (non-production) versions of the site, allow credentials from localhost

<!--more-->

In short, here is the rough configuration:

```ruby
# The main domain, this might be different per environment
domain = 'example.com'

# These subdomains are not trusted and should not be allowed to authenticate with cookies
cors_third_party_subdomains = [
    'blog',
    'shop',
    'support'
].join('|')

# These are the Rack::Cors settings that we want to set, first for all domains and then for trusted ones
cors_headers = {
    :headers => :any,
    :methods => [:get, :post, :put, :delete, :options, :patch],
    :expose => %w(Link),
    :credentials => false
}
cors_headers_internal = cors_headers.merge({:credentials => true})

# This is the actual Rack::Cors configuration
config.middleware.insert_before 0, Rack::Cors do
    # Third party subdomains should not get cookies in case of XSS
    allow do
        origins /^https:\/\/(#{cors_third_party_subdomains})\.#{domain}$/
        resource '*', cors_headers
    end

    # We only want allow-credentials to be true for our own requests
    # Otherwise you'll need to supply or other non-cookie credentials
    allow do
    origins /^https:\/\/(|[^.]+\.)#{domain}$/
    resource '*', cors_headers_internal
    end

    # All other requests made over https allow CORS without credentials
    allow do
    origins /^https:\/\//
    resource '*', cors_headers
    end

    # Allow connections from localhost on non-prod environments as internal requests
    unless Rails.env.production?
        allow do
            origins /^(https?:\/\/)?localhost(:\d+)?$/
            resource '*', cors_headers_internal
        end
    end
end
```

I'm sure there are other ways to deal with this, but I spent a little whiel working on it and finally got just what I wanted. 

A few gotchas to keep in mind:

- You need to make sure to specify the entire origin to prevent suffix attacks (such as `example.com.evil.com`). 
- You also should specific the scheme to prevent downgrade attacks. 
- You should turn off `credentials` for any domain you don't trust.

Give it a try. 