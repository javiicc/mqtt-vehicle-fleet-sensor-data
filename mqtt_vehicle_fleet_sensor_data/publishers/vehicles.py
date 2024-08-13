from enum import Enum
import json
import time
from mqtt_vehicle_fleet_sensor_data.iot.sensors import GPS, Thermistor
import paho.mqtt.client as mqtt


class VehicleType(Enum):
    VAN = 'van'
    TRUCK = 'truck'
 

class Engine:
    def __init__(self) -> None:
        self.thermistor = Thermistor("engine")

    def read_data(self):
        return self.thermistor.read()


class Vehicle:
    def __init__(self, id: str, vehicle_type: VehicleType, route: str) -> None:
        self.id = id
        self.type = vehicle_type
        self.engine = Engine()
        self.gps = GPS(route)

    def run(self):
        self.CentralDevice(self).start_publishing()


    class CentralDevice():
        def __init__(self, outer_vehicle) -> None:
            self.vehicle = outer_vehicle
            self.connected = False
            self.mqtt_broker = "localhost"
            self.port = 1883
            # self.mqtt_topic_data = f"fleet/{self.vehicle.id}"
            self.mqtt_topic_data = "fleet/data"
            self.mqtt_topic_gps = "fleet/gps"

            self._create_client()

        def start_publishing(self):
            try:
                self.mqttc.connect(self.mqtt_broker, self.port, 60)
                # Start the network loop in a separate thread
                # self.mqttc.loop_forever()
                self.mqttc.loop_start() # Non-blocking
            except ConnectionRefusedError as exc:
                print(f"{exc.__class__.__name__}: {exc}")

            # Wait for connection to be established
            while not self.connected:
                time.sleep(0.1)
                        
            while True:
                self.gps_data = self._collect_coordinates()
                self.vehicle_data = self._collect_vehicle_data(self.gps_data)

                self.gps_data["vehicle_id"] = self.vehicle.id
            
                self.mqttc.publish(
                    topic=self.mqtt_topic_gps, 
                    payload=json.dumps(self.gps_data),
                    )
                self.mqttc.publish(
                    topic=self.mqtt_topic_data, 
                    payload=json.dumps(self.vehicle_data),
                    )
            
                time.sleep(1)

        def _on_connect(self, client, userdata, flags, reason_code, properties):
            # The callback for when the client receives a CONNACK response from the server
            print(f"Connected! Result code: {reason_code}")
            self.connected = True

        def _on_publish(self, client, userdata, mid, reason_code, properties):
                # reason_code and properties will only be present in MQTTv5. It's always unset in MQTTv3

                # print(mid % 2)
                # TODO access all published messages, one each mid
                if mid % 2 == 0:
                    print(f"Published vehicle data: {self.vehicle_data}")
                else:
                    print(f"Published coords: {self.gps_data}")

        def _create_client(self) -> None:
            self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            # Assign callbacks
            self.mqttc.on_connect = self._on_connect
            self.mqttc.on_publish = self._on_publish

        def _collect_coordinates(self) -> dict:
            gps_data = self.vehicle.gps.read()
            return gps_data
        
        def _collect_vehicle_data(self, gps: dict) -> dict:
            return {
                "id": self.vehicle.id,
                "type": self.vehicle.type.value,
                "engine_data": self.vehicle.engine.read_data(),
                "gps": gps
            }
