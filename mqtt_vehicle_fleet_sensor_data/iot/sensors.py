from abc import ABC, abstractmethod
import math
import tempfile
from uuid import uuid4
from random import random, uniform
import time
import pandas as pd
import os


class Sensor(ABC):
    @abstractmethod
    def output(self) -> float:
        pass


class O2Sensor:
    """Simulates a zirconia oxygen sensor."""

    def __init__(self):
        self.voltage = 0.0
        self.operating_temperature = 600
        self.response_time = 0.1

    def measure_exhaust_gas(self, air_fuel_ratio):
        """
        Simulate the O2 sensor measuring the exhaust gas and outputting a voltage.
        :param air_fuel_ratio: The current air-fuel ratio in the engine
        :return: The voltage output by the sensor
        """
        # The sensor's voltage output depends on the AFR:
        # - Lean mixture (AFR > 14.7): Lower voltage output (0.1 - 0.45 volts)
        # - Stoichiometric (AFR ≈ 14.7): Mid-range voltage output (~0.45 volts)
        # - Rich mixture (AFR < 14.7): Higher voltage output (0.45 - 0.9 volts)

        print(air_fuel_ratio)

        if air_fuel_ratio > 14.7:
            # Lean mixture
            self.voltage = 0.1 + (
                (air_fuel_ratio - 14.7) / 10.0
            )  # Simulate a voltage drop for leaner mixtures
        elif air_fuel_ratio < 14.7:
            # Rich mixture
            self.voltage = 0.9 - (
                (14.7 - air_fuel_ratio) / 10.0
            )  # Simulate a voltage increase for richer mixtures
        else:
            # Stoichiometric
            self.voltage = 0.45

        self.voltage = max(0.1, min(self.voltage, 0.9))

        return self.voltage


class PressureSensor:
    def __init__(
        self,
        min_pressure: float,
        max_pressure: float,
        min_voltage: float,
        max_voltage: float,
    ):
        """
        Initialize the MAP sensor with its pressure and voltage ranges.

        Args:
            min_pressure (float): Minimum pressure the sensor can measure (in kPa).
            max_pressure (float): Maximum pressure the sensor can measure (in kPa).
            min_voltage (float): Minimum voltage output of the sensor (in volts).
            max_voltage (float): Maximum voltage output of the sensor (in volts).
        """
        self.min_pressure = min_pressure
        self.max_pressure = max_pressure
        self.min_voltage = min_voltage
        self.max_voltage = max_voltage

    def get_voltage(self, pressure_kpa):
        """
        Calculate the output voltage based on the manifold absolute pressure.

        Args:
            pressure_kpa (float): The manifold absolute pressure (in kPa).

        Returns:
            float: The corresponding output voltage of the MAP sensor (in volts).
        """
        if pressure_kpa < self.min_pressure:
            pressure_kpa = self.min_pressure
        elif pressure_kpa > self.max_pressure:
            pressure_kpa = self.max_pressure

        # Calculate the output voltage using linear interpolation
        output_voltage = self.min_voltage + (pressure_kpa - self.min_pressure) * (
            self.max_voltage - self.min_voltage
        ) / (self.max_pressure - self.min_pressure)
        return output_voltage


class ManifoldAbsolutePressure(PressureSensor):
    def __init__(
        self,
        min_pressure=0,
        max_pressure=300,
        min_voltage=0.5,
        max_voltage=4.5,
    ):
        super().__init__(min_pressure, max_pressure, min_voltage, max_voltage)


class FuelPressure(PressureSensor):
    def __init__(
        self,
        min_pressure=200,
        max_pressure=700,
        min_voltage=0.5,
        max_voltage=4.5,
    ):
        super().__init__(min_pressure, max_pressure, min_voltage, max_voltage)


R_0 = 10000  # Resistance at reference temperature (25°C), in ohms
T_0 = 25 + 273.15  # Reference temperature in Kelvin
beta = 3950  # Beta parameter for the thermistor
V_ref = 5  # Reference voltage from ECU in volts
R_pull_up = 10000  # Pull-up resistor value in ohms


class Thermistor:
    """Negative Temperature Coefficient (NTC) thermistor, the resistance decreases as the temperature increases"""

    def __init__(self) -> None:
        self.R_0 = 10000  # resistance at reference temperature (25°C), in ohms
        self.T_0 = 25 + 273.15  # reference temperature in Kelvin
        self.beta = 3950

    def get_resistance(self, temperature: float) -> float:
        """Thermistor's resistance in ohms"""
        temp_kelvin = temperature + 273.15
        R_T = self.R_0 * math.exp(self.beta * (1 / temp_kelvin - 1 / self.T_0))
        return R_T


class VoltageDivider:

    def __init__(self) -> None:
        self.thermistor = Thermistor()
        self.V_ref = 5  # Reference voltage from ECU in volts
        self.R_pull_up = 10000  # Pull-up resistor value in ohms

    def get_voltage(self, temperature: float = uniform(10.0, 40.0)):
        resistance = self.thermistor.get_resistance(temperature)
        V = self.V_ref * (resistance / (resistance + self.R_pull_up))
        return V


class GPS:
    def __init__(self, route: str) -> None:
        self.id = str(uuid4())
        self.file_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "coordinates/clean-routes",
            route + "-clean.csv",
        )
        self.coords = pd.read_csv(self.file_path)
        self.last_coords = None

    def read(self) -> dict:
        self.last_coords = self.coords.iloc[0]

        self.drive_forward()

        return {
            "id": self.id,
            "timestamp": time.time(),
            "lat": self.last_coords.values[0].item(),
            "lon": self.last_coords.values[1].item(),
        }

    def drive_forward(self):
        self.coords.drop([self.coords.index[0]], inplace=True)
        self.coords = pd.concat([self.coords, self.last_coords.to_frame().T])


if __name__ == "__main__":

    # thermistor = Thermistor("engine")
    # print(thermistor.read())

    gps = GPS("dublin-limerick")
    print(gps.read())
