---
title: Categorizing r/Fantasy Book Bingo Books
date: 2021-06-24
programming/languages:
- Python
programming/topics:
- Small Scripts
programming/sources:
- APIs
---
I've been working through the [r/Fantasy 2021 Book Bingo]({{< ref "2021-04-01-book-bingo" >}}) this year:

{{< bingo "2021 Book Bingo" >}}

<!--more-->

One thing that I've been having a bit of trouble with is categorizing books for that. There is a very active [recommendations thread](https://www.reddit.com/r/Fantasy/comments/mhz3k7/the_2021_rfantasy_bingo_recommendations_list/), but without the ability to load the entire thread, it ... isn't great to search. So let's make that easier. 

First thing first, let's get the raw data. It turns out that Reddit has a wonderfully simple API to start with, just add `.json` to a URL to get a thread in JSON format. [Example](https://www.reddit.com/r/Fantasy/comments/mhz3k7/the_2021_rfantasy_bingo_recommendations_list/.json). It's a bit of a weird format, but it's parsable. From there, you have references to child nodes that you can download in order to get one giant JSON object for the entire thread. Which sounds like a fascinating problem, but this time around, I just skipped that and used [this code](https://github.com/saucecode/reddit-thread-ripper/blob/master/ripper.py). Give it a thread, wait a bit (for such a large thread), get JSON. 

You could keep that as a JSON file, but I wanted to be sneaky/weird and put it straight in the script. It's a fair chunk of data with a number of weird characters, so storing it could be tricky... unless you just {{< wikipedia base64 >}} encode the entire thing. You can then store it straight inline and get it all out with `data = json.loads(base64.b64decode('W3siYm9keS...'))`. It's actually not that unusual of an idea. You see the same thing with inline `data:` images in webpages or games that directly embed art assets in the compiled file for optimization/distribution reasons. 

Next, parsing. In this case, the recommendations thread has one first level response for each of the categories in the bingo, but after that just about any level of response could contain book titles. So what we want is to search the JSON object recursively.

- For dictionaries, search the 'body' (for text) and 'replies' (for further children)
- For lists, search all entries (lists of replies)
- For strings (bodies), search the text (case insensitive)

```python
import base64
import json
import sys

data = json.loads(base64.b64decode('W3siYm9keS...'))
    
def search(key, data, path = None):
    path = path or []
    
    if isinstance(data, list):
        for i, child in enumerate(data):
            yield from search(key, child, path)
    elif isinstance(data, dict):
        if body := data.get('body'):
            yield from search(key, body, path)
            yield from search(key, data.get('replies'), path + [body])
    elif isinstance(data, str):
        if key.lower() in data.lower():
            yield path + [data]

def top_level_search(key):
    results = set()
    for result in search(key, data):
        results.add(result[0])
    return list(sorted(results))

for arg in sys.argv[1:]:
    print(arg)
    for result in top_level_search(arg):
        print(result)
    print()
```

I really do love generators in this case, with `yield from`. You can recursively scan through the entire structure and just sort of return a flat list for free. In this case, I'm keeping track of the `path` through the nodes that I took to get to a specific point, although I'm only ending up returning the `top_level_search` for each thread (I did the whole path at first, which was neat). 

And as a result:

```bash
$ python3 ~/Dropbox/book-bingo.py 'Six Wakes'

Six Wakes
**Mystery Plot** \- The main plot of the book centers around solving a mystery. **HARD MODE:** Not a primary world Urban Fantasy (secondary world urban fantasy is okay!)

$ python3 ~/Dropbox/book-bingo.py 'Annihilation'

Annihilation
**First Contact** \- From Wikipedia:  Science Fiction about the first meeting between humans and extraterrestrial life, or of any sentient species' first encounter with another one, given they are from different planets or natural satellites. **HARD MODE:** War does not break out as a result of contact.
**First Person POV** \- defined as:  a literary style in which the narrative is told from the perspective of a narrator speaking directly about themselves. [Link for examples.](https://examples.yourdictionary.com/examples-of-point-of-view.html) **HARD MODE:**  There is more than one perspective, but each perspective is written in First Person.
**Forest Setting** \-  This setting must be used be for a good portion of the book. **HARD MODE:** The entire book takes place in this setting.
**Mystery Plot** \- The main plot of the book centers around solving a mystery. **HARD MODE:** Not a primary world Urban Fantasy (secondary world urban fantasy is okay!)
```

Pretty handy!