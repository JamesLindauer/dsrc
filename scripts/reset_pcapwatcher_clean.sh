#!/bin/bash
ps -eaf | grep pcap  | grep -v -e grep -e reset
ps -eaf | grep pcap  | grep -v -e grep -e reset | awk '{print $2}' | xargs -i kill -9  {}
cat /dev/null > ../PcapWatcher/var/log/pcapwatcher.log
rm -f ../PcapWatcher/var/run/pcapwatcher.lock
ps -eaf | grep pcap  | grep -v -e grep -e reset

