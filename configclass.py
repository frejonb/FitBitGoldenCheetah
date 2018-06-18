import os
import json

def config_from_file(filename, config=None, update=True):
    """Small configuration file management function."""
    if config:
        # We're writing configuration
        if update:
            #We're updating
            json_dump = config_from_file(filename)
            json_dump.update(config)
            return config_from_file(filename,config = json_dump, update=False)
        else:
            #Just write
            with open(filename, 'w') as fdesc:
                fdesc.write(json.dumps(config))
            return config
    else:
        # We're reading config
        if os.path.isfile(filename):
            with open(filename, 'r', errors='ignore') as fdesc:
                return json.loads(fdesc.read())
        else:
            return {}



class configclass(object):
	def load_config_file(self,config_file, default_config):
		#check if file exits if not create it. load config file
		if os.path.isfile(config_file):
			conf_file = config_from_file(config_file)
			if conf_file == default_config:
				self.request_app_setup()
				return False
		else:
			conf_file = config_from_file(config_file, default_config)
			self.request_app_setup()
			return False


		return conf_file
