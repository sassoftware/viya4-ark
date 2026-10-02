# SAS Viya Platform Deployment Report

The SAS Viya Platform Deployment Report generates a web-viewable summary (and JSON-formatted data file) of SAS software deployed
in a Kubernetes cluster. The report includes a list of SAS-deployed components with application resources grouped
together. Overview information is gathered about the Kubernetes cluster into which the SAS components are deployed. If
the report is run with a `KUBECONFIG` capable of gathering node resources and/or pod and node metrics, they are
included in the report. Otherwise, un-retrievable information is omitted.

## Prerequisites

- The tool should be run on a machine from which the Kubernetes command-line interface, `kubectl`, can access the Kubernetes cluster. 
- The tool requires Python 3.6 or higher.  

### Required Python Packages

SAS Viya ARK tools require third-party packages be installed before use. All required packages can be installed using the provided `requirements.txt`:

```commandline
python3 -m pip install -r requirements.txt
```

Download the latest version of this tool and update required packages with every new software order.

## Usage

**Note**: Some information may be omitted or unavailable depending on the permissions granted for the provided
`KUBECONFIG`.

### Basic Example

The following example produces both the web-viewable report and JSON-formatted data. The namespace containing your SAS
deployment can be specified by including the `-n` or `--namespace` option.

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS Viya platform deployment.

```commandline
python3 viya-ark.py deployment-report --namespace sas
```

### Specifying Ingress Controller Namespace

The `-i` or `--ingress-namespace` option can be used to specify the namespace where the ingress controller is deployed.

```commandline
python3 viya-ark.py deployment-report --namespace sas --ingress-namespace ingress-ns
```
**Note**: This option can be helpful if there are issues detecting the correct ingress controller automatically.

The Cluster Overview → Versions → Ingress section always shows three rows: `Ingress API`, `Controller`, and `Version`.
`ingressApi` is derived from `INGRESS_KIND` and `INGRESS_APIVERSION` in the Viya `ingress-input-*` ConfigMap (for
example, `HTTPRoute (gateway.networking.k8s.io/v1)`); an available field is shown on its own, and missing values are
reported as `Unavailable`. The `ingressController` value is the actual controller for every mode: legacy deployments
retain their existing controller names and version probes, while Gateway API deployments report the resolved controller
(currently `Envoy Gateway`, or `Unknown` if it cannot be verified) and its workload image tag as `ingressVersion`.
`ingressImplementation` remains in JSON as a Gateway API compatibility alias and is `null` for legacy modes.

For Gateway API deployments, the report resolves the implementation through either a direct HTTPRoute-to-Gateway parent
reference or an HTTPRoute-to-ListenerSet and then Gateway chain, followed by the GatewayClass controller. ListenerSets
and their Gateways may be in different namespaces; the report uses the reference namespaces and configured host
(including ListenerSet listener hostnames) to select the relevant chain. `GATEWAY_NAME` is not required to equal a
Kubernetes Gateway name. Missing permissions, unresolved references, and digest-only images are reported as unavailable
rather than inferred from CRDs or node images.

### Including Log Snippets for All Pods

Including the `-l` or `--include-pod-log-snips` option yields a report with a 10-line log snippet for each pod.
Using this option increases the runtime of the command as well as the size of the resulting files.

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS Viya platform deployment.

```commandline
python3 viya-ark.py deployment-report -n sas --include-pod-log-snips
```

### Including Resource Definitions for All Resources

Including the `-r` or `--include-resource-definitions` option yields a report with the JSON-formatted resource
definitions for all resources found in the deployment. Using this option increases the size of the resulting files.

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS Viya platform deployment.

```commandline
python3 viya-ark.py deployment-report -n sas --include-resource-definitions
```

### Creating the Data File Only

Including the `-d` or `--data-file-only` option yields only the JSON-formatted data file. The web-viewable HTML report
is omitted.

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS Viya platform deployment.

```commandline
python3 viya-ark.py deployment-report -n sas --data-file-only
```

### Redirecting Output

By default, the output files are written to the current working directory. Including the `-o` or `--output-dir` option
redirects the output files to the given location. The provided value should be an existing path and should not include
any file names.

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS Viya platform deployment.

```commandline
python3 viya-ark.py deployment-report -n sas --output-dir="/path/to/report/"
```

### Help with the Command

The `-h` or `--help` option can be used to view usage information and list all options available for the report.

```commandline
python3 viya-ark.py deployment-report --help
```

## Report Output

This command generates two files upon completion:

* A web-viewable, HTML report: `viya_deployment_report_<timestamp>.html`
* A JSON-formatted data file: `viya_deployment_report_data_<timestamp>.json`
