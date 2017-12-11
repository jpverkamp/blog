---
title: Removing large files from git history
date: 2014-09-03
programming/topics:
- Dotfiles
- Git
- Open Source
- Unix
---
A couple of quick additions to my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}) today:


* `git find-fat` - find large files that no longer exist
* `git trim-fat` - remove files entirely from git history


<!--more-->

Both come courtesy of GitHub user <a href="https://github.com/cmaitchison/">cmaitchison</a>, specifically from his <a href="https://github.com/cmaitchison/git_diet">git_diet</a> repository.

The code[^1][^2] is a little opaque, although it's neat if you're into bash scripts. Honestly though, you mostly only need to use them. For that, here's an example:

```bash
# Find the 20 (-n) largest blobs that no longer exist (-d)
$ git find-fat -n 20 -d

# From just the filenames (-f), remove those files from the git history
$ git find-fat -n 20 -d -f | git trim-fat
```

One thing I really love about `git` is how it works with files on your path named `git-*`. So I can use `git find-fat` rather than needing `git-find-fat`, just as if it were built into `git`. It's not *that* big of a deal, but I still think it's neat.

[^1]: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/git-find-fat">git-find-fat</a>
[^2]: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/git-trim-fat">git-trim-fat</a>