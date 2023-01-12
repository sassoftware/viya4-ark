# SAS Viya Platform LDAP Validator

This tool validates the accuracy of the LDAP properties represented in a 
sitedefault.yaml file by connecting to the LDAP server and fetching some of the 
Users and Groups attributes. When finished, the tool displays a message that 
indicates if the validation was successful or not. If the tool fails to validate 
connection using the settings in the provided sitedefault.yaml file, a non-zero 
code is returned.
You must _run the tool as an Administrator_.

**Important:** This tool validates the LDAP settings in the sitedefault.yaml file 
only. It does not validate the entire sitedefault.yaml file. If you use a 
sitedefault.yaml file, this tool indicates if the tested LDAP settings are correct.
However, that is still not a full guarantee of success since the tool is not able
to check every parameter in the sitedefault.yaml file for accuracy. 

**Note:** SAS recommends that you do not use the sitedefault.yaml file for the 
initial deployment of your SAS Viya platform software. For more information, see [Add a sitedefault File to Your Deployment](http://documentation.sas.com/?cdcId=itopscdc&cdcVersion=default&docsetId=dplyml0phy0dkr&docsetTarget=n08u2yg8tdkb4jn18u8zsi6yfv3d.htm#n19f4zubzxljtdn12lo0nkv4n4cf).

## Prerequisites

The validator tool requires Python 3.6 or higher.  

### Required Python Packages

SAS Viya ARK tools require third-party packages be installed before use. All required packages can be installed using the 
provided `requirements.txt`:

```commandline
python3 -m pip install -r requirements.txt
```

Download the latest version of this tool and update required packages with every new software order.

## Usage

The following command provides usage details:

```
python3 viya-ark.py ldap_validator --help
```
The following example executes the LDAP Validation script against the specified sitedefault.yaml. 

```commandline
python3 viya-ark.py ldap_validator -s /path/to/sitedefault.yaml
```

## Log Output

The tool generates a plain text log file,`ldap_validator_<timestamp>.log. 

