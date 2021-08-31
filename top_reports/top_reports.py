####################################################################
# ### top_reports.py                                             ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import os
import sys

from argparse import ArgumentParser
from typing import List, Text

from top_reports.library.viya_top_reports import ViyaTopReports

from viya_ark_library.command import Command
from viya_ark_library.lrp_indicator import LRPIndicator
from viya_ark_library.k8s.sas_k8s_errors import KubectlRequestForbiddenError, NamespaceNotFoundError
from viya_ark_library.k8s.sas_kubectl import Kubectl

# command line return codes #
_SUCCESS_RC_ = 0
_CONNECTION_ERROR_RC_ = 3
_NAMESPACE_NOT_FOUND_RC_ = 4
_RUNTIME_ERROR_RC_ = 5
_LIST_PODS_FORBIDDEN_ERROR_RC_ = 6


##############################################
# CLASS: ViyaTopReportsCommand             ###
##############################################
class ViyaTopReportsCommand(Command):
    """
    Command implementation for the top-reports command to registered the module as an executable task with the
    launcher script.
    """

    @staticmethod
    def run(argv: List):
        """
        Method called when a request to execute top-reports is made.
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
        return "Generate top reports for a target Kubernetes environment."


##################
# main()       ###
##################
def main(argv: List):
    """
    Implementation of the main script execution for the top-reports command.

    :param argv: The parameters passed to the script at execution.
    """
    # configure ArgumentParser
    arg_parser: ArgumentParser = ArgumentParser(prog=f"viya-ark.py {ViyaTopReportsCommand.command_name()}",
                                                description=ViyaTopReportsCommand.command_desc())

    # add optional arguments
    # kubectl-global-opts
    arg_parser.add_argument(
        "-k", "--kubectl-global-opts", type=Text, default="", dest="kubectl_global_opts",
        help="Any kubectl global options to use with all executions (excluding namespace, which should be set using "
             "-n, --namespace).")
    # namespace
    arg_parser.add_argument(
        "-n", "--namespace", type=Text, default=None, dest="namespace",
        help="Namespace to target containing SAS software, if not defined by KUBECONFIG.")
    # output-dir
    arg_parser.add_argument(
        "-o", "--output-dir", type=Text, default=ViyaTopReports.OUTPUT_DIRECTORY_DEFAULT, dest="output_dir",
        help="Directory where top reports files will be written. Defaults to "
             f"\"{ViyaTopReports.OUTPUT_DIRECTORY_DEFAULT}\".")
    # use-protocol-buffers
    arg_parser.add_argument(
        "-u", "--use-protocol-buffers", action="store_true", dest="use_protocol_buffers",
        help="(Optional)Use protocol-buffers to request metrics. Historically, json format has been used by the "
             "top command to get metrics. Newer Kubernetes releases will migrate to using protocol-buffers. "
             "Switch early by specifying this option.")

    # parse the args passed to this command
    args = arg_parser.parse_args(argv)

    # initialize the kubectl object
    # this will also verify the connection to the cluster and if the namespace is valid, if provided
    try:
        kubectl: Kubectl = Kubectl(namespace=args.namespace, global_opts=args.kubectl_global_opts)
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

    # create the SASTopReports object
    sas_top_reports: ViyaTopReports = ViyaTopReports()

    # gather the details for the reports
    try:
        print()
        with LRPIndicator(enter_message="Generating top reports"):
            sas_top_reports.gather_reports(kubectl=kubectl,
                                           use_protocol_buffers=args.use_protocol_buffers)
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

    data_top_nodes_file, data_top_pods_file = sas_top_reports.write_report(
        output_directory=args.output_dir)

    print(f"\nCreated: {data_top_nodes_file}")
    print(f"\nCreated: {data_top_pods_file}")
    print()

    sys.exit(_SUCCESS_RC_)


####################
# __main__       ###
####################
if __name__ == "__main__":
    main(sys.argv[1:])
