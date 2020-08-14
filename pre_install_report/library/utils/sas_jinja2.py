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


class Jinja2TemplateRenderer(object):
    """
    Class for writing files based on Jinja2 templates.
    """
    def __init__(self, templates_dir='templates'):
        """
        Constructor for Jinja2TemplateRenderer.

        :param templates_dir: The directory containing templates.
        """
        self.file_loader = FileSystemLoader(templates_dir)

    def as_html(self, template_name, dest, *args, **kwargs):
        """
        Renders and writes html templates.

        :param template_name: The name of the template to use.
        :param dest:  The destination and name of the output file.
        :param args: Any single values needed to render the template.
        :param kwargs: Any keyworded values needed to render the template.
        :return: The absolute path to tne newly created file.
        """
        # create environment object for finding templates
        env = Environment(loader=self.file_loader, autoescape=select_autoescape(['html', 'xml']))

        # get the template
        template = env.get_template(template_name)

        # render the template
        contents = template.render(*args, **kwargs)

        # write the contents into the file
        with open(dest, 'w+') as f:
            f.write(contents)

        # return the absolute path to the new file
        return os.path.abspath(dest)
