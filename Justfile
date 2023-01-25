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

push:
	git push origin HEAD

build:
	if [ ! -d public ]; then git clone git@github.com:jpverkamp/jpverkamp.github.io.git public; fi
	cd public; git wipe; git pull --rebase --prune
	#rm -rf public/*
	
	hugo --minify

	cd public; mkdir -p feed; cp atom.xml feed/; cp atom.xml feed/index.html
	cd public; git status

deploy: push build
	cd public; git add .
	cd public; git commit -m "Automatic deployment: {{LAST_COMMIT}}"
	cd public; git push origin master
	