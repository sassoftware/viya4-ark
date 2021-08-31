####################################################################
# ### viya_top_reports.py                                        ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import datetime
import os

from subprocess import CalledProcessError
from typing import AnyStr, List, Optional, Text, Tuple

from viya_ark_library.k8s.sas_k8s_errors import KubectlRequestForbiddenError
from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface

# templates for string-formatted timestamp values #
_READABLE_TIMESTAMP_TMPL_ = "%A, %B %d, %Y %I:%M%p"
_FILE_TIMESTAMP_TMPL_ = "%Y-%m-%dT%H_%M_%S"

# templates for output file names #
_REPORT_DATA_FILE_NAME_TMPL_ = "viya_top_reports_{}_data_{}.txt"


class ViyaTopReports(object):
    """
    A ViyaTopReports object represents the data returned from the Kubernetes top reports.

    The gathered data is written to disk as text files containing the gathered data.
    """

    # default values for arguments shared between the library and command #
    OUTPUT_DIRECTORY_DEFAULT: Text = "./"
    USE_PROTOCOL_BUFFERS_DEFAULT: bool = False

    def __init__(self) -> None:
        """
        Constructor for ViyaTopReports object.
        """
        self._node_report_data = None
        self._pod_report_data = None

    def gather_reports(self, kubectl: KubectlInterface,
                       use_protocol_buffers: bool = USE_PROTOCOL_BUFFERS_DEFAULT) -> None:
        """
        This method executes the gathering of Kubernetes top reports.

        :param kubectl: The configured KubectlInterface object used to communicate with the desired Kubernetes cluster.
        """
        #######################################################################
        # Gather Kubernetes top details                                     ###
        #######################################################################

        if not use_protocol_buffers:
            top_options = ""
        else:
            top_options = "--use_protocol_buffers"

        # mark when these details were gathered #
        gathered: Text = datetime.datetime.now().strftime(_READABLE_TIMESTAMP_TMPL_)

        # get the top node values #
        # if Nodes cannot be listed, display a message #
        top_command = f"top node {top_options}"
        try:
            top_nodes_raw: AnyStr = kubectl.do(top_command, False)
        except CalledProcessError:
            # if a CalledProcessError is raised when gathering nodes, then surface an error up to stop the program #
            # without the ability to list top nodes #
            raise KubectlRequestForbiddenError(f"Listing nodes is forbidden in namespace [{kubectl.get_namespace()}]. "
                                               "Make sure KUBECONFIG is correctly set and that the correct namespace "
                                               "is being targeted. A namespace can be given on the command line using "
                                               "the \"--namespace=\" option.")
        top_nodes_lines: List = top_nodes_raw.decode()

        # get the top pod values #
        # if Pods cannot be listed, display a message #
        top_command = f"top pod {top_options}"
        try:
            top_pods_raw: AnyStr = kubectl.do(top_command, False)
        except CalledProcessError:
            # if a CalledProcessError is raised when gathering pods, then surface an error up to stop the program #
            # without the ability to list top pods #
            raise KubectlRequestForbiddenError(f"Listing pods is forbidden in namespace [{kubectl.get_namespace()}]. "
                                               "Make sure KUBECONFIG is correctly set and that the correct namespace "
                                               "is being targeted. A namespace can be given on the command line using "
                                               "the \"--namespace=\" option.")
        top_pods_lines: List = top_pods_raw.decode()

        # add the gathered data #
        self._node_report_data: Text = top_nodes_lines
        self._pod_report_data: Text = top_pods_lines

    def write_report(self, output_directory: Text = OUTPUT_DIRECTORY_DEFAULT,
                     file_timestamp: Optional[Text] = None) -> Tuple[Optional[AnyStr], Optional[AnyStr]]:
        """
        Writes the report data to text files.

        :param output_directory: The directory where the file should be written.
        :param file_timestamp: A timestamp to use for the file. If one isn't provided, a new one will be created.
        """
        if (self._node_report_data is None) or (self._pod_report_data is None):
            return None, None

        # get a timestamp if one isn't given #
        if file_timestamp is None:
            file_timestamp = datetime.datetime.now().strftime(_FILE_TIMESTAMP_TMPL_)

        # make sure path is valid #
        if output_directory != "" and not output_directory.endswith(os.sep):
            output_directory = output_directory + os.sep

        # Grab the reported data #
        node_data_text = self._node_report_data
        pod_data_text = self._pod_report_data

        # write the report data #
        node_data_file_path: Text = output_directory + _REPORT_DATA_FILE_NAME_TMPL_.format('node', file_timestamp)
        with open(node_data_file_path, "w+") as data_file:
            data_file.write(node_data_text)

        pod_data_file_path: Text = output_directory + _REPORT_DATA_FILE_NAME_TMPL_.format('pod', file_timestamp)
        with open(pod_data_file_path, "w+") as data_file:
            data_file.write(pod_data_text)
        return os.path.abspath(node_data_file_path), os.path.abspath(pod_data_file_path)
