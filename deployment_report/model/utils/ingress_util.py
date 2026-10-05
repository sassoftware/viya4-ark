####################################################################
# ### ingress_util.py                                            ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2022-2026, SAS Institute Inc., Cary, NC, USA.    ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
from subprocess import CalledProcessError
from typing import AnyStr, Dict, List, Optional, Text, Tuple

from deployment_report.model.static.viya_deployment_report_keys import \
    ITEMS_KEY, \
    ViyaDeploymentReportKeys as ReportKeys

from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues as ResourceTypeValues
from viya_ark_library.k8s.k8s_resource_keys import KubernetesResourceKeys
from viya_ark_library.k8s.sas_k8s_ingress import SupportedIngress
from viya_ark_library.k8s.sas_k8s_objects import KubernetesResource
from viya_ark_library.k8s.sas_kubectl_interface import KubectlInterface


# constants values
_NGINX_VERSION_ = "nginx version:"
_RELEASE_ = "Release:"
_PREFIX_INGRESS_INPUT = "ingress-input-"
_KEY_INGRESS_API_VERSION = "INGRESS_APIVERSION"
_GATEWAY_API_CONTROLLER = "gateway.envoyproxy.io/gatewayclass-controller"
_GATEWAY_API_IMPLEMENTATIONS = {
    _GATEWAY_API_CONTROLLER: "Envoy Gateway",
}

# A map of ingress controllers to associated namespaces
_controller_to_ns = {
        SupportedIngress.Controllers.CONTOUR: SupportedIngress.Controllers.NS_CONTOUR,
        SupportedIngress.Controllers.ISTIO: SupportedIngress.Controllers.NS_ISTIO,
        SupportedIngress.Controllers.NGINX: SupportedIngress.Controllers.NS_NGINX,
        SupportedIngress.Controllers.OPENSHIFT: SupportedIngress.Controllers.NS_OPENSHIFT,
    }


def determine_ingress_controller(gathered_resources: Dict) -> Optional[Text]:
    """
    Determines the ingress controller being used in the Kubernetes cluster.

    :param gathered_resources: The complete dictionary of gathered resources from the Kubernetes cluster.
    :return: The ingress controller used in the target cluster or SupportedIngress.Controllers.UNKNOWN
        if the controller cannot be determined.
    """
    ingress_config = get_ingress_config(gathered_resources)
    api_version = ingress_config.get(KubernetesResourceKeys.GATEWAY_API_VERSION, "")
    implementation_group = ingress_config.get(KubernetesResourceKeys.GATEWAY_API_IMPLEMENTATION)
    if api_version.startswith(f"{ResourceTypeValues.GATEWAY_API_GROUP}/") and \
            implementation_group in (None, "", ResourceTypeValues.GATEWAY_API_GROUP):
        return SupportedIngress.Controllers.GATEWAY_API

    # locate the "ingress-input" configmap which defines the ingress used in the deployment
    for resource_name, resource_details \
            in gathered_resources[ResourceTypeValues.K8S_CORE_CONFIG_MAPS][ITEMS_KEY].items():
        if not resource_name.startswith(_PREFIX_INGRESS_INPUT):
            continue
        resource: KubernetesResource = resource_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]
        if not resource.is_sas_resource():
            continue
        data = resource.get_data()
        ingress_api_version = data.get(_KEY_INGRESS_API_VERSION, "")
        for ingress_controller, api_group in SupportedIngress.get_ingress_controller_to_api_group_map().items():
            if ingress_api_version.startswith(api_group):
                return ingress_controller

    # if a controller couldn't be determined, return Unknown
    return SupportedIngress.Controllers.UNKNOWN


def get_ingress_config(gathered_resources: Dict) -> Dict:
    """Return data from the Viya ingress-input ConfigMap, if one was gathered."""
    configmaps = gathered_resources.get(ResourceTypeValues.K8S_CORE_CONFIG_MAPS, {}).get(ITEMS_KEY, {})
    for resource_name, resource_details in configmaps.items():
        if not resource_name.startswith(_PREFIX_INGRESS_INPUT):
            continue
        resource: KubernetesResource = resource_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]
        if resource.is_sas_resource():
            return resource.get_data() or {}
    return {}


def get_ingress_api(ingress_config: Dict) -> Text:
    """Format the ingress kind and API version declared in the Viya ingress ConfigMap."""
    ingress_kind = ingress_config.get(KubernetesResourceKeys.GATEWAY_API_KIND)
    ingress_api_version = ingress_config.get(KubernetesResourceKeys.GATEWAY_API_VERSION)
    if ingress_kind and ingress_api_version:
        return f"{ingress_kind} ({ingress_api_version})"
    if ingress_kind or ingress_api_version:
        return ingress_kind or ingress_api_version
    return "Unavailable"


def gateway_api_uses_listener_sets(resource_cache: Dict) -> bool:
    """Return whether any cached HTTPRoute explicitly references a Gateway API ListenerSet."""
    routes = resource_cache.get(ResourceTypeValues.GATEWAY_API_HTTP_ROUTES, {}).get(ITEMS_KEY, {})
    for route_details in routes.values():
        route: KubernetesResource = route_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]
        for parent_ref in route.get_spec_value(KubernetesResourceKeys.GATEWAY_API_PARENT_REFS) or []:
            if parent_ref.get(KubernetesResourceKeys.GATEWAY_API_PARENT_GROUP,
                              ResourceTypeValues.GATEWAY_API_GROUP) == ResourceTypeValues.GATEWAY_API_GROUP and \
                    parent_ref.get(KubernetesResourceKeys.GATEWAY_API_PARENT_KIND, "Gateway") == "ListenerSet":
                return True
    return False


def route_matches_configured_host(route: KubernetesResource, configured_host: Optional[Text]) -> bool:
    """Return whether an HTTPRoute can serve the configured Viya host."""
    if not configured_host:
        return True

    hostnames = route.get_spec_value(KubernetesResourceKeys.HOSTNAMES) or []
    if not hostnames:
        return True

    return any(_hostname_matches(hostname, configured_host) for hostname in hostnames)


def _hostname_matches(hostname: Text, configured_host: Text) -> bool:
    hostname = hostname.lower().rstrip(".")
    host = configured_host.lower().rstrip(".")
    if hostname == host:
        return True
    return hostname.startswith("*.") and host.endswith(hostname[1:]) and \
        host.count(".") == hostname.count(".")


def _get_cached_resource(resource_type: Dict, name: Text, namespace: Text,
                         default_namespace: Text) -> Optional[KubernetesResource]:
    """Find a namespaced resource by its actual metadata, never by an unqualified name alone."""
    for details in resource_type.get(ITEMS_KEY, {}).values():
        resource: KubernetesResource = details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]
        resource_namespace = resource.get_metadata_value(KubernetesResourceKeys.NAMESPACE) or default_namespace
        if resource.get_name() == name and resource_namespace == namespace:
            return resource
    return None


def _route_parent_gateway_refs(resource_cache: Dict, route: KubernetesResource,
                               route_namespace: Text, configured_host: Optional[Text],
                               default_namespace: Text) -> Tuple[set, List[Text]]:
    """Resolve direct Gateway and ListenerSet HTTPRoute parents to namespaced Gateway references."""
    refs = set()
    issues = []
    if not route_matches_configured_host(route, configured_host):
        return refs, issues

    listener_sets = resource_cache.get(ResourceTypeValues.GATEWAY_API_LISTENER_SETS, {})
    for parent_ref in route.get_spec_value(KubernetesResourceKeys.GATEWAY_API_PARENT_REFS) or []:
        if parent_ref.get(KubernetesResourceKeys.GATEWAY_API_PARENT_GROUP,
                          ResourceTypeValues.GATEWAY_API_GROUP) != ResourceTypeValues.GATEWAY_API_GROUP:
            continue
        parent_kind = parent_ref.get(KubernetesResourceKeys.GATEWAY_API_PARENT_KIND, "Gateway")
        parent_name = parent_ref.get(KubernetesResourceKeys.NAME)
        if not parent_name:
            continue
        parent_namespace = parent_ref.get(KubernetesResourceKeys.GATEWAY_API_PARENT_NAMESPACE) or route_namespace
        if parent_kind == "Gateway":
            refs.add((parent_name, parent_namespace))
            continue
        if parent_kind != "ListenerSet":
            continue

        listener_set = _get_cached_resource(listener_sets, parent_name, parent_namespace, default_namespace)
        if listener_set is None:
            if listener_sets.get(ReportKeys.ResourceTypeDetails.AVAILABLE) is False:
                issues.append("ListenerSet access denied; references could not be verified")
            else:
                issues.append("referenced ListenerSet was not found")
            continue

        listeners = listener_set.get_spec_value(KubernetesResourceKeys.GATEWAY_API_LISTENERS) or []
        if configured_host:
            matching_listener = any(
                not listener.get(KubernetesResourceKeys.GATEWAY_API_LISTENER_HOSTNAME) or
                _hostname_matches(listener[KubernetesResourceKeys.GATEWAY_API_LISTENER_HOSTNAME], configured_host)
                for listener in listeners
            )
            if not matching_listener:
                issues.append("no ListenerSet listener matches the configured host")
                continue

        gateway_parent = listener_set.get_spec_value(KubernetesResourceKeys.GATEWAY_API_PARENT_REF) or {}
        if gateway_parent.get(KubernetesResourceKeys.GATEWAY_API_PARENT_GROUP,
                              ResourceTypeValues.GATEWAY_API_GROUP) != ResourceTypeValues.GATEWAY_API_GROUP or \
                gateway_parent.get(KubernetesResourceKeys.GATEWAY_API_PARENT_KIND, "Gateway") != "Gateway":
            issues.append("ListenerSet parent reference does not reference a Gateway")
            continue
        gateway_name = gateway_parent.get(KubernetesResourceKeys.NAME)
        if not gateway_name:
            issues.append("ListenerSet parent reference could not be resolved")
            continue
        gateway_namespace = gateway_parent.get(KubernetesResourceKeys.GATEWAY_API_PARENT_NAMESPACE) \
            or parent_namespace
        refs.add((gateway_name, gateway_namespace))
    return refs, issues


def determine_gateway_api_implementation(kubectl: KubectlInterface, resource_cache: Dict,
                                         ingress_config: Dict) -> Tuple[Text, Text, Optional[Tuple[Text, Text]]]:
    """Resolve the GatewayClass controller and, for Envoy Gateway, its workload image version."""
    unknown = "Unknown"
    unavailable = "Unavailable"
    ingress_kind = ingress_config.get(KubernetesResourceKeys.GATEWAY_API_KIND)
    if ingress_kind != "HTTPRoute":
        return unknown, f"{unavailable} (unsupported Gateway API route kind: {ingress_kind or 'unknown'})", None
    routes = resource_cache.get(ResourceTypeValues.GATEWAY_API_HTTP_ROUTES, {})
    if not routes.get(ITEMS_KEY):
        return unknown, f"{unavailable} (Gateway API parent reference could not be resolved)", None

    matched_gateway_refs = set()
    resolution_issues = []
    matching_host_routes = 0
    for route_details in routes[ITEMS_KEY].values():
        route: KubernetesResource = route_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]
        route_namespace = route.get_metadata_value(KubernetesResourceKeys.NAMESPACE) or kubectl.get_namespace()
        if route_matches_configured_host(route, ingress_config.get(KubernetesResourceKeys.GATEWAY_API_HOST)):
            matching_host_routes += 1
        refs, issues = _route_parent_gateway_refs(
            resource_cache, route, route_namespace,
            ingress_config.get(KubernetesResourceKeys.GATEWAY_API_HOST), kubectl.get_namespace())
        matched_gateway_refs.update(refs)
        resolution_issues.extend(issues)

    critical_issues = [issue for issue in resolution_issues
                       if issue != "no ListenerSet listener matches the configured host"]
    if matched_gateway_refs and critical_issues:
        return unknown, f"{unavailable} ({critical_issues[0]})", None
    if not matched_gateway_refs:
        if resolution_issues:
            return unknown, f"{unavailable} ({resolution_issues[0]})", None
        if not matching_host_routes:
            return unknown, f"{unavailable} (no HTTPRoute matches the configured host)", None
        return unknown, f"{unavailable} (no matching HTTPRoute parent chain was found)", None

    gateway_type = resource_cache.get(ResourceTypeValues.GATEWAY_API_GATEWAYS, {})

    if gateway_type.get(ReportKeys.ResourceTypeDetails.AVAILABLE):
        matched_gateway_refs = {
            ref for ref in matched_gateway_refs
            if _get_cached_resource(gateway_type, ref[0], ref[1], kubectl.get_namespace()) is not None
        }
        if not matched_gateway_refs:
            return unknown, f"{unavailable} (configured Gateway object was not found)", None
    elif len(matched_gateway_refs) > 1:
        return unknown, f"{unavailable} (Gateway access denied; references could not be verified)", None

    if len(matched_gateway_refs) > 1:
        return unknown, f"{unavailable} (configured Gateway reference is ambiguous across namespaces)", None

    matched_gateway_ref = matched_gateway_refs.pop()
    gateway_name, gateway_namespace = matched_gateway_ref
    gateway = _get_cached_resource(gateway_type, gateway_name, gateway_namespace, kubectl.get_namespace())
    if gateway is None:
        try:
            gateway = kubectl.get_resource_in_namespace(
                ResourceTypeValues.GATEWAY_API_GATEWAYS, gateway_name, gateway_namespace)
        except (CalledProcessError, AttributeError, NotImplementedError):
            return unknown, f"{unavailable} (Gateway access denied or unavailable)", matched_gateway_ref
        gateway_type = resource_cache.setdefault(ResourceTypeValues.GATEWAY_API_GATEWAYS, {
            ReportKeys.ResourceTypeDetails.AVAILABLE: True,
            ReportKeys.ResourceTypeDetails.COUNT: 0,
            ReportKeys.ResourceTypeDetails.KIND: kubectl.api_resources().get_kind(
                ResourceTypeValues.GATEWAY_API_GATEWAYS),
            ITEMS_KEY: {},
        })
        gateway_items = gateway_type[ITEMS_KEY]
        gateway_key = f"{gateway_namespace}/{gateway_name}"
        if gateway_key not in gateway_items:
            gateway_items[gateway_key] = {
                ReportKeys.ResourceDetails.EXT_DICT: {
                    ReportKeys.ResourceDetails.Ext.RESOURCE_TYPE: ResourceTypeValues.GATEWAY_API_GATEWAYS,
                    ReportKeys.ResourceDetails.Ext.RELATIONSHIPS_LIST: [],
                },
                ReportKeys.ResourceDetails.RESOURCE_DEFINITION: gateway,
            }
            gateway_type[ReportKeys.ResourceTypeDetails.COUNT] += 1

    class_name = gateway.get_spec_value(KubernetesResourceKeys.GATEWAY_CLASS_NAME)
    classes = resource_cache.get(ResourceTypeValues.GATEWAY_API_GATEWAY_CLASSES, {}).get(ITEMS_KEY, {})
    gateway_class_details = classes.get(class_name)
    if not class_name or not gateway_class_details:
        return unknown, f"{unavailable} (GatewayClass access denied or unavailable)", matched_gateway_ref
    gateway_class: KubernetesResource = gateway_class_details[ReportKeys.ResourceDetails.RESOURCE_DEFINITION]
    controller_name = gateway_class.get_spec_value(KubernetesResourceKeys.GATEWAY_CLASS_CONTROLLER_NAME)
    implementation = _GATEWAY_API_IMPLEMENTATIONS.get(controller_name)
    if not implementation:
        return unknown, f"{unavailable} (unverified GatewayClass controller: {controller_name or 'unknown'})", \
            matched_gateway_ref

    try:
        workloads = kubectl.get_resources_all_namespaces(ResourceTypeValues.K8S_APPS_DEPLOYMENTS)
    except (CalledProcessError, AttributeError, NotImplementedError):
        return implementation, f"{unavailable} (controller workload access denied)", matched_gateway_ref

    image_versions = set()
    digest_only_images = set()
    for workload in workloads:
        spec = workload.get_spec_value(KubernetesResourceKeys.TEMPLATE) or {}
        pod_spec = spec.get(KubernetesResourceKeys.SPEC, {})
        for container in pod_spec.get(KubernetesResourceKeys.CONTAINERS, []):
            image = container.get(KubernetesResourceKeys.IMAGE, "")
            image_ref, _, digest = image.partition("@")
            image_leaf = image_ref.rsplit("/", 1)[-1]
            repository = image_ref.rsplit("/", 1)[0].split("/")
            if image_leaf.split(":", 1)[0] != "gateway" or repository[-1:] != ["envoyproxy"]:
                continue
            if ":" in image_leaf:
                image_versions.add(image_leaf.rsplit(":", 1)[1])
            elif digest:
                digest_only_images.add(digest)

    if len(image_versions) > 1 or (image_versions and digest_only_images):
        return implementation, f"{unavailable} (controller workload version is ambiguous)", matched_gateway_ref
    if image_versions:
        return implementation, image_versions.pop(), matched_gateway_ref
    if digest_only_images:
        return implementation, f"{unavailable} (controller image is digest-only)", matched_gateway_ref
    return implementation, f"{unavailable} (controller workload image was not found)", matched_gateway_ref


def ignorable_for_controller_if_unavailable(ingress_controller: Text, resource_type: Text) -> bool:
    """
    Determines whether the given resource type is ignorable if unavailable given the ingress controller.

    Example: Unavailable HTTPProxy, Route, and VirtualService resources can be ignored if NGINX controls ingress.

    :param ingress_controller: The ingress controller used by the deployment.
    :param resource_type: The resource type of the unavailable resource.
    """
    ####################
    # Contour
    ####################
    if ingress_controller == SupportedIngress.Controllers.CONTOUR and (
            resource_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
            resource_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES or
            resource_type == ResourceTypeValues.OPENSHIFT_ROUTES or
            resource_type == ResourceTypeValues.ISTIO_VIRTUAL_SERVICES
    ):
        # ignore Ingress, Route, and VirtualService if controller is Contour
        return True

    elif ingress_controller == SupportedIngress.Controllers.GATEWAY_API and (
            resource_type == ResourceTypeValues.CONTOUR_HTTP_PROXIES or
            resource_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
            resource_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES or
            resource_type == ResourceTypeValues.OPENSHIFT_ROUTES or
            resource_type == ResourceTypeValues.ISTIO_VIRTUAL_SERVICES
    ):
        return True

    ####################
    # Istio
    ####################
    elif ingress_controller == SupportedIngress.Controllers.ISTIO and (
            resource_type == ResourceTypeValues.CONTOUR_HTTP_PROXIES or
            resource_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
            resource_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES or
            resource_type == ResourceTypeValues.OPENSHIFT_ROUTES
    ):
        # ignore HTTPProxy, Ingress, and Route if controller is Istio
        return True

    ####################
    # NGINX
    ####################
    elif ingress_controller == SupportedIngress.Controllers.NGINX and (
            resource_type == ResourceTypeValues.CONTOUR_HTTP_PROXIES or
            resource_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
            resource_type == ResourceTypeValues.OPENSHIFT_ROUTES or
            resource_type == ResourceTypeValues.ISTIO_VIRTUAL_SERVICES
    ):
        # ignore HTTPProxy, Route, and VirtualService if controller is NGINX
        return True

    ####################
    # OpenShift
    ####################
    elif ingress_controller == SupportedIngress.Controllers.OPENSHIFT and (
            resource_type == ResourceTypeValues.CONTOUR_HTTP_PROXIES or
            resource_type == ResourceTypeValues.K8S_EXTENSIONS_INGRESSES or
            resource_type == ResourceTypeValues.K8S_NETWORKING_INGRESSES or
            resource_type == ResourceTypeValues.ISTIO_VIRTUAL_SERVICES
    ):
        # ignore HTTPProxy, Ingress, and VirtualService if controller is OpenShift
        return True

    # not ignorable
    return False


def get_ingress_version(kubectl: KubectlInterface, ingress_controller: Text) -> Optional[Text]:
    """
    Retrieves ingress version used in the Kubernetes cluster

    :param kubectl: The KubectlInterface object.
    :return: The ingress controller version used in the target cluster or Blank if it cannot be determined.
    """

    if not kubectl.ingress_ns:
        return ""

    version: Text = ""

    getpod_cmd: AnyStr = "get pods -n " + kubectl.ingress_ns + \
                         " --field-selector=status.phase==Running" + \
                         " -o jsonpath=\"{.items[0].metadata.name}\""

    if ingress_controller == SupportedIngress.Controllers.NGINX:
        podname: AnyStr = kubectl.do(getpod_cmd + " -l app.kubernetes.io/component=controller", ignore_errors=True)

        if podname:
            version_str: AnyStr = kubectl.do("exec -it " + podname.decode() +
                                             " -n " + kubectl.ingress_ns +
                                             " -- /nginx-ingress-controller --version")
            version_list: List = version_str.decode().splitlines()
            for v in version_list:
                if _RELEASE_ in v:
                    version = ' '.join(v.split()) + version
                elif _NGINX_VERSION_ in v:
                    version = version + ", " + v.split()[-1]

    elif ingress_controller == SupportedIngress.Controllers.ISTIO:
        podname: AnyStr = kubectl.do(getpod_cmd + " -l  app=istiod", ignore_errors=True)
        if podname:
            version_str: AnyStr = kubectl.do("exec -it " + podname.decode() +
                                             " -n " + kubectl.ingress_ns +
                                             " -- pilot-discovery version --short")
            version = version_str.decode()

    elif ingress_controller == SupportedIngress.Controllers.OPENSHIFT:
        podname: AnyStr = kubectl.do(getpod_cmd + " -l  name=ingress-operator", ignore_errors=True)
        if podname:
            version_str: AnyStr = kubectl.do("get pod " + podname.decode() +
                                             " -n " + kubectl.ingress_ns +
                                             " -o jsonpath=\"{.spec.containers[].env[" +
                                             "?(@.name=='RELEASE_VERSION')].value}\"")
            version = version_str.decode()

    elif ingress_controller == SupportedIngress.Controllers.CONTOUR:
        podname: AnyStr = kubectl.do(getpod_cmd + " -l controller-revision-hash", ignore_errors=True)
        if podname:
            version_str: AnyStr = kubectl.do("get pod " + podname.decode() +
                                             " -n " + kubectl.ingress_ns +
                                             " -o jsonpath=\"{.spec.containers[*].image}\"")
            version_list: List = version_str.decode().split(' ')
            for v in version_list:
                if version:
                    version = version + ", " + v.split("/")[-1].capitalize()
                else:
                    version = v.split("/")[-1].capitalize()

    return version.strip()


def get_namespace_for_ingress_controller(ingress_controller: Text) -> Text:
    """
    Maps a given ingress controller to its associated namespace as defined by SupportedIngress.Controllers data.

    :param ingress_controller: The ingress controller string (e.g., SupportedIngress.Controllers.CONTOUR).
    :return: The namespace string for the controller, or SupportedIngress.Controllers.UNKNOWN if unsupported.
    """

    return _controller_to_ns.get(ingress_controller, SupportedIngress.Controllers.UNKNOWN)
