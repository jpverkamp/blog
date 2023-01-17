---
title: "A Justfile for my blog"
date: 2023-01-16
programming/languages:
- Rust
- Just
programming/topics:
- Rust
- Make
- Makefile
- Just
- Justfile
- Build
---
For a while now, I've been using [make](https://www.gnu.org/software/make/manual/make.html) as my task runner for my blog. `make run` to run locally, `make deploy` to build and push to GitHub pages. 

But... the syntax isn't great for some things and I've been working a lot with Rust. So let's see what [just](https://github.com/casey/just) can do!

<!--more-->

In a nutshell, here's where I am:

```text
LAST_COMMIT := `git log -1 --pretty=%B | head -n 1`

run:
	hugo server --watch --verbose --buildFuture --buildDrafts --bind 0.0.0.0 --port 80

debug:
	hugo server --watch --verbose --buildFuture --buildDrafts --bind 0.0.0.0 --port 80 --debug

import-flickr:
	python3 scripts/flickr.py --generate

review what:
	python3 scripts/review-{{what}}.py

detextbundle path:
	detextbundle \
	--output-root ~/Projects/blog/static \
	--output-assets embeds/books/attachments \
	--output-markdown - \
	--input "{{path}}" | pbcopy

build:
	if [ ! -d public ]; then git clone git@github.com:jpverkamp/jpverkamp.github.io.git public; fi
	cd public; git wipe; git pull --rebase --prune
	#rm -rf public/*
	
	hugo --minify

	cd public; mkdir -p feed; cp atom.xml feed/; cp atom.xml feed/index.html
	cd public; git status

deploy: build
	cd public; git add .
	cd public; git commit -m "Automatic deployment: {{LAST_COMMIT}}"
	cd public; git push origin master
```

Most of it's a 1 for 1 conversion. Instead of the previous make files, I instead have `just` rules. The interesting ones are `review what` (which takes a param, so that I can say `just review book` instead of remembering `python3 scripts/review-book.py`) and `detextbundle path` which wraps another script I wrote (I'll have to come back to that) and takes a review written as a [TextBundle](http://textbundle.org/) and pulls it into my blog. 

Pretty cool. 

Was it necessary? Nope. Neat though. We'll keep it for the moment. 