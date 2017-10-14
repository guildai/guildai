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
	PYTHONPATH=bazel-bin/guild/guild.runfiles/org_click pylint -rn guild

clean:
	bazel clean

commit-check:
	make
	make check
	make lint

pip-package-linux:
	bazel build packaging/pip:linux
