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

# get the install requirements from requirements.txt
with open("requirements.txt") as requirements_file:
    install_requirements = requirements_file.read().splitlines()

setup(
    # UPDATE VERSION WITH EACH RELEASE
    ##################################
    version="1.3.1",
    ##################################
    name="viya4-ark",
    author="SAS Institute Inc.",
    author_email="Josh.Woods@sas.com",

    license="Apache-2.0",
    licenses_files=["LICENSE"],

    description=("The SAS Viya Administration Resource Kit (SAS Viya ARK) provides tools and utilities to help SAS "
                 "customers prepare for and gather information about a SAS Viya deployment."),
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",

    url="https://github.com/sassoftware/viya4-ark",

    packages=find_packages(exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),

    python_requires=">=3.6",
    # these are setup to match the definitions in requirements.txt
    install_requires=install_requirements
)
