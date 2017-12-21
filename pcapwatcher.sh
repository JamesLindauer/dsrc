#!/bin/bash


METHODS='
python_deps
python_install
get_pip
install_app_deps
install_app
set_cache
'

PREFIX_DIR=


function python_deps
{
	yum install openssl-devel zlib-devel libcurl-devel -y
}


function python_install
{
	tar -xzf $SCRIPT_DIR/deps/Python-2.7.13.tar.gz -C $SCRIPT_DIR/deps/
	pushd $SCRIPT_DIR/deps/Python*
	read -p "INSTALL DIR:" prefix
	PREFIX_DIR=${prefix:-/opt/}
	mkdir -p $PREFIX_DIR 2>/dev/null 
	if ! ./configure --prefix=$PREFIX_DIR 
	then
		popd
		return 1
	fi
	if make && make install > makelog.log 2>&1
	then
		ln -s $PREFIX_DIR/bin/python2.7 /usr/bin/
		popd
		return 0
	fi
	ttyerror "Check $PWD/makelog.log"
	popd
	return 1
		
}


function get_pip
{
	
	if $PREFIX_DIR/bin/python2.7 $SCRIPT_DIR/deps/get-pip.py
	then
		ln -s $PREFIX_DIR/bin/pip2.7 /usr/bin/	
		return 0
	fi
	return 1


}


function install_app_deps
{

	pip2.7 install azure-storage-blob || return 1
	pip2.7 install pycurl || return 1
	return 0
}



function install_app
{
	pushd $SCRIPT_DIR
	read -p "INSTALL DIR:" prefix
	PREFIX_DIR=${prefix:-/opt/}
	mkdir -p $PREFIX_DIR 2>/dev/null 
	cp -rfv PcapWatcher/* $PREFIX_DIR/
	ln -s $PREFIX_DIR/pcapwatcherd /etc/init.d/
	popd
	return 0

}


function set_cache
{
	set_cache_dir
	return $?
}

