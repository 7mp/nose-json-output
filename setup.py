#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

import version as git_versioning


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

with open(os.path.join(os.path.dirname(__file__), 'README.md')) as f:
    readme = f.read()

package_data = {
}

requires = [
]

try:
    version = git_versioning.get_git_version()
except git_versioning.GitVersionNotFound:
    print >> sys.stderr, 'Could not determine git version. Please add a tag with "git tag -a" or "git tag -s"'
    sys.exit(1)

classifiers = [
    "Development Status :: 3 - Alpha",
    # "Development Status :: 4 - Beta",
    # "Development Status :: 5 - Production/Stable",
    # "Development Status :: 6 - Mature",
    # "Development Status :: 7 - Inactive",
    "Environment :: Plugins",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    "Operating System :: OS Independent",
    "Programming Language :: Python",
    "Topic :: Software Development :: Testing",
]

setup(
    author='Tommi Penttinen',
    author_email='penttinen.tommi@gmail.com',
    classifiers=classifiers,
    description='nosetests plugin for formatting log output as JSON (e.g. for use with websocketsd)',
    entry_points={
	'nose.plugins.0.10': [
	    'json_logger = json_logger.plugin:JsonLogCapture',
	    'json_runner = json_logger.runner:HtmlOutput',
	    ]
	},
    install_requires=requires,
    license=license, # 'BSD', 'MIT'
    long_description=readme,
    name='nose-json-logger',
    package_data=package_data,
    packages=find_packages(exclude=['tests']),
    url='https://github.com/7mp/nose-json-logger',
    version=version,
)
