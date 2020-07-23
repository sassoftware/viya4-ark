####################################################################
# ### sas_jinja2.py                                              ###
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
from jinja2 import Environment, FileSystemLoader, select_autoescape
from typing import AnyStr, List, Text, Union


class Jinja2TemplateRenderer(object):
    """
    Class for writing files based on Jinja2 templates.
    """

    def __init__(self, templates_dir: Union[Text, List] = "templates") -> None:
        """
        Constructor for Jinja2TemplateRenderer.

        :param templates_dir: The directory containing templates.
        """
        # get the path to the common templates
        common_templates_dir: Text = os.path.abspath(
            os.path.dirname(os.path.realpath(__file__)) + os.sep + ".." + os.sep + "templates")

        templates: List = list()
        if isinstance(templates_dir, list):
            templates.extend(templates_dir)
            templates.append(common_templates_dir)
        else:
            templates.append(templates_dir)
            templates.append(common_templates_dir)

        self.file_loader: FileSystemLoader = FileSystemLoader(templates)

    def as_html(self, template_name: Text, destination: Text, trim_blocks: bool = False, lstrip_blocks: bool = False,
                *args, **kwargs) -> AnyStr:
        """
        Renders and writes html templates.

        :param template_name: The name of the template to use.
        :param destination:  The destination and name of the output file.
        :param trim_blocks: If set to True the first newline after a block is removed. Defaults to False.
        :param lstrip_blocks: If set to True leading spaces and tabs are stripped from start of a block line. Defaults
                              to False.
        :param args: Any single values needed to render the template.
        :param kwargs: Any keyword-ed values needed to render the template.
        :return: The absolute path to tne newly created file.
        """
        # create environment object for finding templates #
        env: Environment = Environment(loader=self.file_loader, autoescape=select_autoescape(["html", "xml"]),
                                       trim_blocks=trim_blocks, lstrip_blocks=lstrip_blocks)

        # get the template #
        template = env.get_template(template_name)

        # render the template #
        contents: Text = template.render(*args, **kwargs)

        # write the contents into the file #
        with open(destination, "w+") as f:
            f.write(contents)

        # return the absolute path to the new file #
        return os.path.abspath(destination)
