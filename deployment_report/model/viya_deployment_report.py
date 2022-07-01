####################################################################
# ### viya_deployment_report.py                                  ###
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
import json
import os

from subprocess import CalledProcessError
from typing import AnyStr, Dict, List, Optional, Text, Tuple

from deployment_report.model.static.viya_deployment_report_keys import ITEMS_KEY, NAME_KEY
from deployment_report.model.static.viya_deployment_report_keys import ViyaDeploymentReportKeys as Keys
from deployment_report.model.utils import \
    component_util, \
    config_util, \
    ingress_util, \
    metrics_util, \
    relationship_util, \
    resource_util

from viya_ark_library.jinja2.sas_jinja2 import Jinja2TemplateRenderer
from viya_ark_library.k8s.k8s_resource_keys import KubernetesResourceKeys
from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues as ResourceTypeValues
from viya_ark_library.k8s.sas_k8s_errors import KubectlRequestForbiddenError
from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import \
    KubernetesAvailableResourceTypes, \
    KubernetesObjectJSONEncoder
from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface

# templates for string-formatted timestamp values
_READABLE_TIMESTAMP_TMPL_ = "%A, %B %d, %Y %I:%M%p"
_FILE_TIMESTAMP_TMPL_ = "%Y-%m-%dT%H_%M_%S"

# templates for output file names
_REPORT_DATA_FILE_NAME_TMPL_ = "viya_deployment_report_data_{}.json"
_REPORT_FILE_NAME_TMPL_ = "viya_deployment_report_{}.html"

# SAS custom API resource group id
_SAS_API_GROUP_ID_ = "sas.com"

# Configuration keys
_ENVFROM_ = "envFrom"
_PODS_ = "pods"
_CONFIGMAPREF_ = "configMapRef"
_SECRETREF_ = "secretRef"
_REFPC_ = "referenced_pods_containers"
_REFLINK_ = "ref"


class ViyaDeploymentReport(object):
    """
    A ViyaDeploymentReport object represents a summary of all SAS components currently deployed on the target Kubernetes
    environment.

    A cache of Kubernetes resources are stored for access via the API.

    The gathered data can be written to disk as an HTML report and a JSON file containing the gathered data.
    """

    # default values for arguments shared between the model and command #
    DATA_FILE_ONLY_DEFAULT: bool = False
    INCLUDE_POD_LOG_SNIPS_DEFAULT: bool = False
    INCLUDE_RESOURCE_DEFINITIONS_DEFAULT: bool = False
    OUTPUT_DIRECTORY_DEFAULT: Text = "./"

    def __init__(self) -> None:
        """
        Constructor for ViyaDeploymentReport object.
        """
        self._report_data = None

    def as_dict(self) -> Optional[Dict]:
        """
        Returns a dictionary representation of the data gathered by this report. All nested objects are maintained
        as-is. To parse to JSON, the KubernetesObjectJSONEncoder is needed.

        :return: A dictionary representation of the data gathered by this report with all nested objects maintained
                 as-is, or None if data has not been gathered.
        """
        return self._report_data

    def as_dict_json_encoded(self) -> Optional[Dict]:
        """
        Returns a dictionary representation of the data gathered by this report. All nested objects are encoded, using
        the KubernetesObjectJSONEncoder, to native Python objects for JSON compatibility.

        :return: A dictionary representation of the data gathered by this report with all nested objects encoded for
                 JSON compatibility.
        """
        if self._report_data:
            return json.loads(json.dumps(self._report_data, cls=KubernetesObjectJSONEncoder))

        return None

    @staticmethod
    def _create_resource_cache(kubectl: KubectlInterface, sas_custom_resource_types: List[Text]) -> Dict:
        """
        Creates a cache of resources targeted by the deployment report. The cache is a dictionary keyed by the
        resource type value of the resources that have been cached.

        :param kubectl: The Kubectl object configured to communicate with the targeted deployment.

        :raises CalledProcessError: If pod resources cannot be gathered. Pods are the smallest and most basic resource
                                    in Kubernetes and are needed to discover other resource controller types.

        :return: A dictionary of cached resources keyed by their resource type values.
        """
        # create the cache dictionary
        resource_cache: Dict = dict()

        ################
        # No cache_resources() calls should be placed above this call
        ################

        try:
            ################
            # Pods and resource controllers
            ################
            # Pods are the smallest unit in Kubernetes and define 'ownerReferences', which can be used to cache
            # upstream relationships to controller resources
            #
            # resources that are not described in "ownerReferences" definitions will be cached separately
            resource_util.cache_resources(resource_type=ResourceTypeValues.K8S_CORE_PODS,
                                          kubectl=kubectl,
                                          resource_cache=resource_cache)
        except CalledProcessError:
            # if a CalledProcessError is raised when caching pods, then surface an error up to stop the program
            # without the ability to list pods, aggregating component resources won't occur
            raise KubectlRequestForbiddenError(f"Listing pods is forbidden in namespace [{kubectl.get_namespace()}]. "
                                               "Make sure KUBECONFIG is correctly set and that the correct namespace "
                                               "is being targeted. A namespace can be given on the command line using "
                                               "the \"--namespace=\" option.")

        ################
        # No cache_resources() calls should be placed between this call and the previous
        ################

        # cache values that are not owned by components but could still be included in the report, if present
        for resource_type in [ResourceTypeValues.K8S_CORE_NODES,
                              ResourceTypeValues.K8S_CORE_CONFIG_MAPS,
                              ResourceTypeValues.K8S_CORE_SECRETS]:
            try:
                ################
                # Nodes
                # ConfigMaps
                # Secrets
                ################
                resource_util.cache_resources(resource_type=resource_type,
                                              kubectl=kubectl,
                                              resource_cache=resource_cache)
            except CalledProcessError:
                # these resources may not exist or they may not be listable
                # continue without error, they will be omitted from the final report
                pass

        # if pods were found, cache additional resources that relate to them
        if resource_cache[ResourceTypeValues.K8S_CORE_PODS][Keys.ResourceTypeDetails.COUNT] > 0:
            try:
                ################
                # Services
                ################
                # gather details about networking types - start with services
                resource_util.cache_resources(resource_type=ResourceTypeValues.K8S_CORE_SERVICES,
                                              kubectl=kubectl,
                                              resource_cache=resource_cache)
            except CalledProcessError:
                # continue caching other resources, services will be excluded from the final report
                pass

            # look for all resource types used by supported ingress controllers
            for ingress_resource_types in SupportedIngress.get_ingress_controller_to_resource_types_map().values():
                for ingress_resource_type in ingress_resource_types:
                    try:
                        ################
                        # HTTPProxy
                        # Ingress (extensions)
                        # Ingress (networking.k8s.io)
                        # Route
                        # VirtualService
                        ################
                        resource_util.cache_resources(resource_type=ingress_resource_type,
                                                      kubectl=kubectl,
                                                      resource_cache=resource_cache)
                    except CalledProcessError:
                        # continue caching other resources
                        continue

                # make sure an attempt is made to gather any SAS custom resources that were discovered
                # some may have already been gathered if they are upstream owners of any Pods
                for sas_custom_resource_type in sas_custom_resource_types:
                    try:
                        ################
                        # SAS Custom Resources
                        ################
                        resource_util.cache_resources(resource_type=sas_custom_resource_type,
                                                      kubectl=kubectl,
                                                      resource_cache=resource_cache)
                    except CalledProcessError:
                        # continue caching other resources
                        continue

        # return all discovered resources
        return resource_cache

    def gather_details(self, kubectl: KubectlInterface,
                       include_pod_log_snips: bool = INCLUDE_POD_LOG_SNIPS_DEFAULT) -> None:
        """
        This method executes the gathering of Kubernetes resources related to SAS components.
        Before this method is executed class fields will have a None value. This method will
        cache the Kubernetes resources as a dictionary, making the values accessible via the
        API for this class. The data will also be collated into relevant values used to populate
        the HTML report, which can be generated by calling the write_report() method.

        :param kubectl: The configured KubectlInterface object used to communicate with the desired Kubernetes cluster.
        :param include_pod_log_snips: If True, a snippet of the most recent log messages will be
                                      captured as part of the Pod resource. This option will cause
                                      the execution of this method to take significantly longer.
        """
        #######################################################################
        # Initialize class fields                                             #
        #######################################################################
        self._report_data: Dict = dict()

        #######################################################################
        # Get the timestamp for when the report data was gathered             #
        #######################################################################
        report_data_gathered_timestamp: Text = datetime.datetime.now().strftime(_READABLE_TIMESTAMP_TMPL_)

        #######################################################################
        # Get the resource types available in the targeted namespace          #
        #######################################################################
        available_resource_types: KubernetesAvailableResourceTypes = kubectl.api_resources()
        available_resource_types_dict: Dict = available_resource_types.as_dict()

        # make a list of any custom resource types that are provided by SAS
        sas_custom_resource_types: List = list()
        for resource_type, details in available_resource_types_dict.items():
            if _SAS_API_GROUP_ID_ in details[KubernetesAvailableResourceTypes.Keys.GROUP]:
                sas_custom_resource_types.append(resource_type)

        #######################################################################
        # Create a cache of resources discovered in the targeted namespace    #
        #######################################################################
        resource_cache: Dict = self._create_resource_cache(kubectl=kubectl,
                                                           sas_custom_resource_types=sas_custom_resource_types)

        #######################################################################
        # Create a cadence/db/configmaps/secrets information                  #
        #######################################################################
        cadence_info: Text = config_util.get_cadence_version(resource_cache=resource_cache)

        db_dict: Dict = config_util.get_db_info(resource_cache=resource_cache)

        configmaps_dict: Dict = config_util.get_configmaps_info(resource_cache=resource_cache)

        secretsnames_dict: Dict = dict()
        secrets_dict: Dict = config_util.get_secrets_info(resource_cache=resource_cache,
                                                          secretsnames_dict=secretsnames_dict)

        #######################################################################
        # Check whether pod resources were found (resources exist)            #
        #######################################################################
        pods_found: bool = \
            resource_cache[ResourceTypeValues.K8S_CORE_PODS][Keys.ResourceTypeDetails.COUNT] > 0

        #######################################################################
        # Determine ingress controller and unavailable resource types         #
        #######################################################################
        # default values in-case pods were not found
        ingress_controller: Optional[Text] = None
        ingress_version: Optional[Text] = None
        unavailable_resources: List = list()

        # evaluate resources that would be gathered if pods were found
        if pods_found:
            # determine the ingress controller for the deployment
            # this will help to evaluate which resources should be considered "unavailable"
            ingress_controller = ingress_util.determine_ingress_controller(resource_cache)
            if (
                ingress_controller == SupportedIngress.Controllers.NGINX or
                ingress_controller == SupportedIngress.Controllers.ISTIO or
                ingress_controller == SupportedIngress.Controllers.OPENSHIFT or
                ingress_controller == SupportedIngress.Controllers.CONTOUR
               ):
                ingress_version = ingress_util.get_ingress_version(kubectl)

            # determine if any resource types for which caching was attempted were unavailable
            # if at least one is unavailable, a message will be displayed saying that components may not be complete
            # because all resources were not listable
            for resource_type, resource_type_details in resource_cache.items():
                # check if the resource type is unavailable
                if not resource_type_details[Keys.ResourceTypeDetails.AVAILABLE]:
                    # ignore any ingress resource types not related to the ingress controller
                    if not ingress_util.ignorable_for_controller_if_unavailable(ingress_controller, resource_type):
                        # add the resource type to the unavailable resources
                        unavailable_resources.append(resource_type)

        #######################################################################
        # Define relationships between resources                              #
        #######################################################################
        # if pods were not found, resource relationships won't be determinable
        if pods_found:
            # define the relationship between Node and Pod
            relationship_util.define_node_to_pod_relationships(resource_cache=resource_cache)

            # define the relationship between Pod and Service
            relationship_util.define_pod_to_service_relationships(resource_cache=resource_cache)

            # define the relationship between Service and ingress controller resource types
            relationship_util.define_service_to_ingress_relationships(resource_cache=resource_cache,
                                                                      ingress_controller=ingress_controller)

        #######################################################################
        # Get metrics                                                         #
        #######################################################################
        # get Pod metrics
        metrics_util.get_pod_metrics(kubectl, resource_cache[ResourceTypeValues.K8S_CORE_PODS])

        # get Node metrics
        metrics_util.get_node_metrics(kubectl, resource_cache[ResourceTypeValues.K8S_CORE_NODES])

        #######################################################################
        # Gather Pod logs, if requested                                       #
        #######################################################################
        # check if logs were requested
        if pods_found and include_pod_log_snips:
            # loop over all Pods to get their log snips
            for pod_name, pod_details in resource_cache[ResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY].items():
                try:
                    # get the log snip
                    log_snip: List = kubectl.logs(pod_name)

                    # add it to the pod's extension dict
                    pod_ext: Dict = pod_details[Keys.ResourceDetails.EXT_DICT]
                    pod_ext[Keys.ResourceDetails.Ext.LOG_SNIP_LIST]: List = log_snip
                except CalledProcessError:
                    # if the logs can't be retrieved, continue without error
                    pass

        #######################################################################
        # Create the report data dictionary                                   #
        #######################################################################
        # add the gathered time
        self._report_data[Keys.GATHERED]: Text = report_data_gathered_timestamp

        # add any unavailable resources
        self._report_data[Keys.UNAVAILABLE_RESOURCES_LIST]: List = unavailable_resources

        ##################################
        # 'kubernetes' key
        ##################################
        k8s_details_dict = self._report_data[Keys.KUBERNETES_DICT] = dict()

        # create a key to hold the API resources available in the cluster: dict
        k8s_details_dict[Keys.Kubernetes.API_RESOURCES_DICT]: Dict = available_resource_types_dict

        # create a key to hold the API versions in the cluster: list
        k8s_details_dict[Keys.Kubernetes.API_VERSIONS_LIST]: List = kubectl.api_versions()

        # create a key to mark the determined ingress controller for the cluster: str|None
        k8s_details_dict[Keys.Kubernetes.INGRESS_CTRL]: Optional[Text] = ingress_controller

        # create a key to mark the determined ingress version for the cluster: str|None
        k8s_details_dict[Keys.Kubernetes.INGRESS_VER]: Optional[Text] = ingress_version

        # create a key to mark the namespace evaluated for this report: str|None
        k8s_details_dict[Keys.Kubernetes.NAMESPACE] = kubectl.get_namespace()

        # create a key to hold the details about node in the cluster: dict
        k8s_details_dict[Keys.Kubernetes.NODES_DICT]: Dict = resource_cache[ResourceTypeValues.K8S_CORE_NODES]

        # create a key to hold the client/server versions for the cluster: dict
        k8s_details_dict[Keys.Kubernetes.VERSIONS_DICT]: Dict = kubectl.version()

        # create a key to hold the meta information about resources discovered in the cluster: dict
        k8s_details_dict[Keys.Kubernetes.DISCOVERED_RESOURCE_TYPES_DICT]: Dict = dict()

        # create a key to hold the cadence version information: str|None
        k8s_details_dict[Keys.Kubernetes.CADENCE_INFO]: Text = cadence_info

        # create a key to hold the Viya db information: dict
        k8s_details_dict[Keys.Kubernetes.DB_INFO]: Dict = db_dict

        # create a key to hold the Viya configmaps information: dict
        k8s_details_dict[Keys.Kubernetes.CONFIGMAPS_DICT]: Dict = configmaps_dict

        # create a key to hold the Viya secrets information: dict
        k8s_details_dict[Keys.Kubernetes.SECRETS_DICT]: Dict = secrets_dict

        # add the availability and count of all discovered resources
        for resource_type, resource_type_details in resource_cache.items():
            # create an entry for the resource
            type_dict = k8s_details_dict[Keys.Kubernetes.DISCOVERED_RESOURCE_TYPES_DICT][resource_type] = dict()

            # create a key to mark if the resource type was available: bool
            type_dict[Keys.ResourceTypeDetails.AVAILABLE]: bool = \
                resource_type_details[Keys.ResourceTypeDetails.AVAILABLE]

            # create a key to note the total count of the resource type: int
            type_dict[Keys.ResourceTypeDetails.COUNT]: int = resource_type_details[Keys.ResourceTypeDetails.COUNT]

            # create a key to note the kind value of the resource
            type_dict[Keys.ResourceTypeDetails.KIND]: Text = resource_type_details[Keys.ResourceTypeDetails.KIND]

            # create a key to note whether this type is a SAS custom resource definition: bool
            type_dict[Keys.ResourceTypeDetails.SAS_CRD]: bool = resource_type in sas_custom_resource_types

        # if Pods are defined, aggregate the resources that comprise a component
        if pods_found:
            # create the sas and misc entries in report_data
            sas_dict = self._report_data[Keys.SAS_COMPONENTS_DICT] = dict()
            misc_dict = self._report_data[Keys.OTHER_COMPONENTS_DICT] = dict()

            # create components by building them up from the Pod via relationship extensions
            for pod_details in resource_cache[ResourceTypeValues.K8S_CORE_PODS][ITEMS_KEY].values():
                # define a dictionary to hold the aggregated component
                component: Dict = dict()

                # aggregate all the resources related to this Pod into a component
                component_util.aggregate_resources(resource_details=pod_details,
                                                   component=component,
                                                   resource_cache=resource_cache)

                # note whether this component belongs to SAS
                is_sas_component: bool = False

                # get the component name value
                component_name: Text = component[NAME_KEY]

                # iterate over all resource types in the component
                for resource_type_details in component[ITEMS_KEY].values():
                    # iterate over all resources of this type
                    for resource_details in resource_type_details.values():
                        # see if this resource is a SAS resource, if so this component will be treated as a SAS
                        # component
                        is_sas_component = \
                            (is_sas_component or
                             resource_details[Keys.ResourceDetails.RESOURCE_DEFINITION].is_sas_resource())
                        if is_sas_component:
                            break
                    if is_sas_component:
                        break

                # add the component to its appropriate dictionary
                if is_sas_component:
                    if component_name not in sas_dict:
                        # if this component is being added for the first time, create its key
                        sas_dict[component_name]: Dict = component[ITEMS_KEY]
                    else:
                        # otherwise, merge with the resource type
                        for resource_type, resource_type_details in component[ITEMS_KEY].items():
                            # create the resource type dictionary if one is not already defined
                            if resource_type not in sas_dict[component_name]:
                                sas_dict[component_name][resource_type]: Dict = resource_type_details
                            else:
                                # otherwise add the resources into the resource type dict by name
                                for resource_name, resource_details in resource_type_details.items():
                                    sas_dict[component_name][resource_type][resource_name]: Dict = resource_details

                else:
                    # add this to the misc dict, it could not be treated as a SAS component
                    misc_dict[component_name]: Dict = component[ITEMS_KEY]

            # build relationship configmaps to pod containers
            refcfgmaps_dict: Dict = dict()
            refsecrets_dict: Dict = dict()

            for s in sas_dict.keys():
                for mypod in sas_dict[s][_PODS_].keys():
                    myres = sas_dict[s][_PODS_][mypod][Keys.ResourceDetails.RESOURCE_DEFINITION]
                    mypodname = myres[KubernetesResourceKeys.METADATA][NAME_KEY]
                    myspec = myres.get_spec()
                    for c in myspec[KubernetesResourceKeys.CONTAINERS]:
                        if _ENVFROM_ in c.keys():
                            for e in c[_ENVFROM_]:
                                if _CONFIGMAPREF_ in e.keys():
                                    try:
                                        refcfgmaps_dict[e[_CONFIGMAPREF_][NAME_KEY]].append(
                                            mypodname + "_" + c[NAME_KEY])
                                    except KeyError:
                                        refcfgmaps_dict[e[_CONFIGMAPREF_][NAME_KEY]] = [mypodname + "_" + c[NAME_KEY]]

                                elif _SECRETREF_ in e.keys():
                                    try:
                                        refsecrets_dict[e[_SECRETREF_][NAME_KEY]].append(mypodname + "_" + c[NAME_KEY])
                                    except KeyError:
                                        refsecrets_dict[e[_SECRETREF_][NAME_KEY]] = [mypodname + "_" + c[NAME_KEY]]

            for k in refcfgmaps_dict.keys():
                try:
                    configmaps_dict[k][_REFPC_] = refcfgmaps_dict[k]
                except KeyError:
                    continue

            # assign ref secrets
            for r in refsecrets_dict.keys():
                try:
                    k = secretsnames_dict[r]
                    secrets_dict[k][r][_REFLINK_] = refsecrets_dict[r]
                except KeyError:
                    continue

    def get_kubernetes_details(self) -> Optional[Dict]:
        """
        Returns the details gathered about the target Kubernetes cluster.

        :return: A dictionary of details about the targeted Kubernetes cluster or None if details have not been
                 gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.KUBERNETES_DICT]
        except KeyError:
            return None

    def get_api_resources(self) -> Optional[Dict]:
        """
        Convenience method for getting the API resources from the Kubernetes cluster details.

        :return: A dictionary of details about the API resources available in the Kubernetes cluster or None if details
                 have not been gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.KUBERNETES_DICT][Keys.Kubernetes.API_RESOURCES_DICT]
        except KeyError:
            return None

    def get_api_versions(self) -> Optional[List]:
        """
        Convenience method for getting the API versions from the Kubernetes cluster details

        :return: A list of API versions available in the Kubernetes cluster or None if details have not been gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.KUBERNETES_DICT][Keys.Kubernetes.API_VERSIONS_LIST]
        except KeyError:
            return None

    def get_discovered_resources(self) -> Optional[Dict]:
        """
        Convenience method for getting the resources discovered during gathering from the Kubernetes cluster details.

        :return: A dictionary of details about the Resources discovered relating to SAS components or None if details
                 have not been gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.KUBERNETES_DICT][Keys.Kubernetes.DISCOVERED_RESOURCE_TYPES_DICT]
        except KeyError:
            return None

    def get_ingress_controller(self) -> Optional[Text]:
        """
        Convenience method for getting the ingress controller from the Kubernetes cluster details.

        :return: The Kubernetes ingress controller or None if one could not be determined or details have not been
                 gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.KUBERNETES_DICT][Keys.Kubernetes.INGRESS_CTRL]
        except KeyError:
            return None

    def get_namespace(self) -> Optional[Text]:
        """
        Convenience method for getting the namespace value from the Kubernetes cluster details.

        :return: The Kubernetes namespace targeted or None if details have not been gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.KUBERNETES_DICT][Keys.Kubernetes.NAMESPACE]
        except KeyError:
            return None

    def get_node_details(self) -> Optional[Dict]:
        """
        Convenience method for getting the Node details from the Kubernetes cluster details.

        :return: A dictionary of details about Nodes in the Kubernetes cluster or None if details have not been
                 gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.KUBERNETES_DICT][Keys.Kubernetes.NODES_DICT]
        except KeyError:
            return None

    def get_kubernetes_version_details(self) -> Optional[Dict]:
        """
        Convenience method for getting the version details from the Kubernetes cluster details.

        :return: A dictionary of details about Kuberentes versions or None if details have not been gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.KUBERNETES_DICT][Keys.Kubernetes.VERSIONS_DICT]
        except KeyError:
            return None

    def get_other_components(self) -> Optional[Dict]:
        """
        Returns the non-SAS components gathered in the target Kubernetes cluster.

        :return: A dictionary of details about non-SAS components or None if details have not been gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.OTHER_COMPONENTS_DICT]
        except KeyError:
            return None

    def get_sas_components(self) -> Optional[Dict]:
        """
        Returns the SAS components gathered in the target Kubernetes cluster.

        :return: A dictionary of details about SAS components or None if details have not been gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.SAS_COMPONENTS_DICT]
        except KeyError:
            return None

    def get_sas_component(self, component_name: Text) -> Optional[Dict]:
        """
        Convenience method for getting the details about a specific SAS component.

        :param component_name: The name of the SAS component whose details will be retrieved.
        :return: A dictionary of details about the requested SAS component or None if the component does not exist or
                 details have not been gathered.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.SAS_COMPONENTS_DICT][component_name]
        except KeyError:
            return None

    def get_sas_component_resources(self, component_name: Text, resource_types: Text) -> Optional[Dict]:
        """
        Convenience method for getting the details about specific resources for a specific SAS component.

        :param component_name: The name of the SAS component whose details will be retrieved.
        :param resource_types: The resource type value of the resources to retrieve.
        :return: A dictionary of details about all resources of the requested type from the requested SAS component or
                 None if details have not been gathered, the component doesn't exist or the component doesn't define the
                 requested resource_type.
        """
        if self._report_data is None:
            return None

        try:
            return self._report_data[Keys.SAS_COMPONENTS_DICT][component_name][resource_types]
        except KeyError:
            return None

    def write_report(self, output_directory: Text = OUTPUT_DIRECTORY_DEFAULT,
                     data_file_only: bool = DATA_FILE_ONLY_DEFAULT,
                     include_resource_definitions: bool = INCLUDE_RESOURCE_DEFINITIONS_DEFAULT,
                     file_timestamp: Optional[Text] = None) -> Tuple[Optional[AnyStr], Optional[AnyStr]]:
        """
        Writes the report data to a file as a JSON string.

        :param output_directory: The directory where the file should be written.
        :param data_file_only: If True, only the report data JSON file is created.
        :param file_timestamp: A timestamp to use for the file. If one isn't provided, a new one will be created.
        :param include_resource_definitions: If true, the full JSON resource definition will be included for each
                                             object in the report. Otherwise, the definition will be omitted.
        """
        if self._report_data is None:
            return None, None

        # get a timestamp if one isn't given #
        if file_timestamp is None:
            file_timestamp = datetime.datetime.now().strftime(_FILE_TIMESTAMP_TMPL_)

        # make sure path is valid #
        if output_directory != "" and not output_directory.endswith(os.sep):
            output_directory = output_directory + os.sep

        # convert the data to a JSON string #
        data_json = json.dumps(self._report_data, cls=KubernetesObjectJSONEncoder, indent=4, sort_keys=True)

        # write the report data #
        data_file_path: Text = output_directory + _REPORT_DATA_FILE_NAME_TMPL_.format(file_timestamp)
        with open(data_file_path, "w+") as data_file:
            data_file.write(data_json)

        # write the html file, if requested #
        html_file_path: Optional[Text] = None
        if not data_file_only:
            html_file_path = output_directory + _REPORT_FILE_NAME_TMPL_.format(file_timestamp)
            templates_dir = os.path.dirname(os.path.realpath(__file__)) + os.sep + ".." + os.sep + "templates" + os.sep
            template_renderer = Jinja2TemplateRenderer(templates_dir=templates_dir)
            html_file_path = template_renderer.as_html("viya_deployment_report.html.j2", html_file_path,
                                                       trim_blocks=True, lstrip_blocks=True,
                                                       report_data=json.loads(data_json),
                                                       include_definitions=include_resource_definitions)

        return os.path.abspath(data_file_path), html_file_path
