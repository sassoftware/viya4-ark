# SAS Viya Top Reports

The SAS Viya Top Reports generates the top node and top pod reports for a Kubernetes cluster.

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

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS
deployment.

```commandline
python3 viya-ark.py top_reports --namespace sas
```

### Redirecting Output

By default, the output files are written to the current working directory. Including the `-o` or `--output-dir` option
redirects the output files to the given location. The provided value should be an existing path and should not include
any file names.

**Note**: The `sas` namespace used in the example should be replaced with the namespace containing your SAS
deployment.

```commandline
python3 viya-ark.py top_reports -n sas --output-dir="/path/to/report/"
```

### Help with the Command

The `-h` or `--help` option can be used to view usage information and list all options available for the report.

```commandline
python3 viya-ark.py top_reports --help
```

## Report Output

This command generates two files upon completion:

* A data file: `viya_top_reports_node_data_<timestamp>.txt`
* A data file: `viya_top_reports_pod_data_<timestamp>.txt`
