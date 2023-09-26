---
title: Adding local search to Hugo with Pagefind
date: 2023-09-25
programming/languages:
- Go
programming/topics:
- Hugo
---
At this point, I have very nearly 2500 posts going back almost 20 years (... whoa). In a lot of ways, it's a second brain for me. I actually find myself (from time to time) going back and looking up my various old posts.

Sometimes, I wanted to know how I solved a particular programming problem, sometimes I wanted to know when I went somewhere (by pictures!), and sometimes I wanted to know what a particular book or movie was about. 

So for the longest time, I've had (up in the corner there) a nice search box. Powered by Google: ~~Don't Be Evil~~. Well, today, let's see if we can do better!

<!--more-->

{{<toc>}}

## Original solution (Google)

So when I first implemented search:

```html
<form action="//www.google.com/search" method="get" onsubmit="(function(obj){obj.q.value='site:blog.jverkamp.com '+obj.qfront.value;})(this)" class="navbar-form navbar-right" role="search" _lpchecked="1">
    <div class="form-group">
        <input name="q" type="hidden">
        <input name="qfront" type="text" class="form-control" placeholder="Search">
        <button type="submit" class="btn btn-default" value="Search">Search</button>
    </div>
</form>
```

That's actually a pretty wacky search box, but the basic idea is to:

* Take a basic HTML form with the actual search term as `qfront` (I... don't remember why)
* Capture the `onsubmit` event and prepend the advance search directive `site:blog.jverkamp.com` to make sure it only returns results from Google
* Send it off

It's been so long since I implemented that, that I don't actually remember where I got it, but [this StackOverflow](https://stackoverflow.com/a/509052) answer hints it might have come from JavaScriptKit.com? I'm usually better about documenting things like that. 

In any case, it works well enough. But it also has the downsides of:

1. Every search gets redirected off my page to Google
2. Search requires that Google is functioning (granted, they're more likely to be up and running that my site, but still)
3. All searches are sent to Google whether the person who visits my site wants to or not
4. Using Google this way as a custom search engine is [not exactly](https://programmablesearchengine.google.com/about/) the way that Google seems to want you to do this

So... I could do better.

## Moving to DuckDuckGo

Option 2... (which was never actually deployed). Do exactly the same thing, but just *not to Google*!

```html
<form action="https://duckduckgo.com/" method="get" onsubmit="(function(obj){obj.q.value='site:blog.jverkamp.com '+obj.qfront.value;})(this)" class="navbar-form navbar-right" role="search" _lpchecked="1">
    <div class="form-group">
        <input name="q" type="hidden">
        <input name="qfront" type="text" class="form-control" placeholder="Search">
        <button type="submit" class="btn btn-default" value="Search">Search</button>
    </div>
</form>
```

Yeah... that didn't last long. 

## Trying out lunr.js

What I really needed was something that would allow me to index all of my content and serve as a local search engine... but without actually running a server of my own. It's something that I certainly already do, but not for quite as 'public' a service as my blog. Plus, the content is static. If I can serve the index efficiently, then I shouldn't need a server, I should be able to just do this entirely on the front end. 

Luckily, the [Hugo documentation](https://gohugo.io/tools/search/) has a bunch of potential solutions, using various JavaScript libraries. The first one I tried: [lunr.js](https://lunrjs.com/)

First, building the index. There is an `npm` project [`hugo-lunr`](https://www.npmjs.com/package/hugo-lunr) that will do this for us:

```bash
$ npx hugo-lunr -i 'content/**' -o 'public/lunr-index.json'
```

Then, I created a quick (empty) `content/search/_index.md` file and a `layouts/search/list.md` to actually contain the HTML. This is... a bit annoying, but it works out well enough. 

And ... we have search!

But with one fairly (to me) major problem:

```bash
$ du -sh public/lunr-index.json

 11M	public/lunr-index.json
```

Whenever someone does a search, they have to download the `lunr-index.json` file... and it's 11M. Mostly because it contains the *full text content of every single one of those 2500 posts*. If you make more than once search, it's fine. It's cached. But... every time I publish a new post, the entire index is updated. That is... suboptimal, to say the least. 

At least it compresses well (which it would by default when actually being sent to a client)?

```bash
$ gzip public/lumr-index.json

$ du -sh public/lumr-index.json.gz

3.7M	public/lumr-index.json.gz```
```

But... this didn't seem like a great fit. I feel like we should actually be able to pre-build all the indexes actually used for searches. So...

## Trying out Pagefind

This actually works out much the same way. Just use `npx` to run an `npm` package to build:

```bash
$ npx pagefind --site "public"
```

One oddity? It works on the built site (the HTML) rather than the source (Markdown). I think I'm fine with this? 

### Indexing

Quite a bit more parsing, but it still works well:

```bash
$ npm_config_yes=true npx pagefind --site "public"

Running Pagefind v1.0.3 (Extended)
Running from: "/Users/jp/Projects/blog"
Source:       "public"
Output:       "public/../static/pagefind"

[Walking source directory]
Found 4960 files matching **/*.{html}

[Parsing files]
Found a data-pagefind-body element on the site.
↳ Ignoring pages without this tag.
5 pages found without an <html> element.
Pages without an outer <html> element will not be processed by default.
If adding this element is not possible, use the root selector config to target a different root element.

[Reading languages]
Discovered 1 language: unknown

[Building search indexes]
Total:
  Indexed 1 language
  Indexed 2431 pages
  Indexed 73247 words
  Indexed 0 filters
  Indexed 0 sorts

Finished in 5.737 seconds
```

Whee! 

What's the output for this one look like? 

```bash
$ du -sh pagefind

 99M	.
```

... oh. 

So it's actually generating *far* more content than lunr.js did... when one would think that the indexes should be smaller? 

### Generated content

But what's actually happening is that it has the content *and* the indexes split into a bunch of smaller files:

```bash
$ ls -R1 pagefind

fragment/
index/
pagefind-entry.json
pagefind-modular-ui.css
pagefind-modular-ui.js
pagefind-ui.css
pagefind-ui.js
pagefind.js
pagefind.unknown_4250afff34dbb74.pf_meta
pagefind.unknown_92ac9b6e393bcb6.pf_meta
...
pagefind.unknown_fe083fd70e9e1ac.pf_meta
wasm.unknown.pagefind

pagefind/fragment:
unknown_012c683.pf_fragment
unknown_0192cb8.pf_fragment
...
unknown_fffa664.pf_index
```

When you actually search, the frontend will do a bunch of search magic(tm) to get a few actual search terms *and then only load the fragments for those terms*. And when I post something new, only the fragments (keywords) that actually update are ... updated? 

Rather than taking 11MB, on a few quick tests a search needs to only load a few hundred kB of indexes. Acceptable? 

### Actually implementing search

So, how did I actually write search? 

Well, here's the HTML:

```html
{{ define "main" }}
<link href="/pagefind/pagefind-ui.css" rel="stylesheet">
<script src="/pagefind/pagefind-ui.js"></script>

<div id="search"></div>
<script>
    window.addEventListener('DOMContentLoaded', (event) => {
        new PagefindUI({ element: "#search", showSubResults: true });

        const urlParams = new URLSearchParams(window.location.search);
        const query = urlParams.get('q');

        if (query) {
            document.querySelector("#search input").value = query;
            document.querySelector("#search input").dispatchEvent(new Event('input'));
        }
    });
</script>
{{- end -}}
```

By default, all I need is the first line with `new PagefindUI`. The rest of that is actually a neat trick that allows me to support `/search/?q=search+terms` style searches and that Form from [earlier](#original-solution-google):

```html
<form action="/search/" method="get" class="navbar-form navbar-right" role="search" _lpchecked="1">
    <div class="form-group">
        <input name="q" type="text" class="form-control" placeholder="Search">
        <button type="submit" class="btn btn-default" value="Search">Search</button>
    </div>
</form>
```

Pretty cool! Now the search box in the top right functions as normal, but it loads a Pagefind based search instead!

### Limiting indexing and fixing metadata

This works great! But there are a few gotchas with the pagefind defaults that don't quite work how I'd like:

* All of my Hugo taxonomy / list pages are included in search results; this means that often you'll find a series page before the actual content
* All of the search results use 'JP's Blog' as the title; Pagefind will use the first `h1` it finds on the page as the title
* Any search results that don't have any images in the post will have the Creative Commons image (in the footer on every page); Pagefind uses the first img tag

Luckily, each of those has a really simple solution: html `data` tags that I can place right into my layouts!

* `data-pagefind-body`: Put this on the HTML element actually containing the content of a post; if it's found on *any* post, it will only include content that has this tag, which removes all of the taxonomy/list posts by default!
* `data-pagefind-meta="title"`: Put this on the actual title of the page (which in my case is actually an `h2`). 
* `data-pagefind-ignore="all"`: Put this on the footer image. You need to specify `all`, since by default it will just not index the content but will still use it as metadata (post image). 

And that's it! Search that more or less just works!

### Tying it into my build process

I'm still using using [[A Justfile for my blog]] to build things, so integration is pretty straight forward:

```justfile
build:
	...

	hugo --minify
	npx pagefind --site "public"

	...
```

Nice! Unfortunately, that doesn't work great with local development mode, but this does:

```justfile
run baseURL="localhost":
	npm_config_yes=true npx pagefind --site "public" --output-subdir ../static/pagefind
	hugo server --baseURL {{baseURL}} --watch --verbose --buildFuture --buildDrafts --bind 0.0.0.0 --port 80
```

It's a bit verbose, not going to lie, but it does what I want it to do ... more or less. One problem is that it doesn't actually recalculate the index live when I'm doing local development. 

Which... is actually fine? I don't use search much on local content. If I want to rebuild, I just have to run a `just build` before `just run`. It will build the search index twice, but it will be updated!

And as an added bonus, *local search works now*. Quite often when writing a new post, I want to find a previous post. Which works fine with the old Google search bar... except it loads deployed content, not whatever is local. Now, it stays all on localhost. Good times!

## Final thoughts

There are still a few gotchas:

* I need a new dependency to build my blog (`npx` has to be installed)
* The generated scripts aren't included in my [Javascript minification](https://github.com/jpverkamp/blog/blob/be7b29a5b72acabf1bea563c4d35d00fb36a9b71/layouts/partials/includes-js.html) process; I can probably fix this

But for the most part, it's been an interesting learning process and fun to set up. 

As always, if you find anything that you think I could have done better, I'd absolutely [love to hear](mailto:blog@jverkamp.com).

Onward!