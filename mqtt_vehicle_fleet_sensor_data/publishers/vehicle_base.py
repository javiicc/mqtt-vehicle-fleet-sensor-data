from abc import ABC, abstractmethod
import math
from random import uniform
from mqtt_vehicle_fleet_sensor_data.iot.sensors import (
    GPS,
    ManifoldAbsolutePressure,
    VoltageDivider,
)
from mqtt_vehicle_fleet_sensor_data.publishers.telematic_control_unit import (
    TelematicConstrolUnit,
)
from mqtt_vehicle_fleet_sensor_data.utils import calculate_temperature_from_voltage


class EngineControlUnit:
    """Vehicle's ECU. Collects and processes data to be read by the Central Device."""

    def __init__(self) -> None:
        self.voltage_divider = VoltageDivider()
        self.map = ManifoldAbsolutePressure()

    def read_data(self):
        return {
            "ect": self._get_engine_coolant_temperature(),
            "iat": self._get_intake_air_temperature(),
            "map": self._get_manifold_absolute_pressure(),
        }

    def _get_engine_coolant_temperature(self) -> float:
        # TODO Temperature values based on system
        voltage = self.voltage_divider.get_voltage(uniform(10.0, 40.0))
        temperature = calculate_temperature_from_voltage(voltage)
        return temperature

    def _get_intake_air_temperature(self) -> float:
        # TODO Temperature values based on system
        voltage = self.voltage_divider.get_voltage(uniform(10.0, 40.0))
        temperature = calculate_temperature_from_voltage(voltage)
        return temperature

    def _get_manifold_absolute_pressure(self) -> float:
        # TODO Values based on normal and non-normal situations
        return self.map.get_voltage(uniform(10.0, 110.0))


class Vehicle(ABC):
    def __init__(self, id: str, route: str) -> None:
        self.id = id
        self.voltage_divider = VoltageDivider()
        self.gps = GPS(route)
        self.ecu = EngineControlUnit()
        self.central_device = self.create_central_device()

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def create_central_device(self) -> "TelematicConstrolUnit":
        pass

    def collect_data(self):
        return {
            "id": self.id,
            "gps": self._collect_gps_data(),
            "ecu": self._collect_ecu_data(),
            "cabin_temp": self._get_cabin_temperature(),
        }

    def _collect_gps_data(self) -> dict:
        return self.gps.read()

    def _collect_ecu_data(self) -> dict:
        return self.ecu.read_data()

    def _get_cabin_temperature(self) -> float:
        # TODO Temperature values based on system
        voltage = self.voltage_divider.get_voltage(uniform(0.0, 60.0))
        temperature = calculate_temperature_from_voltage(voltage)
        return temperature
