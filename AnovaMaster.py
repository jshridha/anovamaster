from ConfigParser import ConfigParser
import datetime
from enum import Enum
import json
import logging
from threading import Timer

import bluepy

from pycirculate.anova import AnovaController

valid_states = { "disconnected",
                 "stopped",
                 "running"
}

class RESTAnovaController(AnovaController):
    """
    This version of the Anova Controller will keep a connection open over bluetooth
    until the timeout has been reach.
    NOTE: Only a single BlueTooth connection can be open to the Anova at a time.
    """

    TIMEOUT = 5 * 60 # Keep the connection open for this many seconds.
    TIMEOUT_HEARTBEAT = 20

    def __init__(self, mac_address, connect=True, logger=None):
        self.last_command_at = datetime.datetime.now()
        if logger:
            self.logger = logger
        else:
            self.logger = logging.getLogger()
        super(RESTAnovaController, self).__init__(mac_address, connect=connect)

    def set_timeout(self, timeout):
        """
        Adjust the timeout period (in seconds).
        """
        self.TIMEOUT = timeout

    def timeout(self, seconds=None):
        """
        Determines whether the Bluetooth connection should be timed out
        based on the timestamp of the last exectuted command.
        """
        if not seconds:
            seconds = self.TIMEOUT
        timeout_at = self.last_command_at + datetime.timedelta(seconds=seconds)
        if datetime.datetime.now() > timeout_at:
            self.close()
            self.logger.info('Timeout bluetooth connection. Last command ran at {0}'.format(self.last_command_at))
        else:
            self._timeout_timer = Timer(self.TIMEOUT_HEARTBEAT, lambda: self.timeout())
            self._timeout_timer.setDaemon(True)
            self._timeout_timer.start()
            self.logger.debug('Start connection timeout monitor. Will idle timeout in {0} seconds.'.format(
                (timeout_at - datetime.datetime.now()).total_seconds())) 

    def connect(self):
        super(RESTAnovaController, self).connect()
        self.last_command_at = datetime.datetime.now()
        self.timeout()

    def close(self):
        super(RESTAnovaController, self).close()
        try:
            self._timeout_timer.cancel()
        except AttributeError:
            pass

    def _send_command(self, command):
        if not self.is_connected:
            self.connect()
        self.last_command_at = datetime.datetime.now()
        return super(RESTAnovaController, self)._send_command(command)

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

class AnovaStatus(object):
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
        self._anova = RESTAnovaController(self._config.get('anova', 'mac'), connect = False)
        self.anova_connect()

    def anova_connect(self):
        if (self._status.state is "disconnected"):
            self.debug_log("Trying to connect to {}".format(self._config.get('anova', 'mac')))
            try:
                self._anova.connect()
                # We don't know status, but need to set it to something
                # or fetch_status will get sad.
                self._status.state = "stopped"
                self.fetch_status()
            except bluepy.btle.BTLEException:
                # Assuming this was because the device is off / out of range
                print("Can't connect to Anova. Is it on and in range?")
                self._status.state = "disconnected"
        else:
            self.debug_log("Not reconnecting, as we're already connected")

    def fetch_status(self):
        # Update our internal state with the current status from the anova
        self.anova_connect()
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
                self._status.state = 'disconnected'

    def dump_status(self):
        json_status = json.dumps(self._status.__dict__, sort_keys=True,
                                 indent=4)
        print(json_status)

    def debug_log(self, str):
        if (self._config.get('anova', 'verbose')):
            print(str)

if __name__ == '__main__':
    print("Importing config")
    config = AnovaConfiguration()
    print("Setting up connection")
    my_anova = AnovaMaster(config)
    import time
    while True:
        time.sleep(5)
        print("Attempting to fetch status")
        my_anova.fetch_status()
        my_anova.dump_status()
