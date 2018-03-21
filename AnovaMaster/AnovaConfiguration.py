from ConfigParser import ConfigParser

class AnovaConfiguration(ConfigParser):
    def __init__(self):
        self.home_dir = "."
        self.config_dir= "{}/config".format(self.home_dir)
        self.config_file = "{}/AnovaMaster.cfg".format(self.config_dir)
        # This is python3 syntax
        # super().__init__()
        # This is how we do it in old land
        ConfigParser.__init__(self)
        config_handle = open(self.config_file)
        self.readfp(config_handle)
        config_handle.close()
        self.add_defaults()

    def add_defaults(self):
        if (not self.has_option('anova', 'verbose')):
            self.set('anova', 'verbose', False)
