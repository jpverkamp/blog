---
title: Backing up GitHub repositories
date: 2015-09-08
programming/languages:
- Python
programming/topics:
- Backups
---
The newest chapter in my quest to collect entirely too much data / back up All The Things!: GitHub.

Basically, I want to back up all of my own personal GitHub repositories along with any from organizations that I am involved with. Strictly speaking, this is a little strange, since it's unlikely that GitHub is going anywhere soon and, if it does, we are likely to have fair warning. But still, it's nice to have a local copy just in case GitHub is down.

<!--more-->

The code is actually really straight forward. Most of the heavy lifting is being done by the <a href="https://github.com/copitux/python-github3">pygithub3</a> library. One caveat: it's a little strange to install. In my case, I had to first install `pygithub` and then `pygithub3` in order to satisfy a missing dependency (<a href="https://github.com/copitux/python-github3/issues/41">previously reported</a>).

After that, you can authenticate to GitHub, get a list of repositories, and download them all:

```python
#!/usr/bin/env python3

import pygithub3
import os

# Load a list of repos we don't want to download / update
ignored = set()
if os.path.exists('ignore.txt'):
    with open('ignore.txt', 'r') as fin:
        for line in fin:
            ignored.add(line.strip())

# Connect to github (if you have MFA, your password must be a token)
gh = pygithub3.Github(os.environ['GITHUB_USERNAME'], os.environ['GITHUB_PASSWORD'])

# Loop over repos for the specified user, this will include their organization's repos as well
for repo in gh.get_user().get_repos():

    remote_path = repo.ssh_url
    size = repo.size
    owner = repo.owner.login
    name = repo.name
    name_with_owner = '{owner}/{name}'.format(owner = owner, name = name)
    print(name_with_owner)

    # Check if the repo is in the ignore list
    if name in ignored or name_with_owner in ignored:
        print('... skipping')
        continue

    # Build up a list of commands that will be run for the given repo
    local_path = os.path.join('repos', owner, name)
    cmds = ['mkdir -p repos/{owner}; cd repos/{owner}'.format(owner = owner)]

    # Already exists, update it
    if os.path.exists(local_path):
        print('... updating')
        cmds += [
            'cd {name}'.format(name = name),
            'git pull --rebase --prune',                 # Update to the most recent master
            'git submodule update --init --recursive',   # Update submodules
        ]
    # Doesn't exist yet, clone it
    else:
        print('... cloning')
        cmds += [
            'git clone {url}'.format(url = remote_path), # Download a new clean copy using repo name as directory
            'cd {name}'.format(name = name),
            'git submodule update --init --recursive',   # Download and update submodules
        ]

    # Run each command specified above, bailing out if any failed (&&)
    cmds = ' && '.join(cmds)
    os.system(cmds)
    print()
```

Basically, we're going to run a sequence of commands depending on if the repo was previously checked out or not. If it hasn't been (this is the first time), we want to run:


* `git clone {url}`
* `cd {name}`
* `git submodule update --init --recursive`


This will get the initial version and any submodules. I'm not sure that I'm going to keep the submodule code around, but in interest of keeping everything in a runnable state even if GitHub were to vanish tomorrow, it seemed a good idea.

Alternatively, if we want to update a previously cloned repo:


* `cd {name}`
* `git pull --rebase --prune`
* `git submodule update --init --recursive`


This is much the same, it just pulls any new code first.

And that's it. It took a little while to pull all of my repositories down (I have about 15 GB all told, counting various private repositories from work and my university days (which I still help to maintain)), but that's only necessary the first time. After that, it's much quicker.
