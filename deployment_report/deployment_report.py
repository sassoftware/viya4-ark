####################################################################
# ### deployment_report.py                                       ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import getopt
import os
import sys

from typing import List, Optional, Text, Tuple

from deployment_report.model.viya_deployment_report import ViyaDeploymentReport

from viya_arkcd_library.command import Command
from viya_arkcd_library.k8s.sas_k8s_errors import KubectlRequestForbiddenError, NamespaceNotFoundError
from viya_arkcd_library.k8s.sas_kubectl import Kubectl

# command line options
_DATA_FILE_OPT_SHORT_ = "d"
_DATA_FILE_OPT_LONG_ = "data-file-only"
_DATA_FILE_OPT_DESC_TMPL_ = "    -{}, --{:<30} (Optional) Generate only the report data JSON file."

_KUBECTL_GLOBAL_OPT_SHORT_ = "k"
_KUBECTL_GLOBAL_OPT_LONG_ = "kubectl-global-opts"
_KUBECTL_GLOBAL_OPT_DESC_TMPL_ = "    -{}, --{:<30} (Optional) Any kubectl global options to use with all executions " \
                                 "(excluding namespace, which should be set using -n, --namespace=)."

_POD_SNIP_OPT_SHORT_ = "l"
_POD_SNIP_OPT_LONG_ = "include-pod-log-snips"
_POD_SNIP_OPT_DESC_TMPL_ = "    -{}, --{:<30} (Optional) Include a 10-line log snippet for each pod container " \
                           "(increases command runtime and file size)."

_NAMESPACE_OPT_SHORT_ = "n"
_NAMESPACE_OPT_LONG_ = "namespace"
_NAMESPACE_OPT_DESC_TMPL_ = "    -{}, --{:<30} (Optional) The namespace to target containing SAS software, if not " \
                            "defined by KUBECONFIG."

_OUTPUT_DIR_OPT_SHORT_ = "o"
_OUTPUT_DIR_OPT_LONG_ = "output-dir"
_OUTPUT_DIR_OPT_DESC_TMPL_ = "    -{}, --{:<30} (Optional) Existing directory where report files will be written."

_RESOURCE_DEF_OPT_SHORT_ = "r"
_RESOURCE_DEF_OPT_LONG_ = "include-resource-definitions"
_RESOURCE_DEF_OPT_DESC_TMPL_ = "    -{}, --{:<30} (Optional) Include the full JSON resource definition for each " \
                               "object in the report (increases file size)."

_HELP_OPT_SHORT_ = "h"
_HELP_OPT_LONG_ = "help"
_HELP_OPT_DESC_TMPL_ = "    -{}, --{:<30} Print usage."

# command line return codes #
_SUCCESS_RC_ = 0
_BAD_OPT_RC_ = 1
_CONNECTION_ERROR_RC_ = 3
_NAMESPACE_NOT_FOUND_RC_ = 4
_RUNTIME_ERROR_RC_ = 5
_LIST_PODS_FORBIDDEN_ERROR_RC_ = 6


##############################################
#     CLASS: ViyaDeploymentReportCommand     #
##############################################
class ViyaDeploymentReportCommand(Command):
    """
    Command implementation for the deployment-report command to registered the module as an executable task with the
    launcher script.
    """

    @staticmethod
    def run(argv: List):
        """
        Method called when a request to execute the deployment-report is made.
        """
        main(argv)

    @staticmethod
    def command_name() -> Text:
        """
        Method defining the command name value for the project launcher script.
        """
        return os.path.basename(os.path.dirname(__file__)).replace("_", "-")

    @staticmethod
    def command_desc() -> Text:
        """
        Method defining the human-friendly command description for display by the launcher script help.
        """
        return "Generate a deployment report of SAS components for a target Kubernetes environment."


##################
#     main()     #
##################
def main(argv: List):
    """
    Implementation of the main script execution for the deployment-report command.

    :param argv: The parameters passed to the script at execution.
    """
    data_file_only: bool = False
    kubectl_global_opts: Text = ""
    include_pod_log_snips: bool = False
    namespace: Optional[Text] = None
    output_dir: Text = "./"
    include_resource_definitions: bool = False

    # define the short options for this script
    short_opts: Text = (f"{_DATA_FILE_OPT_SHORT_}"
                        f"{_KUBECTL_GLOBAL_OPT_SHORT_}:"
                        f"{_POD_SNIP_OPT_SHORT_}"
                        f"{_NAMESPACE_OPT_SHORT_}:"
                        f"{_OUTPUT_DIR_OPT_SHORT_}:"
                        f"{_RESOURCE_DEF_OPT_SHORT_}"
                        f"{_HELP_OPT_SHORT_}")

    # define the long options for this script
    long_opts: List[Text] = [_DATA_FILE_OPT_LONG_,
                             f"{_KUBECTL_GLOBAL_OPT_LONG_}=",
                             _POD_SNIP_OPT_LONG_,
                             f"{_NAMESPACE_OPT_LONG_}=",
                             f"{_OUTPUT_DIR_OPT_LONG_}=",
                             _RESOURCE_DEF_OPT_LONG_,
                             _HELP_OPT_LONG_]

    # get command line options
    opts: Tuple = tuple()
    try:
        opts, args = getopt.getopt(argv, short_opts, long_opts)
    except getopt.GetoptError as opt_error:
        print()
        print(f"ERROR: {opt_error}", file=sys.stderr)
        usage(_BAD_OPT_RC_)

    # process opts
    for opt, arg in opts:
        if opt in (f"-{_DATA_FILE_OPT_SHORT_}", f"--{_DATA_FILE_OPT_LONG_}"):
            data_file_only = True

        elif opt in (f"-{_KUBECTL_GLOBAL_OPT_SHORT_}", f"--{_KUBECTL_GLOBAL_OPT_LONG_}"):
            kubectl_global_opts = arg

        elif opt in (f"-{_POD_SNIP_OPT_SHORT_}", f"--{_POD_SNIP_OPT_LONG_}"):
            include_pod_log_snips = True

        elif opt in (f"-{_NAMESPACE_OPT_SHORT_}", f"--{_NAMESPACE_OPT_LONG_}"):
            namespace = arg

        elif opt in (f"-{_OUTPUT_DIR_OPT_SHORT_}", f"--{_OUTPUT_DIR_OPT_LONG_}"):
            output_dir = arg

        elif opt in (f"-{_RESOURCE_DEF_OPT_SHORT_}", f"--{_RESOURCE_DEF_OPT_LONG_}"):
            include_resource_definitions = True

        elif opt in (f"-{_HELP_OPT_SHORT_}", f"--{_HELP_OPT_LONG_}"):
            usage(_SUCCESS_RC_)

        else:
            print()
            print(f"ERROR: option {opt} not recognized", file=sys.stderr)
            usage(_BAD_OPT_RC_)

    # initialize the kubectl object
    # this will also verify the connection to the cluster and if the namespace is valid, if provided
    try:
        kubectl: Kubectl = Kubectl(namespace=namespace, global_opts=kubectl_global_opts)
    except ConnectionError as e:
        print()
        print(f"ERROR: {e}", file=sys.stderr)
        print()
        sys.exit(_CONNECTION_ERROR_RC_)
    except NamespaceNotFoundError as e:
        print()
        print(f"ERROR: {e}", file=sys.stderr)
        print()
        sys.exit(_NAMESPACE_NOT_FOUND_RC_)

    # create the SASDeploymentReport object
    sas_deployment_report: ViyaDeploymentReport = ViyaDeploymentReport()

    # gather the details for the report
    try:
        sas_deployment_report.gather_details(kubectl=kubectl,
                                             include_pod_log_snips=include_pod_log_snips)
    except KubectlRequestForbiddenError as e:
        print()
        print(f"ERROR: {e}", file=sys.stderr)
        print()
        sys.exit(_LIST_PODS_FORBIDDEN_ERROR_RC_)
    except RuntimeError as e:
        print()
        print(f"ERROR: {e}", file=sys.stderr)
        print()
        sys.exit(_RUNTIME_ERROR_RC_)

    sas_deployment_report.write_report(output_directory=output_dir,
                                       data_file_only=data_file_only,
                                       include_resource_definitions=include_resource_definitions)

    sys.exit(_SUCCESS_RC_)


###################
#     usage()     #
###################
def usage(exit_code: int):
    """
    Prints the usage information for the deployment-report command and exits the program with the given exit_code.

    :param exit_code: The exit code to return when exiting the program.
    """
    print()
    print(f"Usage: {ViyaDeploymentReportCommand.command_name()} [<options>]")
    print()
    print("Options:")
    print(_DATA_FILE_OPT_DESC_TMPL_.format(_DATA_FILE_OPT_SHORT_, _DATA_FILE_OPT_LONG_))
    print(_KUBECTL_GLOBAL_OPT_DESC_TMPL_.format(_KUBECTL_GLOBAL_OPT_SHORT_, _KUBECTL_GLOBAL_OPT_LONG_ + "=\"<opts>\""))
    print(_POD_SNIP_OPT_DESC_TMPL_.format(_POD_SNIP_OPT_SHORT_, _POD_SNIP_OPT_LONG_))
    print(_NAMESPACE_OPT_DESC_TMPL_.format(_NAMESPACE_OPT_SHORT_, _NAMESPACE_OPT_LONG_ + "=\"<namespace>\""))
    print(_OUTPUT_DIR_OPT_DESC_TMPL_.format(_OUTPUT_DIR_OPT_SHORT_, _OUTPUT_DIR_OPT_LONG_ + "=\"<dir>\""))
    print(_RESOURCE_DEF_OPT_DESC_TMPL_.format(_RESOURCE_DEF_OPT_SHORT_, _RESOURCE_DEF_OPT_LONG_))
    print(_HELP_OPT_DESC_TMPL_.format(_HELP_OPT_SHORT_, _HELP_OPT_LONG_))
    print()
    sys.exit(exit_code)


####################
#     __main__     #
####################
if __name__ == "__main__":
    main(sys.argv[1:])
