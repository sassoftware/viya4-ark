####################################################################
# ### viya_deployment_report_utils.py                            ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2020, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from subprocess import CalledProcessError
from typing import Dict, List, Optional, Text

from deployment_report.model.static.viya_deployment_report_keys import ITEMS_KEY, NAME_KEY
from deployment_report.model.static.viya_deployment_report_ingress_controller \
    import ViyaDeploymentReportIngressController
from deployment_report.model.static.viya_deployment_report_keys import ViyaDeploymentReportKeys as Keys

from viya_ark_library.k8s.sas_k8s_objects import KubernetesApiResources, KubernetesResource
from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface


class ViyaDeploymentReportUtils(object):
    """
    Helper class for the ViyaDeploymentReport model which defines statically invoked methods for running repeatable or
    atomic workflow tasks.
    """

    @staticmethod
    def gather_resource_details(kubectl: KubectlInterface, gathered_resources: Dict,
                                api_resources: KubernetesApiResources, resource_kind: Text) -> None:
        """
        Static method for gathering details about resources in the target Kubernetes cluster.

        The method is called recursively and will gather details about any resources described in current resource's
        "ownerReferences", if defined. If all discovered resource kinds are listable, a complete ownership chain will be
        gathered.

        :param kubectl: The KubectlInterface object for issuing requests to the target Kubernetes cluster.
        :param gathered_resources: The dictionary where gathered resources will be stored.
        :param api_resources: The Kubectle.ApiResources object defining the API resources of the target Kubernetes
                              cluster.
        :param resource_kind: The 'kind' value of the resources to gather.
        """
        # if an attempt has been made to gather this kind, return without moving forward #
        if resource_kind in gathered_resources:
            return

        # get the requested resources from the k8s API #
        resource_name: Text = api_resources.get_name(resource_kind)
        resources: List[KubernetesResource] = list()
        resource_available: bool = True
        if resource_name is not None:
            try:
                resources: Optional[List[KubernetesResource]] = kubectl.get_resources(
                    api_resources.get_name(resource_kind))
            except CalledProcessError as e:
                if resource_kind == KubernetesResource.Kinds.POD:
                    # if a CalledProcessError is raised for pods, surface the error #
                    # if the resource kind is not "Pod", move forward without raising an error since #
                    # pods can still be reported #
                    raise e
                else:
                    # note that this resource was not available
                    resource_available = False

        # save the resources by kind #
        gathered_resources[resource_kind]: Dict = dict()

        # create a key to note whether this resource kind was available for listing: bool #
        gathered_resources[resource_kind][Keys.KindDetails.AVAILABLE]: bool = resource_available

        # create a key to define the number of resources of this kind returned by k8s: int #
        gathered_resources[resource_kind][Keys.KindDetails.COUNT]: int = len(resources)

        # create a key to hold the resources returned by k8s: dict #
        gathered_resources[resource_kind][ITEMS_KEY]: bool = dict()

        # store a unique list of kinds in any 'ownerReferences' definitions #
        owner_kinds: List = list()

        # loop over the resources returned #
        for resource in resources:
            # remove the 'managedFields' key, if it exists, to reduce file size
            resource.get_metadata().pop(KubernetesResource.Keys.MANAGED_FIELDS, None)

            # add the resource to its kind dictionary                                                             #
            # create a key set to the name of the resource, under which all resource details will be stored: dict #
            resource_details = gathered_resources[resource_kind][ITEMS_KEY][resource.get_name()] = dict()

            # create a key to hold extra details about the resource not provided in the resource definition: dict #
            resource_details[Keys.ResourceDetails.EXT_DICT]: Dict = dict()

            # create a key to hold the ext.relationships list, which defines the name and kind of resources #
            # related to this resource: list                                                                 #
            resource_relationship_list = resource_details[Keys.ResourceDetails.EXT_DICT][
                Keys.ResourceDetails.Ext.RELATIONSHIPS_LIST] = list()

            # create a key under which the resource definition will be stored: KubernetesResource #
            resource_details[Keys.ResourceDetails.RESOURCE_DEFINITION]: KubernetesResource = resource

            # see if this resource defines any 'ownerReferences' #
            owner_references: List = resource.get_metadata_value(KubernetesResource.Keys.OWNER_REFERENCES)

            # if the resource does define 'ownerReferences', process them #
            if owner_references is not None:
                # iterate over the references #
                for owner_reference in owner_references:
                    # if the owner reference kind isn't in the owner_kinds list, add it #
                    if owner_reference[KubernetesResource.Keys.KIND] not in owner_kinds:
                        owner_kinds.append(owner_reference[KubernetesResource.Keys.KIND])

                    # add the owning object to the resource's relationships extension list #
                    relationship: Dict = ViyaDeploymentReportUtils._create_relationship_dict(
                        owner_reference[KubernetesResource.Keys.KIND],
                        owner_reference[KubernetesResource.Keys.NAME])

                    resource_relationship_list.append(relationship)

        # if more kinds have been discovered, gather them as well #
        for owner_kind in owner_kinds:
            ViyaDeploymentReportUtils.gather_resource_details(kubectl, gathered_resources, api_resources, owner_kind)

    @staticmethod
    def define_service_to_ingress_relationships(services: Dict, ingresses: Dict) -> None:
        """
        Static method that defines the upstream ext.relationship from a Service to the Ingress that controls
        its in-bound HTTP traffic.

        :param services: The Service resources gathered in the Kubernetes cluster.
        :param ingresses: The Ingress resources gathered in the Kubernetes cluster.
        """
        # the relationship can only be determined if both resources are defined #
        if services[Keys.KindDetails.COUNT] > 0 and ingresses[Keys.KindDetails.COUNT] > 0:

            # iterate over all Ingress objects and find for which Services they define paths #
            for ingress_details in ingresses[ITEMS_KEY].values():
                # get the definition for the current Ingress #
                ingress: KubernetesResource = ingress_details[Keys.ResourceDetails.RESOURCE_DEFINITION]

                # get the rules for this Ingress #
                rules: List = ingress.get_spec_value(KubernetesResource.Keys.RULES)

                # iterate over all rules to process all http paths defined #
                for rule in rules:
                    # get the http paths for this rule #
                    http_paths: List = rule[KubernetesResource.Keys.HTTP][KubernetesResource.Keys.PATHS]

                    # iterate over all http paths to process each backend defined #
                    for http_path in http_paths:

                        # init the service name var
                        service_name: Text

                        # check if this is the current Ingress definition schema
                        if ingress.get_api_version().startswith("networking.k8s.io"):
                            # get the Service name for this path #
                            service_name = \
                                http_path[KubernetesResource.Keys.BACKEND][KubernetesResource.Keys.SERVICE][
                                    KubernetesResource.Keys.NAME]

                        # otherwise, use the old definition schema
                        else:
                            # get the Service name for this path
                            service_name = \
                                http_path[KubernetesResource.Keys.BACKEND][KubernetesResource.Keys.SERVICE_NAME]

                        try:
                            # get the Service associated with this path #
                            service: Dict = services[ITEMS_KEY][service_name]

                            # create the relationship to the Ingress and add it to the Service's relationships #
                            ingress_relationship: Dict = ViyaDeploymentReportUtils._create_relationship_dict(
                                ingress.get_kind(), ingress.get_name())

                            service[Keys.ResourceDetails.EXT_DICT][
                                Keys.ResourceDetails.Ext.RELATIONSHIPS_LIST].append(ingress_relationship)
                        except KeyError:
                            # if the Service isn't defined, move on without error #
                            pass

    @staticmethod
    def define_service_to_virtual_service_relationships(services: Dict, virtual_services: Dict) -> None:
        """
        Static method that defines the upstream ext.relationship from a Service to the VirtualService that
        controls its traffic.

        :param services: The Service resources gathered in the Kubernetes cluster.
        :param virtual_services: The VirtualService resources gathered in the Kubernetes cluster.
        """
        # the relationship can only be determined if both resources are defined #
        if services[Keys.KindDetails.COUNT] > 0 and virtual_services[Keys.KindDetails.COUNT] > 0:

            # iterate over all VirtualService objects and find which Services they define routes for #
            for virtual_service_details in virtual_services[ITEMS_KEY].values():
                # get the definition of the current VirtualService #
                virtual_service: KubernetesResource = virtual_service_details[Keys.ResourceDetails.RESOURCE_DEFINITION]

                # get the http definitions for this VirtualService #
                http_definitions: List = virtual_service.get_spec_value(KubernetesResource.Keys.HTTP)

                if http_definitions is not None:
                    # iterate over all http definitions to process their route definitions #
                    for http_definition in http_definitions:
                        # get the routes defined #
                        routes: List = http_definition.get(KubernetesResource.Keys.ROUTE)

                        if routes is not None:
                            # iterate over all routes to process their destination hosts #
                            for route in routes:
                                # get the name of the Service associated with this route #
                                service_name: Text = route[KubernetesResource.Keys.DESTINATION][
                                    KubernetesResource.Keys.HOST]

                                try:
                                    # get the Service associated with this route #
                                    service: Dict = services[ITEMS_KEY][service_name]

                                    # create the VirtualService relationship and add it to the Service's relationships #
                                    virtual_service_relationship: Dict = \
                                        ViyaDeploymentReportUtils._create_relationship_dict(virtual_service.get_kind(),
                                                                                            virtual_service.get_name())

                                    service[Keys.ResourceDetails.EXT_DICT][
                                        Keys.ResourceDetails.Ext.RELATIONSHIPS_LIST].append(
                                        virtual_service_relationship)
                                except KeyError:
                                    # if the Service isn't defined, move on without error #
                                    pass
                else:
                    tcp_definitions: List = virtual_service.get_spec_value(KubernetesResource.Keys.TCP)

                    if tcp_definitions is not None:
                        # iterate over all tcp definitions to process their route definitions #
                        for tcp_definition in tcp_definitions:
                            # get the routes defined #
                            routes: List = tcp_definition.get(KubernetesResource.Keys.ROUTE)

                            if routes is not None:
                                # iterate over all routes to process their destination hosts #
                                for route in routes:
                                    # get the name of the Service associated with this route #
                                    service_name: Text = route[KubernetesResource.Keys.DESTINATION][
                                        KubernetesResource.Keys.HOST]

                                    # remove any additional address information if given a full address
                                    if "." in service_name:
                                        service_name = service_name[:service_name.find(".")]

                                    try:
                                        # get the Service associated with this route #
                                        service: Dict = services[ITEMS_KEY][service_name]

                                        # create the VirtualService relationship and add it to the Service's #
                                        # relationships #
                                        virtual_service_relationship: Dict = \
                                            ViyaDeploymentReportUtils._create_relationship_dict(
                                                virtual_service.get_kind(),
                                                virtual_service.get_name())

                                        service[Keys.ResourceDetails.EXT_DICT][
                                            Keys.ResourceDetails.Ext.RELATIONSHIPS_LIST].append(
                                            virtual_service_relationship)
                                    except KeyError:
                                        # if the Service isn't defined, move on without error #
                                        pass

    @staticmethod
    def define_pod_to_service_relationships(pods: Dict, services: Dict) -> None:
        """
        Static method that defines the upstream ext.relationship from a Pod to the Service that exposes the
        Pod.

        :param pods: The Pod resources gathered in the Kubernetes cluster.
        :param services: The Service resources gathered in the Kubernetes cluster.
        """
        # create the association between Pod and Service, if both are defined #
        if services[Keys.KindDetails.COUNT] > 0 and pods[Keys.KindDetails.COUNT] > 0:

            # iterate over all Services to process the defined selectors #
            for service_details in services[ITEMS_KEY].values():
                # get the definition for this Service #
                service: KubernetesResource = service_details[Keys.ResourceDetails.RESOURCE_DEFINITION]

                # get the selectors #
                selectors: Dict = service.get_spec_value(KubernetesResource.Keys.SELECTOR)

                # if the Service doesn't define any selectors, continue to the next Service #
                if selectors is None:
                    continue

                # loop through all Pods and find any with matching labels #
                for pod_details in pods[ITEMS_KEY].values():
                    # get the definition for this Pod #
                    pod: KubernetesResource = pod_details[Keys.ResourceDetails.RESOURCE_DEFINITION]

                    # loop through the labels defined by the Service selector and make sure all exist on the Pod #
                    for selector_label, selector_value in selectors.items():
                        # check if the Pod has the same label/value #
                        if pod.get_label(selector_label) != selector_value:
                            # if the label doesn't exist or isn't the same value, break the loop #
                            break
                    else:
                        # if the loop didn't break, add this Service to the Pod's relationships list #
                        service_relationship: Dict = ViyaDeploymentReportUtils._create_relationship_dict(
                            service.get_kind(), service.get_name())

                        pod_details[Keys.ResourceDetails.EXT_DICT][
                            Keys.ResourceDetails.Ext.RELATIONSHIPS_LIST].append(service_relationship)

    @staticmethod
    def define_node_to_pod_relationships(nodes: Dict, pods: Dict) -> None:
        """
        Static method that defines the ext.relationship from a Node to the Pod running within the Node.

        :param nodes: The Node resources gathered in the Kubernetes cluster.
        :param pods: The Pod resources gathered in the Kubernetes cluster.
        """
        # create association between Node and Pod, if both are defined #
        if pods[Keys.KindDetails.COUNT] > 0 and nodes[Keys.KindDetails.COUNT] > 0:
            node_pods: Dict = dict()

            # loop over all Pods to get their Node definition #
            for pod_details in pods[ITEMS_KEY].values():
                # get the definition of the current Pod #
                pod: KubernetesResource = pod_details[Keys.ResourceDetails.RESOURCE_DEFINITION]

                # get the Pod's Node definition #
                node_name: Text = pod.get_spec_value(KubernetesResource.Keys.NODE_NAME)

                try:
                    # create the Pod relationship and add it to the Node's relationships extension list #
                    relationship: Dict = ViyaDeploymentReportUtils._create_relationship_dict(
                        pod.get_kind(), pod.get_name())

                    nodes[ITEMS_KEY][node_name][Keys.ResourceDetails.EXT_DICT][
                        Keys.ResourceDetails.Ext.RELATIONSHIPS_LIST].append(relationship)

                    if node_name not in node_pods:
                        node_pods[node_name]: None = list()

                    node_pods[node_name].append(pod.get_name())
                except KeyError:
                    # if the Node isn't defined, move on without error #
                    pass

    @staticmethod
    def _create_relationship_dict(kind: Text, name: Text) -> Dict:
        """
        _Internal static method for creating a relationship dict object for a resource's ext.relationship list.

        :param kind: The kind value of the related resource.
        :param name: The name value of the related resource.
        :return: The dictionary defining the related resource.
        """
        relationship: Dict = dict()
        relationship[Keys.ResourceDetails.Ext.Relationship.KIND]: Text = kind
        relationship[Keys.ResourceDetails.Ext.Relationship.NAME]: Text = name
        return relationship

    @staticmethod
    def get_pod_metrics(kubectl: KubectlInterface, pods: Dict) -> None:
        """
        Static method for retrieving Pod metrics from the Kubernetes API and defining the ext.metrics
        dictionary for all gathered Pods.

        :param kubectl: The KubectlInterface object for issuing requests to the Kubernetes cluster for Pod metrics.
        :param pods: The Pod resources gathered in the Kubernetes cluster.
        """
        # get Pod metrics if Pods are defined #
        if pods[Keys.KindDetails.COUNT] > 0:
            try:
                # get Pod metrics #
                pod_metrics: Dict = kubectl.top_pods().as_dict()

                # iterate over the returned metrics and add them to the Pod extensions #
                for pod_name, metrics in pod_metrics.items():
                    try:
                        pods[ITEMS_KEY][pod_name][Keys.ResourceDetails.EXT_DICT][
                            Keys.ResourceDetails.Ext.METRICS_DICT]: Dict = metrics
                    except KeyError:
                        # if the Pod isn't defined, move on without error #
                        pass

            except CalledProcessError:
                # if Pod metrics aren't available, move on without error #
                pass

    @staticmethod
    def get_node_metrics(kubectl: KubectlInterface, nodes: Dict) -> None:
        """
        Static method for retrieving Node metrics from the Kubernetes API and defining the metrics extension
        for all gathered Nodes.

        :param kubectl: The KubectlInterface object for issuing requests to the Kubernetes cluster for Node metrics.
        :param nodes: The Node resources gathered in the Kubernetes cluster.
        """
        # get Node metrics if Nodes are defined #
        if nodes[Keys.KindDetails.COUNT] > 0:
            try:
                # get Node metrics #
                node_metrics: Dict = kubectl.top_nodes().as_dict()

                # iterate over the returned metrics and add them to the Node extensions #
                for node_name, metrics in node_metrics.items():
                    try:
                        nodes[ITEMS_KEY][node_name][Keys.ResourceDetails.EXT_DICT][
                            Keys.ResourceDetails.Ext.METRICS_DICT]: Dict = metrics
                    except KeyError:
                        # if the Node isn't defined, move on without error #
                        pass

            except CalledProcessError:
                # if Node metrics aren't available, move on without error #
                pass

    @staticmethod
    def determine_ingress_controller(gathered_resources: Dict) -> Optional[Text]:
        """
        Static method for determining the ingress controller being used in the Kubernetes cluster.

        :param gathered_resources: The complete dictionary of gathered resources from the Kubernetes cluster.
        :return: The ingress controller used in the target cluster or None if the controller cannot be determined.
        """
        # check if a SAS Ingress object is defined #
        if KubernetesResource.Kinds.INGRESS in gathered_resources:
            for ingress_details in gathered_resources[KubernetesResource.Kinds.INGRESS][ITEMS_KEY].values():
                # get the Ingress definition #
                ingress: KubernetesResource = ingress_details[Keys.ResourceDetails.RESOURCE_DEFINITION]
                # if the Ingress is a SAS resource, return nginx as the controller #
                if ingress.is_sas_resource():
                    return ViyaDeploymentReportIngressController.KUBE_NGINX

        if KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE in gathered_resources:
            # check if a SAS VirtualService object is defined #
            for virtual_service_details in gathered_resources[KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE][
                    ITEMS_KEY].values():

                # get the VirtualService definition #
                virtual_service: KubernetesResource = virtual_service_details[Keys.ResourceDetails.RESOURCE_DEFINITION]
                # if the VirtualService is a SAS resource, return istio as the controller #
                if virtual_service.is_sas_resource():
                    return ViyaDeploymentReportIngressController.ISTIO

        # if a controller couldn't be determined, return None #
        return None

    @staticmethod
    def aggregate_component_resources(resource_details: Dict, gathered_resources: Dict, component: Dict):
        """
        Static method that aggregates the various resources that comprise a component deployed into the
        Kubernetes cluster.

        This method is called recursively for each relationship extension to aggregate all related resources.

        :param resource_details: The details of the resource to aggregate into a component.
        :param gathered_resources: The complete dictionary of resources gathered in the Kubernetes cluster.
        :param component: The dictionary where the resources for the current component will be compiled.
        """
        # set up the component dict
        if NAME_KEY not in component:
            component[NAME_KEY]: Text = ""

        if ITEMS_KEY not in component:
            component[ITEMS_KEY]: Dict = dict()

        # get the relationships extension list for this resource #
        resource_relationships: List = resource_details[Keys.ResourceDetails.EXT_DICT][
            Keys.ResourceDetails.Ext.RELATIONSHIPS_LIST]

        # get the resource definition #
        resource: KubernetesResource = resource_details[Keys.ResourceDetails.RESOURCE_DEFINITION]

        # if a SAS component name is defined, use it since this is the most canonical value
        if resource.get_annotation(KubernetesResource.Keys.ANNOTATION_COMPONENT_NAME) is not None:
            component[NAME_KEY] = \
                resource.get_annotation(KubernetesResource.Keys.ANNOTATION_COMPONENT_NAME)

        # if a resource of this kind hasn't been added for the component, create the kind key #
        if resource.get_kind() not in component[ITEMS_KEY]:
            component[ITEMS_KEY][resource.get_kind()]: Dict = dict()

        # add the resource details to its kind dictionary, keyed by its name #
        component[ITEMS_KEY][resource.get_kind()][resource.get_name()]: Dict = resource_details

        # aggregate any resources defined in the relationships extension #
        for relationship in resource_relationships:
            # get the name and kind of the related resource #
            rel_kind: Text = relationship[Keys.ResourceDetails.Ext.Relationship.KIND]
            rel_name: Text = relationship[Keys.ResourceDetails.Ext.Relationship.NAME]

            # get the details for the related resource #
            try:
                related_resource_details: Optional[Dict] = gathered_resources[rel_kind][ITEMS_KEY][rel_name]
            except KeyError:
                # ignore any failures that may be raised if the resource is transient and not defined
                # note that the related resource wasn't found
                related_resource_details: Optional[Dict] = None

            # aggregate the related resource #
            if related_resource_details is not None:
                ViyaDeploymentReportUtils.aggregate_component_resources(related_resource_details, gathered_resources,
                                                                        component)

        # if this is the last resource and the component doesn't have a name determined from an annotation,
        # set a name based on the available values
        if not component[NAME_KEY]:
            component[NAME_KEY]: Text = resource.get_name()

        # if a SAS component name is defined, use it instead
        if resource.get_annotation(KubernetesResource.Keys.ANNOTATION_COMPONENT_NAME) is not None:
            component[NAME_KEY] = \
                resource.get_annotation(KubernetesResource.Keys.ANNOTATION_COMPONENT_NAME)
