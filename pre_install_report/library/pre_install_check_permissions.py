#!/usr/bin/env python3
####################################################################
# ### pre_install_check permissions.py                           ###
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
from subprocess import CalledProcessError
from typing import List, Dict

import requests
import sys
import pprint
import semantic_version
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from pre_install_report.library.utils import viya_constants, viya_messages
from pre_install_report.library.pre_install_utils import PreCheckUtils
from viya_ark_library.logging import ViyaARKLogger
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource

PVC_AZURE_FILE = "pvc_azure_file.yaml"
PVC_AZURE_FILE_PREMIUM = "pvc_azure_file_premium.yaml"
PVC_AZURE_MANAGED_PREMIUM = "pvc_azure_managed_premium.yaml"
PVC_AZURE_STANDARD_DISK = "pvc_azure_standard_disk.yaml"

PVC_AZURE_FILE_NAME = "pvc-azurefile"
PVC_AZURE_FILE_PREMIUM_NAME = "pvc-azurefile-premium"
PVC_AZURE_MANAGED_PREMIUM_NAME = "pvc-azure-managed-premium"
PVC_AZURE_STANDARD_DISK_NAME = "pvc-azure-standard-disk"

PVC_AWS_EBS = "pvc_aws_ebs.yaml"
PVC_AWS_EBS_NAME = "pvc-aws-ebs"

SC_TYPE_STANDARD_LRS = "Standard_LRS"
SC_TYPE_PREMIUM_LRS = "Premium_LRS"
SC_TYPE_STANDARD_DISK_LRS = "StandardSSD_LRS"
SC_TYPE_AWS_EBS = "gp2"
PROVISIONER_AZURE_FILE = "kubernetes.io/azure-file"
PROVISIONER_AZURE_DISK = "kubernetes.io/azure-disk"
PROVISIONER_AWS_EBS = "kubernetes.io/aws-ebs"

INGRESS_REL = '<1.19'


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
        self._ingress_file = "hello-ingress.yaml"
        self._storage_class_sc: List[KubernetesResource] = None
        self._sample_deployment = 0
        self._sample_output = ""
        self._k8s_gitVersion = None

    def _set_results_cluster_admin(self, resource_key, rc):
        """
        Set permissions status for specified resource/verb with cluster admin role

        """
        if rc == 1:
            self.cluster_admin_permission_data[resource_key] = viya_constants.INSUFFICIENT_PERMS
            self.cluster_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = \
                viya_constants.INSUFFICIENT_PERMS + ". Check Logs."

        else:
            self.cluster_admin_permission_data[resource_key] = viya_constants.ADEQUATE_PERMS

    def _set_results_namespace_admin(self, resource_key, rc, message=""):
        """
        Set permissions status for specified resource/verb with namespace admin role

        """
        sample_keys = [viya_constants.PERM_DEPLOYMENT]
        deployment_keys = [viya_constants.PERM_DELETE + viya_constants.PERM_DEPLOYMENT,
                           viya_constants.PERM_SERVICE,
                           viya_constants.PERM_DELETE + viya_constants.PERM_SERVICE,
                           viya_constants.PERM_INGRESS,
                           viya_constants.PERM_DELETE + viya_constants.PERM_INGRESS,
                           viya_constants.PERM_REPLICASET,
                           viya_constants.PERM_CREATE + viya_constants.PERM_ROLE,
                           viya_constants.PERM_CREATE + viya_constants.PERM_ROLEBINDING,
                           viya_constants.PERM_CREATE + viya_constants.PERM_SA,
                           viya_constants.PERM_DELETE + viya_constants.PERM_ROLE,
                           viya_constants.PERM_DELETE + viya_constants.PERM_ROLEBINDING,
                           viya_constants.PERM_DELETE + viya_constants.PERM_SA
                           ]
        if rc != 0:
            self.logger.debug("resource_key = {}, sample_deployment = {} ".format(str(resource_key),
                                                                                  str(self._sample_deployment)))
            if self._sample_deployment != 0:
                if resource_key in deployment_keys:
                    self.namespace_admin_permission_data[resource_key] = viya_constants.INSUFFICIENT_PERMS
                if resource_key in sample_keys:
                    self.namespace_admin_permission_data[resource_key] = viya_constants.INSUFFICIENT_PERMS + \
                                                                         ". Sample Deployment Check failed! " + \
                                                                         "Ensure Node(s) Status is Ready. " + \
                                                                         "Check Permissions in specified namespace. " \
                                                                         + self._sample_output

            else:
                self.namespace_admin_permission_data[resource_key] = viya_constants.INSUFFICIENT_PERMS + " " + message
            self.namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = \
                viya_constants.INSUFFICIENT_PERMS + ". Check Logs."
        else:
            self.namespace_admin_permission_data[resource_key] = viya_constants.ADEQUATE_PERMS
            # self.namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = \
            #    viya_constants.ADEQUATE_PERMS

    def _get_pvc(self, pvc_name, key):
        """
        Get the pvc resource from the Kubernetes using kubectl, if it is deployed successfully

        return KubenestesResource object
        """
        k8s_resource: KubernetesResource = self.utils.get_resource("pvc", pvc_name)
        if k8s_resource is not None:
            self.logger.debug("k8s_resource is NOT None pvc")
            self.check_pvc_phase(k8s_resource, pvc_name, key)
        else:
            self.logger.debug("k8s_resource IS None pvc")
            self._set_results_namespace_admin(key, 1)

    def check_pvc_phase(self, pvc_file, pvc_name, key):
        """
        Get status of deployed pvc yaml

        action:  issue kubectl command to get status Bound / Pending / error

        """
        if pvc_file:
            self.logger.info("pvc_file {}".format(pprint.pformat(pvc_file.as_dict())))
            if (pvc_file.get_status_value("phase") == "Bound"):
                self._set_results_namespace_admin(key, 0)
                self.logger.info("{} status {}".format(pvc_name, pvc_file.get_status_value("phase")))
            else:
                self._set_results_namespace_admin(key, 1, " - Persistent Volume Claim not Bound. Check Logs.")
                self.logger.info("{} status {}".format(pvc_name, pvc_file.get_status_value("phase")))
                self.utils.do_cmd(" describe pvc " + pvc_name)
        else:
            self._set_results_namespace_admin(key, 1)

    def _replace_sc_name_infile(self, template_file, sc_name, outfile):
        self.logger.debug(" sc name for substitution {} ".format(sc_name))
        try:
            os.remove(self.utils._get_filepath(outfile))
        except OSError as err:
            self.logger.error("Unable to delete file: {}".format(err))
            pass
        try:
            with open(self.utils._get_filepath(template_file), 'r') as infile, \
                    open(self.utils._get_filepath(outfile), 'w') as outfile:
                content = infile.read()
                infile.seek(0)
                outfile.write(content.replace('$sc_name$', sc_name))
                outfile.close()
        except IOError as err:
            self.logger.error("IOError templatefile {} outfile {} error {} ".format(template_file, outfile, str(err)))
            pass

    def _delete_pvc_yaml_file(self, outfile):

        try:
            os.remove(self.utils._get_filepath(outfile))
        except OSError as err:
            self.logger.error("Unable to delete file: {}".format(err))
            pass

    def _manage_specific_pvc_type(self, action, check, pvc_template_file, sc_name, pvc_yaml_file, pvc_name, key):
        self.logger.debug("action {} check {} pvc_template_file {} sc_name {} pvc_yaml_file {} pvc_name {} key {}".
                          format(str(action), str(check), str(pvc_template_file), str(sc_name), str(pvc_yaml_file),
                                 str(pvc_name), str(key)))
        if check:
            if action == viya_constants.KUBECTL_APPLY and check:
                self._get_pvc(pvc_name, key)
        else:
            if action == viya_constants.KUBECTL_APPLY:
                self._replace_sc_name_infile(pvc_template_file, sc_name, pvc_yaml_file)
                self.utils.deploy_manifest_file(action, pvc_yaml_file)
            if action == viya_constants.KUBECTL_DELETE:
                rc1 = self.utils.deploy_manifest_file(action, pvc_yaml_file)
                self._set_results_namespace_admin(viya_constants.PERM_DELETE + key, rc1)
                self._delete_pvc_yaml_file(pvc_yaml_file)

    def manage_pvc(self, action, check):
        """
        Apply or delete the pvc

        action:  Apply or Delete pvc and set the report status

        """
        storage_class_names = self.get_storage_classes_details()
        if len(storage_class_names) > 0:
            for value in storage_class_names:
                # check for 'kubernetes.io/azure-file', 'azurefile-disk'
                self.logger.info("Storage class: {}".format(value))
                if value[1] == PVC_AZURE_FILE:
                    self._manage_specific_pvc_type(action, check, "pvc_azure_file.template", value[0],
                                                   PVC_AZURE_FILE, PVC_AZURE_FILE_NAME, viya_constants.PERM_AZ_FILE)
                elif value[1] == PVC_AZURE_FILE_PREMIUM:
                    self._manage_specific_pvc_type(action, check, "pvc_azure_file_premium.template", value[0],
                                                   PVC_AZURE_FILE_PREMIUM, PVC_AZURE_FILE_PREMIUM_NAME,
                                                   viya_constants.PERM_AZ_FILE_PR)
                elif value[1] == PVC_AZURE_MANAGED_PREMIUM:
                    self._manage_specific_pvc_type(action, check, "pvc_azure_managed_premium.template", value[0],
                                                   PVC_AZURE_MANAGED_PREMIUM, PVC_AZURE_MANAGED_PREMIUM_NAME,
                                                   viya_constants.PERM_AZ_DISK)
                elif value[1] == PVC_AZURE_STANDARD_DISK:
                    self._manage_specific_pvc_type(action, check, "pvc_azure_standard_disk.template", value[0],
                                                   PVC_AZURE_STANDARD_DISK, PVC_AZURE_STANDARD_DISK_NAME,
                                                   viya_constants.PERM_AZ_DISK_STANDARD)

                elif value[1] == PVC_AWS_EBS:
                    self._manage_specific_pvc_type(action, check, "pvc_aws_ebs.template", value[0],
                                                   PVC_AWS_EBS, PVC_AWS_EBS_NAME,
                                                   viya_constants.PERM_AWS_EBS)
                else:
                    self.logger.debug("Storage class not attempted {}".format(value))
        else:
            self._skip_pvc_check()

        self.logger.debug("Namespaced results {}".format(pprint.pformat(self.namespace_admin_permission_data)))

    def _skip_pvc_check(self):
        self.namespace_admin_permission_data[viya_constants.PERM_AZ_FILE] = viya_constants.PERM_SKIPPING
        self.namespace_admin_permission_data[viya_constants.PERM_AZ_FILE_PR] = viya_constants.PERM_SKIPPING
        self.namespace_admin_permission_data[viya_constants.PERM_AZ_DISK] = viya_constants.PERM_SKIPPING
        self.namespace_admin_permission_data[viya_constants.PERM_AZ_DISK_STANDARD] = viya_constants.PERM_SKIPPING
        self.namespace_admin_permission_data[viya_constants.PERM_AWS_EBS] = viya_constants.PERM_SKIPPING
        self.namespace_admin_permission_data[viya_constants.PERM_DELETE + viya_constants.PERM_AZ_FILE]\
            = viya_constants.PERM_SKIPPING
        self.namespace_admin_permission_data[viya_constants.PERM_DELETE + viya_constants.PERM_AZ_FILE_PR] \
            = viya_constants.PERM_SKIPPING
        self.namespace_admin_permission_data[viya_constants.PERM_DELETE + viya_constants.PERM_AZ_DISK] \
            = viya_constants.PERM_SKIPPING
        self.namespace_admin_permission_data[viya_constants.PERM_DELETE + viya_constants.PERM_AZ_DISK_STANDARD] \
            = viya_constants.PERM_SKIPPING
        self.namespace_admin_permission_data[viya_constants.PERM_DELETE + viya_constants.PERM_AWS_EBS] \
            = viya_constants.PERM_SKIPPING

    def get_sc_resources(self):
        """
         Uses viyaARK_library common library to retrieve kubernetes resources kind=storage class
         return k8s_resource: List of Kubernetes resources
        """
        self._storage_class_sc = self.utils.get_resources(KubernetesResource.Kinds.STORAGECLASS)
        if not self._storage_class_sc:
            self.cluster_admin_permission_data[viya_constants.PERM_GET + viya_constants.PERM_STORAGE_CLASS] = \
                viya_constants.INSUFFICIENT_PERMS
            self.cluster_admin_permission_aggregate[viya_constants.PERM_GET + viya_constants.PERM_STORAGE_CLASS] = \
                viya_constants.INSUFFICIENT_PERMS
        else:
            self.cluster_admin_permission_data[viya_constants.PERM_GET + viya_constants.PERM_STORAGE_CLASS] = \
                viya_constants.ADEQUATE_PERMS
        return

    def get_storage_classes_details(self):
        """

        """
        k8s_resources = self._storage_class_sc

        storage_classes = []
        if self._storage_class_sc is None:
            return storage_classes
        for k8s_resource in k8s_resources:
            self.logger.debug("As Dict {}".format(pprint.pformat(k8s_resource.as_dict())))
            self.logger.debug("name {} provisioner{} storageaccounttype {} type {} selfLink {} skuName {}".
                              format(str(k8s_resource.get_name()),
                                     str(k8s_resource.get_provisioner()),
                                     str(k8s_resource.get_parameter_value('storageaccounttype')),
                                     str(k8s_resource.get_parameter_value('type')),
                                     str(k8s_resource.get_self_link()),
                                     str(k8s_resource.get_parameter_value('skuName'))))
            # print("selfLink" + str(k8s_resource.get_self_link()))
            # if ("/storageclasses/managed-premium" in str(k8s_resource.get_self_link())):
            #    print("True //storageclasses//managed-premium")
            # if ("/storageclasses/azurefile" in str(k8s_resource.get_self_link())):
            #    print("True storageclasses//managed-premium ")
            # print("get self link : " + str(k8s_resource.get_self_link()))
            if (str(k8s_resource.get_provisioner()) == PROVISIONER_AZURE_FILE):

                if str(k8s_resource.get_parameter_value('skuName')) == SC_TYPE_STANDARD_LRS:
                    storage_classes.append((str(k8s_resource.get_name()),
                                            PVC_AZURE_FILE,
                                            str(k8s_resource.get_provisioner()),
                                            str(k8s_resource.get_parameter_value('skuName'))))
                elif str(k8s_resource.get_parameter_value('skuName')) == SC_TYPE_PREMIUM_LRS:
                    storage_classes.append((str(k8s_resource.get_name()),
                                            PVC_AZURE_FILE_PREMIUM,
                                            str(k8s_resource.get_provisioner()),
                                            str(k8s_resource.get_parameter_value('skuName'))))

            if str(k8s_resource.get_provisioner()) == PROVISIONER_AZURE_DISK:
                if str(k8s_resource.get_parameter_value('storageaccounttype')) == SC_TYPE_PREMIUM_LRS:
                    storage_classes.append((str(k8s_resource.get_name()),
                                            PVC_AZURE_MANAGED_PREMIUM,
                                            str(k8s_resource.get_provisioner()),
                                            str(k8s_resource.get_parameter_value('storageaccounttype'))))
                if str(k8s_resource.get_parameter_value('storageaccounttype')) == SC_TYPE_STANDARD_DISK_LRS:
                    storage_classes.append((str(k8s_resource.get_name()),
                                            PVC_AZURE_STANDARD_DISK,
                                            str(k8s_resource.get_provisioner()),
                                            str(k8s_resource.get_parameter_value('storageaccounttype'))))

            if str(k8s_resource.get_provisioner()) == PROVISIONER_AWS_EBS and \
                    ("/storageclasses/gp2" in str(k8s_resource.get_self_link())) and \
                    str(k8s_resource.get_parameter_value('type')) == SC_TYPE_AWS_EBS:
                storage_classes.append((str(k8s_resource.get_name()),
                                        PVC_AWS_EBS,
                                        str(k8s_resource.get_provisioner()),
                                        str(k8s_resource.get_parameter_value('type'))))
        self.logger.debug("Provisioner {} ".format(pprint.pformat(storage_classes)))
        return storage_classes

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

        if rc == 0:
            rc, sample_output = self.utils.do_cmd(" rollout status deployment.v1.apps/hello-world --timeout=180s")
            # You can check if a Deployment has completed by using kubectl rollout status.
            # If the rollout completed successfully, kubectl rollout status returns a zero exit code.

            if rc != 0:
                self._sample_deployment = 2
                self._sample_output = sample_output
                self._set_results_namespace_admin(viya_constants.PERM_DEPLOYMENT, rc)
                self._set_results_namespace_admin(viya_constants.PERM_SERVICE, rc)
                return 2

            self._set_results_namespace_admin(viya_constants.PERM_DEPLOYMENT, rc)
            self._set_results_namespace_admin(viya_constants.PERM_SERVICE, rc)

            if rc == 0:
                rc, sample_output = self.utils.do_cmd(" scale --replicas=2 deployment/hello-world ")
                if rc != 0:
                    self._sample_deployment = 3
                self._set_results_namespace_admin(viya_constants.PERM_REPLICASET, rc)
                return 3
        else:
            self._sample_deployment = 1
            self._set_results_namespace_admin(viya_constants.PERM_DEPLOYMENT, rc)
            self._set_results_namespace_admin(viya_constants.PERM_SERVICE, rc)

            return 1

    def check_sample_service(self):
        """
        Deploy Kubernetes Service for hello-world appliction in specified namespace and set the
        permissions status in the namespace_admin_permission_data dict object
        """

        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             'helloworld-svc.yaml')
        self._set_results_namespace_admin(viya_constants.PERM_SERVICE, rc)

    def get_server_gitVersion(self):
        """
        Retrieve the Kubernetes servervrsion and validate the gitVersion
        """
        try:
            versions: Dict = self.utils.get_k8s_version()
            serverversion = versions.get('serverVersion')
            gitVersion = serverversion.get('gitVersion')
            self.logger.info("gitversion {} ".format(str(gitVersion)))

            if gitVersion.startswith("v"):
                gitVersion = gitVersion[1:]
            self.set_k8s_gitVersion(gitVersion)
        except CalledProcessError as cpe:
            self.logger.exception('kubectl version command failed. Return code = {}'.format(str(cpe.returncode)))
            sys.exit(viya_messages.RUNTIME_ERROR_RC_)

    def set_ingress_manifest_file(self):
        """
        Retrieve the server Kubernetes gitVersion using and compare it using
        https://pypi.org/project/semantic_version/  2.8.5 initial version
        """
        try:
            curr_version = semantic_version.Version(str(self.get_k8s_gitVersion()))

            if(curr_version in semantic_version.SimpleSpec(INGRESS_REL)):
                self._ingress_file = "hello-ingress-k8s-v118.yaml"
                self.logger.debug("hello-ingress file deployed {} major {} minor {}"
                                  .format(str(self._ingress_file), str(curr_version.major),
                                          str(curr_version.minor)))
        except ValueError as cpe:
            self.logger.exception(viya_messages.EXCEPTION_MESSAGE.format(str(cpe)))
            sys.exit(viya_messages.RUNTIME_ERROR_RC_)

    def check_sample_ingress(self):
        """
        Deploy Kubernetes Ingress for hello-world appliction in the specified
        namespace and set the permissions status in the namespace_admin_permission_data dict object.
        If nginx is ingress controller check Ingress deployment (default)
        """
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             self._ingress_file)
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
        self._set_results_namespace_admin(viya_constants.PERM_DELETE + viya_constants.PERM_SERVICE, rc)

        self.utils.do_cmd(" wait --for=delete pod -l app=hello-world-pod --timeout=12s ")

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
                                             self._ingress_file)
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
        Create the Role and Rolebinding for the custom resource access with specified namespace. Set the
        permissions status in the namespace_admin_permission_data dict object.

        """
        found = self.utils.get_rbac_group_cmd()
        self.logger.debug("get_rbace_group_cmd found = {}, sample_deployment = {}"
                          .format(str(found), str(self._sample_deployment)))
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
            self.logger.debug("sample_deployment = {}".format(str(self._sample_deployment)))
            self.namespace_admin_permission_aggregate["RBAC Checking"] = viya_constants.PERM_SKIPPING
            self._set_results_namespace_admin(viya_constants.PERM_CREATE + viya_constants.PERM_ROLE,
                                              int(self._sample_deployment))
            self._set_results_namespace_admin(viya_constants.PERM_CREATE + viya_constants.PERM_SA,
                                              int(self._sample_deployment))
            self._set_results_namespace_admin(viya_constants.PERM_CREATE + viya_constants.PERM_ROLEBINDING,
                                              int(self._sample_deployment))

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

        self._set_results_namespace_admin_crd(viya_constants.PERM_CREATE + viya_constants.PERM_CR_RBAC
                                              + viya_constants.PERM_SA, rc1)
        allowed: bool = self.utils.can_i(' delete viyas.company.com --as=system:serviceaccount:'
                                         + namespace + ':crreader ')
        if allowed:
            rc2 = 1
        self._set_results_namespace_admin_crd(viya_constants.PERM_DELETE + viya_constants.PERM_CR_RBAC
                                              + viya_constants.PERM_SA, rc2)

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

    def set_k8s_gitVersion(self, version: str):
        """
        Set the current Kubernetes Server Version
        """
        self._k8s_gitVersion = version

    def get_k8s_gitVersion(self):
        """
        Get the current Kubernetes Server Version
        return: string object
        """
        return self._k8s_gitVersion

    def get_ingress_file_name(self):
        """
        Get the ingress manifest to be deployed
        return: string object
        """
        return self._ingress_file
