#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name="omnistate",
    version="1.2.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "omnistate=omnistate.cli.main:main",
            "omnistate-mcp=omnistate.mcp.server:main",
        ],
    },
)
