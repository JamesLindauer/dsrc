
from azure.storage.blob import BlockBlobService
import re , sys , os
import gzip , shutil


class AzureWrapperException(Exception):
	pass



class AzureWrapper(object):
	"""
	Depends mostly on file download and upload and no bytes and streams
	Please note  that this is pertained to a single container 
	In case if you want use multiple conatiner please use 2 object 
	and map accordingle 
	NetworkIO intensive in that case if you would like to use this for
	Migration
	Recommended to use tmps mount points to be faster for cache dir
	"""

	#class level private variables
	__azure_blob_obj=None
	__cache_dir='/tmp/'
	__logger=None
	__container = None
	__acc_key = None
	__acc_name = None
	__compression = False
	__decompression = False

	#write into the init'ed  logger or if found true
	#write it to stderr 
	#dont set if you require no logging
	def __log(self ,_debug ,  _msg ):
		_msg="CacheDir:%s -- Account:%s -- Container:%s -- %s" %(
				self.__cache_dir,
				self.__acc_name,
				self.__container,
				_msg
				)
		if self.__logger:
			try:
				func_pointer = getattr(self.__logger , _debug )
			except:
				_msg+="\n"
				func_pointer = sys.stderr.write
				
			func_pointer(_msg)


	def __decompress(self, _file):
		"""
		Not gonna trap and reraise ..
		Requesting caller to catch the exception
		"""
		self.__log( "info" , "Decompressing %s" %_file )
		_src , _dst  =  _file ,  "%s.gz" %_file 
		shutil.move( _src , _dst )
		with gzip.open(_dst , 'rb' ) as _s_obj , open(_src , 'w') as _d_obj:
			shutil.copyfileobj(_s_obj , _d_obj)
		os.remove(_dst)
		if _file.endswith('.gz'):
			os.rename(_file , _file[:-3])



	def __compress(self, _file):
		"""
		Not gonna trap and reraise ..
		Requesting caller to catch the exception
		mostly IOError and OSError
		"""
		self.__log( "info" , "Compressing %s" %_file )
		
		_src  , _newsrc  = _file  , "%s.gz"  %_file
		with open(_src) as _s_obj , gzip.open(_newsrc , 'wb') as _d_obj:
			shutil.copyfileobj(_s_obj , _d_obj)
		#os.remove(_src)
		return _newsrc


			
			
	def __init__(self , _account_name , _account_auth_key , _container,
									_cache_dir=None , _logger = None,
									_compression=False , _decompression=False):
		
		self.__logger = _logger
		self.__container = _container
		self.__acc_name = _account_name
		self.__acc_key = _account_auth_key
		self.__cache_dir = _cache_dir or '/tmp/'
		self.__compression = _compression
		self.__decompression = _decompression

		self.__log( 'info' , "Init'ed Azure Service Object" )
		self.__azure_blob_obj = BlockBlobService(
				account_name= _account_name , 
				account_key= _account_auth_key
				)

	def get_config(self):
		return \
				{
					"account_name" : self.__acc_name,
					"account_key" : self.__acc_key,
					"container" : self.__container,
					"compression" : self.__compression,
					"decompression" : self.__decompression ,
					"cache_dir" : self.__cache_dir
				}
		
		
	def delete( self , _file):
		"""
		Delete the file in the container
		"""
		self.__log( 'info' , "Deleting %s" %_file )
		self.__azure_blob_obj.delete_blob(
			self.__container,
			_file
			)
		return True
		

	def copy(self , _src , _dst ):
		"""
		Copy the file to the same container
		"""
		self.__log( 'info' , "Copying %s to %s" %( _src , _dst ))
		_blob_url = self.__azure_blob_obj.make_blob_url(
				self.__container,
				_src
				)
		self.__azure_blob_obj.copy_blob(
			self.__container,
			_dst,
			_blob_url
		)
		return True
		
		

		
	def move(self , _src  , _dst):
		"""
		Copy the file first and then delete
		there is no direct api for  move
		costly affair .. yet cant override
		"""
		self.__log( 'info' , "Moving %s to %s" %( _src , _dst ))
		if self.copy(_src , _dst):
			self.delete(_src)
		return True


	def upload(self , _file , _delete=False ):
		"""
		Upload the file from cache directory
		"""
		_upload_path = "%s/%s" %( self.__cache_dir , _file )

		if self.__compression:
			_file = "%s.gz" %_file
			_upload_path = self.__compress(_upload_path)

		self.__log( 'info' , "Uploading %s" %_upload_path)
		self.__azure_blob_obj.create_blob_from_path(
				self.__container,
				_file,
				_upload_path
				)

		if _delete:
			self.__log( 'info' , "Deleting %s" %_upload_path )
			try:
				os.remove(_upload_path)
			except(IOError,OSError):
				raise AzureWrapperException , str(e)
		return True


	def download(self,  _file , _delete=False):
		"""
		download the file into local storage
		%_delete  True if you want to delete after the download
		"""
		_save_path =  "%s/%s" %( self.__cache_dir , _file )
		self.__log('info' , "Downloading %s" %_file )
		self.__azure_blob_obj.get_blob_to_path(
				self.__container,
				_file,
				_save_path
				)
		if self.__decompression:
			self.__decompress(_save_path)

		if _delete:
			self.delete(_file)
		return _save_path


	def download_multi(self , _files , _delete = False):
		"""
		same as download . difference is that  files
		needed to be provided as list
		"""

		if not type(_files) == type([]):
			raise AzureWrapperException , "Files not in list format"
		return \
			map( 
				lambda x:self.download(x , _delete ),
				 _files )


	def upload_multi(self , _files , _delete = False ):
		"""
		same as upload . difference is that  files
		needed to be provided as list
		"""
		if not type(_files) == type([]):
			raise AzureWrapperException , "Files not in list format"
		return \
			map( 
				lambda x:self.upload(x , _delete ),
				 _files )


	def list( self , _regex = r'.*.$'):
		"""
		return a list of filenames in the conatiner
		with %_regex pattern
		"""
		#return a generator
		try:
			_compiled = re.compile(_regex)
		except (re.error , ValueError) , e:
			AzureWrapperException , str(e)

		_gen = self.__azure_blob_obj.list_blobs(self.__container)
		_matches = map( lambda blob_obj:blob_obj.name ,
				filter( 
				lambda _blob: _compiled.search(_blob.name) ,
				_gen 
			))
		return _matches


	def set_container(self  , _name):
		self.__container = _name


