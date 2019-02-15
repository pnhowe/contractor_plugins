VERSION := 0.1

version:
	echo $(VERSION)

all:
	./setup.py build

install:
	./setup.py install --root $(DESTDIR) --install-purelib=/usr/lib/python3/dist-packages/ --prefix=/usr --no-compile -O0

test-requires:
	python3-pytest python3-pytest-cov python3-pytest-django python3-pytest-mock

test:
	py.test-3 -x --cov=contractor_plugins --cov-report html --cov-report term -vv contractor_plugins

clean:
	./setup.py clean
	$(RM) -fr build
	$(RM) -f dpkg
	$(RM) -fr htmlcov
	dh_clean

.PHONY:: test-requires test clean

respkg-distros:
	echo xenial

respkg-requires:
	echo respkg

respkg:
	cd resources && respkg -b ../contractor-plugins-ipmi_$(VERSION).respkg       -n contractor-plugins-ipmi       -e $(VERSION) -c "Contractor Plugins - IPMI"       -t load_ipmi.sh       -d ipmi       -s contractor-os-base
	cd resources && respkg -b ../contractor-plugins-amt_$(VERSION).respkg        -n contractor-plugins-amt        -e $(VERSION) -c "Contractor Plugins - AMT"        -t load_amt.sh        -d amt        -s contractor-os-base
	cd resources && respkg -b ../contractor-plugins-docker_$(VERSION).respkg     -n contractor-plugins-docker     -e $(VERSION) -c "Contractor Plugins - Docker"     -t load_docker.sh     -d docker     -s contractor-os-base
	cd resources && respkg -b ../contractor-plugins-manual_$(VERSION).respkg     -n contractor-plugins-manual     -e $(VERSION) -c "Contractor Plugins - Manual"     -t load_manual.sh     -d manual     -s contractor-os-base
	cd resources && respkg -b ../contractor-plugins-vcenter_$(VERSION).respkg    -n contractor-plugins-vcenter    -e $(VERSION) -c "Contractor Plugins - Vcenter"    -t load_vcenter.sh    -d vcenter    -s contractor-os-base
	cd resources && respkg -b ../contractor-plugins-virtualbox_$(VERSION).respkg -n contractor-plugins-virtualbox -e $(VERSION) -c "Contractor Plugins - VirtualBox" -t load_virtualbox.sh -d virtualbox -s contractor-os-base
	cd resources && respkg -b ../contractor-plugins-iputils_$(VERSION).respkg    -n contractor-plugins-ipuils     -e $(VERSION) -c "Contractor Plugins - IpUtils"    -t load_iputils.sh    -d iputils
	touch respkg

respkg-file:
	echo $(shell ls *.respkg)

.PHONY:: respkg-distros respkg-requires respkg respkg-file

dpkg-distros:
	echo xenial

dpkg-requires:
	echo dpkg-dev debhelper python3-dev python3-setuptools

dpkg:
	dpkg-buildpackage -b -us -uc
	touch dpkg

dpkg-file:
	echo $(shell ls ../contractor-plugins_*.deb):xenial

.PHONY:: dpkg-distros dpkg-requires dpkg dpkg-file
