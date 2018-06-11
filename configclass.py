import os
import json

def config_from_file(filename, config=None):
    """Small configuration file management function."""
    if config:
        # We're writing configuration
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
