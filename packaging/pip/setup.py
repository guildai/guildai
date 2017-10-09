import os
import sys

from setuptools import find_packages, setup

def README():
    path = os.path.join(os.path.dirname(__file__), "README.rst")
    return open(path).read()

def packages():
    return find_packages(exclude=["guild.tests", "guild.tests.*"])

def package_files(pkg, dirs):
    return list(_iter_package_files(pkg, dirs))

def _iter_package_files(pkg, dirs):
    for dir in dirs:
        for root, _, files in os.walk(os.path.join(pkg, dir)):
            pkg_relative_root = root[len(pkg) + 1:]
            for name in files:
                yield os.path.join(pkg_relative_root, name)

setup(
    name="guildai",
    version="0.1.0",
    description="The essential TensorFlow developer toolkit",
    long_description=README(),
    url="https://github.com/guildai/guild-python",
    author="TensorHub, Inc.",
    author_email="garrett@guild.ai",
    packages=packages(),
    package_data={
        "guild": (
            ["guild"] +
            package_files("guild", ["tests", "scripts"])
        ),
        "tensorboard": ["webfiles.zip",],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Education',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Software Development :: Libraries',
    ],
    license="Apache 2.0",
    keywords="guild guildai tensorflow machine learning",
)
