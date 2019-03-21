# Guild tests

Guild tests can be run with the `check` command using the `-T` option
(`-n` here skips the general check info as we're just interested in
tests).

    >>> run("guild check -nT", timeout=600) # doctest: +REPORT_UDIFF
    internal tests:
      anonymous-models:            ok
      batch-basics:                ok
      batch-custom-optimizer:      ok
      batch-grid-search:           ok
      batch-guildfile-optimizers:  ok
      batch-implied-random:        ok
      batch-needed:                ok
      batch-print-cmd:             ok
      batch-random-optimizer:      ok
      batch-random-seeds:          ok
      batch-restart:               ok
      batch-skopt:                 ok
      config:                      ok
      copy-source:                 ok
      cpu-plugin:                  ok
      cross-package-inheritance:   ok
      dependencies:                ok
      dependencies-2:              ok
      disk-plugin:                 ok
      entry-points:                ok
      flag-functions:              ok
      flagdefs:                    ok
      flags-dest:                  ok
      guildfiles:                  ok
      help:                        ok
      import-flags:                ok
      imports:                     ok
      includes:                    ok
      index2:                      ok
      init:                        ok
      keras:                       ok
      logging:                     ok
      ls-cmd:                      ok
      main-bootstrap:              ok
      marked-runs:                 ok
      memory-plugin:               ok
      model-proxies:               ok
      models:                      ok
      namespaces:                  ok
      needed:                      ok
      op-utils:                    ok
      ops:                         ok
      package:                     ok
      plugins:                     ok
      python-utils:                ok
      query-parser:                ok
      remotes:                     ok
      restart-runs:                ok
      run-files:                   ok
      run-flags:                   ok
      run-ops:                     ok
      run-output:                  ok
      run-scripts:                 ok
      runs-1:                      ok
      runs-2:                      ok
      skopt:                       ok
      skopt-utils:                 ok
      step-checks:                 ok
      steps:                       ok
      tables:                      ok
      tfevents:                    ok
      utils:                       ok
      var:                         ok
    <exit 0>
