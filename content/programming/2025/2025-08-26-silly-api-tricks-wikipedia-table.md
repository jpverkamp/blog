---
title: "API Tricks: Wikipedia Table JSON API"
date: 2025-08-16
programming/topics:
- API
- JSON
---
Quick, what is the order of the (as of now) 63 released Walk Disney Animation Studios films? 

```bash
$ api=https://www.wikitable2json.com/api; \
  page=List_of_Walt_Disney_Animation_Studios_films; \
  curl -s "$api/$page?table=0&keyRows=1" \
  | jq '.[0][].Film' -rc \
  | egrep -v '^as' \
  | nl

     1	Snow White and the Seven Dwarfs
     2	Pinocchio
     3	Fantasia
...
    61	Strange World
    62	Wish
    63	Moana 2
```

There is a list on Wikipedia: [[wiki:List of Walt Disney Animation Studios films]](), but the tables there are ... a bit of a pain to copy paste. I could very well just manually do that, but where's the fun in that? 

Luckily, [someone](https://github.com/atye/wikitable2json/) went through the work of providing a wrapper around Wikipedia that will extract all (or selected) tables from a Wikipedia page!

To break down the command:

* `curl -s https://{...}?table=0&keyRows` - Download the first ([[wiki:zero based indexing]]()) table on the page; use the first row as column names (`-s` for 'silent' mode)
* `jq '.[0][].Film` - Extract the first table in the response (`.[0]`), for each row in that table `[]` extract the film name `.Film`
* `egrep -v '^as` - Remove rows starting with 'as ...'; these are extra rows when the studio was renamed

And that's it!

<!--more-->
