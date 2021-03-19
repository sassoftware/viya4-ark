#!/usr/bin/env python3
####################################################################
# ### ldap_validator.py                                          ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
#                                                                ###
####################################################################

import datetime
from ldap3 import Server, Connection
import os
import sys
import inspect
import getopt
import yaml
import traceback
import json
import shutil
import pprint
import logging
from ldap3.core.exceptions import LDAPException
from viya_ark_library.command import Command
from ldap_validator.library.utils import ldap_messages
from viya_ark_library.logging import ViyaARKLogger
try:
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader
######################################################################################
# retrieve at most sizelimit entries for a search.  A sizelimit of 0 (zero) or
# none means no limit.  A sizelimit of  max  means  the maximum integer allowable
# by the protocol.  A server may impose a maximal sizelimit which only the root
# user may override.
sizeLimit = 5

# templates for output file names #
_REPORT_LOG_NAME_TMPL_ = "ldap_validator_{}.log"
_FILE_TIMESTAMP_TMPL_ = "%Y-%m-%dT%H_%M_%S"

# set timestamp for report file
file_timestamp = datetime.datetime.now().strftime(_FILE_TIMESTAMP_TMPL_)

# default log file
logFile = "ldap_validation_" + str(file_timestamp) + ".log"
logFile = logFile.replace(':', '.')  # remove a couple troublesome characters in the timestamp
logFile = logFile.replace(' ', '_')

# sitedefault variables
ldap_server_host = ""
ldap_server_port = ""
ldap_protocol = ""
ldap_anon_bind = ""
ldap_bind_userdn = ""
ldap_bind_pw = ""
ldap_user_basedn = ""
ldap_group_basedn = ""
ldap_defaultadmin_user = ""
ldap_url = ""
# Output directory for logs
output_dir = ""


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

    # dateTimeObj = datetime.now()
    timestamp = datetime.datetime.now().strftime(_FILE_TIMESTAMP_TMPL_)

    logger = open(logFile, "a")

    if (message == ""):
        return None

    if (error_flag):
        message = "[ ERROR ] " + str(message)

    message = "log {} ".format(timestamp) + " - " + str(message)

    # display the message to the terminal and write to the log
    print(message)
    logger.write(message)
    logger.write("\n")

    logger.close()

    return None


# --------------------------------------------------------------------------------------------------
def importSiteDefault(yaml_file, ldap_logger):
    """
    Load config yaml file into dict structure.

    Argument:
        yaml_file(str) - full path/filename of yaml
        ldap_logger    - instance of ViyaARKLogger
    Returns:
        yaml_content(dict) - containing contents of yaml file
    Raises:
        dict - object containing all content from supplied yaml in dict format
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    if not os.path.exists(yaml_file):
        ldap_logger.info("Invalid config yaml specified: " + str(yaml_file))
        logMessage("Invalid config yaml specified: " + str(yaml_file))
        sys.exit(ldap_messages.BAD_SITEYAML_RC_)
        # return "failed"

    try:
        logMessage("Importing sitedefault: " + yaml_file)

        # Read the yaml file
        with open(yaml_file, 'r') as yfile:
            yaml_content = yaml.load(yfile, Loader=Loader)
        yfile.close()

        logMessage("Successfully loaded yaml file '" + str(yaml_file) + "'")

        # define simpler variables
        global ldap_server_host
        global ldap_server_port
        global ldap_protocol
        global ldap_anon_bind
        global ldap_bind_userdn
        global ldap_bind_pw
        global ldap_user_basedn
        global ldap_group_basedn
        global ldap_defaultadmin_user
        global ldap_url

        ldap_url = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['url']
        ldap_server_host = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['host']
        ldap_server_port = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['port']
        ldap_anon_bind = \
            yaml_content['config']['application']['sas.identities.providers.ldap.connection']['anonymousBind']
        ldap_bind_pw = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['password']
        ldap_bind_userdn = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['userDN']
        ldap_user_basedn = yaml_content['config']['application']['sas.identities.providers.ldap.user']['baseDN']
        ldap_group_basedn = yaml_content['config']['application']['sas.identities.providers.ldap.group']['baseDN']
        ldap_defaultadmin_user = yaml_content['config']['application']['sas.identities']['administrator']

        ldap_protocol = ldap_url.split(':')[0]

        ldap_anon_bind = (ldap_anon_bind).lower()
        if (ldap_anon_bind == 'false'):
            ldap_anon_bind = False
        if (ldap_anon_bind == 'true'):
            ldap_anon_bind = True

        logMessage("LDAP URL:                       " + ldap_url)
        logMessage("LDAP Protocol:                  " + ldap_protocol)
        logMessage("LDAP ServerHost:                " + ldap_server_host)
        logMessage("LDAP Server Port:               " + str(ldap_server_port))
        logMessage("LDAP Anonymous Bind:            " + str(ldap_anon_bind))
        if (ldap_bind_pw is not None):
            logMessage("LDAP Anonymous Bind Password:   SET")
        else:
            logMessage("LDAP Anonymous Bind Password:   UNSET")
        logMessage("LDAP Anonymous Bind User DN:    " + ldap_bind_userdn)
        logMessage("LDAP User DN:                   " + ldap_user_basedn)
        logMessage("LDAP Group DN:                  " + ldap_group_basedn)
        logMessage("LDAP Default Admin User:        " + ldap_defaultadmin_user)

        try:
            # check to see if the provided values are valid
            err_msg = "Error: LDAP URL: is undefined."
            assert(ldap_url is not None)
            err_msg = "Error: LDAP Host is undefined."
            assert(ldap_server_host is not None)
            err_msg = "Error: LDAP port is in correctly defined."
            assert(ldap_server_port > 0)
            err_msg = "Error: LDAP server is not accessible on specified host and port."
            assert (pingHost() is True)
            err_msg = "Error: LDAP anonymousBind does not have a value of true or false."
            assert(ldap_anon_bind is True or ldap_anon_bind is False)
            err_msg = "Error: LDAP password is undefined."
            assert(ldap_bind_pw is not None)
            err_msg = "Error: LDAP bind userDN is undefined."
            assert(ldap_bind_userdn is not None)
            err_msg = "Error: LDAP User BaseDN is undefined."
            assert(ldap_user_basedn is not None)
            err_msg = "Error: LDAP Group BaseDN is undefined."
            assert(ldap_group_basedn is not None)
            err_msg = "Error: LDAP Administrator is undefined."
            assert(ldap_defaultadmin_user is not None)
        except AssertionError:
            print("Errors in sitedefault file. {}".format(err_msg))
            print()
            sys.exit(ldap_messages.BAD_SITEYAML_RC_)

        logMessage("Sitedefault contains required values.")

    except (IOError):
        # Log error and raise exception if yaml can't be read.
        error_msg = '{1}\nError loading yaml file {0}\n'.format(yaml_file, traceback.format_exc())
        logMessage(error_msg)
        ldap_logger.info(error_msg)
        # raise ValueError(error_msg)
        sys.exit(ldap_messages.BAD_SITEYAML_RC_)
    except ValueError:
        error_msg = '{1}\nValue Error reading sitedefalt file {0}\n'.format(yaml_file, traceback.format_exc())
        logMessage(error_msg)
        ldap_logger.info(error_msg)
        sys.exit(ldap_messages.BAD_SITEYAML_RC_)
    except KeyError:
        error_msg = '{1}\nKey Error reading sitedefalt file {0}\n'.format(yaml_file, traceback.format_exc())
        logMessage(error_msg)
        ldap_logger.info(error_msg)
        sys.exit(ldap_messages.BAD_SITEYAML_RC_)

    # return yaml_content
    return 0


# --------------------------------------------------------------------------------------------------
def runTestSchedule(ldap_server_host, ldap_logger):
    """
    Run the list of scheduled LDAP Validation tests.

    Argument:
        ldap_server_host - name of LDAP server
        ldap_logger      - instance of ViyaARKLogger
    Returns:
        success flag(bool) - Success/Failure of test schedule
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    if (not performLDAPQuery(ldap_logger, ldap_server_host, ldap_group_basedn, '(objectclass=*)')):
        failTestSuite()

    if (not performLDAPQuery(ldap_logger, ldap_server_host, ldap_user_basedn, '(objectclass=*)')):
        failTestSuite()

    searchString = '(&(objectClass=user)(sAMAccountName=' + ldap_defaultadmin_user + '))'
    if (not performLDAPQuery(ldap_logger, ldap_server_host,  ldap_user_basedn, searchString, True)):
        failTestSuite()

    logMessage("--------------------------------------------------------------------")
    logMessage("SUCCESS: All LDAP search queries completed successfully.")
    logMessage("Log: " + logFile)
    logMessage("--------------------------------------------------------------------")

    return True


# --------------------------------------------------------------------------------------------------
def failTestSuite():
    """
    Ping the LDAP server on the specified connection.

    Argument:
        None
    Returns:
        None
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    logMessage("LDAP sitedefault.yaml verification has failed. Please see the logs for more information.", True)

    sys.exit(ldap_messages.BAD_SITEYAML_RC_)


# --------------------------------------------------------------------------------------------------
def pingHost():
    """
    Ping the LDAP server on the specified connection.

    Argument:
        None
    Returns:
        success flag(bool) - Success/Failure of ping
    """

    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    logMessage("Attempting to ping LDAP server host at " + ldap_server_host)

    response = os.system("ping -c 1 " + ldap_server_host)

    if (int(response) == 0):
        logMessage("Network Active")
        return True
    else:
        logMessage("Network Error")

    return False


# --------------------------------------------------------------------------------------------------
def performLDAPQuery(ldap_logger, ldap_server, searchBase, searchFilter, verify=False):
    """    Execute a query on the defined LDAP server.\n

    Argument:
        ldap_logger    - instance of ViyaARKLogger
        ldap_server    - name of LDAP server
        searchBase(str) - baseDN to be searched
        queryString(str) - LDAP query to be executed
        verify(bool) - Assert that a valid result is returned
    Returns:
        success flag(bool) - Success/Failure of query
    """

    ldap_logger.info(" ldap_server = " + ldap_server + ", searchBase = " + str(searchBase) +
                     ", searchFilter = " + str(searchFilter) + ", verify = " + str(verify))
    logMessage('===Entry {0}==='.format(inspect.stack()[0][3]))

    # perform search

    try:
        logMessage("--------------------------------------------------------------------")
        server = Server(ldap_protocol + "://" + ldap_server)
        logMessage("Attempting to create connection binding.")
        connection = Connection(server, ldap_bind_userdn, ldap_bind_pw, auto_bind=True)
        logMessage("Bind results: " + str(connection))
        try:
            logMessage("--------------------------------------------------------------------")
            logMessage("LDAP Query: search_base=" + searchBase + ", search_filter=" + searchFilter
                       + "verify=" + str(verify))
            connection.search(search_base=searchBase, search_filter=searchFilter, size_limit=sizeLimit)
            response = json.loads(connection.response_to_json())
        except Exception as e:
            logMessage("LDAP search failed with the following error: " + str(e), True)
            ldap_logger.info("LDAP search failed with the following error: " + str(e), True)
            connection.unbind()
            return False
    except LDAPException as e:
        logMessage("Failed connect to Server: " + str(server) + " with error " + str(e), True)
        ldap_logger.info("Failed connect to Server: " + str(server) + " with error " + str(e), True)
        return False
    # parse connection result, response, entries

    parse_result: bool = parse_connection_results(ldap_logger, response, connection.result, connection.entries, verify)
    connection.unbind()
    return parse_result


def parse_connection_results(ldap_logger, response, result, entries, verify):
    """    Parse the results returned by connection to the defined LDAP server.\n

    Argument:
        ldap_logger    - instance of ViyaARKLogger
        response       - results returned in json format
        result(dict)   - result on the connection created
        entries(list)  - entries on the connection created
        verify(bool) - Assert that a valid result is returned
    Returns:
        success flag(bool) - Success/Failure of query
    """
    results_returned = False
    ldap_logger.info("json response LDAP Server connection {}".format(str(response)))
    ldap_logger.info("connection result{}".format(pprint.pformat(result)))
    ldap_logger.info("connection entries {}".format(pprint.pformat(entries)))
    if not(result):
        ldap_logger.info("connection.result is empty")
        return False
    query_rc = int(result['result'])
    logMessage("--------------------------------------------------------------------")
    logMessage("Search query return code: " + str(query_rc))
    logMessage("--------------------------------------------------------------------")
    logMessage("Response: " + str(response['entries']))
    logMessage("--------------------------------------------------------------------")
    logMessage("Result: " + str(result))
    logMessage("--------------------------------------------------------------------")
    logMessage("Entries: ")
    for entry in entries:
        results_returned = True
        logMessage(str(entry))
    logMessage("--------------------------------------------------------------------")

    if (verify):
        try:
            assert(results_returned is True)
        except AssertionError:
            logMessage("Error: LDAP Search did not return any connection entries")
            return False
    try:
        assert(query_rc == 0 or query_rc == 4)
    except AssertionError:
        logMessage("Error: LDAP Search query failed with return code: " + str(query_rc))
        return False

    ldap_logger.info("LDAP search queries completed successfully")
    return True


# --------------------------------------------------------------------------------------------------
###################
#     usage()     #
###################
def usage(exit_code: int):
    """
    Prints the usage information for the pre-install-report command and exits the program with the given exit_code.

    :param exit_code: The exit code to return when exiting the program.
    """
    print()
    print("\n")
    print("This script will attempt to establish a connection to the LDAP")
    print("server defined in your sitedefault.yaml file, and execute several")
    print("queries to establish the validity of the sitedefault.yaml entries.\n")

    print("Usage: python3 ldap_validator.py <-s|--sitedefault> <-l|--logFile> <-p|--port> [<options>]\n")
    print("Example: python3 ldap_validator.py -s /path/to/sitedefault.yaml -l /path/to/my/logFile.txt\n")

    print("Options:\n")
    print("    -s  --sitedefault   (Required)Full path the sitedefault.yaml file being validated.")
    print("    -l  --logFile       (Optional)Specify a customer log file to capture output.")
    print("    -o, --output-dir=\"<dir>\"  (Optional)Write the report and log files to the provided directory")

    print("    -h  --help          (Optional)Show this usage message")
    sys.exit(0)
    print()
    sys.exit(exit_code)


# --------------------------------------------------------------------------------------------------
##################
#     main()     #
##################
def main(argv):

    """
    Main execution point for the ldap_validator script

    Argument:
        arguments(string) - The parameters passed to the script at execution.
    """
    global logFile

    # Parse command line options/arguments
    try:
        opts, args = getopt.getopt(argv, "s:l:o:h", ["sitedefault=", "logFile=", "output_dir=", "help"])
    except getopt.GetoptError as opt_error:
        logMessage(opt_error)

    sitedefault_loc = ""
    output_dir = ""
    for opt, arg in opts:

        logMessage("Processing command line option <" + opt + " " + arg + ">")
        if opt in ('-s', '--sitedefault'):
            logMessage("Setting sitedefault to: " + arg)
            sitedefault_loc = arg
        elif opt in ('-l', '--logFile'):
            oldLogFile = logFile
            logMessage("Setting logging to: " + arg)
            logFile = arg
            shutil.move(oldLogFile, logFile)
        elif opt in ('-o', '--output-dir'):
            output_dir = arg
        elif opt in ('-h', '--help'):
            usage(ldap_messages.SUCCESS_RC_)
        else:
            print()
            print(ldap_messages.OPTION_ERROR.format(str(opt)))
            usage(ldap_messages.BAD_OPT_RC_)

    # make sure path is valid #
    if output_dir != "":
        if not output_dir.endswith(os.sep):
            output_dir = output_dir + os.sep
        else:
            print(ldap_messages.OUPUT_PATH_ERROR)
            usage(ldap_messages.BAD_OPT_RC_)

    report_log_path = output_dir + _REPORT_LOG_NAME_TMPL_.format(file_timestamp)
    # Set up Logger
    # @Sherrell pls add loggin option on command line and update line below
    # sas_logger = ViyaARKLogger(report_log_path, logging_level=logging_level, logger_name="pre_install_logger")
    sas_logger = ViyaARKLogger(report_log_path, logging.INFO, "ldap_logging")
    ldap_logger = sas_logger.get_logger()

    # Load site default and define variables
    importSiteDefault(sitedefault_loc, ldap_logger)
    # Execute test suite
    runTestSchedule(ldap_server_host, ldap_logger)


class LDAPValidatorCommand(Command):
    """
    Command implementation for the pre-install command to register
    this module as an executable task with the launcher script.
    """

    @staticmethod
    def run(argv):
        """
        Method called when a request to execute this task is made.
        """
        main(argv)

    @staticmethod
    def command_name():
        """
        Method defining the command name value for the project launcher script.
        """
        return os.path.basename(os.path.dirname(__file__)).replace("_", "-")

    @staticmethod
    def command_desc():
        """
        Method defining the human-friendly command description for display by the
        launcher script help.
        """
        return "Verify connection to LDAP server"


# --------------------------------------------------------------------------------------------------
##################
#     main()     #
##################
if __name__ == '__main__':
    main(sys.argv[1:])
