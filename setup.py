#!/usr/bin/env python

####################################################################
# ### setup.py                                                   ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

from setuptools import find_packages, setup

setup(
    setup_requires=["pbr"],
    pbr=True,
    licenses_files=["LICENSE"],
    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),
    python_requires=">=3.6",
)
