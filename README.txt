
PREREQUISITES
------------------------------------------------------
	[Environ]
	---------
apache/httpd  -- middleware service for http
mod_python -- apache python support
mod_ssl -- secure socket layer for apache
pwauth -- pluggable authentication module for unix based users and passwd
mod_authnz_external -- extention of the previous one
	[Python]
	--------
xmltodict -- convert xml to dict object (https://github.com/martinblech/xmltodict)
dpkt -- pcap reader for UDP (https://github.com/kbandla/dpkt)
	[J2375]
	-------
asn1c - compile asn.1 schema for J2375 SAE and produce the encoder and decoder 
				(https://github.com/vlm/asn1c)
	[PcapWatcher]
	-------------
Python2.7 - 
pip2.7 - 
libcurl-devel -
pycurl -
azure-blob-storage -







INSTALL
----------------------------------------------------
./install.sh and follow the instructions and input appropriate
values




CONFIGURATION
----------------------------------------------------
/etc/httpd/conf.d/dsrc.conf
/etc/mod_dsrc.conf
<PREFIX_INSTALL>/etc/pcapwatcher.cnf





	










