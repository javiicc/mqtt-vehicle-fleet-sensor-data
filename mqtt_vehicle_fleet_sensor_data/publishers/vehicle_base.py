from abc import ABC, abstractmethod
import math
from pyexpat import model
from mqtt_vehicle_fleet_sensor_data.iot.sensors import GPS, Thermistor, VoltageDivider
from mqtt_vehicle_fleet_sensor_data.publishers.central_device import CentralDevice


class EngineControlUnit:
    """Vehicle's ECU. Collects and processes data to be read by the Central Device."""

    def __init__(self) -> None:
        self.voltage_divider = VoltageDivider()

    def read_data(self):
        return {"ect": self._get_engine_coolant_temperature()}

    def _get_engine_coolant_temperature(self):
        voltage = self.voltage_divider.voltage()
        temp_celsius = self._calculate_temperature_from_voltage(voltage)
        return temp_celsius

    def _calculate_temperature_from_voltage(self, voltage):
        # Steinhart-Hart coefficients for the thermistor (example values)
        A = 1.009249522e-03
        B = 2.378405444e-04
        C = 2.019202697e-07

        V_ref = 5.0  # Reference voltage from the ECU in volts
        R_pull_up = 10000  # Pull-up resistor value in ohms

        # Calculate the resistance of the thermistor from the voltage
        if voltage == V_ref:  # Prevent division by zero
            return float("inf")  # Indicating an open circuit or infinite temperature

        R_thermistor = R_pull_up * (voltage / (V_ref - voltage))

        # Apply Steinhart-Hart equation to calculate the temperature in Kelvin
        lnR = math.log(R_thermistor)
        inv_T = A + B * lnR + C * (lnR**3)
        T_kelvin = 1 / inv_T

        # Convert Kelvin to Celsius
        T_celsius = T_kelvin - 273.15
        return T_celsius


class Vehicle(ABC):
    def __init__(self, id: str, route: str) -> None:
        self.id = id
        self.gps = GPS(route)
        self.ecu = EngineControlUnit()
        self.central_device = self.create_central_device()

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def create_central_device(self) -> "CentralDevice":
        pass

    def collect_data(self):
        return {
            "id": self.id,
            "gps": self._collect_gps_data(),
            "ecu": self._collect_ecu_data(),
        }

    def _collect_gps_data(self) -> dict:
        return self.gps.read()

    def _collect_ecu_data(self) -> dict:
        return self.ecu.read_data()
