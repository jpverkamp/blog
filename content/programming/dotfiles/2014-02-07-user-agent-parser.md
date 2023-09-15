---
title: Command line user agent parsing
date: 2014-02-07 00:10:00
programming/languages:
- Python
programming/topics:
- Dotfiles
- Open Source
- Unix
---
Quite often when working with internet data, you will find yourself wanting to figure out what sort of device users are using to access your content. Luckily, if you're using HTTP, there is a standard for that: The [[wiki:user-agent]]() header.

Since I'm in exactly that position, I've added a new script to my [Dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}) that reads user agents on `stdin`, parses them, and writes them back out in a given format.

<!--more-->

For example:

```bash
$ ua --format "{user_agent[family]} {user_agent[major]}.{user_agent[minor]}"
Mobile Safari 5.1

$ ua --format "{os[family]}"
iOS

$ ua --format "{device[family]}"
iPhone'''
```

The code is very straight forward. We are using `argparse` to get the command line argument, the <a href="https://github.com/ua-parser/uap-python">Python ua-parser</a> library to get a dictionary containing all of the necessary information, and Python's `str.format` method to do formatting:

```python
parser.add_argument(
    '-f',
    '--format',
    dest="format",
    default='{device[family]}\t{os[family]} {os[major]}.{os[minor]}\t{user_agent[family]} {user_agent[major]}.{user_agent[minor]}',
)
args = parser.parse_args()

for line in sys.stdin:
	data = user_agent_parser.Parse(line.strip())
	print args.format.format(**data)
```

If you'd like to see / download the entire code, you can see it in my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}) repository: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/ua">ua</a>.
