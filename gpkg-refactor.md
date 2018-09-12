# gpkg refactor

- For package command, consider options to change the command passed
  to setup (e.g. to use `develop` rather than `bdist_wheel`. This
  should also accept additional options that are passed through to
  that command. Or maybe --setup-cmd which is a quoted string, e.g.

      guild package --setup-cmd 'develop -e'

  This would replace our default command.

- Possibly expose `namespace-packages` in Guild file package.
