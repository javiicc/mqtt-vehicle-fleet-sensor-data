from enum import Enum
import json
from multiprocessing import Process
import time

import paho.mqtt.client as mqtt

from mqtt_vehicle_fleet_sensor_data.iot.sensors import GPS, Thermistor


class VehicleType(Enum):
    VAN = 'van'
    TRUCK = 'truck'
 

class Engine():
    def __init__(self) -> None:
        self.thermistor = Thermistor("engine")


class Vehicle(Process):
    def __init__(self, id: str, vehicle_type: VehicleType, route: str) -> None:
        super().__init__(daemon=True)
        self.id = id
        self.type = vehicle_type
        self.engine = Engine()
        self.gps = GPS(route)


    def run(self):
        self.CentralDevice(self)


    class CentralDevice():
        def __init__(self, outer_vehicle) -> None:
            self.vehicle = outer_vehicle
            self.connected = False
            self.mqtt_broker = "localhost"
            self.port = 1883
            # self.mqtt_topic_vehicle = f"fleet/{self.vehicle.id}"
            self.mqtt_topic_vehicle = "fleet/vans"
            self.mqtt_topic_coordinates = "fleet/coordinates"
            self.mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
            self.start_publishing()


        def start_publishing(self):

            def on_connect(client, userdata, flags, reason_code, properties):
                # The callback for when the client receives a CONNACK response from the server
                print(f"Connected! Result code: {reason_code}")
                self.connected = True
            
            
            def on_publish(client, userdata, mid, reason_code, properties):
                # reason_code and properties will only be present in MQTTv5. It's always unset in MQTTv3

                # print(mid % 2)
                # TODO access all published messages, one each mid
                if mid % 2 == 0:
                    print(f"Published vehicle data: {vehicle_data}")
                else:
                    print(f"Published coords: {coords}")

            self.mqttc.on_connect = on_connect
            self.mqttc.on_publish = on_publish
            self.mqttc.connect(self.mqtt_broker, self.port, 60)

            # Start the network loop in a separate thread
            self.mqttc.loop_start()
            
            # Wait for connection to be established
            while not self.connected:
                time.sleep(0.1)
                        
            while True:
                coords = self.vehicle.gps.read()

                vehicle_data = {
                    "id": self.vehicle.id,
                    "vehicle_type": self.vehicle.type.value,
                    "engine_data": self.vehicle.engine.thermistor.read(),
                    "coordinates": coords
                }
            
                self.mqttc.publish(
                    topic=self.mqtt_topic_coordinates, 
                    payload=json.dumps(coords),
                    )
                self.mqttc.publish(
                    topic=self.mqtt_topic_vehicle, 
                    payload=json.dumps(vehicle_data),
                    )
            
                time.sleep(1)


if __name__ == "__main__":

    n_vans = 4
    n_trucks = 0

    # TODO automate routes probabilistically
    van_processes = [ Vehicle(f"van-{i}", VehicleType.VAN, "dublin-limerick") for i in range(1, n_vans + 1) ]
    
    for i, p in enumerate(van_processes):
        p.start()

        # print(f'--- Process {i + 1} ---')
        # print(f'name: {p.name} PID: {p.pid}')

    van_processes[0].join()
