---
title: Crosslinks by Title in Hugo
date: 2021-07-15
programming/languages:
- Go
programming/topics:
- Hugo
---
Another quick Hugo post. One thing I miss about my previous blogging platform(s) was the ability to generate quick links between posts just by using the title of the post. So rather than this:

[[Crosslinks by Title in Hugo|a cool post]]()


```markdown
This is [a cool post]({{</* ref "2021-07-15-crosslinks-by-title-in-hugo" */>}}), go read it.
```

You could do this:

```markdown
This is {{</* crosslink title="Crosslinks by Title in Hugo" text="a cool post" */>}}.

Or shorter: {{</* crosslink "Crosslinks by Title in Hugo" */>}}.
```

And it should just work. 

<!--more-->

Here's version 1:

```text
{{- $title := or (.Get "title") (.Get 0) -}}
{{- $text := or (.Get "text") (.Get "title") (.Get 0) -}}

{{- $.Scratch.Set "written" false -}}

{{- range $page := .Site.AllPages -}}
    {{- if (and (not ($.Scratch.Get "written")) (eq $page.Title $title)) -}}
        <a href="{{ $page.Permalink }}">{{ $text }}</a>
        {{- $.Scratch.Set "written" true -}}
    {{- end -}}
{{- end -}}

{{- range $page := .Site.AllPages -}}
    {{- if (and (not ($.Scratch.Get "written")) (in $page.Title $title)) -}}
        <a href="{{ $page.Permalink }}">{{ $text }}</a>
        {{- $.Scratch.Set "written" true -}}
    {{- end -}}
{{- end -}}

{{- if (not ($.Scratch.Get "written")) -}}
{{ errorf "Failed to generate crosslink for title: %q, text: %q" $title $text }}
{{- end -}}
```

Is it an absolutely terrible / slow / brute force way to solve it? Oh yeah. It goes through every post twice, looking first for perfect matches by title and then if that doesn't work falling back to substrings. Does it work? Yup. And because of post ordering, it goes newest to oldest, which is kind of nice. 

I'll probably come back to see if I can optimize this somewhat (caching the results or even just the titles would probably go a long way towards it, although Hugo should do a chunk of that for me). But for now, it works. 

On the other hand, if anyone reading this already knows a better way to do this, I'd be happy to see it!