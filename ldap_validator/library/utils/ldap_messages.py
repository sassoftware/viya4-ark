####################################################################
# ### ldap_messages.py                                         ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
# Error Messages written to console and logs
#
# Error Messages

OPTION_ERROR = "ERROR: option {} not recognized"
OPTION_VALUES_ERROR = "ERROR: Provide valid values for all required options. Check option -s."
OUPUT_PATH_ERROR = "ERROR: The report output path is not valid {}. Check value on option -o "
EXCEPTION_MESSAGE = "ERROR: {}"

# command line return codes #
SUCCESS_RC_ = 0
BAD_OPT_RC_ = 1
BAD_ENV_RC_ = 2
BAD_SITEYAML_RC_ = 3
OUPUT_PATH_ERROR = 4
RUNTIME_ERROR_RC_ = 5
