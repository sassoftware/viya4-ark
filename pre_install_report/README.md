# Pre-Installation Check of SAS Viya Platform System Requirements
## Overview
This tool compares your Kubernetes environment to the SAS Viya platform system requirements.  It evaluates a   
number of items, such as memory, CPU cores, software versions, and permissions. The output is a web-viewable,  
HTML report with the results. 

SAS recommends running the tool and resolving any reported issues _before_ beginning a SAS Viya platform
deployment in a Kubernetes cluster.  The tool cannot account for the dynamic resource allocations that 
Kubernetes may orchestrate once the SAS Viya platform is deployed.  The report and the information therein must
be considered a snapshot in time.  

The Kubernetes cluster for a SAS Viya platform deployment must meet the requirements documented in [SAS® Viya® Platform Operations](https://go.documentation.sas.com/doc/en/itopscdc/default/itopssr/titlepage.htm)  
Ensure that the Kubernetes version is within the documented range for the selected cloud provider.  
If the Kubernetes server version is below the default minimum, a warning will be included in the report.


### Memory and vCPU Check
The tool calculates the aggregate Memory and aggregate vCPUs of your cluster. The aggregate Memory is the sum 
of the Memory capacity on all the active and running nodes. The aggregate CPU is calculated similarly.
  
There will be some percentage of Memory on each node in the cluster that is considered "overhead" (consumed by the OS, Kubelet, etc)
and therefore not be available for the SAS Viya platform.   This tool assumes that 85% of the calculated aggregate Memory is available for the SAS Viya platform, 
and the memory sizes in the report reflect this.  

The calculated aggregate number of vCPUs must equal or exceed the required aggregate number of vCPUs for your deployment offering. 
The requirements per offering are detailed in the _Hardware and Resource Requirements_ section of the SAS Viya Operations document. 
The required Memory and vCPUs sizes depend on the instance type used for the node.  

Your required aggregates must be specified in the following file: 
<tool-download-dir>/viya4-ark/pre_install_report/viya_deployment_settings.ini  
Here is an example:
```
# Total Memory of all worker Nodes in GB. Sum of the Memory on all active node required to deploy a specific offering.
# Set value for required for offering
VIYA_MIN_AGGREGATE_WORKER_MEMORY=448G
# Total CPU of all worker Nodes in millicores.  Sum of the vCPUs on all active node required to deploy a specific offering.
# Minimum allowed value = '.001'. 
VIYA_MIN_AGGREGATE_WORKER_CPU_CORES=56
```

If the calculated aggregate memory is less than a percentage (85%) of VIYA_MIN_AGGREGATE_WORKER_MEMORY then the tool will flag a memory issue.  
If the calculated aggregate vCPUs is less than VIYA_MIN_AGGREGATE_WORKER_CPU_CORES then the tool will flag a CPU issue.
 
SAS recommends using the SAS Viya 4 Infrastructure as Code (IaC) tools to create a cluster.  
Refer to the following IaC repositories for [Microsoft Azure](https://github.com/sassoftware/viya4-iac-azure), [AWS](https://github.com/sassoftware/viya4-iac-aws]), [GCP](https://github.com/sassoftware/viya4-iac-gcp) or [Open Source Kubernetes](https://github.com/sassoftware/viya4-iac-k8s)   
For OpenShift refer to the documentation in SAS® Viya® Operations [OpenShift](https://go.documentation.sas.com/doc/en/itopscdc/default/itopssr/n1ika6zxghgsoqn1mq4bck9dx695.htm#p1c8bxlbu0gzuvn1e75nck1yozcn)  
  
Example: See Sizing Recommendations for a Microsoft Azure deployment under [Hardware and Resource Requirements](https://go.documentation.sas.com/doc/en/itopscdc/default/itopssr/n0ampbltwqgkjkn1j3qogztsbbu0.htm#p1wmvm5pzezbwxn1rjjftlfqmeiu). You can use this information to calculate VIYA_MIN_AGGREGATE_WORKER_MEMORY and VIYA_MIN_AGGREGATE_WORKER_CPU_CORES.

| Offering                  | CAS Node(s)          | System Node  | Nodes in User Node Pool(s)  |
| ------------------------- |-------------          | --------- | -------------|
| SAS Visual Analytics and SAS Data Preparation  |  Num of Node: Node 1, CPU: 16, Memory, 128 | Num. of Nodes: 1, CPU: 8,  Memory: 64 | Num of Node: 1 per Node User Node Pool,  CPU: 8 Memory 64 |

VIYA_MIN_AGGREGATE_WORKER_MEMORY =  
CAS Node Memory + System Node Memory + (User Nodes Memory * 4)  

VIYA_MIN_AGGREGATE_WORKER_CPU_CORES=  
CAS node CPU  + System Node CPU + (User Node CPU * 4)


## Prerequisites 
- The tool should be run on a machine from which the Kubernetes command-line interface, `kubectl`,   
can access the Kubernetes cluster. 
- The tool requires Python 3.6 or higher.  

### Required Python Packages
SAS Viya ARK tools require third-party packages be installed before use. You can install all the required packages by   
using the provided requirements.txt file in the following command:

```commandline
python3 -m pip install -r requirements.txt
```

Download the latest version of this tool and update required packages with every new software order.

## Usage

You may set `KUBECONFIG` environment variable.  If not set, `kubectl` will use `.kube/config` by default. 
`KUBECONFIG` must have administrator rights to the cluster where you intend to deploy your SAS Viya platform software.
To obtain a complete report use a `KUBECONFIG` with administrator rights in the cluster.  Otherwise, the report will   
not be able to evaluate items such as memory, CPU cores, software versions and other node details. It is not useful   
for determining if you are ready to deploy your SAS Viya platform software.

Create the namespace where you plan to deploy SAS Viya platform.  A namespace is required to run this tool. Specify the namespace where you plan to deploy SAS Viya platform using the namespace option. If a namespace is not provided, the tool will check the current context for a namespace. Ensure that you are running with the correct namespace.   

After obtaining the latest version of this tool, cd to `<tool-download-dir>/viya4-ark`. 

The following command provides usage details:

```
python3 viya-ark.py pre-install-report -h
```

## Report Output

The tool generates the pre-install check report, viya_pre_install_report_<timestamp>.html.  The report is in a   
web-viewable, HTML format.

## Modify CPU, Memory, and Version Settings

You can modify the <tool-download-dir>/viya4-ark/pre_install_report/viya_deployment_settings.ini file to alter the   
minimum and aggregate settings for CPU and memory on nodes. For more information, see the details in the file.

If you modify the VIYA_K8S_VERSION_MIN to a version less than the minimum Kubernetes version supported by this 
release of the report tool, you are operating outside the supported capabilities of the report tool.  SAS recommends 
using a release of SAS Viya 4 ARK tools that matches the required minimum you are working with. 
