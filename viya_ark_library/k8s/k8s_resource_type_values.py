####################################################################
# ### k8s_resource_type_values.py                                      ###
####################################################################
# ### Author: SAS Institute Inc.                                 ###
####################################################################
#                                                                ###
# Copyright (c) 2022, SAS Institute Inc., Cary, NC, USA.         ###
# All Rights Reserved.                                           ###
# SPDX-License-Identifier: Apache-2.0                            ###
#                                                                ###
####################################################################

class KubernetesResourceTypeValues(object):
    """
    Class providing static references to commonly accessed Kubernetes resource types.
    These values can be used in Kubectl.get_resource[s]() calls to retrieve resources
    without the risk of resource group ambiguity (i.e., resources that define the same
    name/kind under different groups).
    """
    ##############################
    # SAS Custom Resources
    ##############################
    SAS_GROUP_VIYA_SAS_COM = "viya.sas.com"
    SAS_CAS_DEPLOYMENTS = f"casdeployments.{SAS_GROUP_VIYA_SAS_COM}"

    ##############################
    # Kubernetes Resources
    ##############################
    # API: apps
    K8S_GROUP_APPS = "apps"
    K8S_APPS_DEPLOYMENTS = f"deployments.{K8S_GROUP_APPS}"
    K8S_APPS_REPLICA_SETS = f"replicasets.{K8S_GROUP_APPS}"
    K8S_APPS_STATEFUL_SETS = f"statefulsets.{K8S_GROUP_APPS}"

    # API: batch
    K8S_GROUP_BATCH = "batch"
    K8S_BATCH_CRON_JOBS = f"cronjobs.{K8S_GROUP_BATCH}"
    K8S_BATCH_JOBS = f"jobs.{K8S_GROUP_BATCH}"

    # API: core - cannot include group
    K8S_CORE_CONFIG_MAPS = "configmaps"
    K8S_CORE_NAMESPACES = "namespaces"
    K8S_CORE_NODES = "nodes"
    K8S_CORE_PODS = "pods"
    K8S_CORE_SECRETS = "secrets"
    K8S_CORE_SERVICES = "services"

    # API: extensions
    K8S_GROUP_EXTENSIONS = "extensions"
    K8S_EXTENSIONS_INGRESSES = f"ingresses.{K8S_GROUP_EXTENSIONS}"

    # API: metrics.k8s.io
    K8S_GROUP_METRICS_K8S_IO = "metrics.k8s.io"
    K8S_METRICS_NODES = f"nodes.{K8S_GROUP_METRICS_K8S_IO}"
    K8S_METRICS_PODS = f"pods.{K8S_GROUP_METRICS_K8S_IO}"

    # API: networking.k8s.io
    K8S_GROUP_NETWORKING_K8S_IO = "networking.k8s.io"
    K8S_NETWORKING_INGRESSES = f"ingresses.{K8S_GROUP_NETWORKING_K8S_IO}"

    # API: storage.k8s.io
    K8S_GROUP_STORAGE_K8S_IO = "storage.k8s.io"
    K8S_STORAGE_STORAGE_CLASSES = f"storageclasses.{K8S_GROUP_STORAGE_K8S_IO}"

    # API: webinfdsvr.sas.com
    SAS_GROUP_WEBINFDSVR_SAS_COM = "webinfdsvr.sas.com"
    SAS_PGCLUSTERS = f"pgclusters.{SAS_GROUP_WEBINFDSVR_SAS_COM}"
    SAS_DATASERVERS = f"dataservers.{SAS_GROUP_WEBINFDSVR_SAS_COM}"

    SAS_GROUP_CRUNCHYDATA_COM = "postgres-operator.crunchydata.com"
    SAS_CRUNCHYCLUSTERS = f"postgresclusters.{SAS_GROUP_CRUNCHYDATA_COM}"

    ##############################
    # Third-Party Resources
    ##############################
    # Contour
    CONTOUR_GROUP_PROJECTCONTOUR_IO = "projectcontour.io"
    CONTOUR_HTTP_PROXIES = f"httpproxies.{CONTOUR_GROUP_PROJECTCONTOUR_IO}"

    # Istio
    ISTIO_GROUP_NETWORKING_ISTIO_IO = "networking.istio.io"
    ISTIO_VIRTUAL_SERVICES = f"virtualservices.{ISTIO_GROUP_NETWORKING_ISTIO_IO}"

    # OpenShift
    OPENSHIFT_GROUP_ROUTE_OPENSHIFT_IO = "route.openshift.io"
    OPENSHIFT_ROUTES = f"routes.{OPENSHIFT_GROUP_ROUTE_OPENSHIFT_IO}"
