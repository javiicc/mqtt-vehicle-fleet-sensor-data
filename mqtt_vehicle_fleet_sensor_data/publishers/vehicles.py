from copy import deepcopy
from mqtt_vehicle_fleet_sensor_data.iot.sensors import VoltageDivider
from mqtt_vehicle_fleet_sensor_data.publishers.telematic_control_unit import (
    TelematicConstrolUnit,
)
from mqtt_vehicle_fleet_sensor_data.publishers.vehicle_base import Vehicle


class Van(Vehicle):
    def __init__(self, id: str, route: str) -> None:
        # Brokers
        self.mqtt_broker_fleet = {"name": "fleet", "host": "localhost", "port": 1883}
        self.mqtt_broker_vans = {"name": "vans", "host": "localhost", "port": 1884}
        # Topics
        self.mqtt_topic_fleet_data = "fleet/data"
        self.mqtt_topic_fleet_gps = "fleet/gps"
        self.mqtt_topic_van = f"fleet/{id}"
        self.mqtt_topic_van_gps = f"fleet/{id}/gps"
        self.mqtt_topic_van_ecu = f"fleet/{id}/ecu"
        self.mqtt_topic_van_cargo_temp = f"fleet/{id}/cargo-temp"
        # Van specific data
        self.cargo_temp_sensor = VoltageDivider()
        super().__init__(id, route)

    def run(self):
        self.central_device.start_publishing()

    def create_central_device(self) -> "TelematicConstrolUnit":
        return TelematicConstrolUnit(
            [
                self.mqtt_broker_fleet,
                self.mqtt_broker_vans,
            ],
            self.collect_data,
        )

    def collect_data(self) -> dict:
        data = super().collect_data()

        cargo_temp = self.cargo_temp_sensor.get_voltage()
        gps = deepcopy(data["gps"])
        ecu = deepcopy(data["ecu"])

        data["cargo_temperature"] = cargo_temp

        gps["vehicle_id"] = self.id
        cargo_temperature = {"vehicle_id": self.id, "temp": cargo_temp}

        return {
            "data": {
                "mqtt_topic": self.mqtt_topic_fleet_data,
                "mqtt_broker": self.mqtt_broker_fleet["name"],
                "msg": data,
            },
            "gps": {
                "mqtt_topic": self.mqtt_topic_fleet_gps,
                "mqtt_broker": self.mqtt_broker_fleet["name"],
                "msg": gps,
            },
            "van": {
                "mqtt_topic": self.mqtt_topic_van,
                "mqtt_broker": self.mqtt_broker_vans["name"],
                "msg": data,
            },
            "van_gps": {
                "mqtt_topic": self.mqtt_topic_van_gps,
                "mqtt_broker": self.mqtt_broker_vans["name"],
                "msg": gps,
            },
            "van_ecu": {
                "mqtt_topic": self.mqtt_topic_van_ecu,
                "mqtt_broker": self.mqtt_broker_vans["name"],
                "msg": ecu,
            },
            "van_cargo_temp": {
                "mqtt_topic": self.mqtt_topic_van_cargo_temp,
                "mqtt_broker": self.mqtt_broker_vans["name"],
                "msg": cargo_temperature,
            },
        }


class Truck(Vehicle):
    def __init__(self, id: str, route: str) -> None:
        super().__init__(id, route)
        self.mqtt_broker_fleet = {"name": "fleet", "host": "localhost", "port": 1883}
        self.mqtt_broker_trucks = {"name": "trucks", "host": "localhost", "port": 1885}
        self.mqtt_topic_truck = f"fleet/{id}"
        self.mqtt_topic_truck_gps = f"fleet/{id}/gps"
        self.mqtt_topic_truck_trailer_pressure = f"fleet/{id}/trailer-pressure"
        self.central_device = TelematicConstrolUnit(
            [
                self.mqtt_broker_fleet,
                self.mqtt_broker_trucks,
            ],
            self.collect_data,
        )
        self.trailer_pressure_sensor = VoltageDivider()

    def run(self):
        self.central_device.start_publishing()

    def collect_data(self) -> dict:
        gps = super().collect_gps_data()
        trailer_pressure = self.trailer_pressure_sensor.get_voltage()

        vehicle_data = {
            "id": self.id,
            "gps": deepcopy(gps),
            "engine": super().collect_engine_data(),
            "trailer_pressure": trailer_pressure,
        }

        gps["vehicle_id"] = self.id
        # trailer_pressure["vehicle_id"] = self.id

        return {
            "data": {
                "mqtt_topic": self.mqtt_topic_fleet_data,
                "mqtt_broker": self.mqtt_broker_fleet["name"],
                "msg": vehicle_data,
            },
            "gps": {
                "mqtt_topic": self.mqtt_topic_fleet_gps,
                "mqtt_broker": self.mqtt_broker_fleet["name"],
                "msg": gps,
            },
            "truck": {
                "mqtt_topic": self.mqtt_topic_truck,
                "mqtt_broker": self.mqtt_broker_trucks["name"],
                "msg": vehicle_data,
            },
            "truck_gps": {
                "mqtt_topic": self.mqtt_topic_truck_gps,
                "mqtt_broker": self.mqtt_broker_trucks["name"],
                "msg": gps,
            },
        }


if __name__ == "__main__":
    Van("van-1", "dublin-limerick").run()
