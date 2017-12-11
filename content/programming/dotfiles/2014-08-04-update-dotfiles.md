---
title: Updating dotfiles
date: 2014-08-04
programming/languages:
- Python
programming/topics:
- Dotfiles
- Open Source
- Unix
---
After all of these updates to my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}), I finally want something that I can use to keep them up to date. For that, let's write a quick script that can do just that.

<!--more-->

First, we'll use the GitHub API to determine the most recent version of all of the files in the dotfiles repo:

```python
api_url = 'https://api.github.com/repos/jpverkamp/dotfiles/git/trees/master?recursive=1'
api_in = urllib2.urlopen(api_url)
api = json.loads(api_in.read())
api_in.close()
```

You'll of course have to specify your own url if you decide to use this script.

Next, we need something that can calculate a hash from a file on the local file system that matches the format the GitHub api returns. That way, we can use that hash to determine if files have changed, rather than having to download each file to diff them.

Luckily, GitHub user <a href="https://github.com/msabramo">msabramo</a> has a gist with exactly what I need: <a href="https://gist.github.com/msabramo/763200">https://gist.github.com/msabramo/763200</a>:

```python
#!/usr/bin/env python

from sys import argv
from hashlib import sha1
from cStringIO import StringIO

class githash(object):
    def __init__(self):
        self.buf = StringIO()

    def update(self, data):
        self.buf.write(data)

    def hexdigest(self):
        data = self.buf.getvalue()
        h = sha1()
        h.update("blob %u\0" % len(data))
        h.update(data)

        return h.hexdigest()

def githash_data(data):
    h = githash()
    h.update(data)
    return h.hexdigest()

def githash_fileobj(fileobj):
    return githash_data(fileobj.read())


if __name__ == '__main__':
    for filename in argv[1:]:
        fileobj = file(filename)
        print(githash_fileobj(fileobj))
```

Next, we'll iterate through the list fo filesignoreing a few specific files that we never want to update:

```python
for file in api['tree']:
    path = os.path.expanduser('~/.' + file['path'])

    # Skip double dots, those are things like gitignore
    if '..' in path or 'README.md' in path or 'install.py' in path:
        continue

    # Skip local directories that already exist
    if os.path.exists(path) and os.path.isdir(path):
        continue

    ...
```

After that, we'll calculate file hashes using the borrowed code above. Unfortunately, we don't know what sort of line endings we might have in the repo vs. locally, so we have to try all three possible combinations:

```python
# Calculate current file hashes; we generate three to deal with cross platform line endings
    current_hashes = []
    if os.path.exists(path) and os.path.isfile(path):
        with open(path, 'r') as fin:
            content = fin.read()
            current_hashes.append(githash_data(content))
            current_hashes.append(githash_data(content.replace('\r\n', '\n')))
            current_hashes.append(githash_data(content.replace('\n', '\r\n')))
```

At this point, I'm not entirely sure that I shouldn't have just diffed the files locally...

Next, the interactive part: ask the user if they want to download the new file (`y`), skip it (`n`), show a diff (`d`), or quit (`q`):

```python
# If we don't have the most up to date file, ask the user what to do
    if not file['sha'] in current_hashes:
        while True:
            choice = raw_input('{0} needs an update, download? '.format(path))
```

The interesting cases are downloading the file and showing a diff. For the former:

```python
# Download the current file
        if choice == 'y':
            file_in = urllib2.urlopen(file['url'])
            remote_js = json.loads(file_in.read())
            remote_content = decode_file(remote_js)
            file_in.close()

            with open(path, 'wb') as file_out:
                file_out.write(remote_content)

            break
```

Basically, download the file and write it out as a binary locally. Opening the local file as 'wb' mode means that Python won't try to guess what we mean when it comes to things like line endings.

Next, diff. Luckily, Python has a built in library for diffs[^1]:

```python
# Display a diff
        elif choice == 'd':

            if os.path.exists(path) and os.path.isfile(path):
                file_in = urllib2.urlopen(file['url'])
                remote_js = json.loads(file_in.read())
                if remote_js['encoding'] == 'base64':
                    remote_content = decode_file(remote_js).split('\n')
                else:
                    print('Cannot diff, unknown content type: ' + remote_js['encoding'])
                    sys.exit(0)
                file_in.close()

                with open(path, 'r') as file_in:
                    local_content = file_in.read().replace('\r\n', '\n').split('\n')

                for line in difflib.context_diff(local_content, remote_content):
                    print(line)

            elif os.path.isdir(path):
                print('{0} is a directory'.format(path))
            else:
                print('{0} is new'.format(path))
```

And that's pretty much it. There's an else block that will print out any files that are skipped. It works surprisingly well. Technically, we can even use this in place of my original `install.py` script.

Along with the rest of my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}), this script is available on GitHub: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/update-dotfiles">update-dotfiles</a>.

[^1]: What *doesn't* it have?