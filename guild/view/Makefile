lint:
	npm run lint -- -f unix

dev:
	npm run dev

.PHONY: dist
dist: clean
	npm run build

clean:
	rm -rf dist

serve-dist:
	cd dist; python -m SimpleHTTPServer

install:
	npm install
