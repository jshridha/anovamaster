from Queue import Queue, Empty
import json
import logging
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
            logging.debug('Trying to connect to {}'.format(self._config.get('anova', 'mac')))
            try:
                self._anova.connect()
                # We don't know status, but need to set it to something
                # or fetch_status will get sad.
                self._status.state = "stopped"
                self.fetch_status()
            except bluepy.btle.BTLEException:
                # Assuming this was because the device is off / out of range
                logging.info('Can\'t connect to Anova. Is it on and in range?')
                self._status.state = "disconnected"
        else:
            logging.debug('Already connected, skipping connect()')

    def fetch_status(self):
        # Update our internal state with the current status from the anova
        self.anova_connect()
        if (self._status.state is "disconnected"):
            self._status.target_temp = 0
            self._status.current_temp = 0
            self.temp_unit = ''
        else:
            try:
                anova_status = self._anova.anova_status()
                if (anova_status in valid_states):
                    self._status.state = anova_status
                else:
                    logging.warning('Unknown status: '.format(anova_status))
                    raise StatusException(anova_status)

                anova_unit = self._anova.read_unit()
                if (anova_unit in {'c', 'f'}):
                    self._status.temp_unit = anova_unit
                else:
                    logging.warning('Unknown temperature unit: '.format(anova_unit))
                    # TODO: Better custom exceptions?
                    raise StatusException(anova_unit)
                self._status.target_temp = self._anova.read_set_temp()
                self._status.current_temp = self._anova.read_temp()
            except bluepy.btle.BTLEException:
                logging.error('Error retrieving state, disconnecting.')
                self._anova.close()
                self._status.state = 'disconnected'
            except TypeError:
                # TypeError seems to be fairly frequently thrown
                # by the AnovaController. Current best guess is
                # as a result of comms failure. We'll assume the
                # connection has failed for whatever reason. May
                # be a better way of dealing with this though.
                logging.info('Connection error (TypeError), disconnecting.')
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

    def run(self):
        # Every time through the loop, we check for queued commands
        # received via MQTT. If there are any, run those. If not,
        # just fetch status. Then rest a bit between runs.
        # Note: This should be THE ONLY place that actually talks
        # to the Anova.
        # Every time through the loop we increment status_count
        status_count = 0
        # How long to sleep at the end of the loop (in seconds)
        loop_delay = 0.1
        # Send status after this many iterations through the loop
        status_max = 50
        while True:
            next_command = None
            if (not self._command_queue.empty()):
                try:
                    next_command = self._command_queue.get_nowait()
                except Empty:
                    # This shouldn't happen with only one queue
                    # consumer, but catch it and move on if so.
                    pass

            if (next_command is not None):
                if (next_command[0] == 'run'):
                    if (next_command[1] == 'running'):
                        self._anova.start_anova()
                    elif (next_command[1] == 'stopped'):
                        self._anova.stop_anova()
                    else:
                        logging.warning('Unknown mode for run command: {}'.format(next_command[1]))
                elif (next_command[0] == 'temp'):
                    try:
                        target_temp = float(next_command[1])
                    except ValueError:
                        # Couldn't parse it, don't care
                        target_temp = 0
                    # Bounds checking, yes these are hard coded
                    # (and fahrenheit!) from the Anova website
                    if (target_temp >= 77 and target_temp <= 210):
                        self._anova.set_temp(target_temp)
                else:
                    logging.error('Unknown command received: {}'.format(next_command[0]))

            if (status_count >= status_max):
                self.fetch_status()
                json_status = json.dumps(self._status.__dict__, sort_keys=True)
                self._mqtt.publish_message(self._config.get('mqtt', 'status_topic'), json_status)
                status_count = 0
            else:
                status_count = status_count+1

            time.sleep(loop_delay)
