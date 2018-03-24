import paho.mqtt.client as mqtt

class MQTTController(object):
    def __init__(self, config, run_callback, temp_callback):
        def on_connect(client, userdata, flags, rc):
            print("MQTT connected with result code {}".format(str(rc)))
            client.subscribe(config.get('mqtt', 'run_command_topic'))
            client.subscribe(config.get('mqtt', 'temp_command_topic'))

        client = mqtt.Client(client_id="anovapi")
        client.username_pw_set(username=config.get('mqtt', 'username'),
                               password=config.get('mqtt', 'password'))
        client.on_connect = on_connect
        client.loop_start()
        client.connect(config.get('mqtt', 'server'))
        client.publish('kitchenpi/status', 'connected')
        client.on_message = self.generic_handler
        client.message_callback_add(config.get('mqtt', 'run_command_topic'),
                                    self.run_command_handler)
        client.message_callback_add(config.get('mqtt', 'temp_command_topic'),
                                    self.temp_command_handler)

        self._client = client
        self._run_callback = run_callback
        self._temp_callback = temp_callback

    def run_command_handler(self, client, userdata, msg):
        print('run handler received {}: {}'.format(msg.topic, msg.payload.decode()))
        self._run_callback(msg.payload.decode('utf-8'))

    def temp_command_handler(self, client, userdata, msg):
        print('temp handler received {}: {}'.format(msg.topic, msg.payload.decode()))

    def generic_handler(self, client, userdata, msg):
        print('unknown message received {}: {}'.format(msg.topic, msg.payload.decode()))

    def publish_message(self, topic, message):
        self._client.publish(topic, message)

