from Queue import Queue, Empty
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
        self._mqtt = MQTTController(config = config,
                                    command_callback = self.mqtt_command)
        self._status = AnovaStatus()
        self._command_queue = Queue(maxsize=20)
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
                self._anova.close()
                self._status.state = 'disconnected'
            except TypeError:
                # TypeError seems to be fairly frequently thrown
                # by the AnovaController. Current best guess is
                # as a result of comms failure. We'll assume the
                # connection has failed for whatever reason. May
                # be a better way of dealing with this though.
                print("Connection has failed, trying again.")
                self._anova.close()
                self._status.state = 'disconnected'

    def dump_status(self):
        json_status = json.dumps(self._status.__dict__, sort_keys=True,
                                 indent=4)
        print(json_status)

    def mqtt_command(self, command, data):
        # The MQTT library processes incoming messages in a background
        # thread, so this callback will always be run separately to
        # the main Bluetooth message handling. We use a queue to pass
        # inbound messages to the Bluetooth function, to ensure only
        # one thread is trying to use the connection to the Anova.
        self._command_queue.put([command, data])

    def debug_log(self, str):
        if (self._config.get('anova', 'verbose')):
            print(str)

    def run(self):
        # Every time through the loop, we check for queued commands
        # received via MQTT. If there are any, run those. If not,
        # just fetch status. Then rest a bit between runs.
        # Note: This should be THE ONLY place that actually talks
        # to the Anova.
        while True:
            next_command = None
            if (not self._command_queue.empty()):
                try:
                    next_command = self._command_queue.get_nowait()
                except Empty:
                    next_command = ['status', None]
            else:
                next_command = ['status', None]

            if (next_command[0] == 'run'):
                if (next_command[1] == 'running'):
                    self._anova.start_anova()
                elif (next_command[1] == 'stopped'):
                    self._anova.stop_anova()
                else:
                    print('Unknown mode for run command: {}'.format(next_command[1]))
            elif (next_command[0] == 'temp'):
                # TODO: Handle temperature here
                pass
            elif (next_command[0] == 'status'):
                self.fetch_status()
                json_status = json.dumps(self._status.__dict__, sort_keys=True)
                self._mqtt.publish_message(self._config.get('mqtt', 'status_topic'), json_status)
            else:
                print('Unknown command received: {}'.format(next_command[0]))

            time.sleep(1)
