# SAS Viya Administration Resource Kit for Container Deployments 

The SAS Viya Administration Resource Kit for Container Deployments (SAS Viya ARKcd) provides tools and utilities to help SAS customers prepare for a SAS Viya deployment.

## Introduction
SAS Viya ARKcd is a collection of resources that automate and streamline tasks that prepare an environment for a SAS Viya deployment. It also gathers information and generates reports about a deployment.

The master branch supports the latest release of SAS Viya. Visit the releases page for specific information about SAS Viya ARKcd and related SAS Viya product releases.

SAS Viya ARKcd provides the following types of assistance:

  * Pre-deployment assessment and optional configuration
  * Post-deployment automation and utilities

## Prerequisites for SAS Viya ARKcd
Obtain the latest version of SAS Viya ARKcd with every new software order.

Each tool that is included in the resource kit provides a readme that describes its specific prerequisites and functionality.

### Required Python Packages
SAS Viya ARKcd tools require third-party packages be installed before use. All required packages can be installed using the provided `requirements.txt`:

```commandline
$ python3 -m pip install -r requirements.txt
```

## Index of Tools
Tool support for the latest release of SAS Viya:

* [SAS Viya Deployment Report](deployment_report)

## License

This project is licensed under the [Apache 2.0 License](LICENSE).
