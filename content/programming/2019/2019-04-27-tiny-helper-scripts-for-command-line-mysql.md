---
title: Tiny Helper Scripts for Command Line MySQL
date: 2019-04-27
programming/topics:
- Bash
- CSV
- MySQL
programming/languages:
- Bash
- Python
- SQL
---

Quite often, I'll find myself wanting to query and manipulate MySQL data entirely on the command line. I could be building up a pipeline or working on a task that I'm going to eventually automate but haven't quite gotten to yet. Whenver I have to do something like that, I have a small pile of scripts I've written over time that help out:

- `skiphead`: Skip the first line of output, used to skip over headers in a query response
- `skipuntil`: Skip all lines until we see one matching a pattern, used to resume partial tasks 
- `commaify`: Take a list of single values on the command line and turn them into a comma separated list (for use in `IN` clauses)
- `csv2json`: a [previously posted]({{< ref "2015-11-11-csv-to-json.md" >}}) script for converting csv/tab delimited output to json
- `jq`: not my script, but used to take the output of csv2json and query it further in ways that would be complicated to do with SQL

Admitedly, the first two of those are one liners and I could easily remember them, but the advantage of a single command that does it is tab completion. `sk<tab>`, arrow to select which one I want, and off we go. I could put them as an alias, but I don't always use the same shell (mostly [fish](https://fishshell.com/), but sometimes Bash or Zsh). 

<!--more-->

# `skiphead`

```bash
#!/bin/bash

awk 'NR>1'
```

First, skip the header. You can use this after making a MySQL query to skip over the header. Perhaps you want to combine it with `commaify` (later):

```bash
$ echo 'select * from messages where user_id in (' $(echo 'select id from users where email like "%@example.com"' | mysql ... | skiphead | commaify) ')' | mysql... | ... 
```

(I'm purposely leaving out the details of the `mysql` command. I have a wrapper for that I use which I'll post about at some point.)

This will get users matching an email address, skip over the included header, turn into a comma delimited list and pass into another query (perhaps in another database). 

[skiphead on Github](https://github.com/jpverkamp/dotfiles/blob/master/bin/skiphead)

# `skipuntil`

```bash
#!/bin/bash

sed -n "/$@/,\$p"
```

This will use a bit of `sed` trickery ([source](https://stackoverflow.com/questions/5935742/how-to-ignore-all-lines-before-a-match-occurs-in-bash)) to skip lines until a line matches the given regular expression. If you have a long running process that is iterating over some sort of ID (which I often do) that crashes halfway through, you can run the next time with `skipuntil {last good id}` to resume from where you left off. 

If you wanted something a bit more Pythonic (and less opaquely depending on sed's lovely syntax):

```python
#!/usr/bin/env python3

import fileinput
import re
import sys

if len(sys.argv) <= 1:
  print('Usage: skipuntil <regex> <files...>?')
  exit(1)

matcher = re.compile(sys.argv[1])
matched = False

for line in fileinput.input(sys.argv[2:]):
  if not matched and matcher.match(line):
    matched = True
  if matched:
    sys.stdout.write(line)
```

[skipuntil on Github](https://github.com/jpverkamp/dotfiles/blob/master/bin/skipuntil)

# `commaify`

```python
#!/usr/bin/env python3

import fileinput
import re

values = []
for line in fileinput.input():
  line = line.strip()
  if line.isnumeric():
    values.append(line)
  else:
    values.append('"{}"'.format(re.escape(line)))

print(','.join(values))
```

A powerful script that will take a list of items that come in newline delimted ids/numbers/strings and join them into an escaped and quoted (if necessary) list that can be passed to as a MySQL `in` clause. I can't guarantee that it's 100% safe against untrusted inputs, but then again, what is? 

[commaify on Github](https://github.com/jpverkamp/dotfiles/blob/master/bin/commaify)

# `csv2json` / `jq`

As mentioned, this was a script I posted about [a few years ago]({{< ref "2015-11-11-csv-to-json.md" >}}), but it's still useful, particularly in combination with [jq](https://stedolan.github.io/jq/). You can combine data from multiple databases (which SQL generally won't do) or local data or even process in ways that are hard to do with SQL alone. Pretty handy that. 

[csv2json on Github](https://github.com/jpverkamp/dotfiles/blob/master/bin/csv2json)

# Putting it all togther

You can do all sorts of interesting things with these commands all together:

```bash
# Take a CSV file containing multiple fields, extracxt the email column, get unique values, and turn those into user ids
$ echo 'select id from users where email in (' (cat some-user-data.csv | csv2json | jq '.email' | tr -d '"' | sort | uniq | commaify) ')' | mysql... | skiphead > user-ids

# Combine data from multiple sources on the local file system and build a query from it
$ echo '
    select messages.text
    from
      users
      join messages on (users.id = messages.user_id)
    where
      users.email in (' (cat emails | commaify) ')
      and users.id not in (' (cat safe_ids | commaify) ')
  ' | mysql... 
  ```

Pretty cool. Makes the Unix philosophy work for you:


> Write programs that do one thing and do it well.

> Write programs to work together.

> Write programs to handle text streams, because that is a universal interface.

> \- Peter H. Salus in A Quarter-Century of Unix (1994)

