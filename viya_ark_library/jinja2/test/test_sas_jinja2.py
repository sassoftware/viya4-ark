####################################################################
# ### test_sas_jinja2.py                                         ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import os

from viya_ark_library.jinja2.sas_jinja2 import Jinja2TemplateRenderer


def test_as_html():
    # get the current directory of this script to create absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # join the path to this file with the remaining path to the requested test data
    templates_dir = os.path.join(current_dir, "templates")

    jinja2_renderer = Jinja2TemplateRenderer(templates_dir)

    created_file = jinja2_renderer.as_html("unit_test.html.j2", "unit_test.html", test_page_content="Hello World!")

    assert os.path.exists(created_file)
    assert os.path.isfile(created_file)
    assert os.stat(created_file).st_size != 0

    # clean up file
    os.remove(created_file)


def test_as_html_non_utf8_content():
    # get the current directory of this script to create absolute path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # join the path to this file with the remaining path to the requested test data
    templates_dir = os.path.join(current_dir, "templates")

    jinja2_renderer = Jinja2TemplateRenderer(templates_dir)

    created_file = jinja2_renderer.as_html("unit_test.html.j2", "unit_test.html",
                                           test_page_content="None unicode test value: "
                                                             + u"\x54\xea\x73\x74 \x56\xe3\x6c\xfc\xeb")

    assert os.path.exists(created_file)
    assert os.path.isfile(created_file)
    assert os.stat(created_file).st_size != 0

    # clean up file
    os.remove(created_file)
