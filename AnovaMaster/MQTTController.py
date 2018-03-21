import paho.mqtt.client as mqtt

class MQTTController(object):
    def __init__(self, config):
        def on_connect(client, userdata, flags, rc):
            print("MQTT connected with result code {}".format(str(rc)))
            client.subscribe(config.get('mqtt', 'command_topic'))

        client = mqtt.Client(client_id="anovapi")
        client.username_pw_set(username=config.get('mqtt', 'username'),
                               password=config.get('mqtt', 'password'))
        client.on_connect = on_connect
        client.on_message = self.receive_handler
        client.connect(config.get('mqtt', 'server'))
        client.publish('kitchenpi/status', 'connected')

        self._client = client

    def receive_handler(self, client, userdata, msg):
        print('mqtt received {}: {}'.format(msg.topic, msg.payload.decode()))
        # TODO: message handlers here

    def publish_message(self, topic, message):
        self._client.publish(topic, message)

