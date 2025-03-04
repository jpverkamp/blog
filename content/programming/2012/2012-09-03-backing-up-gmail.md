---
title: Backing up Gmail
date: 2012-09-03 14:00:03
programming/languages:
- Python
programming/topics:
- Backups
- Email
---
A little while ago, I decided to finally get around to backing up everything. I'm pulling all of my files from both my website and the servers on campus to my desktop at home, backing my desktop up to an external hard drive, and pushing those backups to an offsite location.

The former two steps are using [here](https://github.com/jpverkamp/small-projects/blob/master/scripts/backup-gmail.txt).

First, some basic setup. Of course, I've blanked out my own username and password. This definitely isn't the best way to authenticate (storing the password in plain text? :(), but it works out well enough.

Most of the variables should be self explanatory, except perhaps `safe_chars`. That one in particular controls the characters that are safe to use in filenames. Everything else will be set to `_`.

```python
#!/usr/bin/env python

from __future__ import print_function

import codecs, datetime, email, email.utils
import imaplib, os, re, sys, time

from pprint import pprint

username = '#####'
password = '#####'

imap_host = 'imap.gmail.com'
imap_port = 993

mailbox = '[Gmail]/All Mail'

output_dir = '#####'
safe_chars = ''.join(chr(c) if chr(c).isupper()
                            or chr(c).islower()
                            else '_' for c in range(256))

collapse = re.compile(r'_+')

id_filename = 'ids.txt'
```

Next, some basic bookkeeping. Set up the directories and figure out which ids we've already read.

```python
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

if os.path.exists(output_dir + id_filename):
    with open(output_dir + id_filename, 'r') as f:
        read_ids = f.read().split('\n')
else:
    read_ids = []
```

Next, authenticate, switch to the `All Mail` mailbox, and get a list of all of the message ids.

```python
print('Authenticating')
mail = imaplib.IMAP4_SSL(imap_host, imap_port)
mail.login(username, password)

print('Switching to %s' % mailbox)
(state, count) = mail.select(mailbox)
count = int(count[0])
print('%s messages to read' % count)

print('Fetching ids')
result, data = mail.uid('search', None, "ALL")
ids = data[0].split()
id_file = open(output_dir + id_filename, 'a')

for id in ids:
    if id in read_ids:
        continue
```

Go through each message and pull out who it's from, the date, and the subject. We'll use the date and subject for the filename to write to.

```python
try:
        result, data = mail.uid('fetch', id, '(RFC822)')
        data = data[0][1]
        msg = email.message_from_string(data)

        msg_from = msg['From']
        msg_subj = msg['Subject'] if msg['Subject'] else '(no subject)'
        msg_date = datetime.datetime.fromtimestamp(
            time.mktime(email.utils.parsedate(msg['Date'])))
        dir = (output_dir + '%04d/%02d/') % (msg_date.year, msg_date.month)
        if not os.path.exists(dir):
            os.makedirs(dir)
```

It's just a flat dump of the email, so it should be easy enough to process for any other reasons or to re-import if that should ever be necessary.

```python
filename = '%04d%02d%02d-%02d%02d%02d-%s' % ( \
            msg_date.year, \
            msg_date.month, \
            msg_date.day, \
            msg_date.hour, \
            msg_date.minute, \
            msg_date.second, \
            collapse.sub('_', msg_subj.translate(safe_chars)).strip('_'))

        print('%s: %s' % (id, filename))

        with open(dir + filename, 'w') as f:
            f.write(data)

    except Exception, ex:
        print('%s: %s' % (id, ex))
```

After we're done, write out the IDs so that they don't get downloaded more than once.

```python
id_file.write('%s\n' % id)
    id_file.flush()
    read_ids.append(id)

id_file.close()
```

So far, it's been working great. I've been running it for a few months now. Took a while to to get the messages at first, but it's much quicker now.

If you want to get the entire source code, you can do so [here](https://github.com/jpverkamp/small-projects/blob/master/scripts/backup-gmail.txt).
