#!/usr/bin/env python

import ez_setup
ez_setup.use_setuptools()

from setuptools import setup

from pg8000 import dbapi

long_description = \
"""pg8000 is a Pure-Python interface to the PostgreSQL database engine.  It is one
of many PostgreSQL interfaces for the Python programming language.  pg8000 is
somewhat distinctive in that it is written entirely in Python and does not rely
on any external libraries (such as a compiled python module, or PostgreSQL's
libpq library).  pg8000 supports the standard Python DB-API version 2.0.

pg8000's name comes from the belief that it is probably about the 8000th
PostgreSQL interface for Python."""

setup(
        name="pg8000",
        version=dbapi.__version__,
        description="PostgreSQL interface library",
        long_description=long_description,
        author="Mathieu Fenniak",
        author_email="biziqe@mathieu.fenniak.net",
        maintainer = "Mariano Reingart",
        maintainer_email = "reingart@gmail.com",
        url="http://code.google.com/p/pg8000",
        download_url="http://pg8000.googlecode.com/files/pg8000-%s.tar.gz" % dbapi.__version__,
        classifiers = [
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "License :: OSI Approved :: BSD License",
            "Programming Language :: Python",
            "Programming Language :: Python :: 2.5",
            "Programming Language :: Python :: 2.6",
            "Operating System :: OS Independent",
            "Topic :: Database :: Front-Ends",
            "Topic :: Software Development :: Libraries :: Python Modules",
        ],
        keywords="postgresql dbapi",
        zip_safe=True,
        tests_require=["pytz"],
        packages = ("pg8000",),
    )

