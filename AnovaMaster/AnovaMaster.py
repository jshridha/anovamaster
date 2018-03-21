import json
import time

from AnovaStatus import AnovaStatus
from MQTTController import MQTTController
from RESTAnovaController import RESTAnovaController
import bluepy

valid_states = { "disconnected",
                 "stopped",
                 "running"
}

class AnovaMaster:
    def __init__(self, config):
        self._config = config
        self._mqtt = MQTTController(config)
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

    def run(self):
        while True:
            self.fetch_status()
            json_status = json.dumps(self._status.__dict__, sort_keys=True)
            self._mqtt.publish_message(self._config.get('mqtt', 'status_topic'),
                                       json_status)
            time.sleep(1)
