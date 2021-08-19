# Pre-Installation Check of SAS Viya System Requirements

This tool compares your Kubernetes environment to the SAS Viya system requirements. It evaluates a number of items, such as memory, CPU cores, software versions, and permissions. The output is a web-viewable, HTML report with the results. 

SAS recommends running the tool and resolving any reported issues before beginning a SAS Viya deployment in a Kubernetes cluster.  

## Prerequisites 
- The tool should be run on a machine from which the Kubernetes command-line interface, `kubectl`, can access the Kubernetes cluster. 
- The tool requires Python 3.6 or higher.  

### Required Python Packages
SAS Viya ARK tools require third-party packages be installed before use. You can install all the required packages by using the provided requirements.txt file in the following command:

```commandline
$ python3 -m pip install -r requirements.txt
```

Download the latest version of this tool and update required packages with every new software order.

## Usage

**Note:** You must set your `KUBECONFIG` environment variable. `KUBECONFIG` must have administrator rights in the namespace where you intend to deploy your SAS Viya software.
To obtain a complete report use a `KUBECONFIG`  with administrator rights in the cluster.

Create the namespace where you plan to deploy SAS Viya.  You must specify the namespace when you run the tool. 

After obtaining the latest version of this tool, cd to `<tool-download-dir>/viya4-ark`. 

The following command provides usage details:

```
python3 viya-ark.py pre-install-report -h
```

**Note:** The tool currently expects an NGINX Ingress controller.  Other Ingress controllers are not evaluated.

### Hints

The values for the Ingress Host and Ingress Port options can be determined with kubectl commands. 
The following section provides hints for a NGINX Ingress controller of Type LoadBalancer. The following commands 
may need to be modified to suit your Ingress controller deployment.  

You must specify the namespace where the Ingress controller is available as well as the Ingress controller name:

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
$ export INGRESS_HOST=$(kubectl -n <ingress-namespace> get service <nginx-ingress-controller-name> -o jsonpath='{.status.loadBalancer.ingress[*].ip}')
$ export INGRESS_HTTP_PORT=$(kubectl -n <ingress-namespace> get service <nginx-ingress-controller-name> -o jsonpath='{.spec.ports[?(@.name=="http")].port}')
$ export INGRESS_HTTPS_PORT=$(kubectl -n <ingress-namespace> get service <nginx-ingress-controller-name> -o jsonpath='{.spec.ports[?(@.name=="https")].port}')
```
The command to determine the Ingress Host may be slightly different with Amazon Elastic Kubernetes Service(EKS):
```
$ export INGRESS_HOST=externalIP=$(kubectl -n <ingress-namespace> get service <nginx-ingress-controller-name> -o jsonpath='{.status.loadBalancer.ingress[*].hostname}')
```

Use the values gathered on the command line for http or https as appropriate for your deployment:

```
python3 viya-ark.py pre-install-report -i nginx  -H $INGRESS_HOST -p $INGRESS_HTTP_PORT 
python3 viya-ark.py pre-install-report -i nginx  -H $INGRESS_HOST -p $INGRESS_HTTPS_PORT 
```
 
## Report Output

The tool generates the pre-install check report,`viya_pre_install_report_<timestamp>.html`. The report is in a web-viewable, HTML format.

## Modify CPU, Memory, and Version Settings

You can modify the <tool-download-dir>/viya4-ark/pre_install_report/viya_check_limit.properties file to alter the minimum and aggregate settings for CPU and memory on nodes. For more information, see the details in the file.

## Known Issues

The following issue may impact the performance and expected results of this tool.
- All Nodes in a cluster must be in the READY state before running the tool.
- If all the Nodes are not in the READY state, the tool takes longer to run. Wait for it to complete.
  Also, the tool may not be able to clean up the pods and replicaset created in the specified namespace as shown in the example output below. If that happens, the pods and replicaset must be manually deleted.
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
