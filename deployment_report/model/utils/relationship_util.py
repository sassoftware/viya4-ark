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

from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource


def create_relationship_dict(kind: Text, name: Text) -> Dict:
    """
    Creates a relationship dict object for a resource's ext.relationship list.

    :param kind: The kind value of the related resource.
    :param name: The name value of the related resource.
    :return: The dictionary defining the related resource.
    """
    relationship: Dict = dict()
    relationship[ReportKeys.ResourceDetails.Ext.Relationship.KIND]: Text = kind
    relationship[ReportKeys.ResourceDetails.Ext.Relationship.NAME]: Text = name
    return relationship


def define_node_to_pod_relationships(nodes: Dict, pods: Dict) -> None:
    """
    Defines the ext.relationship from a Node to a Pod running within that Node.

    :param nodes: The Node resources gathered in the Kubernetes cluster.
    :param pods: The Pod resources gathered in the Kubernetes cluster.
    """
    # create association between Node and Pod, if both are defined
    if pods[ReportKeys.KindDetails.COUNT] > 0 and nodes[ReportKeys.KindDetails.COUNT] > 0:
        # loop over all Pods to get their Node definition
        for pod_details in pods[ITEMS_KEY].values():
            # get the definition of the current Pod
            pod: KubernetesResource = pod_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

            # get the Pod's Node definition
            node_name: Text = pod.get_spec_value(KubernetesResource.Keys.NODE_NAME)

            try:
                # create the Pod relationship and add it to the Node's relationships extension list
                relationship: Dict = create_relationship_dict(pod.get_kind(), pod.get_name())

                # add the relationship to the Node's relationships extension list
                node_ext: Dict = nodes[ITEMS_KEY][node_name][ReportKeys.ResourceDetails.EXT_DICT]
                node_relationships: List = node_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]
                node_relationships.append(relationship)
            except KeyError:
                # if the Node isn't defined, move on without error
                pass


def define_pod_to_service_relationships(pods: Dict, services: Dict) -> None:
    """
    Defines the upstream ext.relationship from a Pod to a Service that exposes the
    Pod.

    :param pods: The Pod resources gathered in the Kubernetes cluster.
    :param services: The Service resources gathered in the Kubernetes cluster.
    """
    # create the association between Pod and Service, if both are defined
    if services[ReportKeys.KindDetails.COUNT] > 0 and pods[ReportKeys.KindDetails.COUNT] > 0:

        # iterate over all Services to process the defined selectors
        for service_details in services[ITEMS_KEY].values():
            # get the definition for this Service
            service: KubernetesResource = service_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

            # get the selectors
            selectors: Dict = service.get_spec_value(KubernetesResource.Keys.SELECTOR)

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
                    service_relationship: Dict = create_relationship_dict(service.get_kind(), service.get_name())

                    # and add it to the pods relationship list
                    pod_ext: Dict = pod_details[ReportKeys.ResourceDetails.EXT_DICT]
                    pod_relationships: List = pod_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]
                    pod_relationships.append(service_relationship)


def define_service_to_ingress_relationships(ingress_controller: Text, gathered_resources: Dict) -> None:
    """
    Defines the upstream ext.relationship from a Service to the ingress kind supported by
    the ingress controller.

    :param ingress_controller: The ingress controller used by the deployment.
    :param gathered_resources: The dictionary of resources gathered from the k8s deployment.
    """
    services: Dict = gathered_resources[KubernetesResource.Kinds.SERVICE]

    # if no services were gathered, there's nothing to do
    if services[ReportKeys.KindDetails.COUNT] > 0:
        # get the dictionary of supported controller to kind mappings
        ingress_kind_map: Dict[Text, Text] = SupportedIngress.get_ingress_controller_to_kind_map()

        # get the resource kind mapped to the ingress controller
        resource_kind: Text = ingress_kind_map.get(ingress_controller, None)

        # if a kind wasn't returned, there's nothing to do
        if resource_kind:
            # get the dictionary of resources
            resources: Optional[Dict] = gathered_resources.get(resource_kind)

            if resources:
                # if none of this resource type was gathered, there's nothing to do
                if resources[ReportKeys.KindDetails.COUNT] > 0:
                    ####################
                    # Contour
                    ####################
                    if resource_kind == KubernetesResource.Kinds.CONTOUR_HTTPPROXY:
                        _define_service_to_contour_httpproxy_relationships(services, resources)

                    ####################
                    # Istio
                    ####################
                    elif resource_kind == KubernetesResource.Kinds.ISTIO_VIRTUAL_SERVICE:
                        _define_service_to_istio_virtual_service_relationships(services, resources)

                    ####################
                    # NGINX
                    ####################
                    elif resource_kind == KubernetesResource.Kinds.INGRESS:
                        _define_service_to_nginx_ingress_relationships(services, resources)

                    ####################
                    # OpenShift
                    ####################
                    elif resource_kind == KubernetesResource.Kinds.OPENSHIFT_ROUTE:
                        _define_service_to_openshift_route_relationships(services, resources)


def _define_service_to_contour_httpproxy_relationships(services: Dict, httpproxies: Dict) -> None:
    """
    Internal method that defines the upstream ext.relationship from a Service to the Contour HTTPProxy that controls
    its in-bound HTTP traffic.

    :param services: The Service resources gathered in the Kubernetes cluster.
    :param httpproxies: The HTTPProxy resources gathered in the Kubernetes cluster.
    """
    # iterate over all HTTPProxy objects and find for which Services they define paths
    for proxy_details in httpproxies[ITEMS_KEY].values():
        # get the definition for the current HTTPProxy
        proxy: KubernetesResource = proxy_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

        # get the routes for this HTTPProxy
        routes: List = proxy.get_spec_value(KubernetesResource.Keys.ROUTES)

        if routes:
            # iterate over all routes to process all associated services
            for route in routes:
                # get the services associated with this route
                route_services: List = route.get(KubernetesResource.Keys.SERVICES, list())

                # iterate over the list of services
                for route_service in route_services:
                    # get the service name
                    service_name: Text = route_service.get(KubernetesResource.Keys.NAME)

                    try:
                        # get the Service associated with this path
                        service: Dict = services[ITEMS_KEY][service_name]

                        # get the current list of service relationships
                        service_ext: Dict = service[ReportKeys.ResourceDetails.EXT_DICT]
                        service_relationships: List = service_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]

                        # make sure this relationship isn't already defined
                        for rel in service_relationships:
                            if rel[ReportKeys.ResourceDetails.Ext.Relationship.KIND] == proxy.get_kind() and \
                                    rel[ReportKeys.ResourceDetails.Ext.Relationship.NAME] == proxy.get_name():
                                # this relationship already exists, break
                                break
                        else:
                            # the relationship wasn't found, add it
                            # create the relationship to the HTTPProxy
                            proxy_relationship: Dict = create_relationship_dict(proxy.get_kind(), proxy.get_name())

                            # and add it to the Service's relationships
                            service_relationships.append(proxy_relationship)
                    except KeyError:
                        # if the Service isn't defined, move on without error
                        pass


def _define_service_to_istio_virtual_service_relationships(services: Dict, virtual_services: Dict) -> None:
    """
    Internal method that defines the upstream ext.relationship from a Service to the Istio VirtualService that
    controls its traffic.

    :param services: The Service resources gathered in the Kubernetes cluster.
    :param virtual_services: The VirtualService resources gathered in the Kubernetes cluster.
    """
    # iterate over all VirtualService objects and find which Services they define routes for
    for virtual_service_details in virtual_services[ITEMS_KEY].values():
        # get the definition of the current VirtualService
        virtual_service: KubernetesResource = virtual_service_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

        # get the http definitions for this VirtualService
        http_definitions: List = virtual_service.get_spec_value(KubernetesResource.Keys.HTTP)

        if http_definitions:
            # iterate over all http definitions to process their route definitions
            for http_definition in http_definitions:
                # get the routes defined
                routes: List = http_definition.get(KubernetesResource.Keys.ROUTE)

                if routes:
                    # iterate over all routes to process their destination hosts
                    for route in routes:
                        # get the name of the Service associated with this route
                        service_name: Text = route[KubernetesResource.Keys.DESTINATION][KubernetesResource.Keys.HOST]

                        try:
                            # get the Service associated with this route
                            service: Dict = services[ITEMS_KEY][service_name]

                            # create the VirtualService relationship
                            virtual_service_relationship: Dict = create_relationship_dict(virtual_service.get_kind(),
                                                                                          virtual_service.get_name())

                            # and add it to the Service's relationships
                            service_ext: Dict = service[ReportKeys.ResourceDetails.EXT_DICT]
                            service_relationships = service_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]
                            service_relationships.append(virtual_service_relationship)
                        except KeyError:
                            # if the Service isn't defined, move on without error
                            pass
        else:
            # get the tcp definitions for this VirtualService
            tcp_definitions: List = virtual_service.get_spec_value(KubernetesResource.Keys.TCP)

            if tcp_definitions:
                # iterate over all tcp definitions to process their route definitions
                for tcp_definition in tcp_definitions:
                    # get the routes defined
                    routes: List = tcp_definition.get(KubernetesResource.Keys.ROUTE)

                    if routes:
                        # iterate over all routes to process their destination hosts
                        for route in routes:
                            # get the name of the Service associated with this route #
                            service_destination: Dict = route[KubernetesResource.Keys.DESTINATION]
                            service_name: Text = service_destination[KubernetesResource.Keys.HOST]

                            # remove any additional address information if given a full address
                            if "." in service_name:
                                service_name = service_name[:service_name.find(".")]

                            try:
                                # get the Service associated with this route
                                service: Dict = services[ITEMS_KEY][service_name]

                                # create the VirtualService relationship
                                virtual_service_relationship: Dict = \
                                    create_relationship_dict(virtual_service.get_kind(), virtual_service.get_name())

                                # and add it to the Service's relationships
                                service_ext: Dict = service[ReportKeys.ResourceDetails.EXT_DICT]
                                svc_relationships: List = service_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]
                                svc_relationships.append(virtual_service_relationship)
                            except KeyError:
                                # if the Service isn't defined, move on without error
                                pass


def _define_service_to_nginx_ingress_relationships(services: Dict, ingresses: Dict) -> None:
    """
    Internal method that defines the upstream ext.relationship from a Service to an Ingress that controls
    its in-bound HTTP traffic.

    :param services: The Service resources gathered in the Kubernetes cluster.
    :param ingresses: The Ingress resources gathered in the Kubernetes cluster.
    """
    # iterate over all Ingress objects and find for which Services they define paths
    for ingress_details in ingresses[ITEMS_KEY].values():
        # get the definition for the current Ingress
        ingress: KubernetesResource = ingress_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

        # get the rules for this Ingress
        rules: List = ingress.get_spec_value(KubernetesResource.Keys.RULES)

        # iterate over all rules to process all http paths defined
        for rule in rules:
            # get the http paths for this rule
            http_paths: List = rule[KubernetesResource.Keys.HTTP][KubernetesResource.Keys.PATHS]

            # iterate over all http paths to process each backend defined
            for http_path in http_paths:
                # init the service name variable
                service_name: Text

                # check the api version of this Ingress
                if ingress.get_api_version().startswith("networking.k8s.io"):
                    # get the Service name defined in this api version
                    path_service: Dict = http_path[KubernetesResource.Keys.BACKEND][KubernetesResource.Keys.SERVICE]
                    service_name = path_service[KubernetesResource.Keys.NAME]

                # use the old definition schema
                else:
                    # get the Service name for api version
                    service_name = http_path[KubernetesResource.Keys.BACKEND][KubernetesResource.Keys.SERVICE_NAME]

                try:
                    # get the Service associated with this path
                    service: Dict = services[ITEMS_KEY][service_name]

                    # create the relationship to the Ingress
                    ingress_relationship: Dict = create_relationship_dict(ingress.get_kind(), ingress.get_name())

                    # and add it to the Service's relationships
                    service_ext: Dict = service[ReportKeys.ResourceDetails.EXT_DICT]
                    service_relationships: List = service_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]
                    service_relationships.append(ingress_relationship)
                except KeyError:
                    # if the Service isn't defined, move on without error
                    pass


def _define_service_to_openshift_route_relationships(services: Dict, routes: Dict) -> None:
    """
    Internal method that defines the upstream ext.relationship from a Service to the OpenShift Route that controls
    its in-bound HTTP traffic.

    :param services: The Service resources gathered in the Kubernetes cluster.
    :param routes: The Route resources gathered in the Kubernetes cluster.
    """
    # iterate over all Route objects and find for which Services they define paths
    for route_details in routes[ITEMS_KEY].values():
        # get the definition for the current Route
        route: KubernetesResource = route_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]

        # get the routes for this HTTPProxy
        to_service_dict: Dict = route.get_spec_value(KubernetesResource.Keys.TO)

        if to_service_dict:
            service_name: Text = to_service_dict.get(KubernetesResource.Keys.NAME, None)

            if service_name:
                try:
                    # get the Service associated with this path
                    service: Dict = services[ITEMS_KEY][service_name]

                    # get the current list of service relationships
                    service_ext: Dict = service[ReportKeys.ResourceDetails.EXT_DICT]
                    service_relationships: List = service_ext[ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST]

                    # create the relationship to the Route
                    route_relationship: Dict = create_relationship_dict(route.get_kind(), route.get_name())

                    # and add it to the Service's relationships
                    service_relationships.append(route_relationship)
                except KeyError:
                    # if the Service isn't defined, move on without error
                    pass
