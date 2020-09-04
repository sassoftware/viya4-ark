####################################################################
# ### test_sas_k8s_errors.py                                     ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import pytest

from viya_ark_library.k8s.sas_k8s_errors import KubectlRequestForbiddenError, NamespaceNotFoundError


def test_kubectl_request_forbidden_error() -> None:
    """
    This test verifies that the message is correctly set for the KubectlRequestForbiddenError.
    """
    expected_message = "test message for KubectlRequestForbiddenError"

    with pytest.raises(KubectlRequestForbiddenError) as exec_info:
        raise KubectlRequestForbiddenError(expected_message)

    assert expected_message in str(exec_info.value)
    assert isinstance(exec_info.value, KubectlRequestForbiddenError)
    assert isinstance(exec_info.value, RuntimeError)


def test_namespace_not_found_error() -> None:
    """
    This test verifies that the message is correctly set for the NamespaceNotFoundError.
    """
    expected_message = "test message for NamespaceNotFoundError"

    with pytest.raises(NamespaceNotFoundError) as exec_info:
        raise NamespaceNotFoundError(expected_message)

    assert expected_message in str(exec_info.value)
    assert isinstance(exec_info.value, NamespaceNotFoundError)
    assert isinstance(exec_info.value, RuntimeError)
