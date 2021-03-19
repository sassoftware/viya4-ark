# SAS Viya LDAP Validator

This tool validates the connection to the LDAP Server.

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

The following command provides usage details:

```
$ python3 viya-ark.py deployment-report --help
```
The following example executes the LDAP Validation script against the specified sitedefault.yaml. 

```commandline
$ python3 ldap_validator.py -s /path/to/sitedefault.yaml
```

### Custom log file

The default logging can be directed to a custom log file.

**Note**: If a custom logfile is not specified, a time-stamped log file will be generated in the directory 
from which the LDAP Validation script is run.

## Report Output

This command one file upon completion:

* A plain text report: `ldap_validation_<timestamp>.log`
