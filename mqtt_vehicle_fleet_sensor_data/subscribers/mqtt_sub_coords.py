import paho.mqtt.client as mqtt


def on_connect(client, userdata, flags, reason_code, properties):
    """"The callback for when the client receives a CONNACK response from the server"""
    if reason_code.is_failure:
        print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
    else:
        # we should always subscribe from on_connect callback to be sure
        # our subscribed is persisted across reconnections.
        client.subscribe(mqtt_topic_coordinates)


def on_subscribe(client, userdata, mid, reason_code_list, properties):
    # Since we subscribed only for a single channel, reason_code_list contains
    # a single entry
    if reason_code_list[0].is_failure:
        print(f"Broker rejected your subscription: {reason_code_list[0]}")
    else:
        print(f"Broker granted the following QoS: {reason_code_list[0].value}")


def on_unsubscribe(client, userdata, mid, reason_code_list, properties):
    # Be careful, the reason_code_list is only present in MQTTv5.
    # In MQTTv3 it will always be empty
    if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
        print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
    else:
        print(f"Broker replied with failure: {reason_code_list[0]}")
    client.disconnect()


# def on_message(client, userdata, message):
#     # userdata is the structure we choose to provide, here it's a list()
#     userdata.append(message.payload)
#     # We only want to process 10 messages
#     if len(userdata) >= 10:
#         client.unsubscribe("$SYS/#")


def on_message(client, userdata, msg):
    # print(f"{msg.topic}: {msg.payload.decode()}")
    print(f"Received: {msg.payload.decode()}")




mqtt_broker = "localhost"
port = 1883
mqtt_topic_vehicle = "fleet/van1"
mqtt_topic_coordinates = "fleet/coordinates"


mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)


mqttc.on_connect = on_connect
mqttc.on_message = on_message
mqttc.on_subscribe = on_subscribe
mqttc.on_unsubscribe = on_unsubscribe


mqttc.connect(mqtt_broker, port, 60)
mqttc.loop_forever()


class MQTTSubscriber:
    def __init__(self, broker, port, mqtt_topic):
        self.broker = broker
        self.port = port
        self.topic = mqtt_topic
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        
        # Assign callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_unsubscribe = self.on_unsubscribe

    def on_connect(self, client, userdata, flags, reason_code, properties):
        """The callback for when the client receives a CONNACK response from the server"""
        if reason_code.is_failure:
            print(f"Failed to connect: {reason_code}. loop_forever() will retry connection")
        else:
            # we should always subscribe from on_connect callback to be sure
            # our subscribed is persisted across reconnections.
            client.subscribe(self.topic_coordinates)

    def on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        # Since we subscribed only for a single channel, reason_code_list contains a single entry
        if reason_code_list[0].is_failure:
            print(f"Broker rejected your subscription: {reason_code_list[0]}")
        else:
            print(f"Broker granted the following QoS: {reason_code_list[0].value}")

    def on_unsubscribe(self, client, userdata, mid, reason_code_list, properties):
        # Be careful, the reason_code_list is only present in MQTTv5.
        # In MQTTv3 it will always be empty
        if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
            print("unsubscribe succeeded (if SUBACK is received in MQTTv3 it success)")
        else:
            print(f"Broker replied with failure: {reason_code_list[0]}")
        client.disconnect()

    def on_message(self, client, userdata, msg):
        # print(f"{msg.topic}: {msg.payload.decode()}")
        print(f"Received: {msg.payload.decode()}")

    def start(self):
        self.client.connect(self.broker, self.port, 60)
        self.client.loop_forever()

# Configuration
mqtt_broker = "localhost"
port = 1883
mqtt_topic_vehicle = "fleet/van1"
mqtt_topic_coordinates = "fleet/coordinates"

# Create and start MQTT subscriber
subscriber = MQTTSubscriber(mqtt_broker, port, mqtt_topic)
subscriber.start()