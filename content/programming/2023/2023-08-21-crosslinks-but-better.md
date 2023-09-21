---
title: Crosslinks by Title in Hugo--But Better!
date: 2023-08-21
programming/languages:
- Go
programming/topics:
- Hugo
---
Once upon a time, I solved [[Crosslinks by Title in Hugo]](). Back then, I added a [shortcode](https://gohugo.io/content-management/shortcodes/) so that I could link to any post by title like this:

```markdown
{{</* crosslink "Title goes here" */>}}
```

It worked pretty well, but ... it never really felt 'Markdown'y. Which I suppose was the point. 

But more recently, I came across [Markdown render hooks](https://gohugo.io/templates/render-hooks/). 

What's that you say? I can write code that will take the parameters to any Markdown link (or image/heading/codeblock) and generate the HTML with a custom template? 

Interesting!

<!--more-->

{{<toc>}}

## The basic implementation

In a nutshell--and per [the docs](https://gohugo.io/templates/render-hooks/)--all you have to do is make a file [`layouts/_default/_markup/render-link.html`]. It will be provided the `.Page` being rendered, the `.Destination` the link is to, the `.Title` (if specified) and the `.Text` / `.PlainText` to the page. 

So if you have:

```markdown
[An example link](https://example.com)
```

`.Text` / `.PlainText` will be `An example link` and `.Destination` will be https://example.com

If we just want to re-implement the basic functionality:

```markdown
<!-- render-link.html -->
<a href="{{ .Destination }}">{{ .Text }}</a>
```

Easy enough. 

Now one step further, what if we want all links (by default) to open in a new tab? 

```markdown
<!-- render-link.html -->
<a href="{{ .Destination }}"{{ if strings.HasPrefix .Destination "http" }} target="_blank" rel="noopener"{{ end }}>{{ .Text }}</a>
```

I think you might be guessing what's next... 

## Implementing wiki-style crosslinks

What's neat about that is the `.Text` can be *pretty* flexible. What if I make links like this:

```markdown
[[Title goes here]]()
```

In this case, `.Text` is `[Title goes here]` (note the leading and trailing square brackets) and `.Destination` is empty. And... it looks an awful lot like a wikistyle crosslink! (The `()` at the end is suboptimal but at the moment unavoidable, so it goes)

So we have:

```markdown
<!-- render-link.html -->
{{-
if (and (strings.HasPrefix .PlainText "[")
        (strings.HasSuffix .PlainText "]")
        (eq .Destination ""))
-}}
    {{- /*
        Crosslinks:
            [[Title]]() 
    */ -}}

    {{- $scratch := newScratch -}}

    {{- $fixedText := substr .PlainText 1 -1 }}
    {{- $fixedText = (replace $fixedText "&lsquo;" "'") -}}
    {{- $fixedText = (replace $fixedText "&rsquo;" "'") -}}

    {{- $parts := split $fixedText "|"  -}}
    {{- $title := $fixedText -}}
    {{- $text := $fixedText -}}

    {{- $scratch.Set "crosslink-url" false -}}

    {{- range $page := .Page.Site.AllPages -}}
        {{- if (and (not ($scratch.Get "crosslink-url")) (eq $page.Title $title)) -}}
            {{- $scratch.Set "crosslink-url" $page.Permalink -}}
        {{- end -}}
    {{- end -}}

    {{- if $scratch.Get "crosslink-url" -}}
        <a href="{{ $scratch.Get "crosslink-url" }}">{{ $text }}</a>
    {{- else -}}
        {{ errorf "Markdown crosslink error in %s, for title: %s, title: %s" .Page.File.Path $title $text }}
    {{- end -}}

{{- else -}}
    <a href="{{ .Destination }}"{{ if strings.HasPrefix .Destination "http" }} target="_blank" rel="noopener"{{ end }}>{{ .Text }}</a>
{{- end -}}
```

It's pretty similar to the [[Crosslinks by Title in Hugo|original crosslink code]](), although I did drop support for partial tags. You need an exact match (and it still doesn't deal with multiple matches, if there are two pages with the same title, you'll get the 'first' one, whatever that means). 

Two gotchas I did have to solve though:

* `render-link.html` doesn't have it's own [scratch space](https://gohugo.io/functions/scratch/) and can't access the one from the page it's on; but they've added `newScratch` since I last looked which solves that issue
* both `.Text` and `.PlainText` have HTML escaping and fancy quotes handled; so `'` becomes `’` becomes `&rsquo;`, while the original page title (that I'm looking up by) still has `'`. Ergo `$fixedText`.

## Allowing custom text

Next problem, what if I don't want the page title to actually appear to the user. In modified wiki-style links, I want `|`:

```markdown
<!-- render-link.html -->
[[Page title goes here|but text goes here]]()
```

If the `$title` and `$text` variables both being assigned to `$fixedText` looked funny... well, it's because I'm working backwards a bit. Instead of that, I have a nice `split` and `index` (with a guard to make sure there's only one `|`):

```markdown
<!-- render-link.html -->

...

{{- if gt (strings.Count .PlainText "|") 1 -}}
{{ errorf "Markdown crosslink error in %s, multiple | in %s" .Page.File.Path .PlainText }}
{{- end -}}

...

{{- $parts := split $fixedText "|"  -}}
{{- $title := index $parts 0 -}}
{{- $text := index $parts (sub (len $parts) 1) -}}

...
```

The rest just works the same way. And because I'm indexing at 0 and `length - 1` (instead of 0 and 1), it 'just works' no matter if there is a `|` or not. 

## Supporting prefixed links

The last thing that I wanted to support (since I was working in this code anyways) is the ability to make other kinds of parameterized links in the same style. Specifically:

```markdown
<!-- render-link.html -->
[[wiki:The Example|apparently a 1637 comedy written by James Shirley]]()
```

To replace:

```markdown
{{</* wikipedia title="The Example" text="apparently a 1637 comedy written by James Shirley" */>}}
```

And it's actually just a few more lines:

```markdown
<!-- render-link.html -->

...

{{- if strings.HasPrefix $title "wiki:" -}}
    {{- $title = substr $title 5 -}}
    {{- if strings.HasPrefix $text "wiki:" -}}{{- $text = substr $text 5 -}}{{- end -}}
    {{- $scratch.Set "crosslink-url" (printf "https://en.wikipedia.org/wiki/%s" $title) -}}
{{- end -}}

...
```

Having the remove `wiki:` from both `$title` and `$text` is a side effect of defaulting `$text` to `$title` if not provided, but other than that, pretty straight forward. And I'm already checking if `crosslink-url` is set, so nothing else needs to change. 

## Link to source

And... that's it. You can see the full source here: [render-link.html](https://github.com/jpverkamp/blog/blob/23e8d305265181be37a089475013827ceaf2bb12/layouts/_default/_markup/render-link.html). 

I'll probably move over a few more shortcodes (`doc` links in particular), but other than that... good to go. It's just easier to write the double square brackets (IMO) and in theory, more portable. We shall see. 

Onward!