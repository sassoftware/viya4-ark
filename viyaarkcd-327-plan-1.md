# Gateway API support in deployment_report

## Problem and approach

`deployment_report` currently determines the ingress controller from `INGRESS_APIVERSION` in a Viya `ingress-input-*` ConfigMap, matching that value against API groups in `SupportedIngress`. Its report and collection paths then assume a controller-specific resource set, namespace, and version probe. The supplied artifacts show an explicit Gateway API deployment: its ingress ConfigMap declares the Gateway API group/version, `HTTPRoute`, and `GATEWAY_NAME`; the API inventory includes Gateway API and Envoy Gateway resource definitions. Keep the API mode (`Gateway API`) distinct from the concrete data-plane/controller implementation (`Envoy Gateway` in this sample), and resolve the latter from the configured Gateway's GatewayClass rather than guessing from installed CRDs, hostnames, or node images.

Implement detection using the ConfigMap's API version, implementation group, kind, gateway name, and host. Collect the relevant Gateway API resources, follow HTTPRoute parent references to Gateway and `spec.gatewayClassName` to GatewayClass, then interpret `GatewayClass.spec.controllerName`. Support Envoy Gateway for the demonstrated case and add other implementations only for verified Gateway API controller identities. Preserve `ingressController: Gateway API`, add a separate implementation field, and derive the implementation version from its controller workload when possible. Unknown implementations or inaccessible workloads should be reported explicitly without an assumed namespace or misleading version.

## Artifact findings

- The `ingress-input-*` ConfigMap reports `INGRESS_APIVERSION=gateway.networking.k8s.io/v1`, `INGRESS_IMPLEMENTATION=gateway.networking.k8s.io`, `INGRESS_KIND=HTTPRoute`, and `GATEWAY_NAME=sas-gateway`; it also has the configured ingress host. This is direct configuration evidence of Gateway API usage. `INGRESS_IMPLEMENTATION` identifies the API group, not Envoy Gateway itself.
- The API inventory includes GatewayClass, Gateway, HTTPRoute, and Envoy Gateway CRDs under `gateway.envoyproxy.io`. Node image inventory includes Envoy Proxy images. These support Envoy Gateway as the likely implementation, but CRD installation and a node image alone do not prove which controller owns the configured Gateway or identify its controller version.
- The discovered-resource summary has no GatewayClass, Gateway, HTTPRoute, or Envoy Gateway entries. It does show one available `ingresses.networking.k8s.io` resource, but that does not override the ConfigMap's `HTTPRoute` selection. The unavailable-resource list contains `virtualservices.networking.istio.io`, `routes.route.openshift.io`, and `ingresses.extensions`; these are unrelated to this Gateway API mode and should not be reported as deployment incompleteness.
- The HTML reports Controller `Unknown` and version `N/A (No default ingress namespace was found)`, consistent with Gateway API missing from the controller map and the subsequent controller-specific namespace/version assumptions.
- A CAS deployment contains both an `ingressTemplate` with NGINX annotations and a `routeTemplate`, each using the configured host. These are templates, not proof of the active ingress implementation; the ConfigMap's Gateway API kind/group should take precedence.
- The API-resource parser currently assigns `namespaced = bool(namespaced_str)`. Since `"false"` is a nonempty string, it is parsed as `True`; the artifact consequently marks GatewayClass namespaced even though GatewayClass is cluster-scoped. Correct this parser and add an explicit false-value regression test before relying on scope metadata for Gateway API collection.

## Cross-tool audit

- `pre_install_report` has no ingress-controller detection, ingress resource queries, or controller-version checks. Its generic API/permission checks remain valid; Gateway-specific pre-install readiness or RBAC validation would be a separate feature, not required for deployment-report recognition.
- `download_pod_logs` only lists Pods and retrieves logs; it has no ingress or networking-resource dependency. `ldap_validator` validates LDAP directly and has no Kubernetes dependency. Neither tool needs Gateway API changes.
- Shared library work is limited to Gateway API resource constants and the `NAMESPACED` parsing fix/test. `SupportedIngress` currently serves the deployment report's ingress paths; generic `Kubectl` resource and namespace operations do not need Gateway-specific behavior.
- Gateway API `HTTPRoute.parentRefs` are not Kubernetes `ownerReferences`. Resolve route-to-Gateway-to-GatewayClass links explicitly in deployment-report logic rather than extending the generic owner-reference traversal in `resource_util`.

## Todos

1. Add shared Gateway API group/resource constants and collection for GatewayClass, Gateway, and HTTPRoute; follow GatewayClass scope and cross-namespace parent references correctly. Correct the shared `NAMESPACED` parser and test `"false"`.
2. Detect the API mode from Viya ingress ConfigMap fields and correlate `GATEWAY_NAME` / HTTPRoute parent references to Gateway and GatewayClass; resolve the concrete implementation through `spec.controllerName`.
3. Report Gateway API as the ingress API/controller label and expose its implementation separately; support Envoy Gateway first, and only add other controllers for verified Gateway API identities. Obtain the version from the implementation control-plane workload, not from node image inventory.
4. Update ingress relationships to connect HTTPRoute backend references to Services, filter unavailable legacy ingress kinds when Gateway API is selected, and clarify controller/version semantics in JSON and HTML.
5. Expand simulator and report tests for the artifact's ConfigMap values, Envoy Gateway and unknown implementations, scoped resource retrieval, unavailable-resource filtering, version lookup failures, and existing ingress behavior; document the report fields. Keep `pre_install_report`, `download_pod_logs`, and `ldap_validator` unchanged.

## Notes and constraints

- Confirm the exact GatewayClass controller name in the target deployment before enabling Envoy Gateway version probing; this report does not include the GatewayClass, Gateway, or HTTPRoute object definitions.
- Gateway API resources may cross namespace boundaries: HTTPRoutes are namespaced, GatewayClass is cluster-scoped, and a Gateway may be outside the Viya namespace. Use ConfigMap and parent-reference data to target resource reads rather than assuming the Viya namespace contains every object.
- Keep detection of Gateway API usage separate from detection of the implementation and its version. If class/workload access is unavailable, preserve the positive Gateway API result while showing the implementation/version as Unknown or unavailable.
- Do not treat API CRD availability, the NGINX annotations in the CAS template, or a node's Envoy image list as definitive evidence of the active controller. Do not attempt general support for every Gateway API route kind unless Viya's configuration requires it.
- Scope is deployment-report recognition, not a drop-in migration: this change will not install or replace a controller, convert existing Ingress or Contour HTTPProxy resources, or claim feature parity. Gateway API compatibility depends on the selected implementation and should not be inferred by the report.
