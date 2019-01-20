# Guild tests

Guild tests can be run with the `check` command using the `-T` option
(`-n` here skips the general check info as we're just interested in
tests).

    >>> run("guild check -nT", timeout=120) # doctest: +REPORT_UDIFF
    internal tests:
      anonymous-models:          ok
      batch-1:                   ok
      batch-2:                   ok
      config:                    ok
      copy-source:               ok
      cpu-plugin:                ok
      cross-package-inheritance: ok
      dependencies:              ok
      disk-plugin:               ok
      entry-points:              ok
      flags-dest:                ok
      guild-test:                ok
      guildfiles:                ok
      help:                      ok
      import-flags:              ok
      imports:                   ok
      includes:                  ok
      index2:                    ok
      init:                      ok
      logging:                   ok
      ls-cmd:                    ok
      main-bootstrap:            ok
      memory-plugin:             ok
      models:                    ok
      namespaces:                ok
      op-utils:                  ok
      ops:                       ok
      package:                   ok
      plugins:                   ok
      python-utils:              ok
      query-parser:              ok
      run-flags:                 ok
      run-ops:                   ok
      run-output:                ok
      run-scripts:               ok
      runs:                      ok
      steps:                     ok
      tables:                    ok
      tfevents:                  ok
      utils:                     ok
      var:                       ok
    <exit 0>
