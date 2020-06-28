#!/bin/sh

set -e

echo "Got base path at '$1'"
echo "Got curent version of '$2'"
echo "Got previsous version of '$3'"

echo "Enabeling VirtualBox plugin..."
/usr/lib/contractor/util/pluginctl --builder=VirtualBoxFoundation --builder=VirtaulBoxComplex --enable /usr/lib/python3/dist-packages/contractor_plugins/VirtualBox

echo "Loading Schema..."
/usr/lib/contractor/util/manage.py migrate VirtualBox

echo "Loading Base data..."
/usr/lib/contractor/util/blueprintLoader ${1}usr/lib/contractor/resources/virtualbox.toml
