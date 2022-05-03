# Contributing to Guild AI

Please read this document before you send a patch:

- Guild AI uses the [Collective Code Construction
  Contract](https://rfc.zeromq.org/spec/42/) process for
  contributions. Please read this if you are unfamiliar with it.

Guild AI grows by the slow and careful accretion of simple, minimal
solutions to real problems faced by many people.

- Each patch defines one clear and agreed problem, and one clear,
  minimal, plausible solution. Avoid large, complex problems and
  large, complex solutions.

- We will usually merge patches aggressively, without a blocking
  review.

- Merged patches typically undergo revisions by maintainers or other
  contributes. If a merged patch cannot be appropriately revised we
  will remove it with reverting patch along with an explanation.

This contribution policy is adapted from the [Zero MQ
project](https://github.com/zeromq/czmq/blob/master/CONTRIBUTING.md)
and authored primarily by our late friend [Pieter
Hintjens](https://github.com/hintjens).

# Tests

Tests are written as doctests. Unit-style tests are in the guild/tests folder, and higher-level "user acceptance tests" (UAT) are in the guild/tests/uat folder.

You can run tests a few ways:

* `make check` will run the tests in the guild/tests folder. You can limit this to a particular test file by passing a space-separated string of tests. For example, `make check TESTS="autocomplete notebook-exec"`
* `make uat` will run the user acceptance tests. These tests are executed in order according to the guild/tests/uat/README.md file. There is no way to select a particular test file, because several of these files depend on earlier files. You can skip tests by creating files that match the test filename in the passed-tests folder. For example, `touch /tmp/guild-uat/passed-tests/guild-example-hello` would skip the guild-example-hello test the next time you run `make uat`.
* run `guild check` for more fine-grained control. See `guild check --help` for more info.

# Releasing

Release automation is done with Github Actions. All you need to do is make an annotated tag and push it to the guild repo. An annotated tag is done with `git tag -a <version>`. In the annotation, copy/paste the changelog for your release.

There are two places that packages may be sent. If a tag has "dev" or "rc" in it, it will be uploaded to test PyPI, https://test.pypi.org/project/guildai/. You can use the --extra-index-url flag for pip to install from test PyPI. If the tag does not contain "dev" or "rc", it will be uploaded to PyPI, https://pypi.org/project/guildai/
