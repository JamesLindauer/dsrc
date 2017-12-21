import watcher,requester
import Queue , time
import gc

reload(watcher)
reload(requester)


##############################################
_config_watcher = {
"azure_containers" : [
	{
	"account_name" : "",
	"account_key" : "",
	"container" : "",
	"compression" : False,
	"decompression" : False ,
	},
	}
	],
"cache_dir" : "/var/mod_dsrc_cache" ,
"sleep" : 3
}

_config_request = {
		"url" : "http://localhost/dsrc/upload.py",
		"user" : "dsrcusers",
		"passwd" : "dsrcsecret",
		"timeout" : 1 * 60 ,
		"verify_peer" : False,
		"verify_host" : False,
		"headers" : [],
		"cache_dir" : "/var/mod_dsrc_cache",
		"azure_containers" : [
							{
								"account_name" : "",
								"account_key" : "",
								"container" : "",
								"compression" : True,
								"decompression" : False ,
							}
						 ],
	
}
##################################################


queue = Queue.Queue()
_obj_watcher = watcher.Watcher(_config_watcher, True)

_obj_request = requester.Requester(_config_request, True)
while True:
	_obj_watcher.set_test_loop(1)
	_obj_watcher.worker_init(queue)
	_obj_request.set_test_loop(7)
	_obj_request.worker_init(queue)
	queue.join()




