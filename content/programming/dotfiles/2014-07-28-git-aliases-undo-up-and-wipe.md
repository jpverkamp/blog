---
title: 'Git aliases: undo, ud, and wipe'
date: 2014-07-28
programming/topics:
- Dotfiles
- Git
- Open Source
- Unix
---
A few new git aliases:


* `git undo` - Undo the most recent commit, unstaging all new files
* `git up` - Update remote branches and submodules, delete merged branches
* `git wipe` - Remove all current changes, saving as a seperate branch


<!--more-->

Specifically, these three lines in my global `.gitconfig`:

```ini
[alias]
  ...
  undo = reset HEAD~1 --mixed
  up = !git pull --rebase --prune $@ && git submodule update --init --recursive
  wipe = !git add -A && git commit -qm 'WIPE SAVEPOINT' && git reset HEAD~1 --hard
```

These three all came from this post: <a href="http://haacked.com/archive/2014/07/28/github-flow-aliases/">GitHub Flow Like a Pro with these 13 Git Aliases</a>.

You can see the entire file here: <a href="https://github.com/jpverkamp/dotfiles/blob/master/gitconfig">.gitconfig</a>
