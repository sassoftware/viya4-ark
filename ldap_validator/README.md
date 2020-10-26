# SAS Viya LDAP Validator

OVERVIEW

## Prerequisites

- The tool requires Python 3.6 or higher.  

### Required Python Packages

SAS Viya ARK tools require third-party packages be installed before use. All required packages can be installed using the 
provided `requirements.txt`:

```commandline
$ python3 -m pip install -r requirements.txt
```

Download the latest version of this tool and update required packages with every new software order.

## Usage

**Note**: Some information may be omitted or unavailable depending on the permissions granted for the provided
`KUBECONFIG`.

### Basic Example

The following example executes the LDAP Validation script against the specified sitedefault.yaml. The sitedefault must 
be provided using the `-y` or `--sitedefault` command line argument.

```commandline
$ python3 ldap_validator.py -y /path/to/sitedefault.yaml
```

### Custom log file

Optionally, by providing the `-l` or `--logFile` command line argument, the default logging can be directed to a custom 
log file.

```commandline
$ python3 ldap_validator.py -y /path/to/sitedefault.yaml -l /path/to/my/logFile.txt
```

**Note**: If the -l command line argument is not provided, a time-stamped log file will be generated in the directory 
from which the LDAP Validation script is run.

### Help with the Command

The `-h` or `--help` option can be used to view usage information and list all options available for the report.

```commandline
$ python3 viya-ark.py deployment-report --help
```

## Report Output

This command one file upon completion:

* A plain text report: `ldap_validation_<timestamp>.log`
