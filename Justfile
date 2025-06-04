LAST_COMMIT := `git log -1 --pretty=%B | head -n 1`

run baseURL="localhost":
	npm_config_yes=true npx pagefind --site "build/run" --output-subdir ../static/pagefind
	just --justfile {{justfile()}} run-hugo "{{baseURL}}"

run-hugo baseURL="localhost":
	hugo server \
		--baseURL {{baseURL}}		\
		--environment staging		\
		--destination build/run     \
		--watch --logLevel info 	\
		--buildFuture --buildDrafts \
		--bind 0.0.0.0 --port 80

debug baseURL="localhost":
	npm_config_yes=true npx pagefind --site "build/debug" --output-subdir ../static/pagefind
	just --justfile {{justfile()}} run debug-hugo "{{baseURL}}"

debug-hugo baseURL="localhost":
	hugo server \
		--baseURL {{baseURL}} 		\
		--environment development	\
		--destination build/debug   \
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
	if [ ! -d build/release ]; then mkdir -p build; git clone git@github.com:jpverkamp/jpverkamp.github.io.git build/release; fi
	cd build/release; git wipe; git pull --rebase --prune; git submodule update --init --recursive
	
	hugo --minify --destination build/release
	npx pagefind --site "build/release"

	cd build/release; mkdir -p feed; cp atom.xml feed/; cp atom.xml feed/index.html
	cd build/release; git status

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
	cd build/release; git add .
	cd build/release; git commit -m "Automatic deployment: {{LAST_COMMIT}}"
	cd build/release; git push origin master
