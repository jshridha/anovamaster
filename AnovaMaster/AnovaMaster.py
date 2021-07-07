import sys

if sys.version_info[0] < 3:
    from Queue import Queue, Empty
else:
    from queue import Queue, Empty

import json
import logging
import time
import datetime

from .AnovaStatus import AnovaStatus, AnovaTimerStatus
from .MQTTController import MQTTController
from .RESTAnovaController import RESTAnovaController
from .StatusException import StatusException

import bluepy

valid_states = { "disconnected",
                 "off",
                 "heat"
}

class AnovaMaster:
    def __init__(self, config):
        self._config = config
        self._mqtt = MQTTController(config = config,
                                    command_callback = self.mqtt_command)
        self._status = AnovaStatus()
        self._timer_status = AnovaTimerStatus()
        self._command_queue = Queue(maxsize=20)
        self._anova = RESTAnovaController(self._config.get('anova', 'mac'), connect = False)
        self.anova_connect()

    def anova_connect(self):
        if (self._status.state is "disconnected"):
            logging.debug('Trying to connect to {}'.format(self._config.get('anova', 'mac')))
            sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            sys.stdout.write('Trying to connect to {}'.format(self._config.get('anova', 'mac')))
            sys.stdout.write('\n')
            try:
                self._anova.connect()
                # We don't know status, but need to set it to something
                # or fetch_status will get sad.
                self._status.state = "stopped"
                self.fetch_status()
            except bluepy.btle.BTLEException:
                # Assuming this was because the device is off / out of range
                logging.info('Can\'t connect to Anova. Is it on and in range?')
                sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                sys.stdout.write('Can\'t connect to Anova. Is it on and in range?\n')
                self._status.state = "disconnected"
        else:
            logging.debug('Already connected, skipping connect()')

    def fetch_status(self):
        # Update our internal state with the current status from the anova
        self.anova_connect()
        if (self._status.state is "disconnected"):
            self._status.target_temp = 0
            self._status.current_temp = 0
            self._timer_status.timer = 0
            self._timer_status.timer_state = False
            self.temp_unit = ''
        else:
            try:
                anova_status = self._anova.anova_status()
                if anova_status == "stopped":
                    anova_status = "off"
                elif anova_status == "running":
                    anova_status = "heat"
                if (anova_status in valid_states):
                    self._status.state = anova_status
                else:
                    logging.warning('Unknown status: '.format(anova_status))
                    sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    sys.stdout.write('Unknown status: '.format(anova_status))
                    sys.stdout.write('\n')
                    raise StatusException(anova_status)

                anova_unit = self._anova.read_unit()
                if (anova_unit in {'c', 'f'}):
                    self._status.temp_unit = anova_unit
                else:
                    logging.warning('Unknown temperature unit: '.format(anova_unit))
                    sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    sys.stdout.write('Unknown temperature unit: '.format(anova_unit))
                    sys.stdout.write('\n')
                    # TODO: Better custom exceptions?
                    raise StatusException(anova_unit)
                self._status.target_temp = self._anova.read_set_temp()
                self._status.current_temp = self._anova.read_temp()
                timer = self._anova.read_timer()
                self._timer_status.timer = timer.split(' ')[0]
                self._timer_status.timer_state = 'heat' if (timer.split(' ')[1] == 'running') else 'off'
            except bluepy.btle.BTLEException:
                logging.error('Error retrieving state, disconnecting.')
                sys.stdout.write('%s Error retrieving state, disconnecting.\n'% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                self._anova.close()
                self._status.state = 'disconnected'
            except TypeError:
                # TypeError seems to be fairly frequently thrown
                # by the AnovaController. Current best guess is
                # as a result of comms failure. We'll assume the
                # connection has failed for whatever reason. May
                # be a better way of dealing with this though.
                logging.info('Connection error (TypeError), disconnecting.')
                sys.stdout.write('%s Connection error (TypeError), disconnecting.\n'% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
                logging.debug("Next Command: {}".format(next_command))
                sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                sys.stdout.write("Next Command: {}".format(next_command))
                sys.stdout.write('\n')
                if (next_command[0] == 'run'):
                    if (next_command[1] == 'heat'):
                        self._anova.start_anova()
                    elif (next_command[1] == 'off'):
                        self._anova.stop_anova()
                    else:
                        logging.warning('Unknown mode for run command: {}'.format(next_command[1]))
                        sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        sys.stdout.write('Unknown mode for run command: {}'.format(next_command[1]))
                        sys.stdout.write('\n')
                elif (next_command[0] == 'temp'):
                    try:
                        target_temp = float(next_command[1])
                    except ValueError:
                        # Couldn't parse it, don't care
                        target_temp = 0
                    # Bounds checking, yes these are hard coded
                    # (based on fahrenheit or Celscius!) from the Anova website
                    if self._status.temp_unit == "f":
                        if (target_temp >= 77 and target_temp <= 210):
                            self._anova.set_temp(target_temp)
                    elif self._status.temp_unit == "c":
                        if (target_temp >= 20 and target_temp <= 99):
                            self._anova.set_temp(target_temp)
                elif (next_command[0] == 'timer_run'):
                    if (next_command[1] == 'heat'):
                        self._anova.start_anova() # Anova must be started before starting timer so forcing start to be safe
                        self._anova.start_timer()
                    elif (next_command[1] == 'off'):
                        self._anova.stop_timer()
                    else:
                        logging.warning('Unknown mode for timer_state command: {}'.format(next_command[1]))
                        sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                        sys.stdout.write('Unknown mode for timer_state command: {}'.format(next_command[1]))
                        sys.stdout.write('\n')
                elif (next_command[0] == 'timer'):
                    try:
                        target_timer = int(next_command[1])
                    except ValueError:
                        # Couldn't parse it, don't care
                        target_timer = 0
                    self._anova.set_timer(target_timer)
                else:
                    logging.error('Unknown command received: {}'.format(next_command[0]))
                    sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                    sys.stdout.write('Unknown command received: {}'.format(next_command[0]))
                    sys.stdout.write('\n')

            if (status_count >= status_max):
                self.fetch_status()
                json_status = json.dumps(self._status.__dict__, sort_keys=True)
                json_timer_status = json.dumps(self._timer_status.__dict__, sort_keys=True)

                self._mqtt.publish_message(self._config.get('mqtt', 'status_topic'), json_status)
                self._mqtt.publish_message(self._config.get('mqtt', 'status_timer'), json_timer_status)
                status_count = 0
            else:
                status_count = status_count+1

            time.sleep(loop_delay)
