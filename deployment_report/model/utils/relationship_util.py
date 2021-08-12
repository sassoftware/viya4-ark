####################################################################
# ### relationship_util.py                                      ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2021, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from typing import Dict, List, Optional, Text

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    ViyaDeploymentReportKeys as ReportKeys

from viya_ark_library.k8s.k8s_resource_keys import KubernetesResourceKeys
from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues as ResourceTypeValues
from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource


def create_relationship_dict(resource_name: Text, resource_type: Text) -> Dict:
    """
    Creates a relationship dict object for a resource's ext.relationship list.

    :param resource_name: The name value of the related resource.
    :param resource_type: The qualified type value of the related resource.
    :return: The dictionary defining the related resource.
    """
    relationship: Dict = dict()
    relationship[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]: Text = resource_name
    relationship[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]: Text = resource_type
    return relationship


def define_node_to_pod_relationships(resource_cache: Dict) -> None:
    """
    Defines the ext.relationship from a Node to a Pod running within that Node.

    :param resource_cache: The cache of resources discovered for the targeted deployment.
    """
    # get details for the cached pods and nodes
    pods: Dict = resource_cache[ResourceTypeValues.K8S_CORE_PODS]
    nodes: Dict = resource_cache[ResourceTypeValues.K8S_CORE_NODES]

    # create association between Node and Pod, if both are defined
    if pods[ReportKeys.ResourceTypeDetails.COUNT] > 0 and nodes[ReportKeys.ResourceTypeDetails.COUNT] > 0:
        # loop over all Pods to get their Node definition
        for pod_details in pods[ITEMS_KEY].values():
            # get the definition of the current Pod
            pod: KubernetesResource = pod_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

            # get the Pod's Node definition
            node_name: Text = pod.get_spec_value(KubernetesResourceKeys.NODE_NAME)

            try:
                # create the Pod relationship and add it to the Node's relationships extension list
                relationship: Dict = create_relationship_dict(resource_name=pod.get_name(),
                                                              resource_type=ResourceTypeValues.K8S_CORE_PODS)

                # add the relationship to the Node's relationships extension list
                node_ext: Dict = nodes[ITEMS_KEY][node_name][ReportKeys.ResourceDetails.EXT_DICT]
                node_relationships: List = node_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]
                node_relationships.append(relationship)
            except KeyError:
                # if the Node isn't defined, move on without error
                pass


def define_pod_to_service_relationships(resource_cache: Dict) -> None:
    """
    Defines the upstream ext.relationship from a Pod to a Service that exposes the Pod.

    :param resource_cache: The cache of resources discovered for the targeted deployment.
    """
    services: Dict = resource_cache[ResourceTypeValues.K8S_CORE_SERVICES]
    pods: Dict = resource_cache[ResourceTypeValues.K8S_CORE_PODS]

    # create the association between Pod and Service, if both are defined
    if services[ReportKeys.ResourceTypeDetails.COUNT] > 0 and pods[ReportKeys.ResourceTypeDetails.COUNT] > 0:

        # iterate over all Services to process the defined selectors
        for service_details in services[ITEMS_KEY].values():
            # get the definition for this Service
            service: KubernetesResource = service_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

            # get the selectors
            selectors: Dict = service.get_spec_value(KubernetesResourceKeys.SELECTOR)

            # if the Service doesn't define any selectors, continue to the next Service
            if selectors is None:
                continue

            # loop through all Pods and find any with matching labels
            for pod_details in pods[ITEMS_KEY].values():
                # get the definition for this Pod
                pod: KubernetesResource = pod_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

                # loop through the labels defined by the Service selector and make sure all exist on the Pod
                for selector_label, selector_value in selectors.items():
                    # check if the Pod has the same label/value
                    if pod.get_label(selector_label) != selector_value:
                        # if the label doesn't exist or isn't the same value, break the loop
                        break
                else:
                    # if the loop didn't break, define the relationship
                    service_relationship: Dict = \
                        create_relationship_dict(resource_name=service.get_name(),
                                                 resource_type=ResourceTypeValues.K8S_CORE_SERVICES)

                    # and add it to the pods relationship list
                    pod_ext: Dict = pod_details[ReportKeys.ResourceDetails.EXT_DICT]
                    pod_relationships: List = pod_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]
                    pod_relationships.append(service_relationship)


def define_service_to_ingress_relationships(resource_cache: Dict, ingress_controller: Text) -> None:
    """
    Defines the upstream ext.relationship from a Service to the ingress kind supported by the ingress controller.

    :param resource_cache: The dictionary of resources gathered from the k8s deployment.
    :param ingress_controller: The ingress controller used by the deployment.
    """
    services: Dict = resource_cache[ResourceTypeValues.K8S_CORE_SERVICES]

    # if no services were gathered, there's nothing to do
    if services[ReportKeys.ResourceTypeDetails.COUNT] > 0:
        # get the dictionary of supported controller to resource type mappings
        controller_to_resource_types_map: Dict[Text, List[Text]] = \
            SupportedIngress.get_ingress_controller_to_resource_types_map()

        # get the resource types mapped to the ingress controller
        resource_types: List[Text] = controller_to_resource_types_map.get(ingress_controller, None)

        # if a resource types weren't returned, there's nothing to do
        if resource_types:
            for resource_type in resource_types:
                # get the dictionary of resources
                resources: Optional[Dict] = resource_cache.get(resource_type)

                if resources:
                    # if none of this resource type was gathered, there's nothing to do
                    if resources[ReportKeys.ResourceTypeDetails.COUNT] > 0:
                        ####################
                        # Contour
                        ####################
                        if ingress_controller == SupportedIngress.Controllers.CONTOUR:
                            _define_service_to_contour_httpproxy_relationships(services, resources, resource_type)

                        ####################
                        # Istio
                        ####################
                        elif ingress_controller == SupportedIngress.Controllers.ISTIO:
                            _define_service_to_istio_virtual_service_relationships(services, resources, resource_type)

                        ####################
                        # NGINX
                        ####################
                        elif ingress_controller == SupportedIngress.Controllers.NGINX:
                            _define_service_to_nginx_ingress_relationships(services, resources, resource_type)

                        ####################
                        # OpenShift
                        ####################
                        elif ingress_controller == SupportedIngress.Controllers.OPENSHIFT:
                            _define_service_to_openshift_route_relationships(services, resources, resource_type)


def _define_service_to_contour_httpproxy_relationships(services: Dict, httpproxies: Dict, httpproxies_type: Text) \
        -> None:
    """
    Internal method that defines the upstream ext.relationship from a Service to the Contour HTTPProxy that controls
    its in-bound HTTP traffic.

    :param services: The Service resources gathered in the Kubernetes cluster.
    :param httpproxies: The HTTPProxy resources gathered in the Kubernetes cluster.
    :param httpproxies_type: The qualified type value of the HTTPProxy resource type.
    """
    # iterate over all HTTPProxy objects and find for which Services they define paths
    for proxy_details in httpproxies[ITEMS_KEY].values():
        # get the definition for the current HTTPProxy
        proxy: KubernetesResource = proxy_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

        # store the list of services to add relationships to
        service_names: List[Text] = list()

        # get the routes for this HTTPProxy
        routes: List = proxy.get_spec_value(KubernetesResourceKeys.ROUTES)

        if routes:
            # iterate over all routes to process all associated services
            for route in routes:
                # get the services associated with this route
                route_services: List = route.get(KubernetesResourceKeys.SERVICES, list())

                # iterate over the list of services
                for route_service in route_services:
                    # get the service name
                    service_name: Text = route_service.get(KubernetesResourceKeys.NAME)

                    # add the service name to the list of related services
                    if service_name not in service_names:
                        service_names.append(service_name)

        for service_name in service_names:
            try:
                # get the Service associated with this path
                service: Dict = services[ITEMS_KEY][service_name]

                # get the current list of service relationships
                service_ext: Dict = service[ReportKeys.ResourceDetails.EXT_DICT]
                service_relationships: List = service_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]

                # make sure this relationship isn't already defined
                for rel in service_relationships:
                    if rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME] == proxy.get_name() and \
                               rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE] == httpproxies_type:
                        # this relationship already exists, break
                        break
                    else:
                        # the relationship wasn't found, add it
                        # create the relationship to the HTTPProxy
                        proxy_relationship: Dict = create_relationship_dict(resource_name=proxy.get_name(),
                                                                            resource_type=httpproxies_type)

                        # and add it to the Service's relationships
                        service_relationships.append(proxy_relationship)
            except KeyError:
                # if the Service isn't defined, continue without error
                continue


def _define_service_to_istio_virtual_service_relationships(services: Dict, virtual_services: Dict,
                                                           virtual_services_type: Text) -> None:
    """
    Internal method that defines the upstream ext.relationship from a Service to the Istio VirtualService that
    controls its traffic.

    :param services: The Service resources gathered in the Kubernetes cluster.
    :param virtual_services: The VirtualService resources gathered in the Kubernetes cluster.
    :param virtual_services_type: The qualified type value of the VirtualService resource type.
    """
    # iterate over all VirtualService objects and find which Services they define routes for
    for virtual_service_details in virtual_services[ITEMS_KEY].values():
        # get the definition of the current VirtualService
        virtual_service: KubernetesResource = virtual_service_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

        # store the list of services to add relationships to
        service_names: List[Text] = list()

        # get the http definitions for this VirtualService
        http_definitions: List = virtual_service.get_spec_value(KubernetesResourceKeys.HTTP)

        if http_definitions:
            # iterate over all http definitions to process their route definitions
            for http_definition in http_definitions:
                # get the routes defined
                routes: List = http_definition.get(KubernetesResourceKeys.ROUTE)

                if routes:
                    # iterate over all routes to process their destination hosts
                    for route in routes:
                        # get the name of the Service associated with this route
                        service_name: Text = route[KubernetesResourceKeys.DESTINATION][KubernetesResourceKeys.HOST]

                        # add the service name to the list of related services
                        if service_name not in service_names:
                            service_names.append(service_name)
        else:
            # get the tcp definitions for this VirtualService
            tcp_definitions: List = virtual_service.get_spec_value(KubernetesResourceKeys.TCP)

            if tcp_definitions:
                # iterate over all tcp definitions to process their route definitions
                for tcp_definition in tcp_definitions:
                    # get the routes defined
                    routes: List = tcp_definition.get(KubernetesResourceKeys.ROUTE)

                    if routes:
                        # iterate over all routes to process their destination hosts
                        for route in routes:
                            # get the name of the Service associated with this route
                            service_destination: Dict = route[KubernetesResourceKeys.DESTINATION]
                            service_name: Text = service_destination[KubernetesResourceKeys.HOST]

                            # remove any additional address information if given a full address
                            if "." in service_name:
                                service_name = service_name[:service_name.find(".")]

                                # add the service name to the list of related services
                                if service_name not in service_names:
                                    service_names.append(service_name)

        for service_name in service_names:
            try:
                # get the Service associated with this route
                service: Dict = services[ITEMS_KEY][service_name]

                # create the VirtualService relationship
                virtual_service_relationship: Dict = \
                    create_relationship_dict(resource_name=virtual_service.get_name(),
                                             resource_type=virtual_services_type)

                # and add it to the Service's relationships
                service_ext: Dict = service[ReportKeys.ResourceDetails.EXT_DICT]
                service_relationships = service_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]
                service_relationships.append(virtual_service_relationship)
            except KeyError:
                # if the Service isn't defined, continue without error
                continue


def _define_service_to_nginx_ingress_relationships(services: Dict, ingresses: Dict, ingresses_type: Text) -> None:
    """
    Internal method that defines the upstream ext.relationship from a Service to an Ingress that controls
    its in-bound HTTP traffic.

    :param services: The Service resources gathered in the Kubernetes cluster.
    :param ingresses: The Ingress resources gathered in the Kubernetes cluster.
    :param ingresses_type: The qualified type value of the Ingress resource type.
    """
    # iterate over all Ingress objects and find for which Services they define paths
    for ingress_details in ingresses[ITEMS_KEY].values():
        # get the definition for the current Ingress
        ingress: KubernetesResource = ingress_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

        # store the list of services to add relationships to
        service_names: List[Text] = list()

        # get the rules for this Ingress
        rules: List = ingress.get_spec_value(KubernetesResourceKeys.RULES)

        # iterate over all rules to process all http paths defined
        for rule in rules:
            # get the http paths for this rule
            http_paths: List = rule[KubernetesResourceKeys.HTTP][KubernetesResourceKeys.PATHS]

            # iterate over all http paths to process each backend defined
            for http_path in http_paths:
                # init the service name variable
                service_name: Text

                # check the api version of this Ingress
                if ingresses_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES:
                    # get the Service name as defined in this group's type
                    path_service: Dict = http_path[KubernetesResourceKeys.BACKEND][KubernetesResourceKeys.SERVICE]
                    service_name = path_service[KubernetesResourceKeys.NAME]
                else:
                    # otherwise, get the Service name as it's defined for the old group resource type
                    service_name = http_path[KubernetesResourceKeys.BACKEND][KubernetesResourceKeys.SERVICE_NAME]

                if service_name not in service_names:
                    service_names.append(service_name)

        for service_name in service_names:
            try:
                # get the Service associated with this path
                service: Dict = services[ITEMS_KEY][service_name]

                # get the Service's existing relationships
                service_ext: Dict = service[ReportKeys.ResourceDetails.EXT_DICT]
                service_relationships: List[Dict] = service_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]

                for rel in service_relationships:
                    # get the relationship attributes
                    rel_name: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_NAME]
                    rel_type: Text = rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE]

                    if rel_name == ingress.get_name():
                        if rel_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES:
                            # a relationship to this service with the same resource name and the currently supported
                            # ingress type already exists and should remain in the relationships list
                            # break the loop so the else clause does not execute
                            break

                        if (rel_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES and
                                ingresses_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES):
                            # a relationship to this service exists with the same resource name but the deprecated
                            # ingress type and a current ingress type with the same name also exists
                            # update the relationship to reference the newer type
                            rel[ReportKeys.ResourceDetails.Ext.Relationship.RESOURCE_TYPE] = ingresses_type

                            # break the loop so the else clause does not execute
                            break
                else:
                    # the loop was not broken so a relationship with this name doesn't exist
                    # create one with the current ingress object
                    ingress_relationship: Dict = create_relationship_dict(resource_name=ingress.get_name(),
                                                                          resource_type=ingresses_type)

                    service_relationships.append(ingress_relationship)
            except KeyError:
                # if the Service isn't defined, continue without error
                continue


def _define_service_to_openshift_route_relationships(services: Dict, routes: Dict, routes_type: Text) -> None:
    """
    Internal method that defines the upstream ext.relationship from a Service to the OpenShift Route that controls
    its in-bound HTTP traffic.

    :param services: The Service resources gathered in the Kubernetes cluster.
    :param routes: The Route resources gathered in the Kubernetes cluster.
    :param routes_type: The qualified type value for the Route resource type.
    """
    # iterate over all Route objects and find for which Services they define paths
    for route_details in routes[ITEMS_KEY].values():
        # get the definition for the current Route
        route: KubernetesResource = route_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

        # get the routes for this HTTPProxy
        to_service_dict: Dict = route.get_spec_value(KubernetesResourceKeys.TO)

        if to_service_dict:
            service_name: Text = to_service_dict.get(KubernetesResourceKeys.NAME, None)

            if service_name:
                try:
                    # get the Service associated with this path
                    service: Dict = services[ITEMS_KEY][service_name]

                    # get the current list of service relationships
                    service_ext: Dict = service[ReportKeys.ResourceDetails.EXT_DICT]
                    service_relationships: List = service_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]

                    # create the relationship to the Route
                    route_relationship: Dict = create_relationship_dict(resource_name=route.get_name(),
                                                                        resource_type=routes_type)

                    # and add it to the Service's relationships
                    service_relationships.append(route_relationship)
                except KeyError:
                    # if the Service isn't defined, move on without error
                    pass
