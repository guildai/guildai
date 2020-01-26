# Guild Example: `hello-package`

This example modifies the [hello](../hello/README.md) example to
include support for packaging.

- [guild.yml](guild.yml) - Project Guild file
- [say.py](say.py) - Prints a greeting
- [cat.py](cat.py) - Prints contents of a file
- [hello.txt](hello.txt) - Sample file used by `hello-file` operation

The Guild file is modified to support packaging with a few
modifications:

- Promote the Guild file format from _operation only_ to _full_
  format. This moves the operations under a model definition. We use
  the anonymous model (named with an empty string) to maintain the
  original interface.

- Add a `package` top-level object to the Guild file. This defines the
  package name and defines the data files that should be included in
  the package.

With package support, the `hello-file` operation can be run on remote
servers. Without this change, the file `hello.txt` would not be
included in the package installed on remote systems.

All of the steps outlined in the [hello](../hello/README.md) can be
run with this example on a remote. Include the additional option
`--remote NAME` for each command that you want to run remotely.
