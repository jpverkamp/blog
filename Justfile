LAST_COMMIT := `git log -1 --pretty=%B | head -n 1`

run baseURL="localhost":
	npm_config_yes=true npx pagefind --site "public" --output-subdir ../static/pagefind
	hugo server \
		--baseURL {{baseURL}}		\
		--watch --logLevel info 	\
		--buildFuture --buildDrafts \
		--bind 0.0.0.0 --port 80    \
		--disableKinds RSS			


debug baseURL="localhost":
	npm_config_yes=true npx pagefind --site "public" --output-subdir ../static/pagefind
	hugo server \
		--baseURL {{baseURL}} 		\
		--watch --logLevel debug	\
		--buildFuture --buildDrafts \
		--disableKinds RSS			\
		--bind 0.0.0.0 --port 80 	\
		--printI18nWarnings        	\
		--printMemoryUsage         	\
		--printPathWarnings        	\
		--printUnusedTemplates     	\
		--templateMetrics          	\
		--templateMetricsHints		

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
	cd public; git wipe; git pull --rebase --prune; git submodule update --init --recursive
	
	hugo --minify
	npx pagefind --site "public"

	cd public; mkdir -p feed; cp atom.xml feed/; cp atom.xml feed/index.html
	cd public; git status

check-drafts:
	@if grep -iR "draft: true" content; then \
		echo "Draft(s) found. Proceed? [y/N]"; \
		read ans; \
		case "$ans" in \
			[Yy]* ) \
				echo "Proceeding...";; \
			* ) \
				exit 1; \
		esac \
	fi

deploy: check-drafts push build
	cd public; git add .
	cd public; git commit -m "Automatic deployment: {{LAST_COMMIT}}"
	cd public; git push origin master
