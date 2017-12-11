---
title: Glorious Gification of HipChat Rooms
date: 2015-12-02
programming/languages:
- Python
programming/topics:
- HipChat
---
To counter yesterday's post on [Iterating the GitHub API]({{< ref "2015-12-01-iterating-the-github-api.md" >}}), how about something a little more lighthearted today: GIFs[^1].

{{< figure src="/embeds/2015/no-regrets.gif" >}}

<!--more-->

Animated GIFs are an amusing--if arguably useful--way of communicating. But hey, if something is worth doing, it's worth OVERDOING, no[^2]?

So I wrote a script to upload my entire collection of GIFs to a HipChat room[^3]:

```python
#!/usr/bin/env python3

import os
import random
import re
import requests
import sys
import time

ACCESS_TOKEN = '{redacted}'
ROOM_ID = 8675309
GIF_PATH = '{redacted}'
TIMEOUT = 60

from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.mime.text import MIMEText

headers = {
    'Authorization': 'Bearer {}'.format(ACCESS_TOKEN),
    'Accept-Charset': 'UTF-8',
    'Content-Type': 'multipart/related',
}

url = 'https://api.hipchat.com/v2/room/{}/share/file'.format(ROOM_ID)

paths = [
    os.path.join(path, file)
    for path, dirs, files in os.walk(GIF_PATH)
    for file in files
    if file.endswith('.gif')
]
random.shuffle(paths)

for path in paths:
    print(path)

    raw_body = MIMEMultipart('related')
    with open(path, 'rb') as fin:
        img = MIMEImage(fin.read())
        img.add_header(
            'Content-Disposition',
            'attachment',
            name = 'file',
            filename = path.split('/')[-1]
        )
        raw_body.attach(img)

    raw_headers, body = raw_body.as_string().split('\n\n', 1)
    boundary = re.search('boundary="([^"]*)"', raw_headers).group(1)

    headers['Content-Type'] = 'multipart/related; boundary="{}"'.format(boundary)

    r = requests.post(url, data = body, headers = headers)
    time.sleep(TIMEOUT)
```

The main reason that this script is at all interesting is that the API excepts (and requires) a `multipart/related` request, but the <a href="http://docs.python-requests.org/en/latest/">Requests</a> won't send one. So instead we have to pull in Python's email libraries in order to generate the request body. It's a bit annoying, but an interesting dive into some of the more esoteric details of web requests. 

Also, I've been on a kick of using slightly more complicated list comprehension:

```python
paths = [
    os.path.join(path, file)
    for path, dirs, files in os.walk(GIF_PATH)
    for file in files
    if file.endswith('.gif')
]
```

Basically, if you put multiple `for` loops in a list comprehension body, it will return a single iterable, nested from the first to the last. So this is equivalent to:

```python
paths = []
for path, dirs, files in os.walk(GIF_PATH):
    for file in files:
        if file.endswith('.gif'):
            os.path.join(path, file)
```

It's arguable which is more Pythonic (probably the latter), but I do find it interesting what impact writing piles of functional code ([Racket]({{< ref "2014-06-11-call-stack-bracket-matcher.md" >}})) will do to code in other languages. 

And, that's it. Short and sweet. Use responsibly.

[^1]: gif, not jif
[^2]: Don't answer that
[^3]: Which I am now uploading for the greater ~~good~~chaos of all