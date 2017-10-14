GUILD = bazel-bin/guild/guild

build:
	bazel build guild

$(GUILD): build

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

commit-check:
	make smoke-test
	make lint

pip-package-linux:
	bazel build packaging/pip:linux
