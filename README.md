# bright-cluster-scaling-profitbricks
Dynamically scale your Bright Computing managed cluster on the Profitbricks platform by adding or removing resources according to your current workload.


## Overview
Bright Computing Cluster Manager's (BCM) included cluster scaling provides a mechanism to dynamically turn on or off additional computing nodes, depending on the current workload.
In a ProfitBricks cloud this mechanism can be extended in a way that virtual nodes may even be created or destroyed. This dynamic scaling thus helps to reduce costs for High Performance Computing and BigData Clusters.

The solution in this repository can easily be installed on a Bright cluster head node and contains the configuration files and scripts to
- dynamically create and remove nodes,
- dynamically power on and power off nodes.
You may as well have some nodes which are always up and running.


## Prerequisites

- You have created a virtual data center.
- You have created a virtual server in the data center with two NICs.
- You have installed BCM on the server and got a valid license.

For the following it is assumed,
- that you used default values during installation,
- that your external net is LAN #1 with a public IP,
- that your internal net is LAN #2 with DHCP disabled.

 
## Installation
The ProfitBricks python SDK must be installed:

	yum update
	yum install python-pip
	pip install profitbricks

Download the repository and put the folder `profitbricks/` in directory `/cm/local/` on the head node.

## Configuration of BCM
For using Bright's power operations, the managed nodes must already be known. Create as many nodes as you need in BCM. 
You can use the cluster manager shell `cmsh` to do this. Don't forget to check if you have sufficient resources at PofitBricks.
 
Add all the nodes to manage to a new node group, say 'pbnodes'. For example, using `cmsh`:

	[cmsh] nodegroup
	[cmsh] add pbnodes
	[cmsh] append nodes node01..node05
	[cmsh] commit

For all of these nodes, that you want to turn on or off, activate custom power control, for example for nodes node02 to node05:

	[cmsh] device
	[cmsh] foreach -n node02..node05 (set powercontrol custom; set custompowerscript /cm/local/profitbricks/bin/pbpowerscript)
	[cmsh] commit

So, node01 is in the same node group 'pbnodes', but not subject to power operations.

To differentiate between power on/off and create/remove a node, you can use the node's `custompowerscriptargument`.
For all of the nodes, that you want to create or destroy, set this property to 'volatile', e.g. for node04 and node05:

	[cmsh] device
	[cmsh] foreach -n node04..node05 (set custompowerscriptargument volatile)
	[cmsh] commit

If this property is not set, the node will only be powered on or off.

By default, CMDaemon has a timeout of 20 seconds, which also affects custom power operations.
However, this timeout may not be sufficient if there are too many provisioning requests queued at ProfitBricks.
Thus, the timeout must be increased to the maximum value of 120 seconds:

1. Add

`AdvancedConfig = { "CustomPowerTimeout=120" }`

to file `/cm/local/apps/cmd/etc/cmd.conf`.

2. Restart CMDaemon by

`systemctl restart cmd.service`

## Configuration of cluster scaling
This solution uses ProfitBricks' Cloud API. To avoid providing your ProfitBricks account data on the command line, you can use a login configuration file.
Call

	python -u  /cm/local/profitbricks/bin/pb_saveLoginFile.py -u <user> -p <password> -L <loginfile>

to create this file.
All scripts are already prepared to use this file instead of user and password arguments.

The custom power script `pbpowerscript` uses the configuration file `pb-powerscript.conf`, located in `profitbricks/etc/`:

	# config file for setting up BC/PB cluster
	# change settings to your own need
	PB_LOGIN_CONF=/cm/local/profitbricks/etc//MyLogin.conf
	PB_DCID=909c5078-057c-4189-8f24-578a70f22b6a
	PB_LANID=2
	PB_CREATE_CPU=2
	PB_CREATE_RAM=2
	PB_CREATE_STORAGE=10

`PB_LOGIN_CONF` contains the path to a file with encoded credentials, used for login at ProfitBricks API.  
`PB_DCID` contains the ID of the virtual data center, where the cluster nodes reside.  
`PB_LANID` contains the ID of the VDC LAN for internalnet, where nodes should connect to.  
`PB_CREATE_CPU`, `PB_CREATE_RAM`, `PB_CREATE_STORAGE` contain the number of CPUs, RAM [in GB], storage size [in GB], respectively, for creation of new nodes.  

You should change the settings according to your needs.

The cluster scaling by `cm-scale-cluster` uses the configuration file `pb-scale-cluster.conf`, located in `profitbricks/etc/`:

	QUEUE=defq NODEGROUP=pbnodes
	DEBUG = YES
	WORKLOAD_MANAGER = slurm
	LOG_FILE  = /var/log/cm-scale-cluster.log
	LOCK_FILE = /var/lock/subsys/cm-scale-cluster
	SPOOL_DIR = /var/spool/cmd
	#PARALLEL_REQUESTS = 10
 
You can change `NODEGROUP` to the value you chose when creating the node group. 
You can change `PARALLEL_REQUESTS` to limit the power operations performed in one call of `cm-scale-cluster`.
All other values should fit to the default installation and need not to be changed.

## Execution
You can directly call `pbpowerscript` to test the power operations:

	/cm/local/profitbricks/bin/pbpowerscript {'STATUS'|'ON'|'OFF'|'RESET'} <node> ['volatile']

Executing the power operations is also possible in Bright's cmgui. You can use the power buttons available in a node's task tab.

To test dynamic scaling, Bright provides the tool `cm-fake-job` to simulate a workload.
The tool is located in `/cm/local/apps/cm-scale-cluster/scripts/` and can be configured by a configuration file with following content:

	WORKLOAD_MANAGER = slurm
	QUEUE = defq
	STATUS = PENDING
	NODES_NUMBER = 1
	PROCESSES_NUMBER = 1


Calling

	/cm/local/apps/cm-scale-cluster/bin/cm-scale-cluster –c /cm/local/profitbricks/etc/pb-scale-cluster.conf

manually will turn nodes on or off, according to the current workload.

For automated scaling, `cm-scale-cluster` execution should be configured as cron job.

