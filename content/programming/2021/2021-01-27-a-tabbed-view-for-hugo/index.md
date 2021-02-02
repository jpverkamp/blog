---
title: A Tabbed View for Hugo
date: 2021-01-27
programming/languages:
- Go
- Python
programming/topics:
- Hugo
---
One thing I've been using for a lot of my recent posts (such as [Backtracking Worms]({{< ref "2020-11-20-backtracking-worms" >}})) is a tabbed view of code that can show arbitrarily tabs full of code or other content and render them wonderfully! For example, we can turn:

{{< source "hugo" "source.hugo" >}}

Into the tabbed example view at the end of [yesterday's post]({{< ref "2021-01-26-rune-dsl" >}})!

To do this, I made a handful of different shortcodes:

{{< tabs >}}
    {{< sourcetab "html" "shortcodes/include.hugo" >}}
    {{< sourcetab "html" "shortcodes/source.hugo" >}}
    {{< sourcetab "html" "shortcodes/tab.hugo" >}}
    {{< sourcetab "html" "shortcodes/sourcetab.hugo" >}}
    {{< sourcetab "html" "shortcodes/tabs.hugo" >}}
    {{< sourcetab "js" "shortcodes/tabs.js" >}}
    {{< sourcetab "html" "shortcodes/p5js.hugo" >}}
{{< /tabs >}}

Each of these expects the source file being rendered to be in the same directory as the content being included. For example, this post has a directory structure [like this](https://github.com/jpverkamp/blog/tree/master/content/programming/2021/2021-01-27-a-tabbed-view-for-hugo). There's a bit of a gotcha in that if a file has the HTML extension, funny things happen (it tries to render the file even without a header), but so it goes. 

Each of the views builds on the one(s) before:

* `include.html`: Directly includes content[^xss] 
* `source.html`: Includes source code as a code block
* `tab.html`: Creates a new tab (should be nested in a `tabs` block)
* `sourcetab.html`: Combines `source` and `tab` in a single command
* `tabs.html`: Does the heavy lifting of rendering the included tabs
* `tabs.js`: Included in the page to allow clicking the various tabs (and automatically clicks the first of each set)
* `p5js.html`: Set up specifically for `p5js` entries, includes a live view of the entire script with some helper content[^todo]

The main magic comes about with Hugo's [scratch functions](https://gohugo.io/functions/scratch/) and how they work in shortcodes. In a nutshell, you can access a shortcodes `.Parent` element, which in turn comes with a `.Scratch` instance which can store semi-arbitrary content. So we can create a list of `tabs` like so:

```hugo
{{ .Parent.Scratch.Add "tabs" (slice (dict "title" $title "content" $content)) }}
```

Originally, I directly used a `dict` to map `$title` to `$content`, but that has two problems:

* You can't have two pages with the same name
* You lose the order of tabs (it will sort them alphabetically, but that's not always what you want)

Most of the rest of the content comes from properly generating the HTML elements for the tabs, which I lifted mostly from [this W3 Schools page](https://www.w3schools.com/howto/howto_js_tabs.asp), although I added a `tabset` ID to each element (either specified or generated automatically by a hash of the content) so that two sets of tabs can be on the same page. 

And that's really it. Hugo is really powerful, although working in a templating language is ... a bit weird sometimes. It's always fun (for me at least :)) to tune your tools though. 

I'm curious if anyone else has done something similar/what you did. It works, but it feels somewhat imperfect and could always be better. [Let me know!](mailto:blog@jverkamp.com)

[^xss]: Yes, I know I'm explicitly trusting the content with `safeHTML`, which is an XSS waiting to happen... but I'm the only one that writes content to this blog, so the impact is minimal; this is the usecase for `safeHTML`
[^todo]: I'll probably write up some of the tricks I used here in a future post