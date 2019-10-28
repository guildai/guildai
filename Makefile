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

UAT_PYTHON = python3

uat:
	@test -e $(guild-uat) || $(guild) init -p 3 $(guild-uat) -y
	@. $(guild-uat)/bin/activate && \
	  WORKSPACE=$(guild-uat) $(guild) check --uat
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

# TODO Remove once OP2 is promoted
#
# The first list of skipped tests should be skipped because each is
# superceded by an OP2-xxx test. Tests in the second list should be
# fixed or replaced with the appropriate OP2-xxx test so that the list
# is eventually empty.
#
OP2-check:
	OP2=1 guild check -nT \
	-s batch-basics \
	-s batch-grid-search \
	-s batch-implied-random \
	-s batch-needed \
	-s batch-random-optimizer \
	-s batch-random-seeds \
	-s batch-restart \
	-s batch-save-trials \
	-s copy-sourcecode-warnings \
	-s cross-package-inheritance \
	-s dependencies-2 \
	-s marked-runs \
	-s needed \
	-s restart-runs \
	-s run-files \
	-s run-labels \
	-s skopt \
	-s sourcecode-digest \
	-s step-checks \
	-s steps \
	\
	-s batch-skopt \
	-s batch-skopt2
