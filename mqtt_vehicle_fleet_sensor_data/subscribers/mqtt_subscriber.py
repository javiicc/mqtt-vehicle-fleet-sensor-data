import paho.mqtt.client as mqtt


class MQTTSubscriber:
    def __init__(self, broker, port, mqtt_topic):
        self.broker = broker
        self.port = port
        self.topic = mqtt_topic

        self._create_client()
    
    def start(self):

        try:
            self.client.connect(self.broker, self.port, 60)
            self.client.loop_forever()
        except ConnectionRefusedError as exc:
            print(f"{exc.__class__.__name__}: {exc}")

    def _create_client(self):
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        # Assign callbacks
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        self.client.on_unsubscribe = self._on_unsubscribe

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        """The callback for when the client receives a CONNACK response from the server"""
        if reason_code.is_failure:
            print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
        else:
            # we should always subscribe from _on_connect callback to be sure
            # our subscribed is persisted across reconnections.
            client.subscribe(self.topic)

    def _on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        # Since we subscribed only for a single channel, reason_code_list contains a single entry
        if reason_code_list[0].is_failure:
            print(f"Broker rejected your subscription: {reason_code_list[0]}")
        else:
            print(f"Broker granted the following QoS: {reason_code_list[0].value}")

    def _on_unsubscribe(self, client, userdata, mid, reason_code_list, properties):
        # Be careful, the reason_code_list is only present in MQTTv5.
        # In MQTTv3 it will always be empty
        if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
            print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
        else:
            print(f"Broker replied with failure: {reason_code_list[0]}")
        client.disconnect()

    def _on_message(self, client, userdata, msg):
        # print(f"{msg.topic}: {msg.payload.decode()}")
        print(f"Received: {msg.payload.decode()}")


if __name__ == "__main__":

    # Configuration
    mqtt_broker = "localhost"
    port = 1884
    mqtt_topic = "fleet/van-1"

    # Create and start MQTT subscriber
    subscriber = MQTTSubscriber(mqtt_broker, port, mqtt_topic)
    subscriber.start()