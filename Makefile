HUGO_IMAGE = klakegg/hugo:0.81.0
LAST_COMMIT = $(shell git log -1 --pretty=%B | head -n 1)

import-flickr:
	[ -f secrets.yaml ]

	# Import all my photosets from flickr and generate a page for each of them
	python3 scripts/flickr.py --generate

import-goodreads:
	[ -f secrets.yaml ]

	# Import recent reviews from goodreads and validate all goodreads shortcodes
	# To import all reviews, use --reviews all
	python3 scripts/goodreads.py -v import
	python3 scripts/goodreads.py -v validate

import: import-flickr import-goodreads

run:
	hugo server --watch --verbose --buildFuture --buildDrafts --bind 0.0.0.0 --port 80

debug:
	hugo server --watch --verbose --buildFuture --buildDrafts --bind 0.0.0.0 --port 80 --debug

build:
	if [ ! -d public ]; then git clone git@github.com:jpverkamp/jpverkamp.github.io.git public; fi
	cd public; git wipe; git pull --rebase --prune
	#rm -rf public/*
	
	hugo --minify

	cd public; mkdir -p feed; cp atom.xml feed/; cp atom.xml feed/index.html
	cd public; git status

deploy: build
	cd public; git add .
	cd public; git commit -m "Automatic deployment (${LAST_COMMIT})"
	cd public; git push origin master
