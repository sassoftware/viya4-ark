####################################################################
# ### sas_k8s_errors.py                                          ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################


class KubectlRequestForbiddenError(RuntimeError):
    """
    Exception raised when a kubectl request is forbidden by the cluster.
    """

    def __init__(self, message):
        super().__init__(message)


class NamespaceNotFoundError(RuntimeError):
    """
    Exception raised when the provided namespace cannot be found in the target environment or in the current context.
    """

    def __init__(self, message):
        super().__init__(message)
