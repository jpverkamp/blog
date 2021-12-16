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
	sleep 30 && open http://localhost/ &
	
	docker run --rm -it -p 80:80 \
		-v $(shell pwd):/src \
		-v /cache \
		${HUGO_IMAGE} \
		server \
			--verbose \
			--buildFuture \
			--cacheDir /cache \
			--bind 0.0.0.0 --port 80

build:
	if [ ! -d public ]; then git clone git@github.com:jpverkamp/jpverkamp.github.io.git public; fi
	cd public; git wipe; git up
	#rm -rf public/*
	
	docker run --rm -it \
		-v $(shell pwd):/src \
		${HUGO_IMAGE}

	cd public; mkdir -p feed; cp atom.xml feed/; cp atom.xml feed/index.html
	cd public; git status

deploy: build
	cd public; git add .
	cd public; git commit -m "Automatic deployment (${LAST_COMMIT})"
	cd public; git push origin master
