#!/bin/sh

set -e

echo "Got base path at '$1'"
echo "Got curent version of '$2'"
echo "Got previsous version of '$3'"

echo "Enabeling Test plugin..."
/usr/lib/contractor/util/pluginctl --builder=TestFoundation --builder=TestComplex --builder=TestCompleedFoundation --enable /usr/lib/python3/dist-packages/contractor_plugins/Test

echo "Loading Schema..."
/usr/lib/contractor/util/manage.py migrate Test

echo "Loading Base data..."
/usr/lib/contractor/util/blueprintLoader ${1}usr/lib/contractor/resources/test.toml
