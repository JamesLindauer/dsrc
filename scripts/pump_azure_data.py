#!/usr/bin/python2.7

import azurewrap , sys , time
import glob , os , uuid , shutil

reload(azurewrap)

if __name__ <> '__main__':
	_src = 'samples'
else:
	_src = "%s/samples/" %os.path.dirname(sys.argv[0])


dsrc = azurewrap.AzureWrapper(
		'<src_account>',
		'<src_key>',
		'<src_cont_name>',
		_src,
		True
		)

edm = azurewrap.AzureWrapper(
		'<dst_account>',
		'<dst_key>',
		'<dst_cont_name>',
		_src,
		True
		)

def clean_edm():
	map(edm.delete , edm.list())


def clean_dsrc():
	map(dsrc.delete , dsrc.list())

def clean_all():
	clean_dsrc()
	clean_edm()

def pump():
	while True:
		for _pcap in glob.glob("%s/*.pcap" %_src):
			_uuid = str(uuid.uuid1()) + '.pcap'
			shutil.copy(_pcap , "%s/%s" %( _src , _uuid ) )
			dsrc.upload(_uuid , True)
			time.sleep(2)
def help():
	sys.stderr.write("""
Usage "pump_azure_data.py" [pump|clean_dsrc|clean_edm]
	clean_edm -- Clean EDM container in Azure Storage
	clean_dar -- Clean DSRC container in Azure Storage
	pump -- pump sample data with uuid as filename
	help -- show this msg and exit
""")
	sys.exit(1)

if __name__ == '__main__':
	try:
		globals()[sys.argv[1]]()
	except(KeyError) , e:
		help()
	
