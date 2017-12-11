import:
	# These will be removed once the old blog is imported
	#rm -rf content/*
	#rm -rf static/embeds/[0-9]* static/embeds/movies
	#python3 scripts/import-old-blog.py ../blog/

	# Import all my photosets from flickr and generate a page for each of them
	python3 scripts/import-flickr.py --generate

	# Import recent reviews from goodreads and validate all goodreads shortcodes
	# To import all reviews, use --reviews all
	python3 scripts/import-goodreads.py --reviews --validate
	#python3 scripts/import-goodreads.py --reviews all --validate

run:
	hugo server

build:
	hugo
