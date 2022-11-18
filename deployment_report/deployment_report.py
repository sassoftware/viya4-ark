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
import os
import sys

from argparse import ArgumentParser
from typing import List, Text

from deployment_report.model.viya_deployment_report import ViyaDeploymentReport

from viya_ark_library.command import Command
from viya_ark_library.lrp_indicator import LRPIndicator
from viya_ark_library.k8s.sas_k8s_errors import KubectlRequestForbiddenError, NamespaceNotFoundError
from viya_ark_library.k8s.sas_kubectl import Kubectl

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
    # configure ArgumentParser
    arg_parser: ArgumentParser = ArgumentParser(prog=f"viya-ark.py {ViyaDeploymentReportCommand.command_name()}",
                                                description=ViyaDeploymentReportCommand.command_desc())

    # add optional arguments
    # data-file-only
    arg_parser.add_argument(
        "-d", "--data-file-only", action="store_true", dest="data_file_only",
        help="Generate only the JSON-formatted data.")
    # ingress namespace
    arg_parser.add_argument(
        "-i", "--ingress-namespace", type=Text, default=None, dest="ingress_namespace",
        help="Ingress namespace in the target cluster.")
    # kubectl-global-opts
    arg_parser.add_argument(
        "-k", "--kubectl-global-opts", type=Text, default="", dest="kubectl_global_opts",
        help="Any kubectl global options to use with all executions (excluding namespace, which should be set using "
             "-n, --namespace).")
    # include-pod-log-snips
    arg_parser.add_argument(
        "-l", "--include-pod-log-snips", action="store_true", dest="include_pod_log_snips",
        help="Include the most recent log lines (up to 10) for each container in the report. This option increases "
             "command runtime and file size.")
    # namespace
    arg_parser.add_argument(
        "-n", "--namespace", type=Text, default=None, dest="namespace",
        help="Namespace to target containing SAS software, if not defined by KUBECONFIG.")
    # output-dir
    arg_parser.add_argument(
        "-o", "--output-dir", type=Text, default=ViyaDeploymentReport.OUTPUT_DIRECTORY_DEFAULT, dest="output_dir",
        help="Directory where log files will be written. Defaults to "
             f"\"{ViyaDeploymentReport.OUTPUT_DIRECTORY_DEFAULT}\".")
    # include-resource-definitions
    arg_parser.add_argument(
        "-r", "--include-resource-definitions", action="store_true", dest="include_resource_definitions",
        help="Include the full JSON-formatted definition for each resource in the report. This option increases file "
             "size.")

    # parse the args passed to this command
    args = arg_parser.parse_args(argv)

    # initialize the kubectl object
    # this will also verify the connection to the cluster and if the namespace is valid, if provided
    try:
        kubectl: Kubectl = Kubectl(namespace=args.namespace, global_opts=args.kubectl_global_opts,
                                   ingress_namespace=args.ingress_namespace)
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
        print()
        with LRPIndicator(enter_message="Generating deployment report"):
            sas_deployment_report.gather_details(kubectl=kubectl,
                                                 include_pod_log_snips=args.include_pod_log_snips)
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

    data_file, html_file = sas_deployment_report.write_report(
        output_directory=args.output_dir,
        data_file_only=args.data_file_only,
        include_resource_definitions=args.include_resource_definitions)

    print(f"\nCreated: {data_file}")
    if not args.data_file_only:
        print(f"Created: {html_file}")
    print()

    sys.exit(_SUCCESS_RC_)


####################
#     __main__     #
####################
if __name__ == "__main__":
    main(sys.argv[1:])
