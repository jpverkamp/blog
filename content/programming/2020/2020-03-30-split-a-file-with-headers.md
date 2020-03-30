---
title: Split a file with headers
date: 2020-03-30
programming/topics:
- Dotfiles
programming/languages:
- Bash
---
I have a bunch of files with Arabic content that I need to split into chunks so they can be better run in parallel[^iknow]. But by default, when I open them in a text editor, the encoding changes from `windows-1256` to `utf-8`[^iknow2]. I could use the Unix `split` command to break them into chunks, but I need to preserve the headers. So... how do I fix all this? 

Write a script!

<!--more-->

Start with [this answer](https://stackoverflow.com/questions/37386246/split-large-csv-file-and-keep-header-in-each-part/45384974#45384974) from StackOverflow and clean it up / add some features I need:

```bash

#!/bin/sh

# Based on:
# https://stackoverflow.com/questions/37386246/split-large-csv-file-and-keep-header-in-each-part/45384974#45384974

# Pass a file in as the first argument on the command line (note, not secure)
file=$1
size=${2:-1000}

tempdir=$(mktemp -d)

# Split header and data
head -1 $file > $tempdir/header
tail -n +2 $file > $tempdir/data

pushd $tempdir > /dev/null
    # Break into chunks
    split -l $size data chunk
    rm data

    # Put them back together 
    for part in `ls -1 $tempdir/chunk*`
    do
        cat $tempdir/header $part > $part-$file
        rm $part
    done
popd > /dev/null

# Pull them here
mv $tempdir/chunk*$file .

rm -rf $tempdir
```

Use `mktemp` to not clutter my directory. It's not perfect, since the files will always be named `chunk[a-z]{2}-...` but that's fine. It does what I need it to do.

```fish
><> for f in *; split-with-headers $f 5000; end
```

[Source on github](https://github.com/jpverkamp/dotfiles/blob/master/bin/split-with-headers)

Hopefully someone else will find this useful. 

[^iknow]: I know that this should probably be done at the app level. 
[^iknow2]: I also know I could just turn this off. 