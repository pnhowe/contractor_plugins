#!/bin/sh

set -e

echo "Got base path at '$1'"
echo "Got curent version of '$2'"
echo "Got previsous version of '$3'"

echo "Enabeling VCenter plugin..."
/usr/lib/contractor/util/pluginctl --builder=VCenterFoundation --builder=VCenterComplex --enable /usr/lib/python3/dist-packages/contractor_plugins/VCenter

echo "Loading Schema..."
/usr/lib/contractor/util/manage.py migrate VCenter

echo "Loading Base data..."
/usr/lib/contractor/util/blueprintLoader ${1}usr/lib/contractor/resources/vcenter.toml
