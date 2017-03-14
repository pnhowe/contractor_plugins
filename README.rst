Contractor Plugins
==================

This contains the core plugins for contractor.


Installation
------------

after installing the python source, you will need to enable the plugins you would
like to use in the django settings.py for contractor.

In the INSTALLED_APPS section, add the desired plugins you would like to use after
'contractor.SubContractor'

for example::

  INSTALLED_APPS = (
      'contractor.User',
      'contractor.Site',
      'contractor.BluePrint',
      'contractor.Building',
      'contractor.Utilities',
      'contractor.Foreman',
      'contractor.SubContractor',
      'contractor_plugins.Manual',
      'contractor_plugins.VirtualBox',
      'django.contrib.admin',
      'django.contrib.auth',
      'django.contrib.contenttypes',
      'django.contrib.sessions',
      'django.contrib.messages',
      'django.contrib.staticfiles',
  )

That is is how your INSTALLED_APPS should look with the  Manual and  VirtualBox
plugins installed.

After that you need to run the django migrate app to create the database tables
for thoes enabled plugins::

  cd /usr/local/contractor/utils
  ./manage migrate

NOTE: if migrate has not been run for contractor it's self yet, that will also
create the database for contractor.  For help configuring contractor for
database access see the contractor README

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
