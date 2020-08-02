#!/bin/sh

set -e

echo "Got base path at '$1'"
echo "Got curent version of '$2'"
echo "Got previsous version of '$3'"

echo "Enabeling Manual plugin..."
/usr/lib/contractor/util/pluginctl --builder=ManualFoundation --builder=ManuialComplex --builder=ManuialCompleedFoundation --enable /usr/lib/python3/dist-packages/contractor_plugins/Manual

echo "Loading Schema..."
/usr/lib/contractor/util/manage.py migrate Manual

echo "Loading Base data..."
/usr/lib/contractor/util/blueprintLoader ${1}usr/lib/contractor/resources/manual.toml
