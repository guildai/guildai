# Guild tests

Guild tests can be run with the `check` command using the `-T` option
(`-n` here skips the general check info as we're just interested in
tests).

    >>> run("guild check -nT")
    internal tests:
      config:                  ok
      cpu-plugin:              ok
      disk-plugin:             ok
      imports:                 ok
      logging:                 ok
      main-bootstrap:          ok
      memory-plugin:           ok
      modelfiles:              ok
      models:                  ok
      namespaces:              ok
      ops:                     ok
      packages:                ok
      plugin-python-utils:     ok
      plugins:                 ok
      resources:               ok
      runs:                    ok
      tables:                  ok
      utils:                   ok
      var:                     ok
    <exit 0>
