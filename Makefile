.PHONY: build

build:
	python2 setup.py build
	python3 setup.py build

install-reqs:
	 pip install --user -r requirements.txt
	 pip3 install --user -r requirements.txt

pip-package:
	python2 setup.py bdist_wheel
	python3 setup.py bdist_wheel

pip-upload:
	make pip-package
	twine upload -si packages@guild.ai -u guildai dist/*.whl

check:
	@if [ -z "$(TESTS)" ]; then \
	  opts="--tests"; \
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
	guild/scripts/guild check $$opts; \

lint:
	PYTHONPATH=guild/external pylint -rn -f parseable setup.py guild

clean:
	rm -rf guild/external/
	rm -rf build/
	rm -rf dist/
	rm -rf guildai.egg-info/

uat:
	guild/scripts/guild check --uat

timing-test:
	guild/tests/timing-test

commit-check:
	make lint
	make check
	make uat
	make timing-test
	@echo "Commit check passed on `python --version 2>&1`"
