# SAS Viya 4 Administration Resource Kit

The SAS Viya Administration Resource Kit (SAS Viya ARK) provides tools and utilities to help SAS customers prepare for and gather information about a SAS Viya deployment.

## Introduction
SAS Viya ARK is a collection of resources that automate and streamline tasks that prepare an environment for a SAS Viya deployment. It also gathers information and generates reports about a deployment.

The main branch supports the latest release of SAS Viya. Visit the releases page for specific information about SAS Viya ARK and related SAS Viya product releases.

SAS Viya ARK provides the following types of assistance:

  * Pre-deployment assessment and optional configuration
  * Post-deployment automation and utilities

## Prerequisites for SAS Viya ARK
Obtain the latest version of SAS Viya ARK with every new software order.

Each tool that is included in the resource kit provides a readme that describes its specific prerequisites and functionality.

### Required Python Packages
SAS Viya ARK tools require third-party packages be installed before use. All required packages can be installed using the provided `requirements.txt`:

```commandline
$ python3 -m pip install -r requirements.txt
```

## Index of Tools
Tool support for the latest release of SAS Viya:

* [SAS Viya Deployment Report](deployment_report)
* [SAS Viya Log Download Tool](download_pod_logs)
* [Pre-installation of SAS Viya System Requirements](pre_install_report)
* [SAS Viya LDAP Validator](ldap_validator)

## Contributing

We welcome your contributions! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to submit contributions to these projects.

## License

This project is licensed under the [Apache 2.0 License](LICENSE).
