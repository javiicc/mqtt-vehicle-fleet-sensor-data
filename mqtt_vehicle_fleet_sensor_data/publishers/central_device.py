import json
import time
import paho.mqtt.client as mqtt


class CentralDevice:
    def __init__(self) -> None:
        self.connected = False
        self.mqtt_broker = "localhost"
        self.port = 1883
        self.message_store = {}
        self._create_client()

    def start_publishing(self, events: dict) -> None:
        try:
            self._stablish_connection()
        except ConnectionRefusedError as exc:
            print(f"{exc.__class__.__name__}: {exc}")

        # Wait for connection to be established
        while not self.connected:
            time.sleep(0.1)
                    
        while True:
            for event in events.values():
                result = self.mqttc.publish(
                    topic=event["mqtt_topic"], 
                    payload=json.dumps(event["msg"]),
                )
                self.message_store[result.mid] = event["msg"]
        
            time.sleep(1)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        # The callback for when the client receives a CONNACK response from the server
        print(f"Connected! Result code: {reason_code}")
        self.connected = True

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        published_message = self.message_store.pop(mid, None)
        if published_message:
            print(f"mid {mid}: {published_message}")
        else:
            print(f"mid {mid} not found")

    def _create_client(self) -> None:
        self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self.mqttc.on_connect = self._on_connect
        self.mqttc.on_publish = self._on_publish

    def _stablish_connection(self) -> None:
        self.mqttc.connect(self.mqtt_broker, self.port, 60)
        # Start the network loop in a separate thread
        # self.mqttc.loop_forever()
        self.mqttc.loop_start() # Non-blocking
