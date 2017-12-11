last_commit = $(shell git log -1 --pretty=%B | head -n 1)

import:
	# Import all my photosets from flickr and generate a page for each of them
	python3 scripts/import-flickr.py --generate

	# Import recent reviews from goodreads and validate all goodreads shortcodes
	# To import all reviews, use --reviews all
	python3 scripts/import-goodreads.py --reviews --validate

run:
	hugo server

build:
	if [ ! -d public ]; then git clone git@github.com:jpverkamp/jpverkamp.github.io.git public; fi
	rm -rf public/*
	hugo
	cd public; git status

test:
	echo ${last_commit}

deploy: build
	cd public; git add .
	cd public; git commit -m "Automatic deployment (${last_commit})"
	cd public; git push origin master
