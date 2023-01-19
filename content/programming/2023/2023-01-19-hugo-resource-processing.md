---
title: "Local JS/CSS with Hugo Pipe"
date: 2023-01-19
programming/languages:
- Javascript
- Go
programming/topics:
- Hugo
---
I recently stumbled across a post that reminded me that [Hugo has pipes](https://gohugo.io/hugo-pipes/introduction/). You can use them to automatically download files and include them as local. This seems like a pretty good idea for JS/CSS (you can argue caching versus security/locality all you want), but I'm going to give it a try.

<!--more-->

In a diff:

```diff
-<link rel="alternate" type="application/atom+xml" title="jverkamp.com (Atom 2.0)" href="//blog.jverkamp.com/feed/">
-
-<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.9.0-alpha2/katex.min.css" integrity="sha384-exe4Ak6B0EoJI0ogGxjJ8rn+RN3ftPnEQrGwX59KTCl5ybGzvHGKjhPKk/KC3abb" crossorigin="anonymous">
-<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/bigfoot/2.1.4/bigfoot-default.min.css" integrity="sha256-s0KLB0LnI5oqhHF8gkgfmxU4usUFEHlWJTxT8q72Tq4=" crossorigin="anonymous" />
-<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/fancybox/3.5.7/jquery.fancybox.min.css" integrity="sha256-Vzbj7sDDS/woiFS3uNKo8eIuni59rjyNGtXfstRzStA=" crossorigin="anonymous" />
-
-<link href="https://fonts.googleapis.com/css?family=Spectral+SC|Lato|Share+Tech+Mono" rel="stylesheet">
-
-<link rel="stylesheet" href="/custom.css" defer />
+{{- $styles := slice
+    "https://cdnjs.cloudflare.com/ajax/libs/KaTeX/0.16.4/katex.css"
+    "https://cdnjs.cloudflare.com/ajax/libs/bigfoot/2.1.4/bigfoot-default.css"
+    "https://cdnjs.cloudflare.com/ajax/libs/fancybox/3.5.7/jquery.fancybox.css"
+    "https://fonts.googleapis.com/css?family=Spectral+SC|Lato|Share+Tech+Mono"
+-}}
+{{- range $styles -}}
+{{- $script := resources.GetRemote . | minify | fingerprint }}
+    <link rel="stylesheet" href="{{ $script.RelPermalink }}" integrity="{{ $script.Data.Integrity }}"></script>
+{{- end }}
+    <link rel="stylesheet" href="/custom.css" />
```

Basically, I make a `slice` of `$styles`, then for each use `resources.GetRemote` to download, `minify` (compress), and `fingerprint` (make a unique filename) it. Use that as a local permalink instead of the remote link and you're good to go. 

The attack would be modifying the script at the time of build rather than at the time of fetch, but I'm okay with that. 

Onward!