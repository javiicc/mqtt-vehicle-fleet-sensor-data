import json
import threading
import time
import paho.mqtt.client as mqtt


class CentralDevice:
    def __init__(self, brokers: list, collect_data) -> None:
        self.mqtt_brokers = brokers
        self._collect_data = collect_data
        self.clients = {}
        self.message_store = {}
        self.clients_connected = False
        self._publish_event = threading.Event()
        self._create_client()

    def start_publishing(self) -> None:
        try:
            self._stablish_connection()
        except ConnectionRefusedError as exc:
            print(f"{exc.__class__.__name__}: {exc}")

        # Wait for connection to be established
        while not self.clients_connected:
            time.sleep(0.1)

        while True:
            for event in self._collect_data().values():
                # Get client already connected to the broker
                mqttc = self.clients[event["mqtt_broker"]]

                self._publish_event.clear()

                result = mqttc.publish(
                    topic=event["mqtt_topic"],
                    payload=json.dumps(event["msg"]),
                )

                if result.rc == mqtt.MQTT_ERR_SUCCESS:
                    self.message_store[result.mid] = event["msg"]
                    # print(f"Message stored with mid {result.mid}: {event['msg']}")
                else:
                    print(f"Failed to publish message: {result.rc}")
                    continue

                self._publish_event.wait()

            time.sleep(1)

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        # The callback for when the client receives a CONNACK response from the server
        print(f"{client} connected! Result code: {reason_code}")

        self.clients_connected = all(
            [client.is_connected() for client in self.clients.values()]
        )

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        published_message = self.message_store.pop(mid, None)

        if published_message:
            print(f"mid {mid}: {published_message}")
        else:
            print(f"mid {mid} not found")

        self._publish_event.set()

    def _create_client(self) -> None:
        for broker in self.mqtt_brokers:
            mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            mqttc.on_connect = self._on_connect
            mqttc.on_publish = self._on_publish

            self.clients[broker["name"]] = mqttc

    def _stablish_connection(self) -> None:
        # Iterate to connect each client to a specific broker
        for broker in self.mqtt_brokers:
            self.clients[broker["name"]].connect(broker["host"], broker["port"], 60)
            # Start the network loop in a separate thread
            # self.mqttc.loop_forever()
            self.clients[broker["name"]].loop_start()  # Non-blocking
