#!/bin/bash


APACHE_USER=
APACHE_GRP=
CACHE_MEM=


METHODS='
install_epel
install_deps
get_inputs
get_pip_deps
set_mod_python
set_j2373_binary
set_cache_dir
'


function get_pip_deps
{
	pip install xmltodict dpkt
}

function get_inputs
{
	read -p "Apache UserName:" APACHE_USER
	read -p "Apache GroupName:" APACHE_GRP
	read -p "Mem Alloc Size[G|M]:" CACHE_MEM
}


function install_deps
{
	echo "Installing repository based deps"
	yum install httpd mod_authnz_external pwauth mod_ssl mod_python python-pip -y
	return 0

}


function set_mod_python
{
	pushd $SCRIPT_DIR/mod_python
	cp -prfv dsrc /var/www/html/
	chown $APACHE_USER.$APACHE_GRP /var/www/html/ -R -v
	cp dsrc.conf /etc/httpd/conf.d/ -v
	cp mod_dsrc.conf /etc/ -v
	useradd dsrcusers -M -s /sbin/nologin
	groupadd dsrc-pcap-uploaders
	usermod -G dsrc-pcap-uploaders -a dsrcusers
	passwd dsrcusers
	popd
	return 0
}


function set_j2373_binary
{
	yum groupinstall "Development Tools" -y
	if ! tar -xzf SCRIPT_DIR/ASNC/asn1c.tar.gz -C SCRIPT_DIR/ASNC/
	then
		return 1
	fi
	pushd $SCRIPT_DIR/ASNC/asn1c/

	if autoreconf -iv
	then
		./configure
	else
		ttywarn "AutoReconf Failed"
		return 1
	fi

	if make >> makelog.log
	then
		pushd examples/sample.source.J2735/
		make
		cp j2735-dump /usr/bin/j2735-encoder-decoder
		chown $APACHE_USER.$APACHE_GRP /usr/bin/j2735-encoder-decoder
		popd
	else
		ttycritical "Make Failed ... check  $SCRIPT_DIR/ASNC/asnc/makelog.log"
		return 1
	fi
	make clean
	popd
	return 0
	
}



