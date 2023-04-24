OS = $(shell uname -s)
BUILD_GUILD_VIEW ?= ""
PYTHON ?= python
PIP := pip
SHELL := bash

ifeq ($(OS),Linux)
    pip_plat_name_args = "-p manylinux_x86_64"
else
    pip_plat_name_args = ""
endif

ifneq ($(wildcard /tmp/.*),)
	NATIVE_TMP = /tmp
	UNIX_TMP = /tmp
	native-guild-uat = /tmp/guild-uat
else
	NATIVE_TMP = "C:\\tmp"
	UNIX_TMP = /c/tmp
	native-guild-uat = $(NATIVE_TMP)\\guild-uat
endif

guild = ./guild/scripts/guild
guild-uat = $(UNIX_TMP)/guild-uat

.PHONY: build

build:
	BUILD_GUILD_VIEW=$(BUILD_GUILD_VIEW) $(PYTHON) setup.py build

install-reqs:
	 pip install --user -r requirements.txt

pip-package:
	rm -rf build
	BUILD_GUILD_VIEW=$(BUILD_GUILD_VIEW) $(PYTHON) setup.py bdist_wheel -p manylinux1_x86_64

pip-upload:
	make pip-package
	export VER=`$(PYTHON) -c 'import guild; print(guild.__version__)'`; \
	export TWINE_PASSWORD=`gpg --quiet --batch -d .pypi-creds.gpg`; \
	twine upload -si packages@guild.ai -u guildai dist/guildai-$$VER*.whl

pip-clean:
	rm -rf build dist guildai.egg-info

check:
	@opts="--fast -c8"; \
	command -v notify-send2; \
	if [ -x "$(command -v notify-send)" ]; then \
	  opts="$$opts --notify"; \
	fi; \
	if [ -z "$(TESTS)" -o "$(TESTS)" = "all" ]; then \
	  opts="$$opts --tests"; \
	else \
	  for test in $(TESTS); do \
	    opts="$$opts -t $$test"; \
	  done; \
	fi; \
	echo guild check $$opts; \
	COLUMNS=999 \
        GUILD_START_THRESHOLD=0.5 \
	BREAKPOINT_PROMPT_TIMEOUT=4 \
	$(guild) check $$opts

lint:
	pylint setup.py tools.py guild

clean:
	rm -rf guild/external/.psutil*
	rm -rf guild/external/psutil*
	rm -rf guild/external/.click*
	rm -rf guild/external/click*
	rm -rf build/
	rm -rf dist/
	rm -rf guildai.egg-info/
	find -name *.pyc | grep -v guild/tests/samples | xargs rm
	rm -rf guild/view/node_modules
	rm -rf .coverage coverage

uat:
	@test -e $(guild-uat) || $(guild) init -p $(PYTHON) $(guild-uat) -y
	@. $(guild-uat)/bin/activate && WORKSPACE=$(guild-uat) EXAMPLES=examples \
	  $(guild) check --uat --notify --concurrency 8
	@echo "Run 'make clean-uat' to remove uat workspace for re-running uat"

clean-uat:
	rm -rf $(guild-uat)

timing-test:
	guild/tests/timing-test

commit-check:
	make lint
	make check
	make uat
	make timing-test
	@echo "Commit check passed on `$(PYTHON) --version 2>&1`"

README.html: README.md
	markdown_py README.md > README.html

format-code:
	@echo Formating Guild source code
	@yapf -ri setup.py tools.py guild examples

coverage-check:
	if [ -z "$(TESTS)" ]; then \
	  tests="-St"; \
	else \
	  for test in $(TESTS); do \
	    tests="$$tests -t $$test"; \
	  done; \
	fi; \
	coverage run -a -m guild.main_bootstrap check $$tests

coverage-report:
	coverage report -m --include=guild/* --omit=guild/_lex.py,guild/_yacc.py,guild/external/*

coverage-annotate:
	coverage annotate -d coverage --include=guild/* --omit=guild/_lex.py,guild/_yacc.py,guild/external/*

coverage-clean:
	rm -rf .coverage coverage

coverage:
	make coverage-clean
	make coverage-check
	make coverage-annotate
	make coverage-report

unused-code:
	python tools.py --unused-code
