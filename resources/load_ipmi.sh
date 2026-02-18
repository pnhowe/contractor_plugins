#!/bin/sh

set -e

echo "Got base path at '$1'"
echo "Got curent version of '$2'"
echo "Got previsous version of '$3'"

echo "Enabeling IPMI plugin..."
/usr/lib/contractor/util/pluginctl --builder=IPMIFoundation --enable /usr/lib/python3/dist-packages/contractor_plugins/IPMI

echo "Loading Schema..."
/usr/lib/contractor/util/manage.py migrate IPMI

echo "Loading Base data..."
/usr/lib/contractor/util/blueprintLoader ${1}usr/lib/contractor/resources/ipmi.toml
