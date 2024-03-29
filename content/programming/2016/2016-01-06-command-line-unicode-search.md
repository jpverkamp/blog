---
title: Command line unicode search
date: 2016-01-06
aliases:
- /2016/12/06/command-line-unicode-search/
programming/languages:
- Python
programming/topics:
- Command line
- Unicode
---
Similar to Monday's post about [command line emoji search]({{< ref "2016-01-04-command-line-emoji-search.md" >}}), I often find myself wanting to look up Unicode characters. I have a custom search engine / bookmark set up in Chrome / Firefox (`uni %s` maps to `http://unicode-search.net/unicode-namesearch.pl?term=%s&.submit=Submit&subs=1`). That actually works great, but given how relatively much of my day I spend on the command line, I thought it would be interesting to do something there:

```bash
$ uni delta
⍋	apl functional symbol delta stile
⍙	apl functional symbol delta underbar
⍍	apl functional symbol quad delta
≜	delta equal to
Δ	greek capital letter delta
δ	greek small letter delta
ẟ	latin small letter delta
ƍ	latin small letter turned delta
𝚫	mathematical bold capital delta
𝜟	mathematical bold italic capital delta
𝜹	mathematical bold italic small delta
𝛅	mathematical bold small delta
𝛥	mathematical italic capital delta
𝛿	mathematical italic small delta
𝝙	mathematical sans-serif bold capital delta
𝞓	mathematical sans-serif bold italic capital delta
𝞭	mathematical sans-serif bold italic small delta
𝝳	mathematical sans-serif bold small delta
ᵟ	modifier letter small delta
```

<!--more-->

The basic idea is to take Python's `unicodedata` module and use that to get the names of characters, then to find those that best match user input. Of course one problem with that is that as of version 8 of the Unicode specification there are up to 263,994 characters defined in 262 different blocks. That's a bit much.

So instead, I'm going to select a handpicked list of blocks that I think might be vaguely interesting (see <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/uni#L284">here</a>) as a default and add the ability to select any other block as a command line switch:

```bash
$ uni --block currency euro
€	euro sign
₠	euro-currency sign
```

So, how do I do it? First, let's assume I have a list of unicode blocks defined as such (available from the Unicode Consortium: <a href="ftp://ftp.unicode.org/Public/8.0.0/ucd/Blocks.txt">Blocks.txt</a>):

```text
0000..007F; Basic Latin
0080..00FF; Latin-1 Supplement
0100..017F; Latin Extended-A
0180..024F; Latin Extended-B
0250..02AF; IPA Extensions
...
```

First, we'll want to either determine which block(s) we'll be looking at:

```python
# Determine which unicode blocks we'll be searching through
blocks = []

if args.block:
    for line in all_blocks.split('\n'):
        if fuzz.token_set_ratio(args.block, line.split('; ')[-1]) > 100 * args.block_threshold:
            blocks.append(line)
else:
    blocks = default_blocks.split('\n')

if not blocks:
    sys.stderr.write('No blocks found\n')
    sys.exit(-1)
```

`args` contains the parsed command line parameters, I'll get to that later. `fuzz` is from the <a href="https://github.com/seatgeek/fuzzywuzzy">fuzzywuzzy</a> Python library for fuzzy string matching. Basically, if the `--block` parameter was specified, we'll search for any that match closely enough, otherwise we'll use the default blocks.

Next, we'll look through and build a list of all possible matching characters within those blocks. Given the formats above, we can get the lower and upper bounds with `int`, specifying base 16 and then use `unicodedata` to get the character name. Again, we'll apply a fuzzy match to the character names.

```python
# Search through all of those blocks, whee
results = []

for block in blocks:
    bounds, name = block.split('; ')
    lower_bound, upper_bound = bounds.split('..')

    lower_bound = int(lower_bound, 16)
    upper_bound = int(upper_bound, 16)

    for codepoint in range(lower_bound, upper_bound + 1):
        try:
            character = chr(codepoint)
            name = unicodedata.name(character, None).lower()
            score = fuzz.token_set_ratio(args.name, name)

            if score > 100 * args.name_threshold:
                results.append((score, name, character))
        except:
            pass

if not results:
    sys.stderr.write('No characters found\n')
    sys.exit(-1)
```

And after that, we have a few tweaks for output. We can print all of the results (default) or just a limited number and we can print just the character or also the name:

```python
# Only print out the requested number of results
for count, (score, name, character) in enumerate(sorted(results)):
    if args.count and count >= args.count:
        break

    if args.quiet:
        print(character)
    else:
        print(character, name, sep = '\t')
```

I guess now would be a good time to go back to how we got the `args` object in the first place:

```python
parser = argparse.ArgumentParser('Search unicode characters')
parser.add_argument('name', nargs = '+', help = ...)
parser.add_argument('--block', '-b', help = ...)
parser.add_argument('--block-threshold', default = 0.9, help = ...)
parser.add_argument('--name-threshold', default = 0.9, help = ...)
parser.add_argument('--count', default = 0, type = int, help = ...)
parser.add_argument('--quiet', '-q', default = False, action = 'store_true', help = ...)
args = parser.parse_args()
```

`argparse` is a most excellent library. It allows you to declaratively specify what your command line parameters will be and then will parse it into an object with one field for each variable (fixing the names so that `--block-threshold` becomes `args.block_threshold`).

And that's it. You can use it to look up all sorts of interesting things:

```python
uni --count 10 --block runic runic

ᛮ	runic arlaug symbol
ᛰ	runic belgthor symbol
᛭	runic cross punctuation
ᚪ	runic letter ac a
ᚫ	runic letter aesc
ᛉ	runic letter algiz eolhx
ᚨ	runic letter ansuz a
ᛒ	runic letter berkanan beorc bjarkan b
ᛍ	runic letter c
ᛣ	runic letter calc
```

(That will display better if you're using a font that includes Unicode range `16A0..16FF; Runic`.)

For the most part, I'll use it in this mode and then select characters to copy and paste. But you could also combine it with <a href="https://github.com/garybernhardt/selecta">selecta</a> and `pbcopy` (on OSX) to get something entirely more interesting:

```bash
$ uni --block runic runic | selecta | cut -f 1 | tr -d '\n' | pbcopy
```

`uni` will display a list of characters, `selecta` will let you search for one, `cut` will get just the character, `tr` will remove the newline, and `pbcopy` will send it to the clipboard. You could even shove it into a Bash/ZSH alias:

```bash
pbuni() {
    uni $@ | selecta | cut -f 1 | tr -d '\n' | pbcopy
}
```

Very cool.

This is in my dotfiles, so you can find the full source here: <a href="https://github.com/jpverkamp/dotfiles/blob/master/bin/uni">uni</a>. Enjoy!
