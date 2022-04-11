OS = $(shell uname -s)

ifeq ($(OS),Linux)
    pip_plat_name_args = "-p manylinux_x86_64"
else
    pip_plat_name_args = ""
endif

ifneq ($(wildcard /tmp/.*),)
	NATIVE_TMP = /tmp
	UNIX_TMP = /tmp
	native-guild-uat = /tmp/guild-uat
	ACTIVATE_FOLDER = "bin"
else
	NATIVE_TMP = "C:\tmp"
	UNIX_TMP = /c/tmp
	native-guild-uat = "$(NATIVE_TMP)\guild-uat"
	ACTIVATE_FOLDER = "Scripts"
endif

guild = ./guild/scripts/guild
guild-uat = $(UNIX_TMP)/guild-uat

.PHONY: build

build:
	python2 setup.py build
	python3 setup.py build

install-reqs:
	 pip install --user -r requirements.txt
	 pip3 install --user -r requirements.txt

pip-package:
	rm -rf build
	python2 setup.py bdist_wheel -p manylinux1_x86_64
	python3 setup.py bdist_wheel -p manylinux1_x86_64

pip-upload:
	make pip-package
	export VER=`python -c 'import guild; print(guild.__version__)'`; \
	export TWINE_PASSWORD=`gpg --quiet --batch -d .pypi-creds.gpg`; \
	twine upload -si packages@guild.ai -u guildai dist/guildai-$$VER*.whl

pip-clean:
	rm -rf build dist guildai.egg-info

check:
	@if [ -z "$(TESTS)" ]; then \
	  opts="-n --tests --notify"; \
	else \
	  opts="-n "; \
	  if [ "$(TESTS)" = "all" ]; then \
	    opts="$$opts --tests --notify"; \
	  else \
	    for test in $(TESTS); do \
	      opts="$$opts -t $$test"; \
	    done; \
	  fi; \
	fi; \
	COLUMNS=999 $(guild) check $$opts; \

lint:
	PYTHONPATH=guild/external pylint -rn -f parseable setup.py guild

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

UAT_PYTHON ?= python3.6

uat:
	mkdir -p $(UNIX_TMP)
	@test -e $(guild-uat) || $(guild) init -p $(UAT_PYTHON) $(native-guild-uat) -y
	@. $(guild-uat)/$(ACTIVATE_FOLDER)/activate && WORKSPACE=$(native-guild-uat) EXAMPLES=examples $(guild) check --uat --notify
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
	@echo "Commit check passed on `python --version 2>&1`"

README.html: README.md
	markdown_py README.md > README.html

format-code:
	@echo Formatting guild code
	@black guild

coverage-check:
	@if [ -z "$(TESTS)" ]; then \
	  tests="-St"; \
	else \
	  for test in $(TESTS); do \
	    tests="$$tests -t $$test"; \
	  done; \
	fi; \
	coverage run -a -m guild.main_bootstrap check -n $$tests

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

disabled-tests:
	@find guild/tests -name '*.md' | xargs grep -HE '^ *>> ' || true
