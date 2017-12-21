#!/bin/bash

function ttyok
{
	echo -ne '\033[1;32m'
	echo -n "OK - $@"
	echo -e '\033[0;0m'
}


function ttywarn
{
	echo -ne '\033[1;33m'
	echo -n "WARNING - $@"
	echo -e '\033[0;0m'

}


function ttyerror
{
	echo -ne '\033[1;31m'
	echo -n "ERROR - $@"
	echo -e '\033[0;0m'
	exit 1
}


function ttycritical
{
	echo -ne '\033[1;31m'
	echo -n "CRITICAL - $@"
	echo -e '\033[0;0m'
}


function get_inp
{			
	while true
	do
		read -p "[y|n]" _inp
		case _inp in
			y|yeah|yes|ok|Y)
				return 0
				;;
			no|n|N|nope|na)
				return 1
				;;
			*)
				#no mercy given to the installer
				#get me a yes or no.
				ttywarn "Invalid Input.. Try Again!!"
				continue
				;;
		esac
	done

}


function install_epel
{
	echo "Installing Epel"
	if rpm -qa | grep -q 'epel-release' 2>/dev/null
	then
		ttyok 'Epel Already Installed I guess..'
		return 0
	fi
	pushd $SCRIPT_DIR/deps
	if ! rpm -iUvh  epel*.rpm
	then
		ttycritical "Epel Release Installation Failed" 
		popd
		return 1
	fi
	popd
	return 0

}


function set_cache_dir
{
	#lets make the read and write for the file perpective
	#more first keeping the file in the ram
	echo "Setting Cache directory and fstab"
	mkdir /var/mod_dsrc_cache 2>/dev/null
	if df -kh |  grep -q -- 'mod_dsrc_cache' 2>/dev/null
	then
		ttyok 'Already Mount Exists . Not Gonna Mount It Again'
		return 0
	fi
		

	MOUNT_CMD="mount -t tmpfs tmpfs /var/mod_dsrc_cache -o \
		rw,size=$CACHE_MEM,nr_inodes=1k,noexec,nodev,nosuid,uid=$APACHE_USER,gid=$APACHE_GRP,mode=1700"
	APPEND_STR="
#---\n#Modification Done by DSRC J2375 encoder-decoder or PcapWatcherapplication installer\n#contact support team in case any mod required\ntmpfs   /var/mod_dsrc_cache    tmpfs  rw,size=$CACHE_MEM,nr_inodes=1k,noexec,nodev,nosuid,uid=$APACHE_USER,gid=$APACHE_GRP,mode=1700 0 0\n#---"
	echo ' Mounting tmpfs to the current running system'
	if $MOUNT_CMD
	then
		ttyok "Mounting done to the running system"
		df -kh | grep -i dsrc_cache
	else
		ttywarn "Mounting Failed"
		return 1
	fi
	echo "Persisting Setting through /etc/fstab"
	echo -e $APPEND_STR >> /etc/fstab
}


function start
{
	for _METHOD in $*
	do
		if $_METHOD
		then
			ttyok "$_METHOD Executed Successfully"
			continue
		else
			ttycritical 'Error in Previous Execution. Continue?'
			trap 'ttycritical "Abort Denied :)"' SIGINT
			if get_inp
			then
				ttywarn "Overiding.. Might loose some functionalities"
				continue
			else
				ttyok "Exitted on User Request :("
			fi
			trap '' SIGINT
		fi
	done
				
}


function testroot
{
	if ! test $UID -eq 0
	then
		ttyerror 'Only root can execute this.. Sorry :('
	fi
}
