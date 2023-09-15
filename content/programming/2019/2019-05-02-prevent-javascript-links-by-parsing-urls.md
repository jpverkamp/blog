---
title: Prevent JavaScript links by parsing URLs
date: 2019-05-02
programming/topics:
- Security
programming/languages:
- Ruby
- JavaScript
- Python
- PHP
- Go
---
If you have a website that allows users to submit URLs, one of the (many many) things people will try to do to break your site is to submit URLs that use the `javascript:` protocol (rather than the more expected `http:` or `https:`). This is almost never something that you want, since it allows users to submit essentially arbitrary code that other users will run on click in the context of your domain ([[wiki:same origin policy]]()). 

So how do you fix it? 

First thought would be to try to check the protocol:

```javascript
> safe_url = (url) => !url.match(/^javascript:/)
[Function: safe_url]

> safe_url('http://www.example.com')
true

> safe_url('javascript:alert(1)')
false
```

<!--more-->

Unfortunately, that's easy enough to bypass:

```javascript
> safe_url('Javascript:alert(1)')
true
```

So we make the test case insensitive:

```javascript
> safe_url = (url) => !url.match(/^javascript/i)
[Function: safe_url]

> safe_url('Javascript:alert(1)')
false
```

But we can still bypass that (note the leading space):

```javascript
> safe_url(' javascript:alert(1)')
true
```

It turns out that most browsers are fairly accepting in trying to guess what a developer meant. They'll just trim off the space and run it. You can't just detect the word `javascript` anywhere though, since this is still perfectly runnable by browsers:

```javascript
> safe_url(' &#14;  javascript:alert(1)')
true
```

Long story short, there are a great many ways to bypass regular expression based filters. At least in my opinion, you're far better off not trying that way at all. Instead, use the built in functionality of your language to parse the URL and then use that to check the protocol. There are still a few gotchas (mostly in relative URLs if you want to allow those and protocol relative URLs starting with `//...`). How would you implement something like that?

```javascript
> new URL('javascript:alert(1)')
URL {
  href: 'javascript:alert(1)',
  origin: 'null',
  protocol: 'javascript:',
  username: '',
  password: '',
  host: '',
  hostname: '',
  port: '',
  pathname: 'alert(1)',
  search: '',
  searchParams: URLSearchParams {},
  hash: '' }
}

> safe_url = (url) => { u = new URL(url); return u.protocol == 'http:' || u.protocol == 'https:' }
[Function: safe_url]

> safe_url('http://www.example.com')
true

> safe_url('HTTPS://www.example.com')
true

> safe_url(' javascript://www.example.com')
false
```

Seems pretty good. Downside is that it blows up on protocol relative and relative URLs:

```javascript
> safe_url('//www.example.com')
Thrown:
{ TypeError [ERR_INVALID_URL]: Invalid URL: //www.example.com
    at onParseError (internal/url.js:241:17)
    at new URL (internal/url.js:319:5)
    at safe_url (repl:1:27) input: '//www.example.com' }
```

If you don't want to support those, that's fine. Otherwise, you might need another trick:

```javascript
> a = document.createElement('a')
<a>​</a>​

> a.href = 'javascript:alert(1)'
"javascript:alert(1)"

> a.protocol
"javascript:"

a.href = '//www.example.com'
"//www.example.com"

a.href = '/relative'
"/relative"
```

And in those cases, it will pick up the protocol (and host in the latter case) of the site you're running in. This may or may not (probably won't) work with server side JavaScript though. 

So, let's say you want to filter to only allow absolute URLs with `http` or `https` protocol. How do you do that in various languages?

JavaScript:

```javascript
function safe_url(url) {
    const a = document.createElement;
    a.href = url;
    return a.protocol == 'http' or a.protocol == 'https';
}
```

Ruby:

```ruby
def safe_url(url)
    begin
        parsed_url = URI.parse(url)
        return ['http', 'https'].include?(parsed_url).scheme)
    rescue URI::InvalidURIError
        return false
    end
end
```

Go:

```go
func safeUrl(url string) string {
    parsedURL, err := url.Parse(url)

    if err == nil {
        return false
    } 
    
    return parsedURL.Scheme == "http" || parsedURL.Scheme == "https";
}
```

PHP:

```php
# PHP
function safe_url($url) {
    $parsed = parse_url($url);
    return $parsed['scheme'] == 'http' or $parsed['scheme'] == 'https';
}
```

Python(3):

```python
def safeUrl(url):
    return urllib.parse.urlparse(url).scheme in ['http', 'https']
```

And believe it or not... I have used a (slightly more complicated) variation of each and every single one of those in production code. Sometimes you realize just how much of a programming polygot you have to be to do security work...

Fun times.
