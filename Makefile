VERSION := $(shell head -n 1 debian/changelog | awk '{match( $$0, /\(.+?\)/); print substr( $$0, RSTART+1, RLENGTH-2 ) }' | cut -d- -f1 )

all:
	./setup.py build

install:
	./setup.py install --root=$(DESTDIR) --install-purelib=/usr/lib/python3/dist-packages/ --prefix=/usr --no-compile -O0

version:
	echo $(VERSION)

clean:
	./setup.py clean || true
	$(RM) -r build
	$(RM) dpkg
	$(RM) -r htmlcov
	$(RM) *.respkg
	$(RM) respkg
	dh_clean || true

dist-clean: clean

.PHONY:: all install version clean dist-clean

test-distros:
	echo ubuntu-xenial

test-requires:
	echo flake8 python3-pytest python3-pytest-cov python3-pytest-django python3-pytest-mock

lint:
	flake8 --ignore=E501,E201,E202,E111,E126,E114,E402 --statistics --exclude=migrations .

test:
	py.test-3 -x --cov=contractor_plugins --cov-report html --cov-report term -vv contractor_plugins

.PHONY:: test-distros test-requres test

respkg-distros:
	echo ubuntu-xenial

respkg-requires:
	echo respkg fakeroot

respkg:
	cd resources && fakeroot respkg -b ../contractor-plugins-ipmi_$(VERSION).respkg       -n contractor-plugins-ipmi       -e $(VERSION) -c "Contractor Plugins - IPMI"       -t load_ipmi.sh       -d ipmi       -s contractor-os-base
	cd resources && fakeroot respkg -b ../contractor-plugins-amt_$(VERSION).respkg        -n contractor-plugins-amt        -e $(VERSION) -c "Contractor Plugins - AMT"        -t load_amt.sh        -d amt        -s contractor-os-base
	cd resources && fakeroot respkg -b ../contractor-plugins-docker_$(VERSION).respkg     -n contractor-plugins-docker     -e $(VERSION) -c "Contractor Plugins - Docker"     -t load_docker.sh     -d docker     -s contractor-os-base
	cd resources && fakeroot respkg -b ../contractor-plugins-manual_$(VERSION).respkg     -n contractor-plugins-manual     -e $(VERSION) -c "Contractor Plugins - Manual"     -t load_manual.sh     -d manual     -s contractor-os-base
	cd resources && fakeroot respkg -b ../contractor-plugins-vcenter_$(VERSION).respkg    -n contractor-plugins-vcenter    -e $(VERSION) -c "Contractor Plugins - VCenter"    -t load_vcenter.sh    -d vcenter    -s contractor-os-base
	cd resources && fakeroot respkg -b ../contractor-plugins-proxmox_$(VERSION).respkg    -n contractor-plugins-proxmox    -e $(VERSION) -c "Contractor Plugins - Proxmox"    -t load_proxmox.sh    -d proxmox    -s contractor-os-base
	cd resources && fakeroot respkg -b ../contractor-plugins-virtualbox_$(VERSION).respkg -n contractor-plugins-virtualbox -e $(VERSION) -c "Contractor Plugins - VirtualBox" -t load_virtualbox.sh -d virtualbox -s contractor-os-base
	cd resources && fakeroot respkg -b ../contractor-plugins-azure_$(VERSION).respkg      -n contractor-plugins-azure      -e $(VERSION) -c "Contractor Plugins - Azure"      -t load_azure.sh      -d azure      -s contractor-os-base
	cd resources && fakeroot respkg -b ../contractor-plugins-iputils_$(VERSION).respkg    -n contractor-plugins-ipuils     -e $(VERSION) -c "Contractor Plugins - IpUtils"    -t load_iputils.sh    -d iputils
	touch respkg

respkg-file:
	echo $(shell ls *.respkg)

.PHONY:: respkg-distros respkg-requires respkg respkg-file

dpkg-distros:
	echo ubuntu-xenial

dpkg-requires:
	echo dpkg-dev debhelper python3-dev python3-setuptools

dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

dpkg-file:
	echo $(shell ls ../contractor-plugins_*.deb):xenial

.PHONY:: dpkg-distros dpkg-requires dpkg dpkg-file
