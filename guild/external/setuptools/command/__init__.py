__all__ = [
    'alias', 'bdist_egg', 'bdist_rpm', 'build_ext', 'build_py', 'develop',
    'easy_install', 'egg_info', 'install', 'install_lib', 'rotate', 'saveopts',
    'sdist', 'setopt', 'test', 'install_egg_info', 'install_scripts',
    'bdist_wininst', 'upload_docs', 'build_clib', 'dist_info',
]

# HACK: macos has some issue with sysconfig not being present on some OS/python combinations.
#    the next couple of lines should fix it.
import distutils
from distutils.sysconfig import get_python_lib
get_python_lib()

from distutils.command.bdist import bdist
import sys

from setuptools.command import install_scripts

if 'egg' not in bdist.format_commands:
    bdist.format_command['egg'] = ('bdist_egg', "Python .egg file")
    bdist.format_commands.append('egg')

del bdist, sys
