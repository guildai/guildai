# Projects

>>> import guild.project

## Loading projects from a directory

Use `from_dir` to load a project from a directory:

>>> project = guild.project.from_dir(sample("projects/mnist"))
>>> project.srcs
['.../samples/projects/mnist/MODEL']

>>> [model.name for model in project]
['mnist-intro', 'mnist-expert']

## Loading projects from a file

Use `from_file` to load a project from a file directly:

>>> project = guild.project.from_file(sample("projects/mnist/MODEL"))
>>> [model.name for model in project]
['mnist-intro', 'mnist-expert']

## Errors

### Invalid format

>>> guild.project.from_dir(sample("projects/invalid-format"))
Traceback (most recent call last):
ProjectFormatError: .../samples/projects/invalid-format/MODEL

### No sources (i.e. MODEL or MODELS)

>>> guild.project.from_dir(sample("projects/missing-sources"))
Traceback (most recent call last):
NoSourcesError: .../samples/projects/missing-sources
