
import azurewrap as _aw
import time , sys

class WatcherExitException(Exception):
	pass


class Watcher(object):
	#list if mandate fields . withouth these entries
	#lets not proceed further
	__mandates = [ 
			"cache_dir",
			"azure_containers",
			"sleep"
		     ]

	__config = None
	__az_objs = []
	__logger = None
	__test='I am just a junk string'

	def __log(self ,_debug ,  _msg ):
		if self.__logger:
			try:
				func_pointer = getattr(self.__logger , _debug )
			except:
				_msg+="\n"
				func_pointer = sys.stderr.write
				
			func_pointer(_msg)
	

	def __validate(self):
		self.__log("info" , "Validation For Config Gonna Start")
		#validate with all madate fields
		if set(self.__mandates) - set(self.__config.keys()) != set([]):
			raise WatcherExitException , "Validation Failed For Config"
		
		
	def __scan(self , _az_obj):
		self.__log("debug" , "Scaning Gonna Start")
		return _az_obj.list(r'.*\.(pcap|hex)$')

		
	def __init__(self, _watcher_config , _logger=False):
		self.__config = _watcher_config
		self.__logger = _logger
		self.__validate()
		count=0
		self.__log( "info" , "Setting Azure Objects")

		#create objects for each container provided
		#in the config .
		if not self.__config['azure_containers']:
			raise WatcherExitException , "No Container Config To Process"
		for _az_config in self.__config['azure_containers']:
			self.__log("debug" , "Creating Config:%s" %repr(_az_config) )
			#shortcut validation  of sub attributes in config
			# through try and key error exception
			try:
				#append azure wrapper created objects to 
				#later operations on each objects
				self.__az_objs.append(
						_aw.AzureWrapper(
							_az_config["account_name"],
							_az_config["account_key"],
							_az_config["container"],
							self.__config['cache_dir'],
							self.__logger,
							_az_config["compression"],
							_az_config["decompression"]
						)
				)
			except(KeyError) , e:
				self.__log('critical' , "Missing Attribs:%s" %str(e))
				#check whether ther are any containers to be processed
				#if not then raise the exception
				if count == len(self.__config['azure_containers']):
					self.__log("error" , "No Azure Containers That I Can Process")
					self.__log("error" , "Sorry Will Raise Exception" )
					raise WatcherExitException , "No Container Config To Process"
				count+=1
				pass
			
		self.__log( "info" , "Initing For Object Done")


	def set_test_loop(self , _iter):
		"""
		Do not continue more than x  iterations
		This is only recommended for testing purpose
		"""
		self.__test=_iter

	
	
	def worker_init(self , _queue):
		while True:
			if type(self.__test) == int:
				self.__test-=1
			self.__log("debug" , "Starting Next Polling")
			for _az_obj in self.__az_objs:
				for _file in self.__scan(_az_obj):
					self.__log("info" , "Adding %s to Queue"  %_file)
					#lets move the files state as we started processing
					#append the moved file name queue
					#queue here is multiprocessing.JoinableQueue
					_rename_file  = "%s.inprocessing" %_file
					_az_obj.move(_file , _rename_file)
					_queue.put( (_az_obj.get_config(), _rename_file))
			self.__log(
				"debug",
				"Sleeping %d Seconds Before Next Poll" %self.__config["sleep"]
				)
			time.sleep(self.__config["sleep"])
			if self.__test > 0:
				continue
			else:
				break
				
		
