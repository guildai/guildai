import os
import sys

from setuptools import find_packages, setup

def README():
    path = os.path.join(os.path.dirname(__file__), "README.rst")
    return open(path).read()

def packages():
    return ["guild"] + find_packages("external")

print("#######################")
print(os.listdir("."))
print("#######################")

"""
setup(
    name="guildai",
    version="0.1.0",
    description="The essential TensorFlow developer toolkit",
    long_description=README(),
    url="https://github.com/guildai/guild-python",
    author="TensorHub, Inc.",
    author_email="garrett@guild.ai",
    packages=packages(),
    #entry_points={
    #    "console_scripts": ["guild=guild.main:main"],
    #},
    package_data={
        "guild": [
            "scripts/*",
            "tests",
        ],
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
"""
