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

from subprocess import CalledProcessError
import os
import pprint
from typing import List, Dict

from pre_install_report.library.utils import viya_constants
from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface, KubernetesAvailableResourceTypes
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
from viya_ark_library.logging import ViyaARKLogger


class PreCheckUtils(object):
    """
    A PreCheckUtils encapslates the functions that use KubectlInterface to retrive information
    from a cluster

    """
    def __init__(self, params):
        """
                Constructor for PrecheckUtils object.
        """
        self.data = None
        self._kubectl: KubectlInterface = params.get(viya_constants.KUBECTL)
        self.sas_logger: ViyaARKLogger = params.get("logger")
        self.logger = self.sas_logger.get_logger()
        self.logger.info("PreCheckUtils ")

    def deploy_manifest_file(self, action, file_name):
        """
        Apply/delete specified manifest in a namespace and return the return code.
        action: indicate apply or delete of file
        file_name: yaml file to apply/delete with kubectl
        return:  kubectl rc
        """
        rc = 0
        data = ''
        file_path = self._get_filepath(file_name)
        try:
            data = self._kubectl.manage_resource(action, file_path, False)
        except CalledProcessError as cpe:
            rc = cpe.returncode
            self.logger.error("deploy_manifest_file rc {} action {} filepath {} error_msg {} error_out {}"
                              .format(str(rc), str(action), str(file_path), str(cpe.stderr), str(cpe.stdout)))
            return 1

        self.logger.info("deploy_manifest_file rc {} action {} filepath {} data{}".format(str(rc), action,
                         file_path, str(data)))
        return rc

    def do_cmd(self, test_cmd):
        """
        Run the specified kubectl command and return the output.

        cmd: kubectl command to be executed
        return:  kubectl rc
        """
        try:
            data = self._kubectl.do(test_cmd, False)

            self.logger.info("cmd {} rc = 0".format(test_cmd))
            self.logger.debug("cmd {} rc = 0 response {}".format(test_cmd, str(data)))
            return 0, str(data)
        except CalledProcessError as e:
            data = e.output
            self.logger.error("do_cmd " + ' rc = ' + str(e.returncode) + test_cmd +
                              ' data = ' + str(data))
            return e.returncode, str(data)

    def get_rbac_group_cmd(self):
        """
        Check if for Role and Rolebinding api groups.

        cmd: kubectl command to retrieve api_resources
        return:  True if both Role and RoleBinding kinds have an api_group
        """
        role: bool = None
        rolebinding: bool = None
        try:
            data: KubernetesAvailableResourceTypes = self._kubectl.api_resources(False)
            role = data.get_api_group("Role")
            rolebinding = data.get_api_group("RoleBinding")
        except CalledProcessError as e:
            self.logger.exception("get_rbac_group_cmd  rc {} ".format(str(e.returncode)))
            return False
        if role is None:
            return False
        if rolebinding is None:
            return False

        self.logger.info("found Role and RoleBinding api groups")

        return True

    def can_i(self, test_cmd):
        """
        Run the specified can-i command in designated namespace
        cmd: kubectl can-icommand to be executed
        return:  True if action is permitted. If not, return false
        """
        try:
            allowed = self._kubectl.can_i(test_cmd, False, False)
            self.logger.info('can -i ' + str(allowed) + "  can-i " + test_cmd)
            return allowed
        except CalledProcessError as cpe:
            self.logger.info('can -i return False' + "  can-i " + 'return code = ' +
                             cpe.returncode + " " + test_cmd)
            return False

    def get_resources(self, resource_kind):
        """
         Retrieve specific kubernetes resource kind

         return k8s_resource: List of Kubernetes resources
         """
        k8s_resources = []
        return_code = 0
        try:
            k8s_resources: List[KubernetesResource] = self._kubectl.get_resources(resource_kind, False)
            # my_list = []
            # for node in k8s_resources:
            #    my_list.append(node.as_dict())
            # pprint.pprint(my_list)

        except CalledProcessError as cpe:
            return_code = str(cpe.returncode)
            self.logger.exception("resource kind {} return code {}".format(str(resource_kind), str(return_code)))
            return k8s_resources

        self.logger.debug(" KubernetesResources {}".format(str(resource_kind)))
        return k8s_resources

    def get_resource(self, resource_kind, resource_name):
        """
        Retrieve specific kubernetes resource by name in json format

        k8s_resource: Kubernetes resource information to retrieve
        return: information as raw json
        """
        k8s_resource = None
        return_code = 0
        try:

            k8s_resource = self._kubectl.get_resource(resource_kind, resource_name, False)
        except CalledProcessError as cpe:
            return_code = str(cpe.returncode)
            self.logger.exception("resource {} {} return code {}".format(str(resource_kind),
                                                                         str(resource_name), str(return_code)))
            return k8s_resource

        self.logger.debug("resource {} {} KubernetesResource {}".format(str(resource_kind),
                                                                        str(resource_name),
                                                                        pprint.pformat(k8s_resource.as_dict())))
        return k8s_resource

    def get_k8s_version(self):
        """
        Retrieve the kubectl version details
        return:  Dict Object or raise cpe
        """

        try:
            versions: Dict = self._kubectl.version()
            return versions
        except CalledProcessError as cpe:
            self.logger.info('kubectl version failed ' + " version " + 'return code = ' +
                             cpe.returncode)
            raise cpe

    def _get_filepath(self, file_name):
        """
        Assemble and return path for specied file in project library

        file_name: name of file in project library/utils
        return:  relative path to specified file.
        """
        current_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(current_dir, "utils" + os.sep + file_name)

        return file_path
