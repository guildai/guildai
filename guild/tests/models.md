# Models

Models play a central role in Guild commands. Models define the
operations that are performed by the `run` command. They are a
resource that can be discovered.

Models are discovered by looking for entry points in the
"guild.models" group. They can be discovered in the *project
directory* (either the current working directory or a location
specified by the user) or in Python distributions (i.e. installed
packages).
