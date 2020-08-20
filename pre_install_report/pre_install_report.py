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

from typing import Optional, Text
import datetime
import pprint
import sys
import os
import logging
import getopt

from pre_install_report.library.utils import viya_constants
from pre_install_report.library.utils import viya_messages
from pre_install_report.library.pre_install_check import ViyaPreInstallCheck
from viya_arkcd_library.command import Command
from viya_arkcd_library.k8s.sas_k8s_errors import NamespaceNotFoundError
from viya_arkcd_library.k8s.sas_kubectl import Kubectl
from viya_arkcd_library.logging import ViyaARKCDLogger

PRP = pprint.PrettyPrinter(indent=4)

# templates for output file names #
_REPORT_FILE_NAME_TMPL_ = "viya_pre_install_report_{}.html"
_REPORT_LOG_NAME_TMPL_ = "viya_pre_install_log_{}.log"
_FILE_TIMESTAMP_TMPL_ = "%Y-%m-%dT%H_%M_%S"

# set timestamp for report file
file_timestamp = datetime.datetime.now().strftime(_FILE_TIMESTAMP_TMPL_)

##############################################
#     CLASS: PreInstallReportCommand     #
##############################################


def _read_properties_file():
    """
    This method reads the externalized properties file viya_cluster_settings.properties

    :returns dict object with key/value pairs read.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    datafile = os.path.join(current_dir, 'viya_cluster_settings.properties')
    if os.path.exists(datafile):
        try:
            check_limits: dict = dict(line.strip().split('=')
                                      for line in open(datafile) if not line.strip().startswith('#'))
            return check_limits
        except OSError as e:
            print(viya_messages.EXCEPTION_MESSAGE.format(e))
            print()
            sys.exit(viya_messages.SET_LIMTS_ERROR_RC_)
        except ValueError as e:
            print(viya_messages.EXCEPTION_MESSAGE.format(e))
            print()
            sys.exit(viya_messages.SET_LIMTS_ERROR_RC_)


def _read_environment_var(env_var):
    """
    This method verifies that the KUBECONFIG environment variable is set.

    :param env_var: Environment variable to check
    """
    try:
        value_env_var = os.environ[env_var]
    except Exception:
        print(viya_messages.KUBECONF_ERROR)
        sys.exit(viya_messages.BAD_ENV_RC_)
    return value_env_var


class PreInstallReportCommand(Command):
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
        return "Generate a pre-installation report of the Kubernetes cluster" \
               " in which Viya is to be deployed."


###################
#     usage()     #
###################
def usage(exit_code: int):
    """
    Prints the usage information for the pre-install-report command and exits the program with the given exit_code.

    :param exit_code: The exit code to return when exiting the program.
    """
    print()
    print("Usage: viya-arkcd.py pre_install_report <-i|--ingress> <-H|--host> <-p|--port> [<options>]")
    print()
    print("Options:")
    print("    -i  --ingress=nginx or istio  (Required)Kubernetes ingress controller used for Viya deployment")
    print("    -H  --host                    (Required)Ingress host used for Viya deployment")
    print("    -p  --port=xxxxx or \"\"        (Required)Ingress port used for Viya deployment")
    print("    -h  --help                    (Optional)Show this usage message")
    print("    -n  --namespace               (Optional)Kubernetes namespace used for Viya deployment")
    print("    -o, --output-dir=\"<dir>\"      (Optional)Write the report and log files to the provided directory")
    print("    -d, --debug                   (Optional)Enables logging at DEBUG level. Default is INFO level")
    print()
    sys.exit(exit_code)

##################
#     main()     #
##################


def main(argv):

    """
    Implementation of the main script execution for the pre_check install command.

    :param argv: The parameters passed to the script at execution.
    """
    try:
        opts, args = getopt.getopt(argv, "i:H:p:hn:o:d",
                                   ["ingress=", "host=", "port=", "help", "namespace=", "output-dir=", "debug"])
    except getopt.GetoptError as opt_error:
        print(viya_messages.EXCEPTION_MESSAGE.format(opt_error))
        usage(viya_messages.BAD_OPT_RC_)

    found_ingress_controller: bool = False
    found_ingress_host: bool = False
    found_ingress_port: bool = False
    output_dir: Optional[Text] = ""
    ingress_port: Optional[Text] = ""
    name_space: Optional[Text] = None
    logging_level: int = logging.INFO

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            usage(viya_messages.SUCCESS_RC_)
        elif opt in ('-d', '--debug'):
            logging_level = logging.DEBUG
        elif opt in ('-n', '--namespace'):
            name_space = arg
        elif opt in ('-i', '--ingress'):
            ingress_controller = arg
            found_ingress_controller = True
        elif opt in ('-H', '--host'):
            ingress_host = arg
            found_ingress_host = True
        elif opt in ('-p', '--port'):
            found_ingress_port = True
            ingress_port = arg
        elif opt in ('-o', '--output-dir'):
            output_dir = arg
        else:
            print()
            print(viya_messages.OPTION_ERROR.format(str(opt)))
            usage(viya_messages.BAD_OPT_RC_)

    if not found_ingress_controller or not found_ingress_host or not found_ingress_port:
        print(viya_messages.OPTION_VALUES_ERROR)
        usage(viya_messages.BAD_OPT_RC_)

    if not(str(ingress_controller) == viya_constants.INGRESS_NGINX
           or str(ingress_controller) == viya_constants.INGRESS_ISTIO):
        print(viya_messages.INGRESS_CONTROLLER_ERROR)
        usage(viya_messages.BAD_OPT_RC_)

    # make sure path is valid #
    if output_dir != "":
        if not output_dir.endswith(os.sep):
            output_dir = output_dir + os.sep
        else:
            print(viya_messages.OUPUT_PATH_ERROR)
            usage(viya_messages.BAD_OPT_RC_)

    report_log_path = output_dir + _REPORT_LOG_NAME_TMPL_.format(file_timestamp)

    try:
        logging.FileHandler(report_log_path)
    except OSError as e:
        print(viya_messages.OUPUT_PATH_ERROR, format(e))
        usage(viya_messages.BAD_OPT_RC_)

    sas_logger = ViyaARKCDLogger(report_log_path, logging_level=logging_level, logger_name="pre_install_logger")
    _read_environment_var('KUBECONFIG')

    try:
        kubectl = Kubectl(namespace=name_space)
    except ConnectionError as e:
        print()
        print(viya_messages.EXCEPTION_MESSAGE.format(e))
        print()
        sys.exit(viya_messages.CONNECTION_ERROR_RC_)
    except NamespaceNotFoundError as e:
        print()
        print(viya_messages.EXCEPTION_MESSAGE.format(e))
        print()
        sys.exit(viya_messages.NAMESPACE_NOT_FOUND_RC_)

    check_limits = _read_properties_file()
    sas_pre_check_report: ViyaPreInstallCheck = ViyaPreInstallCheck(sas_logger,
                                                                    check_limits["VIYA_KUBELET_VERSION_MIN"],
                                                                    check_limits["VIYA_MIN_WORKER_ALLOCATABLE_CPU"],
                                                                    check_limits["VIYA_MIN_AGGREGATE_WORKER_CPU_CORES"],
                                                                    check_limits["VIYA_MIN_ALLOCATABLE_WORKER_MEMORY"],
                                                                    check_limits["VIYA_MIN_AGGREGATE_WORKER_MEMORY"])
    # gather the details for the report
    try:
        sas_pre_check_report.check_details(kubectl, ingress_port, ingress_host, ingress_controller, output_dir)
    except RuntimeError as e:
        print()
        print(viya_messages.EXCEPTION_MESSAGE.format(e))
        print()
        sys.exit(viya_messages.RUNTIME_ERROR_RC_)

    sys.exit(0)

##################
#     main()     #
##################


if __name__ == '__main__':
    main(sys.argv[1:])
# ----------------------------------------------------------------------------
