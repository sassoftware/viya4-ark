####################################################################
# ### viya_messages.py                                         ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020-2022, SAS Institute Inc., Cary, NC, USA.    ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
# Error Messages written to console and logs
#
# Error Messages
CONFIG_ERROR = "ERROR: Unable to read configuration file. Make " \
               "sure that kubectl" \
               " is properly configured and the KUBECONFIG " \
               "environment variable has a valid value"
KUBECONF_ERROR = "ERROR: KUBECONFIG environment var must be set for the script " \
                "to access the Kubernetes cluster."
CHECK_NAMESPACE = ' ERROR: Check available permissions in namespace and if it is valid: '
LIMIT_ERROR = 'ERROR: The value in the viya_deployment_settings.ini file is not valid: {} = {}'
KUBELET_VERSION_ERROR = 'ERROR: Check the VIYA_KUBELET_VERSION_MIN value ' \
                        'specified in the pre_install_report/viya_deployment_settings.ini file'
OPTION_ERROR = "ERROR: option {} not recognized"
OPTION_VALUES_ERROR = "ERROR: Provide valid values for all required options. Check options -i, -p and -H."
INGRESS_CONTROLLER_ERROR = "ERROR: Ingress controller specified must be nginx or openshift. Check value on option -i "
OUPUT_PATH_ERROR = "ERROR: The report output path is not valid {}. Check value on option -o "
EXCEPTION_MESSAGE = "ERROR: {}"
KUBECONF_FILE_ERROR = "ERROR: The file specified in the KUBECONFIG environment does not exist. " \
                      "Check that file {} exists."
KUBERNETES_VERSION_ERROR = "Kubernetes version is missing or invalid: {}"
CLUSTER_CREATION_INFO = "** SAS recommends using the IaC tools to create the cluster. See SAS Viya 4 Infrastructure as Code (IaC) project for Microsoft Azure, AWS, GCP and Open Source Kubernetes. Refer to SAS Viya Documentation for OpenShift."
SIZINGS_INFO = "** Also refer to SAS Viya Documentation for Sizing Recommendations for Microsoft Azure, AWS, GCP, Open Source Kubernetes and OpenShift."

# command line return codes #
SUCCESS_RC_ = 0
BAD_OPT_RC_ = 1
BAD_ENV_RC_ = 2
BAD_CONFIG_RC_ = 3
BAD_CONFIG_JSON_RC_ = 4
CONNECTION_ERROR_RC_ = 5
NAMESPACE_NOT_FOUND_RC_ = 6
RUNTIME_ERROR_RC_ = 7
SET_LIMTS_ERROR_RC_ = 8
INVALID_K8S_VERSION_RC_ = 9
