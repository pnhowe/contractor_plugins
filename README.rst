Contractor Plugins
==================

These plugins give subcontractor the ability to do things.
Which plugins depend on network access, network permissions, 
and design coderations.  For example, the network that has 
access to the IPMI's of the baremetal servers probably does
not also have access to vCenter.  So a instance in the
vCenter network would have the vcenter plugin and iputils
(for ping/socket tests of the installed vms) and another
instance in the out of band managment network would have
the IPMI and iputils (for ping testing the IPMI interfaces).
This way network segmentation can be maintained.  Each instance
will need HTTP(s) which can be proxied back to contractor.


see http://t3kton.github.io

Plugins
=======

Manual (Foundation)
-------------------

This foundation type is for servers that do not have an out of band power controll
system, such as IPMI or DRAC, or you do not want to have contractor automatically
powering on/off your target server.  Each time contractor needs to know the power
state or to have the server powered on/off, it will prompt the user on the jobs
page for the server to be powered on and off, and then the user must resume the
job when the prompted actions are done.

VirtualBox (Foundation)
-----------------------

This foundation type is for creating vms in VirtualBox (by Oracle).  The python
virtual box bindings will need to be installed (for ubuntu/debian the bindings
are included in the virtualbox package)

IpUtils
-------

Utilities for various IP related tasks, suchas iputils.wait_for_port and iputils.ping
