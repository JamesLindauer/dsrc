import sys , os  , re
import pycurl , StringIO
import azurewrap as _aw
import json , gzip

class RequestWorkerExp(Exception):
	pass


class Requester():
	__mandates = [
		'cache_dir',
		'azure_containers',
		'url',
		'user',
		'passwd',
		]

	#at this point there are no default headers
	#may be later if mod_python has some chages
	#and requests for specific static header 
	#you can set it from here
	__default_headers = {}
	__headers = {}
	__az_objs = []
	__logger = False
	__test = 'i am just a junk string to hold type str'

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
			raise RequestWorkerExp , "Validation Failed For Config"
	

	def __clean(self):
		self.__pycurl = pycurl.Curl()
		self.__response_body = StringIO.StringIO()
		self.__response_header = StringIO.StringIO()
		self.__err_code = 200
		self.__src_file = ''
		self.__json_fname = ''
		self.__json  =  {
			"errnum" : 500,
			"errstr" : "Something SomeWhere Wrong , Time to raise a incident ticket"
		}


	def __request(self):
		## for the request using pycurl
		#return error cod
		self.__pycurl = pycurl.Curl()
		#prepare for pycurl data
		_headers = map( 
					lambda x,y: '%s: %s' %(x,y),
					self.__headers.items()
				   )
		_usrpwd = "%s:%s" %(self.__config["user"] , self.__config["passwd"])

		_form_atttach = [
							(
								'file' ,
										( 
										self.__pycurl.FORM_FILE,
										self.__src_file
										)
								)
						 ]

		self.__log("info" , "Preparing Request for %s"  %self.__src_file )	
		#Let the pycurl formulation begin
		self.__pycurl.setopt(self.__pycurl.HTTPHEADER ,_headers)
		self.__pycurl.setopt(self.__pycurl.URL , self.__config["url"])
		self.__pycurl.setopt(self.__pycurl.HTTPAUTH, pycurl.HTTPAUTH_BASIC)
		self.__pycurl.setopt(self.__pycurl.USERPWD , _usrpwd)
		#this is a post request of time form data
		self.__pycurl.setopt(self.__pycurl.POST ,  1)
		self.__pycurl.setopt(self.__pycurl.FOLLOWLOCATION , 1)

		#set the callbacks for HEADER and BODY data
		self.__pycurl.setopt(self.__pycurl.WRITEFUNCTION,
							 self.__response_body.write)

		self.__pycurl.setopt(self.__pycurl.HEADERFUNCTION,
							 self.__response_header.write)

		#attach the the file here
		self.__pycurl.setopt(self.__pycurl.HTTPPOST , _form_atttach )
		if self.__config.has_key("verify_peer"):
			self.__pycurl.setopt(
						self.__pycurl.SSL_VERIFYPEER,
						1 if self.__config["verify_peer"] else 0
						)
		if self.__config.has_key("verify_host"):
			self.__pycurl.setopt(
						self.__pycurl.SSL_VERIFYPEER,
						2 if self.__config["verify_host"] else 0
						)
		try:
			self.__pycurl.perform()
		except(pycurl.error),e:
			self.__log(
						"critical" , 
						"Oops .. Curl Perform Failed:%s" %str(e)
			)

		#before consuming the data. set the StingIo filepoint to 0
		#so that some one can read it 
		#refer StringIO docs for more help
		self.__response_body.seek(0)
		self.__response_header.seek(0)
	

	def __mark_inprocess(  self ,_az_object , _file  ):
		_az_object.move(
				_file ,
				"%s.inprocessing" %_file
		)


	def __mark_done( self , _az_object , _file ):
		_az_object.move(
				_file ,
				re.sub( 
						'inprocessing$',
						'done',
						_file
				)
		)
			

	def __mark_error( self , _az_object , _file):
		_az_object.move(
				_file ,
				re.sub( 
						'inprocessing$',
						'error',
						_file
				)
		)

	def __save(self):
		#lets try to convert into dict
		#and save them in namespace
		_fh = None
		try:
			self.__json = json.loads(self.__response_body.read())
		except(TypeError , ValueError) , e:
			self.__log("error" , "Failed While Converting . Will write static err json")
			pass

		#set the error code for marking in container
		if type(self.__json) == dict and self.__json.has_key('errnum'):
			self.__err_code  = self.__json['errnum']

		try:
			_fh = open(
				self.__json_fname,
				'w'
			)
			json.dump(self.__json , _fh)
		except(OSError, IOError, ValueError, TypeError ) , e:
			#mostly I should be coming here
			self.log(
					"error" ,
					"Failed While Writing to file %s:%s" %(
										self.__json_fname,
										str(e)
										)
					)
		finally:
			if _fh:
				_fh.close()

	def __delete(self):	
		try:
			os.remove(self.__src_file)
		except(IOError,OSError) , e:
			self.__log(
						"warn" ,
						"Error While Deleting %s:%s" %(
								self.__src_file,
								str(e)
								)
					  )
		try:
			os.remove(self.__json_fname)
		except(IOError,OSError) , e:
			self.__log(
						"warn" ,
						"Error While Deleting %s:%s" %(
								self.__json_fname,
								str(e)
								)
					  )

	def __create_obj(self , _az_config):
		return _aw.AzureWrapper(
			_az_config["account_name"],
			_az_config["account_key"],
			_az_config["container"],
			_az_config["cache_dir"],
			self.__logger,
			_az_config["compression"],
			_az_config["decompression"]
			)
		
			
	def __init__(self, _request_config , _logger=False):
		self.__config = _request_config
		self.__logger = _logger
		self.__validate()
		# here we are actually not cleaning 
		#instead it used like default initializers :)
		#coz i am really lazy
		self.__clean()
		count=0
		self.__log( "info" , "Setting Azure Objects")

		#create objects for each container provided
		#in the config .
		if not self.__config['azure_containers']:
			raise RequestWorkerExp , "No Container Config To Process"

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
				self.__log('warn' , "Missing Attribs:%s" %str(e))

				#check whether ther are any containers to be processed
				#if not then raise the exception
				if count == len(self.__config['azure_containers']):
					self.__log("critical" , "No Azure Containers That I Can Process")
					self.__log("critical" , "Sorry Will Raise Exception" )
					raise RequestWorkerExp , "No Container Config To Process"
				count+=1
				pass


	def update_header(self , _dict ):
		self.__headers.update(
			_dict
			)
		self.__headers.update(
			self.__default_headers
		)


	def set_test_loop(self , _iter):
		"""
		Do not continue more than x  iterations
		This is only recommended for testing purpose
		"""
		self.__test=_iter+1

			
		
	def worker_init(self , _queue):
		while True:
			if type(self.__test) == int:
				self.__test-=1
				if _queue.empty():
					break

			self.__log("debug" , "Starting Next Polling")
			_in_az_config , _file = _queue.get()
			#this is a way to shutdown worker gracefully ..
			#other dev call this as POISON PILL
			if _file == 'REQUEST_WORKER_STOP':
				self.__log("info" , "Received Request To Stop.. Bye Bye ..")
				_queue.task_done()
				break
				
			_in_az = self.__create_obj(_in_az_config)
			self.__log("info" , "Got %s To Process" %_file)
			_abs_file = _in_az.download(_file)
			self.__src_file = _abs_file
			
			self.__json_fname = re.sub( ".inprocessing$" , ".json" , _abs_file)
			self.__request()
			self.__save()
			#upload to multiple containers as per config
			#cant really send the delete flag here
			map(
					lambda x:x.upload(os.path.basename(self.__json_fname)) ,
					self.__az_objs
				)
			#delete both respnsed file and source file in the cache
			self.__delete()

			if self.__err_code != 200:
				self.__mark_error(_in_az , _file)
			else:
				self.__mark_done(_in_az , _file)

			#clean all init object pertaining to pycurl
			#and restore to default for nex job
			self.__clean()
			_queue.task_done()

			if type(self.__test) == int :
				if _queue.empty() or self.__test <= 0:
					break
				continue
		

