# SAS Viya LDAP Validator

This tool validates the accuracy of some of the LDAP properties provided in a sitedefault.yaml file.
It will try to connect to the LDAP server and fetch some of the attributes of Users and Groups.
Important: The tests performed here are necessary but not exhaustive. That is, you need to at least pass all
the tests performed by the tool, but that is still not a full guarantee of success, since the tool is not yet able
to check every single parameter for accuracy. On completion it displays a message that indicates if validation
was successful or not.  A non-zero return code is returned if the tool fails to validate connection with the provided 
sitedefault.yaml.

You can use your sitedefault files when laucnhing the tool.

## NOTE:

Restrictions... TBD

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
$ python3 viya-ark.py ldap_validator --help
```
The following example executes the LDAP Validation script against the specified sitedefault.yaml. 

```commandline
$ python3 viya-ark.py ldap_validator -s /path/to/sitedefault.yaml
```

## Log Output

The tool generates a plain text log file to the indicated output directory,`ldap_validator_<timestamp>.log. 

