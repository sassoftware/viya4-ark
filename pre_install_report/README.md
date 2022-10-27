# Pre-Installation Check of SAS Viya System Requirements
## Overview
This tool compares your Kubernetes environment to the SAS Viya system requirements.  It evaluates a   
number of items, such as memory, CPU cores, software versions, and permissions. The output is a web-viewable,  
HTML report with the results. 

SAS recommends running the tool and resolving any reported issues _before_ beginning a SAS Viya 
deployment in a Kubernetes cluster.  The tool cannot account for the dynamic resource allocations that 
Kubernetes may orchestrate once Viya is deployed.  The report and the information therein must
be considered a snapshot in time.  

The Kubernetes cluster for a SAS Viya deployment must meet the requirements documented in [SAS® Viya® Operations](https://go.documentation.sas.com/doc/en/itopscdc/default/itopssr/titlepage.htm)  
Ensure that the Kubernetes version is within the documented range for the selected cloud provider. 


### Memory and vCPU Check
The tool calculates the aggregate Memory and aggregate vCPUs of your cluster. The aggregate Memory is the sum 
of the Memory capacity on all the active and running nodes. The aggregate CPU is calculated similarly.
  
There will be some percentage of Memory on each node in the cluster that is considered "overhead" (consumed by the OS, Kubelet, etc)
and therefore not be available for SAS Viya.   This tool assumes that 85% of the calculated aggregate Memory is available for SAS Viya, 
and the memory sizes in the report reflect this.  

The calculated aggregate number of vCPUs must equal or exceed the required aggregate number of vCPUs for your deployment offering. 
The requirements per offering are detailed in the _Hardware and Resource Requirements_ section of the SAS Viya Operations document. 
The required Memory and vCPUs sizes depend on the instance type used for the node.  

Your required aggregates must be specified in the following file  
<tool-download-dir>/viya4-ark/pre_install_report/viya_deployment_settings.ini  
Example:
```
# Total Memory of all worker Nodes in GB. Sum of the Memory on all active node required to deploy a specific offering.
# Set value for required for offering
VIYA_MIN_AGGREGATE_WORKER_MEMORY=448G
# Total CPU of all worker Nodes in millicores.  Sum of the vCPUs on all active node required to deploy a specific offering.
# Minimum allowed value = '.001'. 
VIYA_MIN_AGGREGATE_WORKER_CPU_CORES=56
```

If calculated aggregate memory is less than a percentage (85%) of VIYA_MIN_AGGREGATE_WORKER_MEMORY then the tool will flag a memory issue.  
If calculated aggregate vCPUs is less than VIYA_MIN_AGGREGATE_WORKER_CPU_CORES then the tool will flag a CPU issue.
 
SAS recommends using the SAS Viya 4 Infrastructure as Code (IaC) tools to create a cluster.  
Refer to the following IaC repositories for [Microsoft Azure](https://github.com/sassoftware/viya4-iac-azure), [AWS](https://github.com/sassoftware/viya4-iac-aws]), [GCP](https://github.com/sassoftware/viya4-iac-gcp) or [Open Source Kubernetes](https://github.com/sassoftware/viya4-iac-k8s)   
For OpenShift refer to the documentation in SAS® Viya® Operations [OpenShift](https://go.documentation.sas.com/doc/en/itopscdc/v_019/itopssr/n1ika6zxghgsoqn1mq4bck9dx695.htm#p1c8bxlbu0gzuvn1e75nck1yozcn)  
  
Example: See Sizing Recommendations for a Microsoft Azure deployment under [Hardware and Resource Requirements](https://go.documentation.sas.com/doc/en/itopscdc/v_028/itopssr/n0ampbltwqgkjkn1j3qogztsbbu0.htm). You can use this information to calculate VIYA_MIN_AGGREGATE_WORKER_MEMORY and VIYA_MIN_AGGREGATE_WORKER_CPU_CORES.

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

**Note:** You must set your `KUBECONFIG` environment variable. `KUBECONFIG` must have administrator rights to the   
cluster where you intend to deploy your SAS Viya software.
To obtain a complete report use a `KUBECONFIG` with administrator rights in the cluster.  Otherwise, the report will   
not be able to evaluate items such as memory, CPU cores, software versions and other node details. It is not useful   
for determining if you are ready to deploy your SAS Viya software.

Create the namespace where you plan to deploy SAS Viya.  A namespace is required to run this tool. Specify the namespace where you plan to deploy SAS Viya using the namespace option. If a namespace is not provided, the tool will check the current context for a namespace. Ensure that you are running with the correct namespace.   

After obtaining the latest version of this tool, cd to `<tool-download-dir>/viya4-ark`. 

The following command provides usage details:

```
python3 viya-ark.py pre-install-report -h
```

### Supported Ingress Values   
The tool currently supports the following ingress controllers: _nginx, openshift_.    
Other ingress controllers are not evaluated.  Select _openshift_ if you are deploying on Red Hat OpenShift.

### Hints
**Note:**  The values for the Ingress Host and Port values are not required if you specify an ingress value   
of _openshift_.  The Ingress Host and Port values must be specified if you specify an ingress
value of _nginx_.  

The values for the Ingress Host and Ingress Port options can be determined with kubectl commands.   

The following section provides hints for a _nginx_ ingress controller of Type LoadBalancer.
The following commands may need to be modified to suit your ingress controller deployment. 

You must specify the namespace where the ingress controller is available as well as the ingress controller name:

```
kubectl -n <nginx-ingress-namespace> get svc <nginx-ingress-controller-name> 
```

  
Here is sample output from the command: 

```
NAME                                 TYPE           CLUSTER-IP    EXTERNAL-IP     PORT(S)                      AGE
ingress-nginx-controller             LoadBalancer   10.0.00.000   55.147.22.101   80:31254/TCP,443:31383/TCP   28d
```

Use the following commands to determine the parameter values:

```
export INGRESS_HOST=$(kubectl -n <ingress-namespace> get service <nginx-ingress-controller-name> -o jsonpath='{.status.loadBalancer.ingress[*].ip}')
export INGRESS_HTTP_PORT=$(kubectl -n <ingress-namespace> get service <nginx-ingress-controller-name> -o jsonpath='{.spec.ports[?(@.name=="http")].port}')
export INGRESS_HTTPS_PORT=$(kubectl -n <ingress-namespace> get service <nginx-ingress-controller-name> -o jsonpath='{.spec.ports[?(@.name=="https")].port}')
```
The command to determine the Ingress Host may be slightly different with Amazon Elastic Kubernetes Service(EKS):
```
export INGRESS_HOST=externalIP=$(kubectl -n <ingress-namespace> get service <nginx-ingress-controller-name> -o jsonpath='{.status.loadBalancer.ingress[*].hostname}')
```

Use the values gathered on the command line for http or https as appropriate for your deployment:

```
python3 viya-ark.py pre-install-report -i nginx  -H $INGRESS_HOST -p $INGRESS_HTTP_PORT 
python3 viya-ark.py pre-install-report -i nginx  -H $INGRESS_HOST -p $INGRESS_HTTPS_PORT 
```
 
## Report Output

The tool generates the pre-install check report, viya_pre_install_report_<timestamp>.html.  The report is in a   
web-viewable, HTML format.

## Modify CPU, Memory, and Version Settings

You can modify the <tool-download-dir>/viya4-ark/pre_install_report/viya_deployment_settings.ini file to alter the   
minimum and aggregate settings for CPU and memory on nodes. For more information, see the details in the file.

## Known Issues

The following issue may impact the performance and expected results of this tool.
- All Nodes in a cluster must be in the READY state before running the tool.
- If all the Nodes are not in the READY state, the tool takes longer to run. Wait for it to complete.  
Also, the tool may not be able to clean up the pods and replicaset created in the specified namespace as shown in   
  the example output below. If that happens, the pods and replicaset must be manually deleted.  
They will look similar to the resources shown below:
```    
    NAME                               READY   STATUS    RESTARTS   AGE
    pod/hello-world-6665cf748b-5x2jq   0/1     Pending   0          115m
    pod/hello-world-6665cf748b-tkq79   0/1     Pending   0          115m

    NAME                                     DESIRED   CURRENT   READY   AGE
    replicaset.apps/hello-world-6665cf748b   2         2         0       115m

    Suggested commands to delete resources before running the tool again:
        kubectl -n <namespace> delete replicaset.apps/hello-world-6665cf748b
        kubectl -n <namespace> delete pod/hello-world-6665cf748b-5x2jq
        kubectl -n <namespace> delete pod/hello-world-6665cf748b-tkq79
```    
