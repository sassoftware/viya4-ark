####################################################################
# ### download_pod_logs.py                                       ###
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

from viya_ark_library.command import Command
from viya_ark_library.lrp_indicator import LRPIndicator
from viya_ark_library.k8s.sas_kubectl import Kubectl
from viya_ark_library.k8s.sas_k8s_errors import NamespaceNotFoundError

from download_pod_logs.model import NoMatchingPodsError, NoPodsError, PodLogDownloader

# command line return codes #
_SUCCESS_RC_ = 0
_BAD_OPT_RC_ = 1
_CONNECTION_ERROR_RC_ = 3
_NAMESPACE_NOT_FOUND_RC_ = 4
_LOGS_UNAVAILABLE_ERROR_RC_ = 5


####################################################################
# CLASS: DownloadPodLogsCommand                                  ###
####################################################################
class DownloadPodLogsCommand(Command):
    """
    Command implementation for the download-pod-logs command to registered the module as an executable task with the
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
        return "Download log files for all or a select list of pods."


####################################################################
# main()                                                         ###
####################################################################
def main(argv: List):
    """
    Implementation of the main script execution for the download-pod-logs command.

    :param argv: The parameters passed to the script at execution.
    """
    # configure ArgumentParser
    arg_parser = ArgumentParser(prog=f"viya-ark.py {DownloadPodLogsCommand.command_name()}",
                                description=DownloadPodLogsCommand.command_desc())

    # add optional arguments
    # namespace
    arg_parser.add_argument(
        "-n", "--namespace", type=Text, default=None, dest="namespace",
        help="Namespace to target containing SAS software, if not defined by KUBECONFIG.")
    # output-dir
    arg_parser.add_argument(
        "-o", "--output-dir", type=Text, default=PodLogDownloader.DEFAULT_OUTPUT_DIR, dest="output_dir",
        help=f"Directory where log files will be written. Defaults to \"{PodLogDownloader.DEFAULT_OUTPUT_DIR}\".")
    # processes
    arg_parser.add_argument(
        "-p", "--processes", type=int, default=PodLogDownloader.DEFAULT_PROCESSES, dest="processes",
        help="Number of simultaneous worker processes used to fetch logs. Defaults to "
             f"\"{PodLogDownloader.DEFAULT_PROCESSES}\".")
    # tail
    arg_parser.add_argument(
        "-t", "--tail", type=int, default=PodLogDownloader.DEFAULT_TAIL, dest="tail",
        help=f"Lines of recent log file to retrieve. Defaults to \"{PodLogDownloader.DEFAULT_TAIL}\".")
    # wait
    arg_parser.add_argument(
        "-w", "--wait", type=int, default=PodLogDownloader.DEFAULT_WAIT, dest="wait",
        help="Wait time, in seconds, before terminating a log-gathering process. Defaults to "
             f"\"{PodLogDownloader.DEFAULT_WAIT}\".")

    # add positional arguments
    arg_parser.add_argument(
        "selected_components", default=None, nargs="*",
        help="A space-separated list of SAS component names used to limit the logs downloaded. If no component names "
             "are provided, logs for all SAS components will be downloaded.")

    # parse the args passed to this command
    args = arg_parser.parse_args(argv)

    # initialize the kubectl object
    # this will also verify the connection to the cluster and if the namespace is valid, if provided
    try:
        kubectl: Kubectl = Kubectl(namespace=args.namespace)
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

    # create the log downloader
    try:
        log_downloader = PodLogDownloader(kubectl=kubectl,
                                          output_dir=args.output_dir,
                                          processes=args.processes,
                                          wait=args.wait)
    except AttributeError as e:
        print()
        print(f"ERROR: {e}", sys.stderr)
        print()
        sys.exit(_BAD_OPT_RC_)

    # download the logs
    try:
        print()
        with LRPIndicator(enter_message="Downloading pod logs"):
            log_dir, timeout_pods = log_downloader.download_logs(selected_components=args.selected_components,
                                                                 tail=args.tail)

        # print any pods that timed out, if present
        if len(timeout_pods) > 0:
            print()
            print("WARNING: Logs for the following pods were not downloaded because they exceeded the configured wait "
                  f"time ({args.wait}s):")
            print()

            # print the pods that timed out
            for pod_name in timeout_pods:
                print(f"    {pod_name}")

            print()
            print("The wait time can be increased using the \"--wait=\" option.")

        # print output directory
        print()
        print(f"Log files created in: {log_dir}")
        print()
    except (NoMatchingPodsError, NoPodsError) as e:
        print()
        print(e)
        print()
        sys.exit(_SUCCESS_RC_)

    # exit successfully
    sys.exit(_SUCCESS_RC_)


####################################################################
# __main__                                                       ###
####################################################################
if __name__ == "__main__":
    main(sys.argv[1:])
