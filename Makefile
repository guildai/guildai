GUILD = bazel-bin/guild/guild

build:
	bazel build guild

$(GUILD): build

pip-package:
	bazel build packaging/pip

check: $(GUILD)
	@if [ -z "$(TESTS)" ]; then \
	  opts="--tests"; \
	else \
	  opts="-s "; \
	  for test in $(TESTS); do \
	    opts="$$opts -t $$test"; \
	  done; \
	fi; \
	$(GUILD) check $$opts; \

lint:
	PYTHONPATH=bazel-bin/guild/guild.runfiles/org_click:bazel-bin/guild/guild.runfiles/org_tensorflow_tensorboard:bazel-bin/guild/guild.runfiles/org_psutil pylint -rn -f parseable guild

clean:
	bazel clean

smoke-test:
	guild/tests/smoke-test

timing-test:
	guild/tests/timing-test

commit-check:
	make check
	make lint
	make smoke-test
	make timing-test
	@echo "Commit check passed on `python --version 2>&1`!"
