GUILD = bazel-bin/guild/guild

build:
	bazel build guild

$(GUILD): build

pip-package:
	bazel build packaging/pip

pip-upload:
	rm -f bazel-genfiles/packaging/pip/*
	make pip-package
	twine upload -si packages@guild.ai -u guildai bazel-genfiles/packaging/pip/*.whl

check: $(GUILD)
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
	$(GUILD) check $$opts; \

lint:
	PYTHONPATH=bazel-bin/guild/guild.runfiles/org_click:bazel-bin/guild/guild.runfiles/org_tensorflow_tensorboard:bazel-bin/guild/guild.runfiles/org_psutil pylint -rn -f parseable guild

clean:
	bazel clean

uat:
	$(GUILD) check --uat

timing-test:
	guild/tests/timing-test

commit-check:
	make check
	make lint
	make user-acceptance-test
	make timing-test
	@echo "Commit check passed on `python --version 2>&1`"
