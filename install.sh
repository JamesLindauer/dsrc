#!/bin/bash


SCRIPT_DIR=$( dirname $0 )

if test -e $SCRIPT_DIR/commons.sh
then
	source $SCRIPT_DIR/commons.sh
else
	echo "$SCRIPT_DIR/commons.sh can't be sourced" 1>&2
	exit 1
	
fi

function sourceandstart
{
	source $1
	start $METHODS

}

function helpme
{
	ttywarn "
Usage $( basename $0 ): [pcapwatcher|moddsrc|help]

Options:
	pcapwatcher : Install only PcapWatcher and it's dependencies
	moddsrc :  Install only ModDSRC modules and it's dependencies
	all : Install both PcapWatcher and ModDSRC
	help -h --help : Show this message and exit
" | sed 's/WARNING -//'
	exit 1
}





case $1 in
	pcapwatcher|moddsrc)
		testroot
		sourceandstart $SCRIPT_DIR/$1.sh
		;;
	all)
		testroot
		sourceandstart $SCRIPT_DIR/moddsrc.sh
		sourceandstart $SCRIPT_DIR/pcapwatcher.sh
		exit 0
		;;
	
	help|-h|--help|*)
		helpme
		;;
esac


