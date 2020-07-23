####################################################################
# ### command.py                                                 ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from abc import ABC, abstractmethod
from typing import List, Text


class Command(ABC):
    """
    Abstract Base Class for implementing a command-driven task in the viya-arkcd project.
    """

    @staticmethod
    @abstractmethod
    def run(argv: List) -> None:
        """
        Abstract method used to invoke the command-driven task from the launcher script.

        :param argv: The arguments passed to the program at execution.
        """
        pass

    @staticmethod
    @abstractmethod
    def command_name() -> Text:
        """
        Abstract method used to by the launcher script to get the task's command-line name value.

        :return: The displayable command name.
        """
        pass

    @staticmethod
    @abstractmethod
    def command_desc() -> Text:
        """
        Abstract method used by the launcher script to get the task's human-friendly description.

        :return: The displayable command description.
        """
        pass
