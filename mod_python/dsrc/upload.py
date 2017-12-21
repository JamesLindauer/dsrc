
from mod_python import util , apache
import uuid , xmltodict , json , os, binascii
import dpkt , subprocess , Queue
import re 
from socket import inet_ntoa
import time


class JumperBack(Exception):
	"""
	This is only the jumper back to main
	in this case its the handler method and return 
	dict on repr and json converted 
	"""
	err={}
	def __init__(self , _err_num , _err_str):

		self.err['errnum'] = _err_num
		self.err['errstr'] = _err_str

	def __str__(self):
		return json.dumps(
			self.err,
			indent = 4
			)
		
	def __repr__(self):
		return repr(self.err)



class Storage(file):

	#default storage based methods start here 
	def __init__(self, directory, advisory_filename):
		self.advisory_filename = advisory_filename
		self.real_filename = directory + '/' + advisory_filename
		super(Storage, self).__init__(self.real_filename, 'w+b')

	def close(self):
		super(Storage, self).close()
		

class StorageFactory:

	def __clean(self , _data):
		"""
		return both the cleaned hexilified and bin data
		"""
		_hexed = re.findall('(001.*)',
			binascii.hexlify(_data)
			)[0]

		return \
			binascii.unhexlify(
				_hexed
			) , _hexed

	def __parse_hex(self):
		self.__fh = None
		try:
			self.__fh = open(self.__file_path , 'r') 
		except(IOError,OSError) , e:
			raise JumperBack , ( apache.HTTP_NOT_ACCEPTABLE ,str(e))
		#presuming each line is having uper bin hex data
		for _line in self.__fh:
			_line = _line.strip()
			self.__inqueue.append(
				{
				   'hex_data' : _line,
				   'udp_data' : binascii.unhexlify(_line)
				}
			)
		
		
	def __parse_pcap(self):
		"""
		method which takes the pcap and reads through
		dpkt udp reader and puts them into the 
		input queue 
		"""

		self.__fh=None
		#if i was not able to read the file that i have created
		#there is no point in doing blah blah blah
		#report to user and log something somewhere 
		#went terribily wrong

		try:
			self.__fh = open(self.__file_path , 'r') 
		except(IOError,OSError) , e:
			raise JumperBack , ( apache.HTTP_NOT_ACCEPTABLE ,str(e))

		#Check whether the file is of proper format
		#else let go back to the user and say we failed ..politely
		try:
			_pcap_obj = dpkt.pcap.Reader(self.__fh)
		except(ValueError,TypeError) , e:
			raise JumperBack , ( 
					apache.HTTP_INTERNAL_SERVER_ERROR ,
					str(e) 
					)


		#lets loop through the pcap and extract the udp from ethernet.
		#and formulate the queue as dicts with all attribs
		for _ts , _buf in _pcap_obj:
			_eth_obj = dpkt.ethernet.Ethernet(_buf)
			_ip_frame = _eth_obj.data
			_udp_frame =  _ip_frame.data
			_bin , _hex = self.__clean(_udp_frame.data)
			self.__inqueue.append(
				{
					'src_ip' : inet_ntoa(_ip_frame.src),
					'dst_ip' : inet_ntoa(_ip_frame.dst),
					'src_port' : _udp_frame.sport,
					'dst_port' : _udp_frame.dport,
					'udp_len' : _udp_frame.ulen,
					'udp_sum' : _udp_frame.sum,
					'udp_data' : _bin,
					'hex_data' : _hex,
					'message_type' : self.frame
				}
				)



	def __spawn(self , _data):
		
		try:
			_bin_path = self.__config[self.decoder]['bin_dir']
			_bin_path += self.__config[self.decoder]['bin']
			_args = self.__config[self.decoder]['bin_args']
			_bin_command = [_bin_path]
			_bin_command.extend(_args)
			_bin_command.extend([ '-p' , self.frame ])
		except(KeyError) , e:
			raise JumperBack , (
					apache.HTTP_METHOD_NOT_ALLOWED,
					str(e)
					)
		#lets go ahead and create the subprocess object and 
		#fetch stdou  , stderr and return code
		#and return them back
		#lets always keep the shell = false for security reasons 
		#no globing (*+) and other bash shortcut invocations
		try:
			_s_obj = subprocess.Popen(_bin_command , 
					  stdin = subprocess.PIPE,
					  stdout = subprocess.PIPE,
					  stderr = subprocess.PIPE,
					  bufsize = 1, 
					  shell = False)
		except(IOError,OSError) , e:
			raise JumperBack , (
				apache.HTTP_INTERNAL_SERVER_ERROR,
				str(e)
				)
		_s_obj.stdin.write(_data)
		_s_obj.stdin.close()
		_stdout=''
		while True:
			time.sleep(0.5)
			_stdout+=_s_obj.stdout.read()
			_tmp = _s_obj.poll()
			if _tmp == None:
				continue
			else:
				break
		#raise JumperBack , ( 123 , "I am here")
		_tmp =  (
			_s_obj.returncode,
			_stdout,
			_s_obj.stderr.read()
			)
		del _s_obj
		return _tmp
		
		
	def __dict_to_json(self):
		#lets 
		if self.__inqueue:
			return json.dumps(
				self.__inqueue
				)
		else:
			return json.dumps({
			'oops'  : 'SOMETHING SOMWHERE TERIBILY WENT WRONG'
			})

	def __postprocessor(self , _path , _key , _val):
		_attrib = {
				"wheelBrakes" : 5,
				"lights" : 9,
				"events" : 12
			 }
		if _attrib.has_key(_key):
			_len = _attrib[_key]
			if _val == '0':
				return _key , map( 
					lambda x:False , range(_len)
					)
			else:
				return _key , map(
					lambda x: True if x=='1' else False ,
					_val
					)
				
					
		try:
			return _key , float(_val) if '.' in _val else int(_val)
		except(ValueError,TypeError):
			return _key , _val
		

		
	def __convert_to_per(self):
		#if the inqueue is empty then there is no 
		#point and we dint get the file of different format or 
		#emipty pcap one. buggers .. run off.
		_all_data = ''
		if not self.__inqueue:
			raise JumperBack , ( 
				apache.HTTP_UNSUPPORTED_MEDIA_TYPE ,
				"No UDP Data Found" 
				)
		_regex = '(<%s>.*?</%s>)' %( 
			self.frame,
			self.frame,
			)
		#ok ... now that the queue is not empty 
		#let go ahead and formulate output for each 
		#UDP frame and spawn to sdtin of the decoder
		
		for _dict in self.__inqueue:
			_all_data += _dict['udp_data']
			
			
		_ret , _stdout , _stderr = self.__spawn(_all_data)

		if _stdout and _ret ==0:
			_stdout = re.sub( '(<.*?>)<(.*?)\/>(<.*?>)', r'\1\2\3' , _stdout )
				
		_output = map( lambda x: xmltodict.parse(x , 
					postprocessor=self.__postprocessor) , 
					re.findall(
						_regex , 
						_stdout,
						re.M | re.S
						)
					) \
				        if  _ret == 0  else None
		if len(_output) != len(self.__inqueue):
			raise JumperBack , (
						apache.HTTP_INTERNAL_SERVER_ERROR,
						"Input to Output Dint Match"
					   )
			
		for _index , _dict in enumerate(self.__inqueue):
			_dict['output'] = _output[_index]
			del _dict['udp_data']
		#clean up
		_output = None
		_all_data = None
		
	

	def __init__(self, directory):
		self.output = None
		self.__inqueue = []
		self.dir = directory
		self.fname = str(uuid.uuid1())
		self.__file_path = self.dir + '/' + self.fname


	def create(self, advisory_filename):
		"""
		Call back function on storage factory to save create
		the file with uuid when the pcap attachment arrives
		"""
		self.__advisory_name = advisory_filename
		return Storage(self.dir, self.fname)


	def process(self):
		"""
		Process the pcap file through dpkt and return
		output if 
		Do not forget to load_values first to do the process.
		"""
		self.__callback = {
				'pcap' : self.__parse_pcap,
				'hex' : self.__parse_hex
				}
		_match_obj = re.search('.*\.(\S+)$' , self.__advisory_name , re.I)
		if _match_obj:
			_ext = _match_obj.group(1).lower()
			try:
				self.__callback[_ext]()
			except(KeyError) , e:
				JumperBack , (
					apache.HTTP_UNSUPPORTED_MEDIA_TYPE,
					"%s Extention Not Supported" %_ext
					)
		else:
			raise JumperBack ,(
					apache.HTTP_NOT_ACCEPTABLE,
					"File Name Dint Have Any Extentions " 
					)
		
		self.__convert_to_per()
		return self.__dict_to_json()


	def load_values(self , _config_file , _decoder , _frame ):
		"""
		load_values(self , _config_file ) -> None
		load the config file from path given in first arg
		"""
		self.decoder = _decoder
		self.frame = _frame
		self.config_file = _config_file
		self.__config = {}
		try:
			execfile( self.config_file , self.__config)
		except(ImportError , SyntaxError), e:
			raise JumperBack , ( 
						apache.HTTP_INTERNAL_SERVER_ERROR
						, "Config Load Failed:%s" %str(e)
					   )

	def __del__(self):
		try:
			if self.__fh:
				self.__fh.close()
			os.remove(self.__file_path)
		except:
			pass
		


def __form_save__(_request):
	_output = ''
	file_factory = StorageFactory('/var/mod_dsrc_cache')
	request_data = util.FieldStorage(_request, keep_blank_values=True,
                                 file_callback=file_factory.create)
	

	#lets sta
	try:
		file_factory.load_values(
				'/etc/mod_dsrc.conf' ,
				request_data.get(
						'Decoder' , 'J2735_UPER_JSON'
						),
				request_data.get(
						'MessageType' , 'MessageFrame'
						)
					)

		_output = file_factory.process()
		del file_factory
		_request.write(_output)
		raise apache.SERVER_RETURN , apache.OK
	#Mama Mia .. no aborts .. always handle :)
	except(JumperBack) , e:
		del file_factory
		_request.write(str(e))
		raise apache.SERVER_RETURN , apache.DONE



def handler(_req):
	if _req.method.lower() == 'post':
		_req.content_type='application/json'
		__form_save__(_req)
	else:
		return  apache.HTTP_NOT_FOUND
	return apache.OK


