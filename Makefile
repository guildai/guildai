OS = $(shell uname -s)

ifeq ($(OS),Linux)
    pip_plat_name_args = "-p manylinux_x86_64"
else
    pip_plat_name_args = ""
endif

guild = ./guild/scripts/guild
guild-uat = /tmp/guild-uat

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
	  opts="-n --tests"; \
	else \
	  opts="-n "; \
	  if [ "$(TESTS)" = "all" ]; then \
	    opts="$$opts --tests"; \
	  else \
	    for test in $(TESTS); do \
	      opts="$$opts -t $$test"; \
	    done; \
	  fi; \
	fi; \
	$(guild) check $$opts; \

lint:
	PYTHONPATH=guild/external pylint -rn -f parseable setup.py $(guild)

clean:
	rm -rf guild/external/
	rm -rf build/
	rm -rf dist/
	rm -rf guildai.egg-info/
	find -name *.pyc | grep -v guild/tests/samples | xargs -r rm
	rm -rf guild/view/node_modules

UAT_PYTHON = python3

uat:
	@test -e $(guild-uat) \
	  || virtualenv $(guild-uat) --python $(UAT_PYTHON)
	@. $(guild-uat)/bin/activate && pip install -qr requirements.txt
	@. $(guild-uat)/bin/activate \
	  && WORKSPACE=$(guild-uat) PATH=$$(pwd)/$$(dirname $(guild)):$$PATH guild check --uat
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
