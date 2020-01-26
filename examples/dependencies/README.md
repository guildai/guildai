# Guild Example: `dependencies`

This example illustrates various dependencies.

- [guild.yml](guild.yml) - Project Guild file
- [file.txt](file.txt) - Sample file used in dependency examples
- [file2.txt](file2.txt) - Sample file used in dependency examples

Supported operations:

```
exit-123           Generates an error with exit code 123
file               Requires a single project file
gen-file           Generate an empty file
missing-dep        Illustrates an error for missing file
process-error      Generates a process error for an invalid command
requires-any-file  Requires file provided by various options
requires-file-op   Requires file provided by file operation
```
