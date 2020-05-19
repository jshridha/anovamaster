import logging

import paho.mqtt.client as mqtt
import datetime
import sys

class MQTTController(object):
    def __init__(self, config, command_callback):
        def on_connect(client, userdata, flags, rc):
            logging.info('MQTT connected with result code {}'.format(str(rc)))
            sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            sys.stdout.write('MQTT connected with result code {}'.format(str(rc)))
            sys.stdout.write('\n')
            client.publish(config.get('mqtt', 'run_command_topic'), '')        # Clearing existing command topics
            client.publish(config.get('mqtt', 'temp_command_topic'), '')       # as trying to run a timer
            client.publish(config.get('mqtt', 'timer_run_command_topic'), '')  # when Anova is not running
            client.publish(config.get('mqtt', 'timer_command_topic'), '')      # will lock the program
            client.subscribe(config.get('mqtt', 'run_command_topic'))
            client.subscribe(config.get('mqtt', 'temp_command_topic'))
            client.subscribe(config.get('mqtt', 'timer_run_command_topic'))
            client.subscribe(config.get('mqtt', 'timer_command_topic'))

        client = mqtt.Client(client_id="anovapi")
        client.username_pw_set(username=config.get('mqtt', 'username'),
                               password=config.get('mqtt', 'password'))
        client.on_connect = on_connect
        client.loop_start()
        client.connect(host=config.get('mqtt', 'server'), port=int(config.get("mqtt", "port")))
        client.on_message = self.generic_handler
        client.message_callback_add(config.get('mqtt', 'run_command_topic'),
                                    self.run_command_handler)
        client.message_callback_add(config.get('mqtt', 'temp_command_topic'),
                                    self.temp_command_handler)
        client.message_callback_add(config.get('mqtt', 'timer_run_command_topic'),
                                    self.timer_run_command_handler)
        client.message_callback_add(config.get('mqtt', 'timer_command_topic'),
                                    self.timer_command_handler)

        self._client = client
        self._command_callback = command_callback

    def run_command_handler(self, client, userdata, msg):
        logging.debug('MQTT run handler received {}: {}'.format(msg.topic, msg.payload.decode()))
        sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        sys.stdout.write('MQTT run handler received {}: {}'.format(msg.topic, msg.payload.decode()))
        sys.stdout.write('\n')
        self._command_callback('run', msg.payload.decode('utf-8'))

    def temp_command_handler(self, client, userdata, msg):
        logging.debug('MQTT temp handler received {}: {}'.format(msg.topic, msg.payload.decode()))
        sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        sys.stdout.write('MQTT temp handler received {}: {}'.format(msg.topic, msg.payload.decode()))
        sys.stdout.write('\n')
        self._command_callback('temp', msg.payload.decode('utf-8'))

    def timer_run_command_handler(self, client, userdata, msg):
        logging.debug('MQTT temp handler received {}: {}'.format(msg.topic, msg.payload.decode()))
        sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        sys.stdout.write('MQTT temp handler received {}: {}'.format(msg.topic, msg.payload.decode()))
        sys.stdout.write('\n')
        self._command_callback('timer_run', msg.payload.decode('utf-8'))

    def timer_command_handler(self, client, userdata, msg):
        logging.debug('MQTT temp handler received {}: {}'.format(msg.topic, msg.payload.decode()))
        sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        sys.stdout.write('MQTT temp handler received {}: {}'.format(msg.topic, msg.payload.decode()))
        sys.stdout.write('\n')
        self._command_callback('timer', msg.payload.decode('utf-8'))

    def generic_handler(self, client, userdata, msg):
        logging.warning('MQTT unknown message received {}: {}'.format(msg.topic, msg.payload.decode()))
        sys.stdout.write('%s '% datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        sys.stdout.write('MQTT unknown message received {}: {}'.format(msg.topic, msg.payload.decode()))
        sys.stdout.write('\n')

    def publish_message(self, topic, message):
        self._client.publish(topic, message)

