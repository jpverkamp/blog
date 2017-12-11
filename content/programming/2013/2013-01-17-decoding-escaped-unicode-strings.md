---
title: Decoding escaped Unicode strings
date: 2013-01-17 14:00:56
programming/languages:
- Python
programming/topics:
- Censorship
- JSON
- Regular Expressions
- Twitter
- Unicode
slug: decoding-escaped-unicode-characters
---
In one of my current research projects involving large amounts of <a href="https://twitter.com/" title="Twitter">Twitter</a> data from a variety of countries, I came across an interesting problem. The Twitter stream is encoded as a series of {{< wikipedia "JSON" >}} objects--each of which has been written out using {{< wikipedia "ASCII" >}} characters. But not all of the Tweets (or even a majority in this case) can be represented with only ASCII. So what happens?

Well, it turns out that they encode the data as JSON strings with {{< wikipedia "Unicode" >}} {{< wikipedia "escape characters" >}}. So if we had the Russian hashtag #победазанами (victory is ours), that would be encoded as such:

```python
"#\u043f\u043e\u0431\u0435\u0434\u0430\u0437\u0430\u043d\u0430\u043c\u0438"
```

<!--more-->

Each block of characters with the form `\uxxxx` (where `x` is a {{< wikipedia "hexadecimal" >}} value) is actually a Unicode character. But the problem is, there's no direct way (to my knowledge) to force Python to convert those to the actual characters. At least not directly. (My original plan was to use `eval`, but some Tweets broke that rather badly.)

What I ended up doing was writing a quick script that would convert such strings. Essentially, it would use regular expression to match the `\uxxxx` pattern. Then it would extract the hex value and convert it to a single Unicode character. Finally, the former would be replaced with the latter, repeating the process so long as more matches were found.

What does that mean in code?

```python
re_uni = re.compile('\\\\u(([0-9a-fA-F]){4})')

def re_unicode(str):
	match = re_uni.search(str)
	while match:
		uni = unichr(int(match.groups()[0], 16))
		str = str[:match.start()] + uni + str[match.end():]
		match = re_uni.search(str)
	return str
```

Now we can do something like this:

```python
>>> re_unicode("#\u043f\u043e\u0431\u0435\u0434\u0430\u0437\u0430\u043d\u0430\u043c\u0438")
#победазанами
```

Line by line, the first interesting point is the regular expression itself. We start with `\u`. Because `\` is the escape character in Python strings, we need to escape it. But it's also the escape character in regular expressions. So we need to escape the `\`s. Ergo `\u` becomes `\\\\u`. Next, we want exactly four hex characters. The group `[0-9a-fA-F]` matches a hex character (although in our dataset, they'll always be lower case so it could be simplified) and the `{4}` means to match exactly four times (short hand for just repeating the group). The extra parenthesis are so we can later pull out just that group.

Next, the match. We use `search` because the pattern might not be at the beginning of the string. If the patter exists, a `Match` object will be returned which can be treated as `True` (ergo the `while` loop). Otherwise, it will return `None`, breaking the loop.

After that, we convert the hex value into an integer (the second argument specifies the base as 16 / hex) and then into a Unicode character with `unichr`. I actually didn't know such a function exists, but it's exactly what we need in this instance.

Finally, we perform the replacement using the beginning and end of the regular expression's match to cut out the old version and put the new version in its place. Loop a few times and we should be good to go.

If there's an easier way to do this, I'd love to hear it. It works great for the project I'm working on, but it seems like this should be something baked into the language. Feel free to leave a comment or send me an email (<a href="mailto:me@jverkamp.com">me@jverkamp.com</a>).
