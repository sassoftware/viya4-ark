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
import getopt
import os
import sys

from typing import List, Optional, Text, Tuple

from viya_arkcd_library.command import Command
from viya_arkcd_library.k8s.sas_kubectl import Kubectl
from viya_arkcd_library.k8s.sas_k8s_errors import NamespaceNotFoundError

from download_pod_logs.model.pod_log_downloader import NoMatchingPodsError, NoPodsError, PodLogDownloader

# command line options
_NAMESPACE_OPT_SHORT_ = "n"
_NAMESPACE_OPT_LONG_ = "namespace"
_NAMESPACE_OPT_DESC_TMPL_ = "    -{}, --{:<30} (Optional) Namespace to target containing SAS software, if not " \
                            "defined by KUBECONFIG."

_OUTPUT_DIR_OPT_SHORT_ = "o"
_OUTPUT_DIR_OPT_LONG_ = "output-dir"
_OUTPUT_DIR_OPT_DESC_TMPL_ = "    -{}, --{:<30} (Optional) Directory where log files will be written. " \
                             f"Defaults to \"./{PodLogDownloader.DEFAULT_OUTPUT_DIR}\"."

_PROCESSES_OPT_SHORT_ = "p"
_PROCESSES_OPT_LONG_ = "processes"
_PROCESSES_OPT_DESC_TMPL_ = "    -{}, --{:<30} (Optional) Number of simultaneous worker processes used " \
                            f"to fetch logs. Defaults to \"{PodLogDownloader.DEFAULT_CONCURRENT_PROCESSES}\"."

_PROCESS_WAIT_TIME_OPT_SHORT_ = "w"
_PROCESS_WAIT_TIME_OPT_LONG_ = "wait"
_PROCESS_WAIT_TIME_DESC_TMPL_ = "    -{}, --{:<30} (Optional) Wait time, in seconds, before terminating a " \
                                f"log-gathering process. Defaults to \"{PodLogDownloader.DEFAULT_PROCESS_WAIT_TIME}\"."

_TAIL_OPT_SHORT_ = "t"
_TAIL_OPT_LONG_ = "tail-lines"
_TAIL_OPT_DESC_TMPL_ = "    -{}, --{:<30} (Optional) Lines of recent log file to retrieve. Defaults to " \
                       f"\"{PodLogDownloader.DEFAULT_TAIL}\"."

_HELP_OPT_SHORT_ = "h"
_HELP_OPT_LONG_ = "help"
_HELP_OPT_DESC_TMPL_ = "    -{}, --{:<30} Print usage."

# command line return codes #
_SUCCESS_RC_ = 0
_BAD_OPT_RC_ = 1
_CONNECTION_ERROR_RC_ = 3
_NAMESPACE_NOT_FOUND_RC_ = 4
_LOGS_UNAVAILABLE_ERROR_RC_ = 5


##############################################
#       CLASS: DownloadPodLogsCommand        #
##############################################
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


##################
#     main()     #
##################
def main(argv: List):
    """
    Implementation of the main script execution for the download-pod-logs command.

    :param argv: The parameters passed to the script at execution.
    """
    namespace: Optional[Text] = None
    output_dir: Text = PodLogDownloader.DEFAULT_OUTPUT_DIR
    concurrent_processes: int = PodLogDownloader.DEFAULT_CONCURRENT_PROCESSES
    process_wait_time: int = PodLogDownloader.DEFAULT_PROCESS_WAIT_TIME
    tail: int = PodLogDownloader.DEFAULT_TAIL

    # define the short options for this script
    short_opts: Text = (f"{_NAMESPACE_OPT_SHORT_}:"
                        f"{_OUTPUT_DIR_OPT_SHORT_}:"
                        f"{_PROCESSES_OPT_SHORT_}:"
                        f"{_PROCESS_WAIT_TIME_OPT_SHORT_}:"
                        f"{_TAIL_OPT_SHORT_}:"
                        f"{_HELP_OPT_SHORT_}")

    long_opts: List[Text] = [f"{_NAMESPACE_OPT_LONG_}=",
                             f"{_OUTPUT_DIR_OPT_LONG_}=",
                             f"{_PROCESSES_OPT_LONG_}=",
                             f"{_PROCESS_WAIT_TIME_OPT_LONG_}=",
                             f"{_TAIL_OPT_LONG_}=",
                             "{_HELP_OPT_LONG_}"]

    # get command line options
    opts: List[Tuple[Text, Text]] = list()
    selected_components: List[Text] = list()
    try:
        opts, selected_components = getopt.getopt(argv, short_opts, long_opts)
    except getopt.GetoptError as opt_error:
        print()
        print(f"ERROR: {opt_error}", file=sys.stderr)
        usage(_BAD_OPT_RC_)

    # process options
    for opt, arg in opts:
        if opt in (f"-{_HELP_OPT_SHORT_}", f"--{_HELP_OPT_LONG_}"):
            usage(_SUCCESS_RC_)

        elif opt in (f"-{_NAMESPACE_OPT_SHORT_}", f"--{_NAMESPACE_OPT_LONG_}"):
            namespace = arg

        elif opt in (f"-{_OUTPUT_DIR_OPT_SHORT_}", f"--{_OUTPUT_DIR_OPT_LONG_}"):
            output_dir = arg

        elif opt in (f"-{_PROCESSES_OPT_SHORT_}", f"--{_PROCESSES_OPT_LONG_}"):
            concurrent_processes = int(arg)

        elif opt in (f"-{_PROCESS_WAIT_TIME_OPT_SHORT_}", f"--{_PROCESS_WAIT_TIME_OPT_LONG_}"):
            process_wait_time = int(arg)

        elif opt in (f"-{_TAIL_OPT_SHORT_}", f"--{_TAIL_OPT_LONG_}"):
            tail = int(arg)

        else:
            print()
            print(f"ERROR: option {opt} not recognized", file=sys.stderr)
            usage(_BAD_OPT_RC_)

    # initialize the kubectl object
    # this will also verify the connection to the cluster and if the namespace is valid, if provided
    try:
        kubectl: Kubectl = Kubectl(namespace=namespace)
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
        log_downloader = PodLogDownloader(kubectl=kubectl, output_dir=output_dir,
                                          concurrent_processes=concurrent_processes,
                                          process_wait_time=process_wait_time)
    except AttributeError as e:
        print()
        print(f"ERROR: {e}", sys.stderr)
        print()
        sys.exit(_BAD_OPT_RC_)

    # download the logs
    try:
        log_downloader.download_logs(selected_components=selected_components, tail=tail)
    except (NoMatchingPodsError, NoPodsError) as e:
        print()
        print(e)
        print()
        sys.exit(_SUCCESS_RC_)

    # exit successfully
    sys.exit(_SUCCESS_RC_)


###################
#     usage()     #
###################
def usage(exit_code: int):
    """
    Prints the usage information for the download-pod-logs command and exits the program with the given exit_code.

    :param exit_code: The exit code to return when exiting the program.
    """
    print()
    print(f"Usage: {DownloadPodLogsCommand.command_name()} [<options>] [<components>]")
    print()
    print("Options:")
    print(_NAMESPACE_OPT_DESC_TMPL_.format(_NAMESPACE_OPT_SHORT_, _NAMESPACE_OPT_LONG_ + "=\"<namespace>\""))
    print(_OUTPUT_DIR_OPT_DESC_TMPL_.format(_OUTPUT_DIR_OPT_SHORT_, _OUTPUT_DIR_OPT_LONG_ + "=\"<dir>\""))
    print(_PROCESSES_OPT_DESC_TMPL_.format(_PROCESSES_OPT_SHORT_, _PROCESSES_OPT_LONG_ + "=\"<processes>\""))
    print(_TAIL_OPT_DESC_TMPL_.format(_TAIL_OPT_SHORT_, _TAIL_OPT_LONG_ + "=\"<tail>\""))
    print(_PROCESS_WAIT_TIME_DESC_TMPL_.format(_PROCESS_WAIT_TIME_OPT_SHORT_, _PROCESS_WAIT_TIME_OPT_LONG_ +
                                               "=\"<wait>\""))
    print(_HELP_OPT_DESC_TMPL_.format(_HELP_OPT_SHORT_, _HELP_OPT_LONG_))
    print()
    print("Optionally, a space-separated list of components can be provided to limit results:")
    print(f"    {DownloadPodLogsCommand.command_name()} -n default sas-visual-analytics sas-annotations")
    print()
    sys.exit(exit_code)


####################
#     __main__     #
####################
if __name__ == "__main__":
    main(sys.argv[1:])
