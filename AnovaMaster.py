from ConfigParser import ConfigParser
from enum import Enum
import json

import bluepy

from pycirculate.anova import AnovaController

valid_states = { "disconnected",
                 "stopped",
                 "running"
}

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

class AnovaStatus:
    def __init__(self):
        self.temp_unit = "C"
        self.current_temp = "0"
        self.target_temp = "0"
        self.state = "disconnected"

class StatusException(Exception):
    def __init__(self, state):
        self.state = state

class AnovaMaster:
    def __init__(self, config):
        self._config = config
        self._status = AnovaStatus()
        self._anova = AnovaController(self._config.get('anova', 'mac'), connect = False)
        self.connect()

    def connect(self):
        if (self._config.get('anova', 'verbose')):
            print("Trying to connect to {}".format(self._config.get('anova', 'mac')))
        if (self._status.state is "disconnected"):
            try:
                self._anova.connect()
                self._status.state = "stopped"
                self.fetch_status()
            except bluepy.btle.BTLEException:
                # Assuming this was because the device is off / out of range
                print("Can't connect to Anova. Is it on and in range?")
                self._status.state = "disconnected"

    def fetch_status(self):
        # Update our internal state with the current status from the anova
        self.connect()
        if (self._status.state is not "disconnected"):
            try:
                anova_status = self._anova.anova_status()
                if (anova_status in valid_states):
                    self._status.state = anova_status
                else:
                    print("Unknown status")
                    raise StatusException(anova_status)

                anova_unit = self._anova.read_unit()
                if (anova_unit in {'c', 'f'}):
                    self._status.temp_unit = anova_unit
                else:
                    print("Unknown temperature unit")
                    # TODO: Better custom exceptions?
                    raise StatusException(anova_unit)
                self._status.target_temp = self._anova.read_set_temp()
                self._status.current_temp = self._anova.read_temp()
            except bluepy.btle.BTLEException:
                print("Failed to receive state. Assuming we're disconnected.")
                self._status.state = AnovaStatus.disconnected

if __name__ == '__main__':
    config = AnovaConfiguration()
    my_anova = AnovaMaster(config)
