# Notes on Windows support

## Building Guild

- Install Python
- Install Node with npm
- Install C++ build tools (see below)
- Clone repo
- Install packages in requirements.txt (`pip install -r requirements.txt`)
- Build wheel (`python setup.py bdist_wheel`)

Helpful links for C++ dev tools:

- https://www.scivision.dev/python-windows-visual-c-14-required/
- https://aka.ms/vs/15/release/vs_buildtools.exe

## Running Guild from source

- Include `guild/guild/scripts` in path

## Using Guild

### Symbolic links

At least when running from source, symlinks fail with "symbolic link
privilege not held". The workaround is to run the command console as
Admin. In theory adding "Create symbolic links" priviledge (Local
Group Policy Editor under Compuater Configuration > Windows Settings >
Security Settings > Local Policies > User Rights Assignment) should
work, but it didn't. I tried both "Everyone" and my user.

### Curses

Windows needs a separate curses library.
