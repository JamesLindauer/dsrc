#!/bin/bash

sudo service httpd stop
sudo service pcapwatcherd stop

sudo rm -rvf /opt/PcapWatcher/ /opt/Python2.7 /usr/bin/python2.7 \
	    /usr/bin/pip2.7 /var/www/html/dsrc/ /etc/init.d/pcapwatcherd  \
	    /etc/httpd/conf.d/dsrc.conf /etc/mod_dsrc.conf


sudo service httpd start

	    
	    






