last_commit = $(shell git log -1 --pretty=%B | head -n 1)

import:
	# Require that the secrets file exists
	[ -f secrets.yaml ]

	# Import all my photosets from flickr and generate a page for each of them
	python3 scripts/import-flickr.py --generate

	# Import recent reviews from goodreads and validate all goodreads shortcodes
	# To import all reviews, use --reviews all
	python3 scripts/import-goodreads.py --reviews --validate

run:
	sleep 10 && open http://localhost:1313/ &
	hugo server --buildFuture

build:
	if [ ! -d public ]; then git clone git@github.com:jpverkamp/jpverkamp.github.io.git public; fi
	cd public; git wipe; git up
	rm -rf public/*
	hugo
	cd public; mkdir -p feed; cp atom.xml feed/; cp atom.xml feed/index.html
	cd public; git status

test:
	echo ${last_commit}

deploy: build
	cd public; git add .
	cd public; git commit -m "Automatic deployment (${last_commit})"
	cd public; git push origin master
