#!/usr/bin/env python3
####################################################################
# ### ldap_validator.py                                          ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
#                                                                ###
####################################################################

import datetime
from ldap3 import Server, Connection
import os
import sys
import getopt
import yaml
import traceback
import json
import pprint
import logging
from ldap_validator.library.utils import ldap_messages
from ldap3.core.exceptions import LDAPException
from viya_ark_library.command import Command
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
_VALIDATOR_LOG_NAME_TMPL_ = "ldap_validator_{}.log"
_FILE_TIMESTAMP_TMPL_ = "%Y-%m-%dT%H_%M_%S"

# set timestamp for report file
file_timestamp = datetime.datetime.now().strftime(_FILE_TIMESTAMP_TMPL_)


# sitedefault variables
ldap_server_host = ""
ldap_server_port = ""
ldap_protocol = ""
ldap_bind_userdn = ""
ldap_bind_pw = ""
ldap_user_basedn = ""
ldap_group_basedn = ""
ldap_defaultadmin_user = ""
ldap_url = ""


# --------------------------------------------------------------------------------------------------
def import_site_default(yaml_file, ldap_logger, sas_logger):
    """
    Load config yaml file into dict structure.

    Argument:
        yaml_file(str) - full path/filename of yaml
    Returns:
        yaml_content(dict) - containing contents of yaml file
    Raises:
        dict - object containing all content from supplied yaml in dict format
    """

    try:
        ldap_logger.info("Importing sitedefault: " + yaml_file)

        # Read the yaml file
        with open(yaml_file, 'r') as yfile:
            try:
                yaml_content = yaml.load(yfile, Loader=Loader)
            except yaml.parser.ParserError:
                ldap_logger.error("Check sitedefault file. It is not well formed.")
                print("Check sitedefault file. It is not well formed.")
                print("Check log file: " + sas_logger.get_log_file())
                sys.exit(ldap_messages.BAD_SITEYAML_RC_)
        yfile.close()

        ldap_logger.info("Successfully loaded yaml file '" + str(yaml_file) + "'")

        # define simpler variables
        global ldap_server_host
        global ldap_server_port
        global ldap_protocol
        global ldap_bind_userdn
        global ldap_bind_pw
        global ldap_user_basedn
        global ldap_group_basedn
        global ldap_defaultadmin_user
        global ldap_url

        try:
            ldap_url = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['url']
            ldap_server_host = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['host']
            ldap_server_port = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['port']
            ldap_bind_pw = yaml_content['config']['application']['sas.identities.providers.ldap.connection']['password']
            ldap_bind_userdn = \
                yaml_content['config']['application']['sas.identities.providers.ldap.connection']['userDN']
            ldap_user_basedn = yaml_content['config']['application']['sas.identities.providers.ldap.user']['baseDN']
            ldap_group_basedn = yaml_content['config']['application']['sas.identities.providers.ldap.group']['baseDN']
            ldap_defaultadmin_user = yaml_content['config']['application']['sas.identities']['administrator']
        except (TypeError, KeyError) as e:
            ldap_logger.exception("Failure while parsing sitedefault file. Check sitedefault file. " + str(e))
            print("Failure while parsing sitedefault file." + str(e))
            print("Check log file: " + sas_logger.get_log_file())
            sys.exit(ldap_messages.BAD_SITEYAML_RC_)

        ldap_protocol = ldap_url.split(':')[0]

        ldap_logger.debug("LDAP URL:                       " + str(ldap_url))
        ldap_logger.debug("LDAP Protocol:                  " + str(ldap_protocol))
        ldap_logger.debug("LDAP ServerHost:                " + str(ldap_server_host))
        ldap_logger.debug("LDAP Server Port:               " + str(ldap_server_port))
        if (ldap_bind_pw is not None):
            ldap_logger.debug("LDAP Anonymous Bind Password:   SET")
        else:
            ldap_logger.debug("LDAP Anonymous Bind Password:   UNSET")

        ldap_logger.debug("LDAP Anonymous Bind User DN:    " + str(ldap_bind_userdn))
        ldap_logger.debug("LDAP User DN:                   " + str(ldap_user_basedn))
        ldap_logger.debug("LDAP Group DN:                  " + str(ldap_group_basedn))
        ldap_logger.debug("LDAP Default Admin User:        " + str(ldap_defaultadmin_user))

        try:
            # check to see if the provided values are valid
            err_msg = "Error: LDAP URL: is undefined."
            assert(ldap_url is not None)
            err_msg = "Error: LDAP Host is undefined."
            assert(ldap_server_host is not None)
            err_msg = "Error: LDAP port is incorrectly defined."
            assert(ldap_server_port > 0)
            err_msg = "Error: LDAP server is not accessible on specified host and port."
            assert (ping_host(ldap_logger) is True)
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
        except (AssertionError, TypeError):
            ldap_logger.exception("Errors in sitedefault file. {}".format(err_msg))
            print("Errors in sitedefault file. {}".format(err_msg))
            print("Check log file: " + sas_logger.get_log_file())
            print()
            sys.exit(ldap_messages.BAD_SITEYAML_RC_)

        ldap_logger.info("Sitedefault contains required values.")

    except (IOError):
        # Log error and raise exception if yaml can't be read.
        error_msg = '{1}\nError loading yaml file {0}\n'.format(yaml_file, traceback.format_exc())
        ldap_logger.exception(error_msg)
        print(error_msg)
        print("Check log file: " + sas_logger.get_log_file())
        sys.exit(ldap_messages.BAD_SITEYAML_RC_)
    except ValueError:
        error_msg = '{1}\nValue Error reading sitedefault file {0}\n'.format(yaml_file, traceback.format_exc())
        print(error_msg)
        ldap_logger.exception(error_msg)
        print("Check log file: " + sas_logger.get_log_file())
        sys.exit(ldap_messages.BAD_SITEYAML_RC_)
    except KeyError:
        error_msg = '{1}\nKey Error reading sitedefault file {0}\n'.format(yaml_file, traceback.format_exc())
        ldap_logger.exception(error_msg)
        print(error_msg)
        print("Check log file: " + sas_logger.get_log_file())
        sys.exit(ldap_messages.BAD_SITEYAML_RC_)

    # return yaml_content
    return 0


# --------------------------------------------------------------------------------------------------
def run_test_schedule(ldap_server_host, ldap_logger):
    """
    Run the list of scheduled LDAP Validation tests.

    Argument:
        ldap_server_host - name of LDAP server
    Returns:
        success flag(bool) - Success/Failure of test schedule
    """

    if (not perform_ldap_query(ldap_logger, ldap_server_host, ldap_group_basedn, '(objectclass=*)')):
        failTestSuite(ldap_logger)

    if (not perform_ldap_query(ldap_logger, ldap_server_host, ldap_user_basedn, '(objectclass=*)')):
        failTestSuite(ldap_logger)

    searchstring = '(&(objectClass=user)(sAMAccountName=' + ldap_defaultadmin_user + '))'
    if (not perform_ldap_query(ldap_logger, ldap_server_host,  ldap_user_basedn, searchstring, True)):
        failTestSuite(ldap_logger)

    return True


# --------------------------------------------------------------------------------------------------
def failTestSuite(ldap_logger):
    """
    Ping the LDAP server on the specified connection.

    Argument:
        None
    Returns:
        None
    """

    ldap_logger.error("LDAP sitedefault.yaml verification has failed. Please see the log for more information.")
    print("LDAP sitedefault.yaml verification has failed. Please see the log for more information.")
    sys.exit(ldap_messages.BAD_SITEYAML_RC_)


# --------------------------------------------------------------------------------------------------
def ping_host(ldap_logger):
    """
    Ping the LDAP server on the specified connection.

    Argument:
        None
    Returns:
        success flag(bool) - Success/Failure of ping
    """

    ldap_logger.debug("Attempting to ping LDAP server host at " + str(ldap_server_host))

    response = os.system("ping -c 1 " + ldap_server_host)

    if (int(response) == 0):
        ldap_logger.info("Network Active")
        return True
    else:
        ldap_logger.error("Network Error")

    return False


# --------------------------------------------------------------------------------------------------
def perform_ldap_query(ldap_logger, ldap_server, searchbase, searchfilter, verify=False):
    """    Execute a query on the defined LDAP server.\n

    Argument:
        ldap_server    - name of LDAP server
        searchbase(str) - baseDN to be searched
        searchfilter(str) - LDAP query to be executed
        verify(bool) - Assert that a valid result is returned
    Returns:
        success flag(bool) - Success/Failure of query
    """

    ldap_logger.debug(" ldap_server = " + str(ldap_server) + ", searchbase = " + str(searchbase) +
                      ", searchFilter = " + str(searchfilter) + ", verify = " + str(verify))
    # perform search

    try:
        ldap_logger.debug("--------------------------------------------------------------------")
        server = Server(ldap_protocol + "://" + str(ldap_server))
        ldap_logger.debug("Attempting to create connection binding.")
        connection = Connection(server, ldap_bind_userdn, ldap_bind_pw, auto_bind=True)
        ldap_logger.debug("Bind results: " + str(connection))
        try:
            ldap_logger.debug("--------------------------------------------------------------------")
            ldap_logger.debug("LDAP Query: search_base=" + str(searchbase) + ", search_filter=" + str(searchfilter) +
                              "verify=" + str(verify))
            connection.search(search_base=searchbase, search_filter=searchfilter, size_limit=sizeLimit)
            response = json.loads(connection.response_to_json())
        except Exception as e:
            ldap_logger.exception("LDAP search failed with the following error: " + str(e))
            connection.unbind()
            return False
    except LDAPException as e:
        ldap_logger.exception("Failed connect to Server: " + str(server) + " with error " + str(e))
        return False
    # parse connection result, response, entries

    parse_result: bool = parse_connection_results(ldap_logger, response, connection.result, connection.entries, verify)
    connection.unbind()
    return parse_result


def parse_connection_results(ldap_logger, response, result, entries, verify):
    """    Parse the results returned by connection to the defined LDAP server.\n

    Argument:
        response       - results returned in json format
        result(dict)   - result on the connection created
        entries(list)  - entries on the connection created
        verify(bool) - Assert that a valid result is returned
    Returns:
        success flag(bool) - Success/Failure of query
    """
    results_returned = False
    ldap_logger.debug("json response LDAP Server connection {}".format(str(response)))
    ldap_logger.debug("connection result{}".format(pprint.pformat(result)))
    ldap_logger.debug("connection entries {}".format(pprint.pformat(entries)))
    if not(result):
        ldap_logger.error("connection.result is empty")
        return False
    query_rc = int(result['result'])
    ldap_logger.debug("--------------------------------------------------------------------")
    ldap_logger.debug("Search query return code: " + str(query_rc))
    ldap_logger.debug("--------------------------------------------------------------------")
    ldap_logger.debug("Response: " + str(response['entries']))
    ldap_logger.debug("--------------------------------------------------------------------")
    ldap_logger.debug("Result: " + str(result))
    ldap_logger.debug("--------------------------------------------------------------------")
    ldap_logger.debug("Entries: ")
    for entry in entries:
        results_returned = True
        ldap_logger.debug(str(entry))
    ldap_logger.debug("--------------------------------------------------------------------")

    if (verify):
        try:
            assert(results_returned is True)
        except AssertionError:
            ldap_logger.exception("Error: LDAP Search did not return any connection entries")
            return False
    try:
        assert(query_rc == 0 or query_rc == 4)
    except AssertionError:
        ldap_logger.exception("Error: LDAP Search query failed with return code: " + str(query_rc))
        return False

    ldap_logger.info("LDAP search queries completed successfully")
    return True


# --------------------------------------------------------------------------------------------------
###################
#     usage()     #
###################
def usage(exit_code: int):
    """
    Prints the usage information for the ldap-validator command and exits the program with the given exit_code.

    :param exit_code: The exit code to return when exiting the program.
    """
    print("\n")
    print("Usage: python3 ldap_validator.py <-s|--sitedefault> [<options>]\n")
    print("Example: python3 ldap_validator.py -s /path/to/sitedefault.yaml\n")

    print("Options:\n")
    print("    -s  --sitedefault           (Required)Full path the sitedefault.yaml file being validated.")
    print("    -o, --output-dir=\"<dir>\"    (Optional)Write the report and log files to the provided directory")
    print("    -d, --debug                 (Optional)Enables logging at DEBUG level. Default is INFO level")
    print("    -h  --help                  (Optional)Show this usage message")
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
    global sas_logger

    sitedefault_loc = ""
    output_dir = ""
    logging_level: int = logging.INFO

    # Parse command line options/arguments
    try:
        opts, args = getopt.getopt(argv, "s:o:dh", ["sitedefault=", "output-dir=", "debug", "help"])
    except getopt.GetoptError as opt_error:
        print(opt_error)
        usage(ldap_messages.BAD_OPT_RC_)

    for opt, arg in opts:

        if opt in ('-s', '--sitedefault'):
            sitedefault_loc = arg
        elif opt in ('-o', '--output-dir'):
            output_dir = arg
        elif opt in ('-d', '--debug'):
            print("Setting log level to DEBUG  ")
            logging_level = logging.DEBUG
        elif opt in ('-h', '--help'):
            usage(ldap_messages.SUCCESS_RC_)
        else:
            print()
            print(ldap_messages.OPTION_ERROR.format(str(opt)), 'error')
            usage(ldap_messages.BAD_OPT_RC_)

        # make sure path is valid #
    if output_dir != "":
        if not output_dir.endswith(os.sep):
            output_dir = output_dir + os.sep
        else:
            print(ldap_messages.OUPUT_PATH_ERROR)
            usage(ldap_messages.BAD_OPT_RC_)

        # Set the full log path
    validator_log_path = output_dir + _VALIDATOR_LOG_NAME_TMPL_.format(file_timestamp)

    try:
        logging.FileHandler(validator_log_path)
    except OSError as e:
        print(ldap_messages.OUPUT_PATH_ERROR, format(e))
        usage(ldap_messages.BAD_OPT_RC_)

    sas_logger = ViyaARKLogger(validator_log_path, logging_level=logging_level, logger_name="ldap_validator_logger")
    ldap_logger = sas_logger.get_logger()

    if not os.path.exists(sitedefault_loc):
        print("Invalid config yaml specified: " + str(sitedefault_loc))
        ldap_logger.error("Invalid config yaml specified: " + str(sitedefault_loc))
        usage(ldap_messages.BAD_OPT_RC_)

    # Show command line
    ldap_logger.debug("Command line: " + str(sys.argv))

    # Load site default and define variables
    is_imported = import_site_default(sitedefault_loc, ldap_logger, sas_logger)

    # Execute test suite
    run_schedule = run_test_schedule(ldap_server_host, ldap_logger)

    if (is_imported == 0 and run_schedule):
        print("SUCCESS: All LDAP search queries completed successfully.")
        ldap_logger.info("SUCCESS: All LDAP search queries completed successfully.")
        print("Log: " + validator_log_path)
        ldap_logger.info("Log: " + str(validator_log_path))
        return exit(ldap_messages.SUCCESS_RC_)


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
