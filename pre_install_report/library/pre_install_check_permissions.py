#!/usr/bin/env python3
####################################################################
# ### pre_install_check permissions.py                           ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pre_install_report.library.utils import viya_constants
from pre_install_report.library.pre_install_utils import PreCheckUtils
from viya_ark_library.logging import ViyaARKLogger


class PreCheckPermissions(object):
    """
    A PreCheckPermissions encapslates the functions and data gathered from permissions testing in a designated namespace
    with an admin or nonadmin role.

    The gathered data can be wwritten to an HTML report.
    """
    def __init__(self, params):
        """
                Constructor for PrecheckPermissions object.
        """

        # the constructor initializes the following variables in the constructor #
        # variables are not used outside of the constructor                      #
        self.ingress_controller = params.get(viya_constants.INGRESS_CONTROLLER)
        self.ingress_host = params.get(viya_constants.INGRESS_HOST)
        self.ingress_port = params.get(viya_constants.INGRESS_PORT)
        self.utils: PreCheckUtils = params.get(viya_constants.PERM_CLASS)
        self.sas_logger: ViyaARKLogger = params.get("logger")
        self.logger = self.sas_logger.get_logger()

        self.namespace_admin_permission_data = {}
        self.cluster_admin_permission_data = {}
        self.namespace_admin_permission_aggregate = {}
        self.cluster_admin_permission_aggregate = {}
        self.namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = viya_constants.ADEQUATE_PERMS
        self.cluster_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = viya_constants.ADEQUATE_PERMS
        self.ingress_data = {}
        self.ingress_data[viya_constants.INGRESS_CONTROLLER] = self.ingress_controller
        self.ingress_file = "hello-ingress.yaml"
        if self.ingress_controller == viya_constants.INGRESS_ISTIO:
            self.ingress_file = "helloworld-gateway.yaml"

    def _set_results_cluster_admin(self, resource_key, rc):
        """
        Set permissions status for specified resource/verb with cluster admin role

        """
        if rc == 1:
            self.cluster_admin_permission_data[resource_key] = viya_constants.INSUFFICIENT_PERMS
            self.cluster_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = viya_constants.INSUFFICIENT_PERMS
        else:
            self.cluster_admin_permission_data[resource_key] = viya_constants.ADEQUATE_PERMS

    def _set_results_namespace_admin(self, resource_key, rc):
        """
        Set permissions status for specified resource/verb with namespace admin role

        """
        if rc == 1:
            self.namespace_admin_permission_data[resource_key] = viya_constants.INSUFFICIENT_PERMS
            self.namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] \
                = viya_constants.INSUFFICIENT_PERMS
        else:
            self.namespace_admin_permission_data[resource_key] = viya_constants.ADEQUATE_PERMS

    def _set_results_namespace_admin_crd(self, resource_key, rc):
        """
        Set permissions status creation of CRD as namespace admin role

        """
        if self.cluster_admin_permission_data[viya_constants.PERM_CREATE + viya_constants.PERM_CRD] \
                == viya_constants.INSUFFICIENT_PERMS:
            self.namespace_admin_permission_data[resource_key] = viya_constants.PERM_SKIPPING
            return rc
        if rc == 1:
            self.namespace_admin_permission_data[resource_key] = viya_constants.INSUFFICIENT_PERMS
            self.namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] \
                = viya_constants.INSUFFICIENT_PERMS
        else:
            self.namespace_admin_permission_data[resource_key] = viya_constants.ADEQUATE_PERMS

    def check_sample_application(self):
        """
        Deploy hello-world in specified namespace and set the permissiions status in the

        """

        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             'hello-application.yaml')
        #    self._set_results_namespace_admin(viya_constants.PERM_DEPLOYMENT, rc)
        #    self._set_results_namespace_admin(viya_constants.PERM_SERVICE, rc)

        if rc == 0:
            rc = self.utils.do_cmd(" rollout status deployment.v1.apps/hello-world ")

            self._set_results_namespace_admin(viya_constants.PERM_DEPLOYMENT, rc)
            self._set_results_namespace_admin(viya_constants.PERM_SERVICE, rc)

            if rc == 0:
                rc = self.utils.do_cmd(" scale --replicas=2 deployment/hello-world ")

                if rc == 0:
                    self._set_results_namespace_admin(viya_constants.PERM_REPLICASET, rc)

    def check_sample_service(self):
        """
        Deploy Kubernetes Service for hello-world appliction in specified namespace and set the
        permissions status in the namespace_admin_permission_data dict object


        """

        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             'helloworld-svc.yaml')
        self._set_results_namespace_admin(viya_constants.PERM_SERVICE, rc)

    def check_sample_ingress(self):
        """
        Deploy Kubernetes Ingress or Gateway and Virtual Service for hello-world appliction in specified
        namespace and set the permissions status in the namespace_admin_permission_data dict object.
        If nginx is ingress controller check Ingress deployment. If istio  is ingress controller check Gateway
        and Virtual Service deployment

        """
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             self.ingress_file)
        self._set_results_namespace_admin(viya_constants.PERM_INGRESS, rc)

    def check_sample_response(self):
        """
        Test Assemble URL to access hello-world appliction with user supplied host and port. If the response indicates
        failure retest with ooption to diable verification.
        """

        port = ""
        response = ""
        if self.ingress_port is not None:
            port = ":" + self.ingress_port
        host_port_app = str(self.ingress_host) + str(port) + "/hello-world"
        url_string = "http://" + host_port_app
        self.logger.info("url {}".format(url_string))
        response = self._request_url(url_string, True)
        if response is not None:
            response.encoding = 'utf-8'
            if response.status_code == 200:
                self.namespace_admin_permission_data[viya_constants.PERM_SAMPLE_STATUS] = str(response.status_code) + \
                                                                        "  " + str(response.text)
                self.logger.info("url {} response status code {}".format(url_string, str(response.status_code)))
            else:
                # attempt the request again with https and verify=False option, suppress InsecureRequestWarning
                url_string = "https://" + host_port_app
                response = self._request_url(url_string, False)
                if response is not None:
                    response.encoding = 'utf-8'
                    if response.status_code == 200:
                        self.namespace_admin_permission_data[viya_constants.PERM_SAMPLE_STATUS] = \
                            str(response.status_code) + "  " + str(response.text)
                        self.logger.info("url {} response status code {}".format(url_string, str(response.status_code)))
                    else:
                        self.namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = \
                            viya_constants.INSUFFICIENT_PERMS

                        self.namespace_admin_permission_data['Sample HTTP Failed'] = "Status Code " + \
                                                                                     str(response.status_code) + \
                                                                                     ": " + str(url_string)
                        self.logger.info("url {} status {} text {}".format(url_string,
                                                                           response.status_code, response.text))
                else:
                    self.logger.error("Retry as https failed url {}".format(url_string))

    def _request_url(self, url_string, verify_cert=True):
        """
        test the assembled URL to access hello-world appliction. Test url and record the response
        in the namespace_admin_permission_data dict object. Suppresses InsecureRequestWarning if
        https attempted.
        """
        try:
            if verify_cert is True:
                response = requests.get(url_string)
            else:
                requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
                response = requests.get(url_string, verify=False)
                self.logger.debug("_request_url() Retry. {} {}.".format("VerifySSL = False", url_string))
        except requests.exceptions.RequestException as rexp:
            self.namespace_admin_permission_data['Sample requests Error occured'] = \
                str(rexp)
            self.namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = \
                viya_constants.INSUFFICIENT_PERMS
            self.logger.error("url {}  error{}".format(url_string, str(rexp)))
            return None

        return response

    def check_delete_sample_application(self):
        """
        Delete hello-world application in specified namespace. Set the
        permissions status in the namespace_admin_permission_data dict object.
        Wait for pods to be deleted.
        """
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_DELETE,
                                             'hello-application.yaml')
        self._set_results_namespace_admin(viya_constants.PERM_DELETE + viya_constants.PERM_DEPLOYMENT, rc)

        rc = self.utils.do_cmd(" wait --for=delete pod -l app=hello-world-pod --timeout=12s ")

    def check_delete_sample_service(self):
        """
        Delete hello-world Kubernetes Service in specified namespace. Set the
        permissions status in the namespace_admin_permission_data dict object.

        """
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_DELETE,
                                             'helloworld-svc.yaml')
        self._set_results_namespace_admin(viya_constants.PERM_DELETE + viya_constants.PERM_SERVICE, rc)

    def check_delete_sample_ingress(self):
        """
        Delete Kubernetes Ingress/Gateway in specified namespace. Set the
        permissions status in the namespace_admin_permission_data dict object.

        """
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_DELETE,
                                             self.ingress_file)
        self._set_results_namespace_admin(viya_constants.PERM_DELETE + viya_constants.PERM_INGRESS, rc)

    def check_create_custom_resource(self):
        """
        Create the  custome resource in specified namespace. Set the
        permissions status in the namespace_admin_permission_data dict object.

        """
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             'crviya.yaml')
        self._set_results_namespace_admin_crd(viya_constants.PERM_CREATE + viya_constants.PERM_CR, rc)

    #    TBD test_cmd = "kubectl get customresourcedefinition viyas.company.com -o name"

    def check_deploy_crd(self):
        """
            Deploy the namespaced Custom Resource definition. Set the
            permissions status in the namespace_admin_permission_data dict object.
        """
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             'crdviya.yaml')
        self._set_results_cluster_admin(viya_constants.PERM_CREATE + viya_constants.PERM_CRD, rc)

    def check_rbac_role(self):
        """
        Check if RBAC is enabled in specified namespace
        Create the Role and Rolebinding for the custome resource access with specified namespace. Set the
        permissions status in the namespace_admin_permission_data dict object.

        """
        found = self.utils.get_rbac_group_cmd()

        if found:
            rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                                 'viya-role.yaml')

            self._set_results_cluster_admin(viya_constants.PERM_CREATE + viya_constants.PERM_ROLE, rc)

            rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                                 'crservice_acct.yaml')
            self._set_results_namespace_admin(viya_constants.PERM_CREATE + viya_constants.PERM_SA, rc)

            rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                                 'viya-rolebinding.yaml')
            self._set_results_namespace_admin(viya_constants.PERM_CREATE + viya_constants.PERM_ROLEBINDING, rc)
        else:
            self.namespace_admin_permission_aggregate["RBAC Checking"] = viya_constants.PERM_SKIPPING

    def check_rbac_delete_role(self):
        """
        Delete the Kubernetes Role, Rolebinding and Service Account deployed for the custom resource access
        with specified namespace. Set the permissions status in the namespace_admin_permission_data dict object.

        """

        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_DELETE,
                                             'viya-role.yaml')
        self._set_results_namespace_admin(viya_constants.PERM_DELETE + viya_constants.PERM_ROLE, rc)
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_DELETE,
                                             'viya-rolebinding.yaml')
        self._set_results_namespace_admin(viya_constants.PERM_DELETE + viya_constants.PERM_ROLEBINDING, rc)
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_DELETE,
                                             'crservice_acct.yaml')
        self._set_results_namespace_admin(viya_constants.PERM_DELETE + viya_constants.PERM_SA, rc)

    def check_get_custom_resource(self, namespace):
        """
        Create the Role and Rolebinding for the custom resource access with specified namespace. Set the
        permissions status in the namespace_admin_permission_data dict object.

        """
        rc1 = 0
        rc2 = 0
        allowed: bool = self.utils.can_i(' create viyas.company.com --as=system:serviceaccount:'
                                         + namespace + ':crreader ')
        if not allowed:
            rc1 = 1

        self._set_results_namespace_admin_crd(viya_constants.PERM_CREATE + viya_constants.PERM_CR + " with RBAC "
                                              + viya_constants.PERM_SA + " resp: = " + str(allowed), rc1)
        allowed: bool = self.utils.can_i(' delete viyas.company.com --as=system:serviceaccount:'
                                         + namespace + ':crreader ')
        if allowed:
            rc2 = 1
        self._set_results_namespace_admin_crd(viya_constants.PERM_DELETE + viya_constants.PERM_CR + " with RBAC "
                                              + viya_constants.PERM_SA + " resp: = " + str(allowed), rc2)

    def check_delete_custom_resource(self):
        """
        Delete the Custom resource with specified namespace. Set the
        permissions status in the namespace_admin_permission_data dict object.

        """

        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_DELETE,
                                             'crviya.yaml')
        self._set_results_namespace_admin_crd(viya_constants.PERM_DELETE + viya_constants.PERM_CR, rc)
        return rc

    def check_delete_crd(self):
        """
        Delete the namespaced Custom resource definition. Set the
        permissions status in the namespace_admin_permission_data dict object.

        """
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_DELETE,
                                             'crdviya.yaml')
        self._set_results_cluster_admin(viya_constants.PERM_DELETE + viya_constants.PERM_CRD, rc)

    def get_cluster_admin_permission_data(self):
        """
        Return cluster_admin_permission_data

        return: dict object with cluster access permissions data
        """
        return self.cluster_admin_permission_data

    def get_namespace_admin_permission_data(self):
        """
        Return namespace_admin_permission_data

        return: dict object with namespace admin access permissions data
        """
        return self.namespace_admin_permission_data

    def get_ingress_data(self):
        """
        Return ingress data

        return: dict object with ingress data
        """
        return self.ingress_data

    def get_namespace_admin_permission_aggregate(self):
        """
        Return namespace_admin_permission_aggregate

        return: dict object with namespace admin aggregate permissions data
        """
        return self.namespace_admin_permission_aggregate

    def get_cluster_admin_permission_aggregate(self):
        """
        Return cluster_admin_permission_aggregate

        return: dict object with cluster admin aggregate permissions data
        """
        return self.cluster_admin_permission_aggregate
