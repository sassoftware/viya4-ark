####################################################################
# ### viya-ark.py                                                ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

import importlib
import inspect
import os
import pkgutil
import sys

from viya_ark_library.command import Command

# command line options #
_HELP_SHORT_OPT_ = "h"
_HELP_LONG_OPT_ = "help"

# return codes #
_SUCCESS_RC_ = 0
_BAD_OPT_RC_ = 1


################
#     Main     #
################
def main(argv: list):
    """
    The main executable method for the viya-ark launcher script.

    :param argv: The list of arguments passed at invocation.
    """
    try:
        # get the requested command value #
        command_name = argv[0]

        # print the usage and exit, if requested #
        if command_name in (f"-{_HELP_SHORT_OPT_}", f"--{_HELP_LONG_OPT_}"):
            usage(_SUCCESS_RC_)

        # convert any dashes in the given command to underscores to align with Pythonic package/module standards #
        command_module_name = command_name.replace("-", "_")

        # attempt to import the requested command module #
        imported_module = None
        try:
            imported_module = importlib.import_module(f"{command_module_name}.{command_module_name}")
        except ModuleNotFoundError:
            print()
            print(f"ERROR: Command [{command_name}] not found.")
            usage(_BAD_OPT_RC_)

        # find any attributes in the module that implement the Command class using reflection #
        command = None
        for attribute_name in dir(imported_module):
            # get the current module attribute by name #
            attribute = getattr(imported_module, attribute_name)

            # if the attribute is:                                  #
            # (1) a class -AND-                                     #
            # (2) a subclass of Command -AND-                       #
            # (3) not abstract                                      #
            # then the attribute defines a command for the project. #
            if inspect.isclass(attribute) and issubclass(attribute, Command) and not inspect.isabstract(attribute):
                command = attribute
                # the Command implementation was found, the loop can break #
                break

        if command is not None:
            # call the Command's run() method to delegate execution to the module, pass all relevant arguments #
            command.run(argv[1:])
        else:
            # if a Command implementation wasn't found, print the usage message #
            print()
            print(f"ERROR: Command [{command_name}] not found.")
            usage(_BAD_OPT_RC_)

    except IndexError:
        # if the launcher script wasn't given enough args, print the usage #
        print()
        print("ERROR: A command must be provided.")
        usage(_BAD_OPT_RC_)


#################
#     Usage     #
#################
def usage(exit_code: int):
    """
    Prints the usage statement for the viya-ark launcher script and exits with the provided exit_code.

    :param exit_code: The code to return upon exit.
    """
    commands = list()

    # walk through all packages parallel to this script #
    paths = [os.path.realpath(os.path.dirname(__file__))]
    for importer, name, is_package in pkgutil.walk_packages(path=paths):
        # skip any objects that are packages (i.e. not modules) #
        if not is_package:
            # import the current module #
            try:
                importlib.import_module(name)
            except ModuleNotFoundError as e:
                # ignore any issues importing pytest, raise any other module import errors
                if e.name != "pytest":
                    raise e

    for subclass in Command.__subclasses__():
        # create a tuple of command details by calling the command_name() and command_desc() methods #
        command_details = (subclass().command_name(), subclass().command_desc())
        # add the command details to the list of discovered commands #
        commands.append(command_details)

    # print the commands as well as the static help command to stdout #
    print()
    print(f"Usage: {os.path.basename(__file__)} <command> [options]")
    print()
    print("Commands:")
    for command in commands:
        print("    {:<30} {}".format(command[0], command[1]))
    help_cmd_display = f"-{_HELP_SHORT_OPT_}, --{_HELP_LONG_OPT_}"
    print("    {:<30} {}".format(help_cmd_display, "Display usage for viya-ark."))
    print()

    sys.exit(exit_code)


##################
#    __main__    #
##################
if __name__ == "__main__":
    main(sys.argv[1:])
