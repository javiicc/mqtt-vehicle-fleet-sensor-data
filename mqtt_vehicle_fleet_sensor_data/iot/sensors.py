from abc import ABC, abstractmethod
import math
import tempfile
from uuid import uuid4
from random import uniform
import time
import pandas as pd
import os


class Sensor(ABC):
    @abstractmethod
    def output(self) -> float:
        pass


class ManifoldAbsolutePressure:
    def __init__(
        self,
        min_pressure: float = 10,
        max_pressure: float = 110,
        min_voltage: float = 0.5,
        max_voltage: float = 4.5,
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
