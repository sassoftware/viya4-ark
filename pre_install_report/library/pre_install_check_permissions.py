#!/usr/bin/env python3
####################################################################
# ### pre_install_check permissions.py                           ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021-2023, SAS Institute Inc., Cary, NC, USA.    ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import os
from typing import List

import pprint
from pre_install_report.library.utils import viya_constants
from pre_install_report.library.pre_install_utils import PreCheckUtils
from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues
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
        self.utils: PreCheckUtils = params.get(viya_constants.PERM_CLASS)
        self.sas_logger: ViyaARKLogger = params.get("logger")
        self.logger = self.sas_logger.get_logger()

        self.namespace_admin_permission_data = {}
        self.cluster_admin_permission_data = {}
        self.namespace_admin_permission_aggregate = {}
        self.cluster_admin_permission_aggregate = {}
        self.namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = viya_constants.ADEQUATE_PERMS
        self.cluster_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = viya_constants.ADEQUATE_PERMS

        self._storage_class_sc: List[KubernetesResource] = None
        self._k8s_git_version = params.get(viya_constants.SERVER_K8S_VERSION)

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
        if rc != 0:
            self.namespace_admin_permission_data[resource_key] = viya_constants.INSUFFICIENT_PERMS + " " + message
            self.namespace_admin_permission_aggregate[viya_constants.PERM_PERMISSIONS] = \
                viya_constants.INSUFFICIENT_PERMS + ". Check Logs."
        else:
            self.namespace_admin_permission_data[resource_key] = viya_constants.ADEQUATE_PERMS

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
        self._storage_class_sc = self.utils.get_resources(KubernetesResourceTypeValues.K8S_STORAGE_STORAGE_CLASSES)
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

    def check_create_custom_resource(self):
        """
        Create the  custome resource in specified namespace. Set the
        permissions status in the namespace_admin_permission_data dict object.

        """
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             'crviya.yaml')
        self._set_results_namespace_admin_crd(viya_constants.PERM_CREATE + viya_constants.PERM_CR, rc)

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
        Check if RBAC is enabled in specified namespace.
        Create the Role, Rolebinding, and Service account in the specified namespace. Set the
        permissions status in the namespace_admin_permission_data dict object.

        """
        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             'viya-role.yaml')

        self._set_results_cluster_admin(viya_constants.PERM_CREATE + viya_constants.PERM_ROLE, rc)

        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             'crservice_acct.yaml')
        self._set_results_namespace_admin(viya_constants.PERM_CREATE + viya_constants.PERM_SA, rc)

        rc = self.utils.deploy_manifest_file(viya_constants.KUBECTL_APPLY,
                                             'viya-rolebinding.yaml')
        self._set_results_namespace_admin(viya_constants.PERM_CREATE + viya_constants.PERM_ROLEBINDING, rc)

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

    def set_k8s_git_version(self, version: str):
        """
        Set the current Kubernetes Server Version
        """
        self._k8s_git_version = version

    def get_k8s_git_version(self):
        """
        Get the current Kubernetes Server Version
        return: string object
        """
        return self._k8s_git_version
