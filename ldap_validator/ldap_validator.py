#!/usr/bin/env python3
####################################################################
# ### pre_install_report.py                                  ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################


from datetime import datetime

import os
import sys
import inspect
import getopt
import yaml
import traceback

try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader
    
# Control vars
cluster_settings = None

#set up logging
logFile = "ldap_validation_" + str(datetime.now()) + ".log"
open(logFile, 'a').close()

# --------------------------------------------------------------------------------------------------
def logMessage(message, error_flag=False):
    """
    Adds a message to the log; flag to mark message as error.

    Argument:
        message(str) - message to be added to the log
        error_flag(bool) - flag to mark the message as an ERROR in the log
    Returns:
        None
    """

    dateTimeObj = datetime.now()

    logger = open(logFile, "a")

    if error_flag: message = "[ ERROR ] " + str(message)
    message = str(dateTimeObj) + " - " + str(message)

    # display the message to the terminal and write to the log
    print(message)
    logger.write(message)
    logger.write("\n")

    logger.close()

    return None

# --------------------------------------------------------------------------------------------------
def importConfigYAML(yaml_file):
    """
    Load config yaml file into dict structure.

    Argument:
        yaml_file(str) - full path/filename of yaml
    Returns:
        yaml_content(dict) - containing contents of yaml file
    Raises:
        dict - object containing all content from supplied yaml in dict format
    """
    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    
    if not os.path.exists(yaml_file):
        logMessage("Invalid config yaml specified: " + str(yaml_file))
        sys.exit(1)
        return "failed"
        
    try:
        logMessage("Importing sitedefault: " + yaml_file)
        
        # Read the yaml file
        with open(yaml_file, 'r') as yfile:
            yaml_content = yaml.load(yfile, Loader=Loader)
        yfile.close()

        logMessage("Successfully loaded yaml file '" + str(yaml_file) + "'")
        
        assert(yaml_content['config']['application']['sas.identities.providers.ldap.connection']['host'] is not None), "Error: LDAP Host is undefined."
        assert(yaml_content['config']['application']['sas.identities.providers.ldap.connection']['port'] is not None), "Error: LDAP port is undefined."
        assert(yaml_content['config']['application']['sas.identities.providers.ldap.connection']['url'] is not None), "Error: LDAP URL is undefined."
        assert(yaml_content['config']['application']['sas.identities.providers.ldap.connection']['anonymousBind'] is not None), "Error: LDAP anonymousBind is undefined."
        assert(yaml_content['config']['application']['sas.identities.providers.ldap.connection']['userDN'] is not None), "Error: LDAP userDN is undefined."
        assert(yaml_content['config']['application']['sas.identities.providers.ldap.connection']['password'] is not None), "Error: LDAP password is undefined."
        assert(yaml_content['config']['application']['sas.identities.providers.ldap.user']['baseDN'] is not None), "Error: LDAP User BaseDN is undefined."
        assert(yaml_content['config']['application']['sas.identities.providers.ldap.group']['baseDN'] is not None), "Error: LDAP Group BaseDN is undefined."
        assert(yaml_content['config']['application']['sas.identities']['administrator'] is not None), "Error: LDAP Administrator is undefined."
        
        logMessage("Sitedefault contains required values.")

    except (IOError, ValueError):
        # Log error and raise exception if yaml can't be read.
        error_msg = '{1}\nError loading yaml file {0}\n'.format(yaml_file, traceback.format_exc())
        logMessage(error_msg)
        raise ValueError(error_msg)

    return yaml_content


##################
#     main()     #
##################


def main(argv):

    """
    Implementation of the main script execution for the pre_check install command.

    :param argv: The parameters passed to the script at execution.
    """
    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))
    

    try:
        opts, args = getopt.getopt(argv, "y:Y",
                                   ["sitedefault=", "sitedefault="])
    except getopt.GetoptError as opt_error:
        logMessage(opt_error)
    
    
    sitedefault_loc = ""
    
    for opt, arg in opts:
        logMessage("Processing command line option <" + opt + " " + arg + ">")
        if opt in ('-y', '--sitedefault'):
            logMessage("Setting sitedefault to: " + arg)
            sitedefault_loc = arg
        elif opt in ('-Y', '--sitedefault'):
            logMessage("Setting sitedefault to: " + arg)
            sitedefault_loc = arg
        else:
            logMessage(opt_error)
            
    cluster_settings = importConfigYAML(sitedefault_loc)

##################
#     main()     #
##################

if __name__ == '__main__':
    main(sys.argv[1:])
# ----------------------------------------------------------------------------
