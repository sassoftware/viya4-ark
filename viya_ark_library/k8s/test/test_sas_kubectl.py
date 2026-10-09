####################################################################
# ### test_sas_kubectl.py                                         ###
####################################################################
#                                                                ###
# Copyright (c) 2026, SAS Institute Inc., Cary, NC, USA.          ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################
import json

from viya_ark_library.k8s.sas_kubectl import Kubectl
from viya_ark_library.k8s.k8s_resource_type_values import KubernetesResourceTypeValues


def test_api_resources_parses_false_namespaced_value_as_cluster_scoped():
    fields = ["NAME", "SHORTNAMES", "APIVERSION", "NAMESPACED", "KIND", "VERBS"]
    values = ["gatewayclasses", "", "gateway.networking.k8s.io/v1", "false", "GatewayClass", "[get list]"]
    widths = [max(len(header), len(value)) + 1 for header, value in zip(fields, values)]
    headers = "".join(header.ljust(width) for header, width in zip(fields, widths))
    row = "".join(value.ljust(width) for value, width in zip(values, widths))

    kubectl = object.__new__(Kubectl)
    kubectl._cached_api_resources = None
    kubectl.do = lambda command, ignore_errors=False: f"{headers}\n{row}\n".encode()

    api_resources = kubectl.api_resources()
    assert api_resources.is_namespaced(
        "GatewayClass", "gateway.networking.k8s.io/v1") is False
    assert api_resources.get_type(
        "GatewayClass", "gateway.networking.k8s.io/v1") == KubernetesResourceTypeValues.GATEWAY_API_GATEWAY_CLASSES


def test_gateway_collection_scopes_do_not_use_configured_namespace():
    kubectl = object.__new__(Kubectl)
    kubectl.exec = "kubectl -n viya"
    kubectl._exec_without_namespace = "kubectl --context=cluster"
    captured = {}

    def fake_do(command, *args, **kwargs):
        captured["exec"] = kubectl.exec
        captured["command"] = command
        return b'{"items": []}'

    kubectl.do = fake_do
    assert kubectl.get_resources_all_namespaces(
        KubernetesResourceTypeValues.GATEWAY_API_HTTP_ROUTES) == []
    assert captured["exec"] == "kubectl --context=cluster"
    assert "--all-namespaces" in captured["command"]
    assert kubectl.exec == "kubectl -n viya"

    assert kubectl.get_resources_cluster_scoped(
        KubernetesResourceTypeValues.GATEWAY_API_GATEWAY_CLASSES) == []
    assert captured["exec"] == "kubectl --context=cluster"
    assert "--all-namespaces" not in captured["command"]
    assert kubectl.exec == "kubectl -n viya"

    resource = {
        "apiVersion": "gateway.networking.k8s.io/v1",
        "kind": "Gateway",
        "metadata": {"name": "sas-gateway", "namespace": "gateway-system"}
    }

    def fake_namespace_do(command, *args, **kwargs):
        captured["exec"] = kubectl.exec
        captured["command"] = command
        return json.dumps(resource).encode()

    kubectl.do = fake_namespace_do
    found = kubectl.get_resource_in_namespace(
        KubernetesResourceTypeValues.GATEWAY_API_GATEWAYS, "sas-gateway", "gateway-system")
    assert found.get_metadata_value("namespace") == "gateway-system"
    assert captured["exec"] == "kubectl --context=cluster"
    assert "--namespace=" in captured["command"]
    assert kubectl.exec == "kubectl -n viya"
