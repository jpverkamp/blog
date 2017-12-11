---
title: Backing up Google Reader / Calendar
date: 2012-09-05 14:00:30
programming/languages:
- Python
programming/topics:
- Backups
slug: backing-up-google-reader
---
Similar to my previous post about [backing up Gmail]({{< ref "2012-09-03-backing-up-gmail.md" >}}), this time I want to back up my [here](https://github.com/jpverkamp/small-projects/blob/master/scripts/backup-google-reader.py), from there it should be easy enough to derive the one for Google Calendar.

First, we have the same setup as last time. Yes, I'm still storing the passwords in plaintext. Perhaps I'll write up a way to avoid this in the future.

```python
#!/usr/bin/env python

import urllib, urllib2

username = '#####'
password = '#####'
```

For the next step, I'm going to fetch Google's login page using `urllib`. Note the `service` we're sending in the POST parameters. This tells Google what we want to access (Google Reader in this case).

```python
# Authenticate to obtain SID
auth_url = 'https://www.google.com/accounts/ClientLogin'
auth_req_data = urllib.urlencode({
    'Email': username,
    'Passwd': password,
    'service': 'reader'
})
auth_req = urllib2.Request(auth_url, data=auth_req_data)
auth_resp = urllib2.urlopen(auth_req)
auth_resp_content = auth_resp.read()
auth_resp_dict = dict(x.split('=') for x in auth_resp_content.split('\n') if x)
auth_token = auth_resp_dict["Auth"]
```

Using the token returned from Google, we can download any files that need the permission we requested earlier. If you'd rather work with Google Calendar, the service that you need is `'cl'`.

```python
# Create a cookie in the header using the SID
header = {}
header['Authorization'] = 'GoogleLogin auth=%s' % auth_token

reader_url = 'https://www.google.com/reader/subscriptions/export?hl=en'
reader_req = urllib2.Request(reader_url, None, header)
reader_resp = urllib2.urlopen(reader_req)
reader_resp_content = reader_resp.read()

print reader_resp_content
```

And that's it. With those we'll get an XML file that contains all of your current subscriptions. In my case, that's being backed with all of the rest of my files. Again, it shouldn't ever be necessary to have to use these, but better safe than sorry (particularly with 240 individual URLs). If you'd rather get your Google Calendars, you scan use the URL `'https://www.google.com/calendar/exporticalzip'`.

If you'd like the to download the whole script, you can get it [here](https://github.com/jpverkamp/small-projects/blob/master/scripts/backup-google-reader.py). To backup Google Calendar instead, just make the two changes noted above.
