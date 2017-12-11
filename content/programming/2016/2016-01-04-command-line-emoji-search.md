---
title: Command line emoji search
date: 2016-01-04
aliases:
- /2016/12/04/command-line-emoji-search/
programming/languages:
- Python
programming/topics:
- Command line
- Emoji
---
Sometimes, I find myself wanting to communicate in {{< wikipedia "emoji" >}}.

:chicken:

How about this:

```bash
$ emoji chicken
🐔

$ emoji "which came first, the :chicken: or the :egg:"
which came first, the 🐔 or the 🍳
```

<!--more-->

To start off, I'm going to use the data from muan's emojilib on GitHub: <a href="https://github.com/muan/emojilib/">github:muan/emojilib</a>. Specifically, their list of keywords that relate to any given emoji: <a href="https://raw.githubusercontent.com/muan/emojilib/master/emojis.json">emojis.json</a>[^1]

We'll fetch that file if we haven't before and otherwise use a locally cached version:

```python
cache_path = os.path.expanduser('~/.emoji.json')
remote_url = 'https://raw.githubusercontent.com/muan/emojilib/master/emojis.json'

if not os.path.exists(cache_path):
    with open(cache_path, 'w') as fout:
        response = requests.get(remote_url)
        fout.write(response.text)

with open(cache_path, 'r') as fin:
    emoji = json.load(fin)
```

After that, there are two different ways that we can look up Emoji. We can either look them up by a semi official name or by keyword. This function will search through the both, matching on names first and then falling back to the first which matches the given keyword (this script isn't designed to return choices for emoji, but rather just choose the first one that fits; because a Python `dict` isn't ordered, this is actually non-deterministic):

```python
def emoji_by_keyword(keyword):
    if keyword in emoji:
        return emoji[keyword]['char']

    for name in emoji:
        if name == 'keys':
            continue

        if keyword in emoji[name]['keywords']:
            return emoji[name]['char']

    return keyword
```

Following that, we can use regular expressions (the `re` module) to replace emoji in a string--if they're set off `:emoji:` style (a la GitHub):

```python
def emojify(string):
    return re.sub(
        r'\:(\w+)\:',
        lambda m : emoji_by_keyword(m.group(1)),
        string
    )
```

That's a neat trick that I use from time to time: the second argument to `re.sub` can be either a literal string or a function. If it's the latter, it's given the match object for each replacement, which we can then pass along to `emoji_by_keyword`.

And finally, let's mess with some command line arguments:

```python
# Run replacement mode on stdin if no parameters
if len(sys.argv) == 1:
    for line in sys.stdin:
        print(emojify(line[:-1]))

# Othwise, run through the list
else:
    for arg in sys.argv[1:]:
        if ':' in arg:
            print(emojify(arg), end = ' ')
        else:
            print(emoji_by_keyword(arg), end = ' ')
```

There are three modes we can be operating in:


* `stdin` mode, where we will read text from `stdin` and replace any `:emoji:` blocks with the corresponding emoji
* String mode, where we find any `:emoji:` in each argument in each input and replace them
* Single lookup mode, where we look up each argument as an individual emoji keyword, without the need for `:`


And, that's it.

```bash
$ emoji fireworks fireworks fireworks
🎆🎆🎆
```

Since this is now one of my [dotfiles]({{< ref "2015-02-11-update-dotfiles-encryption.md" >}}), you can find the entire source here: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/emoji">emoji</a>

[^1]: It's under an MIT license, so all is well.