# SAS Viya Pod Log Download Tool

The SAS Viya pod log download tool collects recent log activity for all or a select list of SAS component pods deployed
in a Kubernetes cluster. The collected logs are written to disk for easy access. Log files are prepended with the status
information available for the pod when the tool is executed.

## Prerequisites

- The tool should be run on a machine from which the Kubernetes command-line interface, `kubectl`, can access the Kubernetes cluster. 
- The tool requires Python 3.6 or higher.  

### Required Python Packages

SAS Viya ARKcd tools require third-party packages be installed before use. All required packages can be installed using the provided `requirements.txt`:

```commandline
$ python3 -m pip install -r requirements.txt
```

Download the latest version of this tool and update required packages with every new software order.

## Usage

**Note**: This tool requires the `KUBECONFIG` environment variable to be set to the kubeconfig file with the cluster
connection information and credentials to use during execution.

### Basic Example

The following example downloads logs for all SAS component pods in the targeted cluster. The namespace containing your SAS
deployment can be specified by including the `-n` or `--namespace` option.

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS
deployment.

```commandline
$ python3 viya-arkcd.py download-pod-logs --namespace sas
```

### Controlling Log Size

Including the `-t` or `--tail` option limits the recent log lines returned to the provided number if the log line count
exceeds the requested limit. By default, `25,000` log lines are returned.

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS
deployment.

```commandline
$ python3 viya-arkcd.py download-pod-logs --namespace sas --tail 1000
```

### Selecting SAS Components

Downloaded logs can be limited to one or a select list of SAS components by including a space-separated list of SAS component
names after all desired options have been included. By default, logs are downloaded for all SAS components. The
[SAS Viya Deployment Report](../deployment_report) tool can be used to generate a list of SAS component names.

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS
deployment.

```commandline
$ python3 viya-arkcd.py download-pod-logs --namespace sas --tail 100 sas-visual-analytics-app sas-consul-server
```

### Redirecting Output

By default, the output files are written to a directory named `sas-k8s-logs` in the current working directory. Including
the `-o` or `--output-dir` option redirects the output files to the given location. The downloaded logs are placed in a
timestamped directory inside of the `output-dir` location to allow for multiple executions.

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS
deployment.

```commandline
$ python3 viya-arkcd.py download-pod-logs -n sas --output-dir="/path/to/report/"
```

### Help with the Command

The `-h` or `--help` option can be used to view usage information and list all options available for this tool.

```commandline
$ python3 viya-arkcd.py download-pod-logs --help
```
